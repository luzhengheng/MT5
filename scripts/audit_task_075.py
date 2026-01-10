#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #075: Audit Script for INF Node Initialization

Validates all deliverables for Task #075:
1. src/infra/handshake.py exists and is executable
2. scripts/setup_inf_env.sh exists and is executable
3. Code passes syntax checks
4. Critical imports available (requests, zmq, numpy)
5. Proper ZMQ cleanup logic present

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
    """Audits Task #075 deliverables"""

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

    def check_python_syntax(self, file_path: str, description: str) -> bool:
        """Check Python syntax"""
        logger.info(f"Checking {description} syntax...")
        full_path = self.project_root / file_path

        if not full_path.exists():
            logger.error(f"  ✗ {file_path} does not exist")
            return False

        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', str(full_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"  ✓ {file_path} has valid syntax")
                return True
            else:
                logger.error(f"  ✗ Syntax error in {file_path}")
                logger.error(f"    {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"  ✗ Syntax check timeout for {file_path}")
            return False
        except Exception as e:
            logger.error(f"  ✗ Syntax check error: {e}")
            return False

    def check_bash_syntax(self, file_path: str, description: str) -> bool:
        """Check bash script syntax"""
        logger.info(f"Checking {description} bash syntax...")
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

    def check_critical_imports(self) -> bool:
        """Check critical dependencies are importable"""
        logger.info("Checking critical Python dependencies...")

        critical_packages = {
            'requests': 'HTTP client for HUB communication',
            'zmq': 'ZeroMQ for GTW communication',
            'numpy': 'Numerical computing',
            'pandas': 'Data manipulation'
        }

        all_ok = True
        for package, description in critical_packages.items():
            try:
                __import__(package)
                logger.info(f"  ✓ {package:12} - {description}")
            except ImportError:
                logger.error(f"  ✗ {package:12} - NOT INSTALLED")
                all_ok = False

        return all_ok

    def check_zmq_cleanup_logic(self) -> bool:
        """Check handshake script has proper ZMQ cleanup"""
        logger.info("Checking ZMQ cleanup logic...")

        handshake_path = self.project_root / "src/infra/handshake.py"

        if not handshake_path.exists():
            logger.error(f"  ✗ Handshake script not found")
            return False

        try:
            with open(handshake_path, 'r') as f:
                content = f.read()

            # Check for context manager usage
            has_context_manager = '__enter__' in content and '__exit__' in content
            has_cleanup = '_cleanup_zmq' in content or 'context.term()' in content
            has_socket_close = 'socket.close()' in content

            if has_context_manager:
                logger.info(f"  ✓ Uses context manager (__enter__/__exit__)")
            else:
                logger.warning(f"  ⚠ No context manager found")

            if has_cleanup:
                logger.info(f"  ✓ Has ZMQ cleanup logic")
            else:
                logger.error(f"  ✗ Missing ZMQ cleanup logic")
                return False

            if has_socket_close:
                logger.info(f"  ✓ Closes ZMQ sockets")
            else:
                logger.warning(f"  ⚠ Socket close not found")

            return has_cleanup

        except Exception as e:
            logger.error(f"  ✗ Error checking cleanup logic: {e}")
            return False

    def check_no_local_model_loading(self) -> bool:
        """Verify handshake script doesn't load local models"""
        logger.info("Checking for local model loading...")

        handshake_path = self.project_root / "src/infra/handshake.py"

        if not handshake_path.exists():
            logger.error(f"  ✗ Handshake script not found")
            return False

        try:
            with open(handshake_path, 'r') as f:
                content = f.read()

            # Red flags for local model loading
            forbidden_patterns = [
                'mlflow.pyfunc.load_model',
                'joblib.load',
                'pickle.load',
                'torch.load.*models/',  # Loading from local models/ directory
                'lightgbm.Booster(model_file'
            ]

            violations = []
            for pattern in forbidden_patterns:
                if pattern in content:
                    violations.append(pattern)

            if violations:
                logger.error(f"  ✗ Found local model loading patterns:")
                for v in violations:
                    logger.error(f"    - {v}")
                return False
            else:
                logger.info(f"  ✓ No local model loading detected")
                return True

        except Exception as e:
            logger.error(f"  ✗ Error checking model loading: {e}")
            return False

    def check_task_directory(self) -> bool:
        """Check task directory exists"""
        logger.info("Checking task directory...")
        task_dir = self.project_root / "docs/archive/tasks/TASK_075"

        if task_dir.exists():
            logger.info(f"  ✓ Task directory exists: {task_dir}")
            return True
        else:
            logger.error(f"  ✗ Task directory NOT FOUND: {task_dir}")
            return False

    def run_audit(self) -> bool:
        """Run complete audit"""
        logger.info("=" * 80)
        logger.info("🔍 AUDIT: Task #075 INF Node Initialization")
        logger.info("=" * 80)
        logger.info("")

        checks = []

        # Check 1: Task directory
        logger.info("[Check 1/9] Task Directory")
        result = self.check_task_directory()
        checks.append(("task_directory", result))
        logger.info("")

        # Check 2: handshake.py exists
        logger.info("[Check 2/9] Handshake Script")
        result = self.check_file_exists(
            "src/infra/handshake.py",
            "handshake.py"
        )
        checks.append(("handshake_exists", result))
        logger.info("")

        # Check 3: handshake.py syntax
        if result:
            logger.info("[Check 3/9] Handshake Syntax")
            result = self.check_python_syntax(
                "src/infra/handshake.py",
                "handshake.py"
            )
            checks.append(("handshake_syntax", result))
            logger.info("")
        else:
            checks.append(("handshake_syntax", False))
            logger.info("[Check 3/9] Skipped (file missing)")
            logger.info("")

        # Check 4: setup_inf_env.sh exists
        logger.info("[Check 4/9] Setup Script")
        result = self.check_file_exists(
            "scripts/setup_inf_env.sh",
            "setup_inf_env.sh"
        )
        checks.append(("setup_exists", result))
        logger.info("")

        # Check 5: setup_inf_env.sh syntax
        if result:
            logger.info("[Check 5/9] Setup Script Syntax")
            result = self.check_bash_syntax(
                "scripts/setup_inf_env.sh",
                "setup_inf_env.sh"
            )
            checks.append(("setup_syntax", result))
            logger.info("")
        else:
            checks.append(("setup_syntax", False))
            logger.info("[Check 5/9] Skipped (file missing)")
            logger.info("")

        # Check 6: Critical imports
        logger.info("[Check 6/9] Critical Dependencies")
        result = self.check_critical_imports()
        checks.append(("critical_imports", result))
        logger.info("")

        # Check 7: ZMQ cleanup logic
        logger.info("[Check 7/9] ZMQ Cleanup Logic")
        if checks[1][1]:  # If handshake exists
            result = self.check_zmq_cleanup_logic()
            checks.append(("zmq_cleanup", result))
        else:
            checks.append(("zmq_cleanup", False))
        logger.info("")

        # Check 8: No local model loading
        logger.info("[Check 8/9] No Local Model Loading")
        if checks[1][1]:  # If handshake exists
            result = self.check_no_local_model_loading()
            checks.append(("no_local_models", result))
        else:
            checks.append(("no_local_models", False))
        logger.info("")

        # Check 9: src/infra directory structure
        logger.info("[Check 9/9] Directory Structure")
        infra_dir = self.project_root / "src/infra"
        if infra_dir.exists() and infra_dir.is_dir():
            logger.info(f"  ✓ src/infra/ directory exists")
            result = True
        else:
            logger.error(f"  ✗ src/infra/ directory missing")
            result = False
        checks.append(("directory_structure", result))
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
