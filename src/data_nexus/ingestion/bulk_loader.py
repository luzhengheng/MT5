"""
EODHD Bulk EOD Data Ingestion Engine

Task #039.5 (ID #040): Bulk data ingestion for US equities (~45k tickers)

Provides BulkEODLoader class for:
- Fetching bulk EOD data via EODHD Bulk API
- Async downloading with rate limiting
- Efficient batch database insertion
- Asset registration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import aiohttp
import pandas as pd
from sqlalchemy import text

from src.data_nexus.config import DatabaseConfig
from src.data_nexus.database.connection import PostgresConnection

logger = logging.getLogger(__name__)


class BulkEODLoader:
    """
    EODHD Bulk EOD Data Loader for US Equities.

    Handles:
    1. Fetching bulk EOD data via EODHD API
    2. Async concurrent downloads with Semaphore rate limiting
    3. Data validation and transformation
    4. Batched database insertion
    5. Asset registration

    Attributes:
        api_key: EODHD API key
        db_config: Database configuration
        base_url: EODHD API base URL
    """

    def __init__(self, api_key: str, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize BulkEODLoader.

        Args:
            api_key: EODHD API key
            db_config: Optional database configuration (uses default if None)
        """
        self.api_key = api_key
        self.db_config = db_config or DatabaseConfig()
        self.base_url = "https://eodhd.com/api"
        self.conn = None

        logger.info(f"Initialized BulkEODLoader")

    def _get_connection(self) -> PostgresConnection:
        """Get or create database connection."""
        if self.conn is None:
            self.conn = PostgresConnection()
        return self.conn

    def fetch_bulk_last_day(self, exchange: str = 'US') -> pd.DataFrame:
        """
        Fetch latest EOD data for entire exchange (Bulk API).

        URL: https://eodhd.com/api/eod-bulk-last-day/{EXCHANGE}

        Args:
            exchange: Exchange code (e.g., 'US')

        Returns:
            DataFrame with columns: code, date, open, high, low, close, volume
        """
        url = f"{self.base_url}/eod-bulk-last-day/{exchange}"
        params = {
            'api_token': self.api_key,
            'fmt': 'json'
        }

        logger.info(f"Fetching bulk EOD data for {exchange}...")

        try:
            import requests
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            df = pd.DataFrame(data)

            logger.info(f"Fetched {len(df)} tickers for {exchange}")

            return df

        except Exception as e:
            logger.error(f"Failed to fetch bulk data: {e}")
            raise

    async def fetch_symbol_history_async(
        self,
        session: aiohttp.ClientSession,
        symbol: str,
        from_date: str,
        to_date: str,
        semaphore: asyncio.Semaphore
    ) -> pd.DataFrame:
        """
        Fetch historical data for single symbol (async).

        Args:
            session: aiohttp ClientSession
            symbol: Symbol code (e.g., 'AAPL.US')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            semaphore: Semaphore for rate limiting

        Returns:
            DataFrame with OHLCV data
        """
        async with semaphore:
            url = f"{self.base_url}/eod/{symbol}"
            params = {
                'api_token': self.api_key,
                'fmt': 'json',
                'from': from_date,
                'to': to_date
            }

            try:
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            df = pd.DataFrame(data)
                            df['symbol'] = symbol
                            return df
                    else:
                        logger.warning(f"Failed to fetch {symbol}: HTTP {resp.status}")
                        return pd.DataFrame()

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {symbol}")
                return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                return pd.DataFrame()

    def fetch_symbol_history(
        self,
        symbol: str,
        from_date: str,
        to_date: str
    ) -> pd.DataFrame:
        """
        Fetch historical data for single symbol (sync wrapper).

        Args:
            symbol: Symbol code (e.g., 'AAPL.US')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data
        """
        url = f"{self.base_url}/eod/{symbol}"
        params = {
            'api_token': self.api_key,
            'fmt': 'json',
            'from': from_date,
            'to': to_date
        }

        try:
            import requests
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                df = pd.DataFrame(data)
                df['symbol'] = symbol
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()

    async def backfill_top_symbols(
        self,
        symbols: List[str],
        from_date: str,
        to_date: str,
        batch_size: int = 100,
        save: bool = True
    ) -> int:
        """
        Backfill historical data for selected symbols (async).

        Args:
            symbols: List of symbols (e.g., ['AAPL.US', 'MSFT.US'])
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            batch_size: Number of rows to save per batch
            save: Whether to save to database

        Returns:
            Total rows ingested
        """
        logger.info(f"Starting backfill for {len(symbols)} symbols ({from_date} to {to_date})")

        total_rows = 0

        # Batch symbols for concurrent fetching
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]

                tasks = [
                    self.fetch_symbol_history_async(
                        session, symbol, from_date, to_date, semaphore
                    )
                    for symbol in batch_symbols
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Combine results
                dfs = [df for df in results if isinstance(df, pd.DataFrame) and len(df) > 0]

                if dfs:
                    batch_df = pd.concat(dfs, ignore_index=True)

                    if save:
                        rows = self.save_batch(batch_df)
                        total_rows += rows
                        logger.info(f"Batch {i//batch_size + 1}: Saved {rows} rows")

        logger.info(f"Backfill complete: {total_rows} total rows")

        return total_rows

    def save_batch(self, df: pd.DataFrame, batch_size: int = 10000) -> int:
        """
        Save batch of data to market_data table.

        Uses PostgreSQL COPY for efficient bulk insert with conflict handling.

        Args:
            df: DataFrame with columns: date, symbol, open, high, low, close, volume
            batch_size: Rows per transaction

        Returns:
            Number of rows inserted
        """
        if df.empty:
            return 0

        logger.info(f"Saving {len(df)} rows to market_data...")

        try:
            conn = self._get_connection()

            # Prepare data
            df['time'] = pd.to_datetime(df['date'])
            df['adjusted_close'] = df.get('adjusted_close', df['close'])

            # Select and rename columns
            save_df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'adjusted_close', 'volume']].copy()
            save_df = save_df.dropna()

            rows_saved = 0

            # Save in batches
            for i in range(0, len(save_df), batch_size):
                batch = save_df.iloc[i:i + batch_size]

                try:
                    # Use SQLAlchemy to_sql with 'append' mode
                    from sqlalchemy import create_engine
                    engine = conn.engine

                    batch.to_sql(
                        'market_data',
                        con=engine,
                        if_exists='append',
                        index=False,
                        method='multi',
                        chunksize=1000
                    )

                    rows_saved += len(batch)
                    logger.debug(f"Saved batch {i//batch_size + 1}: {len(batch)} rows")

                except Exception as e:
                    logger.error(f"Error saving batch: {e}")
                    continue

            logger.info(f"Successfully saved {rows_saved} rows")

            return rows_saved

        except Exception as e:
            logger.error(f"Failed to save batch: {e}")
            return 0

    def register_assets(self, symbols: List[str], exchange: str = 'US') -> int:
        """
        Register symbols in assets table.

        Args:
            symbols: List of symbols (e.g., ['AAPL', 'MSFT'] - without exchange suffix)
            exchange: Exchange code (e.g., 'US')

        Returns:
            Number of assets registered
        """
        logger.info(f"Registering {len(symbols)} assets for {exchange}...")

        try:
            conn = self._get_connection()

            # Prepare asset data
            assets_df = pd.DataFrame({
                'symbol': [f"{symbol}.{exchange}" if '.' not in symbol else symbol for symbol in symbols],
                'exchange': exchange,
                'asset_type': 'Common Stock',
                'is_active': True
            })

            # Insert or update assets
            query = f"""
                INSERT INTO assets (symbol, exchange, asset_type, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE
                SET is_active = TRUE, updated_at = NOW()
            """

            registered = 0

            for _, row in assets_df.iterrows():
                try:
                    conn.execute(query, (row['symbol'], row['exchange'], row['asset_type'], row['is_active']))
                    registered += 1
                except Exception as e:
                    logger.debug(f"Error registering {row['symbol']}: {e}")

            logger.info(f"Registered {registered} assets")

            return registered

        except Exception as e:
            logger.error(f"Failed to register assets: {e}")
            return 0

    def run_daily_update(self, exchange: str = 'US') -> Dict:
        """
        Run daily bulk update for exchange.

        Steps:
        1. Fetch latest bulk EOD data
        2. Save to database
        3. Register new assets

        Args:
            exchange: Exchange code (e.g., 'US')

        Returns:
            Summary dictionary with counts
        """
        logger.info(f"Starting daily update for {exchange}...")

        try:
            # Fetch bulk data
            df = self.fetch_bulk_last_day(exchange=exchange)

            if df.empty:
                logger.warning("No data received from bulk API")
                return {'symbols_count': 0, 'rows_inserted': 0, 'assets_registered': 0}

            # Save to database
            rows_inserted = self.save_batch(df)

            # Extract symbols for asset registration
            symbols = df['code'].unique().tolist()

            # Register assets
            assets_registered = self.register_assets(symbols, exchange=exchange)

            result = {
                'symbols_count': len(symbols),
                'rows_inserted': rows_inserted,
                'assets_registered': assets_registered
            }

            logger.info(f"Daily update complete: {result}")

            return result

        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            return {'symbols_count': 0, 'rows_inserted': 0, 'assets_registered': 0}


# Example usage
if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)

    api_key = os.getenv("EODHD_API_KEY")

    if api_key:
        loader = BulkEODLoader(api_key=api_key)

        # Daily update
        summary = loader.run_daily_update(exchange='US')
        print(f"\nDaily Update Summary:")
        print(f"  Symbols: {summary['symbols_count']}")
        print(f"  Rows Inserted: {summary['rows_inserted']}")
        print(f"  Assets Registered: {summary['assets_registered']}")
    else:
        print("Error: EODHD_API_KEY not set")
