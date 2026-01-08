#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #066: EODHD Bulk Loader CLI Interface
Protocol: v4.3 (Zero-Trust Edition)

Command-line interface for the bulk historical data ingestion pipeline.
Supports flexible symbol selection, date ranges, and concurrency control.

Usage:
    python3 scripts/bulk_loader_cli.py --symbols AAPL.US,MSFT.US
    python3 scripts/bulk_loader_cli.py --symbols AAPL.US --start-date 2024-01-01 --end-date 2024-12-31
    python3 scripts/bulk_loader_cli.py --symbols-file symbols.txt --workers 5
"""

import sys
import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main_bulk_loader import BulkIngestPipeline

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='EODHD Bulk Historical Data Ingestion Pipeline (Task #066)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest single symbol
  python3 scripts/bulk_loader_cli.py --symbols AAPL.US

  # Ingest multiple symbols
  python3 scripts/bulk_loader_cli.py --symbols AAPL.US,MSFT.US,GOOGL.US

  # Ingest from file
  python3 scripts/bulk_loader_cli.py --symbols-file symbols.txt

  # Ingest with specific date range
  python3 scripts/bulk_loader_cli.py --symbols AAPL.US \\
    --start-date 2023-01-01 --end-date 2024-12-31

  # Ingest with custom worker count
  python3 scripts/bulk_loader_cli.py --symbols AAPL.US --workers 10

Environment Variables:
  EODHD_API_TOKEN   - EODHD API token (required)
  POSTGRES_HOST     - Database host (default: localhost)
  POSTGRES_PORT     - Database port (default: 5432)
  POSTGRES_USER     - Database user (default: trader)
  POSTGRES_PASSWORD - Database password (default: password)
  POSTGRES_DB       - Database name (default: mt5_crs)
        """
    )

    # Symbol selection (mutually exclusive)
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of symbols (e.g., AAPL.US,MSFT.US,GOOGL.US)'
    )
    symbol_group.add_argument(
        '--symbols-file',
        type=str,
        help='Path to file containing symbols (one per line)'
    )

    # Date range options
    parser.add_argument(
        '--start-date',
        type=str,
        default=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
        help='Start date (YYYY-MM-DD, default: 1 year ago)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='End date (YYYY-MM-DD, default: today)'
    )

    # Performance options
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of concurrent workers (default: 5, max: 20)'
    )

    # Output/logging options
    parser.add_argument(
        '--log-file',
        type=str,
        default='bulk_loader.log',
        help='Log file path (default: bulk_loader.log)'
    )

    # Dry-run mode
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without executing ingestion'
    )

    return parser.parse_args()


def load_symbols_from_file(filepath: str) -> list:
    """Load symbols from a file (one per line, ignoring comments)."""
    symbols = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                symbols.append(line)
    return symbols


def validate_date_format(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_arguments(args):
    """Validate parsed arguments."""
    errors = []

    # Validate date format
    if not validate_date_format(args.start_date):
        errors.append(f"Invalid start-date format: {args.start_date} (must be YYYY-MM-DD)")

    if not validate_date_format(args.end_date):
        errors.append(f"Invalid end-date format: {args.end_date} (must be YYYY-MM-DD)")

    # Validate date range
    try:
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start > end:
            errors.append(f"start-date ({args.start_date}) is after end-date ({args.end_date})")
    except ValueError:
        pass  # Already reported above

    # Validate worker count
    if args.workers < 1 or args.workers > 20:
        errors.append(f"workers must be between 1 and 20 (got: {args.workers})")

    # Load symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    elif args.symbols_file:
        if not Path(args.symbols_file).exists():
            errors.append(f"Symbols file not found: {args.symbols_file}")
        else:
            try:
                symbols = load_symbols_from_file(args.symbols_file)
            except Exception as e:
                errors.append(f"Error reading symbols file: {e}")

    if symbols is None or len(symbols) == 0:
        errors.append("No symbols provided")
    elif len(symbols) > 1000:
        errors.append(f"Too many symbols ({len(symbols)}, max: 1000)")

    # Report errors
    if errors:
        print(f"{RED}❌ Validation failed:{RESET}")
        for error in errors:
            print(f"   {error}")
        return False, None

    return True, symbols


async def main_async(args, symbols: list) -> int:
    """Async main function."""
    pipeline = BulkIngestPipeline()

    print()
    print(f"{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}EODHD Bulk Ingestion Pipeline (Task #066){RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}")
    print(f"  Symbols: {len(symbols)}")
    print(f"  Date Range: {args.start_date} to {args.end_date}")
    print(f"  Workers: {args.workers}")
    print(f"{CYAN}{'=' * 80}{RESET}")
    print()

    return await pipeline.run(symbols, args.start_date, args.end_date, args.workers)


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate arguments
    is_valid, symbols = validate_arguments(args)
    if not is_valid:
        sys.exit(1)

    # Dry-run mode
    if args.dry_run:
        print(f"{YELLOW}📋 DRY RUN MODE - No data will be ingested{RESET}")
        print()
        print(f"Configuration:")
        print(f"  Symbols: {symbols}")
        print(f"  Date Range: {args.start_date} to {args.end_date}")
        print(f"  Workers: {args.workers}")
        print()
        print(f"{GREEN}✅ Configuration is valid. Run without --dry-run to execute.{RESET}")
        return 0

    # Execute ingestion
    exit_code = asyncio.run(main_async(args, symbols))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
