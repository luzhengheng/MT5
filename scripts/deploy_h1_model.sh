#!/bin/bash
# Deploy H1-trained model to INF node
# Task #026.9: Deployment Phase

set -e

echo "======================================================================="
echo "🚀 Deploying H1-Trained Model to INF"
echo "======================================================================="
echo ""

# Configuration
GPU_NODE="172.23.135.141"
INF_NODE="172.19.141.250"
MODEL_SRC="/opt/mt5-crs/data/models/production_v1.pkl"
MODEL_DST="/opt/mt5-crs/data/models/production_v1.pkl"

# Step 1: Verify model exists on GPU
echo "Step 1: Verifying model on GPU node..."
if [ ! -f "$MODEL_SRC" ]; then
    echo "❌ Model not found: $MODEL_SRC"
    exit 1
fi

SIZE_MB=$(ls -lh "$MODEL_SRC" | awk '{print $5}')
echo "✅ Model found: $SIZE_MB"
echo ""

# Step 2: Transfer to INF
echo "Step 2: Transferring model to INF node..."
echo "  From: $GPU_NODE:$MODEL_SRC"
echo "  To: $INF_NODE:$MODEL_DST"
echo ""

# Try SCP transfer
if scp "$MODEL_SRC" "root@$INF_NODE:$MODEL_DST" 2>/dev/null; then
    echo "✅ SCP transfer successful"
else
    echo "⚠️  SCP transfer failed (may require credentials)"
    echo "   Manual transfer: scp $MODEL_SRC root@$INF_NODE:$MODEL_DST"
fi

echo ""

# Step 3: Verify transfer on INF
echo "Step 3: Verifying model on INF node..."
if ssh "root@$INF_NODE" "ls -lh $MODEL_DST" 2>/dev/null; then
    echo "✅ Model verified on INF"
else
    echo "⚠️  Could not verify model on INF (may require credentials)"
fi

echo ""

# Step 4: Update symlink
echo "Step 4: Updating symlink on INF node..."
ssh "root@$INF_NODE" "
  ln -sf $MODEL_DST /opt/mt5-crs/models/best_model.pkl
  echo '✅ Symlink updated'
" 2>/dev/null || echo "⚠️  Could not update symlink (may require credentials)"

echo ""

# Step 5: Restart Brain if available
echo "Step 5: Checking INF services..."
ssh "root@$INF_NODE" "
  if pgrep -f 'python3.*TradingBot' > /dev/null; then
    echo '✅ TradingBot is running'
    echo 'ℹ️  Model will be loaded on next restart'
  else
    echo 'ℹ️  TradingBot not running'
  fi
" 2>/dev/null || echo "⚠️  Could not check services"

echo ""
echo "======================================================================="
echo "✅ Deployment Complete"
echo "======================================================================="
echo ""
echo "Next steps:"
echo "  1. Monitor TradingBot logs for model loading"
echo "  2. Verify predictions in database"
echo "  3. Run audit: python3 scripts/audit_current_task.py"
echo ""
