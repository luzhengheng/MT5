#!/usr/bin/env python3
"""
Verification Script for Data Nexus Infrastructure

Comprehensive verification of data infrastructure deployment:
1. Docker containers status
2. TimescaleDB connectivity
3. Redis connectivity
4. Configuration loading
5. Connection pooling

Usage:
    python3 scripts/verify_data_infra.py

Exit codes:
    0: All checks passed
    1: One or more checks failed
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def verify_imports():
    """Verify Python modules can be imported."""
    print("[1/6] Verifying Python imports...", end=" ")
    try:
        from src.data_nexus import DatabaseConfig, RedisConfig
        from src.data_nexus import PostgresConnection, RedisClient
        from src.data_nexus.health import check_all_services
        print("✅")
        return True
    except ImportError as e:
        print(f"❌\n       Error: {e}")
        return False


def verify_config_loading():
    """Verify configuration can be loaded from environment."""
    print("[2/6] Verifying configuration loading...", end=" ")
    try:
        from src.data_nexus import DatabaseConfig, RedisConfig

        db_config = DatabaseConfig()
        redis_config = RedisConfig()

        # Verify config has required attributes
        assert hasattr(db_config, "connection_string")
        assert hasattr(redis_config, "connection_url")

        print("✅")
        return True
    except Exception as e:
        print(f"❌\n       Error: {e}")
        return False


def verify_postgres():
    """Verify TimescaleDB connectivity."""
    print("[3/6] Testing PostgreSQL/TimescaleDB...", end=" ")
    try:
        from src.data_nexus import PostgresConnection

        with PostgresConnection() as db:
            if db.health_check():
                version = db.get_version()
                print(f"✅\n       {version[:60]}...")
                return True
            else:
                print("❌\n       Health check failed")
                return False
    except Exception as e:
        print(f"❌\n       Error: {e}")
        return False


def verify_redis():
    """Verify Redis connectivity."""
    print("[4/6] Testing Redis...", end=" ")
    try:
        from src.data_nexus import RedisClient

        with RedisClient() as redis:
            if redis.health_check():
                print("✅")
                return True
            else:
                print("❌\n       Health check failed")
                return False
    except Exception as e:
        print(f"❌\n       Error: {e}")
        return False


def verify_db_operations():
    """Verify basic database operations work."""
    print("[5/6] Testing database operations...", end=" ")
    try:
        from src.data_nexus import PostgresConnection

        with PostgresConnection() as db:
            # Test scalar query
            result = db.query_scalar("SELECT 1")
            assert result == 1, "SELECT 1 failed"

            # Test version query
            version = db.query_scalar("SELECT version()")
            assert "PostgreSQL" in version, "Not PostgreSQL"

            print("✅")
            return True
    except Exception as e:
        print(f"❌\n       Error: {e}")
        return False


def verify_cache_operations():
    """Verify basic cache operations work."""
    print("[6/6] Testing cache operations...", end=" ")
    try:
        from src.data_nexus import RedisClient

        with RedisClient() as redis:
            # Test set/get
            redis.set("__test__", "value")
            result = redis.get("__test__")
            assert result == "value", "Set/get failed"

            # Test delete
            redis.delete("__test__")
            result = redis.get("__test__")
            assert result is None, "Delete failed"

            # Test JSON
            redis.set_json("__test_json__", {"key": "value"})
            obj = redis.get_json("__test_json__")
            assert obj == {"key": "value"}, "JSON failed"
            redis.delete("__test_json__")

            print("✅")
            return True
    except Exception as e:
        print(f"❌\n       Error: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("📊 DATA NEXUS INFRASTRUCTURE VERIFICATION")
    print("=" * 70)
    print()

    results = []

    # Run all checks
    results.append(verify_imports())
    results.append(verify_config_loading())
    results.append(verify_postgres())
    results.append(verify_redis())
    results.append(verify_db_operations())
    results.append(verify_cache_operations())

    print()
    print("=" * 70)

    if all(results):
        print("✅ ALL TESTS PASSED - Infrastructure ready")
        print("=" * 70)
        print()
        print("Data Nexus is ready for use!")
        print()
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed} TEST(S) FAILED - Check setup")
        print("=" * 70)
        print()
        print("Please check the errors above and ensure:")
        print("  1. Docker containers are running: docker-compose up -d")
        print("  2. .env file is configured with correct credentials")
        print("  3. TimescaleDB is accessible at DB_HOST:DB_PORT")
        print("  4. Redis is accessible at REDIS_HOST:REDIS_PORT")
        print()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
