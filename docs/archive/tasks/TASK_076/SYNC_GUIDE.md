# Task #076: Sentinel Daemon - Deployment Sync Guide

**Status**: ✅ COMPLETE
**Version**: 1.0
**Date**: 2026-01-10
**Protocol**: v4.3 (Zero-Trust Edition)

---

## Purpose

This guide describes how to synchronize Task #076 deliverables from the development environment to the production INF server (172.19.141.250).

**Deliverables**:
- `src/strategy/feature_builder.py` (385 lines)
- `src/strategy/sentinel_daemon.py` (496 lines)
- Documentation (COMPLETION_REPORT.md, QUICK_START.md, this file)

---

## Prerequisites

### 1. SSH Access to INF Server

```bash
# Test SSH connectivity
ssh inf "hostname && date"

# Expected output:
# inf
# 2026年 01月 10日 星期五 18:00:00 CST
```

If SSH fails, configure SSH keys:
```bash
ssh-copy-id inf
```

### 2. Git Repository Access

```bash
# Verify Git remote is configured
git remote -v

# Expected output:
# origin  git@github.com:your-org/mt5-crs.git (fetch)
# origin  git@github.com:your-org/mt5-crs.git (push)
```

### 3. Verify Commit Status

```bash
# Ensure Task #076 is committed
git log --oneline -5 | grep "task-076"

# Expected output:
# 55ec6e9 feat(task-076): train and register stacking meta-learner
```

---

## Deployment Methods

Choose one of the following methods based on your environment:

- **Method A**: Git Pull (Recommended for production)
- **Method B**: Direct File Copy (For testing/emergency)
- **Method C**: Docker Volume Mount (If using containerized deployment)

---

## Method A: Git Pull (Recommended)

### Step 1: Commit and Push from Development

```bash
# On development machine
cd /opt/mt5-crs

# Verify all changes are committed
git status

# If uncommitted changes exist:
git add src/strategy/feature_builder.py src/strategy/sentinel_daemon.py
git commit -m "feat(task-076): implement sentinel daemon and feature builder"
git push origin main
```

### Step 2: Pull on INF Server

```bash
# SSH to INF server
ssh inf

# Navigate to project directory
cd /opt/mt5-crs

# Stash any local changes (if needed)
git stash

# Pull latest changes
git pull origin main

# Expected output:
# Updating abc1234..55ec6e9
# Fast-forward
#  src/strategy/feature_builder.py   | 385 +++++++++++++++++++++++++++++++++++
#  src/strategy/sentinel_daemon.py   | 496 +++++++++++++++++++++++++++++++++++++++++++
#  2 files changed, 881 insertions(+)
#  create mode 100644 src/strategy/feature_builder.py
#  create mode 100644 src/strategy/sentinel_daemon.py
```

### Step 3: Verify Files

```bash
# Check file existence
ls -lh src/strategy/*.py

# Expected output:
# -rw-r--r-- 1 trader trader 15K Jan 10 17:00 feature_builder.py
# -rw-r--r-- 1 trader trader 19K Jan 10 17:00 sentinel_daemon.py

# Verify syntax
python3 -m py_compile src/strategy/feature_builder.py
python3 -m py_compile src/strategy/sentinel_daemon.py

# No output = success
```

### Step 4: Test Installation

```bash
# Run handshake test (from Task #075)
python3 src/infra/handshake.py

# Expected: All tests PASS

# Test feature builder import
python3 -c "from src.strategy.feature_builder import FeatureBuilder; print('✓ Import success')"

# Test daemon import
python3 -c "from src.strategy.sentinel_daemon import SentinelDaemon; print('✓ Import success')"
```

---

## Method B: Direct File Copy (Emergency/Testing)

Use this method if Git is unavailable or for quick testing.

### Step 1: Copy Files via SCP

```bash
# From development machine
cd /opt/mt5-crs

# Copy feature_builder.py
scp src/strategy/feature_builder.py inf:/opt/mt5-crs/src/strategy/

# Copy sentinel_daemon.py
scp src/strategy/sentinel_daemon.py inf:/opt/mt5-crs/src/strategy/

# Copy documentation
scp docs/archive/tasks/TASK_076/*.md inf:/opt/mt5-crs/docs/archive/tasks/TASK_076/
```

### Step 2: Verify on INF Server

```bash
# SSH to INF
ssh inf

# Verify file sizes match
cd /opt/mt5-crs
wc -l src/strategy/feature_builder.py src/strategy/sentinel_daemon.py

# Expected output:
#   385 src/strategy/feature_builder.py
#   496 src/strategy/sentinel_daemon.py
#   881 total
```

### Step 3: Set Permissions

```bash
# Ensure correct permissions
chmod 644 src/strategy/feature_builder.py
chmod 755 src/strategy/sentinel_daemon.py  # Executable entry point

# Verify
ls -l src/strategy/*.py
```

---

## Method C: Docker Volume Mount

If using containerized deployment:

### Step 1: Update Docker Compose

```yaml
# docker-compose.yml (on INF server)
services:
  sentinel:
    image: mt5-crs:latest
    volumes:
      - ./src:/app/src:ro  # Read-only mount
      - ./logs:/app/logs   # Writable logs
    environment:
      - HUB_HOST=172.19.141.254
      - GTW_HOST=172.19.141.255
    command: python3 src/strategy/sentinel_daemon.py --dry-run
```

### Step 2: Rebuild and Restart

```bash
# SSH to INF
ssh inf
cd /opt/mt5-crs

# Pull latest code
git pull origin main

# Rebuild container
docker-compose build sentinel

# Restart service
docker-compose up -d sentinel

# View logs
docker-compose logs -f sentinel
```

---

## Post-Deployment Verification

### 1. Environment Check

```bash
# On INF server
ssh inf "cd /opt/mt5-crs && python3 -c 'import requests, zmq, pandas, numpy, schedule; print(\"✓ Dependencies OK\")'"
```

### 2. Connectivity Test

```bash
# Run handshake validation
ssh inf "cd /opt/mt5-crs && python3 src/infra/handshake.py"

# Expected: All 4 tests PASS
```

### 3. Dry-Run Test

```bash
# Start daemon in dry-run mode
ssh inf "cd /opt/mt5-crs && python3 src/strategy/sentinel_daemon.py --dry-run" &

# Wait for one cycle (60 seconds)
sleep 65

# Check for errors
# Should see successful cycle completion

# Stop daemon
pkill -f sentinel_daemon
```

### 4. File Integrity Verification

```bash
# Compare checksums (from dev to prod)

# On development machine:
md5sum src/strategy/feature_builder.py src/strategy/sentinel_daemon.py

# On INF server:
ssh inf "cd /opt/mt5-crs && md5sum src/strategy/feature_builder.py src/strategy/sentinel_daemon.py"

# Checksums should match exactly
```

---

## Rollback Procedure

If deployment fails, rollback to previous version:

### Git Rollback

```bash
# On INF server
ssh inf
cd /opt/mt5-crs

# View recent commits
git log --oneline -10

# Rollback to previous commit (before Task #076)
git reset --hard <previous_commit_hash>

# Example:
git reset --hard 6cd06c5

# Verify rollback
git log --oneline -1
```

### Manual Rollback

```bash
# If files were copied directly, restore from backup
ssh inf "cd /opt/mt5-crs && git checkout HEAD~1 -- src/strategy/"

# Or restore from Git history
ssh inf "cd /opt/mt5-crs && git restore src/strategy/feature_builder.py src/strategy/sentinel_daemon.py"
```

---

## Production Deployment Checklist

Before enabling live trading, verify:

- [ ] ✅ Files deployed successfully
- [ ] ✅ Python syntax valid (py_compile passes)
- [ ] ✅ All dependencies installed
- [ ] ✅ HUB server running and accessible
- [ ] ✅ GTW server running and accessible
- [ ] ✅ EODHD API token configured in .env
- [ ] ✅ Handshake test passes (all 4 tests)
- [ ] ✅ Dry-run test passes (at least 5 cycles)
- [ ] ✅ Memory usage acceptable (<500MB)
- [ ] ✅ No error messages in logs
- [ ] ✅ Predictions received from HUB
- [ ] ✅ Threshold filtering works correctly
- [ ] ✅ Backup/rollback plan documented
- [ ] ✅ Monitoring configured (if available)

---

## Environment-Specific Configuration

### Development Environment

```bash
# Use local test servers
python3 src/strategy/sentinel_daemon.py \
    --hub-host 127.0.0.1 \
    --hub-port 5001 \
    --gtw-host 127.0.0.1 \
    --gtw-port 5555 \
    --dry-run
```

### Staging Environment

```bash
# Use staging servers with dry-run
python3 src/strategy/sentinel_daemon.py \
    --hub-host 172.19.141.254 \
    --gtw-host 172.19.141.255 \
    --threshold 0.65 \
    --dry-run
```

### Production Environment

```bash
# Live trading (only after thorough testing)
python3 src/strategy/sentinel_daemon.py \
    --hub-host 172.19.141.254 \
    --gtw-host 172.19.141.255 \
    --threshold 0.70 \
    --live
```

---

## Troubleshooting Deployment Issues

### Issue 1: Import Errors

**Symptom**:
```
ModuleNotFoundError: No module named 'src.strategy.feature_builder'
```

**Solution**:
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/opt/mt5-crs:$PYTHONPATH

# Or use absolute imports
cd /opt/mt5-crs
python3 -m src.strategy.sentinel_daemon --dry-run
```

---

### Issue 2: Permission Denied

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: 'src/strategy/sentinel_daemon.py'
```

**Solution**:
```bash
# Fix permissions
chmod 755 src/strategy/sentinel_daemon.py
chmod 644 src/strategy/feature_builder.py

# Verify ownership
chown -R trader:trader src/strategy/
```

---

### Issue 3: Git Merge Conflicts

**Symptom**:
```
error: Your local changes to the following files would be overwritten by merge:
    src/strategy/sentinel_daemon.py
```

**Solution**:
```bash
# Stash local changes
git stash

# Pull latest
git pull origin main

# Review stashed changes
git stash show -p

# Apply if needed (may have conflicts)
git stash pop

# Or discard local changes
git stash drop
```

---

### Issue 4: Missing Dependencies

**Symptom**:
```
ModuleNotFoundError: No module named 'schedule'
```

**Solution**:
```bash
# Run setup script from Task #075
bash scripts/setup_inf_env.sh

# Or install manually
pip3 install requests pyzmq pandas numpy schedule
```

---

## Monitoring Post-Deployment

### Check Daemon Status

```bash
# Find running daemon
ssh inf "ps aux | grep sentinel_daemon"

# Check memory usage
ssh inf "ps -o pid,vsz,rss,cmd -C python3 | grep sentinel"
```

### Monitor Logs

```bash
# If running with log file
ssh inf "tail -f /opt/mt5-crs/logs/sentinel.log"

# If running in foreground (screen/tmux)
ssh inf
screen -r sentinel  # Or tmux attach -t sentinel
```

### Check Cycle Success Rate

```bash
# Count successful vs failed cycles
ssh inf "grep 'Trading Cycle Complete' /opt/mt5-crs/logs/sentinel.log | wc -l"
ssh inf "grep 'CYCLE ERROR' /opt/mt5-crs/logs/sentinel.log | wc -l"
```

---

## Automation Recommendations

### Systemd Service (Task #077)

For production, convert to systemd service:

```bash
# Create service file: /etc/systemd/system/sentinel.service
[Unit]
Description=MT5-CRS Sentinel Daemon
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/opt/mt5-crs
ExecStart=/usr/bin/python3 src/strategy/sentinel_daemon.py --live --threshold 0.70
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Deployment Automation

Create deployment script:

```bash
#!/bin/bash
# scripts/deploy_sentinel.sh

set -euo pipefail

echo "Deploying Sentinel Daemon to INF..."

# Pull latest code
ssh inf "cd /opt/mt5-crs && git pull origin main"

# Run tests
ssh inf "cd /opt/mt5-crs && python3 src/infra/handshake.py"

# Restart service (if using systemd)
ssh inf "sudo systemctl restart sentinel"

# Check status
ssh inf "sudo systemctl status sentinel"

echo "✓ Deployment complete"
```

---

## Security Considerations

1. **Secrets Management**: Never commit API tokens to Git
   ```bash
   # Verify .env is in .gitignore
   grep -q ".env" .gitignore || echo ".env" >> .gitignore
   ```

2. **File Permissions**: Restrict access to sensitive files
   ```bash
   chmod 600 .env
   chmod 700 logs/
   ```

3. **Network Security**: Use firewall rules to restrict access
   ```bash
   # Allow only INF → HUB/GTW communication
   sudo ufw allow out to 172.19.141.254 port 5001
   sudo ufw allow out to 172.19.141.255 port 5555
   ```

---

## Version History

| Version | Date | Changes | Commit |
|---------|------|---------|--------|
| 1.0 | 2026-01-10 | Initial deployment | 55ec6e9 |

---

## Related Documentation

- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md) - Full technical documentation
- [QUICK_START.md](./QUICK_START.md) - Operator quick start guide
- [Task #075 SYNC_GUIDE.md](../TASK_075/SYNC_GUIDE.md) - INF environment setup

---

**Protocol v4.3 Compliance**: ✅
**Deployment Ready**: ✅
**Rollback Tested**: ✅
