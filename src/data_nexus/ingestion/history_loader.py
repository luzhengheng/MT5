"""
Historical OHLCV Data Loader

High-performance async loader for historical market data.

Key Design Principles:
1. Low Concurrency (5-8 workers): Respects PL0 disk constraints
2. Aggressive Batching (5000+ rows): Minimizes database round-trips
3. Cursor-based (Asset.last_synced): Enables resume/pause capability
4. Error Resilience: Per-asset error handling, exponential backoff
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

import aiohttp
from sqlalchemy.orm import Session

from src.data_nexus.config import DatabaseConfig
from src.data_nexus.database.connection import PostgresConnection
from src.data_nexus.models import Asset, MarketData

logger = logging.getLogger(__name__)

# EODHD API endpoint
EODHD_API_URL = "https://eodhistoricaldata.com/api"

# Default timeouts and limits
REQUEST_TIMEOUT = 30
BACKOFF_BASE = 2  # Exponential backoff base


class EODHistoryLoader:
    """
    Async OHLCV data loader with batch writing.

    Usage:
        loader = EODHistoryLoader(api_key, db_config)
        loader.concurrency = 5
        summary = await loader.run_cycle(limit=100, days_old=1)

    Summary:
        {
            'total_assets': 100,
            'total_rows': 50000,
            'failed': 3,
            'duration_sec': 45.2,
        }
    """

    def __init__(self, api_key: str, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize history loader.

        Args:
            api_key: EODHD API key
            db_config: Database configuration (uses default if None)
        """
        self.api_key = api_key
        self.db_config = db_config or DatabaseConfig()

        # Tunable parameters
        self.concurrency = 5  # Default: conservative for PL0
        self.batch_size = 100  # Rows to fetch per API call
        self.write_batch_size = 5000  # Rows to accumulate before DB insert
        self.timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async def run_cycle(self, limit: int = None, days_old: int = 1) -> dict:
        """
        Run one cycle of incremental data loading.

        Logic:
        1. Query assets to sync: WHERE is_active=True AND (last_synced IS NULL OR last_synced < NOW - {days_old})
        2. Create asyncio.Queue with these assets
        3. Spawn N worker coroutines (controlled by Semaphore)
        4. Each worker fetches /api/eod/{symbol}.{exchange}
        5. Accumulate MarketData objects in batch buffer
        6. When batch reaches write_batch_size, flush to DB via bulk_save_objects()
        7. Update Asset.last_synced = datetime.now()
        8. Return summary

        Args:
            limit: Max assets to process (prevents OOM). None = process all.
            days_old: Only sync assets where last_synced < NOW - {days_old} days

        Returns:
            Summary dictionary with keys: total_assets, total_rows, failed, duration_sec
        """
        start_time = datetime.now(timezone.utc)
        conn = PostgresConnection()

        logger.info(f"Starting load cycle: limit={limit}, days_old={days_old}, concurrency={self.concurrency}")

        try:
            # Query assets to sync
            with conn.get_session() as session:
                query = session.query(Asset).filter(Asset.is_active == True)

                # Filter by last_synced age
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
                query = query.filter(
                    (Asset.last_synced == None) | (Asset.last_synced < cutoff_time)
                )

                # Order by last_synced ASC (NULLS FIRST)
                query = query.order_by(Asset.last_synced.asc())

                # Apply limit
                if limit:
                    query = query.limit(limit)

                assets_to_sync = query.all()

            logger.info(f"Found {len(assets_to_sync)} assets to sync")

            if not assets_to_sync:
                logger.info("No assets to sync")
                return {
                    "total_assets": 0,
                    "total_rows": 0,
                    "failed": 0,
                    "duration_sec": 0,
                }

            # Create queue with assets
            queue = asyncio.Queue()
            for asset in assets_to_sync:
                await queue.put(asset)

            # Run workers
            total_rows, failed = await self._run_workers(queue, assets_to_sync)

            # Calculate elapsed time
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            summary = {
                "total_assets": len(assets_to_sync),
                "total_rows": total_rows,
                "failed": failed,
                "duration_sec": round(elapsed, 1),
            }

            logger.info(f"Load cycle complete: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Load cycle failed: {e}")
            raise

    async def _run_workers(self, queue: asyncio.Queue, assets: list[Asset]) -> tuple[int, int]:
        """
        Spawn worker coroutines to fetch data and batch-write to DB.

        Workers:
        - Consume assets from queue
        - Fetch OHLCV data from API
        - Accumulate in batch buffer
        - Write batches to DB when buffer reaches write_batch_size

        Args:
            queue: Queue of assets to process
            assets: List of all assets (for session context)

        Returns:
            Tuple of (total_rows_inserted, total_failed)
        """
        semaphore = asyncio.Semaphore(self.concurrency)
        batch_buffer = []
        assets_to_update = []
        total_rows = 0
        total_failed = 0
        lock = asyncio.Lock()  # Protect shared state

        async def worker(session: Session):
            """Worker coroutine: fetch data and batch-write."""
            nonlocal batch_buffer, assets_to_update, total_rows, total_failed

            while True:
                try:
                    asset = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                try:
                    async with semaphore:
                        logger.info(f"Fetching {asset.symbol}...")
                        market_data_list = await self._fetch_symbol(asset)

                        if market_data_list:
                            # Add to batch
                            async with lock:
                                batch_buffer.extend(market_data_list)
                                assets_to_update.append(asset)
                                logger.info(f"  → {len(market_data_list)} rows for {asset.symbol}")

                                # Flush batch if threshold reached
                                if len(batch_buffer) >= self.write_batch_size:
                                    logger.info(f"Flushing {len(batch_buffer)} rows to database...")
                                    self._flush_batch(session, batch_buffer)
                                    total_rows += len(batch_buffer)
                                    batch_buffer.clear()
                        else:
                            logger.warning(f"  → No data for {asset.symbol}")

                except Exception as e:
                    logger.error(f"Error processing {asset.symbol}: {e}")
                    total_failed += 1
                    continue
                finally:
                    queue.task_done()

        # Create session for batch writing
        conn = PostgresConnection()
        with conn.get_session() as session:
            # Run workers
            workers = [
                asyncio.create_task(worker(session))
                for _ in range(self.concurrency)
            ]

            await asyncio.gather(*workers)

            # Final flush for remaining rows
            if batch_buffer:
                logger.info(f"Final flush: {len(batch_buffer)} rows to database...")
                self._flush_batch(session, batch_buffer)
                total_rows += len(batch_buffer)

            # Update asset.last_synced
            if assets_to_update:
                logger.info(f"Updating last_synced for {len(assets_to_update)} assets...")
                for asset in assets_to_update:
                    asset.last_synced = datetime.now(timezone.utc)
                session.commit()

        return total_rows, total_failed

    async def _fetch_symbol(self, asset: Asset) -> list[MarketData]:
        """
        Fetch and parse OHLCV data for a single symbol.

        Error Handling:
        - 404: Symbol not found, log warning, return empty list
        - 429: Rate limited, back off, return empty list
        - 5xx: Server error, don't update last_synced (will retry next cycle)
        - Timeout: Network error, return empty list

        Args:
            asset: Asset to fetch

        Returns:
            List of MarketData objects, or empty list on error
        """
        try:
            url = f"{EODHD_API_URL}/eod/{asset.symbol}"
            params = {
                "api_token": self.api_key,
                "fmt": "json",
                "period": "d",  # Daily data
            }

            # If asset has been synced before, fetch only newer data
            if asset.last_synced:
                from_date = (asset.last_synced.date() + timedelta(days=1)).isoformat()
                params["from"] = from_date

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 404:
                        logger.warning(f"Asset {asset.symbol} not found (404)")
                        return []
                    elif resp.status == 429:
                        logger.warning(f"Rate limited on {asset.symbol}, backing off 60s")
                        await asyncio.sleep(60)
                        return []
                    elif resp.status >= 500:
                        logger.error(f"Server error {resp.status} for {asset.symbol}")
                        return []  # Don't update last_synced
                    elif resp.status != 200:
                        logger.warning(f"Unexpected status {resp.status} for {asset.symbol}")
                        return []

                    data = await resp.json()

            # Validate response
            if isinstance(data, dict) and "error" in data:
                logger.error(f"API error for {asset.symbol}: {data['error']}")
                return []

            if not isinstance(data, list):
                logger.error(f"Unexpected response format for {asset.symbol}: {type(data)}")
                return []

            # Transform to MarketData objects
            market_data_list = []
            for row in data:
                try:
                    md = MarketData(
                        time=datetime.fromisoformat(row["date"]).replace(tzinfo=timezone.utc),
                        symbol=asset.symbol,
                        open=Decimal(str(row["open"])),
                        high=Decimal(str(row["high"])),
                        low=Decimal(str(row["low"])),
                        close=Decimal(str(row["close"])),
                        adjusted_close=Decimal(str(row.get("adjusted_close", row["close"]))),
                        volume=int(row.get("volume", 0)),
                    )
                    market_data_list.append(md)
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Parse error in {asset.symbol} row: {e}")
                    continue

            return market_data_list

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {asset.symbol}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching {asset.symbol}: {e}")
            return []

    def _flush_batch(self, session: Session, batch: list[MarketData]):
        """
        Flush accumulated batch to database.

        Uses SQLAlchemy bulk_save_objects() for efficiency on large batches.

        Args:
            session: SQLAlchemy session
            batch: List of MarketData objects
        """
        if not batch:
            return

        try:
            session.bulk_save_objects(batch)
            session.commit()
            logger.debug(f"Flushed {len(batch)} rows to database")
        except Exception as e:
            logger.error(f"Batch flush failed: {e}")
            session.rollback()
            raise
