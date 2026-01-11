import pandas as pd
import requests
import io
import time
from datetime import datetime, timedelta
from sqlalchemy import text
from src.database.timescale_client import TimescaleClient
import os

class EODHDTimescaleLoader:
    def __init__(self):
        # 默认使用 demo key 进行测试
        self.api_key = os.getenv("EODHD_API_KEY", "demo") 
        self.base_url = "https://eodhistoricaldata.com/api"
        self.db = TimescaleClient()
        self._init_schema()

    def _init_schema(self):
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
                conn.execute(text("SELECT create_hypertable('market_candles', 'time', if_not_exists => TRUE);"))
            except:
                pass
            conn.commit()
            print("✅ DB Schema Ready")

    def fetch_and_store(self, symbol, period='d'):
        print(f"⏳ Fetching {symbol}...")
        url = f"{self.base_url}/eod/{symbol}?api_token={self.api_key}&fmt=csv&period={period}"
        try:
            r = requests.get(url, stream=True)
            if r.status_code != 200: return
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
            if df.empty or 'Date' not in df.columns: return
            
            df.rename(columns={'Date': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
            df['symbol'] = symbol
            df['period'] = period
            df['time'] = pd.to_datetime(df['time'])
            
            df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'period']].to_sql(
                'market_candles', self.db.engine, if_exists='append', index=False, method='multi', chunksize=1000
            )
            print(f"✅ Ingested {len(df)} rows for {symbol}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    loader = EODHDTimescaleLoader()
    # 冒烟测试
    for sym in ["AAPL.US", "TSLA.US"]:
        loader.fetch_and_store(sym)
