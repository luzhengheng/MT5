#!/usr/bin/env python3
"""
Bulk Data Backfill CLI Tool

Task #040: EODHD Bulk Data Ingestion

Provides CLI interface for:
1. Daily bulk update (latest EOD data for entire exchange)
2. Historical backfill for top symbols
3. Symbol registration

Usage Examples:
    # Daily update (fetch latest EOD for all US equities)
    python3 scripts/run_bulk_backfill.py --daily

    # Backfill top 100 symbols for last 365 days
    python3 scripts/run_bulk_backfill.py --backfill --symbols 100 --days 365

    # Register symbols from file
    python3 scripts/run_bulk_backfill.py --register --file symbols.txt
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_nexus.ingestion.bulk_loader import BulkEODLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_daily_update(api_key: str, exchange: str = 'US'):
    """
    Run daily bulk EOD update.

    Args:
        api_key: EODHD API key
        exchange: Exchange code (default: 'US')
    """
    print("=" * 80)
    print("📊 DAILY BULK EOD UPDATE")
    print("=" * 80)
    print()

    loader = BulkEODLoader(api_key=api_key)

    try:
        print(f"Fetching latest EOD data for {exchange} exchange...")
        print()

        result = loader.run_daily_update(exchange=exchange)

        print()
        print("=" * 80)
        print("✅ DAILY UPDATE COMPLETE")
        print("=" * 80)
        print()
        print(f"Symbols processed: {result['symbols_count']:,}")
        print(f"Rows inserted: {result['rows_inserted']:,}")
        print(f"Assets registered: {result['assets_registered']:,}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error during daily update: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_historical_backfill(
    api_key: str,
    top_n: int = 100,
    days_back: int = 365,
    exchange: str = 'US'
):
    """
    Run historical backfill for top N symbols.

    Args:
        api_key: EODHD API key
        top_n: Number of top symbols to backfill
        days_back: Number of days to backfill
        exchange: Exchange code (default: 'US')
    """
    print("=" * 80)
    print(f"📈 HISTORICAL BACKFILL: Top {top_n} Symbols")
    print("=" * 80)
    print()

    loader = BulkEODLoader(api_key=api_key)

    try:
        # Fetch bulk data to get symbol list
        print(f"Fetching symbol list from {exchange} exchange...")
        df = loader.fetch_bulk_last_day(exchange=exchange)

        if df.empty:
            print("❌ No symbols found")
            return 1

        # Sort by volume and take top N
        df_sorted = df.sort_values('volume', ascending=False)
        top_symbols = df_sorted['code'].head(top_n).tolist()

        # Add exchange suffix if needed
        symbols_with_exchange = [
            f"{symbol}.{exchange}" if '.' not in symbol else symbol
            for symbol in top_symbols
        ]

        print(f"Selected top {len(symbols_with_exchange)} symbols by volume")
        print(f"Date range: {days_back} days back from today")
        print()

        # Calculate date range
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        print(f"From: {from_date}")
        print(f"To:   {to_date}")
        print()

        # Run async backfill
        print("Starting async backfill...")
        print()

        total_rows = asyncio.run(
            loader.backfill_top_symbols(
                symbols=symbols_with_exchange,
                from_date=from_date,
                to_date=to_date,
                batch_size=100,
                save=True
            )
        )

        print()
        print("=" * 80)
        print("✅ BACKFILL COMPLETE")
        print("=" * 80)
        print()
        print(f"Symbols processed: {len(symbols_with_exchange):,}")
        print(f"Total rows inserted: {total_rows:,}")
        print(f"Average rows per symbol: {total_rows / len(symbols_with_exchange):.1f}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error during backfill: {e}")
        import traceback
        traceback.print_exc()
        return 1


def register_symbols_from_file(api_key: str, file_path: str, exchange: str = 'US'):
    """
    Register symbols from text file.

    Args:
        api_key: EODHD API key
        file_path: Path to text file with symbols (one per line)
        exchange: Exchange code (default: 'US')
    """
    print("=" * 80)
    print("📝 SYMBOL REGISTRATION")
    print("=" * 80)
    print()

    loader = BulkEODLoader(api_key=api_key)

    try:
        # Read symbols from file
        with open(file_path, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]

        print(f"Loaded {len(symbols)} symbols from {file_path}")
        print()

        # Register assets
        registered = loader.register_assets(symbols=symbols, exchange=exchange)

        print()
        print("=" * 80)
        print("✅ REGISTRATION COMPLETE")
        print("=" * 80)
        print()
        print(f"Symbols registered: {registered:,}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error during registration: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk Data Backfill Tool (Task #040)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Daily update
  python3 scripts/run_bulk_backfill.py --daily

  # Backfill top 500 symbols for last 2 years
  python3 scripts/run_bulk_backfill.py --backfill --symbols 500 --days 730

  # Register symbols from file
  python3 scripts/run_bulk_backfill.py --register --file symbols.txt
        """
    )

    # Operation mode
    parser.add_argument(
        '--daily',
        action='store_true',
        help='Run daily bulk EOD update'
    )
    parser.add_argument(
        '--backfill',
        action='store_true',
        help='Run historical backfill for top symbols'
    )
    parser.add_argument(
        '--register',
        action='store_true',
        help='Register symbols from file'
    )

    # Parameters
    parser.add_argument(
        '--exchange',
        default='US',
        help='Exchange code (default: US)'
    )
    parser.add_argument(
        '--symbols',
        type=int,
        default=100,
        help='Number of top symbols to backfill (default: 100)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='Number of days to backfill (default: 365)'
    )
    parser.add_argument(
        '--file',
        help='Path to symbols file (for --register mode)'
    )

    args = parser.parse_args()

    # Validate API key
    api_key = os.getenv('EODHD_API_KEY')
    if not api_key:
        print("❌ Error: EODHD_API_KEY environment variable not set")
        print()
        print("Set it in .env file or export it:")
        print("  export EODHD_API_KEY='your_api_key'")
        return 1

    # Execute operation
    if args.daily:
        return run_daily_update(api_key=api_key, exchange=args.exchange)

    elif args.backfill:
        return run_historical_backfill(
            api_key=api_key,
            top_n=args.symbols,
            days_back=args.days,
            exchange=args.exchange
        )

    elif args.register:
        if not args.file:
            print("❌ Error: --file required for --register mode")
            return 1
        return register_symbols_from_file(
            api_key=api_key,
            file_path=args.file,
            exchange=args.exchange
        )

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
