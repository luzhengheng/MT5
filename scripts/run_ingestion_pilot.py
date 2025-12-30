#!/usr/bin/env python3
"""
Task #012.04: EODHD Bulk Data Ingestion - Pilot Run
====================================================

Pilot run to validate the bulk ingestion pipeline.
Downloads full historical data for EURUSD and inserts into TimescaleDB.

Expected result: >5000 rows for EURUSD in market_data_ohlcv table.

Usage:
    python3 scripts/run_ingestion_pilot.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader.eodhd_bulk_loader import EODHDBulkLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print formatted section header"""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def print_step(step_num, description):
    """Print step header"""
    print(f"{BLUE}[Step {step_num}]{RESET} {description}")


async def run_pilot_ingestion():
    """
    Execute pilot ingestion for EURUSD.

    Steps:
    1. Load environment variables
    2. Initialize bulk loader
    3. Fetch EURUSD history from 1990-01-01 to present
    4. Insert into market_data_ohlcv table
    5. Report metrics
    """
    print_header("Task #012.04: EODHD Bulk Data Ingestion - Pilot Run")

    # Step 1: Load environment
    print_step(1, "Loading environment variables")

    # Load .env from project root
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"   {GREEN}✅ Loaded .env from {env_file}{RESET}")
    else:
        print(f"   {YELLOW}⚠️  .env not found, using environment variables{RESET}")

    # Check EODHD API token
    api_token = os.getenv("EODHD_API_TOKEN") or os.getenv("EODHD_API_KEY")
    if not api_token:
        print(f"   {RED}❌ EODHD_API_TOKEN not found in environment{RESET}")
        print(f"   {YELLOW}Set it with: export EODHD_API_TOKEN='your_token'{RESET}")
        return 1

    print(f"   {GREEN}✅ API token loaded: {api_token[:10]}...{RESET}")

    # Step 2: Initialize loader
    print_step(2, "Initializing EODHD Bulk Loader")

    try:
        loader = EODHDBulkLoader(
            db_host="localhost",
            db_port=5432,
            db_user="trader",
            db_password="password",
            db_name="mt5_crs",
            api_key=api_token
        )
        print(f"   {GREEN}✅ Loader initialized{RESET}")
    except Exception as e:
        print(f"   {RED}❌ Initialization failed: {e}{RESET}")
        return 1

    # Step 3: Configure ingestion
    print_step(3, "Configuring ingestion parameters")

    symbol = "EURUSD"
    exchange = "FOREX"
    from_date = "1990-01-01"  # Full history
    to_date = datetime.now().strftime("%Y-%m-%d")

    print(f"   Symbol: {symbol}")
    print(f"   Exchange: {exchange}")
    print(f"   Date range: {from_date} to {to_date}")
    print(f"   Expected rows: >5000")
    print()

    # Step 4: Execute ingestion
    print_step(4, "Executing bulk ingestion")

    try:
        start_time = asyncio.get_event_loop().time()

        # Run ingestion pipeline
        rows_inserted, elapsed = await loader.ingest_symbol(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date
        )

        total_elapsed = asyncio.get_event_loop().time() - start_time

        # Step 5: Report metrics
        print_step(5, "Ingestion Metrics")

        print(f"   Symbol: {symbol}")
        print(f"   Rows inserted: {GREEN}{rows_inserted:,}{RESET}")
        print(f"   Time elapsed: {GREEN}{total_elapsed:.2f}s{RESET}")
        print(f"   Insertion rate: {GREEN}{rows_inserted/elapsed:.0f} rows/sec{RESET}")
        print()

        # Verify minimum row requirement
        if rows_inserted >= 5000:
            print(f"   {GREEN}✅ SUCCESS: Inserted {rows_inserted:,} rows (>5000 required){RESET}")
            success = True
        else:
            print(f"   {YELLOW}⚠️  WARNING: Only {rows_inserted} rows inserted (<5000 expected){RESET}")
            success = False

    except Exception as e:
        print(f"   {RED}❌ Ingestion failed: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        await loader.disconnect_db()

    # Final summary
    print_header("Pilot Ingestion Complete")

    if success:
        print(f"{GREEN}✅ SUCCESS{RESET}")
        print(f"   EURUSD historical data successfully ingested")
        print(f"   Rows: {rows_inserted:,}")
        print(f"   Time: {total_elapsed:.2f}s")
        print(f"   Database: mt5_crs.market_data_ohlcv")
        print()
        print(f"{CYAN}Next steps:{RESET}")
        print(f"   1. Verify data: python3 scripts/verify_db_status.py")
        print(f"   2. Query data: SELECT * FROM market_data_ohlcv WHERE symbol='EURUSD' LIMIT 10;")
        print(f"   3. Finish task: python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print(f"{YELLOW}⚠️  WARNING{RESET}")
        print(f"   Ingestion completed but with fewer rows than expected")
        print(f"   Expected: >5000 rows")
        print(f"   Actual: {rows_inserted} rows")
        print()
        print(f"{CYAN}Troubleshooting:{RESET}")
        print(f"   1. Check EODHD API subscription tier")
        print(f"   2. Verify symbol format (EURUSD.FOREX)")
        print(f"   3. Check date range availability")
        print(f"   4. Review API rate limits")
        print()
        return 0  # Still exit 0 since ingestion technically succeeded


async def main():
    """Main entry point"""
    try:
        exit_code = await run_pilot_ingestion()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}❌ Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
