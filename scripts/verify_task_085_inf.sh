#!/bin/bash
# Task #085: INF Server Verification Script
# Verify that Sentinel Daemon metrics endpoint is operational on INF (172.19.141.250)
#
# Execution on INF:
#   bash scripts/verify_task_085_inf.sh
#
# Protocol: v4.3 (Zero-Trust Edition)

set -e

echo "================================================================================"
echo "TASK #085: INF SERVER VERIFICATION"
echo "Expose Sentinel Metrics for HUB Monitoring"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if Sentinel Daemon is running
echo "Step 1: Check Sentinel Daemon Process"
echo "======================================="
if pgrep -f "sentinel_daemon.py" > /dev/null; then
    echo -e "${GREEN}✓ Sentinel Daemon is running${NC}"
    pgrep -f "sentinel_daemon.py" | head -5
else
    echo -e "${YELLOW}⚠ Sentinel Daemon is not running${NC}"
    echo "  You can start it with:"
    echo "  python3 src/strategy/sentinel_daemon.py --metrics-port 8000"
fi
echo ""

# Step 2: Check port 8000
echo "Step 2: Check Port 8000 (Metrics Endpoint)"
echo "=========================================="
if netstat -tulpn 2>/dev/null | grep -q ":8000 "; then
    echo -e "${GREEN}✓ Port 8000 is listening${NC}"
    netstat -tulpn | grep ":8000" || true
else
    echo -e "${YELLOW}⚠ Port 8000 is not listening${NC}"
    echo "  Start Sentinel Daemon with --metrics-port 8000"
fi
echo ""

# Step 3: Test /health endpoint
echo "Step 3: Test Health Endpoint"
echo "============================"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    echo -e "${GREEN}✓ Health endpoint is responding${NC}"
    echo "  Response: $HEALTH"
else
    echo -e "${YELLOW}⚠ Health endpoint is not responding${NC}"
    echo "  Ensure Sentinel Daemon is running"
fi
echo ""

# Step 4: Test /metrics endpoint
echo "Step 4: Test Metrics Endpoint"
echo "============================="
if curl -s http://localhost:8000/metrics > /tmp/sentinel_metrics.txt 2>&1; then
    LINES=$(wc -l < /tmp/sentinel_metrics.txt)
    echo -e "${GREEN}✓ Metrics endpoint is responding${NC}"
    echo "  Retrieved $LINES lines of metrics"

    # Check for required metrics
    echo ""
    echo "  Checking for sentinel metrics:"
    if grep -q "sentinel_trading_cycles_total" /tmp/sentinel_metrics.txt; then
        echo -e "    ${GREEN}✓ sentinel_trading_cycles_total${NC}"
    else
        echo -e "    ${RED}✗ sentinel_trading_cycles_total (missing)${NC}"
    fi

    if grep -q "sentinel_prediction_requests_total" /tmp/sentinel_metrics.txt; then
        echo -e "    ${GREEN}✓ sentinel_prediction_requests_total${NC}"
    else
        echo -e "    ${RED}✗ sentinel_prediction_requests_total (missing)${NC}"
    fi

    if grep -q "sentinel_trading_signals_total" /tmp/sentinel_metrics.txt; then
        echo -e "    ${GREEN}✓ sentinel_trading_signals_total${NC}"
    else
        echo -e "    ${RED}✗ sentinel_trading_signals_total (missing)${NC}"
    fi

    if grep -q "sentinel_daemon_uptime_seconds" /tmp/sentinel_metrics.txt; then
        echo -e "    ${GREEN}✓ sentinel_daemon_uptime_seconds${NC}"
    else
        echo -e "    ${RED}✗ sentinel_daemon_uptime_seconds (missing)${NC}"
    fi

else
    echo -e "${YELLOW}⚠ Metrics endpoint is not responding${NC}"
    echo "  Ensure Sentinel Daemon is running on port 8000"
fi
echo ""

# Step 5: Sample metrics output
echo "Step 5: Sample Metrics Output"
echo "============================="
if [ -f /tmp/sentinel_metrics.txt ]; then
    echo "First 10 metric lines:"
    grep -v "^#" /tmp/sentinel_metrics.txt | head -10 || true
fi
echo ""

# Step 6: Network accessibility
echo "Step 6: Network Configuration"
echo "============================="
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "Local IP: $LOCAL_IP"
echo ""
echo "For HUB to scrape metrics, ensure:"
echo "  1. Port 8000 is open: ufw allow 8000/tcp"
echo "  2. Firewall allows traffic from HUB (172.19.141.254)"
echo "  3. Metrics endpoint is accessible at: http://$LOCAL_IP:8000/metrics"
echo ""

# Step 7: Verification Summary
echo "================================================================================"
echo "VERIFICATION SUMMARY"
echo "================================================================================"
echo ""
echo "INF Sentinel Metrics Checklist:"
echo "  [ ] Port 8000 is listening"
echo "  [ ] /health endpoint responds"
echo "  [ ] /metrics endpoint responds"
echo "  [ ] Prometheus metrics format is correct"
echo "  [ ] Firewall allows port 8000"
echo ""
echo "Next step on HUB (172.19.141.254):"
echo "  bash scripts/verify_task_085_hub.sh"
echo ""
echo "================================================================================"
