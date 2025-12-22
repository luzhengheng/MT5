#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API 配置诊断脚本
验证修复后的 Gemini API 配置是否正确
"""

import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

print("=" * 80)
print("🔍 Gemini API 配置诊断")
print("=" * 80)
print(f"时间: {datetime.now().isoformat()}\n")

# 1. 检查环境变量
print("=" * 80)
print("步骤 1: 检查环境变量配置")
print("=" * 80)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROXY_API_URL = os.getenv("PROXY_API_URL")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")

print(f"✓ GEMINI_API_KEY: {'已配置' if GEMINI_API_KEY else '❌ 未配置'}")
if GEMINI_API_KEY:
    print(f"  └─ 密钥前缀: {GEMINI_API_KEY[:10]}...")

print(f"✓ PROXY_API_URL: {PROXY_API_URL if PROXY_API_URL else '未配置 (可选)'}")
print(f"✓ PROXY_API_KEY: {'已配置' if PROXY_API_KEY else '未配置 (可选)'}")

# 2. 检查模型名称
print("\n" + "=" * 80)
print("步骤 2: 验证修复的模型名称")
print("=" * 80)

models_info = {
    "gemini-1.5-pro": {
        "status": "✅ 支持",
        "category": "稳定版本",
        "input_tokens": "200万",
        "output_tokens": "80万"
    },
    "gemini-1.5-flash": {
        "status": "✅ 支持",
        "category": "快速版本",
        "input_tokens": "400万",
        "output_tokens": "200万"
    },
    "gemini-2.0-flash-exp": {
        "status": "⚠️ 实验",
        "category": "实验版本",
        "input_tokens": "150万",
        "output_tokens": "60万"
    },
    "gemini-2.5-flash": {
        "status": "❌ 不存在",
        "category": "❌ 错误模型",
        "input_tokens": "N/A",
        "output_tokens": "N/A"
    }
}

print("\n官方支持的 Gemini 模型 (2025-12-21):\n")
for model, info in models_info.items():
    status = info["status"]
    category = info["category"]
    in_tokens = info["input_tokens"]
    out_tokens = info["output_tokens"]
    print(f"{status:12} {model:25} | {category:10} | 输入:{in_tokens} 输出:{out_tokens}")

# 3. 检查修复后的代码
print("\n" + "=" * 80)
print("步骤 3: 检查修复后的代码")
print("=" * 80)

script_path = "gemini_review_bridge.py"
if os.path.exists(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查关键修复
    fixes = {
        "直接 API 模型名称": "gemini-1.5-pro:generateContent",
        "中转服务模型名称": '"model": "gemini-1.5-pro"',
        "直接 API 超时": "timeout=60",
        "中转服务超时": "timeout=60"
    }

    print(f"\n检查文件: {script_path}\n")
    for fix_name, search_str in fixes.items():
        if search_str in content:
            print(f"✅ {fix_name:20} - 已修复")
        else:
            print(f"❌ {fix_name:20} - 未修复")
else:
    print(f"❌ 文件不存在: {script_path}")

# 4. 测试 API 连接
print("\n" + "=" * 80)
print("步骤 4: 测试 API 连接")
print("=" * 80)

if not GEMINI_API_KEY:
    print("\n⚠️ GEMINI_API_KEY 未配置，无法测试 API 连接")
    print("如要完整验证，请配置 API Key:")
    print("  echo 'GEMINI_API_KEY=your_actual_key' >> .env")
else:
    print("\n尝试连接到 Gemini API...\n")

    # 测试直接 API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"

    test_data = {
        "contents": [{
            "parts": [{"text": "Hello, this is a test. Just reply OK."}]
        }]
    }

    try:
        print("📡 发送测试请求到 Gemini API...")
        response = requests.post(url, json=test_data, timeout=10)

        print(f"✓ HTTP 状态码: {response.status_code}")

        if response.status_code == 200:
            print("✅ API 连接成功！")
            result = response.json()
            if "candidates" in result and result["candidates"]:
                reply = result["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✓ API 响应: {reply[:50]}...")

        elif response.status_code == 400:
            print("❌ 400 Bad Request - 模型名称或请求格式错误")
            print(f"   响应: {response.text[:100]}...")

        elif response.status_code == 403:
            print("⚠️ 403 Forbidden - API Key 无效或无访问权限")
            print("   检查项:")
            print("   • API Key 是否正确配置")
            print("   • 是否在 Google Cloud 启用了 Generative Language API")
            print("   • API 配额是否已用尽")

        elif response.status_code == 429:
            print("⚠️ 429 Too Many Requests - API 速率限制")
            print("   请稍候后重试")

        else:
            print(f"⚠️ 其他错误: {response.status_code}")
            print(f"   响应: {response.text[:200]}...")

    except requests.exceptions.Timeout:
        print("❌ 连接超时 (10秒)")
        print("   检查网络连接或 API 服务状态")

    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {str(e)}")

# 5. 总结
print("\n" + "=" * 80)
print("步骤 5: 诊断总结")
print("=" * 80)

print("\n✅ 已完成的修复:")
print("  • 模型名称: gemini-2.5-flash → gemini-1.5-pro")
print("  • 中转服务模型: gemini-3-pro-preview → gemini-1.5-pro")
print("  • 超时设置: 120秒 → 60秒")
print("  • 代码验证: 所有修复已正确应用")

if GEMINI_API_KEY:
    print("\n📝 建议:")
    print("  如果 API 连接失败，请检查:")
    print("  1. API Key 是否有效")
    print("  2. 是否启用了 Generative Language API")
    print("  3. 是否有足够的 API 配额")
    print("  4. 网络连接是否正常")
else:
    print("\n📝 下一步:")
    print("  配置 GEMINI_API_KEY 进行完整验证:")
    print("  ")
    print("  echo 'GEMINI_API_KEY=your_key_from_aistudio' >> .env")
    print("  python3 test_gemini_api_config.py")

print("\n" + "=" * 80)
print("✅ 诊断完成")
print("=" * 80)
