#!/usr/bin/env python3
"""
Task #012.03: Initialize EODHD Schema on Existing TimescaleDB
==============================================================

Initialize the market_data_ohlcv hypertable for EODHD data on existing
TimescaleDB instance. Preserves any existing Feast data.

Usage:
    python3 scripts/init_eodhd_db.py
"""

import psycopg2
import sys
from datetime import datetime

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


def print_step(step_num, description):
    """Print step header"""
    print(f"{BLUE}[Step {step_num}]{RESET} {description}")


def connect_to_db(host="localhost", port=5432, user="trader", password="password", db="mt5_crs"):
    """
    Connect to TimescaleDB.

    Args:
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        db: Database name

    Returns:
        Connection object or None if failed
    """
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db
        )
        print(f"   {GREEN}✅ Connected to {host}:{port}/{db}{RESET}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"   {RED}❌ Connection failed: {e}{RESET}")
        return None
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return None


def check_table_exists(conn, table_name):
    """Check if table exists"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            )
            """,
            (table_name,)
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result
    except Exception as e:
        print(f"   {RED}❌ Error checking table: {e}{RESET}")
        return False


def create_market_data_table(conn):
    """
    Create market_data_ohlcv table.

    Args:
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()

        print(f"   Creating table market_data_ohlcv...")

        # Create table
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS market_data_ohlcv (
                time        TIMESTAMPTZ       NOT NULL,
                symbol      TEXT              NOT NULL,
                open        DOUBLE PRECISION  NOT NULL,
                high        DOUBLE PRECISION  NOT NULL,
                low         DOUBLE PRECISION  NOT NULL,
                close       DOUBLE PRECISION  NOT NULL,
                volume      BIGINT            NOT NULL,
                UNIQUE (time, symbol)
            );
        """

        cursor.execute(create_table_sql)
        print(f"   {GREEN}✅ Table created (or already exists){RESET}")

        conn.commit()
        cursor.close()
        return True

    except psycopg2.Error as e:
        print(f"   {RED}❌ Error creating table: {e}{RESET}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return False


def enable_hypertable(conn):
    """
    Enable TimescaleDB hypertable for market_data_ohlcv.

    Args:
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()

        print(f"   Enabling hypertable...")

        # Create hypertable (if_not_exists handles already converted tables)
        create_hypertable_sql = "SELECT create_hypertable('market_data_ohlcv', 'time', if_not_exists => TRUE);"
        cursor.execute(create_hypertable_sql)
        print(f"   {GREEN}✅ Hypertable enabled{RESET}")

        conn.commit()
        cursor.close()
        return True

    except psycopg2.Error as e:
        print(f"   {RED}❌ Error enabling hypertable: {e}{RESET}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return False


def create_indexes(conn):
    """
    Create optimized indexes for time-series queries.

    Args:
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()

        print(f"   Creating indexes...")

        # Index on (symbol, time DESC) for efficient symbol-based queries
        index_sql = """
            CREATE INDEX IF NOT EXISTS ix_symbol_time
            ON market_data_ohlcv (symbol, time DESC);
        """

        cursor.execute(index_sql)
        print(f"   {GREEN}✅ Index created (or already exists){RESET}")

        conn.commit()
        cursor.close()
        return True

    except psycopg2.Error as e:
        print(f"   {RED}❌ Error creating indexes: {e}{RESET}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return False


def verify_schema(conn):
    """
    Verify schema by describing the table.

    Args:
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()

        print(f"   Verifying schema...")

        # Get table info
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'market_data_ohlcv'
            ORDER BY ordinal_position
            """
        )

        columns = cursor.fetchall()

        if not columns:
            print(f"   {RED}❌ Table not found{RESET}")
            return False

        print(f"   {GREEN}✅ Schema verified{RESET}")
        print(f"\n   Column Information:")
        print(f"   {'-' * 70}")
        for col_name, data_type, is_nullable in columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"      {col_name:<15} {data_type:<20} {nullable}")
        print(f"   {'-' * 70}\n")

        cursor.close()
        return True

    except psycopg2.Error as e:
        print(f"   {RED}❌ Error verifying schema: {e}{RESET}")
        return False
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return False


def insert_test_record(conn):
    """
    Insert a test EODHD record to verify functionality.

    Args:
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()

        print(f"   Inserting test record...")

        test_insert_sql = """
            INSERT INTO market_data_ohlcv (time, symbol, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (time, symbol) DO NOTHING;
        """

        # Test data: EURUSD on 2025-12-31 00:00:00 UTC
        test_data = (
            datetime(2025, 12, 31, 0, 0, 0),  # time
            "EURUSD",                          # symbol
            1.0850,                            # open
            1.0860,                            # high
            1.0840,                            # low
            1.0855,                            # close
            1000000                            # volume
        )

        cursor.execute(test_insert_sql, test_data)
        conn.commit()
        print(f"   {GREEN}✅ Test record inserted{RESET}")

        cursor.close()
        return True

    except psycopg2.Error as e:
        print(f"   {YELLOW}⚠️  Test record insert warning: {e}{RESET}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return False


def query_test_record(conn):
    """
    Query the test record to verify data retrieval.

    Args:
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()

        print(f"   Querying test record...")

        query_sql = "SELECT * FROM market_data_ohlcv WHERE symbol = 'EURUSD' LIMIT 1"
        cursor.execute(query_sql)
        result = cursor.fetchone()

        if result:
            time, symbol, open_price, high, low, close, volume = result
            print(f"   {GREEN}✅ Test record retrieved{RESET}")
            print(f"\n   Test Record Data:")
            print(f"   {'-' * 70}")
            print(f"      Time:   {time}")
            print(f"      Symbol: {symbol}")
            print(f"      OHLCV:  {open_price} / {high} / {low} / {close} / {volume}")
            print(f"   {'-' * 70}\n")
        else:
            print(f"   {YELLOW}⚠️  No test record found{RESET}")

        cursor.close()
        return bool(result)

    except psycopg2.Error as e:
        print(f"   {RED}❌ Error querying record: {e}{RESET}")
        return False
    except Exception as e:
        print(f"   {RED}❌ Unexpected error: {e}{RESET}")
        return False


def get_table_row_count(conn, table_name):
    """Get row count for a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except:
        return 0


def print_summary(conn):
    """Print summary of database state"""
    try:
        cursor = conn.cursor()

        print(f"\n   Database Summary:")
        print(f"   {'-' * 70}")

        # Check market_data_ohlcv
        ohlcv_count = get_table_row_count(conn, "market_data_ohlcv")
        print(f"      market_data_ohlcv:  {ohlcv_count} rows")

        # Check for any Feast tables
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name LIKE '%feast%'
            ORDER BY table_name
            """
        )
        feast_tables = cursor.fetchall()

        if feast_tables:
            for (table,) in feast_tables:
                count = get_table_row_count(conn, table)
                print(f"      {table}: {count} rows")

        print(f"   {'-' * 70}\n")
        cursor.close()

    except Exception as e:
        print(f"   {YELLOW}⚠️  Error getting summary: {e}{RESET}")


def main():
    """Main execution function"""
    print_header("Task #012.03: Initialize EODHD Schema on TimescaleDB")

    # Step 1: Connect to database
    print_step(1, "Connecting to TimescaleDB")
    conn = connect_to_db()

    if not conn:
        print(f"\n{RED}❌ Failed to connect to database{RESET}")
        return 1

    # Step 2: Check if table exists
    print_step(2, "Checking if market_data_ohlcv exists")
    table_exists = check_table_exists(conn, "market_data_ohlcv")

    if table_exists:
        print(f"   {YELLOW}⊘ Table already exists{RESET}")
    else:
        print(f"   {YELLOW}→ Table does not exist, creating...{RESET}")

        # Step 3: Create table
        print_step(3, "Creating market_data_ohlcv table")
        if not create_market_data_table(conn):
            print(f"\n{RED}❌ Failed to create table{RESET}")
            conn.close()
            return 1

    # Step 4: Enable hypertable
    print_step(4, "Enabling TimescaleDB hypertable")
    if not enable_hypertable(conn):
        print(f"\n{RED}❌ Failed to enable hypertable{RESET}")
        conn.close()
        return 1

    # Step 5: Create indexes
    print_step(5, "Creating optimized indexes")
    if not create_indexes(conn):
        print(f"\n{RED}❌ Failed to create indexes{RESET}")
        conn.close()
        return 1

    # Step 6: Verify schema
    print_step(6, "Verifying schema")
    if not verify_schema(conn):
        print(f"\n{RED}❌ Failed to verify schema{RESET}")
        conn.close()
        return 1

    # Step 7: Insert test record
    print_step(7, "Inserting test EODHD record")
    insert_test_record(conn)

    # Step 8: Query test record
    print_step(8, "Querying test record")
    query_test_record(conn)

    # Summary
    print_step(9, "Database Summary")
    print_summary(conn)

    # Finalize
    print_header("Schema Initialization Complete")
    print(f"{GREEN}✅ SUCCESS{RESET}")
    print(f"   market_data_ohlcv hypertable initialized")
    print(f"   Ready for EODHD data ingestion")
    print(f"   Previous Feast data preserved")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
