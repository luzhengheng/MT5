#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS Bridge Dependency Verification Script
验证 AI Bridge 核心依赖 (curl_cffi) 可用性

Task #014 交付物
用途: 确保 INF/HUB 节点能够正常使用 curl_cffi 进行 TLS 通信
"""

import sys
import json
from datetime import datetime
from typing import Dict, Any


def verify_curl_cffi() -> Dict[str, Any]:
    """
    验证 curl_cffi 可用性并进行简单测试

    Returns:
        dict: 包含验证结果的字典
            - available: bool, 是否可用
            - version: str, 版本信息 (如果可用)
            - test_result: str, 测试结果
            - error: str, 错误信息 (如果失败)
    """
    result = {
        "available": False,
        "version": None,
        "test_result": "NOT_TESTED",
        "error": None
    }

    try:
        # 1. 尝试导入 curl_cffi
        from curl_cffi import requests
        result["available"] = True

        # 2. 获取版本信息
        try:
            import curl_cffi
            result["version"] = getattr(curl_cffi, "__version__", "unknown")
        except:
            result["version"] = "unknown"

        # 3. 执行简单的 TLS 握手测试
        # 注意: 仅进行 HEAD 请求以最小化流量
        try:
            # 使用 Google 作为 TLS 测试目标 (高可用性)
            response = requests.head(
                "https://www.google.com",
                verify=True,
                timeout=5
            )
            result["test_result"] = f"SUCCESS (HTTP {response.status_code})"
        except Exception as e:
            result["test_result"] = f"FAILED: {str(e)}"

    except ImportError as e:
        result["error"] = f"ImportError: {str(e)}"
        result["test_result"] = "NOT_AVAILABLE"
    except Exception as e:
        result["error"] = f"UnexpectedError: {str(e)}"
        result["test_result"] = "ERROR"

    return result


def verify_pyyaml() -> Dict[str, Any]:
    """
    验证 PyYAML 可用性 (辅助检查)

    Returns:
        dict: 包含验证结果的字典
    """
    result = {
        "available": False,
        "version": None,
        "error": None
    }

    try:
        import yaml
        result["available"] = True
        result["version"] = getattr(yaml, "__version__", "unknown")
    except ImportError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"UnexpectedError: {str(e)}"

    return result


def main():
    """主函数: 执行所有依赖验证并输出结果"""
    print("=" * 60)
    print("🔍 MT5-CRS Bridge Dependency Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print()

    # 验证 curl_cffi
    print("[1/2] Verifying curl_cffi...")
    curl_result = verify_curl_cffi()
    if curl_result["available"]:
        print(f"  ✓ curl_cffi is available (version: {curl_result['version']})")
        print(f"  ✓ TLS Test: {curl_result['test_result']}")
    else:
        print(f"  ✗ curl_cffi is NOT available")
        print(f"  ✗ Error: {curl_result['error']}")
    print()

    # 验证 PyYAML (辅助)
    print("[2/2] Verifying PyYAML (auxiliary)...")
    yaml_result = verify_pyyaml()
    if yaml_result["available"]:
        print(f"  ✓ PyYAML is available (version: {yaml_result['version']})")
    else:
        print(f"  ✗ PyYAML is NOT available")
        print(f"  ✗ Error: {yaml_result['error']}")
    print()

    # 汇总结果
    print("=" * 60)
    all_passed = curl_result["available"] and yaml_result["available"]

    if all_passed:
        print("✅ STATUS: Bridge dependency OK")
        print("=" * 60)
        return 0
    else:
        print("❌ STATUS: Bridge dependency MISSING")
        print("=" * 60)
        print()
        print("📝 Action Items:")
        if not curl_result["available"]:
            print("  - Install curl_cffi: pip install curl_cffi")
        if not yaml_result["available"]:
            print("  - Install PyYAML: pip install pyyaml")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
