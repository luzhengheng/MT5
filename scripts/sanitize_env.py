#!/usr/bin/env python3
"""
Work Order #023.9: Safe Environment Purge
==========================================

Surgical cleanup of legacy Python processes and libraries WITHOUT disrupting
critical infrastructure connections.

Safety Constraints (CRITICAL):
1. Process Safety: Terminate ONLY specific Python processes (src/main.py, jupyter, tensorboard)
   - DO NOT use killall python (avoids killing system tools or this agent)
2. File Safety: Preserve vital inter-server connectivity
   - SKIP: ~/.ssh/ (SSH keys for Git/GitHub access)
   - SKIP: ~/.gitconfig (Git configuration)
   - SKIP: /etc/hosts (Network routing to GTW)
3. Port Safety: Release ZMQ ports 5555/5556
   - DO NOT modify iptables or ufw

Protocol: v2.0 (Strict TDD & Safe Operations)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import psutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path("/opt/mt5-crs")

# ============================================================================
# Safety Constraints - CRITICAL PATHS TO PRESERVE
# ============================================================================

PROTECTED_PATHS = [
    Path.home() / ".ssh",           # SSH keys for Git access
    Path.home() / ".gitconfig",     # Git configuration
    Path("/etc/hosts"),             # Network routing
    Path("/etc/network"),           # Network configuration
    Path("/etc/iptables"),          # Firewall rules
]

PROTECTED_PROCESSES = [
    "sshd",                         # SSH daemon
    "systemd",                      # System manager
    "networkd",                     # Network manager
]


# ============================================================================
# Step 1: Safe Process Termination
# ============================================================================

def terminate_safe_processes():
    """
    Terminate ONLY specific Python processes.

    Safety:
        - Targets ONLY: src/main.py, jupyter, tensorboard
        - Skips: This script, system Python processes
        - Preserves: SSH, network, system daemons

    Returns:
        Number of processes terminated
    """
    logger.info("=" * 70)
    logger.info("🔍 Step 1: Safe Process Termination")
    logger.info("=" * 70)

    current_pid = os.getpid()
    terminated_count = 0

    # Target patterns for safe termination
    target_patterns = [
        "src/main.py",
        "jupyter",
        "tensorboard",
        "trading_brain",
    ]

    logger.info("Scanning for target processes...")
    logger.info(f"Current script PID: {current_pid} (will be skipped)")
    logger.info(f"Target patterns: {target_patterns}")
    print()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            pinfo = proc.info
            pid = pinfo['pid']
            cmdline = pinfo.get('cmdline', [])

            # Skip this script
            if pid == current_pid:
                continue

            # Skip protected processes
            if pinfo['name'] in PROTECTED_PROCESSES:
                continue

            # Check if matches target patterns
            cmdline_str = ' '.join(cmdline) if cmdline else ''

            for pattern in target_patterns:
                if pattern in cmdline_str:
                    logger.info(f"  🎯 Found target: PID {pid} - {cmdline_str[:80]}...")

                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                        logger.info(f"     ✅ Terminated PID {pid}")
                        terminated_count += 1
                    except psutil.TimeoutExpired:
                        logger.warning(f"     ⚠️  Timeout, forcing kill PID {pid}")
                        proc.kill()
                        terminated_count += 1
                    except Exception as e:
                        logger.error(f"     ❌ Failed to terminate PID {pid}: {e}")

                    break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    print()
    logger.info(f"✅ Process termination complete: {terminated_count} processes stopped")
    return terminated_count


# ============================================================================
# Step 2: Safe File Cleanup
# ============================================================================

def cleanup_safe_paths():
    """
    Remove/Archive legacy files with strict safety checks.

    Safety:
        - Removes ONLY: venv/, __pycache__, *.pyc, .pytest_cache
        - Preserves: ~/.ssh/, ~/.gitconfig, /etc/hosts
        - Verification: Double-check path before deletion

    Returns:
        Number of items removed
    """
    logger.info("=" * 70)
    logger.info("🔍 Step 2: Safe File Cleanup")
    logger.info("=" * 70)

    removed_count = 0

    # Targets for removal
    cleanup_targets = [
        PROJECT_ROOT / "venv",
        PROJECT_ROOT / ".pytest_cache",
        PROJECT_ROOT / "trading_brain.log",
    ]

    logger.info("Protected paths (WILL BE SKIPPED):")
    for path in PROTECTED_PATHS:
        logger.info(f"  🛡️  {path}")
    print()

    logger.info("Cleanup targets:")
    for target in cleanup_targets:
        if target.exists():
            logger.info(f"  📁 {target}")
        else:
            logger.info(f"  ⏭️  {target} (does not exist)")
    print()

    # Verify safety before deletion
    for target in cleanup_targets:
        # Double-check not in protected paths
        is_protected = any(
            str(target).startswith(str(protected))
            for protected in PROTECTED_PATHS
        )

        if is_protected:
            logger.critical(f"🛡️  PROTECTED: Skipping {target}")
            continue

        if not target.exists():
            continue

        try:
            if target.is_dir():
                logger.info(f"  🗑️  Removing directory: {target}")
                shutil.rmtree(target)
                logger.info(f"     ✅ Removed {target}")
                removed_count += 1
            else:
                logger.info(f"  🗑️  Removing file: {target}")
                target.unlink()
                logger.info(f"     ✅ Removed {target}")
                removed_count += 1
        except Exception as e:
            logger.error(f"     ❌ Failed to remove {target}: {e}")

    # Clean __pycache__ and *.pyc recursively
    logger.info("\n  🧹 Cleaning __pycache__ and *.pyc files...")
    cache_removed = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_path = Path(root) / '__pycache__'
            try:
                shutil.rmtree(pycache_path)
                cache_removed += 1
            except Exception as e:
                logger.error(f"     ❌ Failed to remove {pycache_path}: {e}")

        # Remove *.pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = Path(root) / file
                try:
                    pyc_path.unlink()
                    cache_removed += 1
                except Exception as e:
                    logger.error(f"     ❌ Failed to remove {pyc_path}: {e}")

    logger.info(f"     ✅ Removed {cache_removed} cache files")
    removed_count += cache_removed

    print()
    logger.info(f"✅ File cleanup complete: {removed_count} items removed")
    return removed_count


# ============================================================================
# Step 3: Port Release Verification
# ============================================================================

def verify_port_release():
    """
    Verify ZMQ ports 5555/5556 are released.

    Safety:
        - Check ONLY: Does not modify iptables/ufw
        - Reports: Port usage status

    Returns:
        True if ports are free, False otherwise
    """
    logger.info("=" * 70)
    logger.info("🔍 Step 3: Port Release Verification")
    logger.info("=" * 70)

    target_ports = [5555, 5556]
    ports_free = True

    for port in target_ports:
        port_in_use = False

        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                port_in_use = True
                logger.warning(f"  ⚠️  Port {port} is in use by PID {conn.pid}")
                ports_free = False
                break

        if not port_in_use:
            logger.info(f"  ✅ Port {port} is free")

    print()
    if ports_free:
        logger.info("✅ All ZMQ ports are released")
    else:
        logger.warning("⚠️  Some ports are still in use (may be normal if Gateway is running)")

    return ports_free


# ============================================================================
# Step 4: Connectivity Preservation Verification
# ============================================================================

def verify_connectivity_preservation():
    """
    Verify critical infrastructure connections are intact.

    Safety checks:
        - SSH keys exist (~/.ssh/id_rsa)
        - Git config exists (~/.gitconfig)
        - /etc/hosts exists

    Returns:
        True if all critical paths exist, False otherwise
    """
    logger.info("=" * 70)
    logger.info("🔍 Step 4: Connectivity Preservation Verification")
    logger.info("=" * 70)

    critical_paths = [
        (Path.home() / ".ssh" / "id_rsa", "SSH private key"),
        (Path.home() / ".gitconfig", "Git configuration"),
        (Path("/etc/hosts"), "Network routing table"),
    ]

    all_preserved = True

    for path, description in critical_paths:
        if path.exists():
            logger.info(f"  ✅ {description}: {path}")
        else:
            logger.error(f"  ❌ {description} MISSING: {path}")
            all_preserved = False

    print()
    if all_preserved:
        logger.info("✅ All critical connectivity paths preserved")
    else:
        logger.critical("❌ CRITICAL: Some connectivity paths are missing!")

    return all_preserved


# ============================================================================
# Main Sanitization
# ============================================================================

def main():
    """Execute safe environment purge."""
    print("=" * 70)
    print("🧹 Work Order #023.9: Safe Environment Purge")
    print("=" * 70)
    print()
    print("Safety Constraints:")
    print("  🛡️  Process Safety: Terminate ONLY specific patterns")
    print("  🛡️  File Safety: Preserve SSH/Git/Network configs")
    print("  🛡️  Port Safety: Release ZMQ ports without firewall changes")
    print()
    print("=" * 70)
    print()

    # Execute sanitization steps
    processes_terminated = terminate_safe_processes()
    files_removed = cleanup_safe_paths()
    ports_free = verify_port_release()
    connectivity_ok = verify_connectivity_preservation()

    # Final summary
    print()
    print("=" * 70)
    print("📊 Sanitization Summary")
    print("=" * 70)
    print()
    print(f"Processes terminated: {processes_terminated}")
    print(f"Files/directories removed: {files_removed}")
    print(f"ZMQ ports status: {'✅ Free' if ports_free else '⚠️  In use'}")
    print(f"Connectivity preserved: {'✅ Yes' if connectivity_ok else '❌ NO'}")
    print()

    if not connectivity_ok:
        print("=" * 70)
        print("❌ CRITICAL ERROR: Connectivity NOT preserved!")
        print("=" * 70)
        print()
        print("Some critical infrastructure paths are missing.")
        print("This may indicate a safety constraint violation.")
        print()
        return 1

    print("=" * 70)
    print("✅ Safe Purge Complete")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Install ML stack: python3 scripts/install_ml_stack.py")
    print("  2. Verify synergy: python3 scripts/verify_synergy.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
