#!/usr/bin/env python3
"""
Root Directory Cleanup Script

Safely removes orphaned virtual environment artifacts from project root.
Does NOT touch legitimate project directories like bin/, src/, scripts/.

Task #040.9: Infrastructure Standardization
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def scan_root_for_orphaned_venv():
    """Identify orphaned venv components in project root."""
    print("🔍 Scanning project root for orphaned venv artifacts...")
    print()

    # These are typically orphaned venv artifacts if found in root
    # (NOT including ./bin which might be legitimate project scripts)
    orphaned_patterns = {
        "lib": "Python packages directory (venv artifact)",
        "lib64": "Python packages symlink (venv artifact)",
        "include": "C headers (venv artifact)",
        "pyvenv.cfg": "Venv config file (venv artifact)",
    }

    found_orphans = {}

    for name, description in orphaned_patterns.items():
        path = PROJECT_ROOT / name

        if path.exists():
            if name == "pyvenv.cfg":
                found_orphans[name] = (path, description, "file")
            else:
                found_orphans[name] = (path, description, "directory")

            print(f"⚠️  Found: {name}")
            print(f"   Type: {found_orphans[name][2]}")
            print(f"   Path: {path}")
            print(f"   Description: {description}")
            print()

    if not found_orphans:
        print("✅ No orphaned venv artifacts found in root")
        print()
        return {}

    return found_orphans


def create_archive_directory():
    """Create backup directory for orphaned files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = PROJECT_ROOT / f"_archive_venv_cleanup_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def backup_orphaned_files(orphans, archive_dir):
    """Move orphaned files to archive directory (non-destructive)."""
    print(f"📦 Creating backup in: {archive_dir.name}")
    print()

    backed_up = []

    for name, (path, description, file_type) in orphans.items():
        try:
            target = archive_dir / name

            if file_type == "directory":
                shutil.move(str(path), str(target))
            else:
                shutil.move(str(path), str(target))

            print(f"✅ Backed up: {name}")
            backed_up.append(name)

        except Exception as e:
            print(f"❌ Failed to backup {name}: {e}")

    print()
    return backed_up


def verify_cleanup():
    """Verify that orphaned files are no longer in root."""
    print("✓ Verifying cleanup...")
    print()

    orphan_names = ["lib", "lib64", "include", "pyvenv.cfg"]
    remaining = []

    for name in orphan_names:
        path = PROJECT_ROOT / name
        if path.exists():
            remaining.append(name)
            print(f"❌ Still present: {name}")
        else:
            print(f"✅ Removed: {name}")

    print()

    if remaining:
        print(f"⚠️  Warning: {len(remaining)} items still remain in root")
        return False
    else:
        print("✅ Cleanup verification passed")
        return True


def verify_project_structure():
    """Ensure legitimate project directories are intact."""
    print("✓ Verifying project structure...")
    print()

    critical_dirs = [
        ("venv", "Virtual environment"),
        ("src", "Source code"),
        ("scripts", "Scripts directory"),
        ("docs", "Documentation"),
    ]

    all_intact = True

    for dirname, description in critical_dirs:
        path = PROJECT_ROOT / dirname
        if path.exists() and path.is_dir():
            print(f"✅ {dirname}/ intact ({description})")
        else:
            print(f"❌ {dirname}/ MISSING! ({description})")
            all_intact = False

    print()
    return all_intact


def main():
    """Execute root directory cleanup."""
    print("=" * 80)
    print("🧹 PROJECT ROOT CLEANUP - Task #040.9")
    print("=" * 80)
    print()

    # Step 1: Scan
    orphans = scan_root_for_orphaned_venv()

    if not orphans:
        print("=" * 80)
        print("✅ SUCCESS: Root directory is already clean")
        print("=" * 80)
        print()

        # Still verify structure
        print("Verifying project structure...")
        print()
        verify_project_structure()
        return 0

    # Step 2: Create backup
    archive_dir = create_archive_directory()

    # Step 3: Move files
    backed_up = backup_orphaned_files(orphans, archive_dir)

    if not backed_up:
        print("❌ Failed to backup any files")
        return 1

    # Step 4: Verify cleanup
    cleanup_ok = verify_cleanup()

    # Step 5: Verify project structure
    structure_ok = verify_project_structure()

    # Summary
    print("=" * 80)

    if cleanup_ok and structure_ok:
        print("✅ SUCCESS: Root directory cleaned and verified")
        print()
        print(f"📦 Archive created: {archive_dir.name}")
        print(f"📝 Items backed up: {', '.join(backed_up)}")
        print()
        print("=" * 80)
        return 0
    else:
        print("❌ FAILURE: Cleanup incomplete")
        print()
        if not cleanup_ok:
            print("   - Orphaned files still present")
        if not structure_ok:
            print("   - Project structure compromised")
        print()
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
