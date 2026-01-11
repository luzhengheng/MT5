#!/usr/bin/env python3
"""
Bridge 工作流程深度诊断
测试完整的 AI 审查流程，包括 JSON 解析
"""
import os
import sys
import json
import re
from dotenv import load_dotenv

try:
    from curl_cffi import requests
    print("✅ curl_cffi 已安装。\n")
except ImportError:
    print("❌ curl_cffi 未安装。")
    sys.exit(1)

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

print("=" * 80)
print("🔍 Bridge 工作流程深度诊断")
print("=" * 80)

# 模拟实际的 Git Diff
MOCK_DIFF = """
diff --git a/src/test.py b/src/test.py
index 1234567..abcdef0 100644
--- a/src/test.py
+++ b/src/test.py
@@ -1,3 +1,5 @@
+import logging
+
 def test_function():
-    return "old"
+    logging.info("New implementation")
+    return "new"
"""

# 使用与 Bridge 完全相同的提示词
prompt = f"""
你是一位资深的 Python 架构师。请审查以下 Git Diff (用于量化交易系统):
{MOCK_DIFF[:1500]}

检查重点：
1. 是否有明显的逻辑错误或死锁风险？
2. 是否有硬编码的敏感信息（密码/密钥）？
3. 代码风格是否符合 PEP8？

**必须输出 JSON**:
{{
    "status": "PASS" | "FAIL",
    "reason": "简短的通过或拒绝理由",
    "commit_message_suggestion": "feat(scope): ..."
}}
"""

print(f"📤 发送的提示词长度: {len(prompt)} 字符")
print(f"📋 提示词片段:")
print("─" * 80)
print(prompt[:300])
print("...")
print("─" * 80)

print("\n🚀 发送请求到 Gemini API...")

try:
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        },
        timeout=60,
        impersonate="chrome110"
    )

    print(f"\n📡 响应状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        # 提取内容
        if 'choices' in data:
            content = data['choices'][0]['message']['content']
        elif 'content' in data:
            content = data['content']
        else:
            print("❌ 未知的响应格式")
            print(f"   响应字段: {list(data.keys())}")
            sys.exit(1)

        print(f"\n💬 原始响应内容:")
        print("=" * 80)
        print(content)
        print("=" * 80)

        # 测试 Bridge 的 JSON 提取逻辑
        print("\n🔧 测试 JSON 提取流程...")
        print("─" * 80)

        # Step 1: 清理 JSON 包装
        clean_content = content.replace("```json", "").replace("```", "").strip()
        print(f"Step 1: 清理 markdown 包装")
        print(f"   长度: {len(content)} → {len(clean_content)}")

        # Step 2: 正则提取 JSON
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', clean_content)
        if json_match:
            clean_content = json_match.group(0)
            print(f"Step 2: 正则提取 JSON 块")
            print(f"   匹配成功，提取长度: {len(clean_content)}")
        else:
            print(f"Step 2: 正则提取 JSON 块")
            print(f"   ⚠️  未找到 JSON 块")

        print(f"\n📋 提取的 JSON 内容:")
        print("─" * 80)
        print(clean_content[:500])
        print("─" * 80)

        # Step 3: JSON 解析
        try:
            result = json.loads(clean_content)
            print(f"\n✅ JSON 解析成功！")
            print(f"   字段: {list(result.keys())}")
            print(f"\n📊 解析结果:")
            print(f"   • status: {result.get('status')}")
            print(f"   • reason: {result.get('reason')}")
            print(f"   • commit_message: {result.get('commit_message_suggestion')}")

            # 检查是否通过
            if result.get('status') == 'PASS':
                print(f"\n✅✅✅ 成功: AI 审查通过！")
                print(f"   建议的提交信息: {result.get('commit_message_suggestion')}")
                print(f"\n🎯 结论: Bridge 应该使用这个 AI 生成的提交信息。")
            else:
                print(f"\n❌ AI 拒绝了提交")
                print(f"   原因: {result.get('reason')}")
                print(f"\n🎯 结论: Bridge 应该阻止提交。")

        except json.JSONDecodeError as je:
            print(f"\n❌ JSON 解析失败")
            print(f"   错误: {str(je)}")
            print(f"   位置: 第 {je.lineno} 行, 第 {je.colno} 列")
            print(f"\n🎯 结论: Bridge 会触发 Fail-Open 降级，使用文件数统计。")

    else:
        print(f"\n❌ API 请求失败")
        print(f"   状态码: {response.status_code}")
        print(f"   响应体: {response.text[:300]}")

    print("\n" + "=" * 80)
    print("🏁 诊断完成")
    print("=" * 80)

except Exception as e:
    print(f"\n💥 异常: {str(e)}")
    print(f"   类型: {type(e).__name__}")
    sys.exit(1)
