#!/usr/bin/env python3
"""
System Diagnostics Report

Generates comprehensive diagnostic report for database, API, and service health.
"""

import os
import sys
import socket
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check_port(host: str, port: int, name: str) -> bool:
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def main():
    """Generate diagnostic report."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "MT5-CRS SYSTEM DIAGNOSTICS".center(78) + "║")
    print("║" + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Environment check
    print("📋 ENVIRONMENT VARIABLES")
    print("-" * 80)

    env_checks = {
        "EODHD_API_KEY": ("EODHD API Key", True),
        "POSTGRES_HOST": ("PostgreSQL Host", False),
        "POSTGRES_PORT": ("PostgreSQL Port", False),
        "POSTGRES_USER": ("PostgreSQL User", True),
        "POSTGRES_PASSWORD": ("PostgreSQL Password", True),
        "POSTGRES_DB": ("PostgreSQL Database", False),
        "REDIS_HOST": ("Redis Host", False),
        "REDIS_PORT": ("Redis Port", False),
    }

    for var, (desc, sensitive) in env_checks.items():
        value = os.getenv(var)
        if value:
            if sensitive:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")

    print()

    # Service check
    print("🔌 SERVICE CONNECTIVITY")
    print("-" * 80)

    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    postgres_ok = check_port(postgres_host, postgres_port, "PostgreSQL")
    redis_ok = check_port(redis_host, redis_port, "Redis")

    status = "✅" if postgres_ok else "❌"
    print(f"{status} PostgreSQL: {postgres_host}:{postgres_port}")

    status = "✅" if redis_ok else "❌"
    print(f"{status} Redis: {redis_host}:{redis_port}")

    print()

    # Database check (if connected)
    if postgres_ok:
        print("📊 DATABASE STATUS")
        print("-" * 80)

        try:
            from dotenv import load_dotenv
            load_dotenv(PROJECT_ROOT / ".env")

            from src.data_nexus.database.connection import PostgresConnection

            conn = PostgresConnection()

            result = conn.query_all("SELECT count(*) FROM market_data")
            market_count = result[0][0] if result else 0

            result = conn.query_all("SELECT count(*) FROM assets")
            assets_count = result[0][0] if result else 0

            print(f"   market_data: {market_count:,} rows")
            print(f"   assets: {assets_count:,} rows")

            if market_count == 0 or assets_count == 0:
                print()
                print("⚠️  WARNING: Empty database detected!")
                print("   Run: python3 scripts/emergency_backfill.py")

        except Exception as e:
            print(f"   ❌ Error querying database: {e}")

        print()

    # Files check
    print("📁 REQUIRED FILES")
    print("-" * 80)

    required_files = [
        ("src/data_nexus/config.py", "Database config"),
        ("src/data_nexus/database/connection.py", "DB connection"),
        ("src/data_nexus/ingestion/bulk_loader.py", "Bulk loader"),
        ("scripts/emergency_backfill.py", "Emergency backfill"),
        ("scripts/manage_features.py", "Feature management"),
        (".env", "Environment file"),
    ]

    for file_path, desc in required_files:
        full_path = PROJECT_ROOT / file_path
        status = "✅" if full_path.exists() else "❌"
        print(f"{status} {file_path} ({desc})")

    print()

    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 80)

    if not postgres_ok:
        print()
        print("PostgreSQL is NOT RUNNING. Start it with:")
        print("  Docker:  docker-compose up -d postgres")
        print("  Local:   systemctl start postgresql")
        print()

    if not os.getenv("POSTGRES_USER"):
        print()
        print("Database credentials not set. Add to .env:")
        print("  POSTGRES_USER=trader")
        print("  POSTGRES_PASSWORD=password")
        print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
