#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Review Bridge - Connectivity Test

验证 Gemini Review Bridge 的网络连通性
检查 API Key、网络连接和服务可用性
"""

import sys
import os
from dotenv import load_dotenv

# --- 尝试导入 curl_cffi ---
try:
    from curl_cffi import requests
    CURL_AVAILABLE = True
except ImportError:
    CURL_AVAILABLE = False
    print("⚠️  WARNING: curl_cffi not found. Install with: pip install curl_cffi")
    import requests as std_requests
    requests = std_requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "INVALID")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")

# --- 颜色配置 ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def test_connectivity():
    """
    执行连通性测试的三个阶段
    """
    print("=" * 80)
    print("Gemini Review Bridge - Connectivity Test")
    print("=" * 80)
    print()

    # --- Test 1: 检查 API Key ---
    print("[Test 1] Checking API Key...")
    if GEMINI_API_KEY == "INVALID":
        print(f"{RED}❌ FAIL: GEMINI_API_KEY not set or invalid{RESET}")
        return False
    print(f"{GREEN}✅ PASS: API Key found (first 8 chars: {GEMINI_API_KEY[:8]}...){RESET}")
    print()

    # --- Test 2: ping API 端点 ---
    print("[Test 2] Pinging API endpoint...")
    print(f"    Target: {GEMINI_BASE_URL}/chat/completions")
    try:
        if CURL_AVAILABLE:
            resp = requests.get(
                f"{GEMINI_BASE_URL}/health",
                headers={"Authorization": f"Bearer {GEMINI_API_KEY}"},
                timeout=10,
                impersonate="chrome110"
            )
        else:
            resp = requests.get(
                f"{GEMINI_BASE_URL}/health",
                headers={"Authorization": f"Bearer {GEMINI_API_KEY}"},
                timeout=10
            )
        print(f"{GREEN}✅ PASS: HTTP {resp.status_code}{RESET}")
        print(f"    Response headers: {dict(resp.headers)}")
    except Exception as e:
        print(f"{RED}❌ FAIL: {type(e).__name__}: {str(e)}{RESET}")
        return False
    print()

    # --- Test 3: 测试实际 API 调用 ---
    print("[Test 3] Testing actual API call...")
    try:
        test_prompt = 'Respond with JSON: {"status": "ok"}'

        if CURL_AVAILABLE:
            resp = requests.post(
                f"{GEMINI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {GEMINI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gemini-pro",
                    "messages": [{"role": "user", "content": test_prompt}],
                    "temperature": 0.3
                },
                timeout=30,
                impersonate="chrome110"
            )
        else:
            resp = requests.post(
                f"{GEMINI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {GEMINI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gemini-pro",
                    "messages": [{"role": "user", "content": test_prompt}],
                    "temperature": 0.3
                },
                timeout=30
            )

        if resp.status_code == 200:
            data = resp.json()
            usage = data.get("usage", {})
            print(f"{GREEN}✅ PASS: HTTP 200{RESET}")
            print(f"    Input Tokens:  {usage.get('prompt_tokens', 0)}")
            print(f"    Output Tokens: {usage.get('completion_tokens', 0)}")
            print(f"    Total Tokens:  {usage.get('total_tokens', 0)}")
            return True
        else:
            print(f"{RED}❌ FAIL: HTTP {resp.status_code}{RESET}")
            print(f"    Response: {resp.text[:500]}")
            return False

    except Exception as e:
        print(f"{RED}❌ FAIL: {type(e).__name__}: {str(e)}{RESET}")
        return False


def main():
    """
    执行所有测试
    """
    success = test_connectivity()
    print()
    print("=" * 80)
    if success:
        print(f"{GREEN}All tests PASSED ✅{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}Some tests FAILED ❌{RESET}")
        print()
        print("Troubleshooting steps:")
        print("1. Check API Key: echo $GEMINI_API_KEY")
        print("2. Check network: ping api.yyds168.net")
        print("3. Check VPN status (if applicable)")
        sys.exit(1)


if __name__ == "__main__":
    main()
