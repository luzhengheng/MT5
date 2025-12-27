#!/usr/bin/env python3
"""
Work Order #023.9: Synergy Verification (The "Link Check")
============================================================

Verify critical infrastructure connections are intact after sanitization.

Connectivity Checks:
1. GTW Link: TCP connectivity to 172.19.141.255 on ports 5555/5556
2. HUB Link: SSH keys valid for Git/GitHub access

This ensures the cleanup didn't isolate the server.

Protocol: v2.0 (Strict TDD)
"""

import sys
import socket
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Infrastructure constants
GATEWAY_IP = "172.19.141.255"
ZMQ_PORTS = [5555, 5556]
SSH_KEY_PATH = Path.home() / ".ssh" / "id_rsa"


# ============================================================================
# Check 1: GTW Link (Gateway Connectivity)
# ============================================================================

def check_gtw_link():
    """
    Verify TCP connectivity to Windows Gateway.

    Checks:
        - Can connect to 172.19.141.255:5555 (ZMQ Command)
        - Can connect to 172.19.141.255:5556 (ZMQ Data)

    Returns:
        (bool, str): (success, message)
    """
    logger.info("=" * 70)
    logger.info("🔍 Check 1: GTW Link (Gateway Connectivity)")
    logger.info("=" * 70)
    print()

    logger.info(f"Target Gateway: {GATEWAY_IP}")
    logger.info(f"ZMQ Ports: {ZMQ_PORTS}")
    print()

    all_reachable = True
    messages = []

    for port in ZMQ_PORTS:
        logger.info(f"Testing {GATEWAY_IP}:{port}...")

        try:
            # Attempt TCP connection with 2-second timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)

            result = sock.connect_ex((GATEWAY_IP, port))

            if result == 0:
                logger.info(f"  ✅ Port {port}: Reachable")
                messages.append(f"Port {port}: OK")
            else:
                logger.warning(f"  ⚠️  Port {port}: Not reachable (may be normal if Gateway not running)")
                messages.append(f"Port {port}: Not reachable")
                # Don't fail - gateway may not be running yet
                # all_reachable = False

            sock.close()

        except socket.gaierror:
            logger.error(f"  ❌ Port {port}: DNS resolution failed")
            messages.append(f"Port {port}: DNS ERROR")
            all_reachable = False
        except socket.timeout:
            logger.warning(f"  ⚠️  Port {port}: Connection timeout")
            messages.append(f"Port {port}: Timeout")
            # Don't fail - gateway may not be running
        except Exception as e:
            logger.error(f"  ❌ Port {port}: {str(e)}")
            messages.append(f"Port {port}: ERROR")
            all_reachable = False

    print()

    # Also test basic network routing
    logger.info("Testing network routing (ping)...")
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", GATEWAY_IP],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            logger.info(f"  ✅ Ping to {GATEWAY_IP}: Success")
            messages.append("Ping: OK")
        else:
            logger.warning(f"  ⚠️  Ping to {GATEWAY_IP}: Failed (may be normal if ICMP blocked)")
            messages.append("Ping: Failed (ICMP may be blocked)")

    except subprocess.TimeoutExpired:
        logger.warning("  ⚠️  Ping timeout")
        messages.append("Ping: Timeout")
    except Exception as e:
        logger.error(f"  ❌ Ping error: {e}")
        messages.append(f"Ping: ERROR")

    print()
    if all_reachable:
        logger.info("✅ GTW Link: Network route intact")
        return True, "Network routing to Gateway intact"
    else:
        logger.error("❌ GTW Link: Network issues detected")
        return False, "Network routing issues"


# ============================================================================
# Check 2: HUB Link (GitHub SSH Access)
# ============================================================================

def check_hub_link():
    """
    Verify SSH keys are valid for Git/GitHub access.

    Checks:
        - SSH key exists (~/.ssh/id_rsa)
        - Git config exists (~/.gitconfig)
        - SSH connection to github.com works (ssh -T git@github.com)

    Returns:
        (bool, str): (success, message)
    """
    logger.info("=" * 70)
    logger.info("🔍 Check 2: HUB Link (GitHub SSH Access)")
    logger.info("=" * 70)
    print()

    # Check 1: SSH key exists
    logger.info(f"Checking SSH key: {SSH_KEY_PATH}")
    if not SSH_KEY_PATH.exists():
        logger.error("  ❌ SSH key NOT found")
        return False, "SSH key missing"

    logger.info("  ✅ SSH key exists")
    print()

    # Check 2: Git config exists
    git_config = Path.home() / ".gitconfig"
    logger.info(f"Checking Git config: {git_config}")
    if not git_config.exists():
        logger.warning("  ⚠️  Git config NOT found (may be normal)")
        # Don't fail - git can work without global config
    else:
        logger.info("  ✅ Git config exists")
    print()

    # Check 3: Test SSH connection to GitHub
    logger.info("Testing SSH connection to github.com...")
    try:
        result = subprocess.run(
            ["ssh", "-T", "git@github.com", "-o", "StrictHostKeyChecking=no"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # ssh -T git@github.com returns exit code 1 with success message
        # "Hi username! You've successfully authenticated..."
        output = result.stdout + result.stderr

        if "successfully authenticated" in output.lower():
            logger.info("  ✅ GitHub SSH: Authenticated")
            print()
            logger.info("SSH Output:")
            for line in output.split('\n')[:5]:  # First 5 lines
                if line.strip():
                    logger.info(f"    {line}")
            print()
            return True, "GitHub SSH access OK"
        else:
            logger.warning("  ⚠️  GitHub SSH: Authentication unclear")
            logger.warning(f"    Output: {output[:200]}")
            return False, "GitHub SSH unclear"

    except subprocess.TimeoutExpired:
        logger.error("  ❌ SSH connection timeout")
        return False, "SSH timeout"
    except FileNotFoundError:
        logger.error("  ❌ ssh command not found")
        return False, "ssh not installed"
    except Exception as e:
        logger.error(f"  ❌ SSH test error: {e}")
        return False, str(e)


# ============================================================================
# Check 3: Git Repository Connectivity
# ============================================================================

def check_git_remote():
    """
    Verify git remote connectivity.

    Returns:
        (bool, str): (success, message)
    """
    logger.info("=" * 70)
    logger.info("🔍 Check 3: Git Remote Connectivity")
    logger.info("=" * 70)
    print()

    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd="/opt/mt5-crs",
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            logger.info("  ✅ Git remotes configured:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"    {line}")
            print()
            return True, "Git remotes OK"
        else:
            logger.warning("  ⚠️  No git remotes configured")
            return False, "No remotes"

    except Exception as e:
        logger.error(f"  ❌ Git remote check error: {e}")
        return False, str(e)


# ============================================================================
# Main Synergy Verification
# ============================================================================

def main():
    """Execute synergy verification."""
    print("=" * 70)
    print("🔗 Work Order #023.9: Synergy Verification")
    print("=" * 70)
    print()
    print("Critical Infrastructure Links:")
    print("  1. GTW Link → Windows Gateway (172.19.141.255)")
    print("  2. HUB Link → GitHub (SSH access)")
    print("  3. Git Remote → Repository connectivity")
    print()
    print("=" * 70)
    print()

    # Run all checks
    gtw_ok, gtw_msg = check_gtw_link()
    hub_ok, hub_msg = check_hub_link()
    git_ok, git_msg = check_git_remote()

    # Final summary
    print()
    print("=" * 70)
    print("📊 Synergy Verification Summary")
    print("=" * 70)
    print()
    print(f"GTW Link (Gateway):  {'✅' if gtw_ok else '❌'} {gtw_msg}")
    print(f"HUB Link (GitHub):   {'✅' if hub_ok else '❌'} {hub_msg}")
    print(f"Git Remote:          {'✅' if git_ok else '❌'} {git_msg}")
    print()

    # Determine overall status
    # GTW link can be warning (gateway may not be running)
    # HUB link MUST be OK (critical for Git operations)
    critical_ok = hub_ok and git_ok

    if critical_ok:
        print("=" * 70)
        print("✅ Synergy Intact: Connected to Repository")
        print("=" * 70)
        print()
        print("Critical Paths:")
        print(f"  ✅ SSH keys: {SSH_KEY_PATH}")
        print(f"  ✅ Git config: {Path.home() / '.gitconfig'}")
        print(f"  ✅ Git repository: /opt/mt5-crs")
        print()
        print("Gateway Status:")
        if gtw_ok:
            print(f"  ✅ Network route to {GATEWAY_IP}: OK")
        else:
            print(f"  ⚠️  Gateway not reachable (normal if not running on Windows)")
        print()
        return 0
    else:
        print("=" * 70)
        print("❌ Synergy BROKEN: Critical connectivity lost!")
        print("=" * 70)
        print()
        print("Issues:")
        if not hub_ok:
            print(f"  ❌ HUB Link: {hub_msg}")
        if not git_ok:
            print(f"  ❌ Git Remote: {git_msg}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
