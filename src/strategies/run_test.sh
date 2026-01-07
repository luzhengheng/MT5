#!/bin/bash
# Simple test runner for breakout strategy
# Captures output to VERIFY_LOG.log for physical verification

echo "========================================================================"
echo "TASK #060: Breakout Strategy Test Runner"
echo "Protocol: v4.3 (Zero-Trust Edition)"
echo "========================================================================"
echo ""

# Execute strategy and capture output
python3 /opt/mt5-crs/src/strategies/strategy_breakout.py 2>&1 | tee -a /opt/mt5-crs/VERIFY_LOG.log

# Capture exit code
EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================================================"
echo "Strategy execution completed with exit code: $EXIT_CODE"
echo "========================================================================"

exit $EXIT_CODE
