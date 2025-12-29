#!/usr/bin/env python3
"""
Aggressive Environment Reset Script - Task #040.9

User-authorized operation to:
1. Delete legacy venv artifacts (bin/, lib/, lib64/, include/, pyvenv.cfg)
2. Rebuild fresh venv
3. Install core packages via Tsinghua mirror
4. Persist verified configuration

Protocol v2.2: Docs-as-Code + Local Storage Only
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def verify_paths():
    """Verify project structure before starting reset."""
    print("🔍 Pre-flight verification...")

    critical = ["src", "scripts", "docs", ".git"]
    for item in critical:
        if not (PROJECT_ROOT / item).exists():
            print(f"❌ CRITICAL: {item}/ not found!")
            return False

    print("✅ Project structure verified")
    return True

def delete_legacy_artifacts():
    """Delete all legacy venv artifacts."""
    print("\n🗑️  Deleting legacy artifacts...")

    targets = ["bin", "lib", "lib64", "include", "pyvenv.cfg", "venv"]

    for target in targets:
        path = PROJECT_ROOT / target
        if path.exists():
            try:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
                print(f"  ✅ Deleted: {target}")
            except Exception as e:
                print(f"  ❌ Failed to delete {target}: {e}")
                return False

    return True

def create_venv():
    """Create fresh virtual environment."""
    print("\n🔨 Creating fresh venv...")

    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(PROJECT_ROOT / "venv")],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("  ✅ venv created")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def install_packages():
    """Install core packages using Tsinghua mirror."""
    print("\n📦 Installing core packages...")

    pip = PROJECT_ROOT / "venv" / "bin" / "pip"
    packages = ["pandas", "sqlalchemy", "psycopg2-binary", "requests", "redis"]
    mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"

    try:
        subprocess.run(
            [str(pip), "install", "-i", mirror] + packages,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
        print(f"  ✅ Installed: {', '.join(packages)}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def write_env():
    """Write .env file with verified credentials."""
    print("\n📝 Writing .env configuration...")

    env_content = """# ============================================================================
# Database Configuration (Task #040.9)
# ============================================================================
DB_URL=postgresql://postgres:password@localhost:5432/data_nexus
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=data_nexus

# ============================================================================
# API Keys
# ============================================================================
EODHD_API_TOKEN=6496528053f746.84974385

# ============================================================================
# Environment Flags
# ============================================================================
ENVIRONMENT=development
DEBUG=false
"""

    try:
        (PROJECT_ROOT / ".env").write_text(env_content)
        print("  ✅ .env written")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def verify_reset():
    """Verify reset was successful."""
    print("\n✓ Verifying reset...")

    checks = [
        ("bin", False),
        ("lib", False),
        ("lib64", False),
        ("pyvenv.cfg", False),
        ("venv", True),
        ("venv/bin/activate", True),
    ]

    for item, should_exist in checks:
        path = PROJECT_ROOT / item
        exists = path.exists()

        if exists == should_exist:
            status = "✓" if exists else "✓"
            print(f"  {status} {item}")
        else:
            print(f"  ✗ {item} (FAILED)")
            return False

    return True

def main():
    """Execute reset workflow."""
    print("=" * 70)
    print("🔄 TASK #040.9: LEGACY ENVIRONMENT RESET")
    print("=" * 70)

    if not verify_paths():
        return 1

    if not delete_legacy_artifacts():
        return 1

    if not create_venv():
        return 1

    if not install_packages():
        return 1

    if not write_env():
        return 1

    if not verify_reset():
        return 1

    print("\n" + "=" * 70)
    print("✅ RESET COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. source venv/bin/activate")
    print("  2. python3 scripts/health_check.py")
    print("  3. python3 scripts/audit_current_task.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
