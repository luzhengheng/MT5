#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #078: Audit Script for Model Server Daemonization

Validates all deliverables for Task #078:
1. Systemd service file exists and is properly configured
2. Service is running and listening on port 5001
3. Service binds to 0.0.0.0 (accepting remote connections)
4. Health check endpoint responds correctly
5. Pydantic v2 migration completed (no v1 imports)

Protocol v4.3 (Zero-Trust Edition) - Gate 1 Audit
"""

import os
import sys
import subprocess
import logging
import requests
from pathlib import Path
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class Task078Auditor:
    """Audits Task #078 deliverables"""

    def __init__(self):
        script_dir = Path(__file__).resolve().parent
        self.project_root = script_dir.parent
        self.checks_passed = []
        self.checks_failed = []

    def check_systemd_service_exists(self) -> bool:
        """Check if systemd service file exists"""
        logger.info("1. Checking systemd service file...")
        service_file = Path("/etc/systemd/system/mt5-model-server.service")

        if service_file.exists():
            logger.info(f"  ✓ Service file exists: {service_file}")
            return True
        else:
            logger.error(f"  ✗ Service file NOT FOUND: {service_file}")
            return False

    def check_service_running(self) -> bool:
        """Check if service is running"""
        logger.info("2. Checking if service is running...")

        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'mt5-model-server'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip() == 'active':
                logger.info("  ✓ Service is running")
                return True
            else:
                logger.error(f"  ✗ Service is NOT running (status: {result.stdout.strip()})")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to check service status: {e}")
            return False

    def check_port_listening(self) -> bool:
        """Check if port 5001 is listening"""
        logger.info("3. Checking if port 5001 is listening...")

        try:
            result = subprocess.run(
                ['lsof', '-i', ':5001'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and 'python3' in result.stdout:
                logger.info("  ✓ Port 5001 is listening")
                return True
            else:
                logger.error("  ✗ Port 5001 is NOT listening")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to check port: {e}")
            return False

    def check_health_endpoint(self) -> bool:
        """Check if health endpoint responds"""
        logger.info("4. Checking health endpoint...")

        try:
            # Test via localhost
            response = requests.get('http://127.0.0.1:5001/health', timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    logger.info(f"  ✓ Health endpoint OK: {data}")
                    return True
                else:
                    logger.error(f"  ✗ Health endpoint returned unhealthy status: {data}")
                    return False
            else:
                logger.error(f"  ✗ Health endpoint returned status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to access health endpoint: {e}")
            return False

    def check_pydantic_v2_migration(self) -> bool:
        """Check that pydantic.v1 imports are removed"""
        logger.info("5. Checking Pydantic v2 migration...")

        files_to_check = [
            "src/serving/models.py",
            "src/serving/app.py"
        ]

        all_good = True
        for file_path in files_to_check:
            full_path = self.project_root / file_path

            if not full_path.exists():
                logger.error(f"  ✗ File not found: {file_path}")
                all_good = False
                continue

            with open(full_path, 'r') as f:
                content = f.read()

            if 'pydantic.v1' in content:
                logger.error(f"  ✗ {file_path} still imports pydantic.v1")
                all_good = False
            else:
                logger.info(f"  ✓ {file_path} uses Pydantic v2")

        return all_good

    def check_service_config(self) -> bool:
        """Check service configuration"""
        logger.info("6. Checking service configuration...")

        service_file = Path("/etc/systemd/system/mt5-model-server.service")

        if not service_file.exists():
            logger.error("  ✗ Service file not found")
            return False

        with open(service_file, 'r') as f:
            content = f.read()

        checks = {
            '--host 0.0.0.0': 'Binds to all interfaces',
            '--port 5001': 'Uses correct port',
            'WorkingDirectory=/opt/mt5-crs': 'Correct working directory',
        }

        all_good = True
        for check, description in checks.items():
            if check in content:
                logger.info(f"  ✓ {description}")
            else:
                logger.error(f"  ✗ Missing: {description}")
                all_good = False

        return all_good

    def run_audit(self) -> bool:
        """Run all audit checks"""
        logger.info("="*60)
        logger.info("TASK #078 AUDIT - Model Server Daemonization")
        logger.info("="*60)

        checks = [
            ("Systemd Service File", self.check_systemd_service_exists),
            ("Service Running", self.check_service_running),
            ("Port Listening", self.check_port_listening),
            ("Health Endpoint", self.check_health_endpoint),
            ("Pydantic v2 Migration", self.check_pydantic_v2_migration),
            ("Service Configuration", self.check_service_config),
        ]

        for name, check_func in checks:
            try:
                if check_func():
                    self.checks_passed.append(name)
                else:
                    self.checks_failed.append(name)
            except Exception as e:
                logger.error(f"  ✗ Exception during {name}: {e}")
                self.checks_failed.append(name)

            logger.info("")  # Blank line

        # Summary
        logger.info("="*60)
        logger.info("AUDIT SUMMARY")
        logger.info("="*60)
        logger.info(f"Passed: {len(self.checks_passed)}/{len(checks)}")
        logger.info(f"Failed: {len(self.checks_failed)}/{len(checks)}")

        if self.checks_failed:
            logger.info("\nFailed checks:")
            for check in self.checks_failed:
                logger.info(f"  ✗ {check}")

        logger.info("="*60)

        return len(self.checks_failed) == 0


def main():
    """Main entry point"""
    auditor = Task078Auditor()
    success = auditor.run_audit()

    if success:
        logger.info("✅ GATE 1 PASSED - All checks successful")
        return 0
    else:
        logger.error("❌ GATE 1 FAILED - Fix issues and re-run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
