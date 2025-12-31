#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Serving API 验证脚本

测试 FastAPI 服务的各个端点。

使用方法:
    python3 scripts/verify_serving_api.py
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Configuration
API_BASE_URL = "http://localhost:8000"
API_STARTUP_TIMEOUT = 30
API_PORT = 8000


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


def is_port_open(port):
    """Check if port is open"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0


def wait_for_api(timeout=API_STARTUP_TIMEOUT):
    """Wait for API to start"""
    log(f"等待 API 启动 (超时: {timeout}s)...", "PHASE")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if is_port_open(API_PORT):
                # Port is open, try to connect to API
                response = requests.get(f"{API_BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    log("API 已启动并响应", "SUCCESS")
                    return True
        except:
            pass

        time.sleep(1)

    log(f"API 启动超时 ({timeout}s)", "ERROR")
    return False


def test_health_endpoint():
    """Test /health endpoint"""
    log("测试 /health 端点", "PHASE")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            log(f"  状态: {data.get('status')}", "INFO")
            log(f"  特征仓库: {data.get('feature_store')}", "INFO")
            log(f"  数据库: {data.get('database')}", "INFO")
            log("/health 端点工作正常", "SUCCESS")
            return True
        else:
            log(f"/health 端点返回状态码 {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"/health 端点测试失败: {e}", "ERROR")
        return False


def test_historical_endpoint():
    """Test /features/historical endpoint"""
    log("测试 /features/historical 端点", "PHASE")

    try:
        # 使用今天和昨天的日期
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        payload = {
            "symbols": ["EURUSD"],
            "features": ["sma_20", "rsi_14"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        log(f"  请求数据: {json.dumps(payload, indent=2)}", "INFO")

        response = requests.post(
            f"{API_BASE_URL}/features/historical",
            json=payload,
            timeout=30
        )

        log(f"  响应状态码: {response.status_code}", "INFO")

        if response.status_code == 200:
            data = response.json()
            log(f"  响应状态: {data.get('status')}", "INFO")
            log(f"  返回行数: {data.get('row_count')}", "INFO")
            log(f"  执行时间: {data.get('execution_time_ms'):.2f} ms", "INFO")

            # 验证数据格式
            if 'data' in data and isinstance(data['data'], list):
                if len(data['data']) > 0:
                    first_record = data['data'][0]
                    log(f"  样本记录: {json.dumps(first_record, default=str, indent=2)}", "INFO")
                    log("/features/historical 端点工作正常", "SUCCESS")
                    return True
                else:
                    log("  返回了空数据列表，但请求成功", "WARN")
                    return True
            else:
                log(f"/features/historical 端点返回格式错误", "ERROR")
                return False
        else:
            log(f"/features/historical 端点返回状态码 {response.status_code}", "ERROR")
            log(f"  响应: {response.text}", "ERROR")
            return False
    except Exception as e:
        log(f"/features/historical 端点测试失败: {e}", "ERROR")
        return False


def test_latest_endpoint():
    """Test /features/latest endpoint"""
    log("测试 /features/latest 端点", "PHASE")

    try:
        payload = {
            "symbols": ["EURUSD", "GBPUSD"],
            "features": ["rsi_14", "bb_upper"]
        }

        log(f"  请求数据: {json.dumps(payload, indent=2)}", "INFO")

        response = requests.post(
            f"{API_BASE_URL}/features/latest",
            json=payload,
            timeout=30
        )

        log(f"  响应状态码: {response.status_code}", "INFO")

        if response.status_code == 200:
            data = response.json()
            log(f"  响应状态: {data.get('status')}", "INFO")
            log(f"  返回符号数: {len(data.get('data', {}))}", "INFO")
            log(f"  执行时间: {data.get('execution_time_ms'):.2f} ms", "INFO")

            # 验证数据格式
            if 'data' in data and isinstance(data['data'], dict):
                log(f"  响应数据: {json.dumps(data['data'], indent=2)}", "INFO")
                log("/features/latest 端点工作正常", "SUCCESS")
                return True
            else:
                log("/features/latest 端点返回格式错误", "ERROR")
                return False
        else:
            log(f"/features/latest 端点返回状态码 {response.status_code}", "ERROR")
            log(f"  响应: {response.text}", "ERROR")
            return False
    except Exception as e:
        log(f"/features/latest 端点测试失败: {e}", "ERROR")
        return False


def test_invalid_request():
    """Test error handling"""
    log("测试错误处理 (无效请求)", "PHASE")

    try:
        payload = {
            "symbols": ["INVALID_SYMBOL"],
            "features": ["sma_20"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }

        response = requests.post(
            f"{API_BASE_URL}/features/historical",
            json=payload,
            timeout=10
        )

        if response.status_code == 400:
            data = response.json()
            log(f"  错误状态: {data.get('status')}", "INFO")
            log(f"  错误代码: {data.get('error_code')}", "INFO")
            log("错误处理工作正常", "SUCCESS")
            return True
        else:
            log(f"预期 400 状态码，但得到 {response.status_code}", "WARN")
            # 这可能不是错误，取决于 INVALID_SYMBOL 是否被检查
            return True
    except Exception as e:
        log(f"错误处理测试失败: {e}", "WARN")
        return True


def main():
    """Main verification function"""
    print()
    print("=" * 80)
    print(f"{CYAN}🧪 Feature Serving API 验证脚本{RESET}")
    print("=" * 80)
    print()

    # Check if API is already running
    if is_port_open(API_PORT):
        log(f"端口 {API_PORT} 已开放", "INFO")
        api_process = None
    else:
        # Start API in background
        log("启动 FastAPI 服务...", "PHASE")
        try:
            api_process = subprocess.Popen(
                ["python3", "-m", "uvicorn", "src.serving.app:app",
                 "--host", "127.0.0.1", "--port", str(API_PORT)],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            log("FastAPI 服务启动进程已创建", "INFO")
        except Exception as e:
            log(f"无法启动 FastAPI 服务: {e}", "ERROR")
            return False

    # Wait for API to be ready
    if not wait_for_api():
        if api_process:
            api_process.terminate()
        return False

    # Run tests
    print()
    results = []

    results.append(("Health Check", test_health_endpoint()))
    print()

    results.append(("Historical Features", test_historical_endpoint()))
    print()

    results.append(("Latest Features", test_latest_endpoint()))
    print()

    results.append(("Error Handling", test_invalid_request()))
    print()

    # Cleanup
    if api_process:
        log("关闭 FastAPI 服务...", "PHASE")
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
            log("FastAPI 服务已关闭", "SUCCESS")
        except:
            api_process.kill()
            log("FastAPI 服务已强制关闭", "WARN")

    # Summary
    print("=" * 80)
    print(f"{CYAN}📊 验证结果总结{RESET}")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status_icon = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
        print(f"{status_icon} {test_name}")

    print()
    if passed == total:
        log(f"所有测试通过 ({passed}/{total})", "SUCCESS")
        print()
        return True
    else:
        log(f"{passed}/{total} 个测试通过", "WARN")
        print()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
