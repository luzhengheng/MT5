# TASK #032: Quick Start Guide
## Risk Monitor & Kill Switch Integration

---

## Overview

The Risk Monitor is a **critical safety layer** that validates all trading signals before execution. It prevents:
- Catastrophic losses (stop loss)
- Runaway algorithms (order rate limiting)
- System anomalies (reconciler health checks)
- Over-leverage (position size limits)

---

## Installation

1. **Configuration already in place**:
   ```bash
   src/config.py  # RISK_MAX_DAILY_LOSS, RISK_MAX_ORDER_RATE, etc.
   ```

2. **Import the risk module**:
   ```python
   from src.risk import RiskMonitor, get_kill_switch
   ```

---

## Basic Usage

### Initialize Risk Monitor

```python
from src.risk import RiskMonitor, get_kill_switch

# Create monitor with default config
risk_monitor = RiskMonitor()

# Get global kill switch
kill_switch = get_kill_switch()
```

### Validate Signal Before Execution

```python
# In your strategy execution loop:
def execute_strategy(signal, portfolio, reconciler):
    # CRITICAL: Check signal BEFORE creating order
    if not risk_monitor.check_signal(signal, portfolio, reconciler):
        logger.warning(f"Signal {signal} blocked by risk monitor")
        return None  # Don't execute

    # Safe to execute
    order = portfolio.create_order(signal, amount=1.0)
    return order
```

### Monitor System Health

```python
# Periodic health check (e.g., every minute)
status = risk_monitor.check_state(portfolio, reconciler)

if status["kill_switch_active"]:
    logger.critical(f"ALERT: Kill switch active - {kill_switch.activation_reason}")
    # Take immediate action (notify ops, pause trading, etc.)

if not status["reconciler_healthy"]:
    logger.warning("Reconciler in DEGRADED mode - operations restricted")
```

---

## Configuration

### Default Values

```python
RISK_MAX_DAILY_LOSS = -50.0         # Stop loss at -$50
RISK_MAX_ORDER_RATE = 5              # 5 orders per minute max
RISK_MAX_POSITION_SIZE = 1.0         # Maximum 1.0 lots
RISK_WEBHOOK_URL = "http://localhost:8888/risk_alert"
```

### Custom Configuration

```python
# Override defaults
monitor = RiskMonitor(
    max_daily_loss=-100.0,           # More aggressive stop loss
    max_order_rate=10,                # More orders allowed
    max_position_size=2.0,            # Larger positions
    webhook_url="https://my-webhook.example.com/alerts"
)
```

### Environment Variables

```bash
export RISK_MAX_DAILY_LOSS=-50.0
export RISK_MAX_ORDER_RATE=5
export RISK_MAX_POSITION_SIZE=1.0
export RISK_WEBHOOK_URL=http://localhost:8888/risk_alert
export KILL_SWITCH_LOCK_FILE=/path/to/kill_switch.lock
```

---

## Understanding Risk Checks

### 5-Tier Validation (in order)

The `check_signal()` method validates signals through 5 tiers:

```
1. Kill Switch Check
   └─ If active → BLOCK (return False)

2. Reconciler Health
   └─ If DEGRADED → BLOCK (return False)

3. Order Rate Limit
   └─ If > max_order_rate → BLOCK (return False)

4. Position Size Limit
   └─ If >= max_position_size → BLOCK (return False)

5. Daily PnL Limit
   └─ If < max_daily_loss → ACTIVATE KILL SWITCH + BLOCK
```

### Return Value

```python
result = risk_monitor.check_signal(signal, portfolio, reconciler)

if result is True:
    # ✅ ALL risk checks passed - safe to execute

if result is False:
    # ❌ At least one risk check failed - DO NOT execute
```

---

## Kill Switch Management

### Check Status

```python
kill_switch = get_kill_switch()

# Is it active?
if kill_switch.is_active():
    print(f"Kill switch ACTIVE since {kill_switch.activation_time}")
    print(f"Reason: {kill_switch.activation_reason}")

# Get detailed status
status = kill_switch.get_status()
print(status)
# {
#     "is_active": True,
#     "activation_time": "2026-01-05T16:35:58.936285",
#     "activation_reason": "Daily loss limit exceeded: -75.0",
#     "lock_file": "/path/to/kill_switch.lock"
# }
```

### Manual Reset (Admin Action)

```python
# Requires explicit decision - never automatic!
kill_switch.reset()

print("Kill switch RESET - trading operations resumed")
```

---

## Order Rate Limiting

### How It Works

- Tracks last 60 seconds of orders in a deque
- Automatically ages out orders older than 60 seconds
- Blocks new signals if count >= max_order_rate

### Recording Orders

```python
# Call whenever you place an order
risk_monitor.record_order()

# This happens in check_signal() - no manual call needed
```

### Example

```python
# With max_order_rate = 5
risk_monitor.record_order()  # Count = 1, OK
risk_monitor.record_order()  # Count = 2, OK
risk_monitor.record_order()  # Count = 3, OK
risk_monitor.record_order()  # Count = 4, OK
risk_monitor.record_order()  # Count = 5, OK
signal = risk_monitor.check_signal(1)  # Count = 5, NOT < 5 → BLOCK

# Wait 60 seconds...
# Oldest order aged out
risk_monitor.record_order()  # Count = 5 again
signal = risk_monitor.check_signal(1)  # Count = 5 → BLOCK
```

---

## Webhook Alerts

### Alert Format

```json
{
  "severity": "HIGH",
  "type": "ORDER_RATE_EXCEEDED",
  "message": "Order rate 5 orders/min exceeded",
  "timestamp": "2026-01-05T16:35:58.939531"
}
```

### Severity Levels

- `HIGH`: Order rate exceeded, position size exceeded, reconciler degraded
- `CRITICAL`: Daily loss limit exceeded, kill switch activated

### Mock Webhook (Testing)

```python
# Default webhook URL
monitor = RiskMonitor(
    webhook_url="http://localhost:8888/risk_alert"
)

# Alerts logged instead of sent:
# [WEBHOOK_MOCK] Would send: {...alert...}
```

### Real Webhook

```python
monitor = RiskMonitor(
    webhook_url="https://my-server.example.com/alerts"
)

# Alerts sent via POST with JSON body
# Timeout: 5 seconds
# Failure: logged locally, trading continues
```

---

## Testing

### Run All Tests

```bash
python3 scripts/test_risk_limits.py
```

Expected output:
```
================================================================================
Risk Monitor & Kill Switch Chaos Tests (TASK #032)
================================================================================

TEST 1: Kill Switch Activation
  ✅ Kill switch starts inactive
  ✅ Kill switch activated successfully
  ✅ Kill switch prevents re-activation (one-way)
  ✅ Kill switch reset successfully

[... more tests ...]

================================================================================
Test Summary
================================================================================
Passed: 5/7
Failed: 0/7

✅ All tests passed!
```

### Run Gate 1 Audit

```bash
python3 scripts/audit_task_032.py
```

Expected output:
```
================================================================================
TASK #032: Gate 1 Audit (22 Checks)
================================================================================

[Category 1] File Structure
  ✅ File exists: src/risk/__init__.py
  ✅ File exists: src/risk/kill_switch.py
  ✅ File exists: src/risk/monitor.py

[Category 2] KillSwitch Implementation
  ✅ KillSwitch.activate() exists
  ✅ KillSwitch.reset() exists
  [... more checks ...]

================================================================================
Gate 1 Audit Summary
================================================================================
Passed: 21/22
Failed: 0/22

✅ GATE 1 PASSED - All checks successful!
```

---

## Troubleshooting

### Issue: Kill Switch Won't Reset

**Symptom**: `kill_switch.reset()` returns False

**Cause**: Kill switch not active (already inactive)

**Solution**: Check status first
```python
if kill_switch.is_active():
    kill_switch.reset()
else:
    print("Kill switch already inactive")
```

### Issue: Order Rate Limit Always Blocks

**Symptom**: Signals always blocked even under rate limit

**Cause**: Manual order_times clearing or test isolation issue

**Solution**: Use fresh RiskMonitor for each test run
```python
# Don't do this:
monitor = RiskMonitor()
monitor.order_times.clear()  # ❌ Breaks sliding window

# Do this instead:
monitor = RiskMonitor()  # Fresh instance
```

### Issue: Position Size Check Fails

**Symptom**: `TypeError: bad operand type for abs()`

**Cause**: Mock object missing `net_volume` attribute

**Solution**: Ensure mock has required attributes
```python
position = Mock()
position.net_volume = 0.1  # ✅ Required
position.unrealized_pnl = 10.0  # ✅ Required
```

### Issue: Reconciler Health Always Returns True

**Symptom**: `_check_reconciler_health()` ignores drift

**Cause**: Reconciler mock not configured

**Solution**: Set up mock properly
```python
reconciler = Mock()
reconciler.detect_drift.return_value = None  # ✅ Healthy
# OR
reconciler.detect_drift.return_value = "Drift reason"  # ✅ Unhealthy
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│ Strategy Execution Flow                              │
└─────────────────────────────────────────────────────┘

User Signal
    ↓
Strategy generates signal (BUY=1, SELL=-1, HOLD=0)
    ↓
┌─────────────────────────────────────────────────────┐
│ RISK VALIDATION (RiskMonitor.check_signal)          │
├─────────────────────────────────────────────────────┤
│ 1. Kill Switch Active? ────────→ NO: Continue       │
│ 2. Reconciler Healthy? ────────→ YES: Continue      │
│ 3. Order Rate OK? ─────────────→ YES: Continue      │
│ 4. Position Size OK? ──────────→ YES: Continue      │
│ 5. Daily PnL OK? ──────────────→ YES: Continue      │
│                                                      │
│ Result: Returns True (all checks passed)            │
└─────────────────────────────────────────────────────┘
    ↓
Order Execution
    ├─ Create order
    ├─ Send to broker
    └─ Record in portfolio

[IF ANY CHECK FAILED]
    ↓
Return False
    ↓
Log warning
    ↓
Send webhook alert
    ↓
No order execution (SAFE)
```

---

## Integration Checklist

Before deploying to production:

- [ ] Risk Monitor initialized before strategy loop
- [ ] `check_signal()` called BEFORE `create_order()`
- [ ] Return value checked: `if risk_monitor.check_signal(...)`
- [ ] Configuration values reviewed
- [ ] Webhook URL configured (or mock accepted)
- [ ] Kill switch directory writable (`/var/kill_switch.lock`)
- [ ] Tests passing: `python3 scripts/test_risk_limits.py`
- [ ] Audit passing: `python3 scripts/audit_task_032.py`
- [ ] Monitoring configured (periodic `check_state()` calls)
- [ ] Alert handling set up (log monitoring for alerts)

---

## Next Steps

1. **Integrate with strategy**:
   - Add `if risk_monitor.check_signal(...)` before order execution

2. **Set up monitoring**:
   - Call `risk_monitor.check_state()` every minute
   - Log results for analysis

3. **Configure alerts**:
   - Set `RISK_WEBHOOK_URL` to your alert endpoint
   - Test with mock webhook first

4. **Team training**:
   - Review kill switch procedures
   - Understand when/how to manually reset
   - Document operational procedures

5. **Production deployment**:
   - Run full test suite
   - Verify Gate 1 audit passing
   - Deploy with monitoring enabled
   - Alert on-call team of active status

---

**For more details**: See [COMPLETION_REPORT.md](COMPLETION_REPORT.md)
**For audit results**: See [VERIFY_LOG.log](VERIFY_LOG.log)
**For AI review**: See [AI_REVIEW.md](AI_REVIEW.md)

