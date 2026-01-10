# Task #074: Synchronization Guide
## Model Serving Deployment - Environment Changes

**Target Environment**: HUB Server (172.19.141.254)
**Impact**: Production Infrastructure
**Rollback Difficulty**: Low (can stop server anytime)
**Date**: 2026-01-10

---

## 📦 Changes Summary

This task introduces:
- ✅ 4 new deployment scripts
- ✅ MLflow Model Server running on port 5001
- ✅ New background process (nohup)
- ✅ New log files in `logs/` directory
- ✅ Model promotion workflow

---

## 🔧 Infrastructure Changes

### 1. New Scripts Added

| File | Purpose | Executable | Location |
|------|---------|------------|----------|
| `scripts/promote_model.py` | Promote model to Production | ✓ | `/opt/mt5-crs/scripts/` |
| `scripts/deploy_hub_serving.sh` | Deploy MLflow server | ✓ | `/opt/mt5-crs/scripts/` |
| `scripts/test_inference_local.py` | Test inference locally | ✓ | `/opt/mt5-crs/scripts/` |
| `scripts/audit_task_074.py` | Task-specific audit | ✓ | `/opt/mt5-crs/scripts/` |

**Permissions**:
```bash
chmod +x scripts/promote_model.py
chmod +x scripts/deploy_hub_serving.sh
chmod +x scripts/test_inference_local.py
chmod +x scripts/audit_task_074.py
```

---

### 2. New Processes

| Process | Command | Port | Auto-Start |
|---------|---------|------|------------|
| MLflow Model Server | `mlflow models serve` | 5001 | No (manual) |

**Process Management**:
```bash
# Check status
ps aux | grep mlflow | grep 5001

# View PID
cat logs/mlflow_server.pid

# Stop server
kill $(cat logs/mlflow_server.pid)
```

---

### 3. New Ports

| Port | Protocol | Service | Binding | Firewall Rule Needed |
|------|----------|---------|---------|---------------------|
| 5001 | TCP | MLflow Model Server | 0.0.0.0 | Yes (from INF server) |

**Firewall Configuration**:
```bash
# Check current rules (AliBaba Cloud Security Group)
# - Login to Alibaba Cloud Console
# - Navigate to: ECS → Security Groups → sg-t4n0dtkxxy1sxnbjsgk6
# - Add Inbound Rule:
#   - Protocol: TCP
#   - Port: 5001
#   - Source: 172.19.0.0/16 (VPC internal)
#   - Priority: 1
#   - Action: Allow

# Alternatively, if using local firewall:
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

---

### 4. New Log Files

| Log File | Purpose | Rotation | Location |
|----------|---------|----------|----------|
| `logs/mlflow_serving_*.log` | Server output | No (manual) | `/opt/mt5-crs/logs/` |
| `logs/mlflow_server.pid` | Process ID | Overwrite | `/opt/mt5-crs/logs/` |

**Log Management**:
```bash
# View latest logs
ls -lt logs/mlflow_serving_*.log | head -1
tail -f logs/mlflow_serving_*.log

# Clean old logs (manual, if needed)
find logs/ -name "mlflow_serving_*.log" -mtime +30 -delete
```

---

## 🔄 Deployment Steps

### Pre-Deployment Checklist

- [ ] Git repository is up-to-date on HUB server
- [ ] MLflow tracking server is running
- [ ] Python virtual environment is activated (if used)
- [ ] Port 5001 is not in use by other services
- [ ] Sufficient disk space (check with `df -h`)

### Deployment Sequence

```bash
# 1. SSH to HUB server
ssh hub  # or ssh root@www.crestive-code.com

# 2. Navigate to project directory
cd /opt/mt5-crs

# 3. Pull latest code
git pull origin main

# 4. Verify scripts exist
ls -la scripts/promote_model.py
ls -la scripts/deploy_hub_serving.sh
ls -la scripts/test_inference_local.py

# 5. Promote model
python3 scripts/promote_model.py

# 6. Deploy server
bash scripts/deploy_hub_serving.sh

# 7. Verify deployment
python3 scripts/test_inference_local.py

# 8. Check server status
ps -p $(cat logs/mlflow_server.pid)
curl http://localhost:5001/ping
```

---

## 🗂️ Environment Variables

### Current (No New Variables)

No new environment variables are required for this task.

### Future (For Production Hardening)

Consider adding for future tasks:

```bash
# Example .env file
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_MODEL_SERVER_PORT=5001
MLFLOW_MODEL_SERVER_HOST=0.0.0.0
MLFLOW_MODEL_SERVER_WORKERS=2
```

---

## 📚 Dependencies

### Python Packages (Already Installed)

No new Python packages required. Task uses existing dependencies:

- `mlflow` (already installed)
- `numpy` (already installed)
- `pandas` (already installed)
- `requests` (already installed)
- `lightgbm` (already installed)
- `torch` (already installed)
- `sklearn` (already installed)

**Verify**:
```bash
python3 -c "import mlflow, numpy, pandas, requests, lightgbm, torch, sklearn; print('All dependencies OK')"
```

---

## 🔍 Verification & Testing

### Post-Deployment Verification

```bash
# 1. Model in Production
python3 << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
versions = client.search_model_versions(
    filter_string="name='stacking_ensemble_task_073'"
)

for v in versions:
    if v.current_stage == 'Production':
        print(f"✓ Production Model: Version {v.version}")
        print(f"  Run ID: {v.run_id}")
EOF

# 2. Server process running
if ps -p $(cat logs/mlflow_server.pid) > /dev/null; then
    echo "✓ Server process running"
else
    echo "✗ Server process not found"
fi

# 3. Health endpoint
if curl -s http://localhost:5001/ping | grep -q "ok"; then
    echo "✓ Health endpoint OK"
else
    echo "✗ Health endpoint failed"
fi

# 4. Run full test suite
python3 scripts/test_inference_local.py
```

---

## 📊 Monitoring

### Key Metrics to Monitor

1. **Server Uptime**
   ```bash
   ps -p $(cat logs/mlflow_server.pid) -o etime
   ```

2. **Port Status**
   ```bash
   netstat -tuln | grep 5001
   ```

3. **Process Resource Usage**
   ```bash
   ps -p $(cat logs/mlflow_server.pid) -o %cpu,%mem,cmd
   ```

4. **Log File Size**
   ```bash
   du -h logs/mlflow_serving_*.log
   ```

5. **Request Latency** (from INF server)
   ```bash
   curl -w "\nTime: %{time_total}s\n" http://172.19.141.254:5001/ping
   ```

---

## 🔙 Rollback Procedures

### If Deployment Fails

```bash
# 1. Stop MLflow server
kill $(cat logs/mlflow_server.pid)

# 2. Revert code changes (if needed)
git reset --hard HEAD~1

# 3. Remove PID file
rm -f logs/mlflow_server.pid

# 4. Check port is released
lsof -i :5001
```

### If Model Issues Occur

```bash
# Demote model from Production
python3 << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
model_name = "stacking_ensemble_task_073"

versions = client.search_model_versions(
    filter_string=f"name='{model_name}'"
)

for v in versions:
    if v.current_stage == 'Production':
        # Transition back to Staging
        client.transition_model_version_stage(
            name=model_name,
            version=v.version,
            stage="Staging"
        )
        print(f"Demoted version {v.version} to Staging")
EOF

# Restart server (will fail with no Production model)
# This forces manual intervention to fix
```

---

## 🚨 Known Issues & Workarounds

### Issue 1: Port Already in Use

**Symptom**: `Address already in use` error

**Workaround**: Script automatically handles this by killing existing process

**Manual Fix**:
```bash
lsof -ti :5001 | xargs kill -15
sleep 3
bash scripts/deploy_hub_serving.sh
```

---

### Issue 2: Model Artifacts Not Found

**Symptom**: `ModelNotFound` or artifact loading errors

**Workaround**: Verify MLflow tracking server is running

**Manual Fix**:
```bash
# Check tracking server
curl http://localhost:5000

# If not running, start it
mlflow server --host 0.0.0.0 --port 5000 &
```

---

### Issue 3: Inference Timeout

**Symptom**: Requests timeout after 30s

**Workaround**: Increase Gunicorn timeout

**Manual Fix**: Edit `scripts/deploy_hub_serving.sh` and add:
```bash
mlflow models serve \
    ... \
    --timeout 300
```

---

## 🔐 Security Considerations

### 1. Network Access Control

- **Current**: Port 5001 binds to `0.0.0.0` (all interfaces)
- **Security Group**: Should restrict to VPC internal (172.19.0.0/16)
- **Action**: Verify Alibaba Cloud Security Group rule only allows INF server

### 2. No Authentication

- **Current**: No API authentication
- **Risk**: Anyone with network access can send inference requests
- **Mitigation**: Network isolation (VPC only)
- **Future**: Add API key authentication (Task #078)

### 3. Process Management

- **Current**: Using `nohup` with PID tracking
- **Risk**: Process may not restart on server reboot
- **Mitigation**: Manual restart after reboot
- **Future**: Migrate to systemd service (see QUICK_START.md)

---

## 📞 Cross-Team Coordination

### Teams to Notify

1. **MLOps Team**
   - New model serving endpoint available
   - Port 5001 on HUB server
   - Model URI: `models:/stacking_ensemble_task_073/Production`

2. **Infrastructure Team**
   - Firewall rule change needed (if not already open)
   - Port 5001 TCP from 172.19.0.0/16
   - Monitor HUB server resource usage

3. **Trading Team** (Future)
   - INF server integration pending (Task #075)
   - Inference API endpoint: `http://172.19.141.254:5001/invocations`

---

## ✅ Completion Checklist

Use this checklist to confirm synchronization:

**Code Synchronization**:
- [ ] Git repository updated on HUB server
- [ ] All 4 scripts present and executable
- [ ] Scripts pass syntax checks

**Model Synchronization**:
- [ ] Model promoted to Production stage in MLflow
- [ ] Model version recorded in Notion

**Infrastructure Synchronization**:
- [ ] MLflow server running on port 5001
- [ ] Process PID recorded in `logs/mlflow_server.pid`
- [ ] Health endpoint responding

**Security Synchronization**:
- [ ] Firewall rules reviewed (port 5001)
- [ ] Network access confirmed (INF ← HUB)

**Documentation Synchronization**:
- [ ] COMPLETION_REPORT.md created
- [ ] QUICK_START.md created
- [ ] VERIFY_LOG.log archived
- [ ] SYNC_GUIDE.md created (this file)
- [ ] Notion task status updated to "Done"

---

## 📝 Change Log

| Date | Change | Version | Impact |
|------|--------|---------|--------|
| 2026-01-10 | Initial deployment | v1.0 | New model serving infrastructure |

---

## 🔗 Related Documentation

- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md) - Full task report
- [QUICK_START.md](./QUICK_START.md) - Deployment guide
- [VERIFY_LOG.log](./VERIFY_LOG.log) - Audit verification log
- [Task #073 Report](../TASK_073/COMPLETION_REPORT.md) - Model training
- [Infrastructure Document](../../📄%20MT5-CRS%20基础设施资产全景档案.md.md) - Server details

---

**Last Updated**: 2026-01-10
**Protocol**: v4.3 (Zero-Trust Edition)
**Task**: #074
**Deployment Status**: ✅ READY FOR PRODUCTION
