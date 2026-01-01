# Task #027.02: Force Model Switch & Final Validation

**Status**: Implementation Phase
**Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
**Objective**: Force update live trading configuration to use deep_v1.json model and verify end-to-end execution

---

## Executive Summary

The live trading configuration (`config/live_strategies.yaml`) still references the old `baseline_v1.json` model instead of the newly trained `deep_v1.json` model from Tasks #026.01-03. This task forces the configuration update and validates the complete end-to-end pipeline with the new model.

This is a critical operational task that ensures live trading uses the latest GPU-trained model rather than the baseline.

---

## Context

### Previous State
- Task #025.01: Live trading configuration created (points to `baseline_v1.json`)
- Task #026.01-03: GPU training pipeline created and fixed
- **Problem**: Configuration not automatically updated to use new model
- **Result**: Live trading would use stale model instead of trained model

### Current Issue
- `config/live_strategies.yaml` line 27: `model_path: models/baseline_v1.json`
- New model available: `models/deep_v1.json` (trained in Tasks #026.01-03)
- Need to force update and verify integration

### Goal
1. Update configuration to use `deep_v1.json`
2. Verify update was successful
3. Run end-to-end validation test
4. Confirm live trading can load the new model

---

## Implementation Details

### Step 1: Force Configuration Update

**Command**:
```bash
sed -i 's/baseline_v1.json/deep_v1.json/g' config/live_strategies.yaml
```

**What Gets Changed**:
- Line 27: `model_path: models/baseline_v1.json` → `model_path: models/deep_v1.json`
- Any other references to `baseline_v1.json` in the file (if they exist)

**Why `sed` Instead of Manual Edit**:
- Atomic operation (prevents partial updates)
- Clear audit trail
- Scriptable for automation
- Idempotent (safe to run multiple times)

### Step 2: Verification

**Command**:
```bash
grep "deep_v1.json" config/live_strategies.yaml
```

**Expected Output**:
```
model_path: models/deep_v1.json
```

**Verification Checks**:
- File exists: `config/live_strategies.yaml`
- Contains: `deep_v1.json` string
- Model file exists: `models/deep_v1.json`
- Model file size > 1MB (actual trained model)

### Step 3: End-to-End Test

**Command**:
```bash
python3 scripts/test_end_to_end.py
```

**What Gets Tested**:
- Configuration loading (YAML parsing)
- Model loading (XGBoost loads `deep_v1.json`)
- Feature data availability (Feature Store connection)
- Signal generation (Model inference on test data)
- Risk management validation (Position sizing calculations)
- Integration test (Full pipeline from data → signal → trade decision)

**Expected Output**:
- No errors during model loading
- Console shows: "Loaded model: deep_v1.json"
- Test passes with model inference results
- Risk limits validated successfully

---

## Operational Force Switch Script

### File: `scripts/ops_force_switch.sh`

```bash
#!/bin/bash
set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${CYAN}$1${NC}"
    echo "================================================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# ============================================================================
# Step 1: Verify Configuration File Exists
# ============================================================================

print_header "Step 1: Verifying Configuration File"

CONFIG_FILE="config/live_strategies.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

print_success "Configuration file exists: $CONFIG_FILE"

# Check current model reference
CURRENT_MODEL=$(grep "model_path:" "$CONFIG_FILE" | head -1)
print_info "Current configuration: $CURRENT_MODEL"

# ============================================================================
# Step 2: Verify New Model Exists
# ============================================================================

print_header "Step 2: Verifying New Model File"

MODEL_FILE="models/deep_v1.json"

if [ ! -f "$MODEL_FILE" ]; then
    print_error "New model file not found: $MODEL_FILE"
    exit 1
fi

print_success "New model file exists: $MODEL_FILE"

# Check file size
MODEL_SIZE=$(du -h "$MODEL_FILE" | cut -f1)
MODEL_BYTES=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null)

if [ "$MODEL_BYTES" -lt 1000000 ]; then
    print_error "Model file too small ($MODEL_BYTES bytes, expected > 1MB)"
    exit 1
fi

print_success "Model size valid: $MODEL_SIZE"

# ============================================================================
# Step 3: Force Configuration Update
# ============================================================================

print_header "Step 3: Forcing Configuration Update"

print_info "Replacing baseline_v1.json with deep_v1.json..."

# Backup original file
cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
print_info "Backup created: ${CONFIG_FILE}.bak"

# Force update using sed
sed -i.bak2 's/baseline_v1.json/deep_v1.json/g' "$CONFIG_FILE"

print_success "Configuration updated"

# ============================================================================
# Step 4: Verification
# ============================================================================

print_header "Step 4: Verifying Configuration Update"

if grep -q "deep_v1.json" "$CONFIG_FILE"; then
    print_success "✓ Config now references deep_v1.json"
else
    print_error "Failed to update configuration"
    # Restore from backup
    mv "${CONFIG_FILE}.bak" "$CONFIG_FILE"
    print_error "Restored from backup"
    exit 1
fi

# Verify no old reference remains
if grep -q "baseline_v1" "$CONFIG_FILE"; then
    print_error "Old baseline_v1 reference still exists"
    exit 1
fi

print_success "✓ No baseline_v1 references remain"

# Show updated line
print_info "Updated model path:"
grep "model_path:" "$CONFIG_FILE"

# ============================================================================
# Step 5: End-to-End Test
# ============================================================================

print_header "Step 5: Running End-to-End Validation Test"

print_info "Executing: python3 scripts/test_end_to_end.py"
echo ""

if ! python3 scripts/test_end_to_end.py 2>&1; then
    print_error "End-to-end test failed"
    exit 1
fi

print_success "End-to-end test passed"

# ============================================================================
# Summary
# ============================================================================

print_header "Force Switch Complete"

echo -e "${GREEN}🎉 Model Switch to deep_v1.json Success!${NC}"
echo ""
echo "Summary:"
echo "  ✅ Configuration backup created"
echo "  ✅ baseline_v1.json replaced with deep_v1.json"
echo "  ✅ Verification passed (grep confirmed new model)"
echo "  ✅ End-to-end test passed"
echo ""
echo "Live trading is now configured to use:"
echo "  - Model: deep_v1.json (GPU-trained on NVIDIA A10)"
echo "  - Asset: EURUSD"
echo "  - Risk: Conservative (0.01 lot, 2% drawdown)"
echo ""
echo "Backup file saved to: ${CONFIG_FILE}.bak"
echo "Ready for live deployment!"
echo ""

exit 0
```

---

## Execution Flow

### Phase 1: Pre-flight Checks
- Verify configuration file exists
- Verify new model file exists
- Check model file size (> 1MB)

### Phase 2: Configuration Update
- Create backup of original configuration
- Use sed to replace all `baseline_v1.json` with `deep_v1.json`
- Atomic operation prevents partial updates

### Phase 3: Post-Update Verification
- Confirm `deep_v1.json` appears in config
- Confirm `baseline_v1.json` no longer appears
- Display updated configuration line

### Phase 4: End-to-End Testing
- Execute `test_end_to_end.py`
- Verify model loads successfully
- Validate signal generation
- Confirm risk management
- Test complete pipeline integration

### Phase 5: Summary and Ready State
- Display completion status
- Show backup file location
- Confirm ready for live deployment

---

## Error Handling

### Configuration File Missing
**Symptom**: "Configuration file not found"
**Resolution**:
```bash
ls -la config/live_strategies.yaml
# If missing, restore from git or Task #025.01 output
```

### New Model Missing
**Symptom**: "New model file not found: models/deep_v1.json"
**Resolution**:
```bash
# Verify model was trained successfully
ls -lh models/deep_v1.json

# If missing, run Task #026.03 fix script
bash scripts/fix_remote_env.sh
```

### Update Failed
**Symptom**: "Failed to update configuration"
**Resolution**:
```bash
# Check backup exists
ls -la config/live_strategies.yaml.bak

# Manual update
sed -i 's/baseline_v1.json/deep_v1.json/g' config/live_strategies.yaml

# Verify
grep "deep_v1.json" config/live_strategies.yaml
```

### End-to-End Test Failed
**Symptom**: "test_end_to_end.py" error
**Resolution**:
```bash
# Run test with verbose output
python3 scripts/test_end_to_end.py -v

# Check model loads
python3 -c "import xgboost as xgb; xgb.Booster(model_file='models/deep_v1.json')"

# Check configuration is valid YAML
python3 -c "import yaml; yaml.safe_load(open('config/live_strategies.yaml'))"
```

---

## Success Criteria

**Minimum Requirements**:
1. ✅ `grep "deep_v1.json" config/live_strategies.yaml` returns match
2. ✅ `grep "baseline_v1" config/live_strategies.yaml` returns no match
3. ✅ `test_end_to_end.py` completes without errors
4. ✅ Console output shows "Loaded model: deep_v1.json"

**Extended Verification**:
1. ✅ Configuration backup created and preserved
2. ✅ Model file size verified (> 1MB)
3. ✅ End-to-end test validates full pipeline
4. ✅ Risk management verified
5. ✅ No stderr errors in test output

---

## Integration Points

### Previous Tasks
- **Task #025.01**: Created live_strategies.yaml (will be updated by this task)
- **Task #026.01-03**: Trained and validated deep_v1.json model

### Future Tasks
- **Live Deployment**: Use updated configuration for actual trading
- **Monitoring**: Track model performance with new deep_v1.json
- **Retraining**: Periodic retraining to update model

---

## Files Created/Modified

### New Files
- `scripts/ops_force_switch.sh` - Force switch script
- `docs/TASK_027_02_PLAN.md` - This documentation

### Modified Files
- `config/live_strategies.yaml` - Updated to use deep_v1.json
- `scripts/audit_current_task.py` - Add Task #027.02 audit section (TBD)

### Backup Files (Created During Execution)
- `config/live_strategies.yaml.bak` - Backup of original configuration

---

## Security and Safety

### Configuration Changes
- **Atomic**: sed command updates all occurrences in one operation
- **Reversible**: Backup file preserves original configuration
- **Auditable**: Clear before/after states for verification
- **Testable**: End-to-end test validates changes before deployment

### Model Validation
- **File size check**: Ensures actual model, not empty file
- **XGBoost load test**: Confirms model format is valid
- **Inference test**: Validates model can make predictions
- **Risk management**: Confirms controls are active

---

## References

- sed manual: `man sed`
- grep manual: `man grep`
- XGBoost: https://xgboost.readthedocs.io/

---

## Document Information

- **Created**: Task #027.02: Force Model Switch & Final Validation
- **Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
- **Status**: Implementation Phase
- **Version**: 1.0

---
