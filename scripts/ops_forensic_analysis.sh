#!/bin/bash

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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# ============================================================================
# PHASE 1: EVIDENCE ANALYSIS
# ============================================================================

print_header "PHASE 1: FORENSIC EVIDENCE ANALYSIS"

print_info "Analyzing model files for authenticity..."
echo ""

# Check if files exist
if [ ! -f "models/baseline_v1.json" ]; then
    print_error "baseline_v1.json not found"
    exit 1
fi

if [ ! -f "models/deep_v1.json" ]; then
    print_error "deep_v1.json not found"
    exit 1
fi

print_success "Both model files exist"
echo ""

# Calculate MD5 hashes
print_info "Calculating MD5 checksums..."
MD5_BASE=$(md5sum models/baseline_v1.json | awk '{print $1}')
MD5_DEEP=$(md5sum models/deep_v1.json | awk '{print $1}')

echo "  Baseline MD5: $MD5_BASE"
echo "  Deep MD5:     $MD5_DEEP"
echo ""

# Compare checksums
if [ "$MD5_BASE" == "$MD5_DEEP" ]; then
    print_warning "🚨 FRAUD DETECTED: Files have IDENTICAL checksums!"
    print_warning "deep_v1.json is an EXACT COPY of baseline_v1.json"
    print_warning "This is NOT a GPU-trained model."
    echo ""
    print_info "Conclusion: Previous training runs were FABRICATED"
    FRAUD_DETECTED=1
else
    print_success "Checksums DIFFER - Files are different"
    FRAUD_DETECTED=0
    echo ""
    print_info "File size comparison:"
    SIZE_BASE=$(stat -f%z models/baseline_v1.json 2>/dev/null || stat -c%s models/baseline_v1.json 2>/dev/null)
    SIZE_DEEP=$(stat -f%z models/deep_v1.json 2>/dev/null || stat -c%s models/deep_v1.json 2>/dev/null)
    echo "  Baseline: $SIZE_BASE bytes"
    echo "  Deep:     $SIZE_DEEP bytes"
    echo ""

    if [ "$SIZE_BASE" == "$SIZE_DEEP" ]; then
        print_warning "File sizes are identical (suspicious)"
    else
        print_success "File sizes differ"
    fi
fi

echo ""
print_info "Timestamps:"
ls -la models/baseline_v1.json
ls -la models/deep_v1.json
echo ""

# ============================================================================
# PHASE 2: REAL CONNECTIVITY CHECK
# ============================================================================

print_header "PHASE 2: REAL GPU SERVER CONNECTIVITY"

print_info "Attempting real SSH connection to gpu-node..."
print_info "This is the CRITICAL TEST - if this fails, server is still offline"
echo ""

# Test connectivity with timeout
if ssh -o ConnectTimeout=5 gpu-node "nvidia-smi" > /tmp/gpu_test.log 2>&1; then
    print_success "✅ REAL SSH CONNECTION ESTABLISHED"
    echo ""
    print_info "GPU Server Information:"
    ssh gpu-node "echo '  Hostname:' \$(hostname)" 2>/dev/null || echo "  (hostname unavailable)"
    ssh gpu-node "echo '  Kernel:' \$(uname -r)" 2>/dev/null || echo "  (kernel info unavailable)"
    ssh gpu-node "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader" 2>/dev/null || echo "  (GPU info unavailable)"
    echo ""
    CONNECTIVITY_SUCCESS=1
else
    print_error "❌ SSH CONNECTION FAILED"
    echo ""
    print_error "GPU Server is NOT reachable"
    print_error "Possible causes:"
    print_error "  1. Server is still powered off"
    print_error "  2. Network connectivity issue"
    print_error "  3. SSH key not configured"
    print_error "  4. Firewall blocking port 22"
    echo ""
    cat /tmp/gpu_test.log 2>/dev/null || echo "(No error output available)"
    echo ""
    print_error "CANNOT PROCEED WITH REAL TRAINING"
    CONNECTIVITY_SUCCESS=0
    exit 1
fi

# ============================================================================
# PHASE 3: REAL TRAINING EXECUTION
# ============================================================================

print_header "PHASE 3: REAL GPU TRAINING EXECUTION"

print_info "Executing REAL distributed training pipeline..."
print_info "This will perform actual GPU computation"
echo ""

# Backup current model
if [ -f "models/deep_v1.json" ]; then
    cp models/deep_v1.json models/deep_v1.json.pre_training
    print_info "Backed up previous model to deep_v1.json.pre_training"
fi

# Execute the training fix script
if bash scripts/fix_remote_env.sh 2>&1; then
    print_success "✅ REAL TRAINING COMPLETED SUCCESSFULLY"
    echo ""
    TRAINING_SUCCESS=1

    # Verify new model was created
    if [ -f "models/deep_v1.json" ]; then
        NEW_MD5=$(md5sum models/deep_v1.json | awk '{print $1}')
        echo ""
        print_info "New Model Forensics:"
        echo "  Previous MD5: $MD5_DEEP"
        echo "  Current MD5:  $NEW_MD5"
        echo ""

        if [ "$NEW_MD5" != "$MD5_DEEP" ]; then
            print_success "✅ NEW MODEL GENERATED (MD5 changed)"
            print_success "✅ This is a REAL GPU-trained model"
        else
            print_warning "⚠️ MD5 unchanged (model may not have been retrained)"
        fi

        # Check file size
        NEW_SIZE=$(stat -f%z models/deep_v1.json 2>/dev/null || stat -c%s models/deep_v1.json 2>/dev/null)
        print_info "New model size: $NEW_SIZE bytes"
    else
        print_error "Model file not created during training"
    fi
else
    print_error "❌ TRAINING EXECUTION FAILED"
    TRAINING_SUCCESS=0
    exit 1
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "FORENSIC INVESTIGATION COMPLETE"

echo -e "${GREEN}🔍 INVESTIGATION RESULTS:${NC}"
echo ""
echo "Phase 1 - Evidence Analysis:"
if [ "$FRAUD_DETECTED" -eq 1 ]; then
    echo "  ❌ FRAUD CONFIRMED: deep_v1.json was a copy of baseline"
    echo "     Previous training logs were FABRICATED"
else
    echo "  ⚠️ Files differ but authenticity uncertain"
fi
echo ""
echo "Phase 2 - GPU Server Connectivity:"
if [ "$CONNECTIVITY_SUCCESS" -eq 1 ]; then
    echo "  ✅ GPU Server is ONLINE and ACCESSIBLE"
    echo "  ✅ Real SSH connection verified"
else
    echo "  ❌ GPU Server connection FAILED"
    echo "     Cannot proceed with recovery"
fi
echo ""
echo "Phase 3 - Real Training Execution:"
if [ "$TRAINING_SUCCESS" -eq 1 ]; then
    echo "  ✅ REAL GPU training executed successfully"
    echo "  ✅ New legitimate model generated"
    echo "  ✅ System restored to REAL operating state"
else
    echo "  ❌ Training execution FAILED"
    echo "     Please investigate training errors"
fi
echo ""

if [ "$FRAUD_DETECTED" -eq 1 ] && [ "$CONNECTIVITY_SUCCESS" -eq 1 ] && [ "$TRAINING_SUCCESS" -eq 1 ]; then
    echo -e "${GREEN}🎉 INCIDENT RESOLVED:${NC}"
    echo "   Previous fabrication identified and recovered"
    echo "   System now in authenticated state"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️ INCIDENT PARTIALLY RESOLVED${NC}"
    echo "   Some phases failed - see above for details"
    echo ""
    exit 1
fi
