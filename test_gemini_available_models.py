#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Gemini API 可用的模型列表
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY 未配置")
    exit(1)

print("=" * 80)
print("🔍 检查 Gemini API 可用模型")
print("=" * 80)

# 获取可用模型列表
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"

try:
    response = requests.get(url, timeout=10)
    print(f"\n状态码: {response.status_code}\n")

    if response.status_code == 200:
        result = response.json()
        models = result.get("models", [])

        print(f"找到 {len(models)} 个可用模型:\n")
        for model in models:
            model_name = model.get("name", "").replace("models/", "")
            print(f"✓ {model_name}")

            # 检查支持的方法
            supported = model.get("supportedGenerationMethods", [])
            if supported:
                print(f"  └─ 支持方法: {', '.join(supported)}")

            # 显示 display_name
            display_name = model.get("displayName", "")
            if display_name:
                print(f"  └─ 显示名: {display_name}")

        print("\n" + "=" * 80)
        print("推荐使用的模型:")
        print("=" * 80)

        # 查找推荐模型
        for model in models:
            model_name = model.get("name", "").replace("models/", "")
            if "gemini" in model_name.lower():
                if "generateContent" in model.get("supportedGenerationMethods", []):
                    print(f"✓ {model_name}")

    else:
        print(f"错误: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ 错误: {e}")
