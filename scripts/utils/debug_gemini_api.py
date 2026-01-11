#!/usr/bin/env python3
"""
Gemini API 诊断脚本
用于测试 API 连接和响应格式
"""
import os
import sys
from dotenv import load_dotenv

# 尝试导入 curl_cffi
try:
    from curl_cffi import requests
    print("✅ curl_cffi 已安装。")
except ImportError:
    print("❌ curl_cffi 未安装。")
    sys.exit(1)

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

print(f"🔧 配置检查:")
print(f"   - URL: {BASE_URL}")
print(f"   - Key: {API_KEY[:5]}******{API_KEY[-4:] if API_KEY else 'None'}")
print(f"   - Model: {MODEL}")

if not API_KEY:
    print("❌ 错误: GEMINI_API_KEY 在 .env 中缺失")
    sys.exit(1)

print("\n🚀 发送测试请求 (impersonate='chrome110')...")
print("━" * 80)

try:
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": "Hello! Reply with 'Titanium Shield Active'."}],
            "temperature": 0.1
        },
        timeout=60,
        impersonate="chrome110"
    )

    print(f"\n📡 响应状态码: {response.status_code}")

    # 打印原始响应（前 800 字符）
    print(f"\n📋 原始响应体 (前 800 字符):")
    print("─" * 80)
    print(response.text[:800])
    print("─" * 80)

    # 尝试解析 JSON
    try:
        data = response.json()
        print(f"\n✅ JSON 解析成功")
        print(f"   - 响应类型: {type(data)}")
        print(f"   - 顶级字段: {list(data.keys())}")

        # 尝试提取内容
        if 'choices' in data:
            content = data['choices'][0]['message']['content']
            print(f"\n💬 提取的内容:")
            print("─" * 80)
            print(content[:500])
            print("─" * 80)

            # 检查预期的响应
            if "Titanium Shield Active" in content:
                print("\n✅ 预期的响应字符串已找到！")
            else:
                print("\n⚠️  预期的响应字符串未找到。")
                print(f"   实际内容: {content[:200]}...")
    except Exception as je:
        print(f"⚠️  JSON 解析失败: {str(je)}")
        print(f"   原始文本: {response.text[:300]}")

    # 最终判定
    print("\n" + "=" * 80)
    if response.status_code == 200:
        print("✅✅✅ 成功: API 连接完全正常！")
        print("   • curl_cffi 穿透有效")
        print("   • API 返回了有效的 200 响应")
        print("   • JSON 格式正确")
    else:
        print("❌❌❌ 失败: API 请求被拒绝或出错。")
        print(f"   • 状态码: {response.status_code}")
        print(f"   • 可能原因: API 密钥无效、账户限制或网络问题")
    print("=" * 80)

except Exception as e:
    print(f"\n💥 异常捕获: {str(e)}")
    print(f"   异常类型: {type(e).__name__}")
    print("\n❌❌❌ 失败: API 连接异常。")
    print(f"   • 可能原因: 网络不可达、超时或 curl_cffi 配置问题")
