#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus - 中文适配版
适配中文数据库字段的自动化协同中台
"""

import os
import sys
import time
import textwrap
import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_ID = os.getenv("NOTION_DB_ID")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/opt/mt5-crs/")

# 初始化检查
if not NOTION_TOKEN or not GEMINI_KEY:
    print("❌ 错误: .env 文件中缺少 NOTION_TOKEN 或 GEMINI_API_KEY")
    print("请编辑 .env 文件，填入正确的密钥")
    sys.exit(1)

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

def get_database_properties():
    """获取数据库字段信息"""
    try:
        response = requests.get(
            f"{NOTION_BASE_URL}/databases/{DATABASE_ID}",
            headers=notion_headers()
        )
        if response.status_code == 200:
            db_info = response.json()
            return db_info.get("properties", {})
        return {}
    except:
        return {}

def find_field_mapping():
    """查找字段映射关系"""
    properties = get_database_properties()
    mapping = {}

    # 查找标题字段
    for prop_name, prop_info in properties.items():
        if prop_info.get("type") == "title":
            mapping["topic"] = prop_name
            print(f"📝 找到标题字段: '{prop_name}'")
            break

    # 查找状态字段
    for prop_name, prop_info in properties.items():
        if prop_info.get("type") == "status":
            mapping["status"] = prop_name
            print(f"📊 找到状态字段: '{prop_name}'")
            break

    # 查找多选字段
    for prop_name, prop_info in properties.items():
        if prop_info.get("type") == "multi_select":
            mapping["context_files"] = prop_name
            print(f"📁 找到上下文字段: '{prop_name}'")
            break

    # 查找文本字段
    for prop_name, prop_info in properties.items():
        if prop_info.get("type") == "rich_text":
            mapping["prompt"] = prop_name
            print(f"💬 找到提示字段: '{prop_name}'")
            break

    return mapping

def call_gemini_api(prompt):
    """调用 Gemini API"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"

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

def update_page_status(page_id, status, field_mapping):
    """更新页面状态"""
    try:
        url = f"{NOTION_BASE_URL}/pages/{page_id}"

        # 构建更新数据
        update_data = {
            "properties": {}
        }

        # 设置状态字段
        if field_mapping.get("status"):
            update_data["properties"][field_mapping["status"]] = {
                "status": {"name": status}
            }

        response = requests.patch(url, headers=notion_headers(), json=update_data)
        if response.status_code != 200:
            print(f"⚠️ 更新状态失败: {response.status_code}")

    except Exception as e:
        print(f"⚠️ 更新状态时出错: {e}")

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

def process_page(page, field_mapping):
    """处理单个页面"""
    page_id = page["id"]
    props = page["properties"]

    topic_field = field_mapping.get("topic", "Topic")

    # 1. 获取标题
    try:
        topic = props[topic_field]["title"][0]["plain_text"]
    except (KeyError, IndexError):
        topic = "Untitled Task"

    print(f"🚀 处理任务: {topic}")

    # 2. 更新状态为处理中
    update_page_status(page_id, "Processing", field_mapping)

    # 3. 读取上下文文件
    context_str = ""
    context_field = field_mapping.get("context_files")
    if context_field and context_field in props and props[context_field]["multi_select"]:
        for item in props[context_field]["multi_select"]:
            print(f"   -> 读取文件: {item['name']}")
            context_str += read_local_file(item['name'])

    # 4. 构建 Prompt
    user_prompt = topic

    prompt_field = field_mapping.get("prompt")
    if prompt_field and prompt_field in props and props[prompt_field]["rich_text"]:
        user_prompt += "\n\n" + props[prompt_field]["rich_text"][0]["plain_text"]

    full_prompt = f"""你是一位资深的量化开发助手，请根据提供的上下文文件和用户请求，给出专业、技术性的回答。

Context Files:
{context_str}

User Request:
{user_prompt}

请用中文回答，提供详细的代码示例和解决方案。回答格式使用 Markdown。"""

    # 5. 调用 Gemini
    print("   -> 🧠 Gemini 思考中...")
    reply_text = call_gemini_api(full_prompt)

    if "❌" in reply_text:
        print(f"   -> {reply_text}")
        update_page_status(page_id, "Error", field_mapping)
        return

    # 6. 写入回复到 Notion
    print("   -> 📝 写入回复...")
    if add_response_to_page(page_id, reply_text):
        update_page_status(page_id, "Replied", field_mapping)
        print("✅ 完成")
    else:
        update_page_status(page_id, "Error", field_mapping)

def monitor_database():
    """监控数据库并处理待处理的任务"""
    print(f"👀 正在监控 Notion 数据库...")
    print("按 Ctrl+C 停止监控\n")

    # 获取字段映射
    field_mapping = find_field_mapping()

    if not field_mapping.get("topic"):
        print("❌ 未找到标题字段，请确保数据库有标题字段")
        return

    while True:
        try:
            url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query"

            # 构建查询 - 查找状态为 "Ready to Send" 或类似状态的页面
            data = {
                "filter": {
                    "property": field_mapping.get("status", "Status"),
                    "status": {"equals": "Ready to Send"}
                }
            }

            response = requests.post(url, headers=notion_headers(), json=data)

            if response.status_code == 200:
                query_result = response.json()
                pages = query_result.get("results", [])

                if pages:
                    print(f"发现 {len(pages)} 个待处理任务")
                    for page in pages:
                        process_page(page, field_mapping)
                        print("-" * 40)
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
            else:
                print(f"⚠️ 查询数据库失败: {response.status_code}")

        except KeyboardInterrupt:
            print("\n👋 监控已停止")
            break
        except Exception as e:
            print(f"\n⚠️ 监控错误: {e}")

        time.sleep(5)

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Notion Nexus - 中文适配版")
    print("=" * 60)

    if not DATABASE_ID:
        print("❌ NOTION_DB_ID 未配置")
        return

    # 测试连接
    print("🔧 测试 Notion 连接...")
    try:
        url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            print("✅ Notion 连接成功！")
            db_info = response.json()
            print(f"📊 数据库: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            print("\n开始监控任务...\n")
            monitor_database()
        else:
            print(f"❌ 无法访问数据库: {response.status_code}")
            print("请检查 NOTION_DB_ID 是否正确，以及机器人是否已连接到数据库。")

    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    main()