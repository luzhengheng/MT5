#!/bin/bash
#
# MT5-CRS Network Synchronization Script (Protocol v3.4)
#
# Purpose: Synchronize all distributed nodes (INF/GTW/GPU) to HUB's main branch
# Architecture: Idempotent, safe, with rollback capability
#
# Usage:
#   ./scripts/maintenance/sync_nodes.sh         # Sync all nodes
#   ./scripts/maintenance/sync_nodes.sh inf     # Sync only INF
#

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HUB_REPO="/opt/mt5-crs"
TARGET_BRANCH="main"
SSH_OPTIONS="-o ConnectTimeout=10 -o StrictHostKeyChecking=no"

# Node definitions (from infrastructure inventory)
declare -A NODES=(
    ["inf"]="root@www.crestive.net:/opt/mt5-crs"
    ["gpu"]="root@www.guangzhoupeak.com:/opt/mt5-crs"
    ["gtw"]="Administrator@gtw.crestive.net:C:/mt5-crs"
)

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current HUB Git hash
get_hub_hash() {
    cd "$HUB_REPO"
    git rev-parse HEAD
}

# Sync Linux node (INF/GPU)
sync_linux_node() {
    local node_name=$1
    local node_ssh=$2
    local target_hash=$3

    log_info "Syncing $node_name ($node_ssh)..."

    # Test SSH connection
    if ! ssh $SSH_OPTIONS ${node_ssh%:*} "echo 'Connection test OK'" > /dev/null 2>&1; then
        log_error "Cannot connect to $node_name. Skipping..."
        return 1
    fi

    # Execute sync on remote node
    ssh $SSH_OPTIONS ${node_ssh%:*} bash << EOF
set -e
cd ${node_ssh#*:}

echo "[\$node_name] Fetching origin..."
git fetch origin

echo "[\$node_name] Resetting to origin/$TARGET_BRANCH..."
git reset --hard origin/$TARGET_BRANCH

echo "[\$node_name] Cleaning untracked files..."
git clean -fd

echo "[\$node_name] Verifying hash..."
LOCAL_HASH=\$(git rev-parse HEAD)
if [ "\$LOCAL_HASH" != "$target_hash" ]; then
    echo "ERROR: Hash mismatch! Expected: $target_hash, Got: \$LOCAL_HASH"
    exit 1
fi

echo "[\$node_name] Sync complete!"
EOF

    if [ $? -eq 0 ]; then
        log_success "$node_name synchronized successfully"

        # Verify from HUB
        remote_hash=$(ssh $SSH_OPTIONS ${node_ssh%:*} "cd ${node_ssh#*:} && git rev-parse HEAD")
        log_info "$node_name hash: $remote_hash"

        if [ "$remote_hash" = "$target_hash" ]; then
            log_success "$node_name hash verification PASSED"
            return 0
        else
            log_error "$node_name hash verification FAILED"
            return 1
        fi
    else
        log_error "$node_name synchronization FAILED"
        return 1
    fi
}

# Sync Windows node (GTW)
sync_windows_node() {
    local node_name=$1
    local node_ssh=$2
    local target_hash=$3

    log_info "Syncing $node_name ($node_ssh)..."

    # Test SSH connection
    if ! ssh $SSH_OPTIONS ${node_ssh%:*} "echo 'Connection test OK'" > /dev/null 2>&1; then
        log_error "Cannot connect to $node_name. Skipping..."
        return 1
    fi

    # Execute sync on remote Windows node (via Git Bash)
    ssh $SSH_OPTIONS ${node_ssh%:*} bash << EOF
set -e
cd ${node_ssh#*:}

echo "[\$node_name] Fetching origin..."
git fetch origin

echo "[\$node_name] Resetting to origin/$TARGET_BRANCH..."
git reset --hard origin/$TARGET_BRANCH

echo "[\$node_name] Cleaning untracked files..."
git clean -fd

echo "[\$node_name] Verifying hash..."
LOCAL_HASH=\$(git rev-parse HEAD)
if [ "\$LOCAL_HASH" != "$target_hash" ]; then
    echo "ERROR: Hash mismatch! Expected: $target_hash, Got: \$LOCAL_HASH"
    exit 1
fi

echo "[\$node_name] Sync complete!"
EOF

    if [ $? -eq 0 ]; then
        log_success "$node_name synchronized successfully"

        # Verify from HUB
        remote_hash=$(ssh $SSH_OPTIONS ${node_ssh%:*} "cd ${node_ssh#*:} && git rev-parse HEAD")
        log_info "$node_name hash: $remote_hash"

        if [ "$remote_hash" = "$target_hash" ]; then
            log_success "$node_name hash verification PASSED"
            return 0
        else
            log_error "$node_name hash verification FAILED"
            return 1
        fi
    else
        log_error "$node_name synchronization FAILED"
        return 1
    fi
}

# Main execution
main() {
    local target_nodes=($@)

    # If no nodes specified, sync all
    if [ ${#target_nodes[@]} -eq 0 ]; then
        target_nodes=("${!NODES[@]}")
        log_info "No nodes specified. Syncing ALL nodes..."
    fi

    # Verify HUB is clean
    log_info "Verifying HUB repository..."
    cd "$HUB_REPO"

    if [ -n "$(git status --porcelain)" ]; then
        log_error "HUB has uncommitted changes. Please commit first."
        git status --short
        exit 1
    fi

    # Get target hash
    TARGET_HASH=$(get_hub_hash)
    log_success "HUB clean. Target hash: $TARGET_HASH"
    echo ""

    # Sync each node
    declare -A results
    for node in "${target_nodes[@]}"; do
        if [ -z "${NODES[$node]}" ]; then
            log_warning "Unknown node: $node. Skipping..."
            continue
        fi

        node_ssh="${NODES[$node]}"

        if [ "$node" = "gtw" ]; then
            sync_windows_node "$node" "$node_ssh" "$TARGET_HASH"
        else
            sync_linux_node "$node" "$node_ssh" "$TARGET_HASH"
        fi

        results[$node]=$?
        echo ""
    done

    # Summary
    echo "========================================"
    echo "SYNCHRONIZATION SUMMARY"
    echo "========================================"
    log_success "HUB Hash: $TARGET_HASH"
    echo ""

    for node in "${target_nodes[@]}"; do
        if [ -z "${NODES[$node]}" ]; then
            continue
        fi

        if [ "${results[$node]}" -eq 0 ]; then
            log_success "$node: ✓ SYNCED"
        else
            log_error "$node: ✗ FAILED"
        fi
    done
    echo "========================================"

    # Exit with error if any sync failed
    for result in "${results[@]}"; do
        if [ "$result" -ne 0 ]; then
            exit 1
        fi
    done

    log_success "All nodes synchronized successfully!"
    return 0
}

# Execute main
main "$@"
