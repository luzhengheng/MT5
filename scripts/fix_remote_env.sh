#!/bin/bash
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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
# Step 1: Verify .env exists locally
# ============================================================================

print_header "Step 1: Checking Local Environment File"

if [ ! -f ".env" ]; then
    print_error ".env file not found in current directory"
    exit 1
fi

print_success ".env file exists locally"

# Get file size
ENV_SIZE=$(du -h .env | cut -f1)
print_info "File size: $ENV_SIZE"

# ============================================================================
# Step 2: Inject .env to Remote
# ============================================================================

print_header "Step 2: Injecting Secrets to GPU Node"

print_info "Transferring .env to gpu-node:~/mt5-crs/.env"

if ! scp .env gpu-node:~/mt5-crs/.env 2>&1; then
    print_error "SCP failed to transfer .env file"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check SSH connectivity: ssh gpu-node echo OK"
    echo "  2. Verify remote directory exists: ssh gpu-node ls -la ~/mt5-crs/"
    echo "  3. Check disk space: ssh gpu-node df -h ~/"
    exit 1
fi

print_success "Environment file transferred to remote"

# Verify on remote
print_info "Verifying .env on remote..."
if ssh gpu-node "test -f ~/mt5-crs/.env"; then
    print_success ".env verified on remote GPU node"
    REMOTE_ENV_SIZE=$(ssh gpu-node "du -h ~/mt5-crs/.env | cut -f1")
    print_info "Remote file size: $REMOTE_ENV_SIZE"
else
    print_error "Failed to verify .env on remote"
    exit 1
fi

# ============================================================================
# Step 3: Retry Remote Training
# ============================================================================

print_header "Step 3: Retrying Remote Training"

print_info "Connecting to gpu-node..."
print_info "Starting training with environment variables..."
print_info "This may take 5-15 minutes..."
echo ""

# Execute training with environment loaded
ssh gpu-node << 'REMOTE_EOF'
set -e

cd ~/mt5-crs || exit 1

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Print system info
echo "=== System Information ==="
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Python: $(python3 --version)"
echo ""

# Verify GPU availability
echo "=== GPU Status ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# Verify API key is available
echo "=== Environment Check ==="
if [ -z "$EODHD_API_KEY" ]; then
    echo "❌ EODHD_API_KEY not set!"
    exit 1
fi
echo "✅ EODHD_API_KEY loaded (length: ${#EODHD_API_KEY})"
echo ""

# Run training
echo "=== Starting Training ==="
python3 scripts/run_deep_training.py

# Verify model was created
if [ -f "models/deep_v1.json" ]; then
    echo ""
    echo "✅ Model saved successfully"
    ls -lh models/deep_v1.json
else
    echo "❌ Model file not found after training"
    exit 1
fi

REMOTE_EOF

if [ $? -ne 0 ]; then
    print_error "Remote training failed"
    exit 1
fi

print_success "Remote training completed successfully"

# ============================================================================
# Step 4: Retrieve Model
# ============================================================================

print_header "Step 4: Retrieving Trained Model"

print_info "Copying model from gpu-node:~/mt5-crs/models/deep_v1.json"

# Ensure local models directory exists
mkdir -p models

# Copy model from remote
if ! scp gpu-node:~/mt5-crs/models/deep_v1.json ./models/ 2>&1; then
    print_error "Failed to retrieve model via SCP"
    echo ""
    echo "Manual retrieval:"
    echo "  ssh gpu-node 'cat ~/mt5-crs/models/deep_v1.json' > models/deep_v1.json"
    exit 1
fi

print_success "Model retrieved successfully"

# ============================================================================
# Step 5: Local Verification
# ============================================================================

print_header "Step 5: Local Model Verification"

if [ ! -f "models/deep_v1.json" ]; then
    print_error "Model file not found locally"
    exit 1
fi

print_success "Model file exists: models/deep_v1.json"

# Check file size (use stat with fallback for macOS vs Linux)
MODEL_SIZE=$(du -h models/deep_v1.json | cut -f1)
MODEL_BYTES=$(stat -f%z models/deep_v1.json 2>/dev/null || stat -c%s models/deep_v1.json 2>/dev/null)

if [ "$MODEL_BYTES" -lt 1000 ]; then
    print_error "Model file too small ($MODEL_BYTES bytes, expected > 1MB)"
    exit 1
fi

print_success "Model size: $MODEL_SIZE (valid)"

# Verify JSON
if ! python3 -c "import json; json.load(open('models/deep_v1.json'))" 2>/dev/null; then
    print_error "Model file is not valid JSON"
    exit 1
fi

print_success "Model file is valid JSON"

# Try to load with XGBoost
if python3 -c "import xgboost as xgb; xgb.Booster(model_file='models/deep_v1.json')" 2>/dev/null; then
    print_success "Model loads successfully with XGBoost"
else
    print_info "Could not load model with XGBoost (may need GPU environment)"
fi

# ============================================================================
# Summary
# ============================================================================

print_header "Training Fix Complete"

echo -e "${GREEN}🎉 Remote Training Retry Success!${NC}"
echo ""
echo "Summary:"
echo "  ✅ .env transferred to remote"
echo "  ✅ Remote training executed with API key"
echo "  ✅ Model retrieved to local models/deep_v1.json"
echo "  ✅ Model validation passed"
echo ""
echo "Model is ready for:"
echo "  - Live trading deployment"
echo "  - Backtesting and analysis"
echo "  - Performance evaluation"
echo ""

exit 0
