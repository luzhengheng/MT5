#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus - 简化版
适用于基础数据库的自动化协同中台
"""

import os
import sys
import time
import textwrap
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_ID = os.getenv("NOTION_DB_ID")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/opt/mt5-crs/")

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

def call_gemini_api(prompt):
    """调用 Gemini API"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"

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
                    "rich_text": [{"text": {"content": "🤖 Gemini Response"}}]
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

def monitor_database():
    """监控数据库并处理新页面"""
    print(f"👀 正在监控 Notion 数据库...")
    print("检测到新页面时会自动调用 Gemini 处理")
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

def process_page(page):
    """处理单个页面"""
    page_id = page["id"]
    props = page["properties"]

    # 获取标题（尝试多种可能的字段名）
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

    # 简单的上下文处理：基于标题推断相关文件
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

    # 调用 Gemini
    print("   -> 🧠 Gemini 思考中...")
    reply_text = call_gemini_api(full_prompt)

    if "❌" in reply_text:
        print(f"   -> {reply_text}")
        return

    # 写入回复
    print("   -> 📝 写入回复...")
    if add_response_to_page(page_id, reply_text):
        print("✅ 处理完成")
    else:
        print("❌ 写入失败")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Notion Nexus - 简化版")
    print("=" * 60)

    if not DATABASE_ID:
        print("❌ NOTION_DB_ID 未配置")
        return

    # 测试连接
    print("🔧 测试连接...")
    try:
        url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            print("✅ Notion 连接成功！")
            db_info = response.json()
            print(f"📊 数据库: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")

            print("\n📝 使用说明:")
            print("1. 在 Notion 数据库中创建新页面")
            print("2. 设置页面标题（如：分析风险管理模块的代码质量）")
            print("3. 保存页面，系统会自动检测并处理")
            print("4. Gemini 的回复会自动添加到页面中")
            print("\n开始监控...\n")

            monitor_database()
        else:
            print(f"❌ 无法访问数据库: {response.status_code}")

    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    main()