#!/bin/bash
# -*- coding: utf-8 -*-
#
# SSH Known Hosts Setup Script for MT5-CRS
# Task #088: Hardening & Security - SSH Host Key Verification
#
# This script adds the cluster nodes' SSH host keys to the user's known_hosts file
# to enable secure SSH connections without requiring StrictHostKeyChecking=no
#
# Protocol v4.3 (Zero-Trust Edition) - SSH Hardening

set -e  # Exit on error

# Define cluster node IPs (from src.config)
INF_IP="172.19.141.250"      # Inference node (Brain)
HUB_IP="172.19.141.254"      # Hub node (Repository/Model Server)
GTW_IP="172.19.141.255"      # Gateway node (Windows MT5 Terminal)

# SSH configuration
SSH_USER="${MT5_SSH_USER:-root}"
KNOWN_HOSTS_FILE="${HOME}/.ssh/known_hosts"

# Function to add host key to known_hosts
add_host_key() {
    local host_ip=$1
    local host_name=$2

    echo "📝 Adding SSH host key for ${host_name} (${host_ip})..."

    # Create .ssh directory if it doesn't exist
    mkdir -p "${HOME}/.ssh"
    chmod 700 "${HOME}/.ssh"

    # Use ssh-keyscan to fetch and add the host key
    # -H: Hash the hostname (optional, for privacy)
    if ssh-keyscan -H "${host_ip}" >> "${KNOWN_HOSTS_FILE}" 2>/dev/null; then
        echo "  ✓ Successfully added ${host_name}"
    else
        echo "  ⚠ Warning: Failed to add ${host_name}, but continuing..."
    fi
}

# Main execution
echo "=========================================================================="
echo "MT5-CRS SSH Known Hosts Setup (Task #088: SSH Hardening)"
echo "=========================================================================="
echo ""
echo "This script adds cluster node SSH host keys to ${KNOWN_HOSTS_FILE}"
echo ""

# Add each cluster node
add_host_key "${INF_IP}" "INF (Inference/Brain)"
add_host_key "${HUB_IP}" "HUB (Repository/Model Server)"
add_host_key "${GTW_IP}" "GTW (Gateway)"

# Secure the known_hosts file
chmod 600 "${KNOWN_HOSTS_FILE}" 2>/dev/null || true

echo ""
echo "=========================================================================="
echo "✅ SSH Known Hosts Setup Complete"
echo "=========================================================================="
echo ""
echo "Summary:"
echo "  - Host keys added for: INF, HUB, GTW"
echo "  - Known hosts file: ${KNOWN_HOSTS_FILE}"
echo "  - SSH connections can now use StrictHostKeyChecking=accept-new"
echo ""
echo "Next steps:"
echo "  1. Verify SSH connectivity: ssh -o BatchMode=yes root@${INF_IP} 'echo OK'"
echo "  2. Run verify_cluster_health.py to validate cluster health"
echo ""
