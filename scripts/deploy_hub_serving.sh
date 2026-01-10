#!/bin/bash
# -*- coding: utf-8 -*-
#
# Task #074: Deploy Model Serving on HUB Server
#
# Starts MLflow Model Server for the Production stacking ensemble model.
# This script must be executed on HUB server (172.19.141.254).
#
# Critical Configuration:
# - Binds to 0.0.0.0:5001 to allow INF server connections
# - Uses --no-conda for faster startup
# - Deploys Production model URI: models:/stacking_ensemble_task_073/Production
#
# Usage:
#   bash scripts/deploy_hub_serving.sh
#
# Protocol v4.3 (Zero-Trust Edition)

set -euo pipefail  # Exit on error, undefined variable, or pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODEL_NAME="stacking_ensemble_task_073"
MODEL_STAGE="Production"
MODEL_URI="models:/${MODEL_NAME}/${MODEL_STAGE}"
HOST="0.0.0.0"  # CRITICAL: Bind to all interfaces for INF connectivity
PORT="5001"
WORKERS="2"
LOG_FILE="logs/mlflow_serving_$(date +%Y%m%d_%H%M%S).log"

# Print header
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Task #074: Deploy MLflow Model Serving on HUB${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Validate environment
echo -e "${YELLOW}[Step 1] Validating environment...${NC}"

# Check if running on HUB server (optional, remove if not needed)
# CURRENT_IP=$(hostname -I | awk '{print $1}')
# if [[ ! "$CURRENT_IP" =~ ^172\.19\. ]]; then
#     echo -e "${RED}✗ WARNING: Not running on HUB server (expected 172.19.x.x network)${NC}"
#     echo -e "${YELLOW}  Current IP: ${CURRENT_IP}${NC}"
#     echo -e "${YELLOW}  Continuing anyway...${NC}"
# fi

# Check MLflow is installed
if ! command -v mlflow &> /dev/null; then
    echo -e "${RED}✗ Error: MLflow not found${NC}"
    echo -e "${YELLOW}  Please install: pip install mlflow${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MLflow installed${NC}"

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Error: Python3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3 installed${NC}"

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✓ Logs directory ready${NC}"

# Verify model exists in Production
echo ""
echo -e "${YELLOW}[Step 2] Verifying model in Production stage...${NC}"

python3 << EOF
import mlflow
from mlflow.tracking import MlflowClient

try:
    client = MlflowClient()
    versions = client.search_model_versions(
        filter_string="name='${MODEL_NAME}'"
    )

    production_versions = [
        v for v in versions
        if v.current_stage.lower() == 'production'
    ]

    if not production_versions:
        print("${RED}✗ Error: No model found in Production stage${NC}")
        print("${YELLOW}  Please run: python3 scripts/promote_model.py${NC}")
        exit(1)

    version = production_versions[0]
    print(f"${GREEN}✓ Model found in Production: version {version.version}${NC}")
    print(f"${GREEN}  Run ID: {version.run_id}${NC}")
    print(f"${GREEN}  URI: ${MODEL_URI}${NC}")

except Exception as e:
    print(f"${RED}✗ Error validating model: {e}${NC}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# Check if port is already in use
echo ""
echo -e "${YELLOW}[Step 3] Checking port availability...${NC}"

if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Warning: Port ${PORT} is already in use${NC}"
    echo -e "${YELLOW}  Existing process:${NC}"
    lsof -Pi :${PORT} -sTCP:LISTEN
    echo ""

    # Non-interactive: automatically terminate process (graceful first, then force)
    echo -e "${YELLOW}  Auto-terminating existing process (non-interactive mode)...${NC}"
    PID=$(lsof -ti :${PORT})
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}  Sending SIGTERM to PID ${PID}...${NC}"
        kill -15 $PID
        sleep 3

        # Check if process is still running
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}  Process still running, sending SIGKILL...${NC}"
            kill -9 $PID
            sleep 2
        fi

        echo -e "${GREEN}✓ Process ${PID} terminated${NC}"
    else
        echo -e "${RED}✗ Could not identify process PID${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Port ${PORT} is available${NC}"
fi

# Start MLflow Model Server
echo ""
echo -e "${YELLOW}[Step 4] Starting MLflow Model Server...${NC}"
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Model URI:  ${MODEL_URI}"
echo -e "  Host:       ${HOST} (CRITICAL: Accessible from INF server)"
echo -e "  Port:       ${PORT}"
echo -e "  Workers:    ${WORKERS}"
echo -e "  Log file:   ${LOG_FILE}"
echo ""

# Run in background and capture PID
nohup mlflow models serve \
    -m "${MODEL_URI}" \
    -p ${PORT} \
    --host ${HOST} \
    --no-conda \
    --workers ${WORKERS} \
    > "${LOG_FILE}" 2>&1 &

SERVER_PID=$!
echo -e "${GREEN}✓ MLflow server started (PID: ${SERVER_PID})${NC}"

# Save PID to file for easy management
echo ${SERVER_PID} > logs/mlflow_server.pid
echo -e "${GREEN}✓ PID saved to logs/mlflow_server.pid${NC}"

# Wait for server to start
echo ""
echo -e "${YELLOW}[Step 5] Waiting for server to start...${NC}"
sleep 5

# Check if server is running
if ps -p ${SERVER_PID} > /dev/null; then
    echo -e "${GREEN}✓ Server process is running${NC}"
else
    echo -e "${RED}✗ Server failed to start${NC}"
    echo -e "${YELLOW}  Check logs: ${LOG_FILE}${NC}"
    exit 1
fi

# Test server health
echo ""
echo -e "${YELLOW}[Step 6] Testing server health...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:${PORT}/ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is healthy and responding${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo -e "${RED}✗ Server health check failed after ${MAX_RETRIES} retries${NC}"
            echo -e "${YELLOW}  Check logs: ${LOG_FILE}${NC}"
            exit 1
        fi
        echo -e "${YELLOW}  Waiting for server... (${RETRY_COUNT}/${MAX_RETRIES})${NC}"
        sleep 2
    fi
done

# Display server information
echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}✓ MLflow Model Server Deployed Successfully!${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo -e "${BLUE}Server Details:${NC}"
echo -e "  Model:      ${MODEL_NAME}"
echo -e "  Stage:      ${MODEL_STAGE}"
echo -e "  URI:        ${MODEL_URI}"
echo -e "  PID:        ${SERVER_PID}"
echo ""
echo -e "${BLUE}Endpoints:${NC}"
echo -e "  Health:     http://${HOST}:${PORT}/ping"
echo -e "  Inference:  http://${HOST}:${PORT}/invocations"
echo -e "  Version:    http://${HOST}:${PORT}/version"
echo ""
echo -e "${BLUE}Access from INF server:${NC}"
echo -e "  curl http://172.19.141.254:${PORT}/ping"
echo ""
echo -e "${BLUE}Management:${NC}"
echo -e "  View logs:  tail -f ${LOG_FILE}"
echo -e "  Stop:       kill \$(cat logs/mlflow_server.pid)"
echo ""
echo -e "${YELLOW}Note: Server is running in background (nohup)${NC}"
echo -e "${YELLOW}      Use 'kill \$(cat logs/mlflow_server.pid)' to stop${NC}"
echo ""
echo -e "${BLUE}======================================================================${NC}"

exit 0
