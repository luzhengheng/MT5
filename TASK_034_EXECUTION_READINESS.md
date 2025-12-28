# Task #034 Execution Readiness Guide

**Status**: ✅ Code Ready, ⏳ Awaiting Infrastructure
**Date**: 2025-12-28
**Phase**: 2 (Data Intelligence)

---

## 📋 Current State

### ✅ What's Ready
- SQLAlchemy ORM models (`src/data_nexus/models.py`) ✅
- Database schema & Alembic migrations (`alembic/`) ✅
- Asset Discovery service (`src/data_nexus/ingestion/asset_discovery.py`) ✅
- History Loader (`src/data_nexus/ingestion/history_loader.py`) ✅
- CLI interface (`bin/run_ingestion.py`) ✅
- Verification scripts ✅
- Dependencies listed (`requirements.txt`) ✅
- EODHD API key available ✅

### ⏳ What's Missing
- **TimescaleDB database running** ❌
- **Alembic migrations applied** ❌
- **Python dependencies installed** ⚠️

---

## 🚀 Execution Checklist

### Phase 1: Infrastructure Setup (5 minutes)

#### 1.1 Start Docker Containers
```bash
cd /opt/mt5-crs
docker-compose up -d
```

**Expected Output**:
```
Creating mt5-crs_timescaledb_1 ... done
Creating mt5-crs_redis_1 ... done
```

**Verify**:
```bash
docker-compose ps
# Should show both services as "Up"
```

#### 1.2 Wait for Database Readiness
```bash
# Wait ~10 seconds for TimescaleDB to initialize
sleep 10

# Test connection
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from src.data_nexus.database.connection import PostgresConnection
try:
    conn = PostgresConnection()
    print(f"✅ Database ready: {conn.get_version()}")
except Exception as e:
    print(f"❌ Not ready: {e}")
EOF
```

#### 1.3 Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Key packages for Task #034**:
```
aiohttp>=3.9.0       # Async HTTP
aiodns>=3.1.0        # Async DNS
click>=8.1.0         # CLI
sqlalchemy>=2.0.23   # ORM
psycopg2-binary>=2.9.9 # PostgreSQL
```

#### 1.4 Apply Database Migrations
```bash
alembic upgrade head
```

**Expected Output**:
```
INFO [alembic.runtime.migration] Context impl PostgresqlImpl with target database 'postgresql+psycopg2://trader:password@timescaledb:5432/mt5_crs'
INFO [alembic.runtime.migration] Will assume transactional DDL.
INFO [alembic.runtime.migration] Running upgrade  -> 9d94c566de79, Init schema with hypertables
```

**Verify**:
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from src.data_nexus.database.connection import PostgresConnection
conn = PostgresConnection()
result = conn.query_scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
print(f"✅ Tables created: {result} tables found")
EOF
```

---

### Phase 2: Asset Discovery (2-3 minutes)

#### 2.1 Run Asset Discovery
```bash
export EODHD_API_KEY='6946528053f746.84974385'
python3 bin/run_ingestion.py discover --exchange FOREX
```

**Expected Output**:
```
================================================================================
📥 ASSET DISCOVERY: FOREX
================================================================================

🔍 Discovering assets for FOREX...
   ✅ User: [account_name]
   API Limit: [limit]/day, Remaining: [remaining]
   ✅ EOD Data: 150 rows, 7 columns
      Fields: Code, Exchange, Name, Type, Country, Currency, ISIN

================================================================================
✅ SUCCESS
================================================================================
Added/updated: 150 assets
```

#### 2.2 Verify Assets in Database
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from src.data_nexus.database.connection import PostgresConnection
conn = PostgresConnection()

# Count Forex assets
count = conn.query_scalar("SELECT COUNT(*) FROM assets WHERE exchange='FOREX'")
print(f"✅ FOREX Assets in DB: {count}")

# Show sample
rows = conn.query_all("SELECT symbol, asset_type, last_synced FROM assets WHERE exchange='FOREX' LIMIT 5")
for row in rows:
    print(f"   {row[0]:15} | {row[1]:20} | {row[2]}")
EOF
```

**Expected Output**:
```
✅ FOREX Assets in DB: 150
   EURUSD.FOREX   | Currency            | None
   GBPUSD.FOREX   | Currency            | None
   USDJPY.FOREX   | Currency            | None
   ...
```

---

### Phase 3: Historical Data Ingestion (30-60 minutes)

#### 3.1 Start Backfill with High Concurrency
```bash
export EODHD_API_KEY='6946528053f746.84974385'
python3 bin/run_ingestion.py backfill --limit 500 --concurrency 10
```

**Expected Output** (live logging):
```
================================================================================
📊 HISTORICAL DATA BACKFILL
================================================================================

⚙️  Configuration:
   Limit: 500 assets
   Concurrency: 10
   Days old: 1

⏳ Starting backfill...
[2025-12-28 10:30:45] INFO: Starting load cycle: limit=500, days_old=1, concurrency=10
[2025-12-28 10:30:45] INFO: Found 150 assets to sync
[2025-12-28 10:30:46] INFO: Fetching EURUSD.FOREX...
[2025-12-28 10:30:47] INFO: Fetching GBPUSD.FOREX...
   → 5000 rows for EURUSD.FOREX
   → 5100 rows for GBPUSD.FOREX
...
[2025-12-28 10:35:20] INFO: Flushing 5000 rows to database...
[2025-12-28 10:40:00] INFO: Update last_synced for 150 assets...

================================================================================
✅ COMPLETE
================================================================================
Assets processed: 150
Rows inserted: 750000 (estimated for 20 years × 150 pairs)
Failed: 0
Duration: 245.3s
Rate: 3061 rows/sec
```

#### 3.2 Monitor Disk Usage
```bash
# Monitor in separate terminal during backfill
watch -n 5 'du -sh /opt/mt5-crs/data/timescaledb'
```

**Expected**: Disk usage should grow from ~100MB to ~2-3GB as data loads.

---

### Phase 4: Data Verification (2-3 minutes)

#### 4.1 Create Verification Script
```bash
cat > scripts/verify_forex_data.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/mt5-crs')

from src.data_nexus.database.connection import PostgresConnection
from datetime import datetime

def verify():
    db = PostgresConnection()

    print("=" * 80)
    print("📊 FOREX DATA VERIFICATION")
    print("=" * 80)
    print()

    with db.get_session() as session:
        # 1. Check Asset Count
        asset_count = db.query_scalar("SELECT COUNT(*) FROM assets WHERE exchange='FOREX'")
        print(f"✅ Total Forex Pairs: {asset_count}")

        # 2. Check Data Volume
        row_count = db.query_scalar("SELECT COUNT(*) FROM market_data")
        print(f"✅ Total OHLCV Rows: {row_count:,}")

        # 3. Check Date Range
        min_date = db.query_scalar("SELECT MIN(time) FROM market_data")
        max_date = db.query_scalar("SELECT MAX(time) FROM market_data")
        print(f"✅ Date Range: {min_date} to {max_date}")

        # 4. Sample Data (EURUSD)
        latest = db.query_one(
            "SELECT symbol, time, open, high, low, close, volume FROM market_data "
            "WHERE symbol='EURUSD.FOREX' ORDER BY time DESC LIMIT 1"
        )
        if latest:
            print(f"✅ EURUSD Latest: {latest[1]} | O:{latest[2]} H:{latest[3]} L:{latest[4]} C:{latest[5]} V:{latest[6]}")
        else:
            print(f"❌ EURUSD data missing!")

        # 5. Check Sync Status
        synced = db.query_scalar("SELECT COUNT(*) FROM assets WHERE last_synced IS NOT NULL AND exchange='FOREX'")
        unsynced = db.query_scalar("SELECT COUNT(*) FROM assets WHERE last_synced IS NULL AND exchange='FOREX'")
        print(f"✅ Assets Synced: {synced}/{asset_count}")
        print(f"✅ Assets Unsynced: {unsynced}/{asset_count}")

        # 6. Hypertable Status
        result = db.query_one(
            "SELECT hypertable_name, time_column_name, chunk_interval "
            "FROM timescaledb_information.hypertables WHERE hypertable_name='market_data'"
        )
        if result:
            print(f"✅ Hypertable: {result[0]} (chunks: {result[2]})")
        else:
            print(f"❌ Hypertable not found!")

    print()
    print("=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    verify()
EOF

chmod +x scripts/verify_forex_data.py
```

#### 4.2 Run Verification
```bash
python3 scripts/verify_forex_data.py
```

**Expected Output**:
```
================================================================================
📊 FOREX DATA VERIFICATION
================================================================================

✅ Total Forex Pairs: 150
✅ Total OHLCV Rows: 750,000
✅ Date Range: 2004-01-01 to 2025-12-27
✅ EURUSD Latest: 2025-12-27 | O:1.04123 H:1.04567 L:1.04001 C:1.04456 V:1500000
✅ Assets Synced: 150/150
✅ Assets Unsynced: 0/150
✅ Hypertable: market_data (chunks: INTERVAL '1 month')

================================================================================
✅ VERIFICATION COMPLETE
================================================================================
```

---

### Phase 5: Commit & Finalize (2 minutes)

#### 5.1 Commit Verification Script
```bash
git add scripts/verify_forex_data.py
git commit -m "test(task-034): Add Forex data verification script

Comprehensive verification of Forex ingestion including:
- Asset count and sync status
- Total OHLCV rows and date range
- Sample data validation (EURUSD)
- Hypertable configuration check
- Ready for production monitoring"
```

#### 5.2 Update Task Status
```bash
# Mark Task #034 as complete in Notion (if using CLI)
python3 scripts/project_cli.py finish
```

---

## ⏱️ Total Execution Time

| Phase | Duration |
|-------|----------|
| Infrastructure Setup | 5 min |
| Asset Discovery | 2 min |
| Historical Data Backfill | 45 min |
| Data Verification | 2 min |
| Commit & Finalize | 2 min |
| **TOTAL** | **~60 min** |

---

## 🔍 Troubleshooting

### Database Connection Issues
```bash
# Test connection
python3 << 'EOF'
from src.data_nexus.database.connection import PostgresConnection
try:
    conn = PostgresConnection()
    print(conn.get_version())
except Exception as e:
    print(f"Error: {e}")
EOF

# Check docker logs
docker-compose logs timescaledb
```

### API Rate Limits
If you see `429 Rate Limited` during backfill:
- Reduce concurrency: `--concurrency 5`
- Add delay between requests (modify history_loader.py)
- Pause and resume later: Data already synced won't be re-requested

### Disk Space Issues
If backfill fails with disk errors:
```bash
# Check disk usage
du -sh /opt/mt5-crs/data/timescaledb

# If needed, clean up and restart
docker-compose down
rm -rf /opt/mt5-crs/data/timescaledb
docker-compose up -d
# Re-run migrations and discovery
```

---

## 📊 Expected Results

After successful execution:
- ✅ 150 Forex currency pairs in `assets` table
- ✅ ~750,000 OHLCV rows in `market_data` hypertable (20 years × 150 pairs)
- ✅ All assets marked with `last_synced` timestamp
- ✅ Data partitioned into monthly chunks by TimescaleDB
- ✅ Ready for ML training (Task #035+)

---

## 🎯 Next Steps

Once Task #034 is complete:

1. **Task #034.5** (Optional): Real-time WebSocket Ingestion
   - Stream live tick data for active trading hours
   - Complement historical EOD data with intraday updates

2. **Task #035**: Feature Engineering & ML Training
   - Build trading signals using Forex OHLCV data
   - Train ML models on currency pair movements

3. **Task #036**: Live Trading System
   - Execute trades based on ML signals
   - Risk management and portfolio optimization

---

## 📝 Execution Log Template

When executing, capture logs in a file:

```bash
# Start execution
python3 bin/run_ingestion.py backfill --limit 500 --concurrency 10 | tee task_034_execution.log

# Verify
python3 scripts/verify_forex_data.py | tee -a task_034_execution.log

# Check final status
git log --oneline -5 | tee -a task_034_execution.log
```

This creates a complete audit trail of the execution.

---

**Ready for Execution**: Yes ✅
**Prerequisites**: Docker + Python environment + EODHD API key
**Estimated Duration**: ~60 minutes
**Risk Level**: Low (read-only API, schema already validated)

Generated: 2025-12-28
Author: Claude Sonnet 4.5
Status: Awaiting Infrastructure Setup & Execution
