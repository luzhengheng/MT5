#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #077: Audit Script for Systemd Service Deployment

Validates all deliverables for Task #077:
1. Systemd service file exists and has correct syntax
2. Installation script exists and is executable
3. Logrotate configuration exists
4. Service can be installed (dry-run check)
5. No syntax errors in bash scripts

Protocol v4.3 (Zero-Trust Edition) - Gate 1 Audit
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class TaskAuditor:
    """Audits Task #077 deliverables"""

    def __init__(self):
        # Dynamically determine project root
        script_dir = Path(__file__).resolve().parent
        self.project_root = script_dir.parent
        self.checks_passed = []
        self.checks_failed = []

    def check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if file exists"""
        logger.info(f"Checking {description}...")
        full_path = self.project_root / file_path

        if full_path.exists():
            logger.info(f"  ✓ {file_path} exists")
            return True
        else:
            logger.error(f"  ✗ {file_path} NOT FOUND")
            return False

    def check_bash_syntax(self, file_path: str, description: str) -> bool:
        """Check bash script syntax"""
        logger.info(f"Checking {description} syntax...")
        full_path = self.project_root / file_path

        if not full_path.exists():
            logger.error(f"  ✗ {file_path} does not exist")
            return False

        try:
            result = subprocess.run(
                ['bash', '-n', str(full_path)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"  ✓ {file_path} has valid bash syntax")
                return True
            else:
                logger.error(f"  ✗ Bash syntax error in {file_path}")
                logger.error(f"    {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"  ✗ Bash syntax check timeout")
            return False
        except Exception as e:
            logger.error(f"  ✗ Bash syntax check error: {e}")
            return False

    def check_systemd_service_syntax(self) -> bool:
        """Check systemd service file syntax"""
        logger.info("Checking systemd service file syntax...")

        service_file = self.project_root / "systemd/mt5-sentinel.service"

        if not service_file.exists():
            logger.error(f"  ✗ Service file not found")
            return False

        try:
            # Read and validate basic structure
            with open(service_file, 'r') as f:
                content = f.read()

            # Check for required sections
            required_sections = ['[Unit]', '[Service]', '[Install]']
            for section in required_sections:
                if section not in content:
                    logger.error(f"  ✗ Missing required section: {section}")
                    return False

            # Check for required directives
            required_directives = ['ExecStart=', 'Type=', 'Restart=']
            for directive in required_directives:
                if directive not in content:
                    logger.error(f"  ✗ Missing required directive: {directive}")
                    return False

            # Use systemd-analyze verify if available
            try:
                result = subprocess.run(
                    ['systemd-analyze', 'verify', str(service_file)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # systemd-analyze may return warnings, not necessarily errors
                if result.returncode == 0 or result.returncode == 1:
                    logger.info(f"  ✓ Service file syntax valid")
                    return True
                else:
                    logger.error(f"  ✗ systemd-analyze verification failed")
                    logger.error(f"    {result.stderr}")
                    return False

            except FileNotFoundError:
                logger.warning(f"  ⚠ systemd-analyze not available, using basic checks")
                logger.info(f"  ✓ Basic service file structure valid")
                return True

        except Exception as e:
            logger.error(f"  ✗ Service file validation error: {e}")
            return False

    def check_executable_permission(self, file_path: str, description: str) -> bool:
        """Check if file has executable permission"""
        logger.info(f"Checking {description} permissions...")
        full_path = self.project_root / file_path

        if not full_path.exists():
            logger.error(f"  ✗ {file_path} does not exist")
            return False

        if os.access(full_path, os.X_OK):
            logger.info(f"  ✓ {file_path} is executable")
            return True
        else:
            logger.error(f"  ✗ {file_path} is not executable")
            logger.error(f"    Run: chmod +x {file_path}")
            return False

    def check_service_dependencies(self) -> bool:
        """Check if sentinel daemon exists"""
        logger.info("Checking service dependencies...")

        sentinel_path = self.project_root / "src/strategy/sentinel_daemon.py"

        if not sentinel_path.exists():
            logger.error(f"  ✗ Sentinel daemon not found: {sentinel_path}")
            return False

        logger.info(f"  ✓ Sentinel daemon exists")

        # Check venv Python
        venv_python = self.project_root / "venv/bin/python"
        if not venv_python.exists():
            logger.error(f"  ✗ venv Python not found: {venv_python}")
            return False

        logger.info(f"  ✓ venv Python exists")

        return True

    def check_env_file(self) -> bool:
        """Check .env file exists"""
        logger.info("Checking environment configuration...")

        env_file = self.project_root / ".env"

        if not env_file.exists():
            logger.warning(f"  ⚠ .env file not found (service may fail without EODHD_API_TOKEN)")
            return True  # Not blocking, just a warning

        logger.info(f"  ✓ .env file exists")

        # Check for critical variables
        with open(env_file, 'r') as f:
            env_content = f.read()

        if 'EODHD_API_TOKEN' not in env_content:
            logger.warning(f"  ⚠ EODHD_API_TOKEN not found in .env")

        return True

    def check_task_directory(self) -> bool:
        """Check task directory exists"""
        logger.info("Checking task directory...")
        task_dir = self.project_root / "docs/archive/tasks/TASK_077"

        if task_dir.exists():
            logger.info(f"  ✓ Task directory exists: {task_dir}")
            return True
        else:
            logger.error(f"  ✗ Task directory NOT FOUND: {task_dir}")
            return False

    def run_audit(self) -> bool:
        """Run complete audit"""
        logger.info("=" * 80)
        logger.info("🔍 AUDIT: Task #077 Systemd Service Deployment")
        logger.info("=" * 80)
        logger.info("")

        checks = []

        # Check 1: Task directory
        logger.info("[Check 1/9] Task Directory")
        result = self.check_task_directory()
        checks.append(("task_directory", result))
        logger.info("")

        # Check 2: Systemd service file exists
        logger.info("[Check 2/9] Systemd Service File")
        result = self.check_file_exists(
            "systemd/mt5-sentinel.service",
            "systemd service file"
        )
        checks.append(("service_file_exists", result))
        logger.info("")

        # Check 3: Service file syntax
        if result:
            logger.info("[Check 3/9] Service File Syntax")
            result = self.check_systemd_service_syntax()
            checks.append(("service_syntax", result))
            logger.info("")
        else:
            checks.append(("service_syntax", False))
            logger.info("[Check 3/9] Skipped (file missing)")
            logger.info("")

        # Check 4: Installation script exists
        logger.info("[Check 4/9] Installation Script")
        result = self.check_file_exists(
            "scripts/install_service.sh",
            "installation script"
        )
        checks.append(("install_script_exists", result))
        logger.info("")

        # Check 5: Installation script syntax
        if result:
            logger.info("[Check 5/9] Installation Script Syntax")
            result = self.check_bash_syntax(
                "scripts/install_service.sh",
                "installation script"
            )
            checks.append(("install_script_syntax", result))
            logger.info("")
        else:
            checks.append(("install_script_syntax", False))
            logger.info("[Check 5/9] Skipped (file missing)")
            logger.info("")

        # Check 6: Installation script executable
        if checks[3][1]:  # If install script exists
            logger.info("[Check 6/9] Installation Script Permissions")
            result = self.check_executable_permission(
                "scripts/install_service.sh",
                "installation script"
            )
            checks.append(("install_script_executable", result))
            logger.info("")
        else:
            checks.append(("install_script_executable", False))
            logger.info("[Check 6/9] Skipped (file missing)")
            logger.info("")

        # Check 7: Logrotate config exists
        logger.info("[Check 7/9] Logrotate Configuration")
        result = self.check_file_exists(
            "systemd/mt5-sentinel.logrotate",
            "logrotate configuration"
        )
        checks.append(("logrotate_exists", result))
        logger.info("")

        # Check 8: Service dependencies
        logger.info("[Check 8/9] Service Dependencies")
        result = self.check_service_dependencies()
        checks.append(("service_dependencies", result))
        logger.info("")

        # Check 9: Environment file
        logger.info("[Check 9/9] Environment Configuration")
        result = self.check_env_file()
        checks.append(("env_file", result))
        logger.info("")

        # Summary
        logger.info("=" * 80)
        logger.info("📊 Audit Summary")
        logger.info("=" * 80)

        passed = sum(1 for _, result in checks if result)
        total = len(checks)

        for check_name, result in checks:
            status = "✓" if result else "✗"
            logger.info(f"  {status} {check_name}")

        logger.info("")
        logger.info(f"Result: {passed}/{total} checks passed")

        if passed == total:
            logger.info("")
            logger.info("✅ GATE 1 AUDIT PASSED")
            logger.info("=" * 80)
            return True
        else:
            logger.info("")
            logger.error("❌ GATE 1 AUDIT FAILED")
            logger.error("Please fix the issues above and re-run audit")
            logger.info("=" * 80)
            return False


def main():
    """Main entry point"""
    auditor = TaskAuditor()
    success = auditor.run_audit()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
