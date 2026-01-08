# 🚀 QUICK START: EODHD Data Integrity Validator

**Task**: #066.1 - EODHD Data Ingestion & Integrity Validation
**Status**: ✅ Production Ready
**Last Updated**: 2026-01-09

---

## 30-Second Setup

```bash
# 1. Ensure database is running
docker ps | grep postgres  # Should show 'mt5_crs_timescaledb'

# 2. Run validation on a single symbol
cd /opt/mt5-crs
python3 scripts/validate_data.py --symbol AAPL.US

# 3. Check the summary output
# Should show: ✅ ALL VALIDATIONS PASSED
```

---

## Common Commands

### Validate Single Symbol
```bash
python3 scripts/validate_data.py --symbol AAPL.US
```

### Validate Multiple Symbols
```bash
python3 scripts/validate_data.py --symbols AAPL.US,MSFT.US,GOOGL.US,TSLA.US
```

### Validate ALL Symbols in Database
```bash
python3 scripts/validate_data.py --check-all
```

### See Help Text
```bash
python3 scripts/validate_data.py --help
```

---

## What Gets Checked?

For each symbol, 6 validation checks are performed:

| Check | What It Validates | Pass Condition |
|-------|------------------|----------------|
| 1️⃣ **Row Count** | Data exists in database | ≥ 1 row |
| 2️⃣ **Duplicates** | No duplicate time/symbol pairs | 0 duplicates |
| 3️⃣ **Null Fields** | Required fields are present | No NULLs in: time, symbol, open, high, low, close, volume |
| 4️⃣ **Price Sanity** | Prices are reasonable | All prices > 0, no >10x volatility |
| 5️⃣ **OHLC Logic** | Open/High/Low/Close relationships valid | high ≥ low, open/close ∈ [low, high] |
| 6️⃣ **Time Continuity** | No unexpected gaps in data | Only weekends/holidays allowed (< 5 gaps) |

---

## Interpreting Output

### ✅ Success Example
```
================================================================================
DATA INTEGRITY VALIDATOR (Task #066.1)
================================================================================
  Symbols: 1
  Checks per symbol: 6
================================================================================

Validating AAPL.US...
  ✅ Row count: 2,847 rows
  ✅ No duplicates
  ✅ No unexpected null values
  ✅ Price sanity checks passed
  ✅ OHLC logic valid
  ✅ Time series continuous

================================================================================
VALIDATION SUMMARY
================================================================================
  Total Checks: 6
  ✅ Passed: 6
  ❌ Failed: 0
  Duration: 0.45 seconds

================================================================================
✅ ALL VALIDATIONS PASSED
================================================================================
```

### ❌ Failure Example
```
Validating AAPL.US...
  ✅ Row count: 2,847 rows
  ❌ Validation failed: Found 12 duplicate records
  ⚠️  Null values found in: close(3), volume(5)
  ❌ Found 8 records with non-positive prices
```

---

## Troubleshooting

### Problem: "No data found for AAPL.US"
**Cause**: Symbol hasn't been ingested yet (run Task #066 bulk loader first)

**Solution**:
```bash
# Ingest data first
python3 scripts/bulk_loader_cli.py --symbols AAPL.US --workers 5

# Then validate
python3 scripts/validate_data.py --symbol AAPL.US
```

### Problem: "ConnectionRefusedError: Connection to database failed"
**Cause**: PostgreSQL/TimescaleDB container not running

**Solution**:
```bash
# Start Docker containers
docker-compose -f docker-compose.data.yml up -d

# Verify
docker ps | grep mt5_crs
```

### Problem: "ModuleNotFoundError: No module named 'src'"
**Cause**: Running from wrong directory

**Solution**:
```bash
# Make sure you're in project root
cd /opt/mt5-crs

# Then run the script
python3 scripts/validate_data.py --symbol AAPL.US
```

### Problem: "No symbols found in database"
**Cause**: Asset table is empty (run Task #065 infrastructure setup)

**Solution**:
```bash
# Initialize database schema
python3 src/infrastructure/init_db.py

# Verify Asset table has data
python3 -c "
from src.data_nexus.database.connection import PostgresConnection
db = PostgresConnection()
count = db.query_scalar('SELECT COUNT(*) FROM market.asset')
print(f'Assets in database: {count}')
"
```

---

## Environment Variables

### Required
None - all have sensible defaults

### Optional (customize behavior)
```bash
# Database connection parameters
export POSTGRES_HOST=localhost       # Default: localhost
export POSTGRES_PORT=5432            # Default: 5432
export POSTGRES_USER=trader          # Default: trader
export POSTGRES_PASSWORD=password    # Default: password
export POSTGRES_DB=mt5_crs          # Default: mt5_crs

# Then run validation
python3 scripts/validate_data.py --symbol AAPL.US
```

---

## Understanding the Time Continuity Check

The validator allows gaps on **weekends only** (Saturday/Sunday). Market holidays beyond weekends are not automatically detected and will be reported as gaps.

### Example: Normal (No Error)
```
Mon Jan 8 - Tue Jan 9 = 1 day ✅
Tue Jan 9 - Wed Jan 10 = 1 day ✅
Wed Jan 10 - Thu Jan 11 = 1 day ✅
Thu Jan 11 - Fri Jan 12 = 1 day ✅
Fri Jan 12 - Mon Jan 15 = Weekend (Sat/Sun) ✅
```

### Example: Holiday (Reported as Warning)
```
Fri Jan 12 - Mon Jan 15 = 3 days (should be 1)
  → Fri to Sat/Sun = 2 days (weekend, OK)
  → Sun to Mon = 1 day
  → But Jan 15 is MLK Day (US market holiday)
  ⚠️  Warning: Found 1 gap in time series (may be market holiday)
```

**Note**: For markets with many holidays, the validator is intentionally conservative. Human review may be needed to verify holiday gaps are legitimate.

---

## Integration with Bulk Loader (Task #066)

### Typical Workflow
```bash
# Step 1: Ingest data (Task #066)
$ python3 scripts/bulk_loader_cli.py --symbols AAPL.US,MSFT.US --workers 5 --start-date 2024-01-01
✅ Ingested 1,234 rows for AAPL.US
✅ Ingested 1,456 rows for MSFT.US

# Step 2: Validate data quality (Task #066.1)
$ python3 scripts/validate_data.py --symbols AAPL.US,MSFT.US
✅ ALL VALIDATIONS PASSED

# Step 3: Data is now ready for analysis (Task #067+)
```

---

## Performance Tips

### Large Symbol Sets
For validating 100+ symbols, the validator runs sequentially. To speed up:

1. **Validate in batches**:
```bash
# Split symbols into groups
python3 scripts/validate_data.py --symbols AAPL.US,MSFT.US,GOOGL.US &
python3 scripts/validate_data.py --symbols TSLA.US,AMZN.US,NVDA.US &
wait
```

2. **Monitor database queries**:
```bash
# Open another terminal and monitor slow queries
psql -U trader -d mt5_crs -c "
SELECT query, mean_time FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 5;
"
```

---

## Security Notes

### Parameterized Queries ✅
All database queries use parameterized SQL (prevent SQL injection):
```python
# Good ✅
query = "SELECT * FROM table WHERE symbol = %s"
db.query(query, (symbol,))

# Bad ❌ (not used)
query = f"SELECT * FROM table WHERE symbol = '{symbol}'"
```

### No Hardcoded Secrets ✅
Database credentials come from environment variables:
```bash
export POSTGRES_PASSWORD="your-secure-password"  # Set before running
```

### Error Messages ✅
Errors include context but never expose sensitive data:
```
ConnectionRefusedError: Database connection failed (localhost:5432)
  → Only shows host/port, not credentials
```

---

## Getting Help

### View Full Documentation
```bash
cat docs/archive/tasks/TASK_066.1/COMPLETION_REPORT.md
```

### Check Validation Script Source
```bash
# Read the validator implementation
cat scripts/validate_data.py

# Key functions:
# - DataValidator.validate_symbol()     : Main validation loop
# - DataValidator._check_row_count()    : Check 1
# - DataValidator._check_duplicates()   : Check 2
# - DataValidator._check_null_fields()  : Check 3
# - DataValidator._check_price_sanity() : Check 4
# - DataValidator._check_ohlc_logic()   : Check 5
# - DataValidator._check_time_continuity() : Check 6
```

### View Recent Validation Run
```bash
tail -100 VERIFY_LOG.log  # See last audit
```

---

## Next Steps

After successful validation ✅:
- Data is ready for downstream analysis (Task #067+)
- Can proceed with trading strategy development
- Monitor data quality over time (consider adding cron job)

---

**Questions?** See COMPLETION_REPORT.md for full technical details.
