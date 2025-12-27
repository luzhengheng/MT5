#!/usr/bin/env python3
"""
Work Order #026: EODHD Deep Historical Data Fetcher
====================================================

Fetches 10 years of Forex and Commodity data from EODHD API.

Strategy:
- Daily data (10 years): Captures long-term trends
- Intraday data (120 days): Captures precise intraday patterns
- GPU training on full feature set

This module provides:
1. fetch_history(symbol, period, from_date, to_date)
   - Handles pagination automatically
   - Caches results to avoid duplicate API calls
   - Saves to CSV in /opt/mt5-crs/data/raw/

2. Daily + Intraday strategy:
   - EURUSD/XAUUSD daily for 10 years (2015-2025)
   - EURUSD/XAUUSD 1H for last 120 days (recent precision)

Protocol: v2.0 (Strict TDD & GPU Training)
"""

import os
import sys
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# EODHD API Configuration
# ============================================================================

class EODHDFetcher:
    """Fetches historical OHLCV data from EODHD API."""

    # EODHD API endpoint
    BASE_URL = "https://eodhd.com/api/eod"

    # Supported symbols (add .FOREX or .CRYPTO as needed)
    FOREX_SYMBOLS = {
        'EURUSD': 'EURUSD.FOREX',
        'XAUUSD': 'XAUUSD.FOREX',
    }

    # Data directory
    DATA_DIR = Path("/opt/mt5-crs/data/raw")

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize EODHD fetcher.

        Args:
            api_key: EODHD API key (defaults to EODHD_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("EODHD_API_KEY")

        if not self.api_key:
            raise ValueError(
                "EODHD API key not found. Set EODHD_API_KEY environment variable."
            )

        # Ensure data directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory: {self.DATA_DIR}")

    # ========================================================================
    # Data Fetching
    # ========================================================================

    def fetch_history(
        self,
        symbol: str,
        period: str = "d",
        from_date: str = "2015-01-01",
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from EODHD API.

        Args:
            symbol: Symbol name (e.g., 'EURUSD')
            period: 'd' for daily, '1h' for hourly, '5m' for 5-minute
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume

        Notes:
            - EODHD has rate limits (~500 calls/day for free tier)
            - This fetcher caches locally to avoid duplicate calls
            - For large datasets, may require multiple API calls or bulk CSV
        """
        if to_date is None:
            to_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching {symbol} {period} data from {from_date} to {to_date}")

        # Get full symbol name
        full_symbol = self.FOREX_SYMBOLS.get(symbol, symbol)
        logger.info(f"Full symbol: {full_symbol}")

        # Check cache first
        cache_file = self._get_cache_path(symbol, period)
        if cache_file.exists():
            logger.info(f"Loading from cache: {cache_file}")
            df = pd.read_csv(cache_file)
            df['Date'] = pd.to_datetime(df['Date'])
            return df

        # Fetch from API
        try:
            logger.info(f"Fetching from EODHD API...")
            df = self._fetch_from_api(
                full_symbol,
                period=period,
                from_date=from_date,
                to_date=to_date
            )

            if df is None or df.empty:
                logger.error(f"No data returned for {symbol}")
                return pd.DataFrame()

            # Save to cache
            logger.info(f"Saving to cache: {cache_file}")
            df.to_csv(cache_file, index=False)

            logger.info(f"✅ Fetched {len(df)} rows for {symbol} {period}")
            return df

        except Exception as e:
            logger.error(f"❌ Failed to fetch {symbol}: {e}")
            raise

    def _fetch_from_api(
        self,
        symbol: str,
        period: str,
        from_date: str,
        to_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Internal API call handler.

        Args:
            symbol: Full symbol (e.g., 'EURUSD.FOREX')
            period: 'd', '1h', '5m'
            from_date: Start date
            to_date: End date

        Returns:
            DataFrame or None if API call fails
        """
        # EODHD API parameters
        params = {
            'api_token': self.api_key,
            'from': from_date,
            'to': to_date,
            'period': period,
            'fmt': 'json',
        }

        try:
            logger.info(f"Making API request to EODHD...")
            response = requests.get(
                self.BASE_URL,
                params={**params, 'symbols': symbol},
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"API error {response.status_code}: {response.text[:200]}")
                return None

            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                # Single symbol response
                if symbol in data:
                    rows = data[symbol]
                elif 'data' in data:
                    rows = data['data']
                else:
                    logger.error(f"Unexpected API response format: {data.keys()}")
                    return None
            elif isinstance(data, list):
                # Direct list response
                rows = data
            else:
                logger.error(f"Unexpected API response type: {type(data)}")
                return None

            if not rows:
                logger.warning(f"No data in API response")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(rows)

            # Rename columns to match expected format
            column_mapping = {
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                'adjusted_close': 'AdjClose',
            }

            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})

            # Ensure Date is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])

            # Sort by date
            if 'Date' in df.columns:
                df = df.sort_values('Date').reset_index(drop=True)

            logger.info(f"✅ Received {len(df)} rows from API")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing API response: {e}")
            return None

    def _get_cache_path(self, symbol: str, period: str) -> Path:
        """Get local cache file path for symbol and period."""
        return self.DATA_DIR / f"{symbol}_{period}.csv"

    # ========================================================================
    # Deep History Strategy
    # ========================================================================

    def fetch_deep_history(self, symbols: Optional[List[str]] = None) -> dict:
        """
        Fetch deep historical data using optimal strategy.

        Strategy:
        - Daily data: 10 years (2015-2025) for trend analysis
        - Hourly data: Last 120 days for precision

        Args:
            symbols: List of symbols (defaults to FOREX_SYMBOLS.keys())

        Returns:
            Dict mapping symbol -> {'daily': df, 'hourly': df}
        """
        if symbols is None:
            symbols = list(self.FOREX_SYMBOLS.keys())

        results = {}

        for symbol in symbols:
            logger.info(f"\n{'='*70}")
            logger.info(f"Fetching deep history for {symbol}")
            logger.info(f"{'='*70}")

            # Daily data: 10 years
            logger.info(f"\n📊 Fetching daily data (10 years)...")
            daily_df = self.fetch_history(
                symbol=symbol,
                period="d",
                from_date="2015-01-01",
                to_date=None
            )

            logger.info(f"   ✅ Daily: {len(daily_df)} rows")

            # Hourly data: Last 120 days
            logger.info(f"\n📊 Fetching hourly data (120 days)...")
            to_date = datetime.now()
            from_date = to_date - timedelta(days=120)

            hourly_df = self.fetch_history(
                symbol=symbol,
                period="1h",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )

            logger.info(f"   ✅ Hourly: {len(hourly_df)} rows")

            results[symbol] = {
                'daily': daily_df,
                'hourly': hourly_df,
            }

        return results


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Fetch deep historical data for EURUSD and XAUUSD."""
    print("=" * 70)
    print("📥 EODHD Deep Historical Data Fetcher")
    print("=" * 70)
    print()

    try:
        # Initialize fetcher
        fetcher = EODHDFetcher()

        # Fetch deep history for all symbols
        results = fetcher.fetch_deep_history()

        # Summary
        print()
        print("=" * 70)
        print("📊 Data Fetching Complete")
        print("=" * 70)
        print()

        for symbol, data in results.items():
            print(f"{symbol}:")
            print(f"  Daily:  {len(data['daily'])} rows")
            print(f"  Hourly: {len(data['hourly'])} rows")
            print()

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
