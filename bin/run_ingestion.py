#!/usr/bin/env python3
"""
EODHD Data Ingestion CLI

Provides commands for discovering assets and loading historical OHLCV data.

Usage:
    python3 bin/run_ingestion.py discover --exchange US
    python3 bin/run_ingestion.py backfill --limit 100 --concurrency 5

Commands:
    discover    Fetch exchange symbol list and ingest to database
    backfill    Load historical OHLCV data for assets
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import click

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_nexus.config import DatabaseConfig
from src.data_nexus.ingestion.asset_discovery import AssetDiscovery
from src.data_nexus.ingestion.history_loader import EODHistoryLoader


@click.group()
def cli():
    """EODHD Data Ingestion CLI."""
    pass


@cli.command()
@click.option(
    '--exchange',
    required=True,
    help='Exchange code (US, LSE, TSE, etc.)'
)
def discover(exchange):
    """
    Discover and ingest assets for an exchange.

    Example:
        python3 bin/run_ingestion.py discover --exchange US

    This command:
    1. Fetches the symbol list from EODHD
    2. Parses the CSV response
    3. Upserts each symbol into the assets table
    4. Sets last_synced=NULL for new assets (signals: needs data)
    5. Reactivates inactive assets
    """
    # Check API key
    api_key = os.environ.get('EODHD_API_KEY')
    if not api_key:
        click.echo("❌ EODHD_API_KEY not found in environment")
        click.echo("   Set it with: export EODHD_API_KEY='your-key'")
        sys.exit(1)

    click.echo("=" * 80)
    click.echo(f"📥 ASSET DISCOVERY: {exchange}")
    click.echo("=" * 80)
    click.echo()

    try:
        db_config = DatabaseConfig()
        discovery = AssetDiscovery(api_key, db_config)

        click.echo(f"🔍 Discovering assets for {exchange}...")
        count = asyncio.run(discovery.discover_exchange(exchange))

        click.echo()
        click.echo("=" * 80)
        click.echo(f"✅ SUCCESS")
        click.echo("=" * 80)
        click.echo(f"Added/updated: {count} assets")
        click.echo()

        return 0

    except Exception as e:
        click.echo()
        click.echo("=" * 80)
        click.echo(f"❌ FAILED: {e}")
        click.echo("=" * 80)
        click.echo()
        return 1


@cli.command()
@click.option(
    '--limit',
    default=100,
    type=int,
    help='Max assets to process (prevents OOM)'
)
@click.option(
    '--concurrency',
    default=5,
    type=int,
    help='Number of concurrent API requests'
)
@click.option(
    '--days-old',
    default=1,
    type=int,
    help='Sync assets older than N days'
)
def backfill(limit, concurrency, days_old):
    """
    Download historical OHLCV data for assets.

    Example:
        python3 bin/run_ingestion.py backfill --limit 500 --concurrency 5

    This command:
    1. Queries assets where last_synced IS NULL or is old
    2. Fetches OHLCV data from EODHD API
    3. Accumulates in batch buffer
    4. Writes to database in batches (5000+ rows)
    5. Updates Asset.last_synced timestamp
    6. Supports resume on subsequent runs
    """
    # Check API key
    api_key = os.environ.get('EODHD_API_KEY')
    if not api_key:
        click.echo("❌ EODHD_API_KEY not found in environment")
        click.echo("   Set it with: export EODHD_API_KEY='your-key'")
        sys.exit(1)

    click.echo("=" * 80)
    click.echo("📊 HISTORICAL DATA BACKFILL")
    click.echo("=" * 80)
    click.echo()

    try:
        db_config = DatabaseConfig()
        loader = EODHistoryLoader(api_key, db_config)
        loader.concurrency = concurrency

        click.echo(f"⚙️  Configuration:")
        click.echo(f"   Limit: {limit} assets")
        click.echo(f"   Concurrency: {concurrency}")
        click.echo(f"   Days old: {days_old}")
        click.echo()

        start_time = datetime.now()
        click.echo(f"⏳ Starting backfill...")

        summary = asyncio.run(loader.run_cycle(limit=limit, days_old=days_old))

        elapsed = summary['duration_sec']

        click.echo()
        click.echo("=" * 80)
        click.echo(f"✅ COMPLETE")
        click.echo("=" * 80)
        click.echo(f"Assets processed: {summary['total_assets']}")
        click.echo(f"Rows inserted: {summary['total_rows']}")
        click.echo(f"Failed: {summary['failed']}")
        click.echo(f"Duration: {elapsed:.1f}s")
        if summary['total_rows'] > 0:
            rate = summary['total_rows'] / elapsed
            click.echo(f"Rate: {rate:.0f} rows/sec")
        click.echo()

        return 0

    except Exception as e:
        click.echo()
        click.echo("=" * 80)
        click.echo(f"❌ FAILED: {e}")
        click.echo("=" * 80)
        click.echo()
        import traceback
        traceback.print_exc()
        return 1


@cli.command()
def status():
    """
    Show ingestion status and statistics.

    Displays:
    - Total assets in database
    - Assets with data (last_synced != NULL)
    - Assets without data (last_synced IS NULL)
    - Total OHLCV rows
    - Date range of data
    """
    click.echo("=" * 80)
    click.echo("📊 INGESTION STATUS")
    click.echo("=" * 80)
    click.echo()

    try:
        from src.data_nexus.database.connection import PostgresConnection

        conn = PostgresConnection()

        # Total assets
        total_assets = conn.query_scalar("SELECT COUNT(*) FROM assets")
        click.echo(f"Total assets: {total_assets}")

        # Assets with data
        with_data = conn.query_scalar(
            "SELECT COUNT(*) FROM assets WHERE last_synced IS NOT NULL"
        )
        click.echo(f"Assets with data: {with_data}")

        # Assets without data
        without_data = conn.query_scalar(
            "SELECT COUNT(*) FROM assets WHERE last_synced IS NULL"
        )
        click.echo(f"Assets without data: {without_data}")

        # Total rows
        total_rows = conn.query_scalar("SELECT COUNT(*) FROM market_data")
        click.echo(f"Total OHLCV rows: {total_rows}")

        # Date range
        min_date = conn.query_scalar(
            "SELECT MIN(time) FROM market_data"
        )
        max_date = conn.query_scalar(
            "SELECT MAX(time) FROM market_data"
        )
        click.echo(f"Date range: {min_date} to {max_date}")

        click.echo()
        return 0

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        click.echo()
        return 1


if __name__ == '__main__':
    cli()
