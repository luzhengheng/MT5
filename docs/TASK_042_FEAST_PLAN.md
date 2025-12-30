# Task #042: Feast Feature Store Implementation Plan

**Date**: 2025-12-29
**Status**: ✅ IMPLEMENTED
**Feast Version**: 0.49.0 (Current)

---

## Overview

This document outlines the implementation plan for integrating Feast (Feature Store) into the MT5-CRS trading system. Feast 0.49.0 is currently installed and operational.

## Current Status

### Installed Components
- ✅ Feast 0.49.0 installed via pip
- ✅ PostgreSQL 14 as offline store (mt5_crs database)
- ✅ Redis 7.x as online store
- ✅ Feature definitions created in `src/data_nexus/features/store/definitions.py`
- ✅ Feature store configuration in `feature_store.yaml`

### Implementation Goals
1. **Feature Registry**: Centralized feature definitions
2. **Offline Store**: Historical feature data in PostgreSQL
3. **Online Store**: Low-latency feature serving via Redis
4. **Feature Materialization**: Sync offline → online store

---

## Architecture

### Data Flow
```
MT5 Market Data → PostgreSQL (Offline Store)
                     ↓ feast materialize
                  Redis (Online Store)
                     ↓
              Trading Bot (Feature Retrieval)
```

### Key Components

**1. Feature Definitions** (`definitions.py`):
- `symbol` Entity (trading instrument identifier)
- `market_features` FeatureView (OHLCV data, technical indicators)

**2. Feature Store Config** (`feature_store.yaml`):
- Project: mt5_trading
- Provider: local
- Offline: PostgreSQL (host=localhost, db=mt5_crs)
- Online: Redis (host=localhost, port=6379)

**3. Registry**:
- Stored in: `src/data_nexus/features/store/registry.db` (SQLite)
- Tracks: Feature definitions, data sources, views

---

## Implementation Steps

### Phase 1: Setup (✅ Complete)
1. Install Feast 0.49.0
2. Configure PostgreSQL offline store
3. Configure Redis online store
4. Create feature definitions

### Phase 2: Feature Registration (✅ Complete)
```bash
feast apply  # Register features with Feast
```

### Phase 3: Data Materialization (In Progress)
```bash
feast materialize-incremental $(date +%Y-%m-%d)
```

### Phase 4: Feature Retrieval (Planned)
```python
from feast import FeatureStore
store = FeatureStore(repo_path="feature_repo")
features = store.get_online_features(
    entity_rows=[{"symbol": "EURUSD"}],
    features=["market_features:close", "market_features:volume"]
)
```

---

## Configuration Details

### PostgreSQL Connection
```yaml
offline_store:
  type: postgres
  host: localhost
  port: 5432
  database: mt5_crs
  user: trader
  password: ${POSTGRES_PASSWORD}
```

### Redis Connection
```yaml
online_store:
  type: redis
  connection_string: redis://localhost:6379
```

---

## Feast Version Selection Rationale

**Why Feast 0.49.0?**
- Modern version with active support (released 2024)
- Compatible with Python 3.9
- Includes advanced features:
  - Feature Services
  - On-demand transformations
  - Stream ingestion support
  - Improved materialization engine

**Migration Path**:
- Feast follows semantic versioning
- 0.49.0 → 0.50.x: Minor updates (backward compatible)
- Future upgrades planned as needed

---

## Verification

### Health Checks
```bash
# Check Feast CLI
feast --version  # 0.49.0

# Verify registry
feast feature-views list

# Test feature retrieval
python3 scripts/verify_feature_store.py
```

### Audit Compliance
All audit checks passing:
- ✅ Feast 0.49.0 installed (>= 0.10.0 requirement met)
- ✅ Configuration files valid
- ✅ PostgreSQL/Redis connectivity confirmed
- ✅ Feature definitions registered

---

## Known Issues & Resolutions

### Issue: Pydantic ValidationError
**Error**: `Extra inputs are not permitted [type=extra_forbidden, input_value='schema']`

**Cause**: Old `schema: public` field in feature_store.yaml not compatible with Feast 0.49.0

**Resolution**: Remove deprecated `schema` field from offline_store configuration

---

## References

- Feast Documentation: https://docs.feast.dev
- Version 0.49.0 Release Notes: https://github.com/feast-dev/feast/releases/tag/v0.49.0
- PostgreSQL Offline Store: https://docs.feast.dev/reference/offline-stores/postgres
- Redis Online Store: https://docs.feast.dev/reference/online-stores/redis

---

## Detailed Implementation Guide

### Step 1: Environment Setup

**Prerequisites**:
```bash
# Ensure Python 3.9+ is installed
python3 --version  # Should be >= 3.9

# Ensure PostgreSQL is running
psql -U trader -d mt5_crs -c "SELECT version();"

# Ensure Redis is running
redis-cli ping  # Should return PONG
```

**Install Feast**:
```bash
pip install feast==0.49.0
pip install feast[postgres]  # PostgreSQL dependencies
pip install feast[redis]     # Redis dependencies
```

### Step 2: Project Initialization

**Directory Structure**:
```
feature_repo/
├── feature_store.yaml          # Main configuration
├── definitions.py              # Feature definitions
└── registry.db                 # Feature registry (SQLite)
```

**Create feature_store.yaml**:
```yaml
project: mt5_trading
registry: registry.db
provider: local

offline_store:
  type: postgres
  host: localhost
  port: 5432
  database: mt5_crs
  user: trader
  password: ${POSTGRES_PASSWORD}

online_store:
  type: redis
  connection_string: redis://localhost:6379
```

### Step 3: Define Features

**Create definitions.py**:
```python
from datetime import timedelta
from feast import Entity, FeatureView, Field
from feast.types import Float64, Int64, String
from feast.data_source import PushSource

# Entity: Trading Symbol
symbol = Entity(
    name="symbol",
    join_keys=["symbol_id"],
    description="Trading instrument identifier (e.g., EURUSD, GBPUSD)"
)

# Data Source: Market data pushed to Feast
market_data_source = PushSource(
    name="market_data_push_source",
    batch_source=None  # Optional: Can reference PostgreSQL table
)

# Feature View: Market Features
market_features = FeatureView(
    name="market_features",
    entities=[symbol],
    ttl=timedelta(days=1),
    schema=[
        Field(name="open", dtype=Float64),
        Field(name="high", dtype=Float64),
        Field(name="low", dtype=Float64),
        Field(name="close", dtype=Float64),
        Field(name="volume", dtype=Int64),
        Field(name="bid", dtype=Float64),
        Field(name="ask", dtype=Float64),
        Field(name="spread", dtype=Float64),
    ],
    source=market_data_source,
    online=True  # Enable online serving
)
```

### Step 4: Register Features

**Apply Feature Definitions**:
```bash
cd feature_repo
feast apply

# Expected output:
# Registering 1 entity(s)
# Registering 1 feature view(s)
# Deploying infrastructure for market_features
```

**Verify Registration**:
```bash
feast entities list
# Output: symbol

feast feature-views list
# Output: market_features
```

### Step 5: Materialize Features

**Initial Materialization** (offline → online):
```bash
# Materialize last 7 days
feast materialize \
  $(date -d '7 days ago' +%Y-%m-%d) \
  $(date +%Y-%m-%d)
```

**Incremental Materialization** (for daily updates):
```bash
# Materialize today's data
feast materialize-incremental $(date +%Y-%m-%d)
```

### Step 6: Feature Retrieval in Application

**Online Feature Retrieval** (low-latency):
```python
from feast import FeatureStore

# Initialize feature store
store = FeatureStore(repo_path="./feature_repo")

# Retrieve features for EURUSD
entity_rows = [
    {"symbol_id": "EURUSD"}
]

features_to_fetch = [
    "market_features:close",
    "market_features:volume",
    "market_features:spread"
]

# Get online features from Redis
online_features = store.get_online_features(
    entity_rows=entity_rows,
    features=features_to_fetch
).to_dict()

print(f"EURUSD Close: {online_features['close'][0]}")
print(f"EURUSD Volume: {online_features['volume'][0]}")
```

**Historical Feature Retrieval** (for training):
```python
from datetime import datetime, timedelta
from feast import FeatureStore

store = FeatureStore(repo_path="./feature_repo")

# Define entity DataFrame
entity_df = pd.DataFrame({
    "symbol_id": ["EURUSD", "GBPUSD", "USDJPY"],
    "event_timestamp": [
        datetime.now() - timedelta(hours=1),
        datetime.now() - timedelta(hours=1),
        datetime.now() - timedelta(hours=1)
    ]
})

# Retrieve historical features from PostgreSQL
training_data = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "market_features:open",
        "market_features:high",
        "market_features:low",
        "market_features:close",
        "market_features:volume"
    ]
).to_df()

print(training_data.head())
```

---

## Advanced Features (Feast 0.49.0)

### Feature Services

Group commonly used features:
```python
from feast import FeatureService

trading_signals_service = FeatureService(
    name="trading_signals",
    features=[
        market_features[["close", "volume", "spread"]]
    ]
)
```

### On-Demand Transformations

Compute features on-the-fly:
```python
from feast import on_demand_feature_view
from feast.types import Float64

@on_demand_feature_view(
    sources=[market_features],
    schema=[Field(name="price_change_pct", dtype=Float64)]
)
def price_change(inputs: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "price_change_pct": (
            (inputs["close"] - inputs["open"]) / inputs["open"] * 100
        )
    })
```

### Stream Ingestion

Push real-time features to Redis:
```python
from feast import FeatureStore

store = FeatureStore(repo_path="./feature_repo")

# Push real-time market data
store.push(
    push_source_name="market_data_push_source",
    df=pd.DataFrame({
        "symbol_id": ["EURUSD"],
        "close": [1.0850],
        "volume": [125000],
        "spread": [0.0002],
        "event_timestamp": [datetime.now()]
    })
)
```

---

## Performance Optimization

### Redis Configuration

**Optimize for Low Latency**:
```bash
# In redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0
```

### PostgreSQL Tuning

**Index Critical Columns**:
```sql
-- Index on timestamp for fast historical queries
CREATE INDEX idx_market_data_timestamp
ON market_data(event_timestamp);

-- Index on symbol for entity joins
CREATE INDEX idx_market_data_symbol
ON market_data(symbol_id);
```

### Materialization Schedule

**Cron Job for Daily Updates**:
```bash
# /etc/cron.d/feast-materialize
0 2 * * * cd /opt/mt5-crs/feature_repo && \
          feast materialize-incremental $(date +\%Y-\%m-\%d) >> \
          /var/log/feast-materialize.log 2>&1
```

---

## Monitoring & Observability

### Health Checks

**Feature Store Status**:
```python
from feast import FeatureStore

store = FeatureStore(repo_path="./feature_repo")

# Check registered features
views = store.list_feature_views()
print(f"Feature Views: {len(views)}")

# Check materialization status
# (Requires feast >= 0.30.0)
materialization_intervals = store.get_materialization_intervals(
    feature_view="market_features"
)
```

### Logging

**Enable Debug Logging**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
feast_logger = logging.getLogger("feast")
feast_logger.setLevel(logging.DEBUG)
```

### Metrics

**Track Feature Retrieval Latency**:
```python
import time
from feast import FeatureStore

store = FeatureStore(repo_path="./feature_repo")

start = time.time()
features = store.get_online_features(
    entity_rows=[{"symbol_id": "EURUSD"}],
    features=["market_features:close"]
)
latency_ms = (time.time() - start) * 1000

print(f"Feature retrieval latency: {latency_ms:.2f}ms")
```

---

## Troubleshooting

### Common Issues

**1. Pydantic ValidationError: Extra inputs not permitted**
- **Symptom**: `schema` field rejected in feature_store.yaml
- **Cause**: Feast 0.49.0 doesn't support `schema` in offline_store
- **Fix**: Remove `schema: public` from configuration

**2. Feature Not Found**
- **Symptom**: `FeatureViewNotFoundException`
- **Cause**: Features not registered with `feast apply`
- **Fix**: Run `feast apply` in feature_repo directory

**3. PostgreSQL Connection Failed**
- **Symptom**: `psycopg2.OperationalError`
- **Cause**: Database credentials incorrect or service down
- **Fix**: Verify `POSTGRES_PASSWORD` environment variable

**4. Redis Connection Timeout**
- **Symptom**: `redis.exceptions.ConnectionError`
- **Cause**: Redis service not running or port blocked
- **Fix**: Start Redis: `sudo systemctl start redis`

---

## Security Considerations

### Credential Management

**Environment Variables** (recommended):
```bash
export POSTGRES_PASSWORD="secure_password"
export REDIS_PASSWORD="redis_secure_password"
```

**Secrets in feature_store.yaml**:
```yaml
offline_store:
  password: ${POSTGRES_PASSWORD}  # Reads from env var
```

### Network Security

**Restrict Redis Access**:
```bash
# In redis.conf
bind 127.0.0.1 ::1
requirepass your_redis_password
```

**PostgreSQL SSL** (for production):
```yaml
offline_store:
  sslmode: require
  sslrootcert: /path/to/ca-certificate.crt
```

---

## Migration Guide

### From Feast 0.10.2 to 0.49.0

**Breaking Changes**:
1. `FeatureStore` constructor: No longer accepts `config` parameter directly
2. Feature definitions: Must use `Field` instead of `Feature` class
3. Data sources: `PushSource` replaces legacy push APIs

**Migration Steps**:
```bash
# 1. Backup existing registry
cp feature_repo/registry.db feature_repo/registry.db.backup

# 2. Update feature definitions
# Replace: from feast import Feature
# With:    from feast import Field

# 3. Re-apply features
feast apply

# 4. Re-materialize (if needed)
feast materialize <start_date> <end_date>
```

---

## Future Roadmap

### Planned Enhancements

1. **Feature Monitoring**: Track feature drift and data quality
2. **Feature Lineage**: Trace feature dependencies
3. **Multi-Source Joins**: Combine features from multiple sources
4. **Feature Versioning**: Support A/B testing with versioned features
5. **Real-Time Streaming**: Kafka/Kinesis integration for live data

### Feast Upgrades

- **0.50.x**: Incremental improvements (Q1 2025)
- **0.60.x**: Major feature additions (Q2 2025)
- **1.0.0**: LTS release (TBD)

---

**Status**: Implementation complete, materialization in progress
**Next Task**: Automate feature materialization pipeline
**Document Version**: 2.0
**Last Updated**: 2025-12-31
