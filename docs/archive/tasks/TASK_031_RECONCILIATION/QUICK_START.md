# TASK #031: State Reconciliation & Crash Recovery - Quick Start Guide

## Overview

The State Reconciler module handles synchronization between Python's local PortfolioManager state and the Windows MT5 gateway. It protects against data loss from crashes and detects external modifications to positions.

## Prerequisites

Before using the State Reconciler, ensure:

1. **Task #029 (E2E Execution)** - ExecutionGateway working with GET_POSITIONS support
2. **Task #030 (Portfolio Manager)** - PortfolioManager tracking orders and positions
3. **Windows MT5 Gateway** running on `tcp://172.19.141.255:5555`
4. **Python Environment** with ZMQ and all dependencies installed

## Quick Start (Three Options)

### Option 1: Run Unit Tests Only

Test the reconciliation logic without requiring the gateway:

```bash
python3 scripts/test_reconciliation.py

# Expected output:
# Passed: 8/8
# Failed: 0/8
# ✅ All tests passed!
```

**What gets tested**:
- Startup recovery (zombie positions)
- Continuous drift detection
- Zombie vs ghost position detection
- Volume drift correction
- Gateway offline degradation
- Audit trail logging

**Time**: ~1 second

---

### Option 2: Integrate with Paper Trading Loop

Add reconciliation to the paper trading main loop:

```python
from src.strategy.reconciler import StateReconciler
from src.main_paper_trading import ExecutionGateway
from src.strategy.portfolio import PortfolioManager
from src.config import SYNC_INTERVAL_SEC

# Create components
pm = PortfolioManager(symbol="EURUSD")
gateway = ExecutionGateway()
reconciler = StateReconciler(pm, gateway, sync_interval_sec=SYNC_INTERVAL_SEC)

# On startup: recover any zombie positions
startup_result = reconciler.startup_recovery()
print(f"Recovered {startup_result.recovered} positions")

# In main loop: periodic drift detection
result = reconciler.sync_continuous()
if result:
    print(f"Drift detected: {len(result.drifts)} differences")
```

---

### Option 3: Manual Reconciliation

Perform immediate reconciliation without waiting for interval:

```python
from src.strategy.reconciler import StateReconciler

reconciler = StateReconciler(pm, gateway)

# Get current drift status
drift = reconciler.detect_drift()
if drift:
    print(f"Drift: {drift}")

# Perform full sync
result = reconciler.sync_positions()
print(f"Sync result: {result.status.value}")
print(f"  - Recovered: {result.recovered}")
print(f"  - Closed: {result.closed}")
print(f"  - Drifts fixed: {len(result.drifts)}")
```

## Configuration

### Environment Variables

```bash
# Reconciliation sync interval (default 15 seconds)
export SYNC_INTERVAL_SEC=15

# Gateway configuration (from TASK #029)
export GTW_HOST=172.19.141.255
export GTW_PORT=5555
export GTW_TIMEOUT_MS=2000
```

### Python Configuration

```python
from src.config import SYNC_INTERVAL_SEC, GTW_HOST, GTW_PORT

print(f"Sync every {SYNC_INTERVAL_SEC} seconds")
print(f"Gateway at {GTW_HOST}:{GTW_PORT}")
```

## StateReconciler API

### Core Methods

#### `startup_recovery() -> SyncResult`

Load any orphaned positions from gateway on startup.

**Use case**: Called once when application starts to rehydrate state after potential crash

```python
result = reconciler.startup_recovery()
assert result.recovered >= 0
```

---

#### `sync_continuous() -> Optional[SyncResult]`

Periodic sync check (non-blocking). Returns None if sync interval hasn't elapsed.

**Use case**: Call frequently from main loop - handles time-based throttling internally

```python
result = reconciler.sync_continuous()  # Returns None if too soon
if result and result.drifts:
    print(f"Detected {len(result.drifts)} drifts")
```

---

#### `sync_positions() -> SyncResult`

Full synchronization: compare local vs remote and reconcile.

**Use case**: Manual sync, testing, or when immediate reconciliation needed

```python
result = reconciler.sync_positions()
print(f"Status: {result.status.value}")
```

---

#### `detect_drift() -> Optional[str]`

Fast drift check (no modification). Returns None if state is consistent.

**Use case**: Quick health check before making trading decisions

```python
drift = reconciler.detect_drift()
if drift:
    print(f"State inconsistency: {drift}")
```

---

#### `get_audit_trail() -> List[Dict]`

Get all state changes for forensics and debugging.

```python
trail = reconciler.get_audit_trail()
for entry in trail[-10:]:  # Last 10 changes
    print(f"{entry['timestamp']} {entry['action']}: {entry['details']}")
```

---

#### `get_status() -> Dict`

Get reconciliation status.

```python
status = reconciler.get_status()
print(f"Last sync: {status['last_sync_time']}")
print(f"Sync count: {status['sync_count']}")
```

## Three-Phase Reconciliation

### Phase 1: Startup Recovery

When Python starts, check gateway for any open positions:

```
Python starts → Position is FLAT
↓
Query gateway: GET_POSITIONS
↓
If gateway has position → "Zombie" (Python lost it, gateway still has it)
↓
Force-add to local state
↓
Log: [RECOVERY] Zombie position recovered: Ticket 123456, LONG 0.01L
```

### Phase 2: Continuous Drift Detection

Every 15 seconds (configurable), compare local vs remote:

```
Timer triggers (15 sec elapsed)
↓
Query gateway: GET_POSITIONS
↓
Compare local positions with remote
├─ Remote has, local doesn't → Recovery (zombie)
├─ Local has, remote doesn't → Ghost close
└─ Volumes differ → Drift correction
↓
Log: [SYNC] Reconciliation complete: +0 -1 ~2 drifts
```

### Phase 3: Forced Sync

Handle conflict resolution:

```
Detect: Local LONG 0.01L, Remote LONG 0.02L
↓
Problem: Volume mismatch (drift)
↓
Solution: Update local to match remote (gateway is source of truth)
↓
Log: [DRIFT_FIX] Volume 0.01L → 0.02L
```

## Key Concepts

### Zombie Position

**Definition**: Position exists on MT5 gateway but not in Python local state

**Cause**: Python process crash/restart, position left open

**Recovery**: Force-add to local state with ticket number from gateway

```
[RECOVERY] Zombie position recovered: Ticket 123456, LONG 0.01L
```

### Ghost Position

**Definition**: Position exists in Python local state but not on MT5 gateway

**Cause**: User closed position in MT5 terminal manually

**Handling**: Force-close in local state

```
[CLOSED] Ghost position removed (Ticket 123456)
```

### Drift

**Definition**: Local and remote state differ (volume, price, etc.)

**Causes**:
- Network timeout caused incomplete fill confirmation
- Concurrent modifications
- Rounding errors

**Resolution**: Remote (gateway) is source of truth - local state updated

```
[DRIFT_FIX] Ticket 123456: volume 0.01L → 0.02L, price 1.0543 → 1.0544
```

## Error Handling

### Gateway Offline

If gateway doesn't respond to GET_POSITIONS:

```python
result = reconciler.startup_recovery()
assert result.status == SyncStatus.DEGRADED
assert "Gateway offline" in result.errors[0]
```

- No crash - system degrades gracefully
- Local state unchanged
- Warnings logged
- Next sync will retry

### Audit Trail Limits

Audit trail keeps last 1000 entries to avoid memory bloat:

```python
trail = reconciler.get_audit_trail()
assert len(trail) <= 1000
```

## Monitoring & Logs

### Key Log Messages

```
[STARTUP] Starting recovery process
[RECOVERY] Zombie position recovered: Ticket 123456, LONG 0.01L
[SYNC] Starting full synchronization
[DRIFT_FIX] Ticket 123456: volume mismatch corrected
[SYNC] State Reconciled: Local matches Remote (0.1ms)
```

### Checking Status

```python
status = reconciler.get_status()
print(f"Syncs performed: {status['sync_count']}")
print(f"Next sync due: {status['next_sync_due']}")
print(f"Audit entries: {status['audit_trail_entries']}")
```

## Testing

### Run All Tests

```bash
python3 scripts/test_reconciliation.py
```

### Run Gate 1 Audit

```bash
python3 scripts/audit_task_031.py
```

### Manual Testing

```python
from src.strategy.reconciler import StateReconciler
from src.strategy.portfolio import PortfolioManager
from unittest.mock import Mock

# Create mock gateway
gateway = Mock()
gateway.get_positions.return_value = {
    "status": "SUCCESS",
    "positions": [...]
}

pm = PortfolioManager(symbol="EURUSD")
reconciler = StateReconciler(pm, gateway)

# Test startup recovery
result = reconciler.startup_recovery()
assert result.recovered == 1
```

## Common Scenarios

### Scenario 1: Clean Startup

```
Python starts → Portfolio FLAT
↓
Query gateway → No open positions
↓
Result: ✅ No recovery needed, clean state
```

### Scenario 2: Crash Recovery

```
Python crashes with LONG 0.01L position open
↓
Python restarts → Portfolio FLAT (lost state)
↓
Query gateway → LONG 0.01L still open (Ticket 123456)
↓
Reconciler: Force-add position from gateway
↓
Result: Local state restored from gateway
```

### Scenario 3: External Modification

```
Python running, tracking LONG 0.01L
↓
User manually closes position in MT5 terminal
↓
Next sync (15 sec): Query gateway → No positions
↓
Reconciler: Force-close ghost position in local state
↓
Result: Local state matches remote
```

## Next Steps

1. **Run tests**: `python3 scripts/test_reconciliation.py`
2. **Run audit**: `python3 scripts/audit_task_031.py`
3. **Integrate**: Add reconciler to main paper trading loop
4. **Deploy**: Monitor for startup recovery and drift detection

## Troubleshooting

### "Gateway offline" errors

**Cause**: Windows gateway not responding to GET_POSITIONS

**Solution**:
```bash
# Check if gateway is listening
netstat -an | grep 5555

# Test connectivity
nc -zv 172.19.141.255 5555
```

### Large audit trail

**Cause**: Many state changes → audit trail growing

**Solution**:
```python
# Check size
trail = reconciler.get_audit_trail()
print(len(trail))  # Auto-pruned at 1000 entries
```

### Mismatch still detected

**Cause**: Sync interval too short, network lag

**Solution**:
```bash
# Increase sync interval
export SYNC_INTERVAL_SEC=30
```

---

**Last Updated**: 2026-01-05
**Status**: ✅ Ready for Production
**Maintainer**: MT5-CRS Development Team
