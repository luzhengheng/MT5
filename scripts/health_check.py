#!/usr/bin/env python3
"""Health check script - verifies database connectivity"""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv("DB_URL", "postgresql://postgres:password@localhost:5432/data_nexus")

print("\n📊 Infrastructure Health Check\n")
print(f"Database: {db_url.split('@')[0].split('://')[1].split(':')[0]}:***@{db_url.split('@')[1]}\n")

try:
    engine = create_engine(db_url, connect_args={"connect_timeout": 3})
    with engine.connect() as conn:
        market = conn.execute(text("SELECT COUNT(*) FROM market_data")).fetchone()[0]
        assets = conn.execute(text("SELECT COUNT(*) FROM assets")).fetchone()[0]
    print(f"✅ Connection successful\n")
    print(f"📈 Table Statistics:")
    print(f"   market_data: {market:,} rows")
    print(f"   assets: {assets:,} rows\n")
    print("✅ System Healthy\n")
    sys.exit(0)
except Exception as e:
    print(f"❌ Connection Failed: {e}\n")
    print("❌ System Unhealthy\n")
    sys.exit(1)
