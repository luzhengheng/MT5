# TASK #030: Paper Trading System - Quick Start Guide

## Overview

The Portfolio Manager & Paper Trading Loop implements a complete trading cycle:

```
ZMQ Market Data Ticks
    ↓
StrategyEngine (Task #028)
    ↓ generates signals (1/0/-1)
    ↓
PortfolioManager (Task #030)
    ↓ checks risk (position conflicts)
    ↓
ExecutionGateway (Task #029)
    ↓ sends orders to Windows MT5
    ↓
Fill Response
    ↓
Position Update
```

## Prerequisites

Before starting the paper trading system, ensure:

1. **Market Data Publisher** running on `tcp://localhost:5556` (Task #025)
2. **Windows MT5 Gateway** running on `tcp://172.19.141.255:5555` (Task #029)
3. **XGBoost Model** trained and saved at `models/xgboost_price_predictor.json` (Task #027)
4. **Python Environment** with dependencies from `pyproject.toml`
5. **Configuration** properly set in `.env` file

## Quick Start (Three Options)

### Option 1: Run Unit Tests Only (No Gateway Required)

Best for validating Portfolio Manager logic without a running Windows gateway.

```bash
# Run all unit tests
python3 scripts/test_portfolio_logic.py

# Expected output:
# ✅ All tests passed!
# Passed: 11/11
# Failed: 0/11
```

**What gets tested**:
- Order creation and validation
- Risk checking (position conflicts)
- Fill processing
- Position state updates
- FIFO accounting
- Edge cases

**Time**: ~2 seconds

---

### Option 2: Run Paper Trading Loop (Gateway Required)

Start the complete paper trading system with live market data and execution.

```bash
# Set environment variables (optional - defaults in config.py)
export TRADING_SYMBOL="EURUSD"
export ZMQ_MARKET_DATA_URL="tcp://localhost:5556"
export ZMQ_EXECUTION_URL="tcp://172.19.141.255:5555"

# Run paper trading
python3 src/main_paper_trading.py

# Press Ctrl+C to stop
```

**What happens**:
1. Connects to market data publisher (ZMQ PUB)
2. Receives real-time market ticks
3. StrategyEngine processes ticks → generates signals
4. PortfolioManager checks risk → allows/blocks orders
5. ExecutionGateway sends orders to Windows MT5
6. Receives fill responses and updates positions
7. Logs all events to `paper_trading.log`

**Expected log output**:
```
[2026-01-05 15:00:00] [PaperTrading] [INFO] StrategyEngine initialized for EURUSD
[2026-01-05 15:00:00] [PaperTrading] [INFO] PortfolioManager initialized
[2026-01-05 15:00:00] [Gateway] [INFO] ✅ Connected to tcp://172.19.141.255:5555
[2026-01-05 15:00:00] [PaperTrading] [INFO] Starting Paper Trading Loop

[CYCLE 1] Signal=1, Confidence=0.65
[RISK] PASS: Position=FLAT, Signal=1 allowed
[ORDER] Created ORD_0_1704...: BUY 0.01L @ 1.0543
[SEND] Order ORD_0_1704...: BUY 0.01 @ 1.0543
[RECV] Response: {'status': 'FILLED', 'ticket': 123456, 'filled_price': 1.0543, ...}
[FILL] CONFIRMED ORD_0_1704...: Ticket=123456, Price=1.0543, Vol=0.01
[POSITION] OPENED: EURUSD LONG 0.01L @ 1.0543

[CYCLE 2] Signal=0, Confidence=0.55
[RISK] HOLD signal - no order sent

[CYCLE 3] Signal=-1, Confidence=0.68
[RISK] PASS: Signal=SELL(-1), Position=LONG(0.01)
[ORDER] Created ORD_1_1704...: SELL 0.01L @ 1.0550
[SEND] Order ORD_1_1704...: SELL 0.01 @ 1.0550
[RECV] Response: {'status': 'FILLED', 'ticket': 123457, 'filled_price': 1.0550, ...}
[FILL] CONFIRMED ORD_1_1704...: Ticket=123457, Price=1.0550, Vol=0.01
[POSITION] CLOSED: EURUSD via ORD_1_1704...

🛑 Shutdown requested
Paper Trading Summary
Cycles: 3, Signals: 2, Orders: 2, Fills: 2
```

**Time**: Runs indefinitely until Ctrl+C

**Troubleshooting**:
- If gateway connection fails: "⚠️  Gateway connection failed - will retry per order"
- If ZMQ market data unavailable: Engine timeout (no ticks processed)
- Check `paper_trading.log` for detailed error messages

---

### Option 3: Test Portfolio Logic with Mock Fills

Test the integration without real market data or gateway.

```bash
# Create a test script
cat > test_manual_trading.py << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.strategy.portfolio import PortfolioManager, create_fill_response

# Create portfolio manager
pm = PortfolioManager(symbol="EURUSD")
print(f"Position: {pm.get_position_summary()}")

# BUY signal
order1 = pm.create_order(signal=1, price=1.0543, volume=0.01)
print(f"BUY order created: {order1.order_id}")

# Simulate fill
pm.on_fill(create_fill_response(order1.order_id, 123456, 1.0543, 0.01))
print(f"Position after fill: {pm.get_position_summary()}")

# Try BUY again (should be blocked)
order2 = pm.create_order(signal=1, price=1.0550, volume=0.01)
print(f"Second BUY result: {order2} (None = blocked by risk check)")

# SELL to close
order3 = pm.create_order(signal=-1, price=1.0550, volume=0.01)
print(f"SELL order created: {order3.order_id}")

# Fill SELL
pm.on_fill(create_fill_response(order3.order_id, 123457, 1.0550, 0.01))
print(f"Position after SELL: {pm.get_position_summary()}")

# Print history
print(f"\nOrder History:")
for order in pm.get_order_history():
    print(f"  {order['order_id']}: {order['action']} {order['volume']}L @ {order['fill_price']}")
EOF

python3 test_manual_trading.py
```

**Expected output**:
```
Position: {'status': 'FLAT', 'symbol': 'EURUSD'}
BUY order created: ORD_0_1704...
Position after fill: {'status': 'OPEN', 'symbol': 'EURUSD', 'direction': 'LONG', 'net_volume': 0.01, 'avg_entry_price': 1.0543, ...}
Second BUY result: None (None = blocked by risk check)
SELL order created: ORD_1_1704...
Position after SELL: {'status': 'FLAT', 'symbol': 'EURUSD'}

Order History:
  ORD_0_1704...: BUY 0.01L @ 1.0543
  ORD_1_1704...: SELL 0.01L @ 1.0550
```

**Time**: ~1 second

---

## Configuration

### Environment Variables

```bash
# Trading symbol (default: EURUSD)
export TRADING_SYMBOL="EURUSD"

# Market data ZMQ URL (default: tcp://localhost:5556)
export ZMQ_MARKET_DATA_URL="tcp://localhost:5556"

# Order execution ZMQ URL (default: tcp://172.19.141.255:5555)
export ZMQ_EXECUTION_URL="tcp://172.19.141.255:5555"

# Windows gateway host (default: 172.19.141.255)
export GTW_HOST="172.19.141.255"

# Windows gateway port (default: 5555)
export GTW_PORT=5555

# Gateway timeout in milliseconds (default: 2000)
export GTW_TIMEOUT_MS=2000

# Order volume in lots (default: 0.01)
export DEFAULT_VOLUME=0.01
```

### Via .env File

Create `.env` in project root:

```env
TRADING_SYMBOL=EURUSD
ZMQ_MARKET_DATA_URL=tcp://localhost:5556
ZMQ_EXECUTION_URL=tcp://172.19.141.255:5555
GTW_HOST=172.19.141.255
GTW_PORT=5555
GTW_TIMEOUT_MS=2000
DEFAULT_VOLUME=0.01
```

### Python Configuration

```python
from src.strategy.portfolio import PortfolioManager

# Create manager for specific symbol
pm = PortfolioManager(symbol="GBPUSD")

# Create order
order = pm.create_order(signal=1, price=1.2543, volume=0.1)

# Simulate fill
pm.on_fill({
    'order_id': order.order_id,
    'ticket': 123456,
    'filled_price': 1.2543,
    'filled_volume': 0.1,
    'status': 'FILLED',
    'timestamp': time.time()
})

# Check position
print(pm.get_position_summary())
```

---

## Portfolio Manager API

### Core Methods

#### `check_risk(signal: int) -> bool`

Check if signal is allowed based on current position.

```python
pm = PortfolioManager(symbol="EURUSD")

# Check BUY signal (returns True if allowed)
if pm.check_risk(1):  # BUY
    order = pm.create_order(1, price=1.0543)
```

**Signal values**:
- `1`: BUY signal
- `-1`: SELL signal
- `0`: HOLD signal (always rejected)

---

#### `create_order(signal: int, price: float, volume: float = 0.01) -> Optional[Order]`

Create an order if risk check passes.

```python
order = pm.create_order(signal=1, price=1.0543, volume=0.01)

if order:
    print(f"Order created: {order.order_id}")
    # Send to gateway
else:
    print("Order blocked by risk check")
```

---

#### `on_fill(fill_response: Dict) -> bool`

Process fill response from gateway.

```python
fill_response = {
    'order_id': order.order_id,
    'ticket': 123456,
    'filled_price': 1.0543,
    'filled_volume': 0.01,
    'status': 'FILLED',  # or 'REJECTED'
    'timestamp': time.time()
}

success = pm.on_fill(fill_response)
if success:
    print(f"Fill processed: {pm.get_position_summary()}")
```

---

#### `get_position_summary() -> Dict`

Get current position state.

```python
summary = pm.get_position_summary()

# If FLAT:
# {'status': 'FLAT', 'symbol': 'EURUSD'}

# If OPEN:
# {
#     'status': 'OPEN',
#     'symbol': 'EURUSD',
#     'direction': 'LONG' | 'SHORT',
#     'net_volume': float,           # +0.01 for LONG, -0.01 for SHORT
#     'avg_entry_price': float,
#     'current_price': float,
#     'unrealized_pnl': float,
#     'orders_count': int
# }
```

---

#### `get_order_history() -> List[Dict]`

Get all orders (filled, pending, rejected).

```python
history = pm.get_order_history()
for order in history:
    print(f"{order['order_id']}: {order['action']} {order['status']}")
```

---

## Monitoring & Logs

### Main Log Files

```bash
# Paper trading session log
tail -f paper_trading.log

# Full test output
cat docs/archive/tasks/TASK_030_PAPER_TRADING/VERIFY_LOG.log
```

### Key Log Messages

```
[RISK] PASS: Signal allowed
[RISK] BLOCKED: Signal rejected due to position conflict
[ORDER] Created: New order
[SEND] Order: Sending to gateway
[RECV] Response: Gateway response received
[FILL] CONFIRMED: Order filled
[POSITION] OPENED: New position created
[POSITION] UPDATED: Position modified
[POSITION] CLOSED: Position liquidated
```

### Interpreting Logs

```
[RISK] BLOCKED: Signal=BUY(1) but position is LONG(0.01)
→ Strict single-position model prevents buying while already long

[FILL] REJECTED: ORD_0 - Insufficient margin
→ Order rejected by gateway (e.g., insufficient margin)

[POSITION] UPDATED: EURUSD LONG 0.02L @ avg 1.0545
→ Position increased from 0.01L to 0.02L at average price 1.0545
```

---

## Common Scenarios

### Scenario 1: Simple Buy-Sell Cycle

```bash
# Market tick: EURUSD @ 1.0543
# Signal: BUY (confidence 0.65)
# Expected: Position opens LONG 0.01L

# Market tick: EURUSD @ 1.0545
# Signal: HOLD
# Expected: No order

# Market tick: EURUSD @ 1.0550
# Signal: SELL (confidence 0.68)
# Expected: Position closes, trade closed

# Result: +7 pips profit
```

### Scenario 2: Signal Blocked (Conflict)

```bash
# Market tick: EURUSD @ 1.0543
# Signal: BUY
# Expected: Position opens LONG

# Market tick: EURUSD @ 1.0544
# Signal: BUY (again)
# Expected: BLOCKED - "Signal=BUY(1) but position is LONG(0.01)"

# Position remains LONG until opposite signal (SELL)
```

### Scenario 3: Rejection from Gateway

```bash
# Market tick: EURUSD @ 1.0543
# Signal: BUY
# Order sent to gateway

# Gateway response: REJECTED - "Insufficient margin"
# Expected: Order marked REJECTED, no position opens
```

---

## Testing Checklist

- [ ] Unit tests pass: `python3 scripts/test_portfolio_logic.py`
- [ ] Portfolio class imports without errors
- [ ] Environment variables configured
- [ ] Gateway connection works (or mock fills used)
- [ ] Logs are readable and informative
- [ ] Position summary format correct
- [ ] Order history trackable
- [ ] Risk checks block same-direction signals
- [ ] Opposite-direction signals allowed
- [ ] HOLD signals always rejected
- [ ] Position closes on net zero volume

---

## Troubleshooting

### "Gateway connection failed"

**Cause**: Windows MT5 gateway not running on port 5555

**Solution**:
```bash
# Check if gateway is listening
netstat -an | grep 5555

# Or use nc to test
nc -zv 172.19.141.255 5555

# If not running, start the Windows gateway service
```

### "Insufficient data: only X rows. Need at least 30"

**Cause**: StrategyEngine needs minimum 30 ticks in buffer before inference

**Solution**:
- Wait longer for market data
- Or reduce `min_buffer_size` in StrategyEngine

### "zmq.Again - No data from publisher"

**Cause**: Market data publisher not running or not pushing data

**Solution**:
```bash
# Check if market data publisher is running
# Should be publishing on tcp://localhost:5556

# Test ZMQ connection
python3 -c "import zmq; print(zmq.zmq_version())"
```

### Orders not being filled

**Cause**: Various (gateway offline, timeout, rejection)

**Solution**:
1. Check logs: `tail -100 paper_trading.log | grep FILL`
2. Verify gateway is responding
3. Check timeout setting (GTW_TIMEOUT_MS)
4. Verify order format is correct

---

## Next Steps

1. **Run unit tests**: `python3 scripts/test_portfolio_logic.py`
2. **Review logs**: Check `VERIFY_LOG.log`
3. **Gate 2 audit**: (To be created)
4. **AI review**: `python3 gemini_review_bridge.py`
5. **Production deployment**: After Gate 2 & AI review pass

---

## Further Reading

- **Portfolio Manager**: `src/strategy/portfolio.py`
- **Paper Trading Loop**: `src/main_paper_trading.py`
- **Unit Tests**: `scripts/test_portfolio_logic.py`
- **Verification Log**: `docs/archive/tasks/TASK_030_PAPER_TRADING/VERIFY_LOG.log`
- **Completion Report**: `docs/archive/tasks/TASK_030_PAPER_TRADING/COMPLETION_REPORT.md`

---

**Last Updated**: 2026-01-05
**Status**: ✅ Ready for Gate 2 Audit
**Maintainer**: MT5-CRS Development Team
