#!/usr/bin/env python3
"""
Database Connectivity Check Script (Task #040.10)

Verifies PostgreSQL connection and database status.
Protocol v2.2: Infrastructure verification required
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(msg, level="INFO"):
    """Print formatted log message."""
    colors = {"SUCCESS": GREEN, "ERROR": RED, "INFO": CYAN, "HEADER": BLUE}
    prefix = {"SUCCESS": "✅", "ERROR": "❌", "INFO": "ℹ️", "HEADER": "═"}.get(level, "•")
    color = colors.get(level, RESET)
    print(f"{color}{prefix} {msg}{RESET}")


def check_connectivity():
    """Check database connectivity."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}🔗 DATABASE CONNECTIVITY CHECK{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    try:
        import psycopg2

        # Get credentials from environment
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DB")

        log(f"Attempting connection to {host}:{port}...", "INFO")

        # Try to connect
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )

        cursor = conn.cursor()

        # Get server version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        log(f"Connected to database successfully", "SUCCESS")
        print(f"  Version: {version.split(',')[0]}")

        # Count rows in market_data
        cursor.execute("SELECT COUNT(*) FROM market_data")
        row_count = cursor.fetchone()[0]
        log(f"market_data table contains {row_count} rows", "SUCCESS")

        # Get data range
        cursor.execute("""
            SELECT MIN(time) as earliest, MAX(time) as latest
            FROM market_data
        """)
        earliest, latest = cursor.fetchone()
        log(f"Data range: {earliest} to {latest}", "INFO")

        # Count unique symbols
        cursor.execute("""
            SELECT COUNT(DISTINCT symbol) FROM market_data
        """)
        symbol_count = cursor.fetchone()[0]
        log(f"Unique symbols: {symbol_count}", "INFO")

        cursor.close()
        conn.close()

        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{GREEN}✅ DATABASE CONNECTION SUCCESSFUL{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")

        print("Connection Summary:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  User: {user}")
        print(f"  Rows: {row_count:,}")
        print()

        return True

    except ImportError:
        log("psycopg2 not installed", "ERROR")
        return False
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{RED}❌ DATABASE CONNECTION FAILED{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")
        return False


if __name__ == "__main__":
    success = check_connectivity()
    sys.exit(0 if success else 1)
