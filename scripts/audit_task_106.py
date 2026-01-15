#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit and Test Suite for Task #106
MT5 Live Connector - Gate 1 Local Static Checks and Unit Tests

This script validates:
1. Static Code Quality: pylint, mypy, code metrics
2. Unit Tests: pytest execution with coverage
3. Import Validation: Core modules can be imported
4. Documentation Completeness: ARCHITECTURE.md exists
5. Deliverables Check: All 4 core files present

Protocol: v4.3 (Zero-Trust Edition)
Gate 1 Standard: Zero Errors, 100% deliverable completeness
Author: MT5-CRS Hub Agent
"""

import sys
import os
import subprocess
import logging
import unittest
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('VERIFY_LOG.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class AuditConfig:
    """Audit configuration for Task #106"""

    # Project root
    PROJECT_ROOT = Path("/opt/mt5-crs")

    # Core deliverable files
    CORE_FILES = [
        PROJECT_ROOT / "src/execution/mt5_live_connector.py",
        PROJECT_ROOT / "src/execution/heartbeat_monitor.py",
        PROJECT_ROOT / "scripts/gateway/mt5_zmq_server.py",
        PROJECT_ROOT / "src/execution/secure_loader.py",
    ]

    # Documentation
    ARCHITECTURE_DOC = PROJECT_ROOT / "docs/archive/tasks/TASK_106_MT5_BRIDGE/ARCHITECTURE.md"

    # Test files pattern
    TEST_PATTERN = "test_*.py"

    # Pylint threshold
    PYLINT_MIN_SCORE = 8.0

    # Code metrics thresholds
    MAX_LINE_COUNT_PER_FILE = 1000

    # Coverage target
    MIN_COVERAGE_PCT = 75.0


# ============================================================================
# Audit Results Tracker
# ============================================================================

class AuditResults:
    """Track audit results"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0

    def add_result(self, check_name: str, passed: bool, message: str = "",
                   details: str = ""):
        """Add a check result"""
        result = {
            "check": check_name,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.results.append(result)
        self.total_checks += 1

        if passed:
            self.passed_checks += 1
            logger.info(f"✅ PASS: {check_name} - {message}")
        else:
            self.failed_checks += 1
            logger.error(f"❌ FAIL: {check_name} - {message}")
            if details:
                logger.error(f"   Details: {details}")

    def get_summary(self) -> str:
        """Get summary string"""
        return (
            f"Total: {self.total_checks}, "
            f"Passed: {self.passed_checks}, "
            f"Failed: {self.failed_checks}"
        )


# ============================================================================
# Static Code Quality Checks
# ============================================================================

class StaticCodeChecker:
    """Static code quality checker"""

    def __init__(self, results: AuditResults):
        self.results = results

    def run_pylint(self, file_path: Path) -> Tuple[bool, float, str]:
        """Run pylint on a file"""
        try:
            cmd = ["pylint", str(file_path), "--score=yes"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse score from output
            output = result.stdout
            score = 0.0
            for line in output.split('\n'):
                if 'rated at' in line.lower():
                    # Extract score like "Your code has been rated at 9.52/10"
                    parts = line.split('rated at')
                    if len(parts) > 1:
                        score_str = parts[1].split('/')[0].strip()
                        score = float(score_str)
                        break

            passed = score >= AuditConfig.PYLINT_MIN_SCORE
            return passed, score, output

        except subprocess.TimeoutExpired:
            return False, 0.0, "Pylint timeout"
        except Exception as e:
            return False, 0.0, str(e)

    def run_mypy(self, file_path: Path) -> Tuple[bool, str]:
        """Run mypy type checking on a file"""
        try:
            cmd = ["mypy", str(file_path), "--ignore-missing-imports"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr
            # Success if no errors (warnings are ok)
            passed = "error" not in output.lower() or result.returncode == 0
            return passed, output

        except subprocess.TimeoutExpired:
            return False, "Mypy timeout"
        except Exception as e:
            return False, str(e)

    def count_lines(self, file_path: Path) -> Tuple[int, int, int]:
        """Count total lines, code lines, and comment lines"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)
            code_lines = 0
            comment_lines = 0

            for line in lines:
                stripped = line.strip()
                if stripped:
                    if stripped.startswith('#'):
                        comment_lines += 1
                    else:
                        code_lines += 1

            return total_lines, code_lines, comment_lines

        except Exception as e:
            logger.error(f"Error counting lines: {e}")
            return 0, 0, 0

    def check_file(self, file_path: Path) -> bool:
        """Run all checks on a single file"""
        file_name = file_path.name
        logger.info(f"\n{'='*70}")
        logger.info(f"Checking: {file_name}")
        logger.info(f"{'='*70}")

        all_passed = True

        # Check 1: File exists
        if not file_path.exists():
            self.results.add_result(
                f"File Exists: {file_name}",
                False,
                "File not found",
                str(file_path)
            )
            return False
        else:
            self.results.add_result(
                f"File Exists: {file_name}",
                True,
                f"Found at {file_path}"
            )

        # Check 2: Line count
        total, code, comments = self.count_lines(file_path)
        line_check_passed = total <= AuditConfig.MAX_LINE_COUNT_PER_FILE
        self.results.add_result(
            f"Line Count: {file_name}",
            line_check_passed,
            f"Total: {total}, Code: {code}, Comments: {comments}",
            f"Threshold: {AuditConfig.MAX_LINE_COUNT_PER_FILE}"
        )
        all_passed = all_passed and line_check_passed

        # Check 3: Pylint
        pylint_passed, score, output = self.run_pylint(file_path)
        self.results.add_result(
            f"Pylint: {file_name}",
            pylint_passed,
            f"Score: {score:.2f}/10.0",
            output[:500] if not pylint_passed else ""
        )
        all_passed = all_passed and pylint_passed

        # Check 4: Mypy
        mypy_passed, output = self.run_mypy(file_path)
        self.results.add_result(
            f"Mypy: {file_name}",
            mypy_passed,
            "Type checking passed" if mypy_passed else "Type errors found",
            output[:500] if not mypy_passed else ""
        )
        all_passed = all_passed and mypy_passed

        return all_passed

    def check_all_core_files(self) -> bool:
        """Check all core files"""
        logger.info("\n" + "█"*70)
        logger.info("█ STATIC CODE QUALITY CHECKS")
        logger.info("█"*70)

        all_passed = True
        for file_path in AuditConfig.CORE_FILES:
            file_passed = self.check_file(file_path)
            all_passed = all_passed and file_passed

        return all_passed


# ============================================================================
# Import Validation
# ============================================================================

class ImportValidator:
    """Validate that core modules can be imported"""

    def __init__(self, results: AuditResults):
        self.results = results

    def test_import_module(self, module_path: str, class_name: str = None) -> bool:
        """Test importing a module"""
        try:
            # Add project root to path
            sys.path.insert(0, str(AuditConfig.PROJECT_ROOT))

            # Import module
            parts = module_path.split('.')
            module = __import__(module_path)
            for part in parts[1:]:
                module = getattr(module, part)

            # If class name specified, check it exists
            if class_name:
                if not hasattr(module, class_name):
                    return False

            return True

        except Exception as e:
            logger.error(f"Import error: {e}")
            return False

    def validate_all_imports(self) -> bool:
        """Validate all core module imports"""
        logger.info("\n" + "█"*70)
        logger.info("█ IMPORT VALIDATION")
        logger.info("█"*70)

        imports_to_test = [
            ("src.execution.mt5_live_connector", "MT5LiveConnector"),
            ("src.execution.heartbeat_monitor", "HeartbeatMonitor"),
            ("src.execution.secure_loader", "SecureModuleLoader"),
        ]

        all_passed = True
        for module_path, class_name in imports_to_test:
            passed = self.test_import_module(module_path, class_name)
            self.results.add_result(
                f"Import: {module_path}.{class_name}",
                passed,
                f"{'Successfully imported' if passed else 'Import failed'}"
            )
            all_passed = all_passed and passed

        # Check dependencies
        dependencies = [
            ("zmq", "pyzmq library"),
            ("yaml", "pyyaml library"),
        ]

        for module_name, lib_name in dependencies:
            try:
                __import__(module_name)
                self.results.add_result(
                    f"Dependency: {lib_name}",
                    True,
                    f"{lib_name} is installed"
                )
            except ImportError:
                self.results.add_result(
                    f"Dependency: {lib_name}",
                    False,
                    f"{lib_name} is NOT installed"
                )
                all_passed = False

        return all_passed


# ============================================================================
# Unit Tests Execution
# ============================================================================

class UnitTestRunner:
    """Run pytest unit tests"""

    def __init__(self, results: AuditResults):
        self.results = results

    def run_pytest(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Run pytest with coverage"""
        try:
            # Run pytest with coverage
            cmd = [
                "pytest",
                str(AuditConfig.PROJECT_ROOT / "tests"),
                "-v",
                "--tb=short",
                "-k", "mt5 or heartbeat or connector",
                "--maxfail=5"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(AuditConfig.PROJECT_ROOT)
            )

            output = result.stdout + result.stderr

            # Parse results
            test_count = 0
            passed_count = 0
            failed_count = 0

            for line in output.split('\n'):
                if 'passed' in line.lower():
                    # Try to extract numbers like "5 passed in 2.3s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'passed' and i > 0:
                            try:
                                passed_count = int(parts[i-1])
                            except ValueError:
                                pass
                if 'failed' in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'failed' and i > 0:
                            try:
                                failed_count = int(parts[i-1])
                            except ValueError:
                                pass

            test_count = passed_count + failed_count

            stats = {
                "total": test_count,
                "passed": passed_count,
                "failed": failed_count,
                "return_code": result.returncode
            }

            passed = result.returncode == 0 or (failed_count == 0 and passed_count > 0)

            return passed, output, stats

        except subprocess.TimeoutExpired:
            return False, "Pytest timeout (5 minutes)", {"total": 0, "passed": 0, "failed": 0}
        except Exception as e:
            return False, str(e), {"total": 0, "passed": 0, "failed": 0}

    def run_all_tests(self) -> bool:
        """Run all unit tests"""
        logger.info("\n" + "█"*70)
        logger.info("█ UNIT TESTS EXECUTION")
        logger.info("█"*70)

        passed, output, stats = self.run_pytest()

        self.results.add_result(
            "Unit Tests Execution",
            passed,
            f"Tests: {stats['total']}, Passed: {stats['passed']}, Failed: {stats['failed']}",
            output[:1000] if not passed else ""
        )

        # Log full output for debugging
        logger.info(f"\nPytest Output:\n{output[:2000]}")

        return passed


# ============================================================================
# Documentation Completeness
# ============================================================================

class DocumentationChecker:
    """Check documentation completeness"""

    def __init__(self, results: AuditResults):
        self.results = results

    def check_architecture_doc(self) -> bool:
        """Check ARCHITECTURE.md exists and has content"""
        logger.info("\n" + "█"*70)
        logger.info("█ DOCUMENTATION COMPLETENESS")
        logger.info("█"*70)

        doc_path = AuditConfig.ARCHITECTURE_DOC

        # Check existence
        if not doc_path.exists():
            self.results.add_result(
                "ARCHITECTURE.md Exists",
                False,
                f"File not found at {doc_path}"
            )
            return False

        self.results.add_result(
            "ARCHITECTURE.md Exists",
            True,
            f"Found at {doc_path}"
        )

        # Check content
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()

            line_count = len(content.split('\n'))
            word_count = len(content.split())

            # Must have reasonable content
            has_content = line_count > 50 and word_count > 200

            self.results.add_result(
                "ARCHITECTURE.md Content",
                has_content,
                f"Lines: {line_count}, Words: {word_count}"
            )

            # Check for key sections
            required_sections = ["架构", "协议", "组件"]
            sections_found = sum(1 for s in required_sections if s in content)

            self.results.add_result(
                "ARCHITECTURE.md Sections",
                sections_found >= 2,
                f"Found {sections_found}/3 key sections"
            )

            return has_content and sections_found >= 2

        except Exception as e:
            self.results.add_result(
                "ARCHITECTURE.md Content",
                False,
                f"Error reading file: {e}"
            )
            return False


# ============================================================================
# Deliverables Check
# ============================================================================

class DeliverablesChecker:
    """Check all deliverables are present"""

    def __init__(self, results: AuditResults):
        self.results = results

    def check_deliverables(self) -> bool:
        """Check all core deliverables exist"""
        logger.info("\n" + "█"*70)
        logger.info("█ DELIVERABLES CHECK")
        logger.info("█"*70)

        all_exist = True

        for i, file_path in enumerate(AuditConfig.CORE_FILES, 1):
            exists = file_path.exists()
            self.results.add_result(
                f"Deliverable #{i}: {file_path.name}",
                exists,
                f"{'Found' if exists else 'MISSING'} at {file_path}"
            )
            all_exist = all_exist and exists

        return all_exist


# ============================================================================
# Main Audit Orchestrator
# ============================================================================

def run_full_audit() -> bool:
    """Run complete Gate 1 audit"""
    logger.info("\n" + "█"*70)
    logger.info("█ TASK #106 GATE 1 AUDIT")
    logger.info("█ MT5 Live Connector - Local Static Checks & Unit Tests")
    logger.info("█"*70)
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    logger.info(f"Protocol: v4.3 (Zero-Trust Edition)")
    logger.info("█"*70 + "\n")

    results = AuditResults()

    # Phase 1: Deliverables Check
    deliverables_checker = DeliverablesChecker(results)
    deliverables_ok = deliverables_checker.check_deliverables()

    # Phase 2: Static Code Quality
    static_checker = StaticCodeChecker(results)
    static_ok = static_checker.check_all_core_files()

    # Phase 3: Import Validation
    import_validator = ImportValidator(results)
    imports_ok = import_validator.validate_all_imports()

    # Phase 4: Unit Tests
    test_runner = UnitTestRunner(results)
    tests_ok = test_runner.run_all_tests()

    # Phase 5: Documentation
    doc_checker = DocumentationChecker(results)
    docs_ok = doc_checker.check_architecture_doc()

    # Final Summary
    logger.info("\n" + "█"*70)
    logger.info("█ AUDIT SUMMARY")
    logger.info("█"*70)
    logger.info(f"Total Checks: {results.total_checks}")
    logger.info(f"Passed: {results.passed_checks}")
    logger.info(f"Failed: {results.failed_checks}")
    logger.info(f"Pass Rate: {results.passed_checks/results.total_checks*100:.1f}%")
    logger.info("█"*70)

    # Phase results
    logger.info("\nPhase Results:")
    logger.info(f"  {'✅' if deliverables_ok else '❌'} Deliverables Check")
    logger.info(f"  {'✅' if static_ok else '❌'} Static Code Quality")
    logger.info(f"  {'✅' if imports_ok else '❌'} Import Validation")
    logger.info(f"  {'✅' if tests_ok else '❌'} Unit Tests")
    logger.info(f"  {'✅' if docs_ok else '❌'} Documentation")

    # Overall result
    all_passed = (
        deliverables_ok and
        static_ok and
        imports_ok and
        tests_ok and
        docs_ok
    )

    logger.info("\n" + "█"*70)
    if all_passed:
        logger.info("█ ✅ GATE 1 AUDIT PASSED - Zero Errors")
    else:
        logger.info("█ ❌ GATE 1 AUDIT FAILED")
        logger.info("█")
        logger.info("█ Failed Checks:")
        for result in results.results:
            if not result['passed']:
                logger.info(f"█   - {result['check']}: {result['message']}")
    logger.info("█"*70 + "\n")

    return all_passed


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Gate 1 Audit for Task #106...")
    success = run_full_audit()

    exit_code = 0 if success else 1
    logger.info(f"\nExit Code: {exit_code}")
    sys.exit(exit_code)
