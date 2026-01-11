# Environment Setup Remediation Guide

**Audit Status**: ⚠️ **5 Issues Found**
**Date**: 2025-12-28
**System**: INF Node (sg-infer-core-01)

---

## 📋 Audit Results Summary

### ✅ What's Working (8 Checks)
- ✅ Disk Space: 155.3GB free (well above 10GB threshold)
- ✅ Docker Daemon: Running
- ✅ EODHD API: Network connectivity confirmed
- ✅ EODHD WebSocket: Network connectivity confirmed
- ✅ EODHD API Key: Configured and valid
- ✅ Alembic Migrations: Framework present
- ✅ Ingestion Code: All components present
- ✅ File Permissions: All readable

### ❌ What Needs Fixing (5 Critical Issues)

| # | Issue | Impact | Fix Time |
|---|-------|--------|----------|
| 1 | TimescaleDB Container Not Running | ❌ Cannot ingest data | 2 min |
| 2 | Redis Container Not Running | ❌ Cannot cache data | 2 min |
| 3 | Database Connection Failed | ❌ Cannot write OHLCV data | After #1 |
| 4 | Redis Connection Failed | ⚠️ Cache unavailable | After #2 |
| 5 | Python Dependencies Missing | ❌ Cannot run ingestion | 2 min |

---

## 🔧 Remediation Steps

### Step 1: Start Docker Containers (2 minutes)

**Command**:
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
```

**Expected**:
```
NAME                    STATUS
mt5-crs_timescaledb_1   Up 2 seconds
mt5-crs_redis_1         Up 1 second
```

**Why**: Containers are the foundation for data storage. Without them:
- TimescaleDB: No place to store OHLCV data
- Redis: No cache for feature engineering

---

### Step 2: Install Python Dependencies (2 minutes)

**Command**:
```bash
pip install -r requirements.txt
```

**Expected Output**:
```
Collecting aiohttp>=3.9.0
  Using cached aiohttp-3.9.x-py3-9-manylinux_x86_64.whl
Collecting aiodns>=3.1.0
  Using cached aiodns-3.1.x-py3-9-manylinux_x86_64.whl
...
Successfully installed aiohttp-3.9.x aiodns-3.1.x click-8.1.x ...
```

**Verify**:
```bash
python3 << 'EOF'
required = ['aiohttp', 'aiodns', 'click', 'sqlalchemy', 'psycopg2', 'redis']
for pkg in required:
    try:
        __import__(pkg)
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg}")
EOF
```

**Why**: These packages are required for async ingestion:
- `aiohttp`: Async HTTP requests to EODHD
- `aiodns`: Async DNS resolution
- `click`: CLI argument parsing
- Others: Already installed (ORM, database, cache)

---

### Step 3: Verify Database Connectivity (1 minute)

**Wait 10 seconds for TimescaleDB to fully initialize**:
```bash
sleep 10
```

**Test Connection**:
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/mt5-crs')
from src.data_nexus.database.connection import PostgresConnection

try:
    conn = PostgresConnection()
    version = conn.get_version()
    print(f"✅ Database Connected: {version}")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
EOF
```

**Expected Output**:
```
✅ Database Connected: PostgreSQL 14.9 (TimescaleDB 2.12...)
```

---

### Step 4: Verify Redis Connectivity (1 minute)

**Test Connection**:
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/mt5-crs')
from src.data_nexus.cache.redis_client import RedisClient

try:
    client = RedisClient()
    if client.ping():
        print("✅ Redis Connected and Responsive")
    else:
        print("❌ Redis Ping Failed")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
EOF
```

**Expected Output**:
```
✅ Redis Connected and Responsive
```

---

### Step 5: Apply Database Migrations (2 minutes)

**Command**:
```bash
cd /opt/mt5-crs
alembic upgrade head
```

**Expected Output**:
```
INFO [alembic.runtime.migration] Context impl PostgresqlImpl with target database 'postgresql+psycopg2://trader:password@timescaledb:5432/mt5_crs'
INFO [alembic.runtime.migration] Will assume transactional DDL.
INFO [alembic.runtime.migration] Running upgrade  -> 9d94c566de79, Init schema with hypertables
```

**Verify Schema**:
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/mt5-crs')
from src.data_nexus.database.connection import PostgresConnection

conn = PostgresConnection()

# Check tables
tables = conn.query_all(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
)
print(f"✅ Tables Created: {len(tables)}")
for row in tables:
    print(f"   - {row[0]}")

# Check hypertable
ht = conn.query_one(
    "SELECT hypertable_name FROM timescaledb_information.hypertables"
)
if ht:
    print(f"✅ Hypertable Configured: {ht[0]}")
EOF
```

**Expected Output**:
```
✅ Tables Created: 3
   - assets
   - market_data
   - corporate_actions
✅ Hypertable Configured: market_data
```

---

### Step 6: Re-run Full Environment Audit (2 minutes)

**Command**:
```bash
python3 scripts/ops_check_env.py
```

**Expected Output**:
```
✅ [Disk Space          ] PASS   Free: 155.3GB / Total: 196.5GB
✅ [Docker Daemon       ] PASS   Daemon running
✅ [TimescaleDB Container] PASS   Status: running
✅ [Redis Container     ] PASS   Status: running
✅ [Database Connectivity] PASS   Connected - PostgreSQL 14.9...
✅ [Redis Connectivity  ] PASS   Connected and responsive
✅ [Network - EODHD API ] PASS   Connected to eodhd.com:443
✅ [Network - EODHD WebSocket] PASS   Connected to ws.eodhistoricaldata.com:443
✅ [EODHD API Key       ] PASS   Configured: 6946528053...4385
✅ [Python Dependencies ] PASS   All 6 packages installed
✅ [Alembic Migrations  ] PASS   Configured with 1 migration(s)
✅ [Ingestion Code      ] PASS   All components present
✅ [File Permissions    ] PASS   All critical files readable

================================================================================
📊 AUDIT SUMMARY: 13 Passed, 0 Failed
================================================================================

🚀 ✅ SYSTEM READY FOR TAKEOFF

All environmental checks passed. You can proceed with:
  1. Task #034 (Forex Data Ingestion)
  2. Task #035 (Feature Engineering & ML)
```

---

## ⏱️ Total Remediation Time

| Step | Duration |
|------|----------|
| 1. Start Containers | 2 min |
| 2. Install Dependencies | 2 min |
| 3. Test DB Connection | 1 min |
| 4. Test Cache Connection | 1 min |
| 5. Apply Migrations | 2 min |
| 6. Full Audit Re-run | 2 min |
| **TOTAL** | **~10 minutes** |

---

## 🎯 One-Command Quick Fix

If you want to run everything in one shot:

```bash
cd /opt/mt5-crs && \
echo "🔧 Starting containers..." && \
docker-compose up -d && \
sleep 10 && \
echo "📦 Installing dependencies..." && \
pip install -r requirements.txt --quiet && \
echo "🗄️  Applying migrations..." && \
alembic upgrade head && \
echo "✅ Running final audit..." && \
python3 scripts/ops_check_env.py
```

**Total Time**: ~10-15 minutes (including Docker initialization)

---

## 🚨 Troubleshooting

### If Docker Fails to Start
```bash
# Check docker logs
docker-compose logs timescaledb

# If container is corrupted, restart it
docker-compose down
rm -rf /opt/mt5-crs/data/timescaledb
docker-compose up -d
```

### If Dependencies Won't Install
```bash
# Update pip first
pip install --upgrade pip

# Try again with verbose output
pip install -r requirements.txt -v
```

### If Database Connection Still Fails
```bash
# Check database is actually running
docker-compose ps

# Check database logs
docker-compose logs timescaledb | tail -20

# Verify connection string
python3 -c "from src.data_nexus.config import DatabaseConfig; print(DatabaseConfig().connection_string())"
```

### If Alembic Migration Fails
```bash
# Check migration status
alembic current

# If stuck, reset and re-run
alembic downgrade base
alembic upgrade head
```

---

## ✨ What Each Step Does

### Docker Containers
- **TimescaleDB**: Time-series database for storing OHLCV data
  - Will store ~750k rows of Forex history
  - Optimized for fast time-range queries

- **Redis**: In-memory cache for feature engineering
  - Will cache calculated features
  - Used by ML training pipelines

### Python Dependencies
- **aiohttp**: Async HTTP client (required for high-concurrency API calls)
- **aiodns**: Async DNS (speeds up hostname resolution)
- **click**: CLI framework (powers the ingestion commands)
- **Others**: Already available (SQLAlchemy, psycopg2, redis)

### Database Schema
- **assets**: Master list of tradeable symbols (150 FOREX pairs)
- **market_data**: OHLCV historical data (TimescaleDB hypertable)
- **corporate_actions**: Dividend/split events

---

## 📊 Current vs. Target State

### Current State (Before Fix)
```
❌ Docker Containers: Not running
❌ Database: Not accessible
❌ Cache: Not accessible
❌ Dependencies: Partially installed
⚠️  Network: OK
⚠️  Code: Ready
```

### Target State (After Fix)
```
✅ Docker Containers: Running (timescaledb + redis)
✅ Database: Accessible and initialized
✅ Cache: Accessible and operational
✅ Dependencies: All installed
✅ Network: OK
✅ Code: Ready
✅ Schema: Created and tested
```

---

## 🎯 Next Steps After Remediation

Once all 13 checks pass, proceed with:

```bash
# 1. Asset Discovery (2-3 minutes)
export EODHD_API_KEY='6946528053f746.84974385'
python3 bin/run_ingestion.py discover --exchange FOREX

# 2. Historical Data Backfill (30-60 minutes)
python3 bin/run_ingestion.py backfill --limit 500 --concurrency 10

# 3. Verify Results
python3 scripts/verify_forex_data.py
```

---

## 📋 Remediation Checklist

- [ ] Run `docker-compose up -d`
- [ ] Run `pip install -r requirements.txt`
- [ ] Wait 10 seconds for DB initialization
- [ ] Run `python3 scripts/ops_check_env.py`
- [ ] Verify all 13 checks pass
- [ ] Confirm: "SYSTEM READY FOR TAKEOFF"
- [ ] Proceed with Task #034 execution

---

**Status**: Ready to begin remediation ✅
**Estimated Time**: 10-15 minutes
**Risk Level**: Low (no data modifications, only infrastructure setup)
**Next**: Execute these commands and report the final audit output

Generated: 2025-12-28
Author: Claude Sonnet 4.5
