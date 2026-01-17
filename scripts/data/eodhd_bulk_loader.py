#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EODHD Historical Data Bulk Loader

Downloads historical market data from EODHD API and loads it into TimescaleDB
using high-performance COPY command for bulk inserts.

Task #095: EODHD Historical Data Cold Path Construction
Protocol v4.3 (Hub-Native Edition)

Usage:
    python3 eodhd_bulk_loader.py --symbol AAPL --days 30 --task-id 095
    python3 eodhd_bulk_loader.py --symbols-file tickers.txt --days 365
"""

import os
import sys
import argparse
import logging
import requests
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from io import StringIO
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EODHDBulkLoader:
    """Bulk loader for EODHD historical data"""

    def __init__(self, task_id: Optional[str] = None):
        """Initialize the loader with environment variables"""
        # Load environment variables
        project_root = Path(__file__).resolve().parent.parent.parent
        env_file = project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)

        # EODHD API configuration
        self.api_token = os.getenv('EODHD_API_TOKEN')
        if not self.api_token:
            raise ValueError("EODHD_API_TOKEN not found in environment")

        self.api_base_url = "https://eodhistoricaldata.com/api"

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
            'rows_inserted': 0,
            'errors': 0
        }

    def fetch_historical_data(self, symbol: str, exchange: str = "US",
                             days: int = 30) -> Optional[pd.DataFrame]:
        """
        Fetch historical EOD data from EODHD API

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            exchange: Exchange code (default: 'US')
            days: Number of days of historical data

        Returns:
            DataFrame with columns: [Date, Open, High, Low, Close, Volume]
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Construct API URL
        url = f"{self.api_base_url}/eod/{symbol}.{exchange}"
        params = {
            'api_token': self.api_token,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'fmt': 'json'
        }

        try:
            logger.info(f"Fetching {symbol}.{exchange} from {start_date.date()} to {end_date.date()}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data:
                logger.warning(f"No data returned for {symbol}.{exchange}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Validate required columns
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in response for {symbol}")
                return None

            # Add symbol column
            df['symbol'] = symbol

            # Rename and reorder columns
            df = df.rename(columns={'date': 'time'})
            df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']]

            # Convert time to datetime
            df['time'] = pd.to_datetime(df['time'])

            logger.info(f"  ✓ Fetched {len(df)} rows for {symbol}")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"  ✗ Failed to fetch {symbol}: {e}")
            self.stats['errors'] += 1
            return None

        except Exception as e:
            logger.error(f"  ✗ Error processing {symbol}: {e}")
            self.stats['errors'] += 1
            return None

    def bulk_insert_data(self, df: pd.DataFrame) -> int:
        """
        Insert data using PostgreSQL COPY command for high performance

        Args:
            df: DataFrame with market data

        Returns:
            Number of rows inserted
        """
        if df is None or df.empty:
            return 0

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            # Convert DataFrame to CSV string in memory
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            csv_buffer.seek(0)

            # Use COPY command for bulk insert
            cursor.copy_from(
                csv_buffer,
                'market_data',
                sep=',',
                columns=['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            )

            conn.commit()
            rows_inserted = len(df)

            cursor.close()
            conn.close()

            logger.info(f"  ✓ [SUCCESS] Inserted {rows_inserted} rows into market_data using COPY")
            return rows_inserted

        except Exception as e:
            logger.error(f"  ✗ Failed to insert data: {e}")
            self.stats['errors'] += 1
            return 0

    def load_symbol(self, symbol: str, days: int = 30) -> bool:
        """
        Load historical data for a single symbol

        Args:
            symbol: Stock symbol
            days: Number of days of historical data

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing symbol: {symbol}")
        logger.info(f"{'='*60}")

        # Fetch data
        df = self.fetch_historical_data(symbol, days=days)

        if df is None:
            return False

        # Insert data
        rows = self.bulk_insert_data(df)

        if rows > 0:
            self.stats['symbols_processed'] += 1
            self.stats['rows_inserted'] += rows
            return True

        return False

    def load_symbols(self, symbols: List[str], days: int = 30) -> None:
        """
        Load historical data for multiple symbols

        Args:
            symbols: List of stock symbols
            days: Number of days of historical data
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"EODHD BULK LOADER - Task #{self.task_id or 'N/A'}")
        logger.info(f"{'='*60}")
        logger.info(f"Symbols to process: {len(symbols)}")
        logger.info(f"Historical days: {days}")
        logger.info(f"{'='*60}\n")

        for symbol in symbols:
            self.load_symbol(symbol, days=days)

        # Print summary
        self.print_summary()

    def load_from_file(self, filepath: str, days: int = 30) -> None:
        """
        Load symbols from a file (one symbol per line)

        Args:
            filepath: Path to file containing symbols
            days: Number of days of historical data
        """
        try:
            with open(filepath, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]

            logger.info(f"Loaded {len(symbols)} symbols from {filepath}")
            self.load_symbols(symbols, days=days)

        except Exception as e:
            logger.error(f"Failed to read symbols file: {e}")
            sys.exit(1)

    def print_summary(self) -> None:
        """Print execution summary"""
        logger.info(f"\n{'='*60}")
        logger.info("EXECUTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Task ID: {self.task_id or 'N/A'}")
        logger.info(f"Symbols processed: {self.stats['symbols_processed']}")
        logger.info(f"Total rows inserted: {self.stats['rows_inserted']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"{'='*60}")

        if self.stats['errors'] > 0:
            logger.warning(f"⚠️  Completed with {self.stats['errors']} errors")
        else:
            logger.info("✅ Completed successfully with no errors")

    def verify_data(self, symbol: str) -> None:
        """
        Verify data was inserted correctly

        Args:
            symbol: Stock symbol to verify
        """
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT time, symbol, close, volume
                FROM market_data
                WHERE symbol = %s
                ORDER BY time DESC
                LIMIT 5;
            """, (symbol,))

            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            if rows:
                logger.info(f"\n{'='*60}")
                logger.info(f"VERIFICATION - Latest {len(rows)} rows for {symbol}")
                logger.info(f"{'='*60}")
                for row in rows:
                    logger.info(f"  {row[0]} | {row[1]} | Close: {row[2]} | Volume: {row[3]}")
                logger.info(f"{'='*60}\n")
            else:
                logger.warning(f"No data found for {symbol}")

        except Exception as e:
            logger.error(f"Verification failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EODHD Historical Data Bulk Loader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load single symbol
  python3 eodhd_bulk_loader.py --symbol AAPL --days 30 --task-id 095

  # Load multiple symbols
  python3 eodhd_bulk_loader.py --symbols AAPL,MSFT,GOOGL --days 90

  # Load from file
  python3 eodhd_bulk_loader.py --symbols-file tickers.txt --days 365 --task-id 095
        """
    )

    parser.add_argument('--symbol', type=str,
                       help='Single stock symbol to load')
    parser.add_argument('--symbols', type=str,
                       help='Comma-separated list of symbols')
    parser.add_argument('--symbols-file', type=str,
                       help='File containing symbols (one per line)')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of historical data (default: 30)')
    parser.add_argument('--task-id', type=str,
                       help='Task ID for tracking (e.g., 095)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify data after loading')

    args = parser.parse_args()

    # Validate arguments
    if not any([args.symbol, args.symbols, args.symbols_file]):
        parser.error("Must specify --symbol, --symbols, or --symbols-file")

    # Initialize loader
    try:
        loader = EODHDBulkLoader(task_id=args.task_id)
    except Exception as e:
        logger.error(f"Failed to initialize loader: {e}")
        sys.exit(1)

    # Load data
    if args.symbol:
        symbols = [args.symbol]
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    elif args.symbols_file:
        loader.load_from_file(args.symbols_file, days=args.days)
        return 0

    loader.load_symbols(symbols, days=args.days)

    # Verify if requested
    if args.verify and symbols:
        loader.verify_data(symbols[0])

    # Exit code based on success
    if loader.stats['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
