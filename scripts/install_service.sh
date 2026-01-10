#!/bin/bash
# -*- coding: utf-8 -*-
#
# Task #077: Systemd Service Installation Script
#
# Installs the MT5 Sentinel Daemon as a Systemd service on INF server.
#
# Usage:
#   bash scripts/install_service.sh
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
PROJECT_ROOT="/opt/mt5-crs"
SERVICE_FILE="${PROJECT_ROOT}/systemd/mt5-sentinel.service"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_NAME="mt5-sentinel.service"

# Print header
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Task #077: MT5 Sentinel Daemon Service Installation${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Step 1: Validate we're on INF server
echo -e "${YELLOW}[Step 1/7] Validating execution environment...${NC}"

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
    echo -e "${YELLOW}  Expected: 172.19.x.x (Singapore INF)${NC}"
    echo -e "${YELLOW}  Current: ${CURRENT_IP}${NC}"
fi
echo ""

# Step 2: Check if running as root
echo -e "${YELLOW}[Step 2/7] Checking permissions...${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ Error: This script must be run as root${NC}"
    echo -e "${YELLOW}  Please run: sudo bash scripts/install_service.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running as root${NC}"
echo ""

# Step 3: Validate service file exists
echo -e "${YELLOW}[Step 3/7] Validating service file...${NC}"

if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}✗ Error: Service file not found${NC}"
    echo -e "${YELLOW}  Expected: ${SERVICE_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Service file exists: ${SERVICE_FILE}${NC}"

# Validate syntax (basic check)
if ! grep -q "ExecStart" "$SERVICE_FILE"; then
    echo -e "${RED}✗ Error: Service file missing ExecStart directive${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Service file syntax OK${NC}"
echo ""

# Step 4: Check dependencies
echo -e "${YELLOW}[Step 4/7] Checking dependencies...${NC}"

# Check Python venv
if [ ! -f "${PROJECT_ROOT}/venv/bin/python" ]; then
    echo -e "${RED}✗ Error: Python venv not found${NC}"
    echo -e "${YELLOW}  Expected: ${PROJECT_ROOT}/venv/bin/python${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python venv found${NC}"

# Check sentinel daemon script
if [ ! -f "${PROJECT_ROOT}/src/strategy/sentinel_daemon.py" ]; then
    echo -e "${RED}✗ Error: Sentinel daemon script not found${NC}"
    echo -e "${YELLOW}  Expected: ${PROJECT_ROOT}/src/strategy/sentinel_daemon.py${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Sentinel daemon script found${NC}"

# Check .env file
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    echo -e "${YELLOW}  Service may fail to start if EODHD_API_TOKEN is not set${NC}"
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi
echo ""

# Step 5: Stop existing service (if running)
echo -e "${YELLOW}[Step 5/7] Stopping existing service (if any)...${NC}"

if systemctl is-active --quiet mt5-sentinel 2>/dev/null; then
    echo -e "${YELLOW}  Stopping mt5-sentinel service...${NC}"
    systemctl stop mt5-sentinel
    echo -e "${GREEN}✓ Service stopped${NC}"
else
    echo -e "  No existing service running"
fi
echo ""

# Step 6: Install service file
echo -e "${YELLOW}[Step 6/7] Installing service file...${NC}"

# Copy service file to systemd directory
cp "$SERVICE_FILE" "${SYSTEMD_DIR}/${SERVICE_NAME}"
echo -e "${GREEN}✓ Service file copied to ${SYSTEMD_DIR}/${SERVICE_NAME}${NC}"

# Set proper permissions
chmod 644 "${SYSTEMD_DIR}/${SERVICE_NAME}"
echo -e "${GREEN}✓ Permissions set (644)${NC}"

# Reload systemd daemon
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"
echo ""

# Step 7: Enable and start service
echo -e "${YELLOW}[Step 7/7] Enabling and starting service...${NC}"

# Enable service (auto-start on boot)
systemctl enable mt5-sentinel
echo -e "${GREEN}✓ Service enabled (will start on boot)${NC}"

# Start service
systemctl start mt5-sentinel
echo -e "${GREEN}✓ Service started${NC}"

# Wait a moment for service to initialize
sleep 2
echo ""

# Verification
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Service Status Verification${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Check if service is active
if systemctl is-active --quiet mt5-sentinel; then
    echo -e "${GREEN}✓ Service is active (running)${NC}"
else
    echo -e "${RED}✗ Service is not active${NC}"
    echo -e "${YELLOW}  Check logs: journalctl -u mt5-sentinel -n 50${NC}"
    exit 1
fi

# Check if service is enabled
if systemctl is-enabled --quiet mt5-sentinel; then
    echo -e "${GREEN}✓ Service is enabled (auto-start on boot)${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Service is not enabled${NC}"
fi

# Show service status
echo ""
echo -e "${BLUE}Current Service Status:${NC}"
systemctl status mt5-sentinel --no-pager -l

echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:         ${YELLOW}journalctl -u mt5-sentinel -f${NC}"
echo -e "  Check status:      ${YELLOW}systemctl status mt5-sentinel${NC}"
echo -e "  Stop service:      ${YELLOW}systemctl stop mt5-sentinel${NC}"
echo -e "  Start service:     ${YELLOW}systemctl start mt5-sentinel${NC}"
echo -e "  Restart service:   ${YELLOW}systemctl restart mt5-sentinel${NC}"
echo -e "  Disable service:   ${YELLOW}systemctl disable mt5-sentinel${NC}"
echo ""
echo -e "${BLUE}======================================================================${NC}"

exit 0
