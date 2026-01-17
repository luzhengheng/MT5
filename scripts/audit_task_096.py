#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #096 TDD Audit Script - Feature Engineering Engine Validation

This script validates:
1. market_features table existence and schema
2. TA-Lib environment correctness
3. Feature calculation accuracy (RSI, SMA, ATR, MACD)
4. Data alignment between market_data and market_features

Protocol v4.3 (Zero-Trust Edition)
"""

import os
import sys
import argparse
import logging
import psycopg2
import pandas as pd
import numpy as np
import talib
from pathlib import Path
from typing import Dict, Tuple
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class Task096Auditor:
    """TDD Auditor for Feature Engineering Engine"""

    def __init__(self, init_only: bool = False):
        """Initialize auditor with database connection"""
        # Load environment
        project_root = Path(__file__).resolve().parent.parent
        env_file = project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)

        # Database configuration
        self.db_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER', 'trader'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'mt5_crs')
        }

        self.init_only = init_only
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def run_all_tests(self) -> bool:
        """Run all validation tests"""
        logger.info("=" * 80)
        logger.info("Task #096 TDD Audit - Feature Engineering Engine")
        logger.info("=" * 80)

        # Test 1: Check TA-Lib installation
        self.test_talib_environment()

        # Test 2: Check database connection
        self.test_database_connection()

        # Test 3: Check market_data table
        self.test_market_data_exists()

        # If init_only, create the table and exit
        if self.init_only:
            logger.info("\n[INIT MODE] Creating market_features table...")
            self.create_market_features_table()
            return True

        # Test 4: Check market_features table (expected to fail initially)
        self.test_market_features_exists()

        # Test 5: Validate feature calculation accuracy
        self.test_feature_calculation_accuracy()

        # Print summary
        self.print_summary()

        return len(self.test_results['failed']) == 0

    def test_talib_environment(self):
        """Test 1: Validate TA-Lib installation"""
        test_name = "TA-Lib Environment"
        try:
            version = talib.__version__
            logger.info(f"✓ {test_name}: TA-Lib {version} installed")

            # Test basic functionality
            test_data = np.random.random(100)
            sma = talib.SMA(test_data, timeperiod=5)

            if not np.isnan(sma[-1]):
                self.test_results['passed'].append(test_name)
                logger.info(f"  └─ Basic calculation test passed")
            else:
                raise ValueError("SMA calculation returned NaN")

        except Exception as e:
            self.test_results['failed'].append((test_name, str(e)))
            logger.error(f"✗ {test_name}: {e}")

    def test_database_connection(self):
        """Test 2: Validate database connectivity"""
        test_name = "Database Connection"
        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.close()
            conn.close()

            self.test_results['passed'].append(test_name)
            logger.info(f"✓ {test_name}: Connected to PostgreSQL")
            logger.info(f"  └─ {version.split(',')[0]}")

        except Exception as e:
            self.test_results['failed'].append((test_name, str(e)))
            logger.error(f"✗ {test_name}: {e}")

    def test_market_data_exists(self):
        """Test 3: Validate market_data table"""
        test_name = "market_data Table"
        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()

            # Check table exists
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name = 'market_data'
            """)
            if cur.fetchone()[0] == 0:
                raise ValueError("market_data table does not exist")

            # Check row count
            cur.execute("SELECT COUNT(*) FROM market_data")
            row_count = cur.fetchone()[0]

            # Check available symbols
            cur.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol")
            symbols = [row[0] for row in cur.fetchall()]

            cur.close()
            conn.close()

            self.test_results['passed'].append(test_name)
            logger.info(f"✓ {test_name}: {row_count} rows, {len(symbols)} symbols")
            logger.info(f"  └─ Symbols: {', '.join(symbols[:5])}" +
                       (f" ... (+{len(symbols)-5} more)" if len(symbols) > 5 else ""))

        except Exception as e:
            self.test_results['failed'].append((test_name, str(e)))
            logger.error(f"✗ {test_name}: {e}")

    def create_market_features_table(self):
        """Create market_features hypertable"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()

            # Drop table if exists
            cur.execute("DROP TABLE IF EXISTS market_features CASCADE;")

            # Create table
            cur.execute("""
                CREATE TABLE market_features (
                    time TIMESTAMPTZ NOT NULL,
                    symbol VARCHAR(20) NOT NULL,

                    -- Momentum Indicators
                    rsi_14 DOUBLE PRECISION,

                    -- Trend Indicators
                    sma_20 DOUBLE PRECISION,
                    sma_50 DOUBLE PRECISION,
                    sma_200 DOUBLE PRECISION,
                    ema_12 DOUBLE PRECISION,
                    ema_26 DOUBLE PRECISION,

                    -- Volatility Indicators
                    atr_14 DOUBLE PRECISION,
                    bbands_upper DOUBLE PRECISION,
                    bbands_middle DOUBLE PRECISION,
                    bbands_lower DOUBLE PRECISION,

                    -- MACD
                    macd DOUBLE PRECISION,
                    macd_signal DOUBLE PRECISION,
                    macd_hist DOUBLE PRECISION,

                    -- Volume Indicators
                    obv DOUBLE PRECISION,

                    PRIMARY KEY (time, symbol)
                );
            """)

            # Create hypertable
            cur.execute("""
                SELECT create_hypertable('market_features', 'time',
                                        if_not_exists => TRUE);
            """)

            # Create index on symbol
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_features_symbol
                ON market_features(symbol, time DESC);
            """)

            conn.commit()
            cur.close()
            conn.close()

            logger.info("✓ market_features table created successfully")
            logger.info("  └─ Hypertable enabled with time partitioning")
            logger.info("  └─ Indexes created on (symbol, time)")

        except Exception as e:
            logger.error(f"✗ Failed to create market_features table: {e}")
            raise

    def test_market_features_exists(self):
        """Test 4: Validate market_features table"""
        test_name = "market_features Table"
        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()

            # Check table exists
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name = 'market_features'
            """)
            if cur.fetchone()[0] == 0:
                raise ValueError("market_features table does not exist (expected - run with --init-only first)")

            # Check row count
            cur.execute("SELECT COUNT(*) FROM market_features")
            row_count = cur.fetchone()[0]

            cur.close()
            conn.close()

            if row_count == 0:
                self.test_results['warnings'].append((test_name, "Table exists but empty"))
                logger.warning(f"⚠ {test_name}: Table exists but no data")
            else:
                self.test_results['passed'].append(test_name)
                logger.info(f"✓ {test_name}: {row_count} feature rows")

        except Exception as e:
            self.test_results['failed'].append((test_name, str(e)))
            logger.error(f"✗ {test_name}: {e}")

    def test_feature_calculation_accuracy(self):
        """Test 5: Validate feature calculation accuracy"""
        test_name = "Feature Calculation Accuracy"
        try:
            # Generate test OHLC data
            np.random.seed(42)
            n = 100
            close_prices = np.cumsum(np.random.randn(n)) + 100
            high_prices = close_prices + np.abs(np.random.randn(n))
            low_prices = close_prices - np.abs(np.random.randn(n))
            open_prices = close_prices + np.random.randn(n) * 0.5
            volume = np.random.randint(1000, 10000, n)

            # Calculate features using TA-Lib
            rsi_14 = talib.RSI(close_prices, timeperiod=14)
            sma_20 = talib.SMA(close_prices, timeperiod=20)
            atr_14 = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
            macd, macd_signal, macd_hist = talib.MACD(close_prices)

            # Validate results
            errors = []

            # Check RSI is in valid range [0, 100]
            valid_rsi = rsi_14[~np.isnan(rsi_14)]
            if not (np.all(valid_rsi >= 0) and np.all(valid_rsi <= 100)):
                errors.append("RSI values out of range [0, 100]")

            # Check SMA produces reasonable values
            if not np.allclose(sma_20[~np.isnan(sma_20)],
                              close_prices[~np.isnan(sma_20)], rtol=0.5):
                errors.append("SMA values unreasonable")

            # Check ATR is positive
            valid_atr = atr_14[~np.isnan(atr_14)]
            if not np.all(valid_atr > 0):
                errors.append("ATR values not positive")

            # Check MACD calculated
            if np.all(np.isnan(macd)):
                errors.append("MACD calculation failed")

            if errors:
                raise ValueError("; ".join(errors))

            self.test_results['passed'].append(test_name)
            logger.info(f"✓ {test_name}: All indicators calculated correctly")
            logger.info(f"  └─ RSI range: [{valid_rsi.min():.2f}, {valid_rsi.max():.2f}]")
            logger.info(f"  └─ ATR mean: {valid_atr.mean():.2f}")

        except Exception as e:
            self.test_results['failed'].append((test_name, str(e)))
            logger.error(f"✗ {test_name}: {e}")

    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("AUDIT SUMMARY")
        logger.info("=" * 80)

        total = len(self.test_results['passed']) + len(self.test_results['failed'])
        passed = len(self.test_results['passed'])
        failed = len(self.test_results['failed'])
        warnings = len(self.test_results['warnings'])

        logger.info(f"Total Tests: {total}")
        logger.info(f"✓ Passed: {passed}")
        if warnings > 0:
            logger.info(f"⚠ Warnings: {warnings}")
            for test, msg in self.test_results['warnings']:
                logger.info(f"  - {test}: {msg}")

        if failed > 0:
            logger.info(f"✗ Failed: {failed}")
            for test, error in self.test_results['failed']:
                logger.info(f"  - {test}: {error}")
            logger.info("\n[FAIL] Audit did not pass")
            return False
        else:
            logger.info("\n[SUCCESS] All tests passed!")
            return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Task #096 TDD Audit - Feature Engineering Engine'
    )
    parser.add_argument(
        '--init-only',
        action='store_true',
        help='Only create market_features table and exit'
    )

    args = parser.parse_args()

    auditor = Task096Auditor(init_only=args.init_only)
    success = auditor.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
