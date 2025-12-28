#!/usr/bin/env python3
"""
Feast Feature Store Management CLI

Task #041: Feast Feature Store Infrastructure

Wrapper for common Feast operations:
- apply: Register feature definitions
- materialize: Push features to online store (Redis)
- list: Show registered features
- info: Display registry information
- teardown: Remove all Feast artifacts

Usage:
    python3 scripts/manage_features.py apply
    python3 scripts/manage_features.py materialize 2025-01-01 2025-12-29
    python3 scripts/manage_features.py list
    python3 scripts/manage_features.py info
    python3 scripts/manage_features.py teardown
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEATURE_STORE_DIR = PROJECT_ROOT / "src" / "data_nexus" / "features" / "store"


def check_feast_installation():
    """Verify Feast is installed."""
    try:
        result = subprocess.run(
            ["feast", "--help"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    print("❌ Error: Feast not installed")
    print("Install with: pip install 'feast[redis,postgres]'")
    return False


def check_environment():
    """Check required environment variables."""
    required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"⚠️  Warning: Missing environment variables: {missing}")
        print("   Set them in .env file or export them")
        return False
    return True


def apply_features():
    """Register feature definitions with Feast."""
    print("=" * 80)
    print("📋 APPLYING FEATURE DEFINITIONS")
    print("=" * 80)
    print()

    if not FEATURE_STORE_DIR.exists():
        print(f"❌ Error: Feature store directory not found: {FEATURE_STORE_DIR}")
        return 1

    print(f"Feature store directory: {FEATURE_STORE_DIR}")
    print()

    try:
        result = subprocess.run(
            ["feast", "-c", str(FEATURE_STORE_DIR), "apply"],
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            print()
            print("✅ Features applied successfully")
            return 0
        else:
            print()
            print("❌ Failed to apply features")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def materialize_features(from_date: str, to_date: str):
    """
    Materialize features to online store (Redis).

    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    """
    print("=" * 80)
    print("🔄 MATERIALIZING FEATURES TO REDIS")
    print("=" * 80)
    print()

    # Validate dates
    try:
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")
        print(f"Date range: {from_date} to {to_date}")
        print()
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("   Use YYYY-MM-DD format")
        return 1

    try:
        result = subprocess.run(
            [
                "feast",
                "-c", str(FEATURE_STORE_DIR),
                "materialize-incremental",
                from_date,
                to_date
            ],
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            print()
            print("✅ Features materialized successfully")
            return 0
        else:
            print()
            print("❌ Failed to materialize features")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def list_features():
    """List registered features."""
    print("=" * 80)
    print("📊 REGISTERED FEATURES")
    print("=" * 80)
    print()

    try:
        # List entities
        print("Entities:")
        print("-" * 80)
        subprocess.run(
            ["feast", "-c", str(FEATURE_STORE_DIR), "entities", "list"],
            cwd=str(PROJECT_ROOT)
        )
        print()

        # List feature views
        print("Feature Views:")
        print("-" * 80)
        subprocess.run(
            ["feast", "-c", str(FEATURE_STORE_DIR), "feature-views", "list"],
            cwd=str(PROJECT_ROOT)
        )
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def show_info():
    """Display registry information."""
    print("=" * 80)
    print("ℹ️  FEATURE STORE INFO")
    print("=" * 80)
    print()

    registry_path = FEATURE_STORE_DIR / "registry.db"

    if registry_path.exists():
        size_kb = registry_path.stat().st_size / 1024
        print(f"Registry file: {registry_path}")
        print(f"Registry size: {size_kb:.2f} KB")
        print()
    else:
        print("Registry not found. Run 'feast apply' first.")
        print()

    print("Configuration:")
    config_file = FEATURE_STORE_DIR / "feature_store.yaml"
    if config_file.exists():
        print(f"  Config file: {config_file}")
        print()
        with open(config_file) as f:
            print(f.read())
    else:
        print("  Config file not found")

    return 0


def teardown():
    """Remove Feast artifacts."""
    print("=" * 80)
    print("🗑️  TEARDOWN FEAST ARTIFACTS")
    print("=" * 80)
    print()

    registry_path = FEATURE_STORE_DIR / "registry.db"

    if registry_path.exists():
        print(f"Removing registry: {registry_path}")
        registry_path.unlink()
        print("✅ Registry removed")
    else:
        print("ℹ️  No registry file found")

    print()
    print("✅ Teardown complete")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Feast Feature Store Management (Task #041)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply feature definitions
  python3 scripts/manage_features.py apply

  # Materialize features to Redis
  python3 scripts/manage_features.py materialize 2025-01-01 2025-12-29

  # List registered features
  python3 scripts/manage_features.py list

  # Show registry info
  python3 scripts/manage_features.py info

  # Teardown (remove artifacts)
  python3 scripts/manage_features.py teardown
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Apply command
    subparsers.add_parser("apply", help="Register feature definitions")

    # Materialize command
    materialize_parser = subparsers.add_parser(
        "materialize",
        help="Materialize features to online store"
    )
    materialize_parser.add_argument("from_date", help="Start date (YYYY-MM-DD)")
    materialize_parser.add_argument("to_date", help="End date (YYYY-MM-DD)")

    # List command
    subparsers.add_parser("list", help="List registered features")

    # Info command
    subparsers.add_parser("info", help="Show registry information")

    # Teardown command
    subparsers.add_parser("teardown", help="Remove Feast artifacts")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Pre-flight checks
    if not check_feast_installation():
        return 1

    if args.command in ["apply", "materialize"]:
        check_environment()

    # Execute command
    if args.command == "apply":
        return apply_features()

    elif args.command == "materialize":
        return materialize_features(args.from_date, args.to_date)

    elif args.command == "list":
        return list_features()

    elif args.command == "info":
        return show_info()

    elif args.command == "teardown":
        return teardown()

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
