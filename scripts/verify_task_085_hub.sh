#!/bin/bash
# Task #085: HUB Server Verification Script
# Verify cross-node metrics scraping and Prometheus configuration
#
# Execution on HUB (172.19.141.254):
#   bash scripts/verify_task_085_hub.sh
#
# Protocol: v4.3 (Zero-Trust Edition)

set -e

echo "================================================================================"
echo "TASK #085: HUB SERVER VERIFICATION"
echo "Verify Prometheus scrapes INF Sentinel metrics"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

INF_HOST="172.19.141.250"
INF_PORT="8000"
PROMETHEUS_CONFIG="/opt/mt5-crs/config/monitoring/prometheus.yml"

# Step 1: Verify Prometheus configuration
echo "Step 1: Verify Prometheus Configuration"
echo "========================================"
if [ -f "$PROMETHEUS_CONFIG" ]; then
    echo -e "${GREEN}✓ Prometheus config exists${NC}"
    echo "  File: $PROMETHEUS_CONFIG"
    echo ""
    echo "  Checking for sentinel-metrics job:"

    if grep -q "job_name: 'sentinel-metrics'" "$PROMETHEUS_CONFIG"; then
        echo -e "    ${GREEN}✓ Job 'sentinel-metrics' is defined${NC}"
    else
        echo -e "    ${RED}✗ Job 'sentinel-metrics' is missing${NC}"
        echo "    Add the following to prometheus.yml:"
        echo ""
        echo "    - job_name: 'sentinel-metrics'"
        echo "      static_configs:"
        echo "        - targets:"
        echo "            - '172.19.141.250:8000'"
        echo ""
    fi

    if grep -q "172.19.141.250:8000" "$PROMETHEUS_CONFIG"; then
        echo -e "    ${GREEN}✓ INF target (172.19.141.250:8000) is configured${NC}"
    else
        echo -e "    ${RED}✗ INF target is not configured${NC}"
    fi

else
    echo -e "${RED}✗ Prometheus config not found${NC}"
    echo "  Expected: $PROMETHEUS_CONFIG"
fi
echo ""

# Step 2: Test connectivity to INF
echo "Step 2: Test Network Connectivity to INF"
echo "========================================"
echo "Attempting to reach INF metrics endpoint..."
if timeout 5 curl -s http://$INF_HOST:$INF_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Can reach INF metrics endpoint${NC}"
    echo "  URL: http://$INF_HOST:$INF_PORT/health"
else
    echo -e "${YELLOW}⚠ Cannot reach INF metrics endpoint${NC}"
    echo "  Troubleshooting:"
    echo "    1. Check if INF is running: ssh $INF_HOST 'pgrep -f sentinel_daemon'"
    echo "    2. Check port 8000 on INF: ssh $INF_HOST 'netstat -tulpn | grep 8000'"
    echo "    3. Check firewall: ssh $INF_HOST 'ufw status'"
    echo "    4. Enable port: ssh $INF_HOST 'sudo ufw allow 8000/tcp'"
fi
echo ""

# Step 3: Fetch metrics from INF
echo "Step 3: Fetch Metrics from INF"
echo "=============================="
if timeout 10 curl -s http://$INF_HOST:$INF_PORT/metrics > /tmp/inf_metrics.txt 2>&1; then
    LINES=$(wc -l < /tmp/inf_metrics.txt)
    echo -e "${GREEN}✓ Successfully fetched metrics from INF${NC}"
    echo "  Retrieved $LINES lines"
    echo ""
    echo "  Sample metrics:"
    grep -v "^#" /tmp/inf_metrics.txt | head -5 || true
else
    echo -e "${YELLOW}⚠ Failed to fetch metrics from INF${NC}"
    echo "  Ensure INF Sentinel Daemon is running with --metrics-port 8000"
fi
echo ""

# Step 4: Verify Prometheus is running
echo "Step 4: Check Prometheus Service"
echo "================================"
if pgrep -f "prometheus" > /dev/null; then
    echo -e "${GREEN}✓ Prometheus is running${NC}"
    pgrep -f "prometheus" | head -3
else
    echo -e "${YELLOW}⚠ Prometheus is not running${NC}"
    echo "  Start Prometheus with Docker or systemd:"
    echo "    docker restart prometheus"
fi
echo ""

# Step 5: Check Prometheus targets
echo "Step 5: Prometheus Targets Status"
echo "================================="
if command -v curl &> /dev/null; then
    # Try to fetch targets from Prometheus API (if available on localhost)
    if timeout 5 curl -s http://localhost:9090/api/v1/targets > /tmp/prom_targets.json 2>&1; then
        echo -e "${GREEN}✓ Prometheus API is responding${NC}"
        echo ""
        echo "  Active targets:"
        cat /tmp/prom_targets.json | grep -o '"job":"[^"]*"' | sort | uniq || true
    else
        echo -e "${YELLOW}⚠ Prometheus API not accessible on localhost:9090${NC}"
        echo "  Prometheus may be on different port or not running"
    fi
else
    echo "  curl not available, skipping API check"
fi
echo ""

# Step 6: Reload Prometheus configuration
echo "Step 6: Reload Prometheus Configuration"
echo "======================================"
echo "After verifying Prometheus config is correct, reload it:"
echo ""
if command -v docker &> /dev/null && docker ps | grep -q prometheus; then
    echo -e "  ${GREEN}Using Docker:${NC}"
    echo "    docker exec <prometheus_container> kill -HUP 1"
elif command -v systemctl &> /dev/null; then
    echo -e "  ${GREEN}Using systemd:${NC}"
    echo "    sudo systemctl reload prometheus"
else
    echo "  Send SIGHUP to Prometheus process:"
    echo "    sudo kill -HUP <prometheus_pid>"
fi
echo ""

# Step 7: Wait for metrics to appear
echo "Step 7: Verify Metrics in Prometheus"
echo "===================================="
echo "After reloading Prometheus (wait 30-60 seconds), check:"
echo ""
echo "  1. Prometheus Dashboard:"
echo "     - Visit: http://localhost:9090/targets"
echo "     - Look for job_name: 'sentinel-metrics'"
echo "     - Status should be 'UP'"
echo ""
echo "  2. Query metrics:"
echo "     - Visit: http://localhost:9090/graph"
echo "     - Search for: sentinel_trading_cycles_total"
echo "     - Should see metrics with labels: instance='inf-sentinel', component='trading'"
echo ""
echo "  3. Grafana Dashboard:"
echo "     - If configured, check dashboard for Sentinel Trading metrics"
echo ""

# Step 8: Verification Summary
echo "================================================================================"
echo "VERIFICATION SUMMARY"
echo "================================================================================"
echo ""
echo "HUB Prometheus Configuration Checklist:"
echo "  [ ] prometheus.yml contains 'sentinel-metrics' job"
echo "  [ ] INF target (172.19.141.250:8000) is configured"
echo "  [ ] Can reach INF metrics endpoint"
echo "  [ ] Prometheus service is running"
echo "  [ ] Prometheus targets show INF as 'UP'"
echo "  [ ] Metrics appear in Prometheus query interface"
echo ""
echo "================================================================================"
echo ""
echo "Completion next step:"
echo "  Create documentation and commit changes"
echo "  python3 scripts/project_cli.py finish"
echo ""
echo "================================================================================"
