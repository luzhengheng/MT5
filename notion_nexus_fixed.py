#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus 修复版自动部署脚本
先创建基础数据库，然后更新字段
"""

import os
import sys
import requests
import json
import time
from dotenv import load_dotenv
from typing import Dict, List, Optional

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    """获取 Notion API 请求头"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def create_database(parent_page_id: str, title: str) -> Optional[str]:
    """创建基础数据库（不带复杂属性）"""
    try:
        url = f"{NOTION_BASE_URL}/databases"

        database_config = {
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ],
            "properties": {
                "Name": {
                    "title": {}
                }
            }
        }

        response = requests.post(url, headers=notion_headers(), json=database_config)

        if response.status_code == 200:
            result = response.json()
            return result["id"]
        else:
            print(f"❌ 创建基础数据库失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ 创建数据库时出错: {e}")
        return None

def get_main_page_id() -> Optional[str]:
    """获取主页面 ID"""
    try:
        # 搜索 MT5-CRS Nexus 页面
        search_url = f"{NOTION_BASE_URL}/search"
        search_data = {
            "query": "MT5-CRS Nexus",
            "filter": {
                "property": "object",
                "value": "page"
            }
        }

        response = requests.post(search_url, headers=notion_headers(), json=search_data)

        if response.status_code == 200:
            results = response.json().get("results", [])
            for page in results:
                title = page.get("properties", {}).get("title", {}).get("title", [])
                if title and title[0].get("plain_text") == "MT5-CRS Nexus":
                    print(f"✅ 找到主页面: {page['id']}")
                    return page["id"]

        print("❌ 未找到 MT5-CRS Nexus 主页面")
        return None

    except Exception as e:
        print(f"❌ 搜索主页面时出错: {e}")
        return None

def update_database_properties(db_id: str, properties: Dict):
    """更新数据库属性"""
    try:
        url = f"{NOTION_BASE_URL}/databases/{db_id}"

        # 注意：PUT 请求会替换整个数据库配置
        response = requests.request("PATCH", url, headers=notion_headers(), json={"properties": properties})

        if response.status_code == 200:
            print(f"   ✅ 数据库属性更新成功")
            return True
        else:
            print(f"   ❌ 更新属性失败: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ 更新属性时出错: {e}")
        return False

def create_and_configure_databases(main_page_id: str) -> List[Dict]:
    """创建并配置所有数据库"""
    databases = []

    # 1. AI Command Center
    print("🧠 创建 AI Command Center 数据库...")
    ai_db_id = create_database(main_page_id, "🧠 AI Command Center")
    if ai_db_id:
        # 配置属性
        ai_properties = {
            "Name": {"title": {}},
            "Status": {
                "status": {}
            },
            "Context Files": {
                "multi_select": {
                    "options": [
                        {"name": "src/strategy/risk_manager.py", "color": "red"},
                        {"name": "src/feature_engineering/", "color": "blue"},
                        {"name": "bin/run_backtest.py", "color": "green"},
                        {"name": "docs/ML_GUIDE.md", "color": "orange"},
                        {"name": "src/models/", "color": "purple"},
                        {"name": "src/monitoring/", "color": "pink"}
                    ]
                }
            }
        }

        if update_database_properties(ai_db_id, ai_properties):
            databases.append({"name": "🧠 AI Command Center", "id": ai_db_id})

    # 2. Issues
    print("📋 创建 Issues 数据库...")
    issues_db_id = create_database(main_page_id, "📋 Issues")
    if issues_db_id:
        issues_properties = {
            "Name": {"title": {}},
            "ID": {"rich_text": {}},
            "Status": {"status": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "P0 (Critical)", "color": "red"},
                        {"name": "P1 (High)", "color": "orange"},
                        {"name": "P2 (Normal)", "color": "blue"}
                    ]
                }
            },
            "Timeline": {"date": {}},
            "Code Delta": {"number": {"format": "number"}}
        }

        if update_database_properties(issues_db_id, issues_properties):
            databases.append({"name": "📋 Issues", "id": issues_db_id})

    # 3. Knowledge Graph
    print("💡 创建 Knowledge Graph 数据库...")
    kg_db_id = create_database(main_page_id, "💡 Knowledge Graph")
    if kg_db_id:
        kg_properties = {
            "Name": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "Math", "color": "blue"},
                        {"name": "Risk", "color": "red"},
                        {"name": "Architecture", "color": "orange"},
                        {"name": "Infra", "color": "green"}
                    ]
                }
            },
            "Verification": {"status": {}},
            "GitHub Permalink": {"url": {}}
        }

        if update_database_properties(kg_db_id, kg_properties):
            databases.append({"name": "💡 Knowledge Graph", "id": kg_db_id})

    # 4. Documentation
    print("📚 创建 Documentation 数据库...")
    doc_db_id = create_database(main_page_id, "📚 Documentation")
    if doc_db_id:
        doc_properties = {
            "Name": {"title": {}},
            "Attachment": {"files": {}}
        }

        if update_database_properties(doc_db_id, doc_properties):
            databases.append({"name": "📚 Documentation", "id": doc_db_id})

    return databases

def update_env_file(ai_db_id: str):
    """更新 .env 文件中的 NOTION_DB_ID"""
    env_file = "/opt/mt5-crs/.env"

    # 读取现有内容
    content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()

    # 更新或添加 NOTION_DB_ID
    lines = content.split('\n')
    updated_lines = []
    found_db_id = False

    for line in lines:
        if line.startswith('NOTION_DB_ID='):
            updated_lines.append(f'NOTION_DB_ID={ai_db_id}')
            found_db_id = True
        else:
            updated_lines.append(line)

    if not found_db_id:
        updated_lines.append(f'NOTION_DB_ID={ai_db_id}')

    # 写回文件
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))

    print(f"✅ 已更新 {env_file} 中的 NOTION_DB_ID")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Notion Nexus 修复版自动部署脚本")
    print("=" * 60)

    # 检查配置
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN 未配置")
        return

    print("✅ Notion Token 已配置")

    # 获取主页面
    print("\n🔧 获取主页面...")
    main_page_id = get_main_page_id()

    if not main_page_id:
        print("❌ 无法获取主页面")
        return

    # 创建和配置数据库
    print("\n🏗️ 创建和配置数据库...")
    databases = create_and_configure_databases(main_page_id)

    if databases:
        print(f"\n✅ 成功创建 {len(databases)} 个数据库!")

        # 找到 AI Command Center
        ai_db_id = None
        for db in databases:
            if "AI Command Center" in db["name"]:
                ai_db_id = db["id"]
                break

        # 更新环境变量
        if ai_db_id:
            update_env_file(ai_db_id)

        print("\n📊 数据库列表:")
        for db in databases:
            print(f"   {db['name']}: {db['id']}")

        print("\n🎯 下一步:")
        print("1. 在 Notion 中访问您的 MT5-CRS Nexus 页面")
        print("2. 连接 MT5-CRS-Bot 到 🧠 AI Command Center 数据库")
        print("3. 运行 python nexus_with_proxy.py 开始监控")
        print("4. 测试创建新任务页面")

    else:
        print("\n❌ 数据库创建失败")

if __name__ == "__main__":
    main()