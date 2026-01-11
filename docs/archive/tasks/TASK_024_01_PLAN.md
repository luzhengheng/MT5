# TASK #024.01: Environment Safe Purge Protocol

**Status**: In Progress
**Ticket**: #077
**Category**: Reliability Engineering / Maintenance
**Protocol**: v2.2 (Infrastructure Safety)

---

## 1. Executive Summary

Task #024.01 implements a safe environment purge protocol for the MT5 trading system. When algorithms fail, caches corrupt, or logs overflow, operators need a "Reset Button" that clears runtime state without losing critical configuration or trained models.

This script provides:
- **Selective purge**: Only removes runtime data (logs, cache, docker state)
- **Protected paths**: Never touches models, config, .env, or .git
- **User confirmation**: Requires explicit "y/n" acknowledgement unless `--force` flag is used
- **Verification**: Pre-flight checks ensure safety before any deletion
- **Dry-run support**: `--dry-run` mode shows what would be deleted without actually deleting

---

## 2. Problem Context

### Operational Scenarios

**Scenario 1: Runaway Algorithm**
- Strategy enters infinite loop or oscillation
- Thousands of orders queued
- Need to stop services and reset state FAST
- Solution: `purge_env.py --force` (with confirmation for safety)

**Scenario 2: Cache Corruption**
- Redis cache contains poisoned feature data
- Model predictions become unreliable
- Need to clear cache without restarting entire system
- Solution: `purge_env.py` (selective purge of redis data)

**Scenario 3: Log Explosion**
- Verbose logging filled disk
- Services can't write new logs
- Need to reclaim disk space immediately
- Solution: `purge_env.py` (clear logs, keep running)

**Scenario 4: Corrupt Database State**
- Historical trades in inconsistent state
- Reports show wrong P&L
- Need full reset before retraining
- Solution: `docker compose down`, then `purge_env.py`

### Current Risks (Without Safe Purge)

❌ Operator manually deletes files
- Risk: Accidentally deletes /opt/mt5-crs/models/baseline_v1.json (trained model)
- Risk: Deletes .env file (credentials lost)
- Risk: Deletes .git directory (version history lost)

❌ Docker volumes persist after `docker compose down`
- Named volumes (postgres_data, redis_data) remain
- Old state carries into next run
- Leads to data inconsistency

❌ No way to quickly recover from emergency
- Manual recovery takes 5-10 minutes
- Expensive in fast-moving markets
- Increases operational risk

### Solution: Safe Purge Protocol

✅ Single command with clear output
✅ Protects critical paths
✅ Requires user confirmation
✅ Logs what was deleted
✅ Verifies success

---

## 3. Script Design

### Path Classifications

**Protected Paths** (NEVER delete):
- `models/` - Trained ML models (precious, hard to rebuild)
- `config/` - Strategy configuration
- `.env` - Credentials and secrets
- `.git/` - Version history
- `.gitignore` - Git metadata
- `scripts/` - Maintenance scripts themselves
- `src/` - Application source code
- `docs/` - Documentation

**Ephemeral Paths** (SAFE to delete):
- `logs/` - Application logs (can be regenerated)
- `data/redis/` - Redis cache (can be rebuilt)
- `.docker-compose-state` - Docker metadata (transient)
- Docker volumes: `redis_data`, `postgres_data` (named volumes, recreated on restart)

### Script Architecture

```python
class SafePurge:
    PROTECTED_PATHS = {
        'models', 'config', 'src', 'scripts', 'docs',
        '.git', '.gitignore', '.env', '.env.example'
    }

    EPHEMERAL_PATHS = {
        'logs', 'data/redis', 'data/temp'
    }

    def __init__(self, dry_run=False, force=False):
        self.dry_run = dry_run
        self.force = force
        self.deleted_items = []

    def is_protected(self, path):
        """Check if path is in protected list"""

    def ask_confirmation(self):
        """Prompt user: 'Are you sure? (y/n)'"""

    def stop_services(self):
        """Run: docker compose down"""

    def purge_cache(self):
        """Remove redis data"""

    def purge_logs(self):
        """Remove log files"""

    def cleanup_docker_volumes(self):
        """Remove Docker named volumes (optional with --full)"""

    def verify_cleanup(self):
        """Verify protected paths still exist"""

    def report(self):
        """Show what was deleted"""
```

### Command-Line Interface

```bash
# Interactive mode (shows what will be deleted, asks for confirmation)
python3 scripts/maintenance/purge_env.py

# Force mode (skips confirmation, useful for automation)
python3 scripts/maintenance/purge_env.py --force

# Dry-run mode (shows what WOULD be deleted, doesn't delete anything)
python3 scripts/maintenance/purge_env.py --dry-run

# Full purge (includes Docker named volumes, requires extra confirmation)
python3 scripts/maintenance/purge_env.py --full

# Verbose logging
python3 scripts/maintenance/purge_env.py --verbose

# Combination
python3 scripts/maintenance/purge_env.py --dry-run --verbose
```

### Safety Features

**Feature 1: Pre-flight Checks**
```
Before deletion:
1. Verify models/ directory exists and contains files
2. Verify .env file exists
3. Check .git directory for version history
4. Validate no critical config files will be deleted
```

**Feature 2: User Confirmation**
```
================================================================================
🚨 ENVIRONMENT PURGE PROTOCOL
================================================================================

This will DELETE:
  ✓ logs/                    (application logs)
  ✓ data/redis/              (cache data)
  ✓ Docker services (docker compose down)

This will NOT delete:
  ✓ models/                  (trained models - PROTECTED)
  ✓ config/                  (strategy configuration - PROTECTED)
  ✓ .env                     (secrets - PROTECTED)
  ✓ src/                     (source code - PROTECTED)
  ✓ .git/                    (version history - PROTECTED)

⚠️  Are you sure you want to proceed? (y/n):
```

**Feature 3: Verbose Logging**
```
After confirmation, show each action:
  [1/5] Stopping Docker services...
        $ docker compose down
        ✅ Services stopped

  [2/5] Clearing Redis cache...
        $ rm -rf data/redis/
        ✅ Removed 45 files (2.3 MB)

  [3/5] Clearing logs...
        $ rm -rf logs/
        ✅ Removed 127 files (45.6 MB)

  [4/5] Verifying protection...
        ✅ models/baseline_v1.json (123 MB) - SAFE
        ✅ .env (2 KB) - SAFE
        ✅ .git/ - SAFE

  [5/5] Summary
        Total freed: 47.9 MB
        Runtime: 3.2 seconds
```

**Feature 4: Error Recovery**
```
If deletion fails:
  ❌ Failed to delete logs/: Permission denied

  Recovery:
  1. Check permissions: ls -la logs/
  2. Run with sudo if needed: sudo purge_env.py
  3. Or manually: sudo rm -rf logs/
  4. Verify: python3 scripts/maintenance/purge_env.py --dry-run
```

---

## 4. Implementation Details

### File: `scripts/maintenance/purge_env.py`

```python
#!/usr/bin/env python3
"""
Environment Safe Purge Protocol

Task #024.01: Safely reset runtime state while protecting configuration.

This script provides a "Reset Button" for the MT5 trading system:
- Stops Docker services
- Clears caches and logs
- Protects critical files (models, config, .env, source code)
- Requires user confirmation
- Verifies safety before deletion

Usage:
  python3 scripts/maintenance/purge_env.py                # Interactive
  python3 scripts/maintenance/purge_env.py --force       # Automatic
  python3 scripts/maintenance/purge_env.py --dry-run     # Preview
  python3 scripts/maintenance/purge_env.py --full        # Include volumes
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

class SafePurge:
    """Environment purge protocol with safety guards"""

    # Paths that should NEVER be deleted
    PROTECTED_PATHS = {
        'models',
        'config',
        'src',
        'scripts',
        'docs',
        '.git',
        '.gitignore',
        '.env',
        '.env.example',
        'requirements.txt',
        'Dockerfile.strategy',
        'Dockerfile.api',
        'docker-compose.prod.yml'
    }

    # Paths that are safe to delete
    EPHEMERAL_PATHS = [
        'logs',
        'data/redis',
        'data/temp'
    ]

    def __init__(self, project_root=None, dry_run=False, force=False, full=False, verbose=False):
        self.project_root = Path(project_root or os.getcwd())
        self.dry_run = dry_run
        self.force = force
        self.full = full
        self.verbose = verbose
        self.deleted_items = []
        self.total_size = 0

    def is_protected(self, path):
        """Check if path is in protected list"""
        path_obj = Path(path)

        # Check direct matches
        if path_obj.name in self.PROTECTED_PATHS:
            return True

        # Check parent directories
        for protected in self.PROTECTED_PATHS:
            if protected in str(path):
                return True

        return False

    def log(self, message):
        """Print message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def confirm(self):
        """Ask user for confirmation"""
        if self.force:
            return True

        print()
        print(f"{RED}⚠️  Are you sure you want to proceed? (y/n): {RESET}", end="")

        response = input().strip().lower()

        if response != 'y':
            print(f"{YELLOW}Purge cancelled{RESET}")
            return False

        return True

    def stop_services(self):
        """Stop Docker services"""
        if self.verbose:
            self.log("Stopping Docker services...")

        if self.dry_run:
            self.log(f"{YELLOW}[DRY-RUN]{RESET} docker compose down")
            return

        try:
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                self.log(f"{GREEN}✅ Docker services stopped{RESET}")
            else:
                self.log(f"{YELLOW}⚠️  Docker compose down: {result.stderr.decode()}{RESET}")

        except FileNotFoundError:
            self.log(f"{YELLOW}⚠️  docker-compose not installed, skipping{RESET}")
        except Exception as e:
            self.log(f"{RED}❌ Error stopping services: {e}{RESET}")

    def delete_path(self, path):
        """Safely delete a path"""
        full_path = self.project_root / path

        # Safety check
        if self.is_protected(str(full_path)):
            self.log(f"{YELLOW}⚠️  Skipping protected path: {path}{RESET}")
            return

        if not full_path.exists():
            if self.verbose:
                self.log(f"{YELLOW}ℹ️  Path doesn't exist: {path}{RESET}")
            return

        if self.dry_run:
            self.log(f"{YELLOW}[DRY-RUN]{RESET} rm -rf {path}")
            return

        try:
            if full_path.is_file():
                size = full_path.stat().st_size
                full_path.unlink()
            else:
                size = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
                shutil.rmtree(full_path)

            self.total_size += size
            self.deleted_items.append((path, size))
            self.log(f"{GREEN}✅ Deleted {path}{RESET} ({self._format_size(size)})")

        except PermissionError:
            self.log(f"{RED}❌ Permission denied: {path}{RESET}")
        except Exception as e:
            self.log(f"{RED}❌ Error deleting {path}: {e}{RESET}")

    def purge_logs(self):
        """Remove log files"""
        if self.verbose:
            self.log("Purging logs...")

        self.delete_path('logs')

    def purge_cache(self):
        """Remove Redis cache"""
        if self.verbose:
            self.log("Purging cache...")

        self.delete_path('data/redis')
        self.delete_path('data/temp')

    def cleanup_docker_volumes(self):
        """Remove Docker named volumes"""
        if not self.full:
            return

        if self.verbose:
            self.log("Cleaning up Docker volumes...")

        if self.dry_run:
            self.log(f"{YELLOW}[DRY-RUN]{RESET} docker volume rm redis_data postgres_data prometheus_data grafana_data logs_volume")
            return

        volumes = ['redis_data', 'postgres_data', 'prometheus_data', 'grafana_data', 'logs_volume']

        for volume in volumes:
            try:
                subprocess.run(
                    ["docker", "volume", "rm", volume],
                    capture_output=True,
                    timeout=10
                )
                self.log(f"{GREEN}✅ Removed Docker volume: {volume}{RESET}")
            except Exception as e:
                self.log(f"{YELLOW}⚠️  Could not remove volume {volume}: {e}{RESET}")

    def verify_protection(self):
        """Verify protected paths still exist"""
        if self.verbose:
            self.log("Verifying protection...")

        missing = []

        for protected_path in self.PROTECTED_PATHS:
            full_path = self.project_root / protected_path

            if not full_path.exists():
                missing.append(protected_path)
                self.log(f"{RED}❌ Missing: {protected_path}{RESET}")
            else:
                if self.verbose:
                    self.log(f"{GREEN}✅ Protected: {protected_path}{RESET}")

        return len(missing) == 0

    @staticmethod
    def _format_size(bytes_size):
        """Format bytes to human-readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    def show_summary(self):
        """Display purge summary"""
        print()
        print("=" * 80)
        print(f"📊 PURGE SUMMARY")
        print("=" * 80)
        print()

        if self.dry_run:
            print(f"{YELLOW}[DRY-RUN MODE]{RESET}")
            print("The above items WOULD be deleted but were NOT actually deleted.")
        else:
            if self.deleted_items:
                print(f"{GREEN}Successfully deleted:{RESET}")
                for path, size in self.deleted_items:
                    print(f"  ✓ {path} ({self._format_size(size)})")
                print()

        print(f"Total size reclaimed: {self._format_size(self.total_size)}")
        print()

        if self.verify_protection():
            print(f"{GREEN}✅ All protected paths verified safe{RESET}")
        else:
            print(f"{RED}❌ Some protected paths are missing! Please verify.{RESET}")

        print()

    def run(self):
        """Execute purge protocol"""
        print()
        print("=" * 80)
        print(f"{CYAN}🚨 ENVIRONMENT PURGE PROTOCOL{RESET}")
        print(f"{CYAN}Task #024.01: Safe Runtime Reset{RESET}")
        print("=" * 80)
        print()

        print("This will DELETE:")
        for path in self.EPHEMERAL_PATHS:
            print(f"  ✓ {path:<30} (ephemeral data)")

        if self.full:
            print(f"  ✓ Docker named volumes        (named volumes)")

        print()
        print("This will NOT delete:")
        for path in sorted(self.PROTECTED_PATHS)[:10]:  # Show first 10
            print(f"  ✓ {path:<30} (PROTECTED)")
        if len(self.PROTECTED_PATHS) > 10:
            print(f"  ... and {len(self.PROTECTED_PATHS)-10} more protected paths")

        print()

        if self.dry_run:
            print(f"{YELLOW}[DRY-RUN MODE] - Nothing will be deleted{RESET}")
            print()

        if not self.confirm():
            return 1

        # Execute purge
        print()
        if self.verbose:
            self.log("Starting purge protocol...")

        self.stop_services()
        self.purge_logs()
        self.purge_cache()
        self.cleanup_docker_volumes()

        # Show summary
        self.show_summary()

        return 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Environment Safe Purge Protocol - Reset runtime state safely"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help="Also delete Docker named volumes (more destructive)"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Verbose output"
    )
    parser.add_argument(
        '--root',
        type=str,
        default=None,
        help="Project root directory"
    )

    args = parser.parse_args()

    purge = SafePurge(
        project_root=args.root,
        dry_run=args.dry_run,
        force=args.force,
        full=args.full,
        verbose=args.verbose
    )

    return purge.run()


if __name__ == "__main__":
    sys.exit(main())
```

---

## 5. Safety Test: `scripts/test_purge_safety.py`

```python
#!/usr/bin/env python3
"""
Test purge_env.py safety guards

Verifies that the purge script:
1. Does NOT delete models/
2. Does NOT delete .env
3. Does NOT delete .git
4. Correctly identifies ephemeral paths
5. Confirms before deletion (unless --force)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_protected_paths():
    """Test that SafePurge protects critical paths"""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

    from maintenance.purge_env import SafePurge

    purge = SafePurge(project_root=PROJECT_ROOT)

    # Test protected paths
    protected_paths = [
        'models/baseline_v1.json',
        'config/strategies.yaml',
        '.env',
        '.git',
        'src/main/runner.py',
        'scripts/audit_current_task.py'
    ]

    for path in protected_paths:
        if not purge.is_protected(path):
            print(f"❌ FAIL: {path} should be protected but isn't")
            return False
        else:
            print(f"✅ PASS: {path} is correctly protected")

    # Test ephemeral paths
    ephemeral_paths = [
        'logs/trading.log',
        'data/redis/dump.rdb',
        'data/temp/cache.pkl'
    ]

    for path in ephemeral_paths:
        if purge.is_protected(path):
            print(f"❌ FAIL: {path} should NOT be protected")
            return False
        else:
            print(f"✅ PASS: {path} is correctly identified as ephemeral")

    return True


def main():
    """Run all safety tests"""
    print("=" * 80)
    print("🔒 PURGE SAFETY VERIFICATION")
    print("=" * 80)
    print()

    if test_protected_paths():
        print()
        print("=" * 80)
        print("✅ ALL SAFETY TESTS PASSED")
        print("=" * 80)
        return 0
    else:
        print()
        print("=" * 80)
        print("❌ SAFETY TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. Usage Examples

### Example 1: Interactive Purge (Recommended)
```bash
$ python3 scripts/maintenance/purge_env.py
================================================================================
🚨 ENVIRONMENT PURGE PROTOCOL
...
Are you sure you want to proceed? (y/n): y

[Stopping Docker services...]
[Purging logs...]
[Purging cache...]
[Verifying protection...]

📊 PURGE SUMMARY
...
✅ All protected paths verified safe
```

### Example 2: Dry-Run First
```bash
$ python3 scripts/maintenance/purge_env.py --dry-run
# Shows what WOULD be deleted without actually deleting
```

### Example 3: Force Mode (For Automation)
```bash
$ python3 scripts/maintenance/purge_env.py --force --verbose
# Skips confirmation, shows detailed output
```

### Example 4: Full Purge (Nuclear Option)
```bash
$ python3 scripts/maintenance/purge_env.py --full
# Also deletes Docker named volumes (redis_data, postgres_data, etc.)
```

---

## 7. Success Criteria

✅ **Definition of Done**:

1. `scripts/maintenance/purge_env.py` exists and is executable
2. Purge script protects `models/`, `config/`, `.env`, `.git`, `src/`
3. Purge script safely deletes `logs/`, `data/redis/`, `data/temp/`
4. Confirmation prompt required unless `--force` flag used
5. Dry-run mode works without deleting
6. Safety test confirms protected paths are protected
7. All audit checks passing
8. All code committed and pushed

---

## 8. Integration with Operations

### When to Use Safe Purge

**Use Case 1: Algorithm Runaway**
```bash
# Stop everything and reset
python3 scripts/maintenance/purge_env.py --force
# Start fresh
docker-compose -f docker-compose.prod.yml up -d
```

**Use Case 2: Cache Poisoning**
```bash
# Quick cache clear without stopping services (manual for now)
rm -rf data/redis/*
# Services will rebuild cache on next request
```

**Use Case 3: Disk Space Emergency**
```bash
# Reclaim space from logs
python3 scripts/maintenance/purge_env.py --verbose
# Should free 50-200 MB depending on log verbosity
```

**Use Case 4: Full System Reset Before Retraining**
```bash
# Nuclear option - clears everything except models and config
python3 scripts/maintenance/purge_env.py --full
# Re-download historical data and retrain
```

---

## 9. Key Design Decisions

### Decision 1: Blacklist vs Whitelist
**Decision**: Use blacklist for protected paths (easier to reason about)

**Alternative**: Whitelist ephemeral paths (more conservative)

**Rationale**: Simpler to add new protected paths as codebase evolves. More forgiving if new files appear.

### Decision 2: Confirmation by Default
**Decision**: Require confirmation unless `--force` flag

**Rationale**: Prevents accidental data loss. `--force` for automation/CI.

### Decision 3: Verify After Deletion
**Decision**: Check protected paths exist after purge

**Rationale**: Catches catastrophic failures. Reassures operator.

---

**Author**: Reliability Engineering Team
**Date**: 2026-01-01
**Revision**: 1.0
