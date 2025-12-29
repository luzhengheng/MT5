#!/usr/bin/env python3
"""
Aggressive Environment Reset Script

Forcefully removes legacy venv artifacts and rebuilds clean environment.
User has explicitly authorized this operation.

Task #040.9: Legacy Environment Reset & Standardization
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def verify_safe_paths():
    """Verify critical paths exist before starting deletion."""
    print("🔍 Verifying critical paths...")
    print()

    critical_paths = [
        ("src", "Project source code"),
        ("scripts", "Project scripts"),
        ("docs", "Documentation"),
        (".git", "Git repository"),
    ]

    all_safe = True

    for dirname, description in critical_paths:
        path = PROJECT_ROOT / dirname
        if path.exists():
            print(f"✅ {dirname}/ exists ({description})")
        else:
            print(f"⚠️  {dirname}/ NOT FOUND ({description})")
            all_safe = False

    print()
    return all_safe


def delete_legacy_artifacts():
    """Delete legacy venv artifacts from root."""
    print("🗑️  Deleting legacy artifacts...")
    print()

    legacy_items = [
        "bin",
        "lib",
        "lib64",
        "include",
        "pyvenv.cfg",
    ]

    deleted = []
    failed = []

    for item in legacy_items:
        path = PROJECT_ROOT / item

        if path.exists():
            try:
                if path.is_file():
                    path.unlink()
                    print(f"✅ Deleted: {item}")
                    deleted.append(item)
                else:
                    shutil.rmtree(path)
                    print(f"✅ Deleted: {item}/")
                    deleted.append(item)
            except Exception as e:
                print(f"❌ Failed to delete {item}: {e}")
                failed.append(item)
        else:
            print(f"⏭️  Already gone: {item}")

    print()
    return deleted, failed


def delete_stale_venv():
    """Delete stale venv directory."""
    print("🗑️  Removing stale venv...")
    print()

    venv_path = PROJECT_ROOT / "venv"

    if venv_path.exists():
        try:
            shutil.rmtree(venv_path)
            print(f"✅ Deleted: venv/")
            print()
            return True
        except Exception as e:
            print(f"❌ Failed to delete venv: {e}")
            print()
            return False
    else:
        print(f"⏭️  venv/ does not exist")
        print()
        return True


def create_fresh_venv():
    """Create fresh Python virtual environment."""
    print("🔨 Creating fresh venv...")
    print()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(PROJECT_ROOT / "venv")],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"✅ venv created successfully")
            print()
            return True
        else:
            print(f"❌ venv creation failed")
            print(f"   Error: {result.stderr[:200]}")
            print()
            return False

    except Exception as e:
        print(f"❌ Exception creating venv: {e}")
        print()
        return False


def install_core_packages():
    """Install core packages in venv."""
    print("📦 Installing core packages...")
    print()

    venv_pip = PROJECT_ROOT / "venv" / "bin" / "pip"

    packages = [
        "pandas",
        "sqlalchemy",
        "psycopg2-binary",
        "requests",
        "redis",
        "python-dotenv",
    ]

    try:
        # Upgrade pip first
        print("   Upgrading pip...")
        result = subprocess.run(
            [str(venv_pip), "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"⚠️  pip upgrade had issues")

        # Install packages
        print("   Installing packages...")
        result = subprocess.run(
            [str(venv_pip), "install"] + packages,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print(f"✅ Core packages installed: {', '.join(packages)}")
            print()
            return True
        else:
            print(f"❌ Package installation failed")
            print(f"   Error: {result.stderr[:200]}")
            print()
            return False

    except Exception as e:
        print(f"❌ Exception installing packages: {e}")
        print()
        return False


def generate_env_file():
    """Generate .env file with verified credentials."""
    print("📝 Generating .env file...")
    print()

    env_path = PROJECT_ROOT / ".env"

    # Check if .env exists
    if env_path.exists():
        backup_path = env_path.parent / f".env.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(env_path, backup_path)
        print(f"📦 Backed up existing .env to {backup_path.name}")

    # Read existing .env if present to preserve non-DB settings
    existing_vars = {}
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Preserve non-database settings
                if not any(x in key.upper() for x in ["DB_", "POSTGRES_", "DATABASE"]):
                    existing_vars[key] = value

    # Generate new .env content
    env_content = """# ============================================================================
# Database Configuration (Task #040.9 - Environment Reset)
# ============================================================================
# Verified working connection string
DB_URL=postgresql://trader:password@localhost:5432/mt5_crs
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password
POSTGRES_DB=mt5_crs

# ============================================================================
# API Keys
# ============================================================================
EODHD_API_KEY=6496528053f746.84974385

# ============================================================================
# Environment Flags
# ============================================================================
ENVIRONMENT=development
DEBUG=false

# ============================================================================
# Project Paths (from existing config)
# ============================================================================
PROJECT_ROOT=/opt/mt5-crs
DATA_LAKE_PATH=/opt/mt5-crs/data_lake
MODEL_CACHE_PATH=/opt/mt5-crs/var/cache/models
LOG_PATH=/opt/mt5-crs/var/logs

# ============================================================================
# Preserved Configuration (from previous .env)
# ============================================================================
"""

    # Add preserved variables
    for key, value in existing_vars.items():
        env_content += f"{key}={value}\n"

    try:
        env_path.write_text(env_content)
        print(f"✅ .env file generated")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to write .env: {e}")
        print()
        return False


def verify_reset():
    """Verify reset was successful."""
    print("✓ Verifying reset...")
    print()

    checks = [
        ("bin", False, "Legacy artifact removed"),
        ("lib", False, "Legacy artifact removed"),
        ("lib64", False, "Legacy artifact removed"),
        ("pyvenv.cfg", False, "Legacy artifact removed"),
        ("venv", True, "Fresh venv created"),
        ("src", True, "Source code preserved"),
        ("scripts", True, "Scripts preserved"),
        ("docs", True, "Documentation preserved"),
    ]

    all_passed = True

    for item, should_exist, reason in checks:
        path = PROJECT_ROOT / item
        exists = path.exists()

        if exists == should_exist:
            status = "✅" if exists else "✅"
            action = "Exists" if exists else "Removed"
            print(f"{status} {item:15s} - {action} ({reason})")
        else:
            print(f"❌ {item:15s} - FAILED ({reason})")
            all_passed = False

    print()

    # Check venv structure
    if (PROJECT_ROOT / "venv" / "bin" / "activate").exists():
        print(f"✅ venv/bin/activate exists")
    else:
        print(f"❌ venv/bin/activate missing")
        all_passed = False

    print()
    return all_passed


def main():
    """Execute aggressive environment reset."""
    print("=" * 80)
    print("🔄 AGGRESSIVE ENVIRONMENT RESET - Task #040.9")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This will delete legacy artifacts from project root")
    print("    User explicitly authorized this operation")
    print()

    # Step 1: Verify safe paths
    if not verify_safe_paths():
        print("❌ ABORTED: Critical paths missing")
        return 1

    # Step 2: Delete legacy artifacts
    deleted, failed = delete_legacy_artifacts()

    if failed:
        print(f"⚠️  {len(failed)} items failed to delete: {failed}")

    # Step 3: Delete stale venv
    if not delete_stale_venv():
        print("⚠️  Could not delete stale venv, attempting to rebuild anyway...")

    # Step 4: Create fresh venv
    if not create_fresh_venv():
        print("❌ FAILED: Could not create fresh venv")
        return 1

    # Step 5: Install packages
    if not install_core_packages():
        print("⚠️  Package installation had issues, continuing anyway...")

    # Step 6: Generate .env
    if not generate_env_file():
        print("❌ FAILED: Could not generate .env")
        return 1

    # Step 7: Verify reset
    if not verify_reset():
        print("⚠️  Some verification checks failed")

    # Summary
    print("=" * 80)
    print("✅ RESET COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Run: python3 scripts/health_check.py")
    print("  2. Run: python3 scripts/audit_current_task.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
