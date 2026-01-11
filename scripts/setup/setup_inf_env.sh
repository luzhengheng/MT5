#!/bin/bash
# -*- coding: utf-8 -*-
#
# Task #075: INF Environment Setup Script
#
# Initializes the INF server (Brain) with minimal dependencies required for:
# - HTTP requests to HUB (model inference)
# - ZMQ communication with GTW (trading commands)
# - Lightweight execution environment
#
# This script should be executed on INF server (172.19.141.250)
#
# Usage:
#   bash scripts/setup_inf_env.sh
#
# Protocol v4.3 (Zero-Trust Edition)

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REQUIRED_PACKAGES=(
    "requests"
    "pyzmq"
    "pandas"
    "numpy"
    "schedule"
)

# Print header
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Task #075: INF Environment Setup${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Step 1: Validate we're on INF server
echo -e "${YELLOW}[Step 1] Validating execution environment...${NC}"

CURRENT_IP=$(hostname -I | awk '{print $1}')
HOSTNAME=$(hostname)

echo -e "  Current hostname: ${HOSTNAME}"
echo -e "  Current IP: ${CURRENT_IP}"

if [[ "$CURRENT_IP" =~ ^172\.19\. ]]; then
    echo -e "${GREEN}✓ Running in Singapore VPC (172.19.x.x network)${NC}"
elif [[ "$CURRENT_IP" =~ ^172\.23\. ]]; then
    echo -e "${YELLOW}⚠ Warning: Running in Guangzhou VPC (172.23.x.x)${NC}"
    echo -e "${YELLOW}  This script is intended for INF server (172.19.141.250)${NC}"
    echo -e "${YELLOW}  Continuing anyway...${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Not in expected VPC${NC}"
    echo -e "${YELLOW}  Expected: 172.19.x.x (Singapore)${NC}"
    echo -e "${YELLOW}  Current: ${CURRENT_IP}${NC}"
    echo -e "${YELLOW}  Continuing anyway...${NC}"
fi
echo ""

# Step 2: Check Python installation
echo -e "${YELLOW}[Step 2] Checking Python installation...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Error: Python3 not found${NC}"
    echo -e "${YELLOW}  Please install Python 3.9 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Python installed: ${PYTHON_VERSION}${NC}"
echo ""

# Step 3: Check pip installation
echo -e "${YELLOW}[Step 3] Checking pip installation...${NC}"

if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠ pip3 not found, attempting to install...${NC}"
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}✗ Failed to install pip${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✓ pip3 available${NC}"
echo ""

# Step 4: Install required packages
echo -e "${YELLOW}[Step 4] Installing required Python packages...${NC}"
echo -e "${BLUE}Packages: ${REQUIRED_PACKAGES[*]}${NC}"
echo ""

for package in "${REQUIRED_PACKAGES[@]}"; do
    echo -e "${YELLOW}Installing ${package}...${NC}"

    # Try to import package first
    if python3 -c "import ${package}" 2>/dev/null; then
        echo -e "${GREEN}✓ ${package} already installed${NC}"
    else
        # Install package
        pip3 install "${package}" --quiet || {
            echo -e "${RED}✗ Failed to install ${package}${NC}"
            exit 1
        }
        echo -e "${GREEN}✓ ${package} installed${NC}"
    fi
done
echo ""

# Step 5: Verify installations
echo -e "${YELLOW}[Step 5] Verifying package installations...${NC}"

python3 << 'EOF'
import sys

packages = {
    'requests': 'HTTP client',
    'zmq': 'ZeroMQ messaging (pyzmq)',
    'pandas': 'Data manipulation',
    'numpy': 'Numerical computing',
    'schedule': 'Task scheduling'
}

all_ok = True
for package, description in packages.items():
    try:
        __import__(package)
        print(f"✓ {package:12} - {description}")
    except ImportError as e:
        print(f"✗ {package:12} - FAILED: {e}")
        all_ok = False

if not all_ok:
    print("\n❌ Some packages failed to import")
    sys.exit(1)
else:
    print("\n✅ All packages verified")
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Package verification failed${NC}"
    exit 1
fi
echo ""

# Step 6: Check network connectivity to HUB
echo -e "${YELLOW}[Step 6] Testing connectivity to HUB server...${NC}"

HUB_HOST="172.19.141.254"
HUB_PORT="5001"

echo -e "  Target: ${HUB_HOST}:${HUB_PORT}"

# Try telnet if available
if command -v telnet &> /dev/null; then
    echo -e "${YELLOW}  Testing with telnet (timeout: 5s)...${NC}"

    # Use timeout to prevent hanging
    timeout 5 bash -c "echo quit | telnet ${HUB_HOST} ${HUB_PORT}" 2>&1 | grep -q "Connected" && {
        echo -e "${GREEN}✓ HUB port ${HUB_PORT} is accessible${NC}"
    } || {
        echo -e "${YELLOW}⚠ HUB port ${HUB_PORT} connection test inconclusive${NC}"
        echo -e "${YELLOW}  This may be normal if MLflow server isn't started yet${NC}"
    }
else
    # Fallback to nc (netcat)
    if command -v nc &> /dev/null; then
        echo -e "${YELLOW}  Testing with nc (timeout: 5s)...${NC}"

        nc -zv -w 5 ${HUB_HOST} ${HUB_PORT} 2>&1 | grep -q "succeeded\|open" && {
            echo -e "${GREEN}✓ HUB port ${HUB_PORT} is accessible${NC}"
        } || {
            echo -e "${YELLOW}⚠ HUB port ${HUB_PORT} not accessible${NC}"
            echo -e "${YELLOW}  Verify HUB server is running: ssh hub 'ps aux | grep mlflow'${NC}"
        }
    else
        echo -e "${YELLOW}⚠ telnet and nc not available, skipping port test${NC}"
    fi
fi
echo ""

# Step 7: Check network connectivity to GTW
echo -e "${YELLOW}[Step 7] Testing connectivity to GTW server...${NC}"

GTW_HOST="172.19.141.255"
GTW_PORT="5555"

echo -e "  Target: ${GTW_HOST}:${GTW_PORT}"

if command -v nc &> /dev/null; then
    nc -zv -w 5 ${GTW_HOST} ${GTW_PORT} 2>&1 | grep -q "succeeded\|open" && {
        echo -e "${GREEN}✓ GTW port ${GTW_PORT} is accessible${NC}"
    } || {
        echo -e "${YELLOW}⚠ GTW port ${GTW_PORT} not accessible${NC}"
        echo -e "${YELLOW}  Verify GTW server is running${NC}"
    }
else
    echo -e "${YELLOW}⚠ nc not available, skipping GTW port test${NC}"
fi
echo ""

# Step 8: Create necessary directories
echo -e "${YELLOW}[Step 8] Creating directory structure...${NC}"

DIRS=(
    "logs"
    "src/infra"
    "docs/archive/tasks/TASK_075"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓ Created: ${dir}${NC}"
    else
        echo -e "  ${dir} already exists"
    fi
done
echo ""

# Step 9: Test handshake script
echo -e "${YELLOW}[Step 9] Verifying handshake script...${NC}"

if [ -f "src/infra/handshake.py" ]; then
    echo -e "${GREEN}✓ src/infra/handshake.py exists${NC}"

    # Check syntax
    python3 -m py_compile src/infra/handshake.py 2>&1 && {
        echo -e "${GREEN}✓ Handshake script syntax valid${NC}"
    } || {
        echo -e "${RED}✗ Handshake script has syntax errors${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠ src/infra/handshake.py not found${NC}"
    echo -e "${YELLOW}  This file should be created as part of Task #075${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}✅ INF Environment Setup Complete!${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo -e "${BLUE}Installed Packages:${NC}"
for package in "${REQUIRED_PACKAGES[@]}"; do
    echo -e "  ✓ ${package}"
done
echo ""
echo -e "${BLUE}Network Status:${NC}"
echo -e "  HUB: ${HUB_HOST}:${HUB_PORT} (Model Serving)"
echo -e "  GTW: ${GTW_HOST}:${GTW_PORT} (ZMQ Gateway)"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Ensure HUB model server is running:"
echo -e "     ssh hub 'bash scripts/deploy_hub_serving.sh'"
echo ""
echo -e "  2. Run connectivity test:"
echo -e "     python3 src/infra/handshake.py"
echo ""
echo -e "  3. Review test results and troubleshoot if needed"
echo ""
echo -e "${BLUE}======================================================================${NC}"

exit 0
