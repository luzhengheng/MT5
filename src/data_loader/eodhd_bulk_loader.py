#!/usr/bin/env python3
"""
Task #012.04: EODHD Bulk Data Ingestion Pipeline
=================================================

Implements the "Cold Path" ingestion logic to download history from EODHD API
and bulk-insert into TimescaleDB using asyncpg COPY for performance.

This module provides:
1. EODHDBulkLoader: Main class for data fetching and ingestion
2. fetch_symbol_history(): Fetch OHLCV history from EODHD API
3. bulk_insert(): Bulk insert into market_data_ohlcv using COPY

Protocol: v2.2 (Async + Bulk COPY)
"""

import os
import sys
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from pathlib import Path

import asyncpg
from src.data_loader.eodhd_fetcher import EODHDFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


class EODHDBulkLoader:
    """
    Bulk data loader for EODHD market data into TimescaleDB.

    Provides efficient "cold path" historical data ingestion using:
    - EODHD API for data fetching
    - asyncpg for async database operations
    - COPY command for bulk insertion (much faster than INSERT)
    """

    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_user: str = "trader",
        db_password: str = "password",
        db_name: str = "mt5_crs",
        api_key: Optional[str] = None
    ):
        """
        Initialize EODHD bulk loader.

        Args:
            db_host: TimescaleDB host
            db_port: TimescaleDB port
            db_user: Database user
            db_password: Database password
            db_name: Database name
            api_key: EODHD API key (defaults to EODHD_API_TOKEN env var)
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name

        # Initialize EODHD fetcher
        self.fetcher = EODHDFetcher(api_key=api_key)

        # Connection pool (created on demand)
        self.pool: Optional[asyncpg.Pool] = None

        logger.info(f"{CYAN}EODHDBulkLoader initialized{RESET}")
        logger.info(f"  Database: {db_user}@{db_host}:{db_port}/{db_name}")

    async def connect_db(self) -> asyncpg.Pool:
        """Create asyncpg connection pool to TimescaleDB"""
        if self.pool is not None:
            return self.pool

        logger.info(f"Connecting to TimescaleDB...")

        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"{GREEN}✅ Connected to TimescaleDB{RESET}")
            return self.pool
        except Exception as e:
            logger.error(f"{RED}❌ Connection failed: {e}{RESET}")
            raise

    async def disconnect_db(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info(f"Disconnected from TimescaleDB")

    def fetch_symbol_history(
        self,
        symbol: str,
        exchange: str = "FOREX",
        from_date: str = "1990-01-01",
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from EODHD API.

        Args:
            symbol: Symbol name (e.g., 'EURUSD', 'XAUUSD')
            exchange: Exchange code (FOREX, COMMODITY, etc.)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume
            Cleaned and ready for insertion.
        """
        logger.info(f"{BLUE}[Fetch]{RESET} {symbol} from {from_date} to {to_date or 'today'}")

        if to_date is None:
            to_date = datetime.now().strftime("%Y-%m-%d")

        # Fetch using existing fetcher (handles API, caching, etc.)
        df = self.fetcher.fetch_history(
            symbol=symbol,
            period="d",  # Daily data
            from_date=from_date,
            to_date=to_date
        )

        # Clean data
        df = self._clean_dataframe(df, symbol)

        logger.info(f"{GREEN}✅ Fetched {len(df)} rows for {symbol}{RESET}")
        return df

    def _clean_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Clean OHLCV data for insertion into database.

        Args:
            df: Raw OHLCV DataFrame
            symbol: Trading symbol

        Returns:
            Cleaned DataFrame with proper types and columns
        """
        # Rename columns to match database schema
        df = df.rename(columns={
            'Date': 'time',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        # Ensure time is datetime and convert to UTC
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], utc=True)

        # Add symbol column
        df['symbol'] = symbol

        # Select and order columns to match database schema
        df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']]

        # Handle missing values
        df = df.dropna(subset=['time', 'symbol', 'open', 'close'])

        # Ensure numeric columns are float64
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Ensure volume is int64
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').astype('int64')

        logger.info(f"  Cleaned data: {len(df)} rows, {df.memory_usage().sum() / 1024 / 1024:.2f} MB")

        return df

    async def bulk_insert(
        self,
        df: pd.DataFrame,
        table_name: str = "market_data_ohlcv",
        batch_size: int = 5000
    ) -> Tuple[int, float]:
        """
        Bulk insert DataFrame into TimescaleDB using asyncpg COPY.

        Uses COPY protocol for performance (much faster than INSERT).

        Args:
            df: DataFrame with columns: time, symbol, open, high, low, close, volume
            table_name: Target table name
            batch_size: Batch size for COPY operations

        Returns:
            Tuple: (rows_inserted, seconds_elapsed)

        Raises:
            asyncpg.Error: If database operation fails
        """
        pool = await self.connect_db()

        logger.info(f"{BLUE}[Insert]{RESET} {len(df)} rows into {table_name}...")

        start_time = asyncio.get_event_loop().time()

        try:
            async with pool.acquire() as conn:
                # Prepare data for COPY
                records = [
                    (row['time'], row['symbol'], row['open'], row['high'],
                     row['low'], row['close'], int(row['volume']))
                    for _, row in df.iterrows()
                ]

                # Split into batches
                total_inserted = 0
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]

                    try:
                        # Use COPY for bulk insertion
                        inserted = await conn.copy_records_to_table(
                            table_name,
                            records=batch,
                            columns=['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']
                        )

                        total_inserted += len(batch)
                        percent = (total_inserted / len(records)) * 100
                        logger.info(f"  Progress: {total_inserted}/{len(records)} ({percent:.1f}%)")

                    except asyncpg.UniqueViolationError as e:
                        # Handle duplicate records (ignore)
                        logger.warning(f"  Duplicate records in batch {i//batch_size + 1}, skipping")
                        continue

                    except Exception as e:
                        logger.error(f"{RED}❌ Error in batch {i//batch_size + 1}: {e}{RESET}")
                        raise

                elapsed = asyncio.get_event_loop().time() - start_time
                rate = total_inserted / elapsed if elapsed > 0 else 0

                logger.info(f"{GREEN}✅ Inserted {total_inserted} rows in {elapsed:.2f}s ({rate:.0f} rows/sec){RESET}")

                return total_inserted, elapsed

        except Exception as e:
            logger.error(f"{RED}❌ Bulk insert failed: {e}{RESET}")
            raise

    async def ingest_symbol(
        self,
        symbol: str,
        exchange: str = "FOREX",
        from_date: str = "1990-01-01",
        to_date: Optional[str] = None
    ) -> Tuple[int, float]:
        """
        Complete ingestion pipeline: fetch + clean + insert.

        Args:
            symbol: Symbol name
            exchange: Exchange code
            from_date: Start date
            to_date: End date

        Returns:
            Tuple: (rows_inserted, seconds_elapsed)
        """
        logger.info(f"{CYAN}{'=' * 80}{RESET}")
        logger.info(f"{CYAN}Ingesting {symbol} ({exchange}){RESET}")
        logger.info(f"{CYAN}{'=' * 80}{RESET}")

        # Step 1: Fetch data from EODHD API
        df = self.fetch_symbol_history(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date
        )

        # Step 2: Insert into database
        rows_inserted, elapsed = await self.bulk_insert(df)

        logger.info(f"{CYAN}{'=' * 80}{RESET}")
        logger.info(f"{GREEN}✅ Ingestion complete{RESET}")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Rows inserted: {rows_inserted}")
        logger.info(f"  Time elapsed: {elapsed:.2f}s")
        logger.info(f"  Rate: {rows_inserted/elapsed:.0f} rows/sec")
        logger.info(f"{CYAN}{'=' * 80}{RESET}\n")

        return rows_inserted, elapsed


async def main():
    """Example usage"""
    loader = EODHDBulkLoader()

    try:
        # Ingest EURUSD historical data
        rows, elapsed = await loader.ingest_symbol(
            symbol="EURUSD",
            exchange="FOREX",
            from_date="2015-01-01"
        )

    finally:
        await loader.disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
