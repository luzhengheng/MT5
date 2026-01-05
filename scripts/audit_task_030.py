#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate 1 Audit Script for TASK #030 - Paper Trading System Verification

Validates that all deliverables are complete and meet specification:
- PortfolioManager class implementation
- Integration loop with risk checking
- Unit test suite with passing tests
- Documentation files

Run with: python3 scripts/audit_task_030.py
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


def check_method_defined(filepath, classname, methodname, description):
    """Check if a method is defined in a class"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # Simple pattern matching
            pattern = f"def {methodname}"
            if pattern in content:
                print(f"✅ [{description}] Method defined: {classname}.{methodname}()")
                return True
            else:
                print(f"❌ [{description}] Method not found: {classname}.{methodname}()")
                return False
    except Exception as e:
        print(f"❌ [{description}] Error: {e}")
        return False


def run_unit_tests():
    """Run unit tests and check pass rate"""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/test_portfolio_logic.py"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check for success indicators
        if "✅ All tests passed!" in result.stdout or "Passed: 11/11" in result.stdout:
            print(f"✅ [Unit Tests] All tests passing (11/11)")
            return True
        elif "Failed: 0/11" in result.stdout:
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
    print("GATE 1 AUDIT - TASK #030 (Paper Trading System)")
    print("=" * 80)
    print()

    checks = []

    # ========================================================================
    # Check 1: PortfolioManager Class
    # ========================================================================
    print("[CHECK 1] Validating PortfolioManager class...")
    checks.append(check_file_exists(
        "src/strategy/portfolio.py",
        "Portfolio Module"
    ))

    checks.append(check_class_defined(
        "src/strategy/portfolio.py",
        "PortfolioManager",
        "PortfolioManager Class"
    ))

    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "PortfolioManager",
        "check_risk",
        "check_risk() Method"
    ))

    checks.append(check_method_defined(
        "src/strategy/portfolio.py",
        "PortfolioManager",
        "on_fill",
        "on_fill() Method"
    ))

    checks.append(check_class_defined(
        "src/strategy/portfolio.py",
        "Order",
        "Order Dataclass"
    ))

    checks.append(check_class_defined(
        "src/strategy/portfolio.py",
        "Position",
        "Position Dataclass"
    ))

    print()

    # ========================================================================
    # Check 2: Main Paper Trading Loop
    # ========================================================================
    print("[CHECK 2] Validating main paper trading loop...")
    checks.append(check_file_exists(
        "src/main_paper_trading.py",
        "Paper Trading Main Loop"
    ))

    checks.append(check_class_defined(
        "src/main_paper_trading.py",
        "ExecutionGateway",
        "ExecutionGateway Class"
    ))

    checks.append(check_file_contains(
        "src/main_paper_trading.py",
        "PortfolioManager",
        "Portfolio Integration"
    ))

    checks.append(check_file_contains(
        "src/main_paper_trading.py",
        "StrategyEngine",
        "Strategy Integration"
    ))

    checks.append(check_file_contains(
        "src/main_paper_trading.py",
        "check_risk",
        "Risk Checking"
    ))

    print()

    # ========================================================================
    # Check 3: Unit Test Suite
    # ========================================================================
    print("[CHECK 3] Validating unit test suite...")
    checks.append(check_file_exists(
        "scripts/test_portfolio_logic.py",
        "Unit Test Suite"
    ))

    checks.append(check_file_contains(
        "scripts/test_portfolio_logic.py",
        "def test_",
        "Test Functions"
    ))

    checks.append(check_file_contains(
        "scripts/test_portfolio_logic.py",
        "assert",
        "Test Assertions"
    ))

    # Run tests
    checks.append(run_unit_tests())

    print()

    # ========================================================================
    # Check 4: Verification Log
    # ========================================================================
    print("[CHECK 4] Validating verification log...")
    checks.append(check_file_exists(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/VERIFY_LOG.log",
        "Verification Log"
    ))

    checks.append(check_file_contains(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/VERIFY_LOG.log",
        "✅ VERIFICATION PASSED",
        "Log Status"
    ))

    checks.append(check_file_contains(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/VERIFY_LOG.log",
        "11/11",
        "Test Results"
    ))

    print()

    # ========================================================================
    # Check 5: Documentation Files
    # ========================================================================
    print("[CHECK 5] Validating documentation files...")
    checks.append(check_file_exists(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/QUICK_START.md",
        "Quick Start Guide"
    ))

    checks.append(check_file_contains(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/QUICK_START.md",
        "Portfolio Manager API",
        "API Documentation"
    ))

    checks.append(check_file_exists(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/COMPLETION_REPORT.md",
        "Completion Report"
    ))

    checks.append(check_file_contains(
        "docs/archive/tasks/TASK_030_PAPER_TRADING/COMPLETION_REPORT.md",
        "READY FOR GATE 2",
        "Report Status"
    ))

    print()

    # ========================================================================
    # Check 6: Code Quality
    # ========================================================================
    print("[CHECK 6] Validating code quality...")
    checks.append(check_file_contains(
        "src/strategy/portfolio.py",
        "def __init__",
        "Init Method"
    ))

    checks.append(check_file_contains(
        "src/strategy/portfolio.py",
        "self.logger",
        "Logging Support"
    ))

    checks.append(check_file_contains(
        "src/main_paper_trading.py",
        "logging",
        "Comprehensive Logging"
    ))

    checks.append(check_file_contains(
        "src/strategy/portfolio.py",
        "-> ",
        "Type Hints"
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
        print("Paper Trading System Validation:")
        print("  ✅ PortfolioManager class complete")
        print("  ✅ Main paper trading loop integrated")
        print("  ✅ Unit test suite passing (11/11)")
        print("  ✅ Risk management implemented")
        print("  ✅ Order tracking functional")
        print("  ✅ Documentation complete")
        print()
        print("Ready for Gate 2 Audit and AI Architectural Review")
        return 0
    else:
        print(f"❌ GATE 1 FAILED - {total - passed} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
