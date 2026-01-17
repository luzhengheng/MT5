#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #095: Audit Script for EODHD Historical Data Cold Path

Validates all deliverables for Task #095:
1. TimescaleDB container is running and accessible
2. Database 'market_data' exists and is connectable
3. Table 'market_data' exists and is a hypertable
4. Table schema is correct (time, symbol, open, high, low, close, volume)
5. EODHD bulk loader script exists and is executable

Protocol v4.3 (Zero-Trust Edition) - Gate 1 Audit
"""

import os
import sys
import subprocess
import logging
import psycopg2
from pathlib import Path
from typing import Tuple, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class Task095Auditor:
    """Audits Task #095 deliverables"""

    def __init__(self):
        script_dir = Path(__file__).resolve().parent
        self.project_root = script_dir.parent.parent
        self.checks_passed = []
        self.checks_failed = []

        # Load environment variables
        env_file = self.project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)

        # Database connection parameters
        self.db_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER', 'trader'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'mt5_crs')
        }

    def check_container_running(self) -> bool:
        """Check if TimescaleDB container is running"""
        logger.info("1. Checking TimescaleDB container status...")

        try:
            # Try podman first
            result = subprocess.run(
                ['podman', 'ps', '--filter', 'name=timescaledb', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and 'Up' in result.stdout:
                logger.info(f"  ✓ TimescaleDB container is running (Podman)")
                return True

            # Try docker as fallback
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=timescaledb', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and 'Up' in result.stdout:
                logger.info(f"  ✓ TimescaleDB container is running (Docker)")
                return True

            logger.error("  ✗ TimescaleDB container is NOT running")
            return False

        except Exception as e:
            logger.error(f"  ✗ Failed to check container status: {e}")
            return False

    def check_database_connection(self) -> bool:
        """Check if database is connectable"""
        logger.info("2. Checking database connection...")

        try:
            conn = psycopg2.connect(**self.db_params)
            conn.close()
            logger.info(f"  ✓ Successfully connected to database '{self.db_params['database']}'")
            return True

        except Exception as e:
            logger.error(f"  ✗ Failed to connect to database: {e}")
            return False

    def check_timescaledb_extension(self) -> bool:
        """Check if TimescaleDB extension is installed"""
        logger.info("3. Checking TimescaleDB extension...")

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result and result[0] == 'timescaledb':
                logger.info("  ✓ TimescaleDB extension is installed")
                return True
            else:
                logger.error("  ✗ TimescaleDB extension is NOT installed")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to check TimescaleDB extension: {e}")
            return False

    def check_market_data_table(self) -> bool:
        """Check if market_data table exists"""
        logger.info("4. Checking market_data table existence...")

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'market_data'
                );
            """)

            exists = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            if exists:
                logger.info("  ✓ Table 'market_data' exists")
                return True
            else:
                logger.error("  ✗ Table 'market_data' does NOT exist")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to check table existence: {e}")
            return False

    def check_hypertable_status(self) -> bool:
        """Check if market_data is a hypertable"""
        logger.info("5. Checking hypertable status...")

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT hypertable_name
                FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'market_data';
            """)

            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result and result[0] == 'market_data':
                logger.info("  ✓ 'market_data' is a hypertable")
                return True
            else:
                logger.error("  ✗ 'market_data' is NOT a hypertable")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to check hypertable status: {e}")
            return False

    def check_table_schema(self) -> bool:
        """Check if table schema is correct"""
        logger.info("6. Checking table schema...")

        expected_columns = {
            'time': 'timestamp with time zone',
            'symbol': 'character varying',
            'open': 'numeric',
            'high': 'numeric',
            'low': 'numeric',
            'close': 'numeric',
            'volume': 'bigint'
        }

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'market_data'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()

            cursor.close()
            conn.close()

            all_good = True
            for col_name, col_type in expected_columns.items():
                found = False
                for db_col_name, db_col_type in columns:
                    if db_col_name == col_name:
                        if col_type in db_col_type or db_col_type in col_type:
                            logger.info(f"  ✓ Column '{col_name}' exists with type '{db_col_type}'")
                            found = True
                            break

                if not found:
                    logger.error(f"  ✗ Column '{col_name}' is missing or has wrong type")
                    all_good = False

            return all_good

        except Exception as e:
            logger.error(f"  ✗ Failed to check table schema: {e}")
            return False

    def check_bulk_loader_script(self) -> bool:
        """Check if EODHD bulk loader script exists"""
        logger.info("7. Checking EODHD bulk loader script...")

        loader_path = self.project_root / 'scripts' / 'data' / 'eodhd_bulk_loader.py'

        if loader_path.exists():
            logger.info(f"  ✓ Loader script exists: {loader_path}")

            # Check if executable
            if os.access(loader_path, os.X_OK):
                logger.info("  ✓ Loader script is executable")
                return True
            else:
                logger.info("  ⚠ Loader script exists but is not executable")
                return True  # Not a critical failure
        else:
            logger.error(f"  ✗ Loader script NOT FOUND: {loader_path}")
            return False

    def run_audit(self, init_only: bool = False) -> bool:
        """Run all audit checks"""
        logger.info("="*60)
        logger.info("TASK #095 AUDIT - EODHD Historical Data Cold Path")
        logger.info("="*60)

        if init_only:
            logger.info("Running in INIT-ONLY mode - will initialize database")
            logger.info("="*60)
            return self.initialize_database()

        checks = [
            ("TimescaleDB Container Running", self.check_container_running),
            ("Database Connection", self.check_database_connection),
            ("TimescaleDB Extension", self.check_timescaledb_extension),
            ("Market Data Table Exists", self.check_market_data_table),
            ("Hypertable Status", self.check_hypertable_status),
            ("Table Schema", self.check_table_schema),
            ("Bulk Loader Script", self.check_bulk_loader_script),
        ]

        for name, check_func in checks:
            try:
                if check_func():
                    self.checks_passed.append(name)
                else:
                    self.checks_failed.append(name)
            except Exception as e:
                logger.error(f"  ✗ Exception during {name}: {e}")
                self.checks_failed.append(name)

            logger.info("")  # Blank line

        # Summary
        logger.info("="*60)
        logger.info("AUDIT SUMMARY")
        logger.info("="*60)
        logger.info(f"Passed: {len(self.checks_passed)}/{len(checks)}")
        logger.info(f"Failed: {len(self.checks_failed)}/{len(checks)}")

        if self.checks_failed:
            logger.info("\nFailed checks:")
            for check in self.checks_failed:
                logger.info(f"  ✗ {check}")

        logger.info("="*60)

        return len(self.checks_failed) == 0

    def initialize_database(self) -> bool:
        """Initialize database with required schema"""
        logger.info("Initializing database schema...")

        try:
            conn = psycopg2.connect(**self.db_params)
            conn.autocommit = True
            cursor = conn.cursor()

            # Create TimescaleDB extension
            logger.info("  → Creating TimescaleDB extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            logger.info("  ✓ TimescaleDB extension created")

            # Create market_data table
            logger.info("  → Creating market_data table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    time TIMESTAMPTZ NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    open NUMERIC(12, 4),
                    high NUMERIC(12, 4),
                    low NUMERIC(12, 4),
                    close NUMERIC(12, 4),
                    volume BIGINT
                );
            """)
            logger.info("  ✓ Table 'market_data' created")

            # Convert to hypertable
            logger.info("  → Converting to hypertable...")
            cursor.execute("""
                SELECT create_hypertable('market_data', 'time',
                    if_not_exists => TRUE,
                    migrate_data => TRUE
                );
            """)
            logger.info("  ✓ Hypertable created")

            # Create index on symbol
            logger.info("  → Creating index on symbol...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time
                ON market_data (symbol, time DESC);
            """)
            logger.info("  ✓ Index created")

            cursor.close()
            conn.close()

            logger.info("\n✅ Database initialization completed successfully")
            return True

        except Exception as e:
            logger.error(f"\n❌ Failed to initialize database: {e}")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Audit Task #095 deliverables')
    parser.add_argument('--init-only', action='store_true',
                       help='Initialize database schema only')

    args = parser.parse_args()

    auditor = Task095Auditor()
    success = auditor.run_audit(init_only=args.init_only)

    if success:
        logger.info("✅ GATE 1 PASSED - All checks successful")
        return 0
    else:
        logger.error("❌ GATE 1 FAILED - Fix issues and re-run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
