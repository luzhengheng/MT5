#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #068: Feature Tables Initialization
Phase 3 Data Infrastructure - Hot Path Factory with Technical Indicators
Protocol: v4.3 (Zero-Trust Edition)

This script creates the TimescaleDB tables for storing computed technical indicators:
1. Creates 'features' schema if not exists
2. Creates 'technical_indicators' hypertable for wide-format indicator storage
3. Adds indexes for efficient querying
4. Verifies table structure and constraints
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
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
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'mt5_crs')),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'trader')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'changeme_timescale'))
}

MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds


def connect_to_db(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    Connect to PostgreSQL/TimescaleDB with retry logic.

    Args:
        max_retries: Maximum number of connection attempts
        delay: Delay between retries in seconds

    Returns:
        psycopg2.connection object if successful

    Raises:
        SystemExit if connection fails after all retries
    """
    logger.info("=" * 80)
    logger.info("TASK #068: Feature Tables Initialization")
    logger.info("=" * 80)
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
                import time
                time.sleep(delay)
            else:
                logger.error(f"❌ Failed to connect after {max_retries} attempts")
                sys.exit(1)


def create_features_schema(conn):
    """Create 'features' schema if it doesn't exist."""
    logger.info("🔍 Step 1: Creating 'features' Schema...")

    with conn.cursor() as cur:
        try:
            cur.execute("CREATE SCHEMA IF NOT EXISTS features;")
            logger.info("✅ Schema 'features' created (or already exists)")
            return True
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to create schema: {e}")
            return False


def create_technical_indicators_table(conn):
    """
    Create 'features.technical_indicators' hypertable with technical indicator columns.

    This table uses a wide format (one column per indicator) for optimal Feast integration
    and query performance, as opposed to a normalized long format.

    Columns include:
    - time: Timestamp (hypertable primary key)
    - symbol: Trading symbol identifier (e.g., AAPL.US)
    - Trend indicators: SMA, EMA, MACD
    - Momentum indicators: RSI, ROC
    - Volatility indicators: ATR, Bollinger Bands, high/low ratio
    - Volume indicators: Volume-based measures
    """
    logger.info("🔍 Step 2: Creating 'technical_indicators' Hypertable...")

    with conn.cursor() as cur:
        try:
            # Drop table if exists (for development/testing)
            # In production, use ALTER TABLE for backward compatibility
            cur.execute("DROP TABLE IF EXISTS features.technical_indicators CASCADE;")

            # Create the wide-format technical indicators table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS features.technical_indicators (
                    time TIMESTAMPTZ NOT NULL,
                    symbol VARCHAR(20) NOT NULL,

                    -- Trend Features
                    sma_5 NUMERIC(20, 8),
                    sma_10 NUMERIC(20, 8),
                    sma_20 NUMERIC(20, 8),
                    ema_12 NUMERIC(20, 8),
                    ema_26 NUMERIC(20, 8),

                    -- Momentum Features
                    rsi_14 NUMERIC(20, 8),
                    roc_1 NUMERIC(20, 8),
                    roc_5 NUMERIC(20, 8),
                    roc_10 NUMERIC(20, 8),
                    macd NUMERIC(20, 8),
                    macd_signal NUMERIC(20, 8),
                    macd_hist NUMERIC(20, 8),

                    -- Volatility Features
                    atr_14 NUMERIC(20, 8),
                    bb_upper NUMERIC(20, 8),
                    bb_middle NUMERIC(20, 8),
                    bb_lower NUMERIC(20, 8),
                    high_low_ratio NUMERIC(20, 8),
                    close_open_ratio NUMERIC(20, 8),

                    -- Volume Features
                    volume_sma_5 NUMERIC(20, 8),
                    volume_sma_20 NUMERIC(20, 8),
                    volume_change NUMERIC(20, 8),

                    -- Metadata
                    created_at TIMESTAMPTZ DEFAULT NOW(),

                    PRIMARY KEY (time, symbol)
                );
            """)

            logger.info("✅ Table 'features.technical_indicators' created")

            # Convert to TimescaleDB hypertable
            cur.execute("""
                SELECT create_hypertable(
                    'features.technical_indicators',
                    'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '7 days'
                );
            """)

            logger.info("✅ Hypertable 'features.technical_indicators' configured (7-day chunks)")
            return True

        except psycopg2.Error as e:
            logger.error(f"❌ Failed to create hypertable: {e}")
            return False


def create_indexes(conn):
    """Create indexes for efficient feature queries."""
    logger.info("🔍 Step 3: Creating Indexes...")

    indexes = [
        {
            'name': 'idx_technical_indicators_symbol_time',
            'table': 'features.technical_indicators',
            'columns': '(symbol, time DESC)',
            'description': 'For queries by symbol and time'
        },
        {
            'name': 'idx_technical_indicators_symbol_created',
            'table': 'features.technical_indicators',
            'columns': '(symbol, created_at DESC)',
            'description': 'For freshness checks in Feast'
        },
    ]

    with conn.cursor() as cur:
        for idx in indexes:
            try:
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx['name']}
                    ON {idx['table']} {idx['columns']};
                """)
                logger.info(f"✅ Index '{idx['name']}' created - {idx['description']}")
            except psycopg2.Error as e:
                logger.warning(f"⚠️  Failed to create index '{idx['name']}': {e}")


def verify_table_structure(conn):
    """Verify the table structure and columns."""
    logger.info("🔍 Step 4: Verifying Table Structure...")

    with conn.cursor() as cur:
        try:
            # Get table info
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'features' AND table_name = 'technical_indicators'
                ORDER BY ordinal_position;
            """)

            columns = cur.fetchall()

            if not columns:
                logger.error("❌ No columns found in technical_indicators table")
                return False

            logger.info(f"✅ Table has {len(columns)} columns:")

            # Group columns by category
            categories = {
                'Timestamp/Key': ['time', 'symbol'],
                'Trend': ['sma_5', 'sma_10', 'sma_20', 'ema_12', 'ema_26'],
                'Momentum': ['rsi_14', 'roc_1', 'roc_5', 'roc_10', 'macd', 'macd_signal', 'macd_hist'],
                'Volatility': ['atr_14', 'bb_upper', 'bb_middle', 'bb_lower', 'high_low_ratio', 'close_open_ratio'],
                'Volume': ['volume_sma_5', 'volume_sma_20', 'volume_change'],
                'Metadata': ['created_at']
            }

            column_names = [col[0] for col in columns]

            for category, expected_cols in categories.items():
                found_cols = [col for col in expected_cols if col in column_names]
                logger.info(f"   {category}: {len(found_cols)}/{len(expected_cols)} columns")

            # Get row count
            cur.execute("SELECT COUNT(*) FROM features.technical_indicators;")
            row_count = cur.fetchone()[0]
            logger.info(f"✅ Table currently contains {row_count} rows")

            return True

        except psycopg2.Error as e:
            logger.error(f"❌ Failed to verify table: {e}")
            return False


def get_database_stats(conn):
    """Get feature-related database statistics."""
    logger.info("📊 Step 5: Database Statistics...")

    with conn.cursor() as cur:
        try:
            # Features schema size
            cur.execute("""
                SELECT pg_size_pretty(pg_total_relation_size('features.technical_indicators'))
                AS table_size;
            """)
            table_size = cur.fetchone()[0]
            logger.info(f"   Technical indicators table size: {table_size}")

            # Row count by symbol
            cur.execute("""
                SELECT symbol, COUNT(*) as row_count
                FROM features.technical_indicators
                GROUP BY symbol
                ORDER BY row_count DESC
                LIMIT 10;
            """)

            results = cur.fetchall()
            if results:
                logger.info("   Top 10 symbols by row count:")
                for symbol, row_count in results:
                    logger.info(f"      {symbol}: {row_count} rows")

        except psycopg2.Error as e:
            logger.warning(f"⚠️  Failed to get statistics: {e}")


def main():
    """Main execution flow."""
    try:
        # Step 1: Connect to database
        conn = connect_to_db()

        # Step 2: Create features schema
        if not create_features_schema(conn):
            logger.error("🔴 Schema creation failed")
            sys.exit(1)
        logger.info("")

        # Step 3: Create technical indicators hypertable
        if not create_technical_indicators_table(conn):
            logger.error("🔴 Hypertable creation failed")
            sys.exit(1)
        logger.info("")

        # Step 4: Create indexes
        create_indexes(conn)
        logger.info("")

        # Step 5: Verify table structure
        if not verify_table_structure(conn):
            logger.error("🔴 Table verification failed")
            sys.exit(1)
        logger.info("")

        # Step 6: Get statistics
        get_database_stats(conn)
        logger.info("")

        # Success summary
        logger.info("=" * 80)
        logger.info("✅ SUCCESS: Feature tables initialization complete")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Next Steps:")
        logger.info("  1. Compute indicators: python3 scripts/compute_features.py")
        logger.info("  2. Update Feast definitions: Update src/feature_repo/definitions.py")
        logger.info("  3. Apply Feast config: python3 scripts/init_feast.py")
        logger.info("  4. Materialize to Redis: feast materialize-incremental <timestamp>")
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
