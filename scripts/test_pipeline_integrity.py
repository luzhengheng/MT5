#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Integrity Test

Tests the complete finish pipeline without making real changes.
Verifies all components are available before running finish command.

Task #099.02: Critical Pipeline Repair
"""

import sys
import subprocess
from pathlib import Path

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent


def print_header(title):
    """Print formatted header"""
    print()
    print("=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)
    print()


def print_result(name, success, message=""):
    """Print test result"""
    if success:
        print(f"{GREEN}✅ PASS{RESET}: {name}")
        if message:
            print(f"  {message}")
    else:
        print(f"{RED}❌ FAIL{RESET}: {name}")
        if message:
            print(f"  {message}")
    print()


def test_bridge_exists():
    """Test 1: gemini_review_bridge.py exists"""
    print_header("TEST 1: Gemini Review Bridge Availability")

    bridge_path = PROJECT_ROOT / "gemini_review_bridge.py"

    if not bridge_path.exists():
        print_result(
            "Bridge script location",
            False,
            f"File not found: {bridge_path}"
        )
        return False

    print_result(
        "Bridge script location",
        True,
        f"Found at {bridge_path}"
    )
    return True


def test_bridge_syntax():
    """Test 2: gemini_review_bridge.py has valid syntax"""
    print_header("TEST 2: Bridge Script Syntax")

    bridge_path = PROJECT_ROOT / "gemini_review_bridge.py"

    try:
        import py_compile
        py_compile.compile(str(bridge_path), doraise=True)
        print_result("Syntax validation", True, "No syntax errors")
        return True

    except SyntaxError as e:
        print_result("Syntax validation", False, f"Syntax error: {e}")
        return False
    except Exception as e:
        print_result("Syntax validation", False, f"Compilation error: {e}")
        return False


def test_git_available():
    """Test 3: git command is available"""
    print_header("TEST 3: Git Command Availability")

    try:
        result = subprocess.run(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )

        if result.returncode != 0:
            print_result("Git command", False, "git --version failed")
            return False

        version = result.stdout.decode().strip()
        print_result("Git command", True, f"Found: {version}")
        return True

    except FileNotFoundError:
        print_result("Git command", False, "git not found in PATH")
        return False
    except Exception as e:
        print_result("Git command", False, f"Error: {e}")
        return False


def test_notion_imports():
    """Test 4: Notion updater can be imported"""
    print_header("TEST 4: Notion Updater Import")

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.utils.notion_updater import update_task_status

        print_result(
            "Notion module import",
            True,
            "notion_updater.update_task_status loaded"
        )
        return True

    except ImportError as e:
        print_result("Notion module import", False, f"Import error: {e}")
        return False
    except Exception as e:
        print_result("Notion module import", False, f"Error: {e}")
        return False


def test_project_cli_exists():
    """Test 5: project_cli.py exists"""
    print_header("TEST 5: Project CLI Availability")

    cli_path = PROJECT_ROOT / "scripts" / "project_cli.py"

    if not cli_path.exists():
        print_result("CLI script location", False, f"File not found: {cli_path}")
        return False

    print_result("CLI script location", True, f"Found at {cli_path}")
    return True


def test_project_cli_syntax():
    """Test 6: project_cli.py has valid syntax"""
    print_header("TEST 6: CLI Script Syntax")

    cli_path = PROJECT_ROOT / "scripts" / "project_cli.py"

    try:
        import py_compile
        py_compile.compile(str(cli_path), doraise=True)
        print_result("Syntax validation", True, "No syntax errors")
        return True

    except SyntaxError as e:
        print_result("Syntax validation", False, f"Syntax error: {e}")
        return False
    except Exception as e:
        print_result("Syntax validation", False, f"Compilation error: {e}")
        return False


def test_audit_script():
    """Test 7: audit_current_task.py can be called"""
    print_header("TEST 7: Audit Script Execution")

    audit_path = PROJECT_ROOT / "scripts" / "audit_current_task.py"

    if not audit_path.exists():
        print_result("Audit script", False, f"File not found: {audit_path}")
        return False

    try:
        result = subprocess.run(
            ["python3", str(audit_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            print_result(
                "Audit execution",
                True,
                f"All audit checks passed"
            )
            return True
        else:
            print_result(
                "Audit execution",
                False,
                f"Audit failed with return code {result.returncode}"
            )
            return False

    except subprocess.TimeoutExpired:
        print_result("Audit execution", False, "Audit script timeout")
        return False
    except Exception as e:
        print_result("Audit execution", False, f"Error: {e}")
        return False


def test_logs_dir():
    """Test 8: logs directory exists or can be created"""
    print_header("TEST 8: Logs Directory")

    logs_dir = PROJECT_ROOT / "logs"

    if logs_dir.exists():
        if not logs_dir.is_dir():
            print_result("Logs directory", False, "logs exists but is not a directory")
            return False

        print_result("Logs directory", True, f"Directory exists at {logs_dir}")
        return True

    # Try to create it
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        print_result("Logs directory", True, f"Created at {logs_dir}")
        return True

    except Exception as e:
        print_result("Logs directory", False, f"Cannot create: {e}")
        return False


def main():
    """Run all tests"""
    print()
    print("=" * 80)
    print(f"{CYAN}🔍 PIPELINE INTEGRITY TEST{RESET}")
    print(f"{CYAN}Task #099.02: Critical Pipeline Repair{RESET}")
    print("=" * 80)
    print()

    # Run all tests
    tests = [
        ("Bridge script exists", test_bridge_exists),
        ("Bridge syntax valid", test_bridge_syntax),
        ("Git command available", test_git_available),
        ("Notion updater importable", test_notion_imports),
        ("CLI script exists", test_project_cli_exists),
        ("CLI syntax valid", test_project_cli_syntax),
        ("Audit script executable", test_audit_script),
        ("Logs directory available", test_logs_dir),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{RED}⚠️  Test {test_name} crashed: {e}{RESET}")
            results.append((test_name, False))

    # Summary
    print()
    print("=" * 80)
    print(f"📊 TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("=" * 80)
        print(f"{GREEN}✅ ALL TESTS PASSED - Pipeline is healthy{RESET}")
        print("=" * 80)
        print()
        print("You can now safely run:")
        print(f"  python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print("=" * 80)
        print(f"{RED}❌ SOME TESTS FAILED - Fix issues before using finish command{RESET}")
        print("=" * 80)
        print()
        print("Failed tests:")
        for test_name, result in results:
            if not result:
                print(f"  - {test_name}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
