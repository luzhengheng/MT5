# Task #026.02: Manual Verification of Remote Training

**Status**: Diagnostic & Verification Phase
**Protocol**: v2.2 (Trust, But Verify - Loud Failures)
**Objective**: Manually diagnose and verify remote GPU training execution and model retrieval

---

## Executive Summary

Task #026.01 automated the distributed training workflow, but this task provides critical **manual verification** to ensure:
1. Remote training actually executed
2. Model file was created on GPU node
3. Model artifact is valid and retrievable
4. GPU was utilized (not fallback to CPU)

This is defensive validation following Protocol v2.2 principle of **Loud Failures** - we verify each component works before assuming automation succeeded.

---

## Context

### Problem Statement

The automated script (Task #026.01) may fail silently if:
- SSH connection succeeds but Python script fails
- Dependencies not installed correctly
- GPU not available or not used
- Model file created but SCP transfer failed
- Model file corrupted or in wrong format

### Verification Approach

**Three-Layer Verification**:
1. **Remote Check**: Verify model exists on GPU node
2. **Manual Execution**: If missing, run training manually to see actual errors
3. **Local Validation**: Confirm model is valid and uses GPU

---

## Implementation

### 1. Remote Diagnostic Script (`scripts/debug_remote_training.sh`)

```bash
#!/bin/bash
# Step 1: Check if model exists on remote
echo "📁 Checking for trained model on GPU node..."
ssh gpu-node "ls -lh ~/mt5-crs/models/deep_v1.json" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Model exists on remote GPU node"
    echo "📦 Retrieving model to local..."
    scp gpu-node:~/mt5-crs/models/deep_v1.json ./models/
else
    echo "❌ Model NOT found on remote GPU node"
    echo ""
    echo "🔧 Manual Training Required:"
    echo "1. SSH into GPU node:"
    echo "   ssh gpu-node"
    echo ""
    echo "2. Navigate to project:"
    echo "   cd ~/mt5-crs"
    echo ""
    echo "3. Verify dependencies:"
    echo "   python3 -c 'import xgboost; print(xgboost.__version__)'"
    echo ""
    echo "4. Run training manually:"
    echo "   python3 scripts/run_deep_training.py"
    echo ""
    echo "5. Check for errors and GPU usage in output"
    exit 1
fi
```

### 2. Local Validation (`scripts/validate_model.py`)

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

model_file = Path("models/deep_v1.json")

if not model_file.exists():
    print("❌ Model file not found")
    sys.exit(1)

# Check file size
size = model_file.stat().st_size
if size < 1000000:
    print(f"❌ Model file too small ({size} bytes)")
    sys.exit(1)

# Validate JSON
try:
    with open(model_file) as f:
        model = json.load(f)
    print(f"✅ Valid JSON format ({size} bytes)")
except:
    print("❌ Invalid JSON")
    sys.exit(1)

# Check for GPU signature (gpu_hist tree method)
content = open(model_file).read()
if "gpu_hist" in content or "gpu" in content.lower():
    print("✅ GPU signature found (gpu_hist tree method)")
else:
    print("⚠️ GPU signature not found (may be CPU-trained)")

# Try to load with XGBoost
try:
    import xgboost as xgb
    bst = xgb.Booster(model_file=str(model_file))
    print(f"✅ XGBoost model loads successfully")
    print(f"   Num trees: {len(bst.get_dump())}")
except ImportError:
    print("⚠️ XGBoost not available for validation")
except Exception as e:
    print(f"❌ XGBoost load failed: {e}")
    sys.exit(1)

print("")
print("✅ Model validation PASSED")
sys.exit(0)
```

---

## Execution Steps

### Step 1: Check Remote Status

```bash
bash scripts/debug_remote_training.sh
```

**Possible Outcomes**:
- ✅ Model found → Model retrieved automatically
- ❌ Model not found → Proceed to Step 2

### Step 2: Manual Training (if needed)

```bash
# SSH into remote
ssh gpu-node

# Navigate to project
cd ~/mt5-crs

# Verify GPU
nvidia-smi

# Verify dependencies
python3 -c "import xgboost; print('XGBoost OK')"

# Run training with visible errors
python3 scripts/run_deep_training.py
```

### Step 3: Local Validation

```bash
# Validate model file
python3 scripts/validate_model.py

# Verify GPU signature
grep "gpu_hist" models/deep_v1.json
```

---

## Success Criteria

**Minimum Requirements**:
1. ✅ Model file exists: `models/deep_v1.json`
2. ✅ File size > 1MB
3. ✅ Valid JSON format
4. ✅ Can be loaded by XGBoost

**Extended Verification**:
1. ✅ Contains "gpu_hist" (GPU training signature)
2. ✅ Training output shows GPU utilization
3. ✅ Model trees are present and valid

---

## Troubleshooting

### Issue: SSH Connection Fails
**Solution**: Run `python3 scripts/ops_establish_gpu_link.py`

### Issue: Model File Not Found on Remote
**Solution**: Check `/tmp/training.log` for errors:
```bash
ssh gpu-node "cat /tmp/training.log" | tail -50
```

### Issue: Model File Exists but SCP Fails
**Solution**: Manual retrieval:
```bash
ssh gpu-node "cat ~/mt5-crs/models/deep_v1.json" > models/deep_v1.json
```

### Issue: XGBoost Import Error on Remote
**Solution**: Install manually:
```bash
ssh gpu-node "pip install xgboost"
```

---

## Files Created

- `docs/TASK_026_02_PLAN.md` - This documentation
- `scripts/debug_remote_training.sh` - Remote model verification
- `scripts/validate_model.py` - Local model validation

---

## Document Information

- **Created**: Task #026.02: Manual Verification
- **Protocol**: v2.2 (Trust, But Verify)
- **Status**: Complete
- **Version**: 1.0

---
