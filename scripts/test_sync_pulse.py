#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion-Git 同步验证脚本

测试 Notion API 集成是否正常工作。

使用方法:
    python3 scripts/test_sync_pulse.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(msg, level="INFO"):
    """Print colored log message"""
    colors = {
        "SUCCESS": GREEN,
        "ERROR": RED,
        "WARN": YELLOW,
        "INFO": CYAN,
        "PHASE": BLUE
    }
    prefix = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARN": "⚠️",
        "INFO": "ℹ️",
        "PHASE": "🔹"
    }
    color = colors.get(level, RESET)
    symbol = prefix.get(level, "")
    print(f"{color}{symbol} {msg}{RESET}")


def test_environment_variables():
    """测试环境变量配置"""
    print()
    log("Step 1: Testing Environment Variables", "PHASE")
    print("-" * 80)

    errors = []

    # Check NOTION_TOKEN
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        log("NOTION_TOKEN not set", "ERROR")
        errors.append("NOTION_TOKEN")
    else:
        # Mask token for security
        masked_token = f"{notion_token[:10]}...{notion_token[-5:]}" if len(notion_token) > 20 else "***"
        log(f"NOTION_TOKEN found: {masked_token}", "SUCCESS")

    # Check NOTION_ISSUES_DB_ID
    db_id = os.getenv("NOTION_ISSUES_DB_ID")
    if not db_id:
        log("NOTION_ISSUES_DB_ID not set", "WARN")
        log("  This is optional but recommended", "INFO")
    else:
        masked_id = f"{db_id[:8]}...{db_id[-5:]}" if len(db_id) > 15 else "***"
        log(f"NOTION_ISSUES_DB_ID found: {masked_id}", "SUCCESS")

    print()

    if errors:
        log(f"Missing required variables: {', '.join(errors)}", "ERROR")
        return False
    else:
        log("All required environment variables are set", "SUCCESS")
        return True


def test_notion_api_connection():
    """测试 Notion API 连接"""
    print()
    log("Step 2: Testing Notion API Connection", "PHASE")
    print("-" * 80)

    try:
        import requests

        notion_token = os.getenv("NOTION_TOKEN")
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28"
        }

        # Test with a simple API call (get user info)
        response = requests.get(
            "https://api.notion.com/v1/users/me",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            user_data = response.json()
            user_name = user_data.get("name", "Unknown")
            log(f"Connected as: {user_name}", "SUCCESS")
            log("Notion API connection working", "SUCCESS")
            print()
            return True
        else:
            log(f"API returned status code: {response.status_code}", "ERROR")
            log(f"Response: {response.text[:200]}", "ERROR")
            print()
            return False

    except Exception as e:
        log(f"Connection test failed: {str(e)}", "ERROR")
        print()
        return False


def test_notion_updater_import():
    """测试 notion_updater 模块导入"""
    print()
    log("Step 3: Testing notion_updater Module", "PHASE")
    print("-" * 80)

    try:
        from scripts.utils import notion_updater

        # Check for required functions
        required_functions = [
            'update_task_status',
            'find_page_by_ticket_id',
            'get_headers'
        ]

        missing = []
        for func_name in required_functions:
            if hasattr(notion_updater, func_name):
                log(f"Function '{func_name}' found", "SUCCESS")
            else:
                log(f"Function '{func_name}' NOT found", "ERROR")
                missing.append(func_name)

        print()

        if missing:
            log(f"Missing functions: {', '.join(missing)}", "ERROR")
            return False
        else:
            log("All required functions available", "SUCCESS")
            return True

    except ImportError as e:
        log(f"Failed to import notion_updater: {str(e)}", "ERROR")
        print()
        return False


def test_dry_run_update():
    """测试 dry-run 状态更新（不实际执行）"""
    print()
    log("Step 4: Dry-Run Status Update Test", "PHASE")
    print("-" * 80)

    try:
        from scripts.utils import notion_updater

        # Create a test commit URL
        test_commit_url = f"https://github.com/test/repo/commit/abc123{datetime.now().strftime('%Y%m%d%H%M%S')}"

        log("Test parameters:", "INFO")
        log(f"  Status: Done", "INFO")
        log(f"  Commit URL: {test_commit_url}", "INFO")

        # We won't actually call the function without a valid page_id
        # Just verify the function signature is correct
        import inspect
        sig = inspect.signature(notion_updater.update_task_status)
        params = list(sig.parameters.keys())

        expected_params = ['page_id', 'status', 'commit_url', 'token']
        if all(p in params for p in expected_params[:3]):  # token is optional
            log("Function signature is correct", "SUCCESS")
            print()
            return True
        else:
            log(f"Unexpected function signature: {params}", "ERROR")
            print()
            return False

    except Exception as e:
        log(f"Dry-run test failed: {str(e)}", "ERROR")
        print()
        return False


def main():
    """主测试函数"""
    print()
    print("=" * 80)
    print(f"{BLUE}🧪 Notion-Git Sync Pulse Verification{RESET}")
    print("=" * 80)
    print()
    print(f"Test execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Environment variables
    results.append(("Environment Variables", test_environment_variables()))

    # Test 2: API connection
    if results[0][1]:  # Only test if env vars are set
        results.append(("Notion API Connection", test_notion_api_connection()))
    else:
        results.append(("Notion API Connection", False))
        log("Skipping API test (env vars not set)", "WARN")

    # Test 3: Module import
    results.append(("Module Import", test_notion_updater_import()))

    # Test 4: Dry-run test
    if results[2][1]:  # Only if module imported successfully
        results.append(("Dry-Run Test", test_dry_run_update()))
    else:
        results.append(("Dry-Run Test", False))
        log("Skipping dry-run test (module not available)", "WARN")

    # Summary
    print()
    print("=" * 80)
    print(f"{CYAN}📊 Test Results Summary{RESET}")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status_icon = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
        print(f"{status_icon} {test_name}")

    print()
    print("-" * 80)

    if passed == total:
        print(f"{GREEN}✅ Sync Verified - All {total} tests passed!{RESET}")
        print()
        print(f"{CYAN}Next steps:{RESET}")
        print(f"  • The Notion-Git sync is ready to use")
        print(f"  • Run 'python3 scripts/project_cli.py finish' to test live sync")
        print(f"  • Check Notion dashboard for status updates")
        print()
        return 0
    else:
        print(f"{RED}❌ Tests Failed - {passed}/{total} passed{RESET}")
        print()
        print(f"{YELLOW}Recommended actions:{RESET}")
        print(f"  1. Check .env file for NOTION_TOKEN")
        print(f"  2. Verify Notion integration permissions")
        print(f"  3. Review error messages above")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
