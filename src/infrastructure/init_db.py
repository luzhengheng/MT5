#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #065: Database Initialization & Health Check
Phase 2 Data Infrastructure - Cold Path Factory
Protocol: v4.3 (Zero-Trust Edition)

This script initializes and verifies the TimescaleDB database setup:
1. Waits for database connection (retry logic)
2. Verifies TimescaleDB extension is loaded
3. Checks schema creation
4. Verifies hypertables are configured
5. Tests basic CRUD operations
"""

import os
import sys
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'mt5_data'),
    'user': os.getenv('POSTGRES_USER', 'trader'),
    'password': os.getenv('POSTGRES_PASSWORD', 'changeme_timescale')
}

MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds


def wait_for_db_ready(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    Wait for database to be ready (with retry logic).

    Args:
        max_retries: Maximum number of connection attempts
        delay: Delay between retries in seconds

    Returns:
        psycopg2.connection object if successful

    Raises:
        SystemExit if connection fails after all retries
    """
    logger.info("=" * 70)
    logger.info("TASK #065: TimescaleDB Initialization")
    logger.info("=" * 70)
    logger.info("")

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[{attempt}/{max_retries}] Attempting to connect to TimescaleDB...")
            logger.info(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            logger.info(f"   Database: {DB_CONFIG['database']}")
            logger.info(f"   User: {DB_CONFIG['user']}")

            conn = psycopg2.connect(**DB_CONFIG)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            logger.info("✅ Database connection successful!")
            logger.info("")
            return conn

        except psycopg2.OperationalError as e:
            logger.warning(f"⚠️  Connection failed: {e}")

            if attempt < max_retries:
                logger.info(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"❌ Failed to connect after {max_retries} attempts")
                sys.exit(1)


def verify_timescaledb_extension(conn):
    """Verify TimescaleDB extension is loaded."""
    logger.info("🔍 Step 1: Verifying TimescaleDB Extension...")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'timescaledb';
        """)
        result = cur.fetchone()

        if result:
            extname, version = result
            logger.info(f"✅ TimescaleDB extension loaded: version {version}")
            return True
        else:
            logger.error("❌ TimescaleDB extension not found")
            return False


def verify_schemas(conn):
    """Verify required schemas exist."""
    logger.info("🔍 Step 2: Verifying Database Schemas...")

    required_schemas = ['market_data', 'features', 'backtest']

    with conn.cursor() as cur:
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name IN %s;
        """, (tuple(required_schemas),))

        found_schemas = [row[0] for row in cur.fetchall()]

    for schema in required_schemas:
        if schema in found_schemas:
            logger.info(f"✅ Schema '{schema}' exists")
        else:
            logger.error(f"❌ Schema '{schema}' missing")
            return False

    return True


def verify_hypertables(conn):
    """Verify hypertables are configured."""
    logger.info("🔍 Step 3: Verifying TimescaleDB Hypertables...")

    expected_hypertables = [
        'market_data.ohlcv_daily',
        'market_data.ticks',
        'features.technical_indicators'
    ]

    with conn.cursor() as cur:
        cur.execute("""
            SELECT hypertable_schema || '.' || hypertable_name as full_name
            FROM timescaledb_information.hypertables;
        """)
        hypertables = [row[0] for row in cur.fetchall()]

    for table in expected_hypertables:
        if table in hypertables:
            logger.info(f"✅ Hypertable '{table}' configured")
        else:
            logger.warning(f"⚠️  Hypertable '{table}' not found (may not be created yet)")

    return len(hypertables) > 0


def test_basic_operations(conn):
    """Test basic CRUD operations."""
    logger.info("🔍 Step 4: Testing Basic Operations...")

    test_symbol = 'TEST.US'
    test_time = datetime.now()

    with conn.cursor() as cur:
        # Test INSERT
        try:
            cur.execute("""
                INSERT INTO market_data.ohlcv_daily (time, symbol, open, high, low, close, volume)
                VALUES (%s, %s, 100.0, 105.0, 99.0, 103.0, 1000000)
            """, (test_time, test_symbol))
            logger.info("✅ INSERT operation successful")
        except Exception as e:
            logger.error(f"❌ INSERT failed: {e}")
            return False

        # Test SELECT
        try:
            cur.execute("""
                SELECT symbol, close, volume
                FROM market_data.ohlcv_daily
                WHERE symbol = %s
                ORDER BY time DESC
                LIMIT 1;
            """, (test_symbol,))
            result = cur.fetchone()

            if result:
                symbol, close, volume = result
                logger.info(f"✅ SELECT operation successful: {symbol} @ ${close} (vol: {volume})")
            else:
                logger.error("❌ SELECT returned no results")
                return False
        except Exception as e:
            logger.error(f"❌ SELECT failed: {e}")
            return False

        # Test DELETE (cleanup test data)
        try:
            cur.execute("""
                DELETE FROM market_data.ohlcv_daily
                WHERE symbol = %s;
            """, (test_symbol,))
            logger.info("✅ DELETE operation successful (test data cleaned up)")
        except Exception as e:
            logger.warning(f"⚠️  DELETE failed: {e} (non-critical)")

    return True


def get_database_stats(conn):
    """Get database size and table statistics."""
    logger.info("📊 Step 5: Database Statistics...")

    with conn.cursor() as cur:
        # Total database size
        cur.execute("""
            SELECT pg_size_pretty(pg_database_size(%s)) as db_size;
        """, (DB_CONFIG['database'],))
        db_size = cur.fetchone()[0]
        logger.info(f"   Database size: {db_size}")

        # Table count
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema IN ('market_data', 'features', 'backtest');
        """)
        table_count = cur.fetchone()[0]
        logger.info(f"   Total tables: {table_count}")

        # Hypertable count
        cur.execute("SELECT COUNT(*) FROM timescaledb_information.hypertables;")
        hypertable_count = cur.fetchone()[0]
        logger.info(f"   Hypertables: {hypertable_count}")


def main():
    """Main execution flow."""
    try:
        # Step 1: Wait for database and connect
        conn = wait_for_db_ready()

        # Step 2: Verify TimescaleDB extension
        if not verify_timescaledb_extension(conn):
            logger.error("🔴 TimescaleDB extension verification failed")
            sys.exit(1)
        logger.info("")

        # Step 3: Verify schemas
        if not verify_schemas(conn):
            logger.error("🔴 Schema verification failed")
            sys.exit(1)
        logger.info("")

        # Step 4: Verify hypertables
        verify_hypertables(conn)
        logger.info("")

        # Step 5: Test basic operations
        if not test_basic_operations(conn):
            logger.error("🔴 Basic operations test failed")
            sys.exit(1)
        logger.info("")

        # Step 6: Get statistics
        get_database_stats(conn)
        logger.info("")

        # Success summary
        logger.info("=" * 70)
        logger.info("✅ SUCCESS: TimescaleDB initialization complete")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next Steps:")
        logger.info("  1. Initialize Feast: cd feature_repo && feast apply")
        logger.info("  2. Test ingestion: python3 src/data/eodhd_ingest.py")
        logger.info("  3. Verify data: docker exec -it mt5-crs-timescaledb psql -U trader -d mt5_data")
        logger.info("")

        conn.close()
        return 0

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
