#!/usr/bin/env python3
"""
Environment Fix & Cleanup Script

Task #040.9: Infrastructure Integrity & Identity Check

Performs:
1. Root directory cleanup (move orphaned venv files)
2. Virtual environment validation
3. Venv rebuild (if necessary)
4. Core package installation

Usage:
    python3 scripts/maintenance/fix_environment.py
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def print_header():
    """Print cleanup header."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "ENVIRONMENT FIX & CLEANUP".center(78) + "║")
    print("║" + f"Task #040.9 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()


def scan_root_for_orphaned_venv():
    """Scan root directory for orphaned venv components."""
    print("=" * 80)
    print("🔍 SCANNING ROOT DIRECTORY FOR ORPHANED VENV FILES")
    print("=" * 80)
    print()

    suspects = {
        "pyvenv.cfg": "Venv config file",
        "bin": "Python executables (if contains activate)",
        "lib": "Python packages",
        "lib64": "Python packages (64-bit symlink)",
        "include": "Python headers",
    }

    orphaned = []

    for suspect, description in suspects.items():
        suspect_path = PROJECT_ROOT / suspect

        if suspect_path.exists():
            print(f"Found: {suspect} ({description})")

            # Special handling for 'bin' - could be legitimate
            if suspect == "bin":
                activate_path = suspect_path / "activate"
                if activate_path.exists():
                    print(f"  → Contains activate script (likely orphaned venv)")
                    orphaned.append((suspect, suspect_path))
                else:
                    print(f"  → Does NOT contain activate (likely project directory)")
                    print(f"  → KEEPING: {suspect}")
            else:
                # Definitely orphaned if it's lib, lib64, include, or pyvenv.cfg
                print(f"  → ORPHANED VENV COMPONENT")
                orphaned.append((suspect, suspect_path))

            print()

    return orphaned


def backup_orphaned_files(orphaned_list):
    """Move orphaned files to archive directory."""
    if not orphaned_list:
        print("No orphaned files to move.")
        return True

    print("=" * 80)
    print("📦 BACKING UP ORPHANED FILES")
    print("=" * 80)
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = PROJECT_ROOT / f"_archive_orphaned_{timestamp}"

    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created archive directory: {archive_dir}")
        print()

        for name, path in orphaned_list:
            try:
                dest = archive_dir / name
                print(f"Moving: {path.name} → {archive_dir.name}/")
                shutil.move(str(path), str(dest))
                print(f"  ✅ Moved")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                return False

        print()
        print(f"✅ Backup complete: {archive_dir}")
        print()
        return True

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def verify_venv_structure():
    """Verify virtual environment is properly structured."""
    print("=" * 80)
    print("✅ VERIFYING VENV STRUCTURE")
    print("=" * 80)
    print()

    venv_path = PROJECT_ROOT / "venv"

    if not venv_path.exists():
        print(f"❌ venv directory not found: {venv_path}")
        return False

    print(f"venv location: {venv_path}")
    print()

    # Check required components
    required = {
        "bin": "Python executables",
        "lib": "Python packages",
        "pyvenv.cfg": "Configuration",
    }

    all_present = True

    for component, description in required.items():
        comp_path = venv_path / component
        if comp_path.exists():
            print(f"  ✅ {component:15} → {description}")
        else:
            print(f"  ❌ {component:15} → MISSING ({description})")
            all_present = False

    print()

    # Check activate script
    activate = venv_path / "bin" / "activate"
    if activate.exists():
        print(f"✅ Activation script exists: {activate}")
    else:
        print(f"❌ Activation script missing")
        all_present = False

    print()

    return all_present


def rebuild_venv_if_needed():
    """Rebuild venv if it's corrupted."""
    print("=" * 80)
    print("🔨 VENV HEALTH CHECK")
    print("=" * 80)
    print()

    venv_path = PROJECT_ROOT / "venv"

    # Try to use pip
    pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print("⚠️  pip executable not found. Rebuilding venv...")
        print()

        try:
            # Remove broken venv
            print("Removing broken venv...")
            shutil.rmtree(venv_path)

            # Rebuild
            print("Creating new venv...")
            subprocess.run(
                ["python3", "-m", "venv", str(venv_path)],
                check=True,
                cwd=str(PROJECT_ROOT)
            )

            print("✅ Venv rebuilt successfully")
            print()
            return True

        except Exception as e:
            print(f"❌ Rebuild failed: {e}")
            return False

    else:
        # Test pip
        try:
            result = subprocess.run(
                [str(pip_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"✅ {result.stdout.strip()}")
                print()
                return True
            else:
                print(f"⚠️  pip not functional. Rebuilding...")
                shutil.rmtree(venv_path)
                subprocess.run(
                    ["python3", "-m", "venv", str(venv_path)],
                    check=True,
                    cwd=str(PROJECT_ROOT)
                )
                print("✅ Venv rebuilt")
                print()
                return True

        except Exception as e:
            print(f"⚠️  pip check failed: {e}")
            print("Rebuilding venv...")

            try:
                shutil.rmtree(venv_path)
                subprocess.run(
                    ["python3", "-m", "venv", str(venv_path)],
                    check=True,
                    cwd=str(PROJECT_ROOT)
                )
                print("✅ Venv rebuilt successfully")
                print()
                return True
            except Exception as rebuild_error:
                print(f"❌ Rebuild failed: {rebuild_error}")
                return False


def install_core_packages():
    """Install core packages in venv."""
    print("=" * 80)
    print("📦 INSTALLING CORE PACKAGES")
    print("=" * 80)
    print()

    pip_path = PROJECT_ROOT / "venv" / "bin" / "pip"

    if not pip_path.exists():
        print(f"❌ pip not found at {pip_path}")
        return False

    # Core packages
    packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "requests>=2.28.0",
        "redis>=4.0.0",
    ]

    print(f"Installing {len(packages)} core packages...")
    print()

    try:
        # Update pip first
        print("Updating pip...")
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            capture_output=True,
            check=True
        )
        print("  ✅ pip updated")
        print()

        # Install packages
        for package in packages:
            print(f"Installing {package}...")
            try:
                subprocess.run(
                    [str(pip_path), "install", package],
                    capture_output=True,
                    check=True
                )
                print(f"  ✅ {package}")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  {package} (may already be installed)")

        print()
        print("✅ Core packages installed")
        print()
        return True

    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False


def verify_final_state():
    """Verify final environment state."""
    print("=" * 80)
    print("🎯 FINAL STATE VERIFICATION")
    print("=" * 80)
    print()

    venv_path = PROJECT_ROOT / "venv"
    pip_path = venv_path / "bin" / "pip"

    # Check venv exists
    if not venv_path.exists():
        print("❌ venv directory missing")
        return False

    print("✅ venv directory exists")

    # Check root is clean
    root_suspects = ["pyvenv.cfg", "lib", "lib64", "include"]
    found_suspects = [s for s in root_suspects if (PROJECT_ROOT / s).exists()]

    if found_suspects:
        print(f"⚠️  Root still contains: {found_suspects}")
    else:
        print("✅ Root directory clean")

    # Check pip works
    try:
        result = subprocess.run(
            [str(pip_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"❌ pip not functional")
            return False
    except Exception as e:
        print(f"❌ pip check failed: {e}")
        return False

    print()
    print("✅ ENVIRONMENT READY")
    print()

    return True


def main():
    """Main cleanup flow."""
    print_header()

    # Step 1: Scan
    orphaned = scan_root_for_orphaned_venv()

    # Step 2: Backup
    if orphaned:
        if not backup_orphaned_files(orphaned):
            print("❌ Backup failed. Stopping.")
            return 1

    # Step 3: Verify venv
    if not verify_venv_structure():
        print("⚠️  Venv structure incomplete")

    # Step 4: Rebuild if needed
    if not rebuild_venv_if_needed():
        print("❌ Venv rebuild/check failed")
        return 1

    # Step 5: Install packages
    if not install_core_packages():
        print("⚠️  Package installation had issues")

    # Step 6: Final verification
    if verify_final_state():
        print("🎉 CLEANUP COMPLETE - ENVIRONMENT IS READY")
        return 0
    else:
        print("⚠️  Cleanup incomplete - manual review needed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
