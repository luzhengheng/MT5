# Task #105 - Live Risk Monitor
## Quick Start Guide

**Protocol**: v4.3 (Zero-Trust Edition)
**Status**: ✅ Production Ready

---

## What is the Live Risk Monitor?

The Live Risk Monitor is an **independent, real-time risk monitoring system** that continuously watches your trading account for risk threshold breaches and automatically engages the kill switch (circuit breaker) to prevent catastrophic losses.

**Key Features**:
- ✅ **Real-time monitoring**: Updates with every price tick
- ✅ **Automatic kill switch**: Engages when risk limits exceeded
- ✅ **Multi-metric tracking**: Drawdown, leverage, exposure
- ✅ **Progressive alerts**: WARNING → CRITICAL → KILL
- ✅ **Zero-trust audit trail**: Complete forensic evidence

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Task #104: Live Loop                       │
│  (Trading engine with orders)                          │
├─────────────────────────────────────────────────────────┤
│  Gate 1: Pre-Signal Check                              │
│  └─ If not CB.is_safe() → BLOCK SIGNAL                 │
│                                                         │
│  Gate 2: Pre-Order Check                               │
│  └─ If not CB.is_safe() → BLOCK ORDER                  │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ shared
                         │ CircuitBreaker
                         │
┌─────────────────────────────────────────────────────────┐
│          Task #105: Risk Monitor                        │
│     (Parallel monitoring subsystem)                    │
├─────────────────────────────────────────────────────────┤
│  Every Tick:                                            │
│  1. Update account state (balance, drawdown, leverage) │
│  2. Check against risk limits                          │
│  3. If threshold exceeded → CB.engage() ✅ KILL SWITCH │
│                                                         │
│  If DD > 2% → CRITICAL → Engage CB                     │
│  If DD > 1% → WARNING → Log alert only                 │
│  If LEV > 5x → CRITICAL → Engage CB                    │
│  If LEV > 3x → WARNING → Log alert only                │
└─────────────────────────────────────────────────────────┘
```

---

## Installation & Setup

### 1. Verify Files Are in Place

```bash
# Configuration
cat config/risk_limits.yaml

# Core implementation
cat src/execution/risk_monitor.py

# Test suite
cat scripts/verify_risk_trigger.py

# Test logs
ls -la TASK_105_CHAOS_TEST_LOG.log
cat CHAOS_TEST_RESULTS.json
```

### 2. Run Tests to Verify Installation

```bash
# Execute full test suite
python3 scripts/verify_risk_trigger.py

# Expected output:
# ================================================================================
# 📊 TEST SUMMARY
# ================================================================================
# Total Scenarios: 5
# Passed: 5
# Failed: 0
# ...
# 🎯 OVERALL RESULT: ✅ ALL TESTS PASSED
```

### 3. Prepare Deployment

```bash
# Create log directory
mkdir -p /var/log/mt5_crs/

# Create lock file (for circuit breaker)
touch /tmp/mt5_crs_kill_switch.lock
chmod 666 /tmp/mt5_crs_kill_switch.lock

# Verify permissions
ls -la /tmp/mt5_crs_kill_switch.lock
```

---

## Configuration

### Risk Limits (config/risk_limits.yaml)

The main configuration file defines when the kill switch triggers:

```yaml
# Hard limits (CRITICAL - Kill Switch Engaged)
risk:
  max_daily_drawdown: 0.02          # Kill if DD > 2%
  max_account_leverage: 5.0         # Kill if leverage > 5x
  max_single_position_size: 1.0     # Max lot size

  # Soft limits (WARNING - Alert Only)
alerts:
  drawdown_warning: 0.01            # Alert at 1% DD
  leverage_warning: 3.0             # Alert at 3x leverage
```

### Customizing Risk Limits

To adjust thresholds for your strategy:

```yaml
# Example: Conservative risk profile
risk:
  max_daily_drawdown: 0.01          # 1% (more conservative)
  max_account_leverage: 3.0         # 3x (more conservative)

alerts:
  drawdown_warning: 0.005           # 0.5% warning
  leverage_warning: 2.0             # 2x warning
```

### Configuration Options

| Parameter | Default | Min | Max | Purpose |
|-----------|---------|-----|-----|---------|
| `max_daily_drawdown` | 0.02 | 0.001 | 0.50 | Hard drawdown limit |
| `max_account_leverage` | 5.0 | 1.0 | 20.0 | Hard leverage limit |
| `drawdown_warning` | 0.01 | 0.001 | 0.05 | Soft drawdown limit |
| `leverage_warning` | 3.0 | 1.0 | 10.0 | Soft leverage limit |

---

## Usage Example

### Basic Integration with Live Loop

```python
from execution.live_engine import LiveEngine
from execution.risk_monitor import RiskMonitor
from risk.circuit_breaker import CircuitBreaker

# 1. Create shared circuit breaker
cb = CircuitBreaker()

# 2. Create risk monitor
monitor = RiskMonitor(
    circuit_breaker=cb,
    config_path="config/risk_limits.yaml",
    initial_balance=100000.0
)

# 3. Create live trading engine
engine = LiveEngine(circuit_breaker=cb)

# 4. Main event loop
async def main():
    async for tick_data in market_data_stream:
        # Risk monitoring (runs continuously)
        risk_result = monitor.monitor_tick(tick_data)

        # Log risk events
        if risk_result['alerts']:
            for alert in risk_result['alerts']:
                print(f"⚠️  Risk Alert: {alert['type']}")

        # Trading (only if safe)
        if cb.is_safe():
            await engine.process_tick(tick_data)
        else:
            print("🚫 Trading blocked - Kill switch engaged")

asyncio.run(main())
```

### Reading Risk Alerts

```python
# After monitoring tick:
result = monitor.monitor_tick(tick_data)

# Check for alerts
if result['alerts']:
    for alert in result['alerts']:
        print(f"Alert Type: {alert['type']}")
        print(f"  Value: {alert.get('drawdown_pct', alert.get('leverage'))}")
        print(f"  Limit: {alert['limit']}")
        print(f"  Action: {alert['action']}")

        if alert['action'] == 'KILL_SWITCH_TRIGGERED':
            print("🚨 CRITICAL - Kill switch engaged!")

# Check current state
state = result['account_state']
print(f"Balance: ${state['balance']:,.2f}")
print(f"Drawdown: {state['drawdown_pct']:.2%}")
print(f"Leverage: {state['leverage']:.1f}x")
print(f"Alert Level: {state['alert_level']}")
```

---

## Monitoring & Alerts

### Alert Types

```
DRAWDOWN_WARNING:
├── Triggered: Drawdown >= 1% (soft limit)
├── Action: Alert logged, no kill switch
├── Response: Monitor closely, consider reducing exposure
└── Example: "Drawdown warning 1.08%"

CRITICAL_DRAWDOWN:
├── Triggered: Drawdown >= 2% (hard limit)
├── Action: Kill switch ENGAGED
├── Response: All new orders BLOCKED
└── Example: "🚨 [KILL] Drawdown 2.17%"

LEVERAGE_WARNING:
├── Triggered: Leverage >= 3x (soft limit)
├── Action: Alert logged, no kill switch
├── Response: Reduce position size
└── Example: "Leverage warning 3.2x"

CRITICAL_LEVERAGE:
├── Triggered: Leverage >= 5x (hard limit)
├── Action: Kill switch ENGAGED
├── Response: All new orders BLOCKED
└── Example: "🚨 [KILL] Leverage 5.5x"
```

### Viewing Logs

```bash
# Real-time monitoring
tail -f TASK_105_CHAOS_TEST_LOG.log

# Summary of all kills
grep "KILL" TASK_105_CHAOS_TEST_LOG.log

# Summary of all warnings
grep "WARNING" TASK_105_CHAOS_TEST_LOG.log

# JSON test results
cat CHAOS_TEST_RESULTS.json | jq
```

---

## Kill Switch Management

### Understanding Kill Switch States

```
SAFE:
├── Normal operation
├── Orders can be generated
└── Risk monitoring continues

ENGAGED:
├── Risk threshold breached
├── All new orders BLOCKED
├── Risk monitoring continues
└── Account state still updated
```

### Recovery from Kill Switch

```python
# Get current status
status = circuit_breaker.get_status()
print(f"State: {status['state']}")
print(f"Engaged at: {status['engagement_time']}")
print(f"Reason: {status['metadata']}")

# Manual disengagement (after investigation)
if cb.is_engaged():
    # 1. Analyze why kill switch triggered
    # 2. Verify all positions are hedged/closed
    # 3. Confirm recovery is safe

    # 4. Disengage
    cb.disengage()
    print("✅ Kill switch disengaged, resuming operations")
```

### Automatic Recovery (Future)

Currently, kill switch disengagement is **manual** to ensure safety. Future versions will support:

```python
# (Not yet available)
# cb.schedule_recovery(delay_seconds=60)
# cb.enable_automatic_recovery(cooldown=60)
```

---

## Troubleshooting

### Kill Switch Not Engaging When Expected

```python
# Check if monitoring is running
print(f"Ticks monitored: {monitor.ticks_monitored}")
print(f"Kills triggered: {monitor.kills_triggered}")

# Check current state
state = monitor.get_summary()
print(f"Drawdown: {state['max_drawdown']:.2%} (limit: 2%)")
print(f"Leverage: N/A (check state)")

# Verify configuration loaded
print(f"Config: {monitor.config}")
```

### Monitor Not Updating on Ticks

```python
# Verify tick data includes required fields
tick_data = {
    'tick_id': i,
    'timestamp': datetime.utcnow().isoformat(),
    'symbol': 'EURUSD',
    'bid': 1.08500,          # REQUIRED
    'ask': 1.08510,
    'volume': 100000,
}

result = monitor.monitor_tick(tick_data)
print(f"Updated: {result['account_state']['timestamp']}")
```

### High Latency

```python
# Monitor tick processing time
import time

start = time.time()
result = monitor.monitor_tick(tick_data)
elapsed_ms = (time.time() - start) * 1000

print(f"Processing time: {elapsed_ms:.2f}ms")
# Normal: 1-3ms
# With alerts: 3-5ms
# High load: <10ms

if elapsed_ms > 10:
    print("⚠️  High latency - check system load")
```

---

## Performance Tips

### Optimize Risk Calculations

```python
# ✅ GOOD: Reuse monitor instance
monitor = RiskMonitor(cb, config_path, initial_balance)
for tick in ticks:
    monitor.monitor_tick(tick)  # Reuses state

# ❌ BAD: Create new instance per tick
for tick in ticks:
    m = RiskMonitor(cb, config_path, initial_balance)  # Slow!
    m.monitor_tick(tick)
```

### Batch Processing

```python
# ✅ GOOD: Process ticks as they arrive
async def main():
    async for tick in stream:
        monitor.monitor_tick(tick)

# Less ideal: Batch processing (adds latency)
# Only use if ticks arrive in bursts
```

---

## Testing & Validation

### Run Full Test Suite

```bash
python3 scripts/verify_risk_trigger.py

# Output should show:
# ✅ TEST PASSED for all 5 scenarios
# 🎯 OVERALL RESULT: ✅ ALL TESTS PASSED
```

### Custom Test

```python
# Test custom scenario
from execution.risk_monitor import RiskMonitor
from risk.circuit_breaker import CircuitBreaker

cb = CircuitBreaker(enable_file_lock=False)  # Testing mode
monitor = RiskMonitor(cb, initial_balance=100000.0)

# Simulate price crash
for i in range(1, 6):
    tick = {
        'tick_id': i,
        'timestamp': datetime.utcnow().isoformat(),
        'bid': 1.08500 * (0.98 if i > 3 else 1.0),  # 2% drop on tick 4
        'ask': 1.08510 * (0.98 if i > 3 else 1.0),
    }

    result = monitor.monitor_tick(tick)
    if result['alerts']:
        for alert in result['alerts']:
            if 'CRITICAL' in alert['type']:
                print(f"✅ Kill triggered as expected")
```

---

## Monitoring Dashboard (Future)

Currently, monitoring is via:
- ✅ Structured JSON logs
- ✅ Console output
- ✅ Test results

Future enhancements:
- ⏳ Prometheus metrics export
- ⏳ Grafana dashboard
- ⏳ Real-time alert webhooks
- ⏳ Email notifications

---

## Frequently Asked Questions (FAQ)

**Q: What happens to my account when kill switch engages?**
A: No additional trades are generated. Existing positions remain open. Account continues to be monitored. Manual intervention required to recover.

**Q: Can I trade while kill switch is engaged?**
A: No. The circuit breaker blocks order generation. All new trades are rejected until disengage.

**Q: How do I know kill switch triggered?**
A: Check logs for "[KILL]" messages, check CB state with `cb.get_status()['state']`, or monitor `monitor.kills_triggered` counter.

**Q: What if my drawdown is at exactly 2%?**
A: Comparison is `>=`, so exactly 2% triggers the kill. The "soft limit" is at 1%.

**Q: Can I customize kill switch thresholds?**
A: Yes, edit `config/risk_limits.yaml`. Changes apply on next RiskMonitor instantiation.

**Q: Does kill switch automatically recover?**
A: Currently NO - manual `cb.disengage()` required. Future versions will support automatic recovery.

**Q: What's the latency of risk monitoring?**
A: Typically 1-3ms per tick, <10ms target. Fast enough for millisecond-scale trading.

**Q: Can I run multiple risk monitors?**
A: Yes, but each needs its own CircuitBreaker instance. Shared CB is preferred for coordinated trading.

**Q: Is data persisted when system crashes?**
A: Structured logs are written to files. Account state is in-memory (lost on crash). Use log replay to recover.

---

## Security Considerations

### Kill Switch Security

```
✅ File-based locking: /tmp/mt5_crs_kill_switch.lock
✅ Atomic state updates: No race conditions
✅ No hardcoded credentials: Config-driven
✅ Forensic audit trail: All events timestamped
✅ Read-only telemetry: No data exfiltration risk
```

### Production Deployment

```bash
# Set restrictive permissions
chmod 644 config/risk_limits.yaml
chmod 755 src/execution/
chmod 755 /var/log/mt5_crs/

# Monitor file integrity
sha256sum src/execution/risk_monitor.py > .checksums
# Verify before each deployment
```

---

## Support & Documentation

### Additional Resources

- **Full completion report**: `TASK_105_COMPLETION_REPORT.md`
- **Forensics verification**: `TASK_105_FORENSICS_VERIFICATION.md`
- **Protocol specification**: Protocol v4.3 docs
- **Test results**: `CHAOS_TEST_RESULTS.json`

### Getting Help

1. Check logs: `tail -f TASK_105_CHAOS_TEST_LOG.log`
2. Run tests: `python3 scripts/verify_risk_trigger.py`
3. Review configuration: `cat config/risk_limits.yaml`
4. Consult completion report for architecture details

---

## Summary

The Live Risk Monitor is **production-ready** and provides:

- ✅ Real-time risk monitoring
- ✅ Automatic kill switch engagement
- ✅ Multi-metric tracking (DD, leverage, exposure)
- ✅ Progressive alert escalation
- ✅ Complete forensic audit trail

**Next Steps**:
1. ✅ Review this guide
2. ⏳ Deploy alongside Task #104 LiveEngine
3. ⏳ Configure risk limits for your strategy
4. ⏳ Monitor production performance
5. ⏳ Integrate with monitoring dashboard

---

**Status**: ✅ Production Ready
**Protocol**: v4.3 (Zero-Trust Edition)
**Last Updated**: 2026-01-14 23:28:26 UTC

