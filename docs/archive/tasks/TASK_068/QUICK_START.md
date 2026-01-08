# Task #068: Technical Indicators & Feature Materialization - Quick Start Guide

## Overview

Task #068 implements the feature computation and materialization pipeline for the MT5-CRS trading system. This guide will help you compute technical indicators from OHLCV data and materialize them to Redis for online serving.

## Prerequisites

1. **Docker containers running**:
   ```bash
   docker-compose -f docker-compose.data.yml ps
   # Should show: timescaledb, redis, pgadmin (all running)
   ```

2. **OHLCV data populated**: Task #065/066 should be complete
   ```bash
   psql -h localhost -U trader -d mt5_crs -c "SELECT COUNT(*) FROM market_data.ohlcv_daily;"
   ```

3. **Feast installed**: From Task #067
   ```bash
   feast version
   # Should show: Feast v0.49 or higher
   ```

4. **Environment variables set**:
   ```bash
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_DB=mt5_crs
   export POSTGRES_USER=trader
   export POSTGRES_PASSWORD=<your-password>
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   export REDIS_DB=0
   ```

## Step-by-Step Execution

### Step 1: Create Feature Tables (Phase 1)

Create the TimescaleDB schema for storing computed technical indicators:

```bash
python3 src/infrastructure/init_feature_tables.py
```

Expected output:
```
✅ Schema 'features' created (or already exists)
✅ Table 'features.technical_indicators' created
✅ Hypertable 'features.technical_indicators' configured (7-day chunks)
✅ Index 'idx_technical_indicators_symbol_time' created
```

Verify table structure:
```bash
psql -h localhost -U trader -d mt5_crs -c "\\d features.technical_indicators"
```

### Step 2: Compute Technical Indicators (Phase 2)

Run the feature computation pipeline to calculate indicators from OHLCV data:

```bash
python3 scripts/compute_features.py --symbols AAPL.US,MSFT.US,GOOGL.US --workers 1
```

Options:
- `--symbols`: Comma-separated list of symbols (default: AAPL.US)
- `--workers`: Number of parallel workers (default: 1)
- `--start-date`: Start date in YYYY-MM-DD format (default: 1 year ago)
- `--end-date`: End date in YYYY-MM-DD format (default: today)

Expected output:
```
Processing AAPL.US...
✅ Fetched 252 rows for AAPL.US
✅ Computed 252 rows of indicators for AAPL.US
✅ Inserted 230 rows for AAPL.US

EXECUTION STATISTICS:
Symbols processed: 3
Total rows computed: 756
Total rows inserted: 690
Errors: 0
```

Verify data:
```bash
psql -h localhost -U trader -d mt5_crs -c "SELECT symbol, COUNT(*), MIN(time), MAX(time) FROM features.technical_indicators GROUP BY symbol;"
```

### Step 3: Update Feast Definitions (Phase 3)

The Feast definitions have been updated to use PostgreSQLSource. Apply the configuration:

```bash
# Run Feast apply with secure credential injection
python3 scripts/init_feast.py
```

Expected output:
```
✅ Created temporary config with credentials
✅ Feast apply completed successfully
✅ Feature views registered
```

Verify Feast registry:
```bash
cd src/feature_repo
feast feature-views list
```

Expected output should include:
- technical_indicators_ma (5 features)
- technical_indicators_momentum (7 features)
- technical_indicators_volatility (6 features)
- volume_indicators (3 features)
- price_action (2 features)

### Step 4: Materialize Features to Redis (Phase 4)

Execute Feast materialization to push features from PostgreSQL to Redis:

```bash
cd src/feature_repo
feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

Expected output:
```
Materializing 1 feature views...
  100% |████████████████████████████████| 23/23 features

Materialization complete!
Duration: 2.3s
Features materialized: 690
```

Verify Redis keys:
```bash
redis-cli KEYS "*" | head -20
redis-cli KEYS "*" | wc -l
```

### Step 5: Verify Feature Consistency (Phase 5)

Run the verification script to check feature quality:

```bash
python3 scripts/verify_features.py
```

Expected output:
```
VERIFICATION CHECKS:

1️⃣ Checking feature completeness...
Feature coverage by symbol:
  AAPL.US: 230 rows
  MSFT.US: 230 rows
  GOOGL.US: 230 rows

2️⃣ Checking data quality...
✅ AAPL.US: 0 issues
✅ MSFT.US: 0 issues
✅ GOOGL.US: 0 issues

VERIFICATION SUMMARY:
Data quality issues: 0

✅ VERIFICATION PASSED: Features are high quality
```

## Troubleshooting

### Issue: "No OHLCV data found for symbol"

**Cause**: OHLCV data not populated in `market_data.ohlcv_daily` table.

**Solution**: Complete Task #065/066 first to load market data.

### Issue: "Failed to connect to database"

**Cause**: TimescaleDB container not running or credentials incorrect.

**Solution**:
```bash
docker-compose -f docker-compose.data.yml ps
docker-compose -f docker-compose.data.yml up -d timescaledb
```

### Issue: "PostgreSQL source connection fails during feast apply"

**Cause**: Feast can't connect to PostgreSQL with credentials from YAML.

**Solution**: Use `scripts/init_feast.py` which handles secure credential injection automatically.

### Issue: "Materialization incomplete - features missing in Redis"

**Cause**: PostgreSQL source might not have data or table schema mismatch.

**Solution**:
1. Verify PostgreSQL has data: `SELECT COUNT(*) FROM features.technical_indicators;`
2. Check Feast logs: `feast materialize-incremental --verbose`
3. Verify schema matches definitions.py field names exactly

### Issue: "NaN values in computed indicators"

**Cause**: Indicator warmup period (first N rows) legitimately have NaN.

**Solution**: This is expected behavior. SMA(20) needs 20 rows before producing values.

## Performance Tips

1. **Parallel Processing**: Use `--workers 4` for faster computation (requires multiple DB connections)
2. **Incremental Updates**: Only compute features for new data by setting `--start-date`
3. **Redis AOF**: Disable Redis AOF in development for faster materialization
4. **Batch Size**: For large datasets, process symbols in batches

## Next Steps

After completing Task #068:

1. **Task #069**: Model Training - Train ML models using materialized features
2. **Task #070**: Real-time Feature Serving - Integrate Feast with trading API
3. **Task #071**: Feature Monitoring - Set up drift detection and data quality alerts

## See Also

- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md) - Full execution report with forensic evidence
- [SYNC_GUIDE.md](./SYNC_GUIDE.md) - Deployment guide for production environments
- [Task #067 Documentation](../TASK_067/) - Feast infrastructure setup
