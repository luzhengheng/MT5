# MT5 Gateway - ZMQ Bridge for MT5 Trading

This directory contains the **Windows-side ZMQ server** for Task #106 (MT5 Live Bridge).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Linux Inf Node                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  MT5LiveConnector (src/execution/mt5_live_connector.py) │   │
│  │  - Sends trading commands via ZMQ                        │   │
│  │  - Validates orders with RiskMonitor                     │   │
│  │  - Generates risk_signature                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ▼ ZMQ REQ/REP (Port 5555)             │
└─────────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                     Windows GTW Node                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  MT5ZmqServer (scripts/gateway/mt5_zmq_server.py)       │   │
│  │  - Listens on ZMQ REP socket (port 5555)                │   │
│  │  - Validates risk_signature                              │   │
│  │  - Executes MT5 API calls                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ▼                                      │
│                    MT5 Terminal (Real)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Files

- **mt5_zmq_server.py**: Main ZMQ server (Windows-side gateway)
- **test_mt5_zmq_server.py**: Test client for verification
- **README.md**: This file

## Quick Start (Windows)

### 1. Setup Environment

Create a `.env` file in the project root with your MT5 credentials:

```bash
# MT5 Configuration
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
```

### 2. Install Dependencies

```bash
pip install pyzmq python-dotenv pyyaml
pip install MetaTrader5  # Windows only
```

### 3. Start the Server

```bash
# Start with default settings (uses .env)
python mt5_zmq_server.py

# Start with custom port
python mt5_zmq_server.py --port 6666

# Start with explicit credentials (overrides .env)
python mt5_zmq_server.py --mt5-login 123456 --mt5-password xxx --mt5-server Broker-Server

# Start with debug logging
python mt5_zmq_server.py --debug

# Start without signature validation (TESTING ONLY!)
python mt5_zmq_server.py --no-signature-validation
```

### 4. Test the Server

Open another terminal:

```bash
# Run test suite
python test_mt5_zmq_server.py
```

## Supported Commands

### 1. PING (Heartbeat Check)

**Request:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "action": "PING",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ok",
  "server_time": "2026-01-15T02:08:34.234567Z",
  "latency_ms": 0.111
}
```

### 2. OPEN (Open Position)

**Request:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440001",
  "action": "OPEN",
  "symbol": "EURUSD",
  "type": "BUY",
  "volume": 0.01,
  "price": 0.0,
  "sl": 1.05000,
  "tp": 1.06000,
  "comment": "Strategy_v1",
  "risk_signature": "RISK_PASS:7a3f9e8b:2026-01-15T02:08:33Z",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**Response (Success):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440001",
  "status": "FILLED",
  "ticket": 12345678,
  "symbol": "EURUSD",
  "volume": 0.01,
  "price": 1.05230,
  "execution_time": "2026-01-15T02:08:34.234567Z",
  "latency_ms": 1.234
}
```

**Response (Rejected):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440001",
  "status": "REJECTED",
  "error_code": "INSUFFICIENT_MARGIN",
  "error_msg": "Not enough margin to open position",
  "timestamp": "2026-01-15T02:08:34.234567Z"
}
```

### 3. CLOSE (Close Position)

**Request:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440002",
  "action": "CLOSE",
  "ticket": 12345678,
  "symbol": "EURUSD",
  "volume": 0.01,
  "timestamp": "2026-01-15T02:10:00.123456Z"
}
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440002",
  "status": "FILLED",
  "ticket": 87654321,
  "close_price": 1.05280,
  "execution_time": "2026-01-15T02:10:00.234567Z",
  "latency_ms": 1.123
}
```

### 4. GET_ACCOUNT (Query Account Info)

**Request:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440003",
  "action": "GET_ACCOUNT",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440003",
  "status": "ok",
  "balance": 100000.00,
  "equity": 100500.50,
  "margin": 500.00,
  "free_margin": 99500.50,
  "margin_level": 20100.1,
  "currency": "USD",
  "timestamp": "2026-01-15T02:08:34.234567Z"
}
```

### 5. GET_POSITIONS (Query Open Positions)

**Request:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440004",
  "action": "GET_POSITIONS",
  "symbol": "EURUSD",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**Response:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440004",
  "status": "ok",
  "positions": [
    {
      "ticket": 12345678,
      "symbol": "EURUSD",
      "type": "BUY",
      "volume": 0.01,
      "open_price": 1.05230,
      "current_price": 1.05280,
      "profit": 5.00
    }
  ],
  "timestamp": "2026-01-15T02:08:35.123456Z"
}
```

## Risk Signature Validation

All `OPEN` commands **MUST** include a `risk_signature` field with the format:

```
RISK_PASS:<checksum>:<timestamp>
```

Example: `RISK_PASS:7a3f9e8b:2026-01-15T02:08:33Z`

**Validation Rules:**
1. Signature must exist
2. Format must be `RISK_PASS:<checksum>:<timestamp>`
3. Timestamp must be within TTL (default: 5 seconds)
4. Checksum format must be valid (min 8 chars)

**How to generate risk_signature:**

The signature is automatically generated by `MT5LiveConnector` on the Linux side:

```python
from src.execution.mt5_live_connector import MT5LiveConnector

connector = MT5LiveConnector(...)
result = connector.send_order({
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.01,
    ...
})
# risk_signature is automatically added by connector
```

## Security Features

1. **Zero-Trust Architecture**: Every OPEN command must have valid risk_signature
2. **TTL Enforcement**: Signatures expire after 5 seconds (configurable)
3. **Auto-Reconnect**: Server automatically reconnects to MT5 if connection is lost
4. **Full Audit Logging**: All commands and responses are logged
5. **Error Handling**: Comprehensive error handling and validation

## Performance Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| PING Latency | < 10ms | 99% of requests |
| Order Execution | < 50ms | 95% of requests |
| Uptime | 99.9% | With auto-reconnect |

## Troubleshooting

### Server won't start

**Check MT5 credentials:**
```bash
# Verify .env file exists and contains valid credentials
cat .env | grep MT5
```

**Check port availability:**
```bash
# Windows: Check if port 5555 is already in use
netstat -ano | findstr :5555
```

### MT5 connection fails

**Verify MT5 path:**
```bash
# Make sure MT5_PATH points to the correct terminal64.exe
ls "C:\Program Files\MetaTrader 5\terminal64.exe"
```

**Check MT5 login:**
- Login to MT5 manually to verify credentials
- Ensure server name is correct (case-sensitive)
- Check broker allows API trading

### Orders rejected

**Check risk signature:**
- Signature must be fresh (< 5 seconds old)
- Use `--no-signature-validation` for testing only

**Check margin:**
- Verify account has sufficient margin
- Check GET_ACCOUNT to see available margin

## Command Line Options

```
--host HOST              ZMQ bind host (default: 0.0.0.0)
--port PORT              ZMQ bind port (default: 5555)
--mt5-login LOGIN        MT5 account login (overrides .env)
--mt5-password PASS      MT5 account password (overrides .env)
--mt5-server SERVER      MT5 broker server (overrides .env)
--mt5-path PATH          MT5 terminal path (overrides .env)
--no-signature-validation  Disable signature validation (TESTING ONLY!)
--signature-ttl SECONDS  Signature TTL in seconds (default: 5)
--debug                  Enable debug logging
```

## Windows Path Handling

The server is designed to be Windows-compatible:

- Uses `pathlib.Path` for cross-platform path handling
- Accepts both forward slashes (`/`) and backslashes (`\\`) in paths
- Automatically handles Windows-style paths (e.g., `C:\Program Files\...`)

## Logs

Logs are written to:
- **Console**: All log levels (INFO and above)
- **File**: `scripts/gateway/mt5_zmq_server.log` (append mode)

## Integration with Linux Inf Node

On the Linux side, use `MT5LiveConnector` to send commands:

```python
from src.execution.mt5_live_connector import MT5LiveConnector

# Initialize connector
connector = MT5LiveConnector(
    gateway_host="172.19.141.255",  # Windows GTW IP
    gateway_port=5555,
    circuit_breaker=circuit_breaker,
    initial_balance=100000.0
)

# Connect
if connector.connect():
    print("Connected to Windows GTW")

    # Send order (automatically validated and signed)
    result = connector.send_order({
        "symbol": "EURUSD",
        "type": "BUY",
        "volume": 0.01,
        "sl": 1.05000,
        "tp": 1.06000,
        "comment": "Strategy_v1"
    })

    if result["status"] == "FILLED":
        print(f"Order filled: Ticket #{result['ticket']}")
```

## Protocol Version

**Protocol v4.3 (Zero-Trust Edition)**

Key features:
- Mandatory risk signature validation
- Time-based signature expiry (TTL)
- Full audit logging
- Auto-reconnect capability
- Comprehensive error handling

## Support

For issues or questions:
1. Check logs: `scripts/gateway/mt5_zmq_server.log`
2. Run test suite: `python test_mt5_zmq_server.py`
3. Review architecture: `docs/archive/tasks/TASK_106_MT5_BRIDGE/ARCHITECTURE.md`

## Author

**Claude Sonnet 4.5**
Date: 2026-01-15
Task: #106 (MT5 Live Bridge)
Protocol: v4.3 (Zero-Trust Edition)
