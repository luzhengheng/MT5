#!/usr/bin/env python3
"""
Infrastructure Health Check Script

Verifies database connectivity and reports system health status.
Useful for monitoring, CI/CD, and manual health verification.

Task #040.9: Infrastructure Standardization
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_environment():
    """Load environment variables from .env if present."""
    env_file = PROJECT_ROOT / ".env"

    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)


def get_database_url():
    """Get database URL from environment or use verified fallback."""
    # Try to get from environment
    db_url = os.getenv("DB_URL")

    if db_url:
        return db_url

    # Try to construct from components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    database = os.getenv("POSTGRES_DB", "data_nexus")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def test_database_connection(db_url):
    """Test database connectivity and return result."""
    try:
        from sqlalchemy import create_engine, text

        # Create engine with timeout
        engine = create_engine(db_url, connect_args={"connect_timeout": 3})

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        return True, None
    except Exception as e:
        return False, str(e)


def query_table_counts(db_url):
    """Query row counts from tables."""
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url, connect_args={"connect_timeout": 3})

        counts = {}

        with engine.connect() as conn:
            # Query market_data
            result = conn.execute(text("SELECT COUNT(*) FROM market_data"))
            market_count = result.fetchone()[0]
            counts["market_data"] = market_count

            # Query assets
            result = conn.execute(text("SELECT COUNT(*) FROM assets"))
            assets_count = result.fetchone()[0]
            counts["assets"] = assets_count

        return True, counts
    except Exception as e:
        return False, str(e)


def main():
    """Run infrastructure health check."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "📊 Infrastructure Health Check".center(78) + "║")
    print("║" + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Step 1: Load environment
    load_environment()

    # Step 2: Get database URL
    db_url = get_database_url()

    # Mask password for display
    display_url = db_url
    if "password" in db_url.lower():
        parts = db_url.split(":")
        if len(parts) >= 3:
            # Replace password with masked version
            display_url = db_url.replace(
                db_url.split("@")[0].split(":")[-1],
                "***"
            )

    print(f"🔌 Database: {db_url}")
    print()

    # Step 3: Test connection
    print("Testing database connectivity...")
    connected, error = test_database_connection(db_url)

    if not connected:
        print()
        print("❌ DATABASE CONNECTION FAILED")
        print(f"   Error: {error}")
        print()
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "❌ System Unhealthy".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        return 1

    print("✅ Connection successful")
    print()

    # Step 4: Query row counts
    print("Querying table statistics...")
    success, result = query_table_counts(db_url)

    if not success:
        print()
        print(f"❌ Failed to query tables: {result}")
        print()
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "❌ System Unhealthy".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        return 1

    # Print results
    print()
    print("📈 Table Statistics:")
    print()

    for table, count in result.items():
        print(f"   {table:20s}: {count:>10,} rows")

    print()

    # Final status
    print("=" * 80)
    print()
    print("✅ System Healthy")
    print()
    print("=" * 80)
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        print()
        sys.exit(1)
