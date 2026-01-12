#!/usr/bin/env python3
"""
Forex Data Loader for EODHD API
Specialized loader for 24/5 forex market data with weekend gap handling
"""
import pandas as pd
import requests
import io
import os
import argparse
from datetime import datetime, timedelta
from sqlalchemy import text
from src.database.timescale_client import TimescaleClient


class ForexLoader:
    """
    Forex-specific data loader with enhanced features:
    - 24-hour time alignment
    - Weekend gap detection and handling
    - Support for FOREX suffix symbols (e.g., EURUSD.FOREX)
    """

    def __init__(self):
        self.api_key = os.getenv("EODHD_API_TOKEN", "demo")
        self.base_url = "https://eodhistoricaldata.com/api"
        self.db = TimescaleClient()
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema with market_candles table"""
        with self.db.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_candles (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    open DOUBLE PRECISION,
                    high DOUBLE PRECISION,
                    low DOUBLE PRECISION,
                    close DOUBLE PRECISION,
                    volume DOUBLE PRECISION,
                    period TEXT DEFAULT 'd',
                    UNIQUE (time, symbol, period)
                );
            """))
            try:
                conn.execute(text(
                    "SELECT create_hypertable('market_candles', 'time', if_not_exists => TRUE);"
                ))
            except Exception:
                pass  # Hypertable already exists
            conn.commit()
            print("✅ Database schema ready")

    def fetch_forex_data(self, symbol: str, period: str = 'd',
                         start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetch forex data from EODHD API

        Args:
            symbol: Forex pair (e.g., 'EURUSD.FOREX')
            period: Candle period ('d', 'h', 'm')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with OHLCV data
        """
        # Default date range: last 5 years
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')

        url = (f"{self.base_url}/eod/{symbol}"
               f"?api_token={self.api_key}"
               f"&period={period}"
               f"&from={start_date}"
               f"&to={end_date}"
               f"&fmt=csv")

        print(f"📥 Fetching {symbol} from {start_date} to {end_date}...")

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}: {response.text}")

            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

            if df.empty:
                raise Exception("API returned empty dataset")

            # Standardize column names
            df.rename(columns={
                'Date': 'time',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)

            df['time'] = pd.to_datetime(df['time'])
            df['symbol'] = symbol
            df['period'] = period

            print(f"✅ Fetched {len(df)} candles")
            return df

        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            raise

    def detect_weekend_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and report weekend gaps in forex data

        Args:
            df: DataFrame with 'time' column

        Returns:
            DataFrame with gap analysis
        """
        df_sorted = df.sort_values('time').reset_index(drop=True)
        df_sorted['gap_days'] = df_sorted['time'].diff().dt.days

        # Identify weekend gaps (2-3 days)
        weekend_gaps = df_sorted[df_sorted['gap_days'].between(2, 3)]

        print(f"📊 Gap Analysis:")
        print(f"   - Total candles: {len(df)}")
        print(f"   - Weekend gaps detected: {len(weekend_gaps)}")
        print(f"   - Date range: {df_sorted['time'].min()} to {df_sorted['time'].max()}")

        return weekend_gaps

    def load_to_timescale(self, df: pd.DataFrame, symbol: str):
        """
        Load forex data into TimescaleDB

        Args:
            df: DataFrame with OHLCV data
            symbol: Symbol identifier
        """
        if df.empty:
            print("⚠️  Empty dataframe, skipping load")
            return

        required_cols = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'period']
        df_load = df[required_cols].copy()

        try:
            # Use ON CONFLICT to handle duplicates
            with self.db.engine.begin() as conn:
                # Insert with upsert logic
                for _, row in df_load.iterrows():
                    conn.execute(text("""
                        INSERT INTO market_candles
                        (time, symbol, open, high, low, close, volume, period)
                        VALUES (:time, :symbol, :open, :high, :low, :close, :volume, :period)
                        ON CONFLICT (time, symbol, period)
                        DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
                    """), row.to_dict())

            print(f"✅ Loaded {len(df_load)} rows for {symbol} into TimescaleDB")

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise

    def verify_load(self, symbol: str, period: str = 'd'):
        """
        Verify data was loaded correctly

        Args:
            symbol: Symbol to verify
            period: Period to verify
        """
        with self.db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as row_count,
                    MIN(time) as earliest,
                    MAX(time) as latest
                FROM market_candles
                WHERE symbol = :symbol AND period = :period
            """), {"symbol": symbol, "period": period})

            row = result.fetchone()
            print(f"\n📊 Verification for {symbol}:")
            print(f"   - Total rows: {row[0]}")
            print(f"   - Date range: {row[1]} to {row[2]}")

    def process_symbol(self, symbol: str, period: str = 'd',
                      start_date: str = None, end_date: str = None):
        """
        Complete pipeline: fetch, analyze, load, verify

        Args:
            symbol: Forex symbol (e.g., 'EURUSD.FOREX')
            period: Candle period
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        print(f"\n{'='*60}")
        print(f"Processing {symbol}")
        print(f"{'='*60}")

        # Fetch data
        df = self.fetch_forex_data(symbol, period, start_date, end_date)

        # Analyze gaps
        self.detect_weekend_gaps(df)

        # Load to database
        self.load_to_timescale(df, symbol)

        # Verify
        self.verify_load(symbol, period)

        print(f"{'='*60}\n")


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Load forex data from EODHD into TimescaleDB'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='EURUSD.FOREX',
        help='Forex symbol (e.g., EURUSD.FOREX)'
    )
    parser.add_argument(
        '--period',
        type=str,
        default='d',
        choices=['d', 'h', 'm'],
        help='Candle period'
    )
    parser.add_argument(
        '--from',
        dest='start_date',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--to',
        dest='end_date',
        type=str,
        help='End date (YYYY-MM-DD)'
    )

    args = parser.parse_args()

    loader = ForexLoader()
    loader.process_symbol(
        symbol=args.symbol,
        period=args.period,
        start_date=args.start_date,
        end_date=args.end_date
    )


if __name__ == "__main__":
    main()
