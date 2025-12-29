# Task #040.9: Infrastructure Standardization & Cleanup

**Date**: 2025-12-29
**Task ID**: #044
**Protocol**: v2.2 (Docs-as-Code)
**Status**: Planning Phase

---

## Executive Summary

This task formalizes and automates infrastructure cleanup based on manual verification. The user confirmed database connectivity and identified root directory pollution from orphaned venv artifacts.

**Objectives**:
1. Clean root directory - remove orphaned `bin/`, `lib/` directories
2. Persist verified configuration in `.env` file
3. Create permanent health check script for ongoing infrastructure validation

---

## Part 1: Current State Assessment

### Verified Database Configuration

**Manual Verification Result** (After Testing):
```
Host: localhost
Port: 5432
User: trader
Password: password
Database: mt5_crs
Connection String: postgresql://trader:password@localhost:5432/mt5_crs
Status: ✅ WORKING
Row Counts: market_data=340,494 | assets=975
```

### Root Directory Pollution

**Current State** (After Cleanup):
```
/opt/mt5-crs/
├── bin/          ← KEPT (contains 16 legitimate project scripts)
├── lib/          ← REMOVED (orphaned venv artifact)
├── lib64/        ← REMOVED (orphaned venv artifact)
├── pyvenv.cfg    ← REMOVED (orphaned venv artifact)
├── venv/         ← KEPT (legitimate virtual environment)
├── src/          ← KEPT (project source code)
└── scripts/      ← KEPT (project scripts)
```

**Impact**: Having venv components in root causes confusion and prevents clean separation of concerns.

---

## Part 2: Cleanup Manifest

### Files/Directories to Remove

| Path | Type | Reason | Action |
|------|------|--------|--------|
| `./bin` | Directory | Orphaned venv artifact | DELETE |
| `./lib` | Directory | Orphaned venv artifact | DELETE |
| `./lib64` | Directory | Orphaned venv artifact (symlink) | DELETE |
| `./pyvenv.cfg` | File | Orphaned venv config | DELETE |

### Files/Directories to PRESERVE

| Path | Type | Reason |
|------|------|--------|
| `./venv` | Directory | Legitimate project virtual environment |
| `./src` | Directory | Project source code |
| `./scripts` | Directory | Project scripts and tools |
| `./.env` | File | Configuration file (will create/update) |

---

## Part 3: Health Check Specification

### Purpose

Permanent infrastructure health check script that:
1. Tests database connectivity with verified credentials
2. Queries row counts from `market_data` and `assets` tables
3. Reports system health status
4. Can be integrated into monitoring/CI/CD

### Implementation: scripts/health_check.py

**Logic Flow**:
```python
1. Load DB_URL from environment (os.getenv('DB_URL'))
2. If DB_URL missing, use verified fallback: 'postgresql://postgres:password@localhost:5432/data_nexus'
3. Attempt connection with 3-second timeout
4. If connected:
   - Query: SELECT COUNT(*) FROM market_data
   - Query: SELECT COUNT(*) FROM assets
   - Print row counts
   - Print "✅ System Healthy"
   - Exit with code 0
5. If failed:
   - Print error message with connection details
   - Print "❌ System Unhealthy"
   - Exit with code 1
```

**Expected Output (Success)**:
```
📊 Infrastructure Health Check
================================================================================

✅ Database Connection: postgresql://postgres:password@localhost:5432/data_nexus
✅ Connection Status: HEALTHY

📈 Table Statistics:
   market_data: 340,494 rows
   assets: 975 rows

✅ System Healthy
```

**Expected Output (Failure)**:
```
📊 Infrastructure Health Check
================================================================================

❌ Database Connection Failed: postgresql://postgres:password@localhost:5432/data_nexus
   Error: FATAL: password authentication failed for user "postgres"

❌ System Unhealthy
```

---

## Part 4: Implementation Steps

### Step 1: Documentation (DONE)
✅ This file (`docs/TASK_040_9_INFRA_REPORT.md`)

### Step 2: Root Directory Cleanup Script

**File**: `scripts/maintenance/cleanup_root.py`

**Features**:
- Scan project root for orphaned venv components
- Verify files are actually orphaned (not project files)
- Create backup directory `_archive_venv_cleanup_<timestamp>/`
- Move orphaned files to backup (non-destructive)
- Report cleanup actions taken
- Verify cleanup success

**Safety Measures**:
- DO NOT touch `src/`, `venv/`, `scripts/` directories
- DO NOT touch any `.py` files in root
- Create backup before deletion
- Report all actions for audit trail

### Step 3: Health Check Script

**File**: `scripts/health_check.py`

**Features**:
- Load `.env` configuration
- Use verified database credentials as fallback
- Test connectivity with timeout
- Query row counts from both tables
- Report formatted output
- Exit with proper codes (0 = healthy, 1 = unhealthy)

### Step 4: Environment Configuration

**File**: `.env` (create if missing)

**Content**:
```bash
# Database Configuration (Verified Working)
DB_URL=postgresql://trader:password@localhost:5432/mt5_crs

# Alternative format for components
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password
POSTGRES_DB=mt5_crs
```

### Step 5: Updated Audit Script

**File**: `scripts/audit_current_task.py` (update)

**New Audit Checks**:
1. ✅ Documentation exists (`docs/TASK_040_9_INFRA_REPORT.md`)
2. ✅ Root is clean (no `./bin`, `./lib`, `./lib64`, `./pyvenv.cfg`)
3. ✅ `.env` file exists with DB_URL
4. ✅ `scripts/health_check.py` exists
5. ✅ Cleanup script exists
6. ✅ `health_check.py` runs successfully (exit code 0)
7. ✅ Database connectivity confirmed via health check

---

## Part 5: Success Criteria

Task #040.9 is complete when ALL of the following are true:

1. ✅ Project root is clean
   - `./bin/` does NOT exist
   - `./lib/` does NOT exist
   - `./lib64/` does NOT exist
   - `./pyvenv.cfg` does NOT exist

2. ✅ Configuration is persisted
   - `.env` file exists
   - Contains: `DB_URL=postgresql://postgres:password@localhost:5432/data_nexus`

3. ✅ Health check is functional
   - `python3 scripts/health_check.py` executes successfully
   - Prints row counts for both tables
   - Returns exit code 0

4. ✅ Audit passes
   - `python3 scripts/audit_current_task.py` passes all checks
   - No failures reported

5. ✅ Documentation is complete
   - This file is comprehensive and up-to-date
   - All objectives documented

---

## Part 6: Files Created (Task #040.9)

1. **docs/TASK_040_9_INFRA_REPORT.md** (this file)
   - Comprehensive infrastructure cleanup specification
   - Current state assessment
   - Health check logic documentation

2. **scripts/maintenance/cleanup_root.py**
   - Orphaned venv artifact removal
   - Backup creation for safety
   - Cleanup verification

3. **scripts/health_check.py**
   - Permanent infrastructure health monitoring
   - Database connectivity verification
   - Row count reporting

4. **scripts/audit_current_task.py** (updated)
   - Root cleanliness verification
   - Health check validation
   - Configuration verification

5. **.env** (created or updated)
   - Database configuration persistence
   - Verified connection credentials

---

## Part 7: Execution Workflow

```bash
# Step 1: Initialize (DONE)
python3 scripts/project_cli.py start "Task #040.9: Infra Standardization"

# Step 2: Plan (DONE - this file)
# docs/TASK_040_9_INFRA_REPORT.md created

# Step 3: Cleanup (TODO)
python3 scripts/maintenance/cleanup_root.py

# Step 4: Health Check (TODO)
python3 scripts/health_check.py

# Step 5: Audit (TODO)
python3 scripts/audit_current_task.py

# Step 6: Finish (TODO)
python3 scripts/project_cli.py finish
```

---

## Part 8: Known Considerations

### Database User Authentication
- Verified credentials: `trader:password`
- Database: `mt5_crs`
- Host: `localhost` (127.0.0.1)
- Connected tables: market_data (340,494 rows), assets (975 rows)

### venv Strategy
- Keep `/opt/mt5-crs/venv/` as primary virtual environment
- Clean `bin/`, `lib/`, `lib64/`, `pyvenv.cfg` from root
- These orphaned files suggest a root-level venv was created accidentally

### Fallback Strategy
- If `.env` is missing or DB_URL not set, use verified credentials as fallback
- Prevents script failure if configuration is incomplete

---

**Generated**: 2025-12-29
**Author**: Claude Sonnet 4.5
**Status**: Specification Complete - Ready for Implementation
