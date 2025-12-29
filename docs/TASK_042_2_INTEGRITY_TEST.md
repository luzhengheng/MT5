# Task #042.2: AI Integration Verification & System Integrity Check

**Date**: 2025-12-29
**Protocol**: v2.2 (Docs-as-Code)
**Role**: System Reliability Engineer
**Status**: Implementation Phase

---

## Executive Summary

Comprehensive system integrity verification to ensure:
1. **AI Integration**: External AI audit endpoint (`api.yyds168.net`) operational
2. **Service Connectivity**: Redis, Database, MT5 Gateway accessible
3. **Configuration Completeness**: All critical env vars restored
4. **End-to-End Workflow**: AI review bridge functioning properly

**Scope**: Post-reset verification and recovery of missing inter-server connectivity variables.

---

## Problem Statement

### Background
- Task #040.9 (Legacy Environment Reset) aggressively cleared `.env`
- Task #042.1 restored external AI credentials
- **Gap**: Inter-server connectivity vars (`REDIS_HOST`, `MT5_HTTP_URL`) might be missing
- **Risk**: System appears clean but critical integrations broken

### Critical Variables to Verify
1. ✅ External AI Config (Task #042.1)
   - `GEMINI_API_KEY`
   - `GEMINI_BASE_URL`
   - `GEMINI_MODEL`
   - `GEMINI_PROVIDER`

2. ⚠️ Connectivity Config (Missing)
   - `REDIS_HOST` (Feature store, caching)
   - `REDIS_PORT` (Feature store)
   - `MT5_HTTP_URL` (Gateway to MT5 server)

3. ✅ Database Config (Task #040.9)
   - `DB_URL`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`

---

## Solution Architecture

### 3-Layer Verification

```
┌─────────────────────────────────────────────────────────┐
│           INTEGRITY AUDIT (Task #042.2)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Layer 1: Configuration Validation                       │
│ ├─ Check all critical env vars present                  │
│ ├─ Validate variable formats                            │
│ └─ Report missing vars                                  │
│                                                          │
│ Layer 2: Service Connectivity                           │
│ ├─ Test Redis connection                                │
│ ├─ Test Database connection                             │
│ ├─ Test MT5 Gateway reachability                        │
│ └─ Report service status                                │
│                                                          │
│ Layer 3: End-to-End Workflow                            │
│ ├─ Test AI audit bridge initialization                  │
│ ├─ Verify OpenAI-compatible endpoint access             │
│ ├─ Validate configuration integration                   │
│ └─ Report overall system health                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Documentation ✅ (Current)
**File**: docs/TASK_042_2_INTEGRITY_TEST.md
**Purpose**: This specification document

### Step 2: Connectivity Check Script
**File**: scripts/maintenance/check_connectivity.py

**Functionality**:
```python
def main():
    """
    Multi-layer system integrity check:
    1. Load .env configuration
    2. Validate critical env vars
    3. Test service connectivity
    4. Report findings
    """

    # Layer 1: Configuration
    check_env_variables()  # Check all critical vars

    # Layer 2: Connectivity
    check_redis_connection()
    check_database_connection()
    check_mt5_gateway_config()

    # Layer 3: Workflow
    check_ai_bridge_integration()

    # Report
    print_summary_report()
```

**Check Details**:

1. **Environment Variables** (9 critical vars)
   ```
   ✓ GEMINI_API_KEY
   ✓ GEMINI_BASE_URL
   ✓ GEMINI_MODEL
   ✓ GEMINI_PROVIDER
   ? REDIS_HOST (check)
   ? REDIS_PORT (check)
   ✓ DB_URL
   ✓ POSTGRES_USER
   ? MT5_HTTP_URL (check)
   ```

2. **Redis Connectivity**
   ```python
   import redis
   r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=3)
   r.ping()  # Should return True
   ```

3. **Database Connectivity**
   ```python
   from sqlalchemy import create_engine
   engine = create_engine(DB_URL, connect_args={"connect_timeout": 3})
   conn = engine.connect()  # Should succeed
   ```

4. **MT5 Gateway Config**
   ```python
   MT5_HTTP_URL = os.getenv("MT5_HTTP_URL")
   if not MT5_HTTP_URL:
       warn("MT5_HTTP_URL missing - typical: http://host.docker.internal:8000")
   ```

5. **AI Bridge Integration**
   ```python
   from scripts.utils.openai_audit_adapter import OpenAIAuditAdapter
   adapter = OpenAIAuditAdapter()
   if adapter.is_configured():
       print("✅ AI bridge configured and ready")
   ```

### Step 3: AI Bridge Verification
**File**: gemini_review_bridge.py (review & test)

**Verification Points**:
1. ✅ Uses `os.getenv("GEMINI_BASE_URL")` (not hardcoded)
2. ✅ Uses `os.getenv("GEMINI_API_KEY")` (not hardcoded)
3. ✅ Respects `GEMINI_PROVIDER=openai` flag
4. ✅ Handles API responses with JSON extraction

**Test Approach**:
- Create dummy file change
- Run `python3 gemini_review_bridge.py`
- Expected output: Blue AI feedback block with architecture comments

### Step 4: Configuration Restoration
**File**: .env (append if missing)

**Missing Variables to Restore**:
```bash
# ============================================================================
# Inter-Server Connectivity (Restored - Task #042.2)
# ============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
# MT5 Gateway URL (Windows Host - Please verify IP)
# Typical values:
#   - Docker on Linux: 172.19.0.1:8000 (Docker bridge)
#   - Docker on Mac: host.docker.internal:8000 (Docker Desktop)
#   - Native: 127.0.0.1:8000 (Localhost)
# User Action: Check your environment and update accordingly
MT5_HTTP_URL=http://host.docker.internal:8000
```

---

## Execution Sequence

### 1. Initialize
```bash
python3 scripts/project_cli.py start "Task #042.2: System Integrity"
```

### 2. Execute

#### 2.1 Create Connectivity Check Script
- Write `scripts/maintenance/check_connectivity.py`
- Implement 5 verification points

#### 2.2 Run System Integrity Scan
```bash
python3 scripts/maintenance/check_connectivity.py
```

**Expected Output** (Good):
```
======================================================================
✅ SYSTEM INTEGRITY AUDIT
======================================================================

📋 CRITICAL ENV VARIABLES
----------------------------------------------------------------------
✅ GEMINI_API_KEY           : Present
✅ GEMINI_BASE_URL          : Present
✅ GEMINI_MODEL             : Present
✅ GEMINI_PROVIDER          : Present
✅ REDIS_HOST               : localhost
✅ REDIS_PORT               : 6379
✅ DB_URL                   : postgresql://...
⚠️  MT5_HTTP_URL            : MISSING (see notes)

📡 SERVICE CONNECTIVITY
----------------------------------------------------------------------
✅ Redis: Connected (ping successful)
✅ Database: Connected (query successful)
⚠️  MT5 Gateway: URL missing (needs user config)

🧠 AI BRIDGE INTEGRATION
----------------------------------------------------------------------
✅ OpenAI Adapter: Configured
✅ API Key: Valid format
✅ Base URL: Valid format
✅ Model: Valid format
✅ Ready: Yes

======================================================================
📊 SUMMARY: 8/9 Critical Variables Present
Status: HEALTHY (MT5 Gateway URL optional)
======================================================================
```

#### 2.3 Check gemini_review_bridge.py
```bash
grep -E "GEMINI_BASE_URL|GEMINI_API_KEY|GEMINI_PROVIDER" gemini_review_bridge.py
```

**Expected**: Variables loaded from `.env`, not hardcoded

#### 2.4 Restore Missing Variables
```bash
# If check_connectivity.py reports missing vars:
cat >> .env << 'EOF'

# ============================================================================
# Inter-Server Connectivity (Restored - Task #042.2)
# ============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
MT5_HTTP_URL=http://host.docker.internal:8000
EOF
```

#### 2.5 Verify gemini_review_bridge.py (Optional AI Test)
```bash
# This will test the AI bridge (may trigger Cloudflare challenge)
python3 gemini_review_bridge.py
# Expected output: Blue AI feedback block or API challenge
```

### 3. Finish
```bash
python3 scripts/project_cli.py finish
```

---

## Definition of Done

✅ **Documentation Created**
- docs/TASK_042_2_INTEGRITY_TEST.md exists

✅ **Connectivity Script Created**
- scripts/maintenance/check_connectivity.py exists
- Implements 5 verification points
- Produces clear status report

✅ **AI Bridge Verified**
- gemini_review_bridge.py reviewed
- Uses .env variables (not hardcoded)
- Respects GEMINI_PROVIDER flag

✅ **Configuration Restored**
- .env contains all 9 critical variables
- Missing vars identified and warned about
- Optional vars have sensible defaults

✅ **System Status Healthy**
- check_connectivity.py returns GREEN for critical services
- Redis accessible or warned if needed
- Database accessible
- AI bridge configured and ready
- MT5 URL configured (even if placeholder)

---

## Success Criteria

### Green Lights ✅
1. `check_connectivity.py` runs without errors
2. At least 8/9 critical variables present
3. Redis and Database connectivity verified
4. AI bridge integration confirmed
5. gemini_review_bridge.py uses .env config

### Yellow Lights ⚠️ (Acceptable)
1. MT5_HTTP_URL is placeholder (user to update)
2. Cloudflare challenge on API test (expected)

### Red Lights 🔴 (Failure)
1. Missing critical env vars (not restored)
2. Database unreachable (must fix)
3. AI bridge not configured (must fix)
4. check_connectivity.py fails (must debug)

---

## Verification Checklist

- [ ] docs/TASK_042_2_INTEGRITY_TEST.md created
- [ ] scripts/maintenance/check_connectivity.py created
- [ ] .env reviewed for completeness
- [ ] Missing variables identified
- [ ] Redis connectivity verified (or noted as optional)
- [ ] Database connectivity verified
- [ ] AI bridge configuration validated
- [ ] gemini_review_bridge.py uses .env properly
- [ ] System integrity report generated
- [ ] All critical services operational

---

## Critical Variables Reference

### Essential (Must Have)
| Variable | Source | Purpose |
|----------|--------|---------|
| DB_URL | Task #040.9 | Database connection |
| GEMINI_API_KEY | Task #042.1 | External AI credentials |
| GEMINI_BASE_URL | Task #042.1 | AI endpoint URL |
| GEMINI_PROVIDER | Task #042.1 | Provider type |

### Important (Should Have)
| Variable | Source | Purpose | Default |
|----------|--------|---------|---------|
| REDIS_HOST | Task #042.2 | Cache/Feature store | localhost |
| REDIS_PORT | Task #042.2 | Redis port | 6379 |
| MT5_HTTP_URL | Task #042.2 | MT5 gateway | host.docker.internal:8000 |

### Optional (Nice to Have)
| Variable | Purpose |
|----------|---------|
| DEBUG | Debug mode |
| ENVIRONMENT | dev/prod flag |

---

## Troubleshooting

### "Redis connection refused"
- **Cause**: Redis not running
- **Fix**: Start Redis or update REDIS_HOST to valid address
- **Impact**: Feature store caching won't work

### "Database connection refused"
- **Cause**: PostgreSQL not running
- **Fix**: Start database or verify DB_URL
- **Impact**: Application won't start

### "MT5_HTTP_URL missing"
- **Cause**: MT5 gateway not configured
- **Fix**: Add MT5_HTTP_URL to .env (check your network)
- **Impact**: MT5 integration disabled (non-critical for testing)

### "API error 403 Forbidden"
- **Cause**: Cloudflare WAF blocking request
- **Fix**: Retry or wait (temporary) / Use curl-cffi for bypass
- **Impact**: External AI review blocked (existing code handles this)

---

## Post-Verification Actions

After successful integrity check:

1. **If All Green**:
   ```bash
   echo "✅ System healthy - ready for development"
   ```

2. **If Yellow (MT5 only)**:
   ```bash
   echo "⚠️ MT5 gateway URL needs update - check your network"
   echo "Update .env MT5_HTTP_URL with your actual IP/hostname"
   ```

3. **If Any Red**:
   ```bash
   echo "❌ Critical issues found - see report"
   # Fix issues from troubleshooting guide
   ```

---

## Expected Test Output

```
======================================================================
✅ SYSTEM INTEGRITY AUDIT
======================================================================

📋 CRITICAL ENV VARIABLES (9 total)
----------------------------------------------------------------------
✅ GEMINI_API_KEY           : sk-Oz2G85I...QoEvu
✅ GEMINI_BASE_URL          : https://api.yyds168.net/v1
✅ GEMINI_MODEL             : gemini-3-pro-preview
✅ GEMINI_PROVIDER          : openai
✅ REDIS_HOST               : localhost
✅ REDIS_PORT               : 6379
✅ DB_URL                   : postgresql://postgres:****@localhost:5432/data_nexus
✅ POSTGRES_USER            : postgres
✅ POSTGRES_DB              : data_nexus

📡 SERVICE CONNECTIVITY
----------------------------------------------------------------------
✅ Redis Connection: PING successful (latency: 0.5ms)
✅ Database Connection: SELECT 1 successful
✅ Database Tables: market_data exists, assets exists

🧠 AI BRIDGE INTEGRATION
----------------------------------------------------------------------
✅ OpenAI Adapter: Configured
✅ API Key Present: Yes (format valid)
✅ Base URL: https://api.yyds168.net/v1 (https valid)
✅ Model: gemini-3-pro-preview (format valid)
✅ Provider: openai (matches config)
✅ Status: READY FOR AUDIT

🔗 INTER-SERVER CONNECTIVITY
----------------------------------------------------------------------
✅ MT5_HTTP_URL: http://host.docker.internal:8000 (configured)
ℹ️  Note: MT5 Gateway connectivity requires active MT5 service

======================================================================
📊 OVERALL SYSTEM STATUS
======================================================================
✅ Critical: 8/8 variables (100%)
✅ Services: 2/2 responsive (100%)
✅ Integration: AI bridge ready (100%)
⚠️  Optional: MT5 URL configured (needs verification)

🎯 VERDICT: SYSTEM HEALTHY & CONNECTED
======================================================================
```

---

## Timeline

| Step | Duration |
|------|----------|
| Documentation | 5 min |
| Check script | 20 min |
| AI bridge review | 5 min |
| Config restoration | 5 min |
| Testing & report | 10 min |
| **Total** | **~45 min** |

---

## References

- Task #040.9: Legacy Environment Reset
- Task #042.1: External Audit Configuration
- docs/TASK_042_1_AUDIT_FIX.md
- TASK_042_1_COMPLETION_REPORT.md

---

**Created**: 2025-12-29
**Author**: Claude Sonnet 4.5
**Protocol**: v2.2 (Docs-as-Code)
**Status**: Implementation In Progress
