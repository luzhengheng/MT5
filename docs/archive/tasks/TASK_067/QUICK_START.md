# 🚀 QUICK START: Feast Feature Store Deployment

**Task**: #067 - Feast Feature Store Deployment
**Status**: ✅ Production Ready
**Last Updated**: 2026-01-09

---

## 60-Second Setup

```bash
# 1. Set database password (required for initialization)
export POSTGRES_PASSWORD='your-secure-password'

# 2. Run secure initialization
python3 scripts/init_feast.py

# 3. Verify installation works
python3 src/feature_repo/test_feature_store.py

# 4. You're done! Feature store is ready
```

---

## What Is Feast?

Feast is a **Feature Store** - a centralized repository for feature definitions and materialized feature values.

**In MT5-CRS context**:
- **Offline Store** (Postgres/TimescaleDB): Historical data for ML training
- **Online Store** (Redis): Real-time features for trading decisions
- **Registry**: Definitions of all features and entities

**Why it matters**: Ensures training and serving use the same feature definitions (prevents "training-serving skew").

---

## Current Feature Views (6 Total)

All features are defined but not yet computed (that's Task #068).

### 1. `ohlcv_features` (7 features)
Raw OHLCV data from Task #066.1:
- `open` - Opening price
- `high` - Highest price
- `low` - Lowest price
- `close` - Closing price
- `volume` - Trading volume
- `adjusted_close` - Split-adjusted close
- (plus timestamp)

### 2. `technical_indicators_ma` (8 features)
Moving average indicators (placeholder for Task #068):
- SMA: 5, 10, 20, 50, 200 day
- EMA: 12, 26 day

### 3. `technical_indicators_momentum` (7 features)
Momentum indicators (placeholder for Task #068):
- RSI-14
- MACD, Signal, Histogram
- Stochastic %K, %D

### 4. `technical_indicators_volatility` (7 features)
Volatility measures (placeholder for Task #068):
- ATR-14
- Bollinger Bands (Upper, Middle, Lower, Width)
- Standard Deviation-20

### 5. `volume_indicators` (5 features)
Volume-based features (placeholder for Task #068):
- Volume SMA-20
- Volume Ratio
- On-Balance Volume (OBV)
- Volume-Weighted Average Price (VWAP)

### 6. `price_action` (8 features)
Candle and price patterns (placeholder for Task #068):
- Daily return, log return
- Price range, body size
- Upper/lower shadows
- Candle direction (green/red)

---

## How to Use

### Get Current Features

```python
from feast import FeatureStore
from datetime import datetime
import pandas as pd

# Initialize store
store = FeatureStore(repo_path="src/feature_repo")

# Get features for a symbol
entity_rows = [{
    "symbol": "AAPL.US",
    "event_timestamp": datetime.now()
}]

features = store.get_online_features(
    entity_rows=entity_rows,
    features=[
        "ohlcv_features:close",
        "ohlcv_features:volume",
    ]
).to_df()

print(features)
# Output: columns [symbol, event_timestamp, close, volume]
#         rows will have NULL values (features not materialized yet)
```

### List All Entities

```python
store = FeatureStore(repo_path="src/feature_repo")
entities = store.list_entities()
print([e.name for e in entities])
# Output: ['symbol']
```

### List All Feature Views

```python
store = FeatureStore(repo_path="src/feature_repo")
views = store.list_feature_views()
for view in views:
    print(f"{view.name}: {len(view.schema)} features")
```

---

## Environment Variables

All credentials are loaded from environment or `.env` file:

```bash
# Required (must be set securely)
export POSTGRES_PASSWORD='your-password'

# Optional (these have defaults shown)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=trader
export POSTGRES_DB=mt5_crs
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
```

**Best Practice**: Use `python-dotenv`:
```bash
# Create .env.local with sensitive info (never commit)
POSTGRES_PASSWORD=secret123

# Load it in your code
from dotenv import load_dotenv
load_dotenv('.env.local')
```

---

## Troubleshooting

### Problem: "Connection refused on localhost:5432"
**Cause**: PostgreSQL not running or not accessible

**Solution**:
```bash
# Check Docker
docker ps | grep postgres
# Should show: timescaledb (Up, port 5432->5432)

# If not running:
docker-compose -f docker-compose.data.yml up -d timescaledb
```

### Problem: "POSTGRES_PASSWORD environment variable is not set"
**Cause**: Password not provided to `init_feast.py`

**Solution**:
```bash
# Set it before running
export POSTGRES_PASSWORD='your-password'
python3 scripts/init_feast.py
```

### Problem: "Connection to server... failed: fe_sendauth: no password supplied"
**Cause**: Wrong password or credentials not injected correctly

**Solution**:
```bash
# Verify credentials are correct
echo $POSTGRES_PASSWORD
echo $POSTGRES_HOST
echo $POSTGRES_USER

# Re-run initialization
python3 scripts/init_feast.py
```

### Problem: "FileNotFoundError: data/ohlcv_features.parquet"
**Cause**: Running from wrong directory or missing dummy data

**Solution**:
```bash
# Must run from project root
cd /opt/mt5-crs

# Dummy data is created during setup, but if missing:
python3 scripts/init_feast.py  # Re-run to recreate it
```

---

## Architecture Reference

```
┌─────────────────────────────────────────────────────────────┐
│                  Feast Feature Store                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Registry (src/feature_repo/data/registry.db)               │
│  └─ Entity: symbol                                          │
│  └─ 6 Feature Views (42 total features)                     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│          Offline Store                  Online Store         │
│      (Batch/Training)                (Serving/Trading)       │
│                                                               │
│  PostgreSQL/TimescaleDB ←──────────→ Redis (Cache)          │
│  (market_data.ohlcv_daily)            (Real-time access)   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Initialization Details

The `init_feast.py` script:

1. **Loads environment** from `.env` or system variables
2. **Validates credentials** (especially POSTGRES_PASSWORD)
3. **Creates temporary config** with injected passwords
4. **Runs `feast apply`** to register features
5. **Restores original config** (no credentials left behind)
6. **Cleans up temporary files**

This approach ensures credentials are **never committed to git**.

---

## Next Steps

### For Task #068 (Feature Computation)
You'll need to:
1. Create feature computation functions (e.g., `compute_sma_20()`)
2. Define `@on_demand_feature_view` decorators for real-time computation
3. Create Feast materialization job to push features to Redis
4. Test end-to-end feature retrieval

### For Task #069+ (ML Training)
You'll need to:
1. Use `store.get_historical_features()` to fetch training data from offline store
2. Create training datasets with features + labels
3. Train ML models
4. Evaluate on validation sets

---

## Key Files

| File | Purpose |
|------|---------|
| `src/feature_repo/definitions.py` | Feature view definitions |
| `src/feature_repo/feature_store.yaml` | Feast configuration (template, no creds) |
| `scripts/init_feast.py` | Secure initialization script |
| `src/feature_repo/test_feature_store.py` | Infrastructure validation |
| `src/feature_repo/data/registry.db` | Feast registry (git-ignored) |

---

## Common Commands

```bash
# Initialize feature store
python3 scripts/init_feast.py

# Test infrastructure
python3 src/feature_repo/test_feature_store.py

# List entities in Feast
cd src/feature_repo && feast entities list

# List feature views
cd src/feature_repo && feast feature-views list

# Materialize features (after Task #068)
cd src/feature_repo && feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

---

## References

- [Feast Documentation](https://docs.feast.dev/)
- [Task #066](../../TASK_066): EODHD Bulk Ingestion
- [Task #066.1](../../TASK_066.1): Data Validation
- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md): Full technical details

---

**Questions?** See COMPLETION_REPORT.md for comprehensive technical documentation.
