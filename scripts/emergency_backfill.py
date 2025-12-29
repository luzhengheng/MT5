#!/usr/bin/env python3
"""
EMERGENCY DATA BACKFILL SCRIPT

Task #040.5: Emergency Data Injection (Fix Empty DB)

This script performs a forceful, verbose data injection to fix empty database tables.
It will:
1. Verify API credentials
2. Download real data for a single symbol (AAPL.US)
3. Insert into database with immediate verification
4. Report row counts at each step

Usage:
    export EODHD_API_KEY="YOUR_API_KEY"
    python3 scripts/emergency_backfill.py

"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import logging

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_api_key():
    """Verify EODHD API key is available."""
    print("=" * 80)
    print("🔐 STEP 1: VERIFY API CREDENTIALS")
    print("=" * 80)
    print()

    api_key = os.getenv("EODHD_API_KEY")

    if not api_key:
        print("❌ CRITICAL: EODHD_API_KEY not set")
        print()
        print("Set it with:")
        print("  export EODHD_API_KEY='your_real_token'")
        return False

    # Mask the key
    masked = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    print(f"✅ API Key found: {masked}")
    print()
    return api_key


def download_single_symbol(api_key: str, symbol: str = "AAPL.US") -> dict:
    """Download real data for single symbol."""
    print("=" * 80)
    print(f"⬇️  STEP 2: DOWNLOAD DATA FOR {symbol}")
    print("=" * 80)
    print()

    import requests

    base_url = "https://eodhd.com/api"

    # Use 30 days of history
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    url = f"{base_url}/eod/{symbol}"
    params = {
        "api_token": api_key,
        "fmt": "json",
        "from": from_date,
        "to": to_date
    }

    print(f"📡 Downloading from EODHD API...")
    print(f"   URL: {url}")
    print(f"   Symbol: {symbol}")
    print(f"   Date range: {from_date} to {to_date}")
    print()

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data:
            print("❌ No data returned from API")
            print(f"   Response status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return {}

        if isinstance(data, list):
            print(f"✅ Downloaded {len(data)} records for {symbol}")
            print(f"   Sample record: {data[0] if data else 'N/A'}")
            print()
            return {"symbol": symbol, "data": data}
        else:
            print(f"❌ Unexpected response format: {type(data)}")
            return {}

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 401:
            print("   Possible issue: Invalid or expired API key")
        elif e.response.status_code == 403:
            print("   Possible issue: API access denied")
        return {}
    except Exception as e:
        print(f"❌ Download failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


def verify_database_connection():
    """Verify database is accessible."""
    print("=" * 80)
    print("🗄️  STEP 3: VERIFY DATABASE CONNECTION")
    print("=" * 80)
    print()

    try:
        from src.data_nexus.database.connection import PostgresConnection

        print("📡 Connecting to PostgreSQL...")
        conn = PostgresConnection()

        # Get initial row counts
        result = conn.query_all("SELECT count(*) as count FROM market_data")
        market_data_count = result[0][0] if result else 0

        result = conn.query_all("SELECT count(*) as count FROM assets")
        assets_count = result[0][0] if result else 0

        print(f"✅ Database connection successful!")
        print()
        print(f"📊 BEFORE IMPORT:")
        print(f"   market_data: {market_data_count:,} rows")
        print(f"   assets: {assets_count:,} rows")
        print()

        return conn, market_data_count, assets_count

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print()
        print("Make sure PostgreSQL is running:")
        print("  - Docker: docker-compose up -d postgres")
        print("  - Local: systemctl start postgresql")
        print()
        import traceback
        traceback.print_exc()
        return None, 0, 0


def insert_data(conn, symbol_data: dict) -> int:
    """Insert downloaded data into database."""
    print("=" * 80)
    print("💾 STEP 4: INSERT DATA INTO DATABASE")
    print("=" * 80)
    print()

    if not symbol_data or "data" not in symbol_data:
        print("❌ No data to insert")
        return 0

    import pandas as pd

    data = symbol_data["data"]
    symbol = symbol_data["symbol"]

    try:
        print(f"📝 Preparing {len(data)} records for insertion...")

        # Convert to DataFrame
        df = pd.DataFrame(data)
        df["symbol"] = symbol

        # Ensure correct column names and types
        df["time"] = pd.to_datetime(df["date"])
        df["adjusted_close"] = df.get("adjusted_close", df["close"])

        # Select and rename columns
        save_df = df[["time", "symbol", "open", "high", "low", "close", "adjusted_close", "volume"]].copy()
        save_df = save_df.dropna()

        print(f"✅ Prepared {len(save_df)} clean records")
        print()

        print(f"🔄 Inserting into market_data...")

        from sqlalchemy import create_engine
        engine = conn.engine

        # Insert in batches
        batch_size = 1000
        rows_inserted = 0

        for i in range(0, len(save_df), batch_size):
            batch = save_df.iloc[i:i + batch_size]
            try:
                batch.to_sql(
                    "market_data",
                    con=engine,
                    if_exists="append",
                    index=False,
                    method="multi",
                    chunksize=1000
                )
                rows_inserted += len(batch)
                print(f"   Batch {i//batch_size + 1}: Inserted {len(batch)} rows (total: {rows_inserted})")
            except Exception as e:
                print(f"   ⚠️  Batch {i//batch_size + 1} failed: {e}")

        print()
        print(f"✅ Inserted {rows_inserted} rows into market_data")
        print()

        # Register asset
        print(f"🏷️  Registering asset {symbol}...")

        register_query = f"""
            INSERT INTO assets (symbol, exchange, asset_type, is_active)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE
            SET is_active = TRUE, updated_at = NOW()
        """

        try:
            conn.execute(register_query, (symbol, "US", "Common Stock", True))
            print(f"✅ Asset registered: {symbol}")
            print()
        except Exception as e:
            print(f"⚠️  Asset registration failed: {e}")

        return rows_inserted

    except Exception as e:
        print(f"❌ Insertion failed: {e}")
        import traceback
        traceback.print_exc()
        return 0


def verify_final_counts(conn, initial_market, initial_assets) -> tuple:
    """Verify final row counts after insertion."""
    print("=" * 80)
    print("✅ STEP 5: VERIFY FINAL ROW COUNTS")
    print("=" * 80)
    print()

    try:
        result = conn.query_all("SELECT count(*) as count FROM market_data")
        final_market = result[0][0] if result else 0

        result = conn.query_all("SELECT count(*) as count FROM assets")
        final_assets = result[0][0] if result else 0

        print(f"📊 FINAL COUNTS:")
        print(f"   market_data: {final_market:,} rows (was {initial_market:,}) → +{final_market - initial_market:,}")
        print(f"   assets: {final_assets:,} rows (was {initial_assets:,}) → +{final_assets - initial_assets:,}")
        print()

        if final_market > 0 and final_assets > 0:
            print("🎉 SUCCESS: Database now has data!")
            return True, final_market, final_assets
        else:
            print("❌ FAILURE: Database still empty")
            return False, final_market, final_assets

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False, 0, 0


def main():
    """Main execution flow."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "EMERGENCY DATA BACKFILL SCRIPT - Task #040.5".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Step 1: Verify API key
    api_key = verify_api_key()
    if not api_key:
        return 1

    # Step 2: Download data
    symbol_data = download_single_symbol(api_key, "AAPL.US")
    if not symbol_data:
        print("⚠️  Download failed, but will continue if database is available")

    # Step 3: Verify database connection
    conn, initial_market, initial_assets = verify_database_connection()
    if not conn:
        print()
        print("=" * 80)
        print("❌ FATAL: Cannot proceed without database connection")
        print("=" * 80)
        return 1

    # Step 4: Insert data
    if symbol_data:
        rows_inserted = insert_data(conn, symbol_data)
    else:
        print("⚠️  Skipping data insertion (no data downloaded)")
        rows_inserted = 0

    # Step 5: Verify final counts
    success, final_market, final_assets = verify_final_counts(
        conn, initial_market, initial_assets
    )

    print()
    print("=" * 80)
    if success:
        print("✅ EMERGENCY BACKFILL COMPLETE - DATABASE RESTORED")
        print("=" * 80)
        print()
        print(f"Next steps:")
        print(f"  1. Run audit: python3 scripts/audit_current_task.py")
        print(f"  2. Finish task: python3 scripts/project_cli.py finish")
        return 0
    else:
        print("❌ EMERGENCY BACKFILL INCOMPLETE")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
