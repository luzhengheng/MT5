#!/bin/bash

echo "=========================================="
echo "XGBoost Version Compatibility Check"
echo "=========================================="
echo ""

echo "LOCAL HUB XGBoost:"
pip show xgboost | grep Version
echo ""

echo "GPU NODE XGBoost:"
ssh gpu-node "pip show xgboost | grep Version"
echo ""

# Extract versions and compare
LOCAL_VER=$(pip show xgboost | grep Version | awk '{print $2}')
REMOTE_VER=$(ssh gpu-node "pip show xgboost | grep Version" | awk '{print $2}')

echo "Comparison:"
echo "  Local:  $LOCAL_VER"
echo "  Remote: $REMOTE_VER"
echo ""

if [ "$LOCAL_VER" == "$REMOTE_VER" ]; then
    echo "✅ Versions MATCH"
else
    echo "❌ Version MISMATCH detected"
    echo "   Local $LOCAL_VER != Remote $REMOTE_VER"
    echo ""
    echo "To fix, run: bash scripts/align_xgboost.sh"
fi
