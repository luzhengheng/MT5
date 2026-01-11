#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #068: Feature Computation Pipeline
Phase 3 Feature Computation - Compute Technical Indicators from OHLCV
Protocol: v4.3 (Zero-Trust Edition)

This script computes technical indicators from OHLCV data and stores them in TimescaleDB:
1. Reads OHLCV data from market_data.ohlcv_daily
2. Computes technical indicators (SMA, EMA, RSI, ATR, Bollinger Bands, etc.)
3. Stores computed features in features.technical_indicators table
4. Supports batch processing with worker pool for parallelization

Usage:
    python3 scripts/compute_features.py --symbols AAPL.US,MSFT.US --workers 4 --start-date 2024-01-01
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy.indicators import TechnicalIndicators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
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


class FeatureComputationPipeline:
    """
    Pipeline for computing technical indicators and storing them in TimescaleDB.

    Architecture:
    1. Connect to PostgreSQL/TimescaleDB
    2. For each symbol:
       - Fetch OHLCV data from market_data.ohlcv_daily
       - Compute technical indicators using TechnicalIndicators class
       - Bulk insert into features.technical_indicators using COPY protocol
    """

    def __init__(self):
        """Initialize the pipeline with database connection."""
        self.conn = None
        self.indicators = TechnicalIndicators()
        self.stats = {
            'symbols_processed': 0,
            'rows_computed': 0,
            'rows_inserted': 0,
            'errors': []
        }

    def connect_db(self, max_retries: int = 5) -> bool:
        """
        Connect to PostgreSQL database.

        Args:
            max_retries: Maximum connection attempts

        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[{attempt}/{max_retries}] Connecting to PostgreSQL...")
                self.conn = psycopg2.connect(**DB_CONFIG)
                self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                logger.info("✅ Database connection successful")
                return True
            except psycopg2.OperationalError as e:
                logger.warning(f"⚠️  Connection failed: {e}")
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    logger.error(f"❌ Failed to connect after {max_retries} attempts")
                    return False

        return False

    def fetch_ohlcv(self, symbol: str, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch OHLCV data from market_data.ohlcv_daily.

        Args:
            symbol: Trading symbol (e.g., 'AAPL.US')
            start_date: Optional start date (default: 1 year ago)
            end_date: Optional end date (default: today)

        Returns:
            DataFrame with OHLCV data sorted by time
        """
        if not self.conn:
            logger.error("Database connection not established")
            return pd.DataFrame()

        # Set default date range (1 year of data for indicator computation)
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT time, open, high, low, close, volume
                    FROM market_data.ohlcv_daily
                    WHERE symbol = %s
                      AND time >= %s
                      AND time <= %s
                    ORDER BY time ASC;
                """, (symbol, start_date, end_date))

                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                if not rows:
                    logger.warning(f"No OHLCV data found for {symbol}")
                    return pd.DataFrame()

                df = pd.DataFrame(rows, columns=columns)
                logger.info(f"Fetched {len(df)} rows for {symbol}")
                return df

        except psycopg2.Error as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {e}")
            self.stats['errors'].append(f"Fetch error for {symbol}: {e}")
            return pd.DataFrame()

    def compute_indicators(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Compute all technical indicators for OHLCV DataFrame.

        Indicators computed:
        - Trend: SMA(5,10,20), EMA(12,26)
        - Momentum: RSI(14), ROC(1,5,10), MACD
        - Volatility: ATR(14), Bollinger Bands(20)
        - Volume-based: Not in indicators class, will add basic ones

        Args:
            df: OHLCV DataFrame with columns: time, open, high, low, close, volume
            symbol: Symbol name (for logging)

        Returns:
            DataFrame with computed indicator columns
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {symbol}, skipping computation")
            return df

        try:
            # Trend indicators
            df = self.indicators.calculate_sma(df, period=5, price_col='close')
            df = self.indicators.calculate_sma(df, period=10, price_col='close')
            df = self.indicators.calculate_sma(df, period=20, price_col='close')
            df = self.indicators.calculate_ema(df, period=12, price_col='close')
            df = self.indicators.calculate_ema(df, period=26, price_col='close')

            # Momentum indicators
            df = self.indicators.calculate_rsi(df, period=14, price_col='close')

            # Rate of Change (ROC)
            df['roc_1'] = df['close'].pct_change(1)
            df['roc_5'] = df['close'].pct_change(5)
            df['roc_10'] = df['close'].pct_change(10)

            # MACD (simplified version: diff of EMA(26) - EMA(12))
            if 'ema_12' in df.columns and 'ema_26' in df.columns:
                df['macd'] = df['ema_12'] - df['ema_26']
                # MACD signal line (9-period EMA of MACD)
                df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                df['macd_hist'] = df['macd'] - df['macd_signal']

            # Volatility indicators
            df = self.indicators.calculate_atr(df, period=14)
            df = self.indicators.calculate_bollinger_bands(df, period=20, std_dev=2.0)

            # Price ratios
            df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
            df['close_open_ratio'] = (df['close'] - df['open']) / df['open']

            # Volume indicators
            df['volume_sma_5'] = df['volume'].rolling(window=5).mean()
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
            df['volume_change'] = df['volume'].pct_change(1)

            logger.info(f"Computed {len(df)} rows of indicators for {symbol}")
            self.stats['rows_computed'] += len(df)
            return df

        except Exception as e:
            logger.error(f"Error computing indicators for {symbol}: {e}")
            self.stats['errors'].append(f"Computation error for {symbol}: {e}")
            return df

    def insert_features(self, df: pd.DataFrame, symbol: str) -> int:
        """
        Insert computed features into features.technical_indicators using COPY protocol.

        Args:
            df: DataFrame with computed indicators
            symbol: Symbol name (for database insert)

        Returns:
            Number of rows inserted
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {symbol}, skipping insert")
            return 0

        # Select only the columns we want to insert
        feature_columns = [
            'time', 'sma_5', 'sma_10', 'sma_20', 'ema_12', 'ema_26',
            'rsi_14', 'roc_1', 'roc_5', 'roc_10', 'macd', 'macd_signal', 'macd_hist',
            'atr_14', 'bb_upper_20', 'bb_middle_20', 'bb_lower_20',
            'high_low_ratio', 'close_open_ratio',
            'volume_sma_5', 'volume_sma_20', 'volume_change'
        ]

        # Filter to only existing columns
        available_columns = [col for col in feature_columns if col in df.columns]
        df_subset = df[available_columns].copy()

        # Add symbol column
        df_subset['symbol'] = symbol

        # Remove rows with NaN values (from indicator warm-up period)
        df_clean = df_subset.dropna()

        if df_clean.empty:
            logger.warning(f"No valid rows after removing NaN for {symbol}")
            return 0

        try:
            with self.conn.cursor() as cur:
                # Build column list
                cols = ','.join(['symbol'] + available_columns)

                # Use COPY for efficient bulk insert
                with cur.copy(f"""
                    COPY features.technical_indicators ({cols})
                    FROM STDIN
                """) as copy_handle:
                    for _, row in df_clean.iterrows():
                        # Prepare row data with symbol first
                        values = (symbol,) + tuple(row[col] if pd.notna(row[col]) else None
                                                   for col in available_columns)
                        copy_handle.write('\t'.join(str(v) for v in values) + '\n')

                rows_inserted = len(df_clean)
                logger.info(f"Inserted {rows_inserted} rows for {symbol}")
                self.stats['rows_inserted'] += rows_inserted
                return rows_inserted

        except Exception as e:
            logger.error(f"Error inserting features for {symbol}: {e}")
            self.stats['errors'].append(f"Insert error for {symbol}: {e}")
            # Fall back to row-by-row insert
            return self._insert_features_fallback(df_clean, symbol)

    def _insert_features_fallback(self, df: pd.DataFrame, symbol: str) -> int:
        """
        Fallback: Insert features row-by-row (slower but more reliable).

        Args:
            df: DataFrame with computed indicators
            symbol: Symbol name

        Returns:
            Number of rows inserted
        """
        if df.empty:
            return 0

        rows_inserted = 0

        try:
            with self.conn.cursor() as cur:
                for _, row in df.iterrows():
                    # Build dynamic INSERT statement based on available columns
                    cols = ['symbol', 'time'] + [col for col in df.columns if col != 'symbol' and col != 'time']
                    placeholders = ', '.join(['%s'] * len(cols))
                    cols_str = ', '.join(cols)

                    values = [symbol, row['time']] + [
                        row[col] if pd.notna(row[col]) else None
                        for col in df.columns if col != 'symbol' and col != 'time'
                    ]

                    cur.execute(f"""
                        INSERT INTO features.technical_indicators ({cols_str})
                        VALUES ({placeholders})
                        ON CONFLICT (time, symbol) DO UPDATE
                        SET {', '.join([f'{col} = EXCLUDED.{col}' for col in cols if col not in ['time', 'symbol']])}
                    """, values)

                    rows_inserted += 1

            logger.info(f"Inserted {rows_inserted} rows for {symbol} (fallback method)")
            self.stats['rows_inserted'] += rows_inserted
            return rows_inserted

        except Exception as e:
            logger.error(f"Fallback insert also failed for {symbol}: {e}")
            self.stats['errors'].append(f"Fallback insert error for {symbol}: {e}")
            return rows_inserted

    def compute_for_symbol(self, symbol: str, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> bool:
        """
        Compute and insert features for a single symbol.

        Args:
            symbol: Trading symbol
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing {symbol}...")

        # Fetch OHLCV
        df_ohlcv = self.fetch_ohlcv(symbol, start_date, end_date)
        if df_ohlcv.empty:
            return False

        # Compute indicators
        df_with_features = self.compute_indicators(df_ohlcv, symbol)
        if df_with_features.empty:
            return False

        # Insert into database
        rows_inserted = self.insert_features(df_with_features, symbol)
        if rows_inserted == 0:
            return False

        self.stats['symbols_processed'] += 1
        return True

    def compute_batch(self, symbols: List[str], workers: int = 1,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> Dict[str, bool]:
        """
        Compute features for multiple symbols (sequential or parallel).

        Args:
            symbols: List of symbols
            workers: Number of worker threads (1 = sequential)
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary mapping symbol -> success status
        """
        results = {}

        if workers == 1:
            # Sequential processing
            logger.info(f"Processing {len(symbols)} symbols sequentially...")
            for symbol in symbols:
                try:
                    success = self.compute_for_symbol(symbol, start_date, end_date)
                    results[symbol] = success
                except Exception as e:
                    logger.error(f"Exception processing {symbol}: {e}")
                    results[symbol] = False
                    self.stats['errors'].append(f"Exception for {symbol}: {e}")
        else:
            # Parallel processing (process-based)
            logger.info(f"Processing {len(symbols)} symbols with {workers} workers...")
            # Note: For true parallelism with DB, we would need separate connections per worker
            # For now, fall back to sequential
            logger.warning("Parallel processing not fully implemented, using sequential")
            for symbol in symbols:
                try:
                    success = self.compute_for_symbol(symbol, start_date, end_date)
                    results[symbol] = success
                except Exception as e:
                    logger.error(f"Exception processing {symbol}: {e}")
                    results[symbol] = False
                    self.stats['errors'].append(f"Exception for {symbol}: {e}")

        return results

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def print_stats(self):
        """Print execution statistics."""
        logger.info("=" * 80)
        logger.info("EXECUTION STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Symbols processed: {self.stats['symbols_processed']}")
        logger.info(f"Total rows computed: {self.stats['rows_computed']}")
        logger.info(f"Total rows inserted: {self.stats['rows_inserted']}")
        logger.info(f"Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.info("\nError Details:")
            for error in self.stats['errors']:
                logger.error(f"  - {error}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compute technical indicators and store in TimescaleDB'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        default='AAPL.US',
        help='Comma-separated list of symbols (default: AAPL.US)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of worker threads (default: 1)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD) - default: 1 year ago'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD) - default: today'
    )

    args = parser.parse_args()

    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]

    # Parse dates
    start_date = None
    end_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid start date format: {args.start_date}")
            sys.exit(1)

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}")
            sys.exit(1)

    # Create pipeline
    logger.info("=" * 80)
    logger.info("TASK #068: Feature Computation Pipeline")
    logger.info("=" * 80)
    logger.info("")

    pipeline = FeatureComputationPipeline()

    # Connect to database
    if not pipeline.connect_db():
        logger.error("Failed to connect to database")
        sys.exit(1)

    logger.info(f"Processing symbols: {symbols}")
    logger.info(f"Workers: {args.workers}")
    if start_date:
        logger.info(f"Start date: {start_date.date()}")
    if end_date:
        logger.info(f"End date: {end_date.date()}")
    logger.info("")

    # Compute features
    start_time = time.time()
    results = pipeline.compute_batch(symbols, args.workers, start_date, end_date)
    elapsed_time = time.time() - start_time

    # Print results
    logger.info("")
    logger.info("PROCESSING RESULTS:")
    for symbol, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"  {symbol}: {status}")

    # Print statistics
    logger.info("")
    pipeline.print_stats()
    logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
    logger.info("")

    # Cleanup
    pipeline.close()

    # Exit with appropriate code
    if any(results.values()):
        logger.info("✅ Feature computation completed")
        return 0
    else:
        logger.error("❌ Feature computation failed for all symbols")
        return 1


if __name__ == "__main__":
    sys.exit(main())
