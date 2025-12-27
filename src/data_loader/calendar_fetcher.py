#!/usr/bin/env python3
"""
Task #027: EODHD Economic Calendar Fetcher
===========================================

Fetches high-impact economic events from EODHD Economic Calendar API.

These events correlate with market volatility and can be used to:
1. Filter out high-volatility periods during training
2. Add event features to the feature engineering pipeline
3. Identify macro-driven market movements

Protocol: v2.0 (Official EODHD Protocol)
"""

import os
import sys
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Economic Calendar Fetcher
# ============================================================================

class CalendarFetcher:
    """Fetches economic events from EODHD Economic Calendar API."""

    # EODHD API endpoint for economic calendar
    CALENDAR_URL = "https://eodhd.com/api/calendar/economic"

    # Data directory
    DATA_DIR = Path("/opt/mt5-crs/data/raw")

    # High-impact currencies (USD, EUR, GBP, etc)
    MAJOR_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Calendar Fetcher.

        Args:
            api_key: EODHD API key (defaults to EODHD_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("EODHD_API_KEY")

        if not self.api_key:
            raise ValueError(
                "❌ FATAL: EODHD API key not found!\n"
                "   Economic calendar requires API access.\n"
                "   Export: export EODHD_API_KEY='your_key_here'"
            )

        logger.info(f"✅ EODHD API key loaded: {self.api_key[:10]}...")

        # Ensure data directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory: {self.DATA_DIR}")

    def fetch_calendar(
        self,
        from_date: str = "2015-01-01",
        to_date: Optional[str] = None,
        min_importance: int = 3
    ) -> pd.DataFrame:
        """
        Fetch economic calendar events.

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD), defaults to today
            min_importance: Minimum importance level (1-3, where 3=High)

        Returns:
            DataFrame with economic events
        """
        if to_date is None:
            to_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching economic calendar events from {from_date} to {to_date}...")

        try:
            # Build API request
            params = {
                'api_token': self.api_key,
                'from': from_date,
                'to': to_date,
                'fmt': 'json',
            }

            logger.info(f"Making API request to: {self.CALENDAR_URL}")
            logger.info(f"   Date range: {from_date} to {to_date}")
            logger.info(f"   Min importance: {min_importance}")

            response = requests.get(
                self.CALENDAR_URL,
                params=params,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"❌ API ERROR {response.status_code}")
                logger.error(f"   Status: {response.reason}")
                logger.error(f"   Response: {response.text[:200]}")
                raise RuntimeError(
                    f"EODHD Calendar API returned {response.status_code}"
                )

            logger.info(f"✅ HTTP 200 OK received")

            # Parse response
            data = response.json()

            if not isinstance(data, list):
                logger.error(f"❌ Expected list response, got {type(data)}")
                return pd.DataFrame()

            logger.info(f"✅ Received {len(data)} total events")

            # Convert to DataFrame
            df = pd.DataFrame(data)

            if df.empty:
                logger.warning("No calendar events returned")
                return df

            # Clean up column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]

            # Filter for major currencies
            if 'currency' in df.columns:
                df = df[df['currency'].isin(self.MAJOR_CURRENCIES)]
                logger.info(f"✅ Filtered to {len(df)} events in major currencies")

            # Filter for high-impact events
            if 'importance' in df.columns:
                # Convert importance to numeric if needed
                importance_map = {'Low': 1, 'Medium': 2, 'High': 3}
                if df['importance'].dtype == 'object':
                    df['importance'] = df['importance'].map(importance_map).fillna(df['importance'])

                high_impact = df[df['importance'] >= min_importance]
                logger.info(f"✅ {len(high_impact)} high-impact events (importance >= {min_importance})")
                df = high_impact

            # Convert date column to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            # Sort by date
            if 'date' in df.columns:
                df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"❌ Failed to fetch calendar: {e}")
            raise

    def save_calendar(self, df: pd.DataFrame, filename: str = "macro_events.csv"):
        """
        Save calendar DataFrame to CSV.

        Args:
            df: DataFrame to save
            filename: Output filename
        """
        if df.empty:
            logger.warning("Calendar DataFrame is empty, skipping save")
            return

        filepath = self.DATA_DIR / filename
        logger.info(f"Saving calendar to: {filepath}")

        df.to_csv(filepath, index=False)
        logger.info(f"✅ Saved {len(df)} events to {filepath}")

    def fetch_and_save(
        self,
        from_date: str = "2015-01-01",
        to_date: Optional[str] = None,
        min_importance: int = 3,
        filename: str = "macro_events.csv"
    ) -> pd.DataFrame:
        """
        Fetch calendar and save to file.

        Args:
            from_date: Start date
            to_date: End date
            min_importance: Minimum importance level
            filename: Output filename

        Returns:
            DataFrame with events
        """
        df = self.fetch_calendar(from_date, to_date, min_importance)
        self.save_calendar(df, filename)
        return df


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Fetch economic calendar for recent months."""
    print("=" * 70)
    print("📅 EODHD Economic Calendar Fetcher")
    print("=" * 70)
    print()

    try:
        fetcher = CalendarFetcher()

        # Fetch high-impact events from 2015 to today
        df = fetcher.fetch_and_save(
            from_date="2015-01-01",
            to_date=None,  # Use today
            min_importance=3,  # High impact only
            filename="macro_events.csv"
        )

        # Summary
        print()
        print("=" * 70)
        print("✅ Calendar Fetch Complete")
        print("=" * 70)
        print()

        if not df.empty:
            print(f"Total events: {len(df)}")
            print()
            print("Columns:", list(df.columns))
            print()
            print("Sample events:")
            print(df[['date', 'event', 'currency', 'importance']].head(10))
            print()

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
