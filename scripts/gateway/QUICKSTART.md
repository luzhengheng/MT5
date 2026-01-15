# MT5 ZMQ Server - Quick Start Guide

**Task #106**: MT5 Live Bridge - Windows Gateway
**Protocol**: v4.3 (Zero-Trust Edition)

---

## 5-Minute Setup (Windows)

### Step 1: Install Dependencies

```bash
pip install pyzmq python-dotenv pyyaml MetaTrader5
```

### Step 2: Configure MT5 Credentials

Create `.env` file in project root:

```bash
# .env
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
```

### Step 3: Start Server

```bash
python mt5_zmq_server.py
```

**Expected Output**:
```
================================================================================
MT5 ZMQ Server Initialized - Protocol v4.3
  Bind Address: 0.0.0.0:5555
  MT5 Server: YourBroker-Server
  Signature Validation: True
  Signature TTL: 5s
================================================================================
✅ [ZMQ] Listening on tcp://0.0.0.0:5555
✅ [MT5] Connected successfully
================================================================================
🚀 MT5 ZMQ Server is RUNNING - Waiting for commands...
================================================================================
```

### Step 4: Test Server

Open another terminal:

```bash
python test_mt5_zmq_server.py
```

**Expected Output**:
```
================================================================================
🧪 Testing MT5 ZMQ Server
================================================================================

📡 Connecting to tcp://localhost:5555...

--------------------------------------------------------------------------------
Test 1: PING (Heartbeat)
--------------------------------------------------------------------------------
✅ PING test passed

[... more tests ...]

================================================================================
✅ All tests passed!
================================================================================
```

---

## Common Use Cases

### 1. Start with Custom Port

```bash
python mt5_zmq_server.py --port 6666
```

### 2. Start with Debug Logging

```bash
python mt5_zmq_server.py --debug
```

### 3. Start Without Signature Validation (Testing Only!)

```bash
python mt5_zmq_server.py --no-signature-validation
```

**⚠️ WARNING**: Only use this for testing! Production must validate signatures.

### 4. Override .env Credentials

```bash
python mt5_zmq_server.py --mt5-login 123456 --mt5-password xxx --mt5-server Broker-Server
```

---

## Integration with Linux Inf Node

On the **Linux side**, use `MT5LiveConnector`:

```python
from src.execution.mt5_live_connector import MT5LiveConnector
from src.risk.circuit_breaker import CircuitBreaker

# Initialize
cb = CircuitBreaker()
connector = MT5LiveConnector(
    gateway_host="172.19.141.255",  # Windows GTW IP
    gateway_port=5555,
    circuit_breaker=cb,
    initial_balance=100000.0
)

# Connect
connector.connect()

# Send order (automatically validated and signed by RiskMonitor)
result = connector.send_order({
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.01,
    "sl": 1.05000,
    "tp": 1.06000,
    "comment": "Strategy_v1"
})

print(f"Status: {result['status']}")
if result['status'] == 'FILLED':
    print(f"Ticket: {result['ticket']}")
```

---

## Troubleshooting

### Issue: "Port already in use"

**Solution**:
```bash
netstat -ano | findstr :5555
taskkill /PID <pid> /F
```

### Issue: "MT5 connection failed"

**Check**:
- [ ] MT5 terminal is running
- [ ] Credentials in `.env` are correct
- [ ] Broker allows API trading
- [ ] MT5_PATH points to `terminal64.exe`

### Issue: "Orders rejected - RISK_SIGNATURE_INVALID"

**Check**:
- [ ] Using `MT5LiveConnector` (auto-generates signatures)
- [ ] System clocks synchronized (Linux ↔ Windows)
- [ ] Signature TTL not exceeded (default: 5s)

For testing, temporarily disable validation:
```bash
python mt5_zmq_server.py --no-signature-validation
```

---

## Architecture Diagram

```
Linux Inf (172.19.141.250)          Windows GTW (172.19.141.255)
┌──────────────────────────┐        ┌───────────────────────────┐
│  MT5LiveConnector        │        │  MT5ZmqServer             │
│  - RiskMonitor           │        │  - ZMQ REP Socket         │
│  - Risk Signature Gen    │        │  - Signature Validation   │
│  - ZMQ REQ Client        │        │  - MT5Service             │
└────────────┬─────────────┘        └────────┬──────────────────┘
             │                               │
             └──── ZMQ REQ/REP (5555) ───────┤
                   JSON Protocol v4.3        │
                                             ▼
                                    ┌────────────────────┐
                                    │  MT5 Terminal      │
                                    │  (Real Trading)    │
                                    └────────────────────┘
```

---

## Command Reference

| Command | Purpose | Required Fields |
|---------|---------|-----------------|
| `PING` | Heartbeat check | uuid, timestamp |
| `OPEN` | Open position | uuid, symbol, type, volume, **risk_signature** |
| `CLOSE` | Close position | uuid, ticket |
| `GET_ACCOUNT` | Query account | uuid |
| `GET_POSITIONS` | Query positions | uuid (optional: symbol filter) |

**Note**: All `OPEN` commands **MUST** include `risk_signature`.

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| PING Latency | < 10ms | 99% of requests |
| Order Execution | < 50ms | 95% (excluding broker latency) |
| Uptime | 99.9% | With auto-reconnect |

---

## Security Checklist

- [x] Risk signature validation enabled
- [x] Signature TTL = 5 seconds
- [x] Auto-reconnect on MT5 disconnect
- [x] Full audit logging
- [x] Structured error responses
- [x] No silent failures

---

## Next Steps

1. ✅ **Server Running**: Verify server starts without errors
2. ✅ **Test Suite Passes**: Run `test_mt5_zmq_server.py`
3. ✅ **Linux Integration**: Connect from Linux Inf node
4. ✅ **Test Order Execution**: Execute small test order
5. ✅ **Monitor Logs**: Check `mt5_zmq_server.log`
6. ✅ **Production Deploy**: Deploy to production GTW

---

## Support & Documentation

- **Full Documentation**: `scripts/gateway/README.md`
- **Implementation Details**: `scripts/gateway/IMPLEMENTATION_SUMMARY.md`
- **Architecture**: `docs/archive/tasks/TASK_106_MT5_BRIDGE/ARCHITECTURE.md`
- **Logs**: `scripts/gateway/mt5_zmq_server.log`

---

## Author

**Claude Sonnet 4.5**
Task: #106 (MT5 Live Bridge)
Date: 2026-01-15
Protocol: v4.3 (Zero-Trust Edition)

**Status**: ✅ Production Ready
