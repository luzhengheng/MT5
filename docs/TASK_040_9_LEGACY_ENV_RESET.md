# Task #040.9: Legacy Environment Reset & Standardization

**Date**: 2025-12-29
**Protocol**: v2.2 (Docs-as-Code) - Local storage only
**Authorization**: User explicitly authorized aggressive cleanup of root artifacts
**Status**: Implementation Phase

---

## Executive Summary

This task performs an **aggressive cleanup** of the legacy development environment to resolve root directory pollution and establish a clean, verified infrastructure baseline. The operation includes:

1. **Nuke legacy artifacts** (`bin/`, `lib/`, `lib64/`, `include/`, `pyvenv.cfg`)
2. **Rebuild fresh venv** with core dependencies
3. **Persist verified configuration** in `.env`
4. **Provide immediate recovery tools** (health check, emergency backfill)

---

## Context & Problem Statement

### Current Root Pollution
```
/opt/mt5-crs/
├── bin/          ← LEGACY (contains old scripts from deprecated project)
├── lib/          ← LEGACY (orphaned venv artifact)
├── lib64/        ← LEGACY (orphaned venv artifact)
├── include/      ← LEGACY (orphaned C headers)
├── pyvenv.cfg    ← LEGACY (old venv config)
├── venv/         ← CURRENT (stale, will rebuild)
├── src/          ← PROJECT CODE (protected)
└── scripts/      ← PROJECT SCRIPTS (protected)
```

### Impact
- Confusion between legacy and current artifacts
- Multiple venv sources causing dependency conflicts
- Unclear project structure and maintenance burden

### Verified Configuration (Per User Authorization)
```
Database Host: localhost
Database Port: 5432
User: postgres
Password: password
Database: data_nexus
Connection String: postgresql://postgres:password@localhost:5432/data_nexus
Status: User-specified credentials configured (database initialization pending)

NOTE: During testing, discovered existing mt5_crs database with 340k+ rows.
      User explicitly authorized data_nexus configuration.
      Emergency backfill tool provided for immediate population.
```

---

## Cleanup Scope

### To Be Deleted
| Item | Type | Reason |
|------|------|--------|
| `bin/` | Directory | Legacy scripts |
| `lib/` | Directory | Orphaned venv packages |
| `lib64/` | Symlink | Orphaned venv symlink |
| `include/` | Directory | Orphaned C headers |
| `pyvenv.cfg` | File | Old venv config |
| `venv/` | Directory | Stale venv (will rebuild) |

### To Be Preserved
| Item | Type | Reason |
|------|------|--------|
| `src/` | Directory | Project source code |
| `scripts/` | Directory | Project scripts |
| `docs/` | Directory | Project documentation |
| `.git/` | Directory | Git repository |

---

## Implementation Specification

### reset_env.py - The Reset Script

**Location**: `scripts/maintenance/reset_env.py`

**Execution Flow**:
```
1. Verify safe paths (src/, scripts/, docs/, .git/ exist)
2. Delete legacy artifacts:
   - rm -rf bin lib lib64 include pyvenv.cfg venv
3. Create fresh venv:
   - python3 -m venv venv
4. Install core packages (using Tsinghua mirror for speed):
   - venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
     pandas sqlalchemy psycopg2-binary requests redis
5. Generate .env file with verified credentials
6. Verify all components are in place
```

**Safety Measures**:
- Pre-flight path verification
- Selective deletion (only specified items)
- No venv operations until verified rebuilt
- Comprehensive post-action verification

### Configuration Persistence

**File**: `.env` (Generated)

**Content**:
```bash
# ============================================================================
# Database Configuration (Task #040.9)
# ============================================================================
DB_URL=postgresql://postgres:password@localhost:5432/data_nexus
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=data_nexus

# ============================================================================
# API Keys
# ============================================================================
EODHD_API_TOKEN=6496528053f746.84974385

# ============================================================================
# Environment Flags
# ============================================================================
ENVIRONMENT=development
DEBUG=false
```

### health_check.py - Connectivity Verification

**Location**: `scripts/health_check.py`

**Purpose**: Verify environment health and database connectivity

**Logic**:
```python
1. Load .env file
2. Extract DB_URL from environment
3. Connect to database with 3-second timeout
4. Query: SELECT COUNT(*) FROM market_data
5. Query: SELECT COUNT(*) FROM assets
6. Print row counts
7. Exit 0 if healthy, 1 if failed
```

**Expected Output (Success)**:
```
📊 Infrastructure Health Check
Database: postgresql://postgres:***@localhost:5432/data_nexus
✅ Connection successful
📈 Table Statistics:
   market_data: X rows
   assets: Y rows
✅ System Healthy
```

### emergency_backfill.py - Data Recovery Tool

**Location**: `scripts/emergency_backfill.py`

**Purpose**: Populate empty database with initial data for development

**Logic**:
```python
1. Load .env for database and API credentials
2. Download AAPL.US historical data (last 30 days)
3. Insert into market_data table
4. Register asset in assets table
5. Verify row count increased
6. Print success confirmation
```

**Usage**:
```bash
python3 scripts/emergency_backfill.py
```

**Expected Output**:
```
⬇️  DOWNLOADING AAPL.US (30 days)
✅ Downloaded 30 records

💾 INSERTING INTO DATABASE
✅ Inserted 30 rows into market_data
✅ Registered AAPL.US in assets

📊 VERIFICATION
   market_data: 30 rows (was 0) → +30
   assets: 1 row (was 0) → +1

🎉 SUCCESS: Database populated
```

---

## Audit Specification

### audit_current_task.py - Verification Checks

**Required Checks**:

1. **Cleanup Verification**:
   - `os.path.exists("./bin")` → False ✅
   - `os.path.exists("./lib")` → False ✅
   - `os.path.exists("./lib64")` → False ✅
   - `os.path.exists("./include")` → False ✅
   - `os.path.exists("./pyvenv.cfg")` → False ✅

2. **Venv Verification**:
   - `os.path.exists("venv/bin/activate")` → True ✅
   - `venv/bin/pip list` works → Yes ✅

3. **Configuration Verification**:
   - `os.path.exists(".env")` → True ✅
   - `.env` contains `DB_URL=postgresql://postgres:password@localhost:5432/data_nexus` ✅

4. **Health Check Verification**:
   - `python3 scripts/health_check.py` → Exit code 0 ✅
   - Output contains "System Healthy" ✅

---

## Execution Workflow

```bash
# Step 1: Documentation (DONE - this file)
# Created: docs/TASK_040_9_LEGACY_ENV_RESET.md

# Step 2: Create Reset Script (TODO)
# Create: scripts/maintenance/reset_env.py

# Step 3: Create Health Check (TODO)
# Create: scripts/health_check.py

# Step 4: Create Emergency Backfill (TODO)
# Create: scripts/emergency_backfill.py

# Step 5: Execute Reset (TODO)
python3 scripts/maintenance/reset_env.py

# Step 6: Verify Health (TODO)
python3 scripts/health_check.py

# Step 7: Run Audit (TODO)
python3 scripts/audit_current_task.py
```

---

## Success Criteria (Definition of Done)

✅ **Root Directory Clean**
- `./bin/` does NOT exist
- `./lib/` does NOT exist
- `./lib64/` does NOT exist
- `./include/` does NOT exist
- `./pyvenv.cfg` does NOT exist

✅ **Fresh venv Created**
- `./venv/bin/activate` EXISTS
- Core packages installed and functional

✅ **Configuration Persisted**
- `.env` file exists
- Contains `DB_URL=postgresql://postgres:password@localhost:5432/data_nexus`

✅ **Health Check Passes**
- `python3 scripts/health_check.py` returns exit code 0
- Prints "System Healthy"
- Shows row counts for both tables

✅ **Audit Passes**
- All 4 verification checks pass
- No legacy artifacts remain
- Project structure intact

---

## Known Constraints & Considerations

### Database Configuration
- **Verified credentials**: `postgres:password@localhost:5432/data_nexus`
- **Tables**: `market_data`, `assets` (may be empty initially)
- **Recovery**: Use `emergency_backfill.py` if tables are empty

### Package Installation
- **Mirror**: Tsinghua (`https://pypi.tuna.tsinghua.edu.cn/simple`)
- **Reason**: Faster and more reliable for Chinese network
- **Packages**: pandas, sqlalchemy, psycopg2-binary, requests, redis

### API Key
- **EODHD_API_TOKEN**: `6496528053f746.84974385`
- **Usage**: Data backfill and historical downloads

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Delete wrong files | Pre-flight verification of safe paths |
| Git damage | Git directory explicitly protected |
| Data loss | Database is external, venv is rebuilable |
| Incomplete cleanup | Post-action verification of all deletions |

---

## Post-Reset Steps

After reset completes and audit passes:

1. **Activate venv**:
   ```bash
   source venv/bin/activate
   ```

2. **Verify connectivity**:
   ```bash
   python3 scripts/health_check.py
   ```

3. **Populate database (if empty)**:
   ```bash
   python3 scripts/emergency_backfill.py
   ```

4. **Full data backfill (optional)**:
   ```bash
   python3 scripts/run_bulk_backfill.py --symbols 100 --days 365
   ```

---

**Document Created**: 2025-12-29
**Author**: Claude Sonnet 4.5
**Protocol**: v2.2 (Docs-as-Code)
**Status**: Ready for Implementation
