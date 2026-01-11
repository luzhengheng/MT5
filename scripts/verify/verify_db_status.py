#!/usr/bin/env python3
"""
Task #012.03: Verify TimescaleDB Status
========================================

Verify the TimescaleDB schema by printing table row counts and structure.
Shows both EODHD market_data_ohlcv and any existing Feast tables.

Usage:
    python3 scripts/verify_db_status.py
"""

import psycopg2
import sys

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print formatted section header"""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def connect_to_db(host="localhost", port=5432, user="trader", password="password", db="mt5_crs"):
    """Connect to TimescaleDB"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db
        )
        return conn
    except Exception as e:
        print(f"{RED}❌ Connection failed: {e}{RESET}")
        return None


def get_all_tables(conn):
    """Get list of all tables in public schema"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        print(f"{RED}❌ Error getting tables: {e}{RESET}")
        return []


def get_row_count(conn, table_name):
    """Get row count for a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        return 0


def get_table_info(conn, table_name):
    """Get column information for a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,)
        )
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        return []


def check_hypertable_status(conn, table_name):
    """Check if table is a TimescaleDB hypertable"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                h.table_name,
                dimensions.column_name as partition_column,
                dimensions.interval_length
            FROM _timescaledb_catalog.hypertable h
            LEFT JOIN _timescaledb_catalog.dimension dimensions
                ON h.id = dimensions.hypertable_id
            WHERE h.table_name = %s
            """,
            (table_name,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except:
        return False


def main():
    """Main execution function"""
    print_header("TimescaleDB Status Verification")

    # Connect to database
    conn = connect_to_db()
    if not conn:
        return 1

    # Get all tables
    tables = get_all_tables(conn)

    if not tables:
        print(f"{YELLOW}⚠️  No tables found in database{RESET}")
        conn.close()
        return 0

    print(f"{BLUE}Database: mt5_crs{RESET}")
    print(f"{BLUE}Tables Found: {len(tables)}{RESET}\n")

    # Organize tables by category
    ohlcv_tables = [t for t in tables if 'market_data_ohlcv' in t or 'ohlcv' in t]
    feast_tables = [t for t in tables if 'feast' in t.lower()]
    other_tables = [t for t in tables if t not in ohlcv_tables and t not in feast_tables]

    # Display EODHD OHLCV tables
    if ohlcv_tables:
        print(f"{CYAN}━━━ EODHD Market Data Tables ━━━{RESET}")
        for table in ohlcv_tables:
            count = get_row_count(conn, table)
            is_hypertable = check_hypertable_status(conn, table)
            hypertable_marker = f" {GREEN}[Hypertable]{RESET}" if is_hypertable else ""
            print(f"   {GREEN}✓{RESET} {table:<40} {count:>10} rows{hypertable_marker}")

        # Show detailed schema for market_data_ohlcv
        if 'market_data_ohlcv' in ohlcv_tables:
            print(f"\n{CYAN}   Schema: market_data_ohlcv{RESET}")
            columns = get_table_info(conn, 'market_data_ohlcv')
            print(f"   {'-' * 70}")
            for col_name, data_type, is_nullable in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"      {col_name:<20} {data_type:<25} {nullable}")
            print(f"   {'-' * 70}")
        print()

    # Display Feast tables
    if feast_tables:
        print(f"{CYAN}━━━ Feast Feature Store Tables ━━━{RESET}")
        for table in feast_tables:
            count = get_row_count(conn, table)
            is_hypertable = check_hypertable_status(conn, table)
            hypertable_marker = f" {GREEN}[Hypertable]{RESET}" if is_hypertable else ""
            print(f"   {GREEN}✓{RESET} {table:<40} {count:>10} rows{hypertable_marker}")
        print()

    # Display other tables
    if other_tables:
        print(f"{CYAN}━━━ Other Tables ━━━{RESET}")
        for table in other_tables:
            count = get_row_count(conn, table)
            is_hypertable = check_hypertable_status(conn, table)
            hypertable_marker = f" {GREEN}[Hypertable]{RESET}" if is_hypertable else ""
            print(f"   {GREEN}✓{RESET} {table:<40} {count:>10} rows{hypertable_marker}")
        print()

    # Summary
    total_rows = sum(get_row_count(conn, t) for t in tables)
    hypertable_count = sum(1 for t in tables if check_hypertable_status(conn, t))

    print(f"{CYAN}━━━ Summary ━━━{RESET}")
    print(f"   Total Tables:     {len(tables)}")
    print(f"   Hypertables:      {hypertable_count}")
    print(f"   Total Rows:       {total_rows:,}")
    print()

    # Verification
    if 'market_data_ohlcv' in tables:
        is_hypertable = check_hypertable_status(conn, 'market_data_ohlcv')
        count = get_row_count(conn, 'market_data_ohlcv')

        print_header("Verification Result")
        print(f"{GREEN}✅ SUCCESS{RESET}")
        print(f"   market_data_ohlcv table exists: YES")
        print(f"   market_data_ohlcv is hypertable: {'YES' if is_hypertable else 'NO'}")
        print(f"   market_data_ohlcv row count: {count}")
        print(f"   Database ready for EODHD data ingestion")
        print()

        conn.close()
        return 0
    else:
        print_header("Verification Result")
        print(f"{RED}❌ FAILURE{RESET}")
        print(f"   market_data_ohlcv table not found")
        print(f"   Run: python3 scripts/init_eodhd_db.py")
        print()

        conn.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
