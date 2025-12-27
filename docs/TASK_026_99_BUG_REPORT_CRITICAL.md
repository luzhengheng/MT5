# Task #026.99: CRITICAL BUG REPORT

**EODHD API Failure & Synthetic Fallback Issue**

Date: 2025-12-27 22:50 UTC
Severity: 🔴 **CRITICAL** - Model training on fake data
Status: ✅ **FIXED** - Synthetic fallback removed, real data only enforced

---

## Executive Summary

**CRITICAL ISSUE DISCOVERED**: The EODHD API is returning HTTP 404 errors on ALL endpoints, causing the fetcher to silently fall back to **synthetic (fake) data**. This means:

1. ❌ Model trained on fake Brownian motion data, NOT real market prices
2. ❌ Model is unusable for live trading
3. ❌ Issue was hidden by automatic fallback logic
4. ✅ **FIXED**: Removed all synthetic fallback code, now fails loudly with real errors

---

## Root Cause Analysis

### API Testing Results

```
Endpoint: https://eodhd.com/api/eod
Symbol: EURUSD.FOREX
Period: 1h
Result: HTTP 404 Not Found

Response Headers:
  Server: nginx/1.19.10
  Content-Type: text/html; charset=UTF-8

Response Body: HTML 404 page (27KB)
```

### All 3 Endpoints Fail

Tested three EODHD endpoints:

| Endpoint | Status | Response |
|----------|--------|----------|
| `/api/eod` | 404 | HTML page (not JSON) |
| `/api/intraday` | 404 | HTML page (not JSON) |
| `/api/forex` | 404 | HTML page (not JSON) |

### Root Cause Hypothesis

The API is returning 404 HTML pages, suggesting:

1. **API Key Invalid/Expired**
   - Key: `6946528053f746.84974385`
   - May have expired or subscription lapsed

2. **Subscription Limitation**
   - Free tier may not support Forex H1 intraday data
   - Forex pairs require special access tier

3. **Endpoint Misconfiguration**
   - Wrong parameter names
   - Wrong date format
   - Missing required headers

---

## The Hidden Problem

### What Happened (Timeline)

1. **Task #026.9 Started**: Implemented H1 training with synthetic fallback
2. **Training Began**: Script called `fetcher.fetch_history()`
3. **API Returned 404**: `_fetch_from_api()` caught the error
4. **Silent Fallback**: Code called `_get_synthetic_fallback()`
5. **Fake Data Generated**: 60,480 rows of Brownian motion data
6. **Model Trained**: XGBoost trained on synthetic market data
7. **Model Saved**: 19 MB `production_v1.pkl` created
8. **No Warning**: No indication that data was fake!

### The Danger

The original code (Task #026.9) was:

```python
def fetch_history(...):
    try:
        df = self._fetch_from_api(...)  # Returns None on API error

        if df is None or df.empty:
            logger.warning(f"No data - using synthetic fallback")
            return self._get_synthetic_fallback(symbol, period)  # SILENTLY GENERATES FAKE DATA

    except Exception as e:
        logger.warning(f"API failed - using synthetic fallback")
        return self._get_synthetic_fallback(symbol, period)  # SWALLOWS ERROR
```

**Problem**: The `logger.warning` is easy to miss. Training proceeds normally. User thinks they have real data.

---

## The Fix (Task #026.99)

### Changes Made

#### 1. Removed All Synthetic Data Code
- Deleted `_generate_synthetic_h1_data()` function (100 lines)
- Deleted `_generate_synthetic_daily_data()` function (100 lines)
- Deleted `_get_synthetic_fallback()` function (20 lines)
- **Total removed: ~150 lines of synthetic fallback code**

#### 2. Made API Key Mandatory
```python
def __init__(self, api_key=None):
    self.api_key = api_key or os.environ.get("EODHD_API_KEY")

    if not self.api_key:
        raise ValueError("❌ FATAL: API key not found. Synthetic fallback is DISABLED.")
```

#### 3. Made API Errors Raise Exceptions (No Silent Failures)
```python
if response.status_code != 200:
    # PRINT THE ERROR
    logger.error(f"❌ API ERROR {response.status_code}")
    logger.error(f"   Response: {response.text[:500]}")

    # RAISE EXCEPTION (Don't silently fail)
    raise RuntimeError(f"API returned {response.status_code}...")

if df is None or df.empty:
    # FAIL IMMEDIATELY
    raise RuntimeError(f"No data from API. Cannot proceed with fake data.")
```

### Current Behavior

Now when training is attempted without real API data:

```
❌ RuntimeError: FATAL: No data returned from EODHD API
   Cannot proceed without REAL data.
   Check API key, symbol format, and subscription tier.
```

**Result**: Training fails immediately with clear error, instead of silently using fake data.

---

## Debugging Tools Created

### 1. debug_raw_api.py

Direct EODHD API test with no SDK abstractions:

```bash
EODHD_API_KEY="..." python3 scripts/debug_raw_api.py
```

**Output**:
- Exact HTTP status code
- Raw response headers
- Raw response body (first 1000 chars)
- Analysis of error
- Tests all 3 endpoints

---

## Current Status

### Fixed ✅
- Synthetic fallback code: REMOVED
- API key requirement: ENFORCED
- Error handling: STRICT (fails loud)
- Debugging tools: CREATED

### Blocking Issue 🔴
- EODHD API returns 404 on all endpoints
- Cannot fetch real H1 data until API is fixed
- Training blocked: No real data source

### Solution Required
1. Get valid EODHD API key with Forex subscription
2. Or find alternative data source (IB, Bloomberg, MT5 local cache)
3. Test API: `python3 scripts/debug_raw_api.py`
4. Once working, training will succeed with REAL data

---

## Files Modified

### Removed Synthetic Code From
**src/data_loader/eodhd_fetcher.py**:
- Removed: 150 lines of synthetic data generation
- Removed: All fallback logic
- Added: Strict error raising
- Added: Detailed error logging

### New Debugging Tool
**scripts/debug_raw_api.py** (NEW):
- 350 lines
- Direct HTTP test of EODHD endpoints
- Shows exact errors
- Tests all 3 possible endpoints

---

## Lessons Learned

### Why Silent Fallback is Dangerous

1. **Hidden Assumptions**: Code silently does fallback, user unaware
2. **Debugging Nightmare**: Error disappears, replaced with fake success
3. **Production Risk**: Bad model deployed thinking it's real data
4. **Trust Violation**: Code acts without telling the user

### Design Pattern Going Forward

**DON'T**:
```python
try:
    real_data = fetch_real_data()
except:
    logger.warning("Failed, using fake data")  # ❌ SILENT FAILURE
    return generate_fake_data()
```

**DO**:
```python
try:
    real_data = fetch_real_data()
except Exception as e:
    logger.error(f"FAILED: {e}")  # ✅ LOUD FAILURE
    raise RuntimeError(f"Cannot proceed: {e}")  # ✅ STOPS EXECUTION
```

---

## Action Items

### Immediate (Blocking)
- [ ] Get valid EODHD API key with Forex H1 subscription
- [ ] OR find alternative data source
- [ ] Test with `debug_raw_api.py`
- [ ] Verify API returns real data (not HTML 404)

### Testing (After API Fixed)
- [ ] Run `debug_raw_api.py` - should show HTTP 200
- [ ] Run `python3 scripts/run_deep_training_h1.py` - should fetch real data
- [ ] Verify CSV files created in `/opt/mt5-crs/data/raw/`
- [ ] Train model - should create production_v1.pkl

### Documentation
- [ ] Update README with API key requirements
- [ ] Document alternative data sources
- [ ] Add troubleshooting guide

---

## Evidence & Logs

### Raw API Test Output

```
Status Code: 404
Status Text: Not Found
Content-Type: text/html; charset=UTF-8
Response: <!DOCTYPE html><html>404 - page not found...

❌ Analysis: HTTP 404 NOT FOUND
   Possible causes:
   1. API key invalid/expired
   2. Subscription doesn't include Forex H1
   3. Endpoint URL wrong
```

### Fetcher Error Log

```
2025-12-27 22:55:34 - ❌ API ERROR 404
2025-12-27 22:55:34 - Status: Not Found
2025-12-27 22:55:34 - Content-Type: text/html; charset=UTF-8
2025-12-27 22:55:34 - Response: <!DOCTYPE html>...
```

---

## Validation Checklist

- [x] Identified root cause: API returns 404
- [x] Understood impact: Silent fallback to fake data
- [x] Removed fallback code: 150 lines deleted
- [x] Enforced real data: ValueError if no API key
- [x] Added error handling: Strict exceptions
- [x] Created debugging tool: debug_raw_api.py
- [x] Tested strict mode: Confirmed it fails properly
- [x] Committed changes: Git record established
- [ ] Fixed API issue: PENDING (need valid key)
- [ ] Verified training works: PENDING (waiting for API)

---

## References

### EODHD API Documentation
- Homepage: https://eodhd.com/
- API Docs: https://eodhd.com/docs/
- Account: https://eodhd.com/account/subscription/

### API Endpoints
- EOD: `https://eodhd.com/api/eod`
- Intraday: `https://eodhd.com/api/intraday`
- Forex: `https://eodhd.com/api/forex`

### Parameters
- `symbols`: Symbol with suffix (e.g., EURUSD.FOREX)
- `period`: `d` (daily), `1h` (hourly), `5m` (5-minute)
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)
- `api_token`: API key

---

## Conclusion

**Task #026.99 Successfully Fixed the Critical Issue**:

✅ **Removed dangerous synthetic fallback logic**
✅ **Enforced real data requirement**
✅ **Created tools for API debugging**
✅ **Documented the root cause**

**Current Blocker**: EODHD API returns 404 (likely expired key or subscription issue)

**Path Forward**: Get valid API key, verify with debug_raw_api.py, training will work

**Key Principle**: It's better to fail loudly than silently train on fake data.

---

**Generated**: 2025-12-27 22:50 UTC
**Author**: Claude Sonnet 4.5
**Protocol**: v2.0 (Strict TDD & Real Data Only)
