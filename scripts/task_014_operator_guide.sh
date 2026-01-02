#!/bin/bash
# Task #014 Operator Quick Reference Guide
# 用途: 指导操作员完成远程部署和验证

set -e

echo "=================================================="
echo "Task #014 Operator Guide"
echo "=================================================="
echo ""
echo "This guide will walk you through the remote deployment"
echo "and verification steps for Task #014."
echo ""

# Check if we're on the right branch
echo "[1/5] Checking Git Status..."
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (current: $BRANCH)"
else
    echo "✓ On main branch"
fi

# Show pending deliverables
echo ""
echo "[2/5] Pending Deliverables:"
echo "  - Feast Registry (data/registry.db)"
echo "  - Remote verification logs"
echo ""

# Ask for confirmation
echo "[3/5] Ready to proceed?"
echo "  Press Ctrl+C to cancel or Enter to continue..."
read

# Sync to HUB
echo ""
echo "[4/5] Syncing to HUB node..."
if [ -f "./scripts/maintenance/sync_nodes.sh" ]; then
    ./scripts/maintenance/sync_nodes.sh
    echo "✓ Sync completed"
else
    echo "✘ sync_nodes.sh not found"
    exit 1
fi

# Provide SSH commands
echo ""
echo "[5/5] Next Steps (Manual):"
echo ""
echo "On HUB node (www.crestive-code.com):"
echo "  ssh root@www.crestive-code.com"
echo "  cd /opt/mt5-crs"
echo "  redis-cli ping                    # Verify Redis"
echo "  feast apply                       # Initialize Feast"
echo "  ls -lh data/registry.db          # Verify registry"
echo ""
echo "On INF node (www.crestive.net):"
echo "  ssh root@www.crestive.net"
echo "  cd /opt/mt5-crs"
echo "  python3 src/utils/bridge_dependency.py"
echo ""
echo "After verification:"
echo "  python3 scripts/audit_current_task.py"
echo ""
echo "=================================================="
