#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Engineering Engine

Reads raw OHLCV data from TimescaleDB market_data table,
calculates technical indicators using TA-Lib,
and writes features to market_features table.

Task #096: Batch Feature Engineering Engine Construction
Protocol v4.3 (Hub-Native Edition)

Usage:
    # Generate features for single symbol
    python3 feature_engine.py --symbol AAPL --task-id 096

    # Generate features for all symbols
    python3 feature_engine.py --all --task-id 096

    # Incremental mode (only new data)
    python3 feature_engine.py --symbol AAPL --incremental
"""

import os
import argparse
import logging
import psycopg2
import pandas as pd
import talib
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureEngine:
    """Technical feature calculator using TA-Lib"""

    def __init__(self, task_id: Optional[str] = None):
        """Initialize feature engine with database connection"""
        # Load environment
        project_root = Path(__file__).resolve().parent.parent.parent
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

        # Task tracking
        self.task_id = task_id
        if task_id:
            logger.info(f"Task ID: {task_id}")

        # Statistics
        self.stats = {
            'symbols_processed': 0,
            'features_calculated': 0,
            'rows_inserted': 0,
            'errors': 0
        }

    def get_available_symbols(self) -> List[str]:
        """Get list of symbols available in market_data"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()

            cur.execute("""
                SELECT DISTINCT symbol
                FROM market_data
                ORDER BY symbol
            """)
            symbols = [row[0] for row in cur.fetchall()]

            cur.close()
            conn.close()

            logger.info(f"Found {len(symbols)} symbols in market_data")
            return symbols

        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            raise

    def fetch_market_data(self, symbol: str,
                         incremental: bool = False) -> Optional[pd.DataFrame]:
        """
        Fetch raw OHLCV data from market_data table

        Args:
            symbol: Stock symbol
            incremental: If True, only fetch data after last feature timestamp

        Returns:
            DataFrame with columns: [time, open, high, low, close, volume]
        """
        try:
            conn = psycopg2.connect(**self.db_params)

            # Build query
            if incremental:
                # Get last feature timestamp for this symbol
                query = """
                    SELECT time, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = %s
                    AND time > COALESCE(
                        (SELECT MAX(time)
                         FROM market_features
                         WHERE symbol = %s),
                        '1970-01-01'::timestamptz
                    )
                    ORDER BY time
                """
                df = pd.read_sql_query(
                    query, conn, params=(symbol, symbol)
                )
            else:
                # Full backfill
                query = """
                    SELECT time, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = %s
                    ORDER BY time
                """
                df = pd.read_sql_query(query, conn, params=(symbol,))

            conn.close()

            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return None

            logger.info(f"Fetched {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            return None

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators using TA-Lib

        Args:
            df: DataFrame with OHLCV columns

        Returns:
            DataFrame with calculated features
        """
        if df.empty or len(df) < 50:  # Need minimum 50 rows for basic indicators
            logger.warning(f"Insufficient data for feature calculation (need 50+, got {len(df)})")
            return pd.DataFrame()

        if len(df) < 200:
            logger.warning(
                f"Limited data ({len(df)} rows) - "
                f"SMA_200 will have fewer valid values"
            )

        try:
            # Extract price arrays
            high_prices = df['high'].values.astype(float)
            low_prices = df['low'].values.astype(float)
            close_prices = df['close'].values.astype(float)
            volume = df['volume'].values.astype(float)

            # Initialize features dictionary
            features = {
                'time': df['time'].values
            }

            # Momentum Indicators
            features['rsi_14'] = talib.RSI(close_prices, timeperiod=14)

            # Trend Indicators - SMA
            features['sma_20'] = talib.SMA(close_prices, timeperiod=20)
            features['sma_50'] = talib.SMA(close_prices, timeperiod=50)
            features['sma_200'] = talib.SMA(close_prices, timeperiod=200)

            # Trend Indicators - EMA
            features['ema_12'] = talib.EMA(close_prices, timeperiod=12)
            features['ema_26'] = talib.EMA(close_prices, timeperiod=26)

            # Volatility Indicators
            features['atr_14'] = talib.ATR(
                high_prices, low_prices, close_prices, timeperiod=14
            )

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close_prices,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2
            )
            features['bbands_upper'] = bb_upper
            features['bbands_middle'] = bb_middle
            features['bbands_lower'] = bb_lower

            # MACD
            macd, macd_signal, macd_hist = talib.MACD(
                close_prices,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
            features['macd'] = macd
            features['macd_signal'] = macd_signal
            features['macd_hist'] = macd_hist

            # Volume Indicators
            features['obv'] = talib.OBV(close_prices, volume)

            # Create DataFrame
            feature_df = pd.DataFrame(features)

            # Drop rows with NaN (insufficient historical data)
            initial_rows = len(feature_df)
            feature_df = feature_df.dropna()
            dropped_rows = initial_rows - len(feature_df)

            if dropped_rows > 0:
                logger.info(
                    f"Dropped {dropped_rows} rows with NaN values "
                    f"(kept {len(feature_df)} valid rows)"
                )

            logger.info(
                f"Calculated {len(feature_df.columns)-1} features "
                f"for {len(feature_df)} time periods"
            )

            return feature_df

        except Exception as e:
            logger.error(f"Feature calculation failed: {e}")
            return pd.DataFrame()

    def write_features(self, symbol: str, feature_df: pd.DataFrame) -> int:
        """
        Write features to market_features table

        Args:
            symbol: Stock symbol
            feature_df: DataFrame with calculated features

        Returns:
            Number of rows inserted
        """
        if feature_df.empty:
            logger.warning(f"No features to write for {symbol}")
            return 0

        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor()

            # Add symbol column
            feature_df['symbol'] = symbol

            # Reorder columns to match table schema
            columns = [
                'time', 'symbol',
                'rsi_14',
                'sma_20', 'sma_50', 'sma_200',
                'ema_12', 'ema_26',
                'atr_14',
                'bbands_upper', 'bbands_middle', 'bbands_lower',
                'macd', 'macd_signal', 'macd_hist',
                'obv'
            ]

            # Prepare insert query with ON CONFLICT for idempotency
            insert_query = f"""
                INSERT INTO market_features ({', '.join(columns)})
                VALUES ({', '.join(['%s'] * len(columns))})
                ON CONFLICT (time, symbol) DO UPDATE SET
                    rsi_14 = EXCLUDED.rsi_14,
                    sma_20 = EXCLUDED.sma_20,
                    sma_50 = EXCLUDED.sma_50,
                    sma_200 = EXCLUDED.sma_200,
                    ema_12 = EXCLUDED.ema_12,
                    ema_26 = EXCLUDED.ema_26,
                    atr_14 = EXCLUDED.atr_14,
                    bbands_upper = EXCLUDED.bbands_upper,
                    bbands_middle = EXCLUDED.bbands_middle,
                    bbands_lower = EXCLUDED.bbands_lower,
                    macd = EXCLUDED.macd,
                    macd_signal = EXCLUDED.macd_signal,
                    macd_hist = EXCLUDED.macd_hist,
                    obv = EXCLUDED.obv
            """

            # Batch insert
            rows_inserted = 0
            for _, row in feature_df.iterrows():
                values = tuple(row[col] for col in columns)
                cur.execute(insert_query, values)
                rows_inserted += 1

            conn.commit()
            cur.close()
            conn.close()

            logger.info(
                f"[SUCCESS] Inserted {rows_inserted} "
                f"feature rows for {symbol}"
            )
            return rows_inserted

        except Exception as e:
            logger.error(f"Failed to write features for {symbol}: {e}")
            return 0

    def process_symbol(self, symbol: str, incremental: bool = False) -> bool:
        """
        Process single symbol: Fetch -> Calculate -> Write

        Args:
            symbol: Stock symbol
            incremental: If True, only process new data

        Returns:
            True if successful
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing symbol: {symbol}")
        logger.info(f"Mode: {'Incremental' if incremental else 'Full Backfill'}")
        logger.info(f"{'='*60}")

        try:
            # Step 1: Fetch market data
            df = self.fetch_market_data(symbol, incremental)
            if df is None or df.empty:
                logger.warning(f"No data available for {symbol}")
                return False

            # Step 2: Calculate features
            feature_df = self.calculate_features(df)
            if feature_df.empty:
                logger.warning(
                    f"Feature calculation produced no results for {symbol}"
                )
                return False

            # Step 3: Write to database
            rows_inserted = self.write_features(symbol, feature_df)

            # Update statistics
            self.stats['symbols_processed'] += 1
            self.stats['features_calculated'] += len(feature_df.columns) - 1
            self.stats['rows_inserted'] += rows_inserted

            return True

        except Exception as e:
            logger.error(f"Failed to process {symbol}: {e}")
            self.stats['errors'] += 1
            return False

    def process_all_symbols(self, incremental: bool = False):
        """Process all available symbols"""
        symbols = self.get_available_symbols()

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {len(symbols)} symbols")
        logger.info(f"{'='*60}\n")

        for symbol in symbols:
            self.process_symbol(symbol, incremental)

    def print_stats(self):
        """Print processing statistics"""
        logger.info(f"\n{'='*60}")
        logger.info("PROCESSING STATISTICS")
        logger.info(f"{'='*60}")
        logger.info(f"Symbols Processed: {self.stats['symbols_processed']}")
        logger.info(f"Feature Types: {self.stats['features_calculated']}")
        logger.info(f"Total Rows Inserted: {self.stats['rows_inserted']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"{'='*60}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Feature Engineering Engine - Task #096'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        help='Stock symbol to process (e.g., AAPL)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all available symbols'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Only process data after last feature timestamp'
    )
    parser.add_argument(
        '--task-id',
        type=str,
        help='Task ID for tracking'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.symbol and not args.all:
        parser.error("Must specify either --symbol or --all")

    # Initialize engine
    engine = FeatureEngine(task_id=args.task_id)

    # Process
    if args.all:
        engine.process_all_symbols(incremental=args.incremental)
    else:
        engine.process_symbol(args.symbol, incremental=args.incremental)

    # Print statistics
    engine.print_stats()


if __name__ == '__main__':
    main()
