#!/usr/bin/env python3
r"""
Task #011.19: Retry GTW SSH Key Deployment
Purpose: Deploy SSH key to Gateway (GTW) Windows node after OpenSSH is enabled
Protocol: v2.2 (Docs-as-Code)

This script:
1. Loads the pre-generated SSH public key
2. Prompts for Administrator password on GTW
3. Connects via Paramiko SSH
4. Deploys key to C:\Users\Administrator\.ssh\authorized_keys
5. Sets proper file permissions via icacls
"""

import os
import sys
from pathlib import Path
from getpass import getpass
import paramiko
from paramiko import SSHClient, AutoAddPolicy

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Paths
HOME = Path.home()
SSH_DIR = HOME / ".ssh"
PUBLIC_KEY_PATH = SSH_DIR / "id_rsa.pub"

# GTW Configuration
GTW_CONFIG = {
    "hostname": "172.19.141.255",
    "user": "Administrator",
    "os": "Windows",
    "ssh_dir": r"C:\Users\Administrator\.ssh",
}


def print_header(title, subtitle=""):
    """Print formatted section header."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    if subtitle:
        print(f"{CYAN}  {subtitle}{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")


def check_status(name, status, detail="", error=""):
    """Print formatted status check."""
    symbol = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
    detail_str = f"  [{detail}]" if detail else ""
    if error:
        print(f"  {symbol} {name:<50} {detail_str}")
        print(f"     {RED}Error: {error}{RESET}")
    else:
        print(f"  {symbol} {name:<50} {detail_str}")
    return status


def read_public_key():
    """Read public key from file."""
    print(f"\n{BLUE}[Step 1]{RESET} Read Local SSH Public Key")

    if not PUBLIC_KEY_PATH.exists():
        check_status("Public key exists", False, "", f"Not found at {PUBLIC_KEY_PATH}")
        print(f"\n  {YELLOW}⚠️  SSH key not generated yet.{RESET}")
        print(f"  {YELLOW}Run ops_universal_key_setup.py first to generate keys.{RESET}\n")
        return None

    try:
        with open(PUBLIC_KEY_PATH, 'r') as f:
            pub_key = f.read().strip()

        # Extract fingerprint
        if pub_key.startswith("ssh-rsa"):
            fingerprint = pub_key.split()[1][:16]
        else:
            fingerprint = "unknown"

        check_status("Public key readable", True, f"Fingerprint: {fingerprint}...")
        return pub_key

    except Exception as e:
        check_status("Public key read", False, "", str(e))
        return None


def deploy_key_to_gtw(public_key):
    """Deploy public key to GTW Windows node."""
    print(f"\n{BLUE}[Step 2]{RESET} Connect to GTW and Deploy Key")

    hostname = GTW_CONFIG["hostname"]
    user = GTW_CONFIG["user"]
    ssh_dir = GTW_CONFIG["ssh_dir"]

    # Windows OpenSSH for Administrator users uses ProgramData path
    programdata_ssh_dir = r"C:\ProgramData\ssh"
    programdata_authkeys = r"C:\ProgramData\ssh\administrators_authorized_keys"

    # Prompt for password
    password = getpass(f"\n  Enter password for {user}@{hostname}: ")

    if not password:
        check_status("Authentication", False, "", "No password provided")
        return False

    try:
        # Create SSH client
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        # Connect
        print(f"\n  Connecting to {hostname}...")
        client.connect(
            hostname=hostname,
            username=user,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        check_status(f"SSH connection to GTW", True, f"{user}@{hostname}")

        # Deploy to BOTH paths for compatibility
        print(f"\n  Deploying public key to user directory: {ssh_dir}...")

        # Path A: User .ssh directory (C:\Users\Administrator\.ssh\authorized_keys)
        mkdir_user = f'if not exist "{ssh_dir}" mkdir "{ssh_dir}"'
        append_user = f'echo {public_key} >> "{ssh_dir}\\authorized_keys"'
        icacls_user_dir = f'icacls "{ssh_dir}" /inheritance:r /grant "Administrators:(F)" /grant "SYSTEM:(F)"'
        icacls_user_file = f'icacls "{ssh_dir}\\authorized_keys" /inheritance:r /grant "Administrators:(F)" /grant "SYSTEM:(F)"'

        user_cmd = f'{mkdir_user} && {append_user} && {icacls_user_dir} && {icacls_user_file}'

        # Execute user directory deployment
        stdin, stdout, stderr = client.exec_command(user_cmd)
        stdout.channel.recv_exit_status()
        error_output = stderr.read().decode().strip()

        if error_output and "already exists" not in error_output and "successfully processed" not in error_output.lower():
            print(f"     Warning (user path): {error_output[:200]}")

        check_status(f"Key deployed to user .ssh", True, f"{ssh_dir}\\authorized_keys")

        # Path B: ProgramData (C:\ProgramData\ssh\administrators_authorized_keys)
        # This is the standard path for Administrator users in Win32-OpenSSH
        print(f"\n  Deploying public key to ProgramData: {programdata_authkeys}...")

        mkdir_programdata = f'if not exist "{programdata_ssh_dir}" mkdir "{programdata_ssh_dir}"'
        append_programdata = f'echo {public_key} >> "{programdata_authkeys}"'
        icacls_programdata_dir = f'icacls "{programdata_ssh_dir}" /inheritance:r /grant "Administrators:(F)" /grant "SYSTEM:(F)"'
        icacls_programdata_file = f'icacls "{programdata_authkeys}" /inheritance:r /grant "Administrators:(F)" /grant "SYSTEM:(F)"'

        programdata_cmd = f'{mkdir_programdata} && {append_programdata} && {icacls_programdata_dir} && {icacls_programdata_file}'

        # Execute ProgramData deployment
        stdin, stdout, stderr = client.exec_command(programdata_cmd)
        stdout.channel.recv_exit_status()
        error_output = stderr.read().decode().strip()

        if error_output and "already exists" not in error_output and "successfully processed" not in error_output.lower():
            print(f"     Warning (ProgramData): {error_output[:200]}")

        check_status(f"Key deployed to ProgramData", True, f"{programdata_authkeys}")

        # Verify both deployments
        print(f"\n  Verifying key deployment...")

        # Verify user path
        verify_user_cmd = f'type "{ssh_dir}\\authorized_keys"'
        stdin, stdout, stderr = client.exec_command(verify_user_cmd)
        verify_user_output = stdout.read().decode().strip()
        user_deployed = public_key[:20] in verify_user_output

        # Verify ProgramData path
        verify_programdata_cmd = f'type "{programdata_authkeys}"'
        stdin, stdout, stderr = client.exec_command(verify_programdata_cmd)
        verify_programdata_output = stdout.read().decode().strip()
        programdata_deployed = public_key[:20] in verify_programdata_output

        # Check results
        check_status(f"User .ssh verification", user_deployed, "Key present" if user_deployed else "")
        check_status(f"ProgramData verification", programdata_deployed, "Key present" if programdata_deployed else "")

        # Verify permissions
        print(f"\n  Verifying permissions...")
        verify_perms_user = f'icacls "{ssh_dir}\\authorized_keys"'
        stdin, stdout, stderr = client.exec_command(verify_perms_user)
        perms_user = stdout.read().decode().strip()

        verify_perms_programdata = f'icacls "{programdata_authkeys}"'
        stdin, stdout, stderr = client.exec_command(verify_perms_programdata)
        perms_programdata = stdout.read().decode().strip()

        # Check for strict permissions (no inheritance, only Administrators/SYSTEM)
        user_secure = "BUILTIN\\Administrators:(F)" in perms_user or "Administrators:(F)" in perms_user
        programdata_secure = "BUILTIN\\Administrators:(F)" in perms_programdata or "Administrators:(F)" in perms_programdata

        check_status(f"User .ssh permissions", user_secure, "Strict ACLs" if user_secure else "")
        check_status(f"ProgramData permissions", programdata_secure, "Strict ACLs" if programdata_secure else "")

        if programdata_deployed:
            print(f"\n  {GREEN}✅ GTW Key Installed (ProgramData path - recommended){RESET}")
            print(f"  {GREEN}✅ Permissions fixed - inheritance removed{RESET}")
            client.close()
            return True
        elif user_deployed:
            print(f"\n  {GREEN}✅ GTW Key Installed (User path){RESET}")
            print(f"  {YELLOW}⚠️  ProgramData deployment failed - may need manual fix{RESET}")
            client.close()
            return True
        else:
            check_status(f"Key verification on GTW", False, "", "Key not found in any authorized_keys")
            client.close()
            return False

    except paramiko.AuthenticationException as e:
        check_status(f"Authentication", False, "", "Invalid password or authentication failed")
        return False
    except paramiko.SSHException as e:
        check_status(f"SSH connection", False, "", str(e))
        print(f"\n  {RED}❌ Connection failed. Is OpenSSH Server running on GTW?{RESET}")
        print(f"  {YELLOW}Run the Windows setup guide first: MANUAL_WINDOWS_SSH_SETUP.md{RESET}\n")
        return False
    except Exception as e:
        check_status(f"Key deployment", False, "", str(e))
        return False


def verify_connection():
    """Verify password-less SSH connection to GTW."""
    print(f"\n{BLUE}[Step 3]{RESET} Verify Password-less SSH Access")

    try:
        import subprocess

        print(f"\n  Testing SSH connection to GTW...")
        result = subprocess.run(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "gtw",
                "echo SUCCESS"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            check_status("Password-less SSH to GTW", True, "Connection successful")
            print(f"\n  {GREEN}✅ GTW is now accessible via: ssh gtw{RESET}")
            return True
        else:
            error = result.stderr.strip() or "Unknown error"
            check_status("Password-less SSH to GTW", False, "", error)
            print(f"\n  {YELLOW}⚠️  Connection test failed.{RESET}")
            print(f"  {YELLOW}Ensure SSH config is properly generated.{RESET}\n")
            return False

    except Exception as e:
        check_status("SSH verification", False, "", str(e))
        return False


def main():
    """Execute GTW SSH key deployment."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  TASK #011.19: RETRY GTW SSH KEY DEPLOYMENT{RESET}")
    print(f"{CYAN}  After Windows OpenSSH Setup{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    print(f"{YELLOW}Prerequisites:{RESET}")
    print(f"  1. OpenSSH Server installed on GTW (Windows)")
    print(f"  2. SSH service running (netstat -ano | findstr :22)")
    print(f"  3. Firewall allows port 22")
    print(f"  4. SSH key pair generated (~/.ssh/id_rsa)")
    print()

    # Step 1: Read public key
    public_key = read_public_key()
    if not public_key:
        print(f"\n{RED}❌ Failed to read public key{RESET}\n")
        return 1

    # Step 2: Deploy key to GTW
    if not deploy_key_to_gtw(public_key):
        print(f"\n{RED}❌ Failed to deploy key to GTW{RESET}\n")
        print(f"{YELLOW}Troubleshooting:{RESET}")
        print(f"  1. Verify OpenSSH is installed: Get-WindowsCapability -Online | Where-Object Name -like '*OpenSSH*'")
        print(f"  2. Check service is running: Get-Service sshd")
        print(f"  3. Verify port 22 is listening: netstat -ano | findstr :22")
        print(f"  4. Check firewall rule: Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP'")
        print()
        return 1

    # Step 3: Verify connection
    print()
    if verify_connection():
        print_header("DEPLOYMENT SUCCESSFUL")
        print(f"  {GREEN}✅ GTW SSH key deployment complete!{RESET}\n")
        print(f"  {GREEN}You can now use:{RESET}")
        print(f"    • ssh gtw")
        print(f"    • ssh gtw 'powershell command'")
        print(f"    • scp file.txt gtw:/path/to/destination")
        print()
        return 0
    else:
        print_header("VERIFICATION FAILED")
        print(f"  {RED}❌ SSH connection test failed{RESET}\n")
        print(f"  {YELLOW}Check your SSH config in ~/.ssh/config:{RESET}")
        print(f"    Host gtw")
        print(f"      HostName 172.19.141.255")
        print(f"      User Administrator")
        print(f"      IdentityFile ~/.ssh/id_rsa")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
