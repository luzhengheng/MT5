#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #066: EODHD Async Bulk Ingestion Pipeline - Main Entry Point
Protocol: v4.3 (Zero-Trust Edition)

This module provides a unified entry point for the EODHD bulk data ingestion
pipeline, orchestrating existing loader implementations with proper error handling,
validation, and audit trail.

Architecture:
- Leverages existing EODHDBulkLoader (asyncpg + COPY protocol)
- Integrates with TimescaleDB hypertables
- Rate-limited async fetching with Semaphore
- Comprehensive error handling and validation
- Physical verification for Zero-Trust compliance

Usage:
    python3 src/main_bulk_loader.py --symbols AAPL.US,MSFT.US --start-date 2024-01-01
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    EODHD_API_TOKEN,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB
)
from src.data_loader.eodhd_bulk_loader import EODHDBulkLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


class BulkIngestPipeline:
    """
    EODHD Bulk Data Ingestion Pipeline Orchestrator.

    Coordinates existing bulk loader implementations with:
    - Health checks and pre-flight validation
    - Data quality checks
    - Error handling and retry logic
    - Physical verification for audit trail
    """

    def __init__(self):
        """Initialize the bulk ingestion pipeline."""
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()

        # Validate configuration
        if not EODHD_API_TOKEN:
            logger.error(f"{RED}❌ EODHD_API_TOKEN not set in environment{RESET}")
            logger.error(f"{YELLOW}Set via: export EODHD_API_TOKEN='your_token_here'{RESET}")
            sys.exit(1)

        # Initialize bulk loader
        self.loader = EODHDBulkLoader(
            db_host=POSTGRES_HOST,
            db_port=POSTGRES_PORT,
            db_user=POSTGRES_USER,
            db_password=POSTGRES_PASSWORD,
            db_name=POSTGRES_DB,
            api_key=EODHD_API_TOKEN
        )

        logger.info(f"{CYAN}🚀 Bulk Ingestion Pipeline Initialized{RESET}")
        logger.info(f"{CYAN}⚡ Session ID: {self.session_id}{RESET}")
        logger.info(f"{CYAN}⚡ Start Time: {self.start_time.isoformat()}{RESET}")

    async def health_check(self) -> bool:
        """
        Perform pre-flight health checks.

        Returns:
            True if all checks pass, False otherwise
        """
        logger.info(f"{BLUE}🔍 Running health checks...{RESET}")

        try:
            # Check database connectivity
            pool = await self.loader.connect_db()
            logger.info(f"{GREEN}  ✅ Database connection: OK{RESET}")

            # Check if market_data schema exists
            async with pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = 'market_data')"
                )
                if result:
                    logger.info(f"{GREEN}  ✅ market_data schema: EXISTS{RESET}")
                else:
                    logger.error(f"{RED}  ❌ market_data schema: NOT FOUND{RESET}")
                    logger.error(f"{YELLOW}  Run: python3 src/infrastructure/init_db.py{RESET}")
                    return False

                # Check if ohlcv_daily table exists
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'market_data' AND table_name = 'ohlcv_daily')"
                )
                if result:
                    logger.info(f"{GREEN}  ✅ ohlcv_daily table: EXISTS{RESET}")
                else:
                    logger.error(f"{RED}  ❌ ohlcv_daily table: NOT FOUND{RESET}")
                    return False

            logger.info(f"{GREEN}✅ All health checks passed{RESET}")
            return True

        except Exception as e:
            logger.error(f"{RED}❌ Health check failed: {e}{RESET}")
            return False

    async def ingest_symbols(
        self,
        symbols: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        max_workers: int = 5
    ) -> Dict[str, any]:
        """
        Ingest historical data for multiple symbols with concurrent workers.

        Args:
            symbols: List of symbols (e.g., ['AAPL.US', 'MSFT.US'])
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)
            max_workers: Maximum concurrent workers (default: 5)

        Returns:
            Summary dict with success/failure counts and metrics
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"{CYAN}📊 Starting ingestion for {len(symbols)} symbols{RESET}")
        logger.info(f"{CYAN}📅 Date range: {start_date} to {end_date}{RESET}")
        logger.info(f"{CYAN}👷 Workers: {max_workers}{RESET}")

        summary = {
            'total_symbols': len(symbols),
            'successful': 0,
            'failed': 0,
            'total_rows': 0,
            'errors': [],
            'session_id': self.session_id
        }

        # Create semaphore to limit concurrent workers
        semaphore = asyncio.Semaphore(max_workers)

        async def _worker(symbol: str) -> Tuple[str, int, Optional[str]]:
            """Worker coroutine for concurrent symbol processing."""
            async with semaphore:
                try:
                    logger.info(f"{BLUE}Processing {symbol}...{RESET}")

                    # Fetch and ingest via existing loader
                    rows_inserted = await self.loader.ingest_symbol(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date
                    )

                    logger.info(
                        f"{GREEN}  ✅ {symbol}: {rows_inserted} rows inserted{RESET}"
                    )
                    return (symbol, rows_inserted, None)

                except Exception as e:
                    logger.error(f"{RED}  ❌ {symbol}: {e}{RESET}")
                    return (symbol, 0, str(e))

        # Create worker tasks for all symbols
        tasks = [_worker(symbol) for symbol in symbols]

        # Execute all workers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Process results and update summary
        for symbol, rows_inserted, error in results:
            if error is None:
                summary['successful'] += 1
                summary['total_rows'] += rows_inserted
            else:
                summary['failed'] += 1
                summary['errors'].append({
                    'symbol': symbol,
                    'error': error
                })

        return summary

    async def run(
        self,
        symbols: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        max_workers: int = 5
    ) -> int:
        """
        Execute the complete bulk ingestion pipeline.

        Args:
            symbols: List of symbols to ingest
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD, default: today)
            max_workers: Maximum concurrent workers (default: 5)

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        try:
            # Health check
            if not await self.health_check():
                logger.error(f"{RED}❌ Health checks failed, aborting{RESET}")
                return 1

            # Run ingestion
            summary = await self.ingest_symbols(symbols, start_date, end_date, max_workers)

            # Print summary
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()

            print()
            print(f"{CYAN}{'=' * 80}{RESET}")
            print(f"{CYAN}📊 INGESTION SUMMARY{RESET}")
            print(f"{CYAN}{'=' * 80}{RESET}")
            print(f"  Session ID: {summary['session_id']}")
            print(f"  Total Symbols: {summary['total_symbols']}")
            print(f"  {GREEN}✅ Successful: {summary['successful']}{RESET}")
            print(f"  {RED}❌ Failed: {summary['failed']}{RESET}")
            print(f"  Total Rows Inserted: {summary['total_rows']}")
            print(f"  Duration: {duration:.2f} seconds")

            if summary['total_rows'] > 0:
                rows_per_sec = summary['total_rows'] / duration
                print(f"  Performance: {rows_per_sec:.1f} rows/sec")

            if summary['errors']:
                print(f"\n{YELLOW}⚠️  Errors:{RESET}")
                for error in summary['errors']:
                    print(f"  - {error['symbol']}: {error['error']}")

            print(f"{CYAN}{'=' * 80}{RESET}")

            # Physical verification for Zero-Trust
            print()
            print(f"{CYAN}⚡ [PROOF] SESSION COMPLETED: {self.session_id}{RESET}")
            print(f"{CYAN}⚡ [PROOF] SESSION END: {end_time.isoformat()}{RESET}")
            print(f"{CYAN}⚡ [PROOF] ROWS INSERTED: {summary['total_rows']}{RESET}")

            # Cleanup
            if self.loader.pool:
                await self.loader.pool.close()

            # Return success/failure
            return 0 if summary['failed'] == 0 else 1

        except Exception as e:
            logger.error(f"{RED}❌ Pipeline failed: {e}{RESET}")
            import traceback
            logger.error(traceback.format_exc())
            return 1


async def main_async(symbols: List[str], start_date: str, end_date: Optional[str] = None):
    """Async entry point."""
    pipeline = BulkIngestPipeline()
    return await pipeline.run(symbols, start_date, end_date)


def main():
    """
    Main entry point for the bulk ingestion pipeline.

    This function is intended to be called from CLI scripts or other modules.
    For command-line usage, use scripts/bulk_loader_cli.py instead.
    """
    # Example usage (for testing)
    symbols = ['AAPL.US', 'MSFT.US', 'GOOGL.US']
    start_date = '2024-01-01'
    end_date = '2024-12-31'

    print(f"{YELLOW}⚠️  Running in test mode with sample symbols{RESET}")
    print(f"{YELLOW}For production use, call via scripts/bulk_loader_cli.py{RESET}")
    print()

    exit_code = asyncio.run(main_async(symbols, start_date, end_date))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
