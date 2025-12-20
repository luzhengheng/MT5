#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Gemini 3 Pro 原版连接
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PROXY_API_KEY = os.getenv("PROXY_API_KEY")
PROXY_API_URL = os.getenv("PROXY_API_URL")

def test_gemini_3_pro():
    """测试 Gemini 3 Pro 原版"""
    print("🧪 测试 Gemini 3 Pro 原版...")

    try:
        url = f"{PROXY_API_URL}/v1/chat/completions"

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {PROXY_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": "gemini-3-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的量化开发助手。"
                },
                {
                    "role": "user",
                    "content": "请用一句话介绍你自己。"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        print(f"📡 调用 API: {url}")
        print(f"🤖 模型: gemini-3-pro")

        response = requests.post(url, headers=headers, json=data, timeout=30)

        print(f"\n📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and result['choices']:
                reply = result['choices'][0]['message']['content']
                print(f"✅ Gemini 3 Pro 原版连接成功！")
                print(f"\n🤖 Gemini 3 Pro 回复:")
                print(f"{reply}")
                print(f"\n✅ 配置更新成功！现在 Notion Nexus 将使用 Gemini 3 Pro 原版。")
                return True
            else:
                print(f"❌ 响应格式异常")
                return False
        else:
            print(f"❌ API 调用失败")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Gemini 3 Pro 原版测试")
    print("=" * 60)
    test_gemini_3_pro()
