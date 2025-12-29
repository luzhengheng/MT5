# Task #040.9: Infrastructure Integrity & Identity Check

**Date**: 2025-12-29
**Task**: Infrastructure Audit & Environment Repair
**Protocol**: v2.2 (Docs-as-Code)
**Status**: Diagnostic Phase

---

## Executive Summary

This task performs a comprehensive infrastructure audit to:
1. **Verify server identity** (hostname, IP addresses)
2. **Clean up polluted root directory** (orphaned bin/, lib/ directories)
3. **Standardize virtual environment** (ensure proper venv structure)
4. **Verify database connectivity** (PostgreSQL/TimescaleDB)
5. **Document environment state** for future reference

---

## Context & Problem Statement

### User-Reported Issues

1. **Environment Confusion**: Missing or unclear venv structure
2. **Server Identity**: Expected hostname `sg-infer-core-01` not explicitly verified
3. **Root Directory Pollution**: Possible exploded venv files in project root
4. **Database Connectivity**: Unclear which host/credentials work

### Current Environment State (Pre-Audit)

**Server Information** (Initial Check):
```
Hostname: CRS
IP Address: 172.19.141.254
```

**Note**: User expected hostname `sg-infer-core-01`, but actual hostname is `CRS`.

**Project Root Pollution**:
```
/opt/mt5-crs/
├── bin/          ← Suspicious (could be orphaned venv)
├── venv/         ← Proper venv exists
├── lib/          ← Not present (good)
├── lib64/        ← Not present (good)
└── pyvenv.cfg    ← Not present (good)
```

**Initial Assessment**:
- ✅ Proper `venv/` directory exists
- ⚠️  `bin/` directory present in root (needs investigation)
- ✅ No `lib/`, `lib64/`, or `pyvenv.cfg` in root

---

## Diagnostic Objectives

### 1. Server Identity Verification

**Goals**:
- Confirm actual hostname (is it `CRS` or `sg-infer-core-01`?)
- Detect all IP addresses (public, private, localhost)
- Verify network interfaces
- Document OS and Python versions

**Expected Output**:
```
🖥️  Server Hostname: CRS (or sg-infer-core-01)
🌐 Private IP: 172.19.141.254
🌐 Localhost: 127.0.0.1
🐧 OS: Linux 5.10.134-19.2.al8.x86_64
🐍 Python: 3.9.x
```

### 2. Environment Cleanup

**Goals**:
- Identify orphaned directories in project root
- Move or remove `bin/` if it's not part of project structure
- Ensure clean separation between project code and venv
- Verify `venv/` is properly structured

**Cleanup Strategy**:
```python
# IF bin/ is orphaned venv remnant:
mv /opt/mt5-crs/bin /opt/mt5-crs/_archive_orphaned_bin

# IF bin/ is legitimate project code:
# Keep it (e.g., contains custom scripts)

# Verify venv structure:
venv/
├── bin/          ← Python executables
├── lib/          ← Python packages
├── lib64/        ← Symlink to lib
├── pyvenv.cfg    ← Venv config
└── include/      ← Headers
```

### 3. Virtual Environment Standardization

**Goals**:
- Confirm `venv/` has all required components
- Verify `venv/bin/activate` works
- Test package installation in venv
- Document installed packages

**Validation Checks**:
```bash
# Check venv activation
source venv/bin/activate

# Verify pip works
pip --version

# List installed packages
pip list

# Test critical imports
python -c "import pandas, sqlalchemy, psycopg2, redis"
```

### 4. Database Connectivity Matrix

**Goals**:
- Test connectivity to PostgreSQL via multiple methods
- Try different credential combinations
- Verify TimescaleDB extension availability
- Document working connection string

**Connection Attempts**:

| Host         | Port | User      | Password         | Expected Result |
|--------------|------|-----------|------------------|-----------------|
| localhost    | 5432 | postgres  | (empty)          | ?               |
| localhost    | 5432 | postgres  | password         | ?               |
| localhost    | 5432 | trader    | mt5crs_dev_2025  | ?               |
| 127.0.0.1    | 5432 | trader    | mt5crs_dev_2025  | ?               |
| 172.19.141.254 | 5432 | trader  | mt5crs_dev_2025  | ?               |
| CRS          | 5432 | trader    | mt5crs_dev_2025  | ?               |

**Success Criteria**: At least one connection method works.

---

## Implementation Architecture

### Tool 1: fix_environment.py

**Purpose**: Clean up root directory and standardize venv

**Location**: `scripts/maintenance/fix_environment.py`

**Features**:
1. **Scan Root**: Identify suspicious files/directories
2. **Backup**: Move suspects to `_archive_orphaned_*/`
3. **Verify Venv**: Ensure `venv/` is healthy
4. **Rebuild (if needed)**: Recreate venv if corrupted
5. **Reinstall Core Packages**: pandas, sqlalchemy, psycopg2, redis

**Logic**:
```python
def scan_root_directory():
    """Identify orphaned venv components."""
    suspects = ['bin', 'lib', 'lib64', 'include', 'pyvenv.cfg']
    found = []

    for suspect in suspects:
        path = PROJECT_ROOT / suspect
        if path.exists():
            # Check if it's actually part of project
            if is_orphaned_venv_component(path):
                found.append(path)

    return found

def cleanup_orphaned_files(suspects):
    """Move orphaned files to archive."""
    archive_dir = PROJECT_ROOT / f"_archive_orphaned_{timestamp}"
    archive_dir.mkdir(exist_ok=True)

    for suspect in suspects:
        shutil.move(str(suspect), str(archive_dir / suspect.name))

def verify_venv():
    """Ensure venv is properly structured."""
    venv_path = PROJECT_ROOT / "venv"

    required = ['bin', 'lib', 'pyvenv.cfg']
    missing = [comp for comp in required if not (venv_path / comp).exists()]

    if missing:
        print(f"❌ Venv missing: {missing}")
        print("🔧 Rebuilding venv...")
        rebuild_venv()
    else:
        print("✅ Venv structure valid")

def rebuild_venv():
    """Recreate virtual environment."""
    subprocess.run(["python3", "-m", "venv", "venv"], check=True)

    # Install core packages
    subprocess.run([
        "venv/bin/pip", "install",
        "pandas", "sqlalchemy", "psycopg2-binary", "requests", "redis"
    ], check=True)
```

### Tool 2: deep_probe.py

**Purpose**: Deep diagnostic of server identity and database connectivity

**Location**: `scripts/maintenance/deep_probe.py`

**Features**:
1. **Server Identity**:
   - Hostname (platform.node())
   - All IP addresses (socket.getaddrinfo)
   - OS details (platform.system(), platform.release())
   - Python version

2. **Network Interfaces**:
   - List all network interfaces
   - IPv4/IPv6 addresses
   - Loopback, private, public IPs

3. **Database Connectivity**:
   - Brute-force all credential combinations
   - Test localhost vs hostname vs IP
   - Verify TimescaleDB extension
   - Show successful connection string

4. **Service Health**:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - Any other critical services

**Logic**:
```python
def verify_server_identity():
    """Print comprehensive server information."""
    print("🖥️  Server Identity:")
    print(f"   Hostname: {platform.node()}")
    print(f"   FQDN: {socket.getfqdn()}")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {platform.python_version()}")

    # Get all IP addresses
    hostname = socket.gethostname()
    ip_list = socket.getaddrinfo(hostname, None)

    for ip_info in ip_list:
        family, addr = ip_info[0], ip_info[4][0]
        print(f"   IP ({family}): {addr}")

def test_database_connectivity():
    """Brute-force test all DB connection methods."""
    credentials = [
        ("localhost", 5432, "postgres", ""),
        ("localhost", 5432, "postgres", "password"),
        ("localhost", 5432, "trader", "password"),
        ("localhost", 5432, "trader", "mt5crs_dev_2025"),
        ("127.0.0.1", 5432, "trader", "mt5crs_dev_2025"),
        (platform.node(), 5432, "trader", "mt5crs_dev_2025"),
    ]

    for host, port, user, password in credentials:
        try:
            conn_string = f"postgresql://{user}:{password}@{host}:{port}/mt5_crs"
            engine = create_engine(conn_string, connect_args={"connect_timeout": 3})

            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]

                print(f"✅ SUCCESS: {user}@{host}:{port}")
                print(f"   Connection: {conn_string}")
                print(f"   Version: {version[:50]}...")
                return conn_string  # Return first working connection

        except Exception as e:
            print(f"❌ FAILED: {user}@{host}:{port} → {e}")

    return None
```

---

## Audit Specification

### Audit Checks (scripts/audit_current_task.py)

1. **Documentation**: `docs/TASK_040_9_INFRA_AUDIT.md` exists
2. **Venv Structure**: `venv/bin/activate` exists
3. **Root Clean**: `pyvenv.cfg` NOT in project root
4. **Maintenance Tools**: `scripts/maintenance/fix_environment.py` exists
5. **Diagnostic Tool**: `scripts/maintenance/deep_probe.py` exists
6. **Deep Probe Runs**: `deep_probe.py` executes without errors
7. **Database Connected**: At least one DB connection method works

---

## Expected Outcomes

### 1. Server Identity Report

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          SERVER IDENTITY REPORT                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

🖥️  HOSTNAME: CRS
🌐 IP ADDRESS (Primary): 172.19.141.254
🌐 LOOPBACK: 127.0.0.1
🐧 OPERATING SYSTEM: Linux 5.10.134-19.2.al8.x86_64
🐍 PYTHON VERSION: 3.9.x
```

### 2. Environment Health Report

```
📁 PROJECT ROOT STATUS:
   ✅ venv/ exists and is healthy
   ✅ No orphaned venv files in root
   ✅ pip functional in venv
   ✅ Core packages installed: pandas, sqlalchemy, psycopg2, redis

🔧 CLEANUP ACTIONS TAKEN:
   - Moved bin/ to _archive_orphaned_20251229/ (if orphaned)
   - Verified venv structure
   - No rebuild needed
```

### 3. Database Connectivity Report

```
🗄️  DATABASE CONNECTIVITY:
   ✅ Connection: postgresql://trader:***@localhost:5432/mt5_crs
   ✅ TimescaleDB: Detected
   ✅ Tables: market_data, assets
   ✅ Row Counts: market_data (30), assets (1)
```

---

## File Deliverables

1. **[docs/TASK_040_9_INFRA_AUDIT.md](docs/TASK_040_9_INFRA_AUDIT.md)** (this file)
   - Comprehensive infrastructure audit specification
   - Diagnostic objectives and strategies
   - Expected outcomes

2. **[scripts/maintenance/fix_environment.py](scripts/maintenance/fix_environment.py)**
   - Root directory cleanup
   - Venv verification and rebuild
   - Package installation

3. **[scripts/maintenance/deep_probe.py](scripts/maintenance/deep_probe.py)**
   - Server identity verification
   - Network interface discovery
   - Database connectivity brute-force testing
   - Comprehensive diagnostic report

4. **[scripts/audit_current_task.py](scripts/audit_current_task.py)** (updated)
   - Infrastructure integrity checks
   - Venv validation
   - Database connectivity assertion

---

## Usage Instructions

### Step 1: Run Deep Probe (Diagnostic)

```bash
python3 scripts/maintenance/deep_probe.py
```

**Output**: Full diagnostic report showing:
- Server hostname and IPs
- Database connectivity status
- Network interfaces
- Service health

### Step 2: Run Environment Fix (if needed)

```bash
python3 scripts/maintenance/fix_environment.py
```

**Actions**:
- Cleans up orphaned files
- Verifies venv health
- Rebuilds venv if necessary
- Installs core packages

### Step 3: Run Audit

```bash
python3 scripts/audit_current_task.py
```

**Validation**: All infrastructure checks must pass

---

## Known Issues & Resolutions

### Issue 1: Hostname Mismatch

**Expected**: `sg-infer-core-01`
**Actual**: `CRS`

**Resolution**: Document actual hostname and update all references

### Issue 2: bin/ Directory in Root

**Possible Causes**:
1. Orphaned venv from accidental root-level venv creation
2. Legitimate project scripts directory
3. Symlink from another location

**Resolution**: `fix_environment.py` determines origin and archives if orphaned

### Issue 3: Database Connection Failures

**Symptoms**: Password authentication failures, connection refused

**Root Causes**:
1. PostgreSQL not running
2. Wrong credentials
3. Wrong host (localhost vs IP vs hostname)

**Resolution**: `deep_probe.py` tests all combinations and reports working connection

---

## Success Criteria

Task #040.9 is complete when:

1. ✅ Server identity documented (hostname: CRS, IP: 172.19.141.254)
2. ✅ Project root directory clean (no orphaned venv files)
3. ✅ Virtual environment standardized and healthy
4. ✅ Database connectivity verified and documented
5. ✅ All audit checks passing (7/7)
6. ✅ Deep probe runs successfully
7. ✅ Comprehensive diagnostic report generated

---

## Future Maintenance

### Recommended Practices

1. **Always use venv**: Never install packages globally
2. **Activate before work**: `source venv/bin/activate`
3. **Periodic audits**: Run `deep_probe.py` monthly
4. **Document changes**: Update this doc when environment changes

### Environment Variables

**Critical vars** (should be in `.env`):
```bash
POSTGRES_USER=trader
POSTGRES_PASSWORD=mt5crs_dev_2025
POSTGRES_DB=mt5_crs
POSTGRES_HOST=localhost  # or CRS or 172.19.141.254
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

EODHD_API_KEY=6946528053f746.84974385
```

---

**Generated**: 2025-12-29
**Author**: Claude Sonnet 4.5
**Protocol**: v2.2 (Docs-as-Code)
**Status**: Specification Complete
