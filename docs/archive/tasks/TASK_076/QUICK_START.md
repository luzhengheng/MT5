# Task #076: Sentinel Daemon - Quick Start Guide

**Status**: ✅ COMPLETE
**Version**: 1.0
**Date**: 2026-01-10
**Protocol**: v4.3 (Zero-Trust Edition)

---

## Overview

The Sentinel Daemon is a production-ready trading orchestrator that runs continuously on the INF node. It automates the complete trading cycle:

1. Fetch market data from EODHD API
2. Build lightweight features (pure pandas/numpy)
3. Request predictions from HUB model server
4. Execute trades via GTW (if confidence threshold met)

**Execution Frequency**: Every 1 minute at :58 seconds

---

## Prerequisites

### 1. Verify Environment Setup

```bash
# On INF server (172.19.141.250)
cd /opt/mt5-crs

# Check Python dependencies
python3 -c "import requests, zmq, pandas, numpy, schedule; print('✓ All dependencies available')"
```

If dependencies are missing:
```bash
pip3 install requests pyzmq pandas numpy schedule
```

### 2. Verify HUB Server is Running

```bash
# Test HUB model server connectivity
curl -s http://172.19.141.254:5001/ping

# Expected output: {"status": "ok"} or similar
```

If HUB is not running, start it:
```bash
ssh hub "cd /opt/mt5-crs && bash scripts/deploy_hub_serving.sh"
```

### 3. Verify GTW Server is Running

```bash
# Check if GTW ZMQ port is listening
nc -zv 172.19.141.255 5555

# Expected output: Connection to 172.19.141.255 5555 port [tcp/*] succeeded!
```

### 4. Set EODHD API Token

```bash
# Verify .env file has EODHD_API_TOKEN
grep EODHD_API_TOKEN /opt/mt5-crs/.env

# If missing, add it:
echo "EODHD_API_TOKEN=your_token_here" >> /opt/mt5-crs/.env
```

---

## Quick Start (Dry-Run Mode)

### Step 1: Run in Dry-Run Mode (Recommended First)

**Dry-run mode** makes predictions but **does NOT execute real trades**. This is safe for testing.

```bash
cd /opt/mt5-crs
python3 src/strategy/sentinel_daemon.py --dry-run
```

**Expected Output**:
```
============================================================
Sentinel Daemon Initialized
============================================================
HUB: http://172.19.141.254:5001
GTW: tcp://172.19.141.255:5555
Symbol: EURUSD
Threshold: 0.6
Dry Run: True
============================================================
Starting Sentinel Daemon...
Scheduled to run every 1 minute at :58 seconds
Press Ctrl+C to stop

[2026-01-10 10:58:00] ===== Trading Cycle Start =====
[2026-01-10 10:58:01] Fetching EURUSD data from EODHD...
[2026-01-10 10:58:02] Building features (23 features)...
[2026-01-10 10:58:03] Requesting prediction from HUB...
[2026-01-10 10:58:04] Prediction: [0.15, 0.35, 0.50] → BUY (confidence: 0.50)
[2026-01-10 10:58:04] Confidence 0.50 below threshold 0.60 - NO ACTION
[2026-01-10 10:58:04] ===== Trading Cycle Complete =====
```

### Step 2: Monitor Execution

Let the daemon run for 5-10 minutes and observe:

✅ **Success Indicators**:
- No error messages
- Regular cycle execution every minute
- Predictions received from HUB
- Proper threshold filtering

⚠️ **Warning Signs**:
- Connection timeouts to HUB or GTW
- Feature building errors
- API rate limit errors

### Step 3: Stop the Daemon

Press `Ctrl+C` to gracefully stop:
```
^C
Received interrupt signal
Shutting down Sentinel Daemon...
Daemon stopped.
```

---

## Live Trading Mode (Production)

⚠️ **WARNING**: Live mode executes **REAL TRADES**. Only use after successful dry-run testing.

### Run in Live Mode

```bash
cd /opt/mt5-crs
python3 src/strategy/sentinel_daemon.py --live --threshold 0.65
```

**Key Differences**:
- `--live` flag enables real trade execution
- Recommended higher threshold (0.65-0.7) for live trading
- All predictions above threshold will result in actual trades

**Expected Output** (Live Mode):
```
============================================================
Sentinel Daemon Initialized
============================================================
HUB: http://172.19.141.254:5001
GTW: tcp://172.19.141.255:5555
Symbol: EURUSD
Threshold: 0.65
Dry Run: False  ← LIVE MODE ACTIVE
============================================================

[2026-01-10 11:58:04] Prediction: [0.10, 0.20, 0.70] → BUY (confidence: 0.70)
[2026-01-10 11:58:04] !!! LIVE MODE: Sending BUY signal to GTW...
[2026-01-10 11:58:05] GTW Response: {"status": "success", "order_id": "12345"}
[2026-01-10 11:58:05] ✓ Trade executed successfully
```

---

## Configuration Options

### Command-Line Arguments

| Option | Default | Description |
|--------|---------|-------------|
| `--hub-host` | 172.19.141.254 | HUB server IP address |
| `--hub-port` | 5001 | HUB model serving port |
| `--gtw-host` | 172.19.141.255 | GTW server IP address |
| `--gtw-port` | 5555 | GTW ZMQ port |
| `--symbol` | EURUSD | Trading symbol |
| `--threshold` | 0.6 | Confidence threshold (0.0-1.0) |
| `--dry-run` | True | Safe mode (no trades) |
| `--live` | False | Live trading mode |

### Example Configurations

**Conservative Live Trading** (higher threshold):
```bash
python3 src/strategy/sentinel_daemon.py --live --threshold 0.75
```

**Different Symbol** (requires model retraining):
```bash
python3 src/strategy/sentinel_daemon.py --dry-run --symbol GBPUSD
```

**Custom Servers** (for testing):
```bash
python3 src/strategy/sentinel_daemon.py \
    --hub-host 192.168.1.100 \
    --hub-port 8080 \
    --gtw-host 192.168.1.200 \
    --gtw-port 6666 \
    --dry-run
```

---

## Troubleshooting

### Problem 1: "Connection refused" to HUB

**Symptom**:
```
[ERROR] Connection failed - HUB may not be running
```

**Solution**:
```bash
# Check if HUB is running
ssh hub "ps aux | grep mlflow"

# If not running, start it
ssh hub "cd /opt/mt5-crs && bash scripts/deploy_hub_serving.sh"

# Verify health
curl http://172.19.141.254:5001/ping
```

---

### Problem 2: "ZMQ timeout" to GTW

**Symptom**:
```
[ERROR] ZMQ timeout - GTW may not be running
```

**Solution**:
```bash
# Check if GTW port is listening
nc -zv 172.19.141.255 5555

# Check GTW server logs
ssh gtw "tail -f /path/to/gtw/logs/gateway.log"
```

---

### Problem 3: "Insufficient data for feature building"

**Symptom**:
```
[ERROR] Need at least 100 bars, got 50
```

**Root Cause**: EODHD API returned incomplete data

**Solution**:
```bash
# Test EODHD API manually
curl "https://eodhistoricaldata.com/api/intraday/EURUSD.FOREX?api_token=YOUR_TOKEN&interval=1h&fmt=json" | jq length

# Expected: > 100 bars
# If less, wait for more data to accumulate or adjust lookback window
```

---

### Problem 4: API Rate Limit Exceeded

**Symptom**:
```
[ERROR] EODHD API error: 429 Too Many Requests
```

**Solution**:
- EODHD free tier: 20 requests/day
- Reduce execution frequency or upgrade API plan
- Check current usage: https://eodhistoricaldata.com/cp/usage

---

### Problem 5: High Memory Usage

**Symptom**:
```bash
free -h
# Shows >3GB used on INF (4GB limit)
```

**Solution**:
```bash
# Restart daemon to clear memory
pkill -f sentinel_daemon
python3 src/strategy/sentinel_daemon.py --dry-run

# Monitor memory during execution
watch -n 5 'free -h'
```

---

## Monitoring and Logs

### View Real-Time Logs

```bash
# Option 1: Direct output (foreground)
python3 src/strategy/sentinel_daemon.py --dry-run

# Option 2: Background with log file
nohup python3 src/strategy/sentinel_daemon.py --dry-run > logs/sentinel.log 2>&1 &

# View logs
tail -f logs/sentinel.log
```

### Check Daemon Process

```bash
# Find running daemon
ps aux | grep sentinel_daemon

# Example output:
# trader  12345  0.5  2.1  450M  ...  python3 src/strategy/sentinel_daemon.py --dry-run
```

### Stop Daemon Gracefully

```bash
# Find process ID
PID=$(pgrep -f sentinel_daemon)

# Send SIGINT (same as Ctrl+C)
kill -2 $PID

# Verify stopped
ps aux | grep sentinel_daemon
```

---

## Performance Expectations

### Typical Execution Times (per cycle)

| Stage | Time | Notes |
|-------|------|-------|
| Data Fetch | 1-2s | EODHD API latency |
| Feature Building | 0.1s | Pure pandas operations |
| HUB Inference | 0.5s | Network + model time |
| GTW Execution | 0.1s | ZMQ is very fast |
| **Total** | **2-3s** | Well under 60s cycle time |

### Memory Footprint

- Baseline: ~200MB (Python + pandas)
- Per cycle: +50MB (OHLCV data + features)
- Peak: ~300MB (well under 4GB limit)

### Network Requirements

- Outbound HTTP to EODHD API (eodhistoricaldata.com:443)
- Outbound HTTP to HUB (172.19.141.254:5001)
- Outbound ZMQ to GTW (172.19.141.255:5555)

---

## Safety Features

1. **Dry-Run by Default**: Must explicitly use `--live` flag
2. **Confidence Threshold**: Only trade when model is confident (default 0.6)
3. **Fail Fast**: 1-second timeout on HUB requests
4. **Never-Crash**: Errors logged but daemon continues
5. **Graceful Degradation**: Skips cycle on errors, retries next minute

---

## Next Steps

After successful testing:

1. **Convert to Systemd Service** (Task #077):
   - Auto-start on server boot
   - Automatic restart on crashes
   - Proper log rotation

2. **Add Monitoring** (Task #078):
   - Prometheus metrics
   - Grafana dashboards
   - Alert on failures

3. **Multi-Symbol Support** (Task #079):
   - Trade multiple currency pairs
   - Symbol-specific models
   - Portfolio management

---

## Support and Documentation

- **Full Documentation**: [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- **Deployment Guide**: [SYNC_GUIDE.md](./SYNC_GUIDE.md)
- **Architecture Overview**: [COMPLETION_REPORT.md#architecture-overview](./COMPLETION_REPORT.md#architecture-overview)

---

**Protocol v4.3 Compliance**: ✅
**Task #076 Status**: ✅ COMPLETE
**Daemon Status**: ✅ OPERATIONAL
