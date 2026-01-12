#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus - 支持 API 中转的版本
支持多种 API 中转方案
"""

import os
import sys
import time
import textwrap
import requests
from dotenv import load_dotenv
from src.utils.path_utils import get_project_root

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")
PROXY_API_URL = os.getenv("PROXY_API_URL")
DATABASE_ID = os.getenv("NOTION_DB_ID")
PROJECT_ROOT = str(get_project_root())

# Notion API 配置
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    """获取 Notion API 请求头"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def call_gemini_direct(prompt):
    """直接调用 Google Gemini API"""
    try:
        # 使用稳定版本 gemini-1.5-flash (修正：gemini-2.5-flash 不存在)
        # 参考 Gemini Pro 审查建议：验证正确的API模型名称
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        response = requests.post(url, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "❌ Gemini 返回空响应"
        else:
            return f"❌ Gemini API Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ 调用 Gemini 时出错: {e}"

def call_gemini_proxy_1(prompt):
    """使用中转服务 1 - Gemini Proxy"""
    try:
        url = "https://api.aiproxy.io/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {PROXY_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gemini-2.0-flash-exp",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的量化开发助手，请提供专业的技术分析和建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                return "❌ 中转服务返回空响应"
        else:
            return f"❌ 中转服务 Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ 调用中转服务时出错: {e}"

def call_gemini_proxy_2(prompt):
    """使用中转服务 2 - 固定使用 Gemini 3 Pro Preview"""
    try:
        url = f"{PROXY_API_URL}/v1/chat/completions"

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {PROXY_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": "gemini-3-pro-preview",  # 固定使用 Gemini 3 Pro Preview (实测可用)
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的量化开发助手，请提供专业的技术分析和建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        print(f"   -> 使用模型: gemini-3-pro-preview (Gemini 3 Pro)")
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                return "❌ 中转服务返回空响应"
        else:
            return f"❌ 中转服务 Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ 调用 Gemini 3 Pro 时出错: {e}"

def call_gemini_api(prompt):
    """智能选择 Gemini API 调用方式"""
    print("   -> 🔄 选择 API 服务...")

    # 优先使用配置的中转服务
    if PROXY_API_URL and PROXY_API_KEY and not PROXY_API_KEY.startswith("your_"):
        print("   -> 📡 使用购买的中转服务...")
        result = call_gemini_proxy_2(prompt)
        if not result.startswith("❌"):
            print("   -> ✅ 中转服务成功")
            return result
        else:
            print(f"   -> ⚠️ 中转服务失败: {result}")

    # 备选：尝试其他中转服务
    if PROXY_API_KEY and not PROXY_API_KEY.startswith("your_"):
        print("   -> 📡 尝试备用中转服务...")
        result = call_gemini_proxy_1(prompt)
        if not result.startswith("❌"):
            print("   -> ✅ 备用中转成功")
            return result
        else:
            print(f"   -> ⚠️ 备用中转失败: {result}")

    # 最后尝试直接 API
    print("   -> 🔗 尝试直接 API...")
    result = call_gemini_direct(prompt)
    if result.startswith("❌"):
        print(f"   -> ❌ 所有 API 都失败了")
    else:
        print("   -> ✅ 直接 API 成功")

    return result

def read_local_file(filepath):
    """读取本地文件内容"""
    safe_path = os.path.normpath(os.path.join(PROJECT_ROOT, filepath.strip()))
    if not safe_path.startswith(PROJECT_ROOT):
        return f"\n[Security Alert: Access denied to {filepath}]\n"

    if os.path.exists(safe_path):
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 5000:
                    content = content[:5000] + "\n... [文件过长已截断]"
                return f"\n\n--- FILE: {filepath} ---\n{content}\n--- END FILE ---\n"
        except Exception as e:
            return f"\n[Error reading file: {e}]\n"
    return f"\n[WARNING: File not found: {filepath}]\n"

def add_response_to_page(page_id, response_text):
    """将回复添加到页面"""
    try:
        chunks = textwrap.wrap(response_text, width=1800, replace_whitespace=False)

        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🤖 AI Response (via Proxy)"}}]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            }
        ]

        for chunk in chunks:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": chunk}}]
                }
            })

        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"
        response = requests.patch(url, headers=notion_headers(), json={"children": children})

        if response.status_code != 200:
            print(f"⚠️ 添加回复失败: {response.status_code}")
            return False

        return True

    except Exception as e:
        print(f"⚠️ 添加回复时出错: {e}")
        return False

def process_page(page):
    """处理单个页面"""
    page_id = page["id"]
    props = page["properties"]

    # 获取标题
    title = "Untitled Task"
    for field_name in ["名称", "Topic", "Title", "Name"]:
        if field_name in props and props[field_name].get("title"):
            title = props[field_name]["title"][0]["plain_text"]
            break

    print(f"🚀 处理任务: {title}")

    # 检查是否已经有回复
    if page.get("has_children"):
        print("   -> 页面已有内容，跳过处理")
        return

    # 智能文件关联
    context_str = ""
    if "风险管理" in title or "risk" in title.lower():
        files_to_read = ["src/strategy/risk_manager.py", "docs/BACKTEST_GUIDE.md"]
    elif "特征工程" in title or "feature" in title.lower():
        files_to_read = ["src/feature_engineering/", "docs/ML_GUIDE.md"]
    elif "回测" in title or "backtest" in title.lower():
        files_to_read = ["bin/run_backtest.py", "src/reporting/"]
    elif "代码" in title or "code" in title.lower():
        files_to_read = ["src/"]
    else:
        files_to_read = []

    for filepath in files_to_read:
        print(f"   -> 读取文件: {filepath}")
        context_str += read_local_file(filepath)

    # 构建提示
    full_prompt = f"""你是一位资深的量化开发助手。用户提出了以下问题或任务：

任务标题: {title}

相关代码上下文:
{context_str}

请根据任务标题和上下文，提供专业的技术回答。如果涉及代码分析，请提供具体的建议和改进方案。请用中文回答，格式使用 Markdown。"""

    # 调用 AI
    print("   -> 🧠 AI 思考中...")
    reply_text = call_gemini_api(full_prompt)

    if "❌" in reply_text:
        print(f"   -> {reply_text}")

        # 如果所有 API 都失败，添加一个备用回复
        fallback_response = f"""# 🤖 AI 分析结果

## 任务：{title}

很抱歉，AI 服务暂时不可用。但根据任务标题，我可以提供以下基础分析：

## 建议的分析方向：

### 1. 代码质量检查
- 检查错误处理机制
- 分析性能瓶颈
- 审查代码结构

### 2. 功能分析
- 验证业务逻辑正确性
- 检查边界条件处理
- 评估可维护性

### 3. 优化建议
- 提升代码可读性
- 优化算法效率
- 增强错误处理

### 4. 手动检查文件
请检查以下相关文件：
{chr(10).join([f"- {file}" for file in files_to_read])}

---
*系统将在 API 服务恢复后提供完整的 AI 分析结果。*"""

        print("   -> 📝 写入备用回复...")
        add_response_to_page(page_id, fallback_response)
        print("✅ 处理完成（备用回复）")
        return

    # 写入回复
    print("   -> 📝 写入回复...")
    if add_response_to_page(page_id, reply_text):
        print("✅ 处理完成")
    else:
        print("❌ 写入失败")

def monitor_database():
    """监控数据库并处理新页面"""
    print(f"👀 正在监控 Notion 数据库...")
    print("检测到新页面时会自动调用 AI 处理")
    print("支持多种 API 中转方案")
    print("按 Ctrl+C 停止监控\n")

    processed_pages = set()

    while True:
        try:
            url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query"
            response = requests.post(url, headers=notion_headers(), json={})

            if response.status_code == 200:
                query_result = response.json()
                pages = query_result.get("results", [])

                new_pages = [page for page in pages if page["id"] not in processed_pages]

                if new_pages:
                    print(f"发现 {len(new_pages)} 个新页面")
                    for page in new_pages:
                        process_page(page)
                        processed_pages.add(page["id"])
                        print("-" * 40)
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            print("\n👋 监控已停止")
            break
        except Exception as e:
            print(f"\n⚠️ 监控错误: {e}")

        time.sleep(5)

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Notion Nexus - API 中转版")
    print("=" * 60)

    # 显示当前配置
    print("📋 当前配置:")
    print(f"   Notion Token: {'✅ 已配置' if NOTION_TOKEN else '❌ 未配置'}")
    print(f"   Gemini Key: {'✅ 已配置' if GEMINI_KEY else '❌ 未配置'}")
    print(f"   代理 API Key: {'✅ 已配置' if PROXY_API_KEY and not PROXY_API_KEY.startswith('your_') else '❌ 未配置'}")
    print(f"   代理 API URL: {'✅ 已配置' if PROXY_API_URL else '❌ 未配置'}")

    if not DATABASE_ID:
        print("❌ NOTION_DB_ID 未配置")
        return

    print(f"\n🔄 API 调用策略:")
    print("   1. 尝试中转服务 (如果配置了代理)")
    print("   2. 尝试自定义中转 (如果配置了URL)")
    print("   3. 尝试直接 Gemini API")
    print("   4. 如果都失败，提供基础分析")

    # 测试连接
    print(f"\n🔧 测试连接...")
    try:
        url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            print("✅ Notion 连接成功！")
            db_info = response.json()
            print(f"📊 数据库: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")

            print("\n📝 使用说明:")
            print("1. 在 Notion 数据库中创建新页面")
            print("2. 设置页面标题，系统会自动处理")
            print("3. 支持多种 API 中转方案")
            print("4. 如果 API 不可用，会提供基础分析")
            print("\n开始监控...\n")

            monitor_database()
        else:
            print(f"❌ 无法访问数据库: {response.status_code}")

    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    main()