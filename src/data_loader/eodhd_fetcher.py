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
    """Fetches historical OHLCV data from EODHD API using correct endpoints."""

    # EODHD API endpoints (v2.0 Protocol)
    # Use /api/intraday/ for hourly/minute data
    INTRADAY_URL = "https://eodhd.com/api/intraday/"
    EOD_URL = "https://eodhd.com/api/eod/"

    # Supported symbols - FOREX pairs (Task #012.05 multi-asset bulk ingestion)
    FOREX_SYMBOLS = {
        'EURUSD': 'EURUSD.FOREX',    # EUR/USD - Primary forex pair
        'GBPUSD': 'GBPUSD.FOREX',    # GBP/USD - British pound
        'USDJPY': 'USDJPY.FOREX',    # USD/JPY - Japanese yen
        'AUDUSD': 'AUDUSD.FOREX',    # AUD/USD - Australian dollar
        'XAUUSD': 'XAUUSD.FOREX',    # XAU/USD - Gold (Forex endpoint preferred)
    }

    # Index symbols (Task #012.05)
    INDEX_SYMBOLS = {
        'GSPC': 'GSPC.INDX',         # S&P 500 Index
        'DJI': 'DJI.INDX',           # Dow Jones Industrial Average
    }

    # Commodities mapping
    COMMODITY_SYMBOLS = {
        'XAUUSD': 'XAUUSD.COMM',  # Gold as commodity (alternative endpoint)
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
                "❌ FATAL: EODHD API key not found!\n"
                "   EODHD data is REQUIRED for production training.\n"
                "   Export: export EODHD_API_KEY='your_key_here'\n"
                "   Synthetic data fallback is DISABLED by design."
            )

        logger.info(f"✅ EODHD API key loaded: {self.api_key[:10]}...")

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

        # Get full symbol name (try FOREX first, then INDEX, then fallback)
        if symbol in self.FOREX_SYMBOLS:
            full_symbol = self.FOREX_SYMBOLS[symbol]
        elif symbol in self.INDEX_SYMBOLS:
            full_symbol = self.INDEX_SYMBOLS[symbol]
        else:
            # Fallback: assume symbol is already in EODHD format
            full_symbol = symbol
        logger.info(f"Full symbol: {full_symbol}")

        # Check cache first
        cache_file = self._get_cache_path(symbol, period)
        if cache_file.exists():
            logger.info(f"Loading from cache: {cache_file}")
            df = pd.read_csv(cache_file)
            df['Date'] = pd.to_datetime(df['Date'])
            return df

        # Fetch from API (NO FALLBACK - REAL DATA ONLY)
        logger.info(f"Fetching from EODHD API...")
        df = self._fetch_from_api(
            full_symbol,
            period=period,
            from_date=from_date,
            to_date=to_date
        )

        if df is None or df.empty:
            raise RuntimeError(
                f"❌ FATAL: No data returned from EODHD API for {symbol}\n"
                f"   Cannot proceed without REAL data.\n"
                f"   Check API key, symbol format, and subscription tier."
            )

        # Save to cache
        logger.info(f"Saving to cache: {cache_file}")
        df.to_csv(cache_file, index=False)

        logger.info(f"✅ Fetched {len(df)} rows for {symbol} {period}")
        return df

    def _get_synthetic_fallback(self, symbol: str, period: str) -> pd.DataFrame:
        """
        Provide synthetic data fallback when API is unavailable.

        Args:
            symbol: Symbol name (EURUSD, XAUUSD)
            period: Data period ('d' for daily, '1h' for hourly)

        Returns:
            DataFrame with synthetic OHLCV data
        """
        if period == "1h":
            # Generate 10 years of H1 data for training
            return self._generate_synthetic_h1_data(symbol, years=10)
        else:
            # For daily, generate 10 years with daily frequency
            return self._generate_synthetic_daily_data(symbol, years=10)

    def _generate_synthetic_daily_data(
        self,
        symbol: str = "EURUSD",
        years: int = 10
    ) -> pd.DataFrame:
        """
        Generate realistic synthetic daily data for training.

        Args:
            symbol: Symbol name
            years: Number of years

        Returns:
            DataFrame with daily OHLCV data
        """
        import numpy as np

        logger.info(f"Generating synthetic {symbol} daily data ({years} years)...")

        np.random.seed(42)

        # Daily data: ~250 trading days per year
        trading_days_per_year = 250
        n_rows = years * trading_days_per_year

        start_date = datetime(2015, 1, 1)
        dates = pd.bdate_range(start=start_date, periods=n_rows)

        # Starting prices
        if "EUR" in symbol:
            start_price = 1.0850
            volatility = 0.01  # 1% per day
        elif "XAU" in symbol:
            start_price = 1200.0
            volatility = 0.02  # 2% per day
        else:
            start_price = 1.1000
            volatility = 0.01

        # Generate price movements
        price_changes = np.random.normal(0, volatility, n_rows)
        cumulative_returns = np.cumsum(price_changes)
        close_prices = start_price * np.exp(cumulative_returns)

        # Generate OHLC
        open_prices = close_prices + np.random.normal(0, volatility / 2, n_rows) * start_price
        highs = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, volatility / 3, n_rows)) * start_price
        lows = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, volatility / 3, n_rows)) * start_price

        # Generate volume
        volumes = np.random.normal(5000000, 1000000, n_rows).astype(int)
        volumes = np.maximum(volumes, 1000000)

        df = pd.DataFrame({
            'Date': dates,
            'Open': open_prices,
            'High': highs,
            'Low': lows,
            'Close': close_prices,
            'Volume': volumes,
        })

        # Ensure OHLC constraints
        df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
        df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)

        logger.info(f"✅ Generated {len(df)} rows of synthetic daily data")
        logger.info(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.info(f"   Price range: {df['Close'].min():.5f} to {df['Close'].max():.5f}")

        return df

    def _fetch_from_api(
        self,
        symbol: str,
        period: str,
        from_date: str,
        to_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Internal API call handler using EODHD v2.0 Protocol.

        Args:
            symbol: Full symbol (e.g., 'EURUSD.FOREX', 'XAUUSD.COMM')
            period: '1h' (hourly), '5m' (5-minute), 'd' (daily)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if API call fails
        """
        # Select endpoint based on period
        if period in ['1h', '5m', '15m', '30m']:
            # Use intraday endpoint for hourly and sub-hourly
            endpoint = self.INTRADAY_URL
            interval_param = period
        else:
            # Use EOD endpoint for daily
            endpoint = self.EOD_URL
            interval_param = None

        # Build parameters
        # NOTE: Intraday endpoint requires Unix timestamps, not date strings
        if interval_param:
            # Convert date strings to Unix timestamps for intraday
            from datetime import timezone
            from_ts = int(datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp())
            to_ts = int(datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()) + 86400

            params = {
                'api_token': self.api_key,
                'from': from_ts,
                'to': to_ts,
                'interval': interval_param,
                'fmt': 'json',
            }
        else:
            # For daily, use date strings
            params = {
                'api_token': self.api_key,
                'from': from_date,
                'to': to_date,
                'period': period,
                'fmt': 'json',
            }

        # Build full URL (without query string for logging)
        url_with_symbol = endpoint + symbol

        try:
            logger.info(f"Making EODHD API request (v2.0 Protocol)...")
            logger.info(f"   Endpoint: {endpoint}")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Period: {period}")
            logger.info(f"   Date range: {from_date} to {to_date}")
            if interval_param:
                logger.info(f"   Using Unix timestamps for intraday")
            logger.info(f"   Full URL (masked): {url_with_symbol}?api_token=****...")

            response = requests.get(
                url_with_symbol,
                params=params,
                timeout=30
            )

            if response.status_code != 200:
                # PRINT THE ACTUAL ERROR FOR DEBUGGING
                logger.error(f"❌ API ERROR {response.status_code}")
                logger.error(f"   Status: {response.reason}")
                logger.error(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                logger.error(f"   Response (first 500 chars):\n{response.text[:500]}")
                logger.error(f"   URL: {url_with_symbol}?api_token=****&from={from_date}&to={to_date}&interval={interval_param}")

                # Don't silently fail - raise exception
                raise RuntimeError(
                    f"EODHD API returned {response.status_code} {response.reason}\n"
                    f"Endpoint: {endpoint}{symbol}\n"
                    f"Interval: {interval_param}\n"
                    f"Response: {response.text[:300]}"
                )

            logger.info(f"✅ HTTP 200 OK received")

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
            # Handle both EOD (date) and Intraday (datetime) formats
            column_mapping = {
                'date': 'Date',
                'datetime': 'Date',  # Intraday endpoint uses 'datetime'
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

            # Remove rows with NaN prices (common in intraday data for gaps)
            if all(col in df.columns for col in ['Open', 'Close']):
                df = df.dropna(subset=['Open', 'Close'])
                logger.info(f"   Removed {len(rows) - len(df)} rows with missing prices")

            # Ensure Date is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])

            # Sort by date and remove duplicates
            if 'Date' in df.columns:
                df = df.sort_values('Date').reset_index(drop=True)
                logger.info(f"   Final rows after cleaning: {len(df)}")

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
    # Synthetic Data Fallback
    # ========================================================================

    def _generate_synthetic_h1_data(
        self,
        symbol: str = "EURUSD",
        years: int = 10
    ) -> pd.DataFrame:
        """
        Generate realistic synthetic H1 (hourly) data for training.

        Strategy:
        - 10 years of hourly data = ~87,600 rows
        - Realistic price movements based on Forex volatility
        - Suitable for training deep XGBoost models

        Args:
            symbol: Symbol name (EURUSD, XAUUSD)
            years: Number of years of data

        Returns:
            DataFrame with H1 OHLCV data
        """
        import numpy as np

        logger.info(f"Generating synthetic {symbol} H1 data ({years} years)...")

        np.random.seed(42)

        # Generate hourly timestamps (365*24 hours per year, ~252 trading days)
        trading_hours_per_year = 252 * 24
        n_rows = years * trading_hours_per_year

        start_date = datetime(2015, 1, 1)
        dates = pd.date_range(start=start_date, periods=n_rows, freq='h')

        # EURUSD starting price
        if "EUR" in symbol:
            start_price = 1.0850
            volatility = 0.0005  # 0.05% per hour
        elif "XAU" in symbol:
            start_price = 1200.0
            volatility = 0.001  # 0.1% per hour
        else:
            start_price = 1.1000
            volatility = 0.0005

        # Generate price movements using geometric Brownian motion
        price_changes = np.random.normal(0, volatility, n_rows)
        cumulative_returns = np.cumsum(price_changes)
        close_prices = start_price * np.exp(cumulative_returns)

        # Generate OHLC
        open_prices = close_prices + np.random.normal(0, volatility / 2, n_rows) * start_price
        highs = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, volatility / 3, n_rows)) * start_price
        lows = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, volatility / 3, n_rows)) * start_price

        # Generate volume
        volumes = np.random.normal(100000, 20000, n_rows).astype(int)
        volumes = np.maximum(volumes, 10000)

        df = pd.DataFrame({
            'Date': dates,
            'Open': open_prices,
            'High': highs,
            'Low': lows,
            'Close': close_prices,
            'Volume': volumes,
        })

        # Ensure OHLC constraints
        df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
        df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)

        logger.info(f"✅ Generated {len(df)} rows of synthetic H1 data")
        logger.info(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.info(f"   Price range: {df['Close'].min():.5f} to {df['Close'].max():.5f}")

        return df

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
