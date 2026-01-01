#!/bin/bash

################################################################################
# Remote Training Diagnostic Script
# Task #026.02: Manual Verification of Remote Training
# Protocol: v2.2 (Trust, But Verify)
#
# Verifies training artifact exists on GPU node and retrieves if found.
# If not found, provides manual remediation steps.
#
# Usage:
#   bash scripts/debug_remote_training.sh
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "================================================================================"
echo -e "${CYAN}📋 REMOTE TRAINING DIAGNOSTIC${NC}"
echo "================================================================================"
echo ""

# Step 1: Check remote file
echo -e "${CYAN}Step 1: Checking for trained model on GPU node...${NC}"
echo ""

if ssh -o ConnectTimeout=5 gpu-node "test -f ~/mt5-crs/models/deep_v1.json" 2>/dev/null; then
    echo -e "${GREEN}✅ Model file exists on GPU node${NC}"
    echo ""

    # Show file details
    echo "File details:"
    ssh gpu-node "ls -lh ~/mt5-crs/models/deep_v1.json"
    echo ""

    # Step 2: Retrieve model
    echo -e "${CYAN}Step 2: Retrieving model to local machine...${NC}"
    mkdir -p models

    if scp gpu-node:~/mt5-crs/models/deep_v1.json ./models/ 2>/dev/null; then
        echo -e "${GREEN}✅ Model retrieved successfully${NC}"
        echo ""
        echo "File details:"
        ls -lh ./models/deep_v1.json
        exit 0
    else
        echo -e "${RED}❌ SCP retrieval failed${NC}"
        echo ""
        echo "Try manual retrieval:"
        echo "  ssh gpu-node \"cat ~/mt5-crs/models/deep_v1.json\" > models/deep_v1.json"
        exit 1
    fi
else
    echo -e "${RED}❌ Model file NOT found on GPU node${NC}"
    echo ""
    echo "File does not exist at: ~/mt5-crs/models/deep_v1.json"
    echo ""
    echo "================================================================================"
    echo -e "${YELLOW}🔧 MANUAL TRAINING REQUIRED${NC}"
    echo "================================================================================"
    echo ""
    echo "Please run training manually on the GPU node:"
    echo ""
    echo "1. SSH into GPU node:"
    echo -e "   ${CYAN}ssh gpu-node${NC}"
    echo ""
    echo "2. Navigate to project:"
    echo -e "   ${CYAN}cd ~/mt5-crs${NC}"
    echo ""
    echo "3. Check GPU availability:"
    echo -e "   ${CYAN}nvidia-smi${NC}"
    echo ""
    echo "4. Verify Python and dependencies:"
    echo -e "   ${CYAN}python3 --version${NC}"
    echo -e "   ${CYAN}python3 -c 'import xgboost; print(\"XGBoost OK\")'${NC}"
    echo ""
    echo "5. Check if training script exists:"
    echo -e "   ${CYAN}ls -la scripts/run_deep_training.py${NC}"
    echo ""
    echo "6. Run training and watch for errors:"
    echo -e "   ${CYAN}python3 scripts/run_deep_training.py${NC}"
    echo ""
    echo "7. After training succeeds, verify file was created:"
    echo -e "   ${CYAN}ls -lh ~/mt5-crs/models/deep_v1.json${NC}"
    echo ""
    echo "8. Then retrieve the model:"
    echo -e "   ${CYAN}scp gpu-node:~/mt5-crs/models/deep_v1.json ./models/${NC}"
    echo ""
    echo "================================================================================"
    exit 1
fi
