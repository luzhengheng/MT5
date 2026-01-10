# Task #077: Sentinel Daemon Systemd Service - Quick Start

**Status**: ✅ DEPLOYED
**Version**: 1.0
**Date**: 2026-01-10
**Protocol**: v4.3 (Zero-Trust Edition)

---

## Current Status

🟢 **Service is RUNNING**
- PID: 3110627
- Status: Active (running)
- Auto-start: Enabled
- Memory: 199.5M / 1.0G

⚠️ **Known Issue**: Feature builder timestamp parsing error (non-blocking for service)

---

## Quick Commands

### View Service Status
```bash
systemctl status mt5-sentinel
```

### View Live Logs
```bash
journalctl -u mt5-sentinel -f
```

### Stop Service
```bash
systemctl stop mt5-sentinel
```

### Start Service
```bash
systemctl start mt5-sentinel
```

### Restart Service
```bash
systemctl restart mt5-sentinel
```

### Disable Auto-Start
```bash
systemctl disable mt5-sentinel
```

---

## Installation (If Not Already Installed)

```bash
cd /opt/mt5-crs
bash scripts/install_service.sh
```

Expected output:
```
✅ Installation Complete!
● mt5-sentinel.service - MT5-CRS Sentinel Daemon
   Active: active (running)
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check service status
systemctl status mt5-sentinel

# View error logs
journalctl -u mt5-sentinel -n 50

# Common issues:
# 1. Missing dependencies
pip3 install requests pyzmq pandas numpy schedule

# 2. Missing venv
cd /opt/mt5-crs && python3 -m venv venv

# 3. Missing .env file
cp .env.example .env
```

### High Memory Usage
```bash
# Check current usage
systemctl status mt5-sentinel | grep Memory

# Restart service to clear memory
systemctl restart mt5-sentinel
```

### Logs Not Showing
```bash
# Verify service is running
systemctl is-active mt5-sentinel

# Check systemd journal
journalctl -xe | grep mt5-sentinel
```

---

## Configuration

### Service File
Location: `/etc/systemd/system/mt5-sentinel.service`

To modify:
```bash
# 1. Edit source file
nano /opt/mt5-crs/systemd/mt5-sentinel.service

# 2. Reinstall
bash /opt/mt5-crs/scripts/install_service.sh

# 3. Reload daemon
systemctl daemon-reload

# 4. Restart service
systemctl restart mt5-sentinel
```

### Command-Line Arguments
Edit `ExecStart` in service file:
```ini
# Dry-run mode (default)
ExecStart=/opt/mt5-crs/venv/bin/python .../sentinel_daemon.py --dry-run --threshold 0.6

# Live trading mode (WARNING: Real money!)
ExecStart=/opt/mt5-crs/venv/bin/python .../sentinel_daemon.py --live --threshold 0.7
```

---

## Monitoring

### Check Service Health
```bash
# Quick status check
systemctl is-active mt5-sentinel && echo "✓ Running" || echo "✗ Stopped"

# Detailed status
systemctl status mt5-sentinel --no-pager

# Process info
ps aux | grep sentinel_daemon
```

### Monitor Logs in Real-Time
```bash
# All logs
journalctl -u mt5-sentinel -f

# Errors only
journalctl -u mt5-sentinel -f | grep -E "ERROR|WARN"

# Trading cycles only
journalctl -u mt5-sentinel -f | grep "TRADING CYCLE"
```

### Check Resource Usage
```bash
# Memory
systemctl status mt5-sentinel | grep Memory

# CPU (via htop)
htop -p $(pgrep -f sentinel_daemon)
```

---

## Safety & Rollback

### Stop Trading Immediately
```bash
systemctl stop mt5-sentinel
```

### Disable Service
```bash
systemctl disable mt5-sentinel
systemctl stop mt5-sentinel
```

### Remove Service
```bash
systemctl stop mt5-sentinel
systemctl disable mt5-sentinel
rm /etc/systemd/system/mt5-sentinel.service
systemctl daemon-reload
```

---

## Common Tasks

### Viewing Recent Activity
```bash
# Last 10 minutes
journalctl -u mt5-sentinel --since "10 minutes ago"

# Last 100 lines
journalctl -u mt5-sentinel -n 100

# Today's logs
journalctl -u mt5-sentinel --since today
```

### Checking for Errors
```bash
# Count errors
journalctl -u mt5-sentinel | grep ERROR | wc -l

# View unique errors
journalctl -u mt5-sentinel | grep ERROR | sort | uniq

# Last 10 errors
journalctl -u mt5-sentinel | grep ERROR | tail -10
```

### Verifying Trading Cycles
```bash
# Count cycle executions
journalctl -u mt5-sentinel | grep "TRADING CYCLE START" | wc -l

# View last 5 cycles
journalctl -u mt5-sentinel | grep "TRADING CYCLE START" | tail -5
```

---

## Performance Expectations

### Normal Operation
- **Memory**: 150-250MB
- **CPU**: < 5% average
- **Cycle Time**: 2-3 seconds per minute
- **Restart Time**: < 5 seconds

### Resource Limits
- **Memory Limit**: 1GB (hard cap)
- **File Descriptors**: 4096
- **Restart Delay**: 10 seconds after crash

---

## Next Steps

1. **Monitor for 10 minutes**: Ensure daemon stability
2. **Fix feature_builder bug**: Task #077.2
3. **End-to-end test**: Task #077.3

---

## Support

- **Logs**: `journalctl -u mt5-sentinel`
- **Status**: `systemctl status mt5-sentinel`
- **Docs**: [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- **Issues**: Check [VERIFY_LOG.log](./VERIFY_LOG.log)

---

**Deployment**: 2026-01-10 21:04:46 CST
**Protocol**: v4.3 (Zero-Trust Edition)
**Status**: ✅ OPERATIONAL (with known non-blocking issue)
