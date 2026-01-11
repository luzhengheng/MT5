# Task #026.01: Distributed GPU Training Workflow

**Status**: Implementation Phase
**Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
**Objective**: Automate the sync → train → retrieve loop for distributed XGBoost training on remote GPU node

---

## Executive Summary

This task automates the distributed training workflow for machine learning models on the remote GPU node (Guangzhou Peak A10). The complete loop:

1. **Sync**: `rsync` project code to `gpu-node:~/mt5-crs`
2. **Install**: Remote dependency installation via `pip install -r requirements.txt`
3. **Train**: Execute XGBoost training on GPU via `python3 scripts/run_deep_training.py`
4. **Retrieve**: `scp` the trained model back to local `models/deep_v1.json`
5. **Verify**: Confirm model was successfully trained and retrieved

This enables seamless distributed training while keeping the local development environment synchronized.

---

## Context

### Infrastructure

**Local HUB (Singapore)**:
- Source code and development environment
- `models/` directory for trained models
- `requirements.txt` with all dependencies
- Training orchestration scripts

**Remote GPU Node (Guangzhou)**:
- NVIDIA A10 GPU (compute-optimized)
- Connected via `ssh gpu-node` (Task #026.00)
- Working directory: `~/mt5-crs` (to be synced)
- Model output: `models/deep_v1.json`

### Previous Work

- **Task #026.00**: GPU node SSH connectivity established (`ssh gpu-node` works)
- **Task #016.01**: XGBoost baseline trainer implemented
- **Task #022.01**: Docker deployment with all dependencies defined

### Current State

- SSH access to GPU node is working
- Remote node is idle and ready for training
- Local code is ready for distribution
- Model checkpoint location is known

### Goal

Enable one-command distributed training:
```bash
bash scripts/run_remote_training.sh
```

This should result in:
1. Code synchronized to remote
2. Dependencies installed remotely
3. Training executed on GPU
4. Model retrieved locally
5. Ready for immediate use in live trading

---

## Implementation Details

### 1. Remote Setup Script (`scripts/ops_setup_remote.py`)

**Purpose**: Initialize remote GPU node environment

**Workflow**:
```python
1. Check remote connectivity (ssh gpu-node echo "OK")
2. Create remote directory structure (~/mt5-crs)
3. Install system dependencies (if needed)
4. Install Python dependencies (pip install -r requirements.txt)
5. Verify GPU availability (nvidia-smi)
6. Verify training script availability
```

**Error Handling**:
- Check SSH connectivity before proceeding
- Graceful handling of missing dependencies
- Clear error messages for troubleshooting

### 2. Training Runner (`scripts/run_remote_training.sh`)

**Complete Workflow**:

```bash
#!/bin/bash

# Step 1: Sync code to remote
echo "📁 Syncing code to GPU Node..."
rsync -avz --exclude 'venv' --exclude '.git' --exclude '__pycache__' \
  --exclude '*.pyc' --exclude '.pytest_cache' \
  ./ gpu-node:~/mt5-crs/

# Step 2: Install dependencies and run training
echo "🔥 Triggering Remote Training..."
ssh gpu-node << 'EOF'
cd ~/mt5-crs
pip install -r requirements.txt 2>&1 | tail -5
python3 scripts/run_deep_training.py
EOF

# Step 3: Retrieve trained model
echo "📦 Retrieving Model..."
scp gpu-node:~/mt5-crs/models/deep_v1.json ./models/

# Step 4: Verify
echo "✅ Training Complete!"
if [ -f ./models/deep_v1.json ]; then
  echo "✅ Model available at ./models/deep_v1.json"
  ls -lh ./models/deep_v1.json
else
  echo "❌ Model retrieval failed"
  exit 1
fi
```

**Key Features**:
- Excludes unnecessary files (.git, venv, __pycache__)
- Uses SSH heredoc for complex remote commands
- Shows last 5 lines of pip output (for debugging)
- Verifies model file exists locally
- Returns non-zero exit code on failure

### 3. Training Script (`scripts/run_deep_training.py`)

**Purpose**: Execute XGBoost training on remote GPU

**Implementation** (to be executed remotely):
```python
import xgboost as xgb
import json
from pathlib import Path

# Load training data (from local feature store or database)
X_train, y_train = load_training_data()

# Configure XGBoost for GPU
params = {
    'tree_method': 'gpu_hist',        # Use GPU histogram
    'gpu_id': 0,
    'max_depth': 7,
    'learning_rate': 0.1,
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
}

# Train model
dtrain = xgb.DMatrix(X_train, label=y_train)
model = xgb.train(params, dtrain, num_boost_round=100, verbose_eval=10)

# Save as JSON (portable format)
model.get_booster().save_model('models/deep_v1.json')
print("✅ Model saved: models/deep_v1.json")
```

### 4. Model Retrieval and Verification

**Local Verification** (after scp):
```bash
# Check file exists and has reasonable size
if [ -f models/deep_v1.json ] && [ -s models/deep_v1.json ]; then
  echo "✅ Model file valid"
  wc -l models/deep_v1.json
  head -50 models/deep_v1.json | grep -i "tree\|booster"
else
  echo "❌ Model file missing or empty"
  exit 1
fi
```

---

## Workflow Architecture

```
┌──────────────────────────────────────┐
│  Local HUB (Singapore)                │
│  ~/mt5-crs/                          │
│  - Source code                       │
│  - requirements.txt                  │
│  - scripts/run_remote_training.sh    │
└────────────┬─────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   rsync         (sync code)
      │             │
      └──────┬──────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Remote GPU Node (Guangzhou)          │
│  ~/mt5-crs/ (synced)                 │
│  - Code copied from local            │
│  - Dependencies: pip install         │
│  - Training: python3 run_deep...py   │
│  - Output: models/deep_v1.json       │
└────────────┬─────────────────────────┘
             │
           scp
      (retrieve model)
             │
             ▼
┌──────────────────────────────────────┐
│  Local Models Directory               │
│  models/deep_v1.json                 │
│  (Ready for live trading)            │
└──────────────────────────────────────┘
```

---

## Execution Flow

### Phase 1: Code Synchronization

**rsync Command**:
```bash
rsync -avz --exclude 'venv' --exclude '.git' ./ gpu-node:~/mt5-crs/
```

**Parameters**:
- `-a`: Archive mode (preserves permissions, timestamps)
- `-v`: Verbose (shows progress)
- `-z`: Compression (reduces network bandwidth)
- `--exclude`: Skip unnecessary directories

**What Gets Synced**:
- ✅ Source code (src/)
- ✅ Scripts (scripts/)
- ✅ Configuration (config/)
- ✅ Documentation (docs/)
- ✅ Models (models/ - for reference)
- ✅ requirements.txt
- ❌ Virtual environment (venv/)
- ❌ Git history (.git/)
- ❌ Python cache (__pycache__/)

### Phase 2: Remote Dependency Installation

**pip install on Remote**:
```bash
ssh gpu-node "pip install -r requirements.txt"
```

**Key Dependencies**:
- xgboost (with GPU support)
- pandas, numpy (data handling)
- scikit-learn (preprocessing)
- psycopg2 (database connection)

**Verification**:
```bash
ssh gpu-node "python3 -c 'import xgboost; print(xgboost.__version__)'"
```

### Phase 3: Remote Training

**Training Execution**:
```bash
ssh gpu-node "cd ~/mt5-crs && python3 scripts/run_deep_training.py"
```

**Expected Output**:
```
[10]     training-logloss: 0.45232
[20]     training-logloss: 0.42156
[30]     training-logloss: 0.41023
...
[100]    training-logloss: 0.39856
✅ Model saved: models/deep_v1.json
```

**GPU Utilization**:
- GPU memory: ~2-4GB (depends on batch size)
- Training time: ~5-15 minutes (depends on dataset size)
- GPU utilization: 90-100% (expected for efficient training)

### Phase 4: Model Retrieval

**scp Command**:
```bash
scp gpu-node:~/mt5-crs/models/deep_v1.json ./models/
```

**Local Verification**:
```bash
ls -lh models/deep_v1.json
wc -l models/deep_v1.json
```

**Success Criteria**:
- File exists: `models/deep_v1.json`
- File size > 1MB (actual trained model)
- Readable JSON format
- Contains XGBoost tree structures

---

## Error Handling and Recovery

### SSH Connection Failure

**Symptom**: "ssh: connect to host www.guangzhoupeak.com port 22: Connection refused"

**Resolution**:
1. Verify SSH is running: `ssh gpu-node echo "OK"`
2. Re-run setup: `python3 scripts/ops_establish_gpu_link.py`
3. Check network: `ping www.guangzhoupeak.com`

### rsync Failure

**Symptom**: "rsync: error (23): Partial transfer due to error"

**Resolution**:
1. Check disk space: `ssh gpu-node "df -h ~/"`
2. Check write permissions: `ssh gpu-node "touch ~/test.txt"`
3. Retry rsync with verbose: `rsync -avvz ... gpu-node:~/mt5-crs/`

### pip Install Failure

**Symptom**: "ERROR: pip install failed"

**Resolution**:
1. Check Python: `ssh gpu-node "python3 --version"`
2. Check pip: `ssh gpu-node "pip3 --version"`
3. Update pip: `ssh gpu-node "pip install --upgrade pip"`
4. Install manually: `ssh gpu-node "pip install xgboost"`

### Training Failure

**Symptom**: "Error loading data" or "GPU not found"

**Resolution**:
1. Check GPU: `ssh gpu-node "nvidia-smi"`
2. Check data: `ssh gpu-node "ls -la ~/mt5-crs/data/"`
3. Check logs: `ssh gpu-node "tail -50 training.log"`

### scp Failure

**Symptom**: "scp: error sending"

**Resolution**:
1. Check model exists remotely: `ssh gpu-node "ls -lh ~/mt5-crs/models/deep_v1.json"`
2. Check local permissions: `ls -ld ./models/`
3. Manual retrieval: `ssh gpu-node "cat ~/mt5-crs/models/deep_v1.json" > models/deep_v1.json`

---

## Success Criteria

**Minimum Requirements**:
1. ✅ `run_remote_training.sh` exists and is executable
2. ✅ `deep_v1.json` appears in local `models/` directory
3. ✅ Model file is valid JSON with content

**Extended Verification**:
1. ✅ Training ran on remote host (check logs for Guangzhou timestamps)
2. ✅ GPU was utilized during training (nvidia-smi shows usage)
3. ✅ Model file size > 1MB
4. ✅ Model can be loaded: `xgb.Booster(model_file='models/deep_v1.json')`
5. ✅ Training time < 30 minutes

---

## Audit Checklist

- [ ] `docs/TASK_026_01_PLAN.md` exists
- [ ] `scripts/run_remote_training.sh` exists and is executable
- [ ] Script has rsync step
- [ ] Script has SSH training step
- [ ] Script has scp retrieval step
- [ ] Script has verification step
- [ ] Training completed on remote GPU node
- [ ] Model file `models/deep_v1.json` exists locally
- [ ] Model file is valid (>1MB, JSON format)

---

## Benefits

After this task:

1. **Automated Training**: One-command distributed training
2. **GPU Acceleration**: XGBoost on NVIDIA A10 (10x faster than CPU)
3. **Seamless Integration**: Model automatically available for live trading
4. **Monitoring Ready**: Can add prometheus metrics to training loop
5. **Scalable**: Easy to extend to multiple GPU nodes

---

## Files Modified/Created

### New Files
- `docs/TASK_026_01_PLAN.md` - This documentation
- `scripts/run_remote_training.sh` - Training orchestration script
- `scripts/ops_setup_remote.py` - Remote environment setup (optional)

### Modified Files
- `scripts/audit_current_task.py` - Added Task #026.01 audit section

### System Changes
- `~/mt5-crs/` on remote (synced via rsync)
- `~/.ssh/config` entry for `gpu-node` (from Task #026.00)

---

## References

- XGBoost GPU Training: https://xgboost.readthedocs.io/en/latest/gpu/index.html
- rsync Manual: `man rsync`
- SSH Remote Commands: `man ssh`
- SCP Manual: `man scp`

---

## Future Extensions

- **Task #027.00**: Multi-GPU load balancing (distribute across multiple GPU nodes)
- **Task #028.00**: Training monitoring and metrics (Prometheus integration)
- **Task #029.00**: Automated retraining pipeline (triggered by new data)
- **Task #030.00**: Model versioning and A/B testing

---

## Document Information

- **Created**: Task #026.01: Distributed GPU Training Workflow
- **Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
- **Status**: Complete
- **Version**: 1.0

---
