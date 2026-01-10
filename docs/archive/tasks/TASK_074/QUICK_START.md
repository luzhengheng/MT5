# Task #074: Quick Start Guide
## Model Serving Deployment on HUB Server

**Target Audience**: DevOps Engineers, MLOps Engineers
**Execution Node**: HUB Server (172.19.141.254)
**Estimated Time**: 10-15 minutes
**Prerequisites**: SSH access to HUB server, MLflow Model Registry configured

---

## 🚀 Quick Deployment (3 Steps)

### Step 1: Promote Model to Production

```bash
# Connect to any machine with MLflow access
ssh hub  # or ssh root@www.crestive-code.com

# Navigate to project directory
cd /opt/mt5-crs

# Promote model from Staging to Production
python3 scripts/promote_model.py --model-name stacking_ensemble_task_073
```

**✅ Success Indicator**:
```
✓ Model promotion complete!
  Model: stacking_ensemble_task_073
  Version: 1
  Stage: Production
  Run ID: <run_id>

Production Model URI:
  models:/stacking_ensemble_task_073/Production
```

---

### Step 2: Deploy MLflow Model Server

```bash
# Still on HUB server
bash scripts/deploy_hub_serving.sh
```

**What This Does**:
1. Validates environment (MLflow, Python)
2. Verifies model exists in Production stage
3. Checks port 5001 availability
4. Starts MLflow server (binding to 0.0.0.0:5001)
5. Runs health check loop
6. Displays server information

**✅ Success Indicator**:
```
======================================================================
✓ MLflow Model Server Deployed Successfully!
======================================================================

Server Details:
  Model:      stacking_ensemble_task_073
  Stage:      Production
  URI:        models:/stacking_ensemble_task_073/Production
  PID:        <process_id>

Endpoints:
  Health:     http://0.0.0.0:5001/ping
  Inference:  http://0.0.0.0:5001/invocations
  Version:    http://0.0.0.0:5001/version

Access from INF server:
  curl http://172.19.141.254:5001/ping
```

---

### Step 3: Verify Deployment

```bash
# Test locally on HUB
python3 scripts/test_inference_local.py --host localhost --port 5001
```

**✅ Success Indicator**:
```
================================================================================
Test Summary
================================================================================
✓ PASS   | Health Check
✓ PASS   | Version Check
✓ PASS   | Generate Test Data
✓ PASS   | Model Inference
✓ PASS   | Validate Predictions

✓ All tests passed!
================================================================================
```

---

## 📊 Server Management

### Check Server Status

```bash
# Check if process is running
cat logs/mlflow_server.pid
ps -p $(cat logs/mlflow_server.pid)

# Check server logs
tail -f logs/mlflow_serving_*.log

# Test health endpoint
curl http://localhost:5001/ping
```

### Stop Server

```bash
# Graceful shutdown
kill $(cat logs/mlflow_server.pid)

# Force shutdown (if needed)
kill -9 $(cat logs/mlflow_server.pid)

# Or use script to kill all on port 5001
lsof -ti :5001 | xargs kill -15
```

### Restart Server

```bash
# Stop existing server
kill $(cat logs/mlflow_server.pid)

# Wait for port to be released
sleep 3

# Restart
bash scripts/deploy_hub_serving.sh
```

---

## 🔍 Troubleshooting

### Problem: Port 5001 Already in Use

**Symptom**:
```
⚠ Warning: Port 5001 is already in use
```

**Solution**:
The script automatically handles this by terminating the existing process:
1. Sends SIGTERM (graceful shutdown)
2. Waits 3 seconds
3. If still running, sends SIGKILL (force)

**Manual Override** (if script fails):
```bash
# Find process using port 5001
lsof -i :5001

# Kill it manually
kill -15 <PID>  # Graceful
# or
kill -9 <PID>   # Force
```

---

### Problem: Model Not Found in Production

**Symptom**:
```
✗ Error: No model found in Production stage
Please run: python3 scripts/promote_model.py
```

**Solution**:
```bash
# Check model stages
python3 -c "
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
versions = client.search_model_versions(
    filter_string=\"name='stacking_ensemble_task_073'\"
)

for v in versions:
    print(f'Version {v.version}: Stage={v.current_stage}')
"

# If model is in Staging, promote it
python3 scripts/promote_model.py
```

---

### Problem: Health Check Failing

**Symptom**:
```
✗ Server health check failed after 30 retries
```

**Solutions**:

1. **Check logs**:
```bash
tail -100 logs/mlflow_serving_*.log
```

2. **Check Python dependencies**:
```bash
python3 -c "import mlflow; print(mlflow.__version__)"
python3 -c "import lightgbm; print(lightgbm.__version__)"
python3 -c "import torch; print(torch.__version__)"
```

3. **Check model artifacts**:
```bash
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
        print(f"Production Model: Version {v.version}")
        print(f"Source: {v.source}")
        print(f"Run ID: {v.run_id}")

        # Check if artifacts exist
        run = client.get_run(v.run_id)
        print(f"Artifact URI: {run.info.artifact_uri}")
EOF
```

4. **Manual server start** (for debugging):
```bash
# Start in foreground to see errors
mlflow models serve \
    -m "models:/stacking_ensemble_task_073/Production" \
    -p 5001 \
    --host 0.0.0.0 \
    --no-conda \
    --workers 2
```

---

### Problem: Inference Returns Errors

**Symptom**:
```
✗ Inference failed (status: 500)
```

**Debug Steps**:

1. **Check input format**:
```bash
# Test with curl
curl -X POST http://localhost:5001/invocations \
  -H 'Content-Type: application/json' \
  -d '{
    "dataframe_split": {
      "columns": ["X_tabular", "X_sequential"],
      "data": [[...], [...]]
    }
  }'
```

2. **Check model signature**:
```bash
python3 << 'EOF'
import mlflow

model_uri = "models:/stacking_ensemble_task_073/Production"
model = mlflow.pyfunc.load_model(model_uri)

print("Model metadata:", model.metadata)
if hasattr(model.metadata, 'signature'):
    print("Signature:", model.metadata.signature)
EOF
```

3. **Check server logs**:
```bash
grep -i error logs/mlflow_serving_*.log
grep -i traceback logs/mlflow_serving_*.log
```

---

## 🌐 Network Configuration

### HUB Server Details

| Parameter | Value |
|-----------|-------|
| **Hostname** | `sg-nexus-hub-01` |
| **Internal IP** | `172.19.141.254` |
| **Public Domain** | `www.crestive-code.com` |
| **VPC Network** | `172.19.0.0/16` (Singapore) |
| **Model Server Port** | `5001` |
| **Binding** | `0.0.0.0` (all interfaces) |

### Security Group Rules

Ensure port 5001 is accessible from INF server:

```bash
# On HUB server, check firewall (if using firewalld)
sudo firewall-cmd --list-all

# Add rule if needed
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

### Test Cross-Server Connectivity (from INF)

```bash
# On INF server (172.19.141.250)
curl http://172.19.141.254:5001/ping

# Expected response: {"status": "ok"}
```

---

## 📈 Performance Tuning

### Increase Workers

Edit `scripts/deploy_hub_serving.sh`:
```bash
WORKERS="4"  # Increase from 2 to 4 for higher concurrency
```

### Adjust Timeout

If inference is slow, increase Gunicorn timeout:
```bash
mlflow models serve \
    -m "models:/stacking_ensemble_task_073/Production" \
    -p 5001 \
    --host 0.0.0.0 \
    --no-conda \
    --workers 2 \
    --timeout 300  # Add timeout parameter
```

---

## 🔐 Security Considerations

### 1. Network Isolation

- Model server is bound to `0.0.0.0` to allow INF access
- Ensure firewall rules only allow traffic from trusted sources:
  - INF server: `172.19.141.250`
  - HUB local: `127.0.0.1`

### 2. No Authentication (Current)

⚠️ **Warning**: Current setup has NO authentication. Suitable for internal VPC only.

**For production hardening** (future):
- Add API key authentication
- Use HTTPS/TLS
- Implement rate limiting
- Add request logging/auditing

### 3. Process Management

Current setup uses `nohup` for background execution. For production:

**Recommended**: Use systemd service

Create `/etc/systemd/system/mlflow-serving.service`:
```ini
[Unit]
Description=MLflow Model Serving
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mt5-crs
ExecStart=/usr/bin/mlflow models serve -m models:/stacking_ensemble_task_073/Production -p 5001 --host 0.0.0.0 --no-conda --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mlflow-serving
sudo systemctl start mlflow-serving
sudo systemctl status mlflow-serving
```

---

## 📝 Verification Checklist

Use this checklist to verify successful deployment:

- [ ] Model promoted to Production stage
- [ ] MLflow server process running (check PID file)
- [ ] Health endpoint responds with 200 OK
- [ ] Version endpoint returns model information
- [ ] Inference endpoint accepts test requests
- [ ] Predictions have correct shape (N, 3)
- [ ] Probabilities sum to 1.0
- [ ] Server accessible from localhost
- [ ] (Future) Server accessible from INF server

---

## 🆘 Emergency Procedures

### Complete Reset

If everything fails, perform a complete reset:

```bash
# 1. Kill all MLflow processes
pkill -f mlflow

# 2. Kill anything on port 5001
lsof -ti :5001 | xargs kill -9

# 3. Clean up PID files
rm -f logs/mlflow_server.pid

# 4. Check MLflow tracking server
ps aux | grep mlflow

# 5. Restart from scratch
bash scripts/deploy_hub_serving.sh
```

### Rollback to Previous Model

If the current Production model is causing issues:

```bash
python3 << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
model_name = "stacking_ensemble_task_073"

# List all versions
versions = client.search_model_versions(f"name='{model_name}'")

for v in sorted(versions, key=lambda x: int(x.version), reverse=True):
    print(f"Version {v.version}: {v.current_stage} (Run: {v.run_id})")

# Promote previous version
# client.transition_model_version_stage(
#     name=model_name,
#     version="1",  # Specify version to promote
#     stage="Production"
# )
EOF
```

---

## 📞 Support

For issues or questions:
- Check logs: `logs/mlflow_serving_*.log`
- Review audit trail: `docs/archive/tasks/TASK_074/VERIFY_LOG.log`
- Consult completion report: `docs/archive/tasks/TASK_074/COMPLETION_REPORT.md`

---

**Last Updated**: 2026-01-10
**Protocol**: v4.3 (Zero-Trust Edition)
**Task**: #074
