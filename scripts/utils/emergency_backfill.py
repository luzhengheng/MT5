#!/usr/bin/env python3
"""Emergency data backfill - populate empty database"""
import os, sys, requests
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
api_key = os.getenv("EODHD_API_TOKEN", "6496528053f746.84974385")
db_url = os.getenv("DB_URL", "postgresql://postgres:password@localhost:5432/data_nexus")

print("\n⬇️  EMERGENCY BACKFILL - Task #040.9\n")
print(f"Downloading AAPL.US (30-day history)...")

try:
    url = f"https://eodhd.com/api/eod/AAPL.US?api_token={api_key}&fmt=json&from=2025-11-29&to=2025-12-29"
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 else []
    
    print(f"✅ Downloaded {len(data)} records\n")
    print(f"💾 Inserting into database...")
    
    engine = create_engine(db_url)
    with engine.connect() as conn:
        for row in data:
            conn.execute(text("""
                INSERT INTO market_data (time, symbol, open, high, low, close, adjusted_close, volume)
                VALUES (:time, :symbol, :open, :high, :low, :close, :adjusted_close, :volume)
                ON CONFLICT DO NOTHING
            """), {
                "time": row.get("date"),
                "symbol": "AAPL.US",
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "adjusted_close": row.get("adjusted_close"),
                "volume": row.get("volume")
            })
        conn.execute(text("INSERT INTO assets (symbol) VALUES (:symbol) ON CONFLICT DO NOTHING"), {"symbol": "AAPL.US"})
        conn.commit()
    
    print(f"✅ Inserted {len(data)} rows\n")
    print(f"🎉 SUCCESS: Database populated\n")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Failed: {e}\n")
    sys.exit(1)
