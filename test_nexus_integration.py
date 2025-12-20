#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus 集成测试
测试系统各组件的协同工作
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

def test_env_loading():
    """测试环境变量加载"""
    print("🔍 测试环境变量加载...")
    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = ['NOTION_TOKEN', 'GEMINI_API_KEY']
        for var in required_vars:
            if os.getenv(var):
                print(f"✅ {var} 已加载")
            else:
                print(f"⚠️ {var} 未设置")
        return True
    except Exception as e:
        print(f"❌ 环境变量加载失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("🔍 测试文件操作...")
    try:
        from nexus_bridge import read_local_file

        # 测试读取现有文件
        result = read_local_file("nexus_bridge.py")
        if "def nexus_headers" in result:
            print("✅ 文件读取功能正常")
            return True
        else:
            print("❌ 文件读取异常")
            return False
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def test_api_connectivity():
    """测试 API 连接性"""
    print("🔍 测试 API 连接性...")

    # 测试网络连接
    try:
        import requests
        response = requests.get("https://api.notion.com/v1/", timeout=5)
        print("✅ 网络连接正常")
        return True
    except Exception as e:
        print(f"⚠️ 网络连接问题: {e}")
        return False

def run_integration_tests():
    """运行所有集成测试"""
    print("="*60)
    print("🧪 Notion Nexus 集成测试")
    print("="*60)

    tests = [
        ("环境变量", test_env_loading),
        ("文件操作", test_file_operations),
        ("网络连接", test_api_connectivity)
    ]

    results = []
    for name, test_func in tests:
        print(f"\n运行测试: {name}")
        result = test_func()
        results.append((name, result))

    # 测试结果总结
    print("\n" + "="*60)
    print("📊 测试结果")
    print("="*60)

    passed = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 通过")
            passed += 1
        else:
            print(f"❌ {name}: 失败")

    print(f"\n总体结果: {passed}/{len(results)} 通过")

    if passed == len(results):
        print("\n🎉 集成测试全部通过！")
        print("系统已准备就绪，可以开始使用。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")

if __name__ == "__main__":
    run_integration_tests()
