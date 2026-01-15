#!/bin/bash
# Global Data Asset Audit Executor - Task #110
# Protocol: v4.3 (Zero-Trust Edition)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/VERIFY_LOG.log"

echo "=================================="
echo "Task #110: Global Data Asset Audit"
echo "Protocol: v4.3 (Zero-Trust Edition)"
echo "=================================="
echo ""

# Change to project directory
cd "$PROJECT_ROOT"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check if required dependencies are available
echo "Checking dependencies..."
python3 -c "import pandas" 2>/dev/null && echo "  ✓ pandas available" || echo "  ⚠ pandas not available (non-critical)"
python3 -c "import pyarrow" 2>/dev/null && echo "  ✓ pyarrow available" || echo "  ⚠ pyarrow not available (non-critical)"
echo ""

# Run the inventory audit
echo "Starting inventory audit..."
echo ""

python3 scripts/audit_inventory.py

AUDIT_RESULT=$?

echo ""
echo "=================================="
if [ $AUDIT_RESULT -eq 0 ]; then
    echo "✓ Audit completed successfully"
else
    echo "✗ Audit failed with code: $AUDIT_RESULT"
fi
echo "=================================="

# Display key evidence for zero-trust protocol
echo ""
echo "Physical Evidence Summary:"
echo "  Log file: $LOG_FILE"
echo "  Data Map: docs/archive/tasks/TASK_110_DATA_AUDIT/DATA_MAP.json"
echo "  Report: docs/archive/tasks/TASK_110_DATA_AUDIT/DATA_INVENTORY_REPORT.md"
echo ""

exit $AUDIT_RESULT
