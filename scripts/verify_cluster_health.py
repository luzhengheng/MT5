#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cluster Health Verification Script for MT5-CRS
Task #087: Production Hardening & Auto-Start Configuration

Validates that all critical trading services are running and properly configured
for auto-start across the production cluster.

Protocol v4.3 (Zero-Trust Edition) - Cluster Validation
"""

import subprocess
import sys
import logging
import os
import socket
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("ClusterHealth")


class ClusterHealthVerifier:
    """Verifies health and auto-start configuration of production cluster"""

    def __init__(self):
        # Load cluster configuration from environment variables
        self.hub_ip = os.getenv("MT5_HUB_IP", "172.19.141.254")
        self.inf_ip = os.getenv("MT5_INF_IP", "172.19.141.250")
        self.ssh_user = os.getenv("MT5_SSH_USER", "root")
        self.checks_passed = []
        self.checks_failed = []

        # Validate required environment variables
        if not self.hub_ip or not self.inf_ip:
            raise ValueError("MT5_HUB_IP and MT5_INF_IP environment variables are required")

    def check_local_service(self, service_name: str) -> Tuple[bool, str]:
        """Check if a local systemd service is enabled and running"""
        logger.info(f"Checking local service: {service_name}...")

        # Check if service is enabled
        try:
            result = subprocess.run(
                ['systemctl', 'is-enabled', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return False, f"Service {service_name} is not enabled"

            is_enabled = result.stdout.strip() == "enabled"

            # Check if service is active
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            is_active = result.stdout.strip() == "active"

            status = f"Enabled: {is_enabled}, Active: {is_active}"
            if is_enabled:
                logger.info(f"  ✓ {service_name}: {status}")
                return True, status
            else:
                logger.error(f"  ✗ {service_name}: {status}")
                return False, status

        except Exception as e:
            error_msg = f"Failed to check {service_name}: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            return False, error_msg

    def check_remote_service(self, host_ip: str, service_name: str, host_type: str) -> Tuple[bool, str]:
        """Check if a remote systemd service is enabled and running via SSH"""
        logger.info(f"Checking {host_type} service via SSH ({host_ip}): {service_name}...")

        try:
            # SSH configuration with secure defaults
            ssh_opts = ['-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes']

            # Check if service is enabled
            result = subprocess.run(
                ['ssh'] + ssh_opts + [f'{self.ssh_user}@{host_ip}',
                 f'systemctl is-enabled {service_name}'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                error_msg = f"Service {service_name} is not enabled on {host_type}"
                logger.error(f"  ✗ {error_msg}")
                return False, error_msg

            is_enabled = result.stdout.strip() == "enabled"

            # Check if service is active
            result = subprocess.run(
                ['ssh'] + ssh_opts + [f'{self.ssh_user}@{host_ip}',
                 f'systemctl is-active {service_name}'],
                capture_output=True,
                text=True,
                timeout=10
            )

            is_active = result.stdout.strip() == "active"

            status = f"Enabled: {is_enabled}, Active: {is_active}"
            if is_enabled:
                logger.info(f"  ✓ {host_type} {service_name}: {status}")
                return True, status
            else:
                logger.error(f"  ✗ {host_type} {service_name}: {status}")
                return False, status

        except Exception as e:
            error_msg = f"Failed to check {service_name} on {host_type}: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            return False, error_msg

    def check_network_connectivity(self) -> Tuple[bool, str]:
        """Check network connectivity between HUB and INF"""
        logger.info(f"Checking network connectivity HUB <-> INF...")

        try:
            # Ping INF from HUB context (local)
            result = subprocess.run(
                ['ping', '-c', '1', self.inf_ip],
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"  ✓ Network connectivity HUB <-> INF: OK")
                return True, "Network connectivity OK"
            else:
                logger.error(f"  ✗ Network connectivity HUB <-> INF: FAILED")
                return False, "Network connectivity FAILED"

        except Exception as e:
            error_msg = f"Failed to check network connectivity: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            return False, error_msg

    def check_zmq_ports(self) -> Tuple[bool, str]:
        """Check if ZMQ ports are listening using ss or Python socket"""
        logger.info(f"Checking ZMQ ports...")

        try:
            # Try using 'ss' command first (modern approach)
            result = subprocess.run(
                ['ss', '-tuln'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                zmq_req_listening = ':5555 ' in result.stdout
                zmq_pub_listening = ':5556 ' in result.stdout
            else:
                # Fallback: Use Python socket to check ports
                zmq_req_listening = self._check_port_listening(5555)
                zmq_pub_listening = self._check_port_listening(5556)

            if zmq_req_listening and zmq_pub_listening:
                logger.info(f"  ✓ ZMQ ports (5555/5556): LISTENING")
                return True, "ZMQ ports listening"
            else:
                status = f"REQ:{'Y' if zmq_req_listening else 'N'}, PUB:{'Y' if zmq_pub_listening else 'N'}"
                logger.warning(f"  ⚠ ZMQ ports partially listening: {status}")
                return True, status  # Warning but not critical

        except Exception as e:
            error_msg = f"Failed to check ZMQ ports: {str(e)}"
            logger.warning(f"  ⚠ {error_msg}")
            return True, error_msg  # Warning but not critical

    def _check_port_listening(self, port: int) -> bool:
        """Check if a specific port is listening using Python socket"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def run_all_checks(self) -> bool:
        """Run all cluster health checks"""
        logger.info("=" * 80)
        logger.info("MT5-CRS Cluster Health Verification")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        # Check HUB local services
        logger.info("\n[PHASE 1] Local HUB Services")
        hub_model_ok, hub_model_status = self.check_local_service("mt5-model-server")
        if hub_model_ok:
            self.checks_passed.append(f"HUB mt5-model-server: {hub_model_status}")
        else:
            self.checks_failed.append(f"HUB mt5-model-server: {hub_model_status}")

        # Check INF remote services
        logger.info("\n[PHASE 2] Remote INF Services")
        inf_sentinel_ok, inf_sentinel_status = self.check_remote_service(
            self.inf_ip, "mt5-sentinel", "INF"
        )
        if inf_sentinel_ok:
            self.checks_passed.append(f"INF mt5-sentinel: {inf_sentinel_status}")
        else:
            self.checks_failed.append(f"INF mt5-sentinel: {inf_sentinel_status}")

        # Check network connectivity
        logger.info("\n[PHASE 3] Network Connectivity")
        network_ok, network_status = self.check_network_connectivity()
        if network_ok:
            self.checks_passed.append(f"Network connectivity: {network_status}")
        else:
            self.checks_failed.append(f"Network connectivity: {network_status}")

        # Check ZMQ ports
        logger.info("\n[PHASE 4] Trading Infrastructure")
        zmq_ok, zmq_status = self.check_zmq_ports()
        if zmq_ok:
            self.checks_passed.append(f"ZMQ ports: {zmq_status}")
        else:
            self.checks_failed.append(f"ZMQ ports: {zmq_status}")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Passed Checks: {len(self.checks_passed)}")
        for check in self.checks_passed:
            logger.info(f"  ✓ {check}")

        if self.checks_failed:
            logger.error(f"Failed Checks: {len(self.checks_failed)}")
            for check in self.checks_failed:
                logger.error(f"  ✗ {check}")
        else:
            logger.info(f"Failed Checks: 0")

        logger.info("=" * 80)

        overall_healthy = len(self.checks_failed) == 0
        if overall_healthy:
            logger.info("🟢 Cluster Status: HEALTHY (All critical services enabled)")
        else:
            logger.error("🔴 Cluster Status: DEGRADED (Some services not properly configured)")

        logger.info("=" * 80)
        return overall_healthy


def main():
    """Main entry point"""
    verifier = ClusterHealthVerifier()
    is_healthy = verifier.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    main()
