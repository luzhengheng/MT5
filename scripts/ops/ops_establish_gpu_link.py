#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU Node Connectivity Setup Script
Task #026.00: GPU Node Connectivity Setup (Cross-Region)
Protocol: v2.2 (Configuration-as-Code, Loud Failures)

Establishes secure SSH access from local HUB (Singapore) to remote GPU node (Guangzhou).
Automates SSH key generation and configuration without manual intervention.

Usage:
    python3 scripts/ops_establish_gpu_link.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Configuration
TARGET_HOST = "www.guangzhoupeak.com"
TARGET_USER = "root"
ALIAS = "gpu-node"
SSH_KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")
SSH_PUB_KEY_PATH = os.path.expanduser("~/.ssh/id_rsa.pub")
SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")
SSH_DIR = os.path.expanduser("~/.ssh")

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_header(title):
    """Print formatted header."""
    print()
    print("=" * 80)
    print(f"{CYAN}{title}{RESET}")
    print("=" * 80)
    print()

def print_success(msg):
    """Print success message."""
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    """Print error message."""
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    """Print info message."""
    print(f"{CYAN}ℹ️  {msg}{RESET}")

# ============================================================================
# Step 1: Check SSH Directory
# ============================================================================

def check_ssh_directory():
    """Ensure ~/.ssh directory exists with proper permissions."""
    print_header("Step 1: Checking SSH Directory")

    if not os.path.exists(SSH_DIR):
        print_info(f"Creating SSH directory: {SSH_DIR}")
        os.makedirs(SSH_DIR, mode=0o700)
        print_success("SSH directory created")
    else:
        print_success("SSH directory exists")

    # Fix permissions (should be 700)
    os.chmod(SSH_DIR, 0o700)
    print_success(f"SSH directory permissions set to 700")

# ============================================================================
# Step 2: Check SSH Key
# ============================================================================

def check_ssh_key():
    """Verify or generate SSH key."""
    print_header("Step 2: Checking SSH Key")

    if os.path.exists(SSH_KEY_PATH):
        print_success(f"SSH key exists at {SSH_KEY_PATH}")

        # Check permissions
        key_stat = os.stat(SSH_KEY_PATH)
        if key_stat.st_mode & 0o077:
            print_warning("Private key has insecure permissions, fixing...")
            os.chmod(SSH_KEY_PATH, 0o600)
            print_success("Private key permissions set to 600")
        else:
            print_success("Private key permissions are correct (600)")

        return True
    else:
        print_warning(f"SSH key not found at {SSH_KEY_PATH}")
        print_info("Generating new SSH key...")

        try:
            # Generate RSA key without passphrase (for automation)
            subprocess.run(
                [
                    "ssh-keygen",
                    "-t", "rsa",
                    "-N", "",  # No passphrase
                    "-f", SSH_KEY_PATH,
                    "-C", f"gpu-node-{os.getenv('USER', 'root')}@{os.getenv('HOSTNAME', 'localhost')}"
                ],
                check=True,
                capture_output=True
            )

            # Set correct permissions
            os.chmod(SSH_KEY_PATH, 0o600)
            os.chmod(SSH_PUB_KEY_PATH, 0o644)

            print_success(f"SSH key generated at {SSH_KEY_PATH}")
            print_info(f"Public key: {SSH_PUB_KEY_PATH}")

            return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to generate SSH key: {e}")
            return False
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return False

# ============================================================================
# Step 3: Configure SSH Config
# ============================================================================

def configure_ssh_config():
    """Add or update gpu-node entry in SSH config."""
    print_header("Step 3: Configuring SSH Config")

    ssh_config_entry = f"""
Host {ALIAS}
    HostName {TARGET_HOST}
    User {TARGET_USER}
    IdentityFile {SSH_KEY_PATH}
    StrictHostKeyChecking no
    ConnectTimeout 10
    ServerAliveInterval 60
    ServerAliveCountMax 5
"""

    try:
        # Check if config exists
        if not os.path.exists(SSH_CONFIG_PATH):
            print_info("Creating SSH config file...")
            with open(SSH_CONFIG_PATH, 'w') as f:
                f.write(ssh_config_entry.lstrip())
            os.chmod(SSH_CONFIG_PATH, 0o600)
            print_success(f"SSH config created at {SSH_CONFIG_PATH}")
        else:
            print_info("SSH config exists, checking for gpu-node entry...")

            with open(SSH_CONFIG_PATH, 'r') as f:
                config_content = f.read()

            if f"Host {ALIAS}" in config_content:
                print_success(f"Entry for '{ALIAS}' already exists in SSH config")
            else:
                print_info(f"Adding '{ALIAS}' entry to SSH config...")
                with open(SSH_CONFIG_PATH, 'a') as f:
                    f.write('\n' + ssh_config_entry.lstrip())
                print_success(f"Added '{ALIAS}' to SSH config")

        # Verify permissions
        os.chmod(SSH_CONFIG_PATH, 0o600)
        print_success("SSH config permissions set to 600")

        return True

    except Exception as e:
        print_error(f"Failed to configure SSH: {e}")
        return False

# ============================================================================
# Step 4: Test Connectivity
# ============================================================================

def test_connectivity():
    """Test SSH connection to GPU node."""
    print_header("Step 4: Testing GPU Node Connectivity")

    print_info(f"Testing connection to {ALIAS} ({TARGET_HOST})...")

    try:
        # Try to run nvidia-smi
        result = subprocess.run(
            ["ssh", ALIAS, "nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success("✨ GPU Node Connected!")
            print()
            print("GPU Status (first 300 chars):")
            print("-" * 80)
            print(result.stdout[:300])
            if len(result.stdout) > 300:
                print("...")
            print("-" * 80)
            print()
            return True
        else:
            print_error(f"Connection failed with return code {result.returncode}")

            if "Permission denied" in result.stderr:
                print_error("Permission denied (publickey)")
                print()
                print_warning("🔐 Manual SSH Key Setup Required")
                print()
                print("Your public key has not been installed on the remote server.")
                print("Run this command to copy your public key:")
                print()
                print(f"  {CYAN}ssh-copy-id -i {SSH_PUB_KEY_PATH} {TARGET_USER}@{TARGET_HOST}{RESET}")
                print()
                print("After running that command, retry:")
                print(f"  python3 scripts/ops_establish_gpu_link.py")
                print()
            else:
                print("Error output:")
                print(result.stderr[:200])

            return False

    except subprocess.TimeoutExpired:
        print_error("Connection timeout (>10 seconds)")
        print_warning("Check network connectivity:")
        print(f"  ping {TARGET_HOST}")
        print(f"  nc -zv {TARGET_HOST} 22")
        return False

    except FileNotFoundError:
        print_error("SSH command not found")
        print_info("Please install OpenSSH client:")
        print("  Ubuntu/Debian: sudo apt-get install openssh-client")
        print("  macOS: brew install openssh")
        return False

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

# ============================================================================
# Step 5: Verify SSH Config
# ============================================================================

def verify_ssh_config():
    """Display final SSH config entry."""
    print_header("Step 5: SSH Configuration Summary")

    try:
        with open(SSH_CONFIG_PATH, 'r') as f:
            content = f.read()

        # Find gpu-node section
        lines = content.split('\n')
        in_gpu_section = False
        gpu_section = []

        for line in lines:
            if f"Host {ALIAS}" in line:
                in_gpu_section = True
            elif in_gpu_section and line.startswith('Host '):
                break
            elif in_gpu_section:
                gpu_section.append(line)

        if gpu_section:
            print_success(f"✅ SSH Config Entry for '{ALIAS}':")
            print()
            print(f"Host {ALIAS}")
            for line in gpu_section:
                if line.strip():
                    print(f"    {line.strip()}")
            print()
        else:
            print_warning("Could not find gpu-node section")

    except Exception as e:
        print_error(f"Could not read SSH config: {e}")

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution flow."""
    print()
    print("=" * 80)
    print(f"{CYAN}🌐 GPU NODE CONNECTIVITY SETUP{RESET}")
    print(f"{CYAN}Establishing SSH link: Singapore HUB → Guangzhou GPU Node{RESET}")
    print("=" * 80)
    print()

    # Step 1: SSH Directory
    check_ssh_directory()

    # Step 2: SSH Key
    if not check_ssh_key():
        print_error("Failed to set up SSH key")
        return 1

    # Step 3: SSH Config
    if not configure_ssh_config():
        print_error("Failed to configure SSH config")
        return 1

    # Step 4: Test Connectivity
    connectivity_ok = test_connectivity()

    # Step 5: Verify Config
    verify_ssh_config()

    # Final Summary
    print_header("Summary")

    if connectivity_ok:
        print_success("🎉 GPU Node Setup Complete!")
        print()
        print("You can now use:")
        print(f"  {CYAN}ssh {ALIAS} nvidia-smi{RESET}")
        print()
        print("Or run any command on the GPU node:")
        print(f"  {CYAN}ssh {ALIAS} 'python train.py'{RESET}")
        print()
        return 0
    else:
        print_warning("⚠️  GPU Node setup incomplete")
        print()
        print("The SSH configuration is ready, but the remote key needs setup.")
        print()
        print("Next steps:")
        print(f"1. Run: ssh-copy-id -i {SSH_PUB_KEY_PATH} {TARGET_USER}@{TARGET_HOST}")
        print("2. After key is installed, retry: python3 scripts/ops_establish_gpu_link.py")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
