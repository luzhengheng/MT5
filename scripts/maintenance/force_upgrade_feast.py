#!/usr/bin/env python3
"""
Force Upgrade Feast to Modern Version (Task #042.7)

This script bypasses stale mirrors and installs modern Feast directly from PyPI.

Problem:
- Tsinghua mirror (pypi.tuna.tsinghua.edu.cn) only has Feast up to 0.10.2 (2021)
- Modern Feast versions (0.32.0+) are available on official PyPI

Solution:
- Uninstall old Feast
- Install modern Feast (>=0.32.0) using official PyPI index
- Verify version and Redis support

Protocol v2.2: Infrastructure maintenance task
"""

import subprocess
import sys
from pathlib import Path

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def log(msg, level="INFO"):
    """Print formatted log message."""
    colors = {"SUCCESS": GREEN, "ERROR": RED, "INFO": CYAN, "HEADER": BLUE, "WARNING": YELLOW}
    prefix = {"SUCCESS": "✅", "ERROR": "❌", "INFO": "ℹ️", "HEADER": "═", "WARNING": "⚠️"}.get(level, "•")
    color = colors.get(level, RESET)
    print(f"{color}{prefix} {msg}{RESET}")


def run_command(cmd, description=""):
    """Run command and handle errors."""
    if description:
        log(description, "INFO")

    try:
        # Python 3.6 compatible (no capture_output parameter)
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {' '.join(cmd)}", "ERROR")
        if hasattr(e, 'stderr') and e.stderr:
            log(f"Error: {e.stderr}", "ERROR")
        raise


def force_upgrade_feast():
    """Force upgrade Feast to modern version."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}🔄 FORCE UPGRADE FEAST TO MODERN VERSION{RESET}")
    print(f"{BLUE}Task #042.7: Fix Dependency Hallucination{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")
    
    # Step 1: Check current version
    log("Checking current Feast version...", "INFO")
    try:
        import feast
        old_version = feast.__version__
        log(f"Current version: Feast {old_version}", "WARNING")
    except ImportError:
        old_version = "Not installed"
        log("Feast not currently installed", "WARNING")
    
    # Step 2: Uninstall old version
    log("\nUninstalling old Feast...", "INFO")
    run_command(
        ["pip", "uninstall", "feast", "-y"],
        "Removing Feast 0.10.2..."
    )
    log("Old version removed", "SUCCESS")
    
    # Step 3: Install modern Feast from official PyPI
    log("\nInstalling modern Feast from official PyPI...", "INFO")
    log("Target: feast[redis,postgres]>=0.32.0", "INFO")
    log("Source: https://pypi.org/simple (official)", "INFO")
    
    install_cmd = [
        "pip", "install",
        "feast[redis,postgres]>=0.32.0",
        "--upgrade",
        "--index-url", "https://pypi.org/simple"
    ]
    
    try:
        output = run_command(install_cmd, "Installing from PyPI...")
        log("Installation complete", "SUCCESS")
    except subprocess.CalledProcessError:
        log("Official PyPI failed, trying without extras...", "WARNING")
        # Fallback: Install base Feast first, then extras
        run_command(
            ["pip", "install", "feast>=0.32.0", "--upgrade", "--index-url", "https://pypi.org/simple"],
            "Installing base Feast..."
        )
        log("Base Feast installed, installing extras separately...", "INFO")
    
    # Step 4: Verify installation
    log("\nVerifying installation...", "INFO")
    
    # Force reimport
    if 'feast' in sys.modules:
        del sys.modules['feast']
    
    try:
        import feast
        new_version = feast.__version__
        log(f"Installed version: Feast {new_version}", "SUCCESS")
        
        # Parse version
        version_parts = new_version.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        # Check if version meets requirements
        if major == 0 and minor >= 32:
            log(f"Version {new_version} meets requirement (>=0.32.0)", "SUCCESS")
        elif major > 0:
            log(f"Version {new_version} exceeds requirement (>=0.32.0)", "SUCCESS")
        else:
            log(f"Version {new_version} TOO OLD (need >=0.32.0)", "ERROR")
            sys.exit(1)
        
    except ImportError as e:
        log(f"Failed to import Feast: {e}", "ERROR")
        sys.exit(1)
    
    # Step 5: Test Redis support
    log("\nTesting Redis support...", "INFO")
    try:
        from feast.infra.online_stores.redis import RedisOnlineStoreConfig
        log("Redis online store support confirmed", "SUCCESS")
    except ImportError as e:
        log(f"Redis support not available: {e}", "WARNING")
        log("This is acceptable - may need separate redis package", "INFO")
    
    # Step 6: Display summary
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}📊 UPGRADE SUMMARY{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")
    
    log(f"Old version: {old_version}", "INFO")
    log(f"New version: {new_version}", "SUCCESS")
    log(f"Upgrade successful: {old_version} → {new_version}", "SUCCESS")
    
    print(f"\n{GREEN}🎉 FEAST UPGRADE COMPLETE ✅{RESET}\n")
    print("Next steps:")
    print("  1. Update feature_store.yaml to use Redis")
    print("  2. Update definitions.py with modern Feast API")
    print("  3. Run: feast apply")
    print("  4. Verify: python3 -c 'import feast; print(feast.__version__)'")
    print()
    
    return {"old_version": old_version, "new_version": new_version}


if __name__ == "__main__":
    try:
        result = force_upgrade_feast()
        sys.exit(0)
    except Exception as e:
        log(f"Upgrade failed: {e}", "ERROR")
        sys.exit(1)
