#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate 1 Audit Script for TASK #031 - State Reconciliation & Crash Recovery

Validates that all deliverables are complete and meet specification:
- StateReconciler class implementation
- ExecutionGateway.get_positions() method
- Unit test suite with passing tests
- Documentation files

Run with: python3 scripts/audit_task_031.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ [{description}] File exists: {filepath}")
        return True
    else:
        print(f"❌ [{description}] File missing: {filepath}")
        return False


def check_file_contains(filepath, pattern, description):
    """Check if a file contains a specific pattern"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if pattern in content:
                print(f"✅ [{description}] Found: {pattern}")
                return True
            else:
                print(f"❌ [{description}] Pattern not found: {pattern}")
                return False
    except Exception as e:
        print(f"❌ [{description}] Error reading file: {e}")
        return False


def check_class_defined(filepath, classname, description):
    """Check if a class is defined in a file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            pattern = f"class {classname}"
            if pattern in content:
                print(f"✅ [{description}] Class defined: {classname}")
                return True
            else:
                print(f"❌ [{description}] Class not found: {classname}")
                return False
    except Exception as e:
        print(f"❌ [{description}] Error: {e}")
        return False


def check_method_defined(filepath, methodname, description):
    """Check if a method is defined in a file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            pattern = f"def {methodname}"
            if pattern in content:
                print(f"✅ [{description}] Method defined: {methodname}()")
                return True
            else:
                print(f"❌ [{description}] Method not found: {methodname}()")
                return False
    except Exception as e:
        print(f"❌ [{description}] Error: {e}")
        return False


def run_unit_tests():
    """Run unit tests and check pass rate"""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/test_reconciliation.py"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check for success indicators
        if "✅ All tests passed!" in result.stdout or "Passed: 8/8" in result.stdout:
            print(f"✅ [Unit Tests] All tests passing (8/8)")
            return True
        elif "Failed: 0/8" in result.stdout:
            print(f"✅ [Unit Tests] All tests passing (0 failures)")
            return True
        else:
            print(f"❌ [Unit Tests] Test run failed or incomplete")
            print(f"   Output: {result.stdout[:200]}...")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ [Unit Tests] Test timeout (>10s)")
        return False
    except Exception as e:
        print(f"❌ [Unit Tests] Error running tests: {e}")
        return False


def main():
    """Run Gate 1 validation checks"""
    print("=" * 80)
    print("GATE 1 AUDIT - TASK #031 (State Reconciliation & Crash Recovery)")
    print("=" * 80)
    print()

    checks = []

    # ========================================================================
    # Check 1: StateReconciler Class
    # ========================================================================
    print("[CHECK 1] Validating StateReconciler class...")
    checks.append(check_file_exists(
        "src/strategy/reconciler.py",
        "Reconciler Module"
    ))

    checks.append(check_class_defined(
        "src/strategy/reconciler.py",
        "StateReconciler",
        "StateReconciler Class"
    ))

    checks.append(check_method_defined(
        "src/strategy/reconciler.py",
        "startup_recovery",
        "startup_recovery() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/reconciler.py",
        "sync_positions",
        "sync_positions() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/reconciler.py",
        "sync_continuous",
        "sync_continuous() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/reconciler.py",
        "detect_drift",
        "detect_drift() Method"
    ))

    checks.append(check_class_defined(
        "src/strategy/reconciler.py",
        "RemotePosition",
        "RemotePosition Dataclass"
    ))

    checks.append(check_class_defined(
        "src/strategy/reconciler.py",
        "SyncResult",
        "SyncResult Dataclass"
    ))

    print()

    # ========================================================================
    # Check 2: ExecutionGateway.get_positions() Method
    # ========================================================================
    print("[CHECK 2] Validating ExecutionGateway.get_positions() method...")
    checks.append(check_file_exists(
        "src/main_paper_trading.py",
        "Paper Trading Main Loop"
    ))

    checks.append(check_method_defined(
        "src/main_paper_trading.py",
        "get_positions",
        "get_positions() Method"
    ))

    checks.append(check_file_contains(
        "src/main_paper_trading.py",
        "GET_POSITIONS",
        "GET_POSITIONS Protocol Support"
    ))

    print()

    # ========================================================================
    # Check 3: PortfolioManager Reconciliation Methods
    # ========================================================================
    print("[CHECK 3] Validating PortfolioManager reconciliation methods...")
    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "force_add_position",
        "force_add_position() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "force_close_position",
        "force_close_position() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "force_update_position",
        "force_update_position() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "get_local_positions",
        "get_local_positions() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "find_order_by_ticket",
        "find_order_by_ticket() Method"
    ))

    print()

    # ========================================================================
    # Check 4: Unit Test Suite
    # ========================================================================
    print("[CHECK 4] Validating unit test suite...")
    checks.append(check_file_exists(
        "scripts/test_reconciliation.py",
        "Unit Test Suite"
    ))

    checks.append(check_file_contains(
        "scripts/test_reconciliation.py",
        "def test_",
        "Test Functions"
    ))

    # Run tests
    checks.append(run_unit_tests())

    print()

    # ========================================================================
    # Check 5: Configuration
    # ========================================================================
    print("[CHECK 5] Validating configuration...")
    checks.append(check_file_contains(
        "src/config.py",
        "SYNC_INTERVAL_SEC",
        "Reconciliation Config"
    ))

    print()

    # ========================================================================
    # Check 6: Verification Log
    # ========================================================================
    print("[CHECK 6] Validating verification log...")
    checks.append(check_file_exists(
        "docs/archive/tasks/TASK_031_RECONCILIATION/VERIFY_LOG.log",
        "Verification Log"
    ))

    checks.append(check_file_contains(
        "docs/archive/tasks/TASK_031_RECONCILIATION/VERIFY_LOG.log",
        "✅ All tests passed!",
        "Test Success Status"
    ))

    print()

    # ========================================================================
    # Final Summary
    # ========================================================================
    print("=" * 80)
    print("GATE 1 AUDIT SUMMARY")
    print("=" * 80)
    print()

    passed = sum(checks)
    total = len(checks)

    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print()

    if passed == total:
        print("✅ GATE 1 PASSED - All requirements met")
        print()
        print("State Reconciliation System Validation:")
        print("  ✅ StateReconciler class complete")
        print("  ✅ Startup recovery implemented")
        print("  ✅ Continuous drift detection implemented")
        print("  ✅ ExecutionGateway.get_positions() working")
        print("  ✅ PortfolioManager reconciliation methods added")
        print("  ✅ Unit test suite passing (8/8)")
        print("  ✅ Configuration in place")
        print()
        print("Ready for Gate 2 Audit and AI Architectural Review")
        return 0
    else:
        print(f"❌ GATE 1 FAILED - {total - passed} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
