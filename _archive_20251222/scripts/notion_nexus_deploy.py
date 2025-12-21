#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus 自动部署脚本
自动创建 Notion 数据库架构
"""

import os
import sys
import requests
import json
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

def create_database(parent_page_id: str, database_config: Dict) -> Optional[str]:
    """创建数据库"""
    try:
        url = f"{NOTION_BASE_URL}/databases"

        # 添加 parent page ID
        database_config["parent"] = {
            "type": "page_id",
            "page_id": parent_page_id
        }

        response = requests.post(url, headers=notion_headers(), json=database_config)

        if response.status_code == 200:
            result = response.json()
            return result["id"]
        else:
            print(f"❌ 创建数据库失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ 创建数据库时出错: {e}")
        return None

def get_or_create_main_page() -> Optional[str]:
    """获取或创建主页面 MT5-CRS Nexus"""
    try:
        # 首先搜索是否已存在 MT5-CRS Nexus 页面
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
                    print(f"✅ 找到已存在的主页面: {page['id']}")
                    return page["id"]

        # 如果不存在，获取用户的所有页面，选择第一个作为父页面
        print("🔍 搜索可用页面...")
        search_response = requests.post(search_url, headers=notion_headers(), json={"filter": {"property": "object", "value": "page"}})

        if search_response.status_code == 200:
            pages = search_response.json().get("results", [])
            if pages:
                # 选择第一个页面作为父页面
                root_page_id = pages[0]["id"]
                page_title = pages[0].get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
                print(f"📍 使用页面 '{page_title}' 作为父页面: {root_page_id}")
            else:
                print("❌ 未找到任何页面，无法创建主页面")
                return None
        else:
            print("❌ 无法获取页面列表")
            return None

        page_data = {
            "parent": {
                "type": "page_id",
                "page_id": root_page_id
            },
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": "MT5-CRS Nexus"
                            }
                        }
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": "🚀 MT5-CRS Nexus 知识库"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": "自动化知识管理系统 - 由 Claude Sonnet 4.5 & Gemini Pro 协同构建\n\n"}}
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📊 数据库架构"}}]
                    }
                }
            ]
        }

        create_url = f"{NOTION_BASE_URL}/pages"
        response = requests.post(create_url, headers=notion_headers(), json=page_data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 主页面创建成功: {result['id']}")
            return result["id"]
        else:
            print(f"❌ 创建主页面失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ 处理主页面时出错: {e}")
        return None

def get_ai_command_center_schema() -> Dict:
    """AI Command Center 数据库结构"""
    return {
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "🧠 AI Command Center"
                }
            }
        ],
        "properties": {
            "Topic": {
                "title": {}
            },
            "Status": {
                "status": {
                    "options": [
                        {"name": "Draft", "color": "gray"},
                        {"name": "Ready to Send", "color": "blue"},
                        {"name": "Processing", "color": "yellow"},
                        {"name": "Replied", "color": "green"}
                    ]
                }
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
    }

def get_issues_schema() -> Dict:
    """Issues 数据库结构"""
    return {
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "📋 Issues"
                }
            }
        ],
        "properties": {
            "Task Name": {
                "title": {}
            },
            "ID": {
                "rich_text": {}
            },
            "Status": {
                "status": {
                    "options": [
                        {"name": "Backlog", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Done", "color": "green"},
                        {"name": "Blocked", "color": "red"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "P0 (Critical)", "color": "red"},
                        {"name": "P1 (High)", "color": "orange"},
                        {"name": "P2 (Normal)", "color": "blue"}
                    ]
                }
            },
            "Timeline": {
                "date": {}
            },
            "Code Delta": {
                "number": {
                    "format": "number"
                }
            }
        }
    }

def get_knowledge_graph_schema() -> Dict:
    """Knowledge Graph 数据库结构"""
    return {
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "💡 Knowledge Graph"
                }
            }
        ],
        "properties": {
            "Concept": {
                "title": {}
            },
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
            "Verification": {
                "status": {
                    "options": [
                        {"name": "Verified", "color": "green"},
                        {"name": "Theoretical", "color": "yellow"},
                        {"name": "Deprecated", "color": "red"}
                    ]
                }
            },
            "GitHub Permalink": {
                "url": {}
            }
        }
    }

def get_documentation_schema() -> Dict:
    """Documentation 数据库结构"""
    return {
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "📚 Documentation"
                }
            }
        ],
        "properties": {
            "Doc Name": {
                "title": {}
            },
            "Attachment": {
                "files": {}
            }
        }
    }

def create_all_databases(main_page_id: str) -> List[str]:
    """创建所有数据库"""
    databases = []

    # 1. AI Command Center (最重要的数据库)
    print("🧠 创建 AI Command Center 数据库...")
    ai_db_id = create_database(main_page_id, get_ai_command_center_schema())
    if ai_db_id:
        databases.append(("🧠 AI Command Center", ai_db_id))
        print(f"   ✅ AI Command Center: {ai_db_id}")

    # 2. Issues
    print("📋 创建 Issues 数据库...")
    issues_db_id = create_database(main_page_id, get_issues_schema())
    if issues_db_id:
        databases.append(("📋 Issues", issues_db_id))
        print(f"   ✅ Issues: {issues_db_id}")

    # 3. Knowledge Graph
    print("💡 创建 Knowledge Graph 数据库...")
    kg_db_id = create_database(main_page_id, get_knowledge_graph_schema())
    if kg_db_id:
        databases.append(("💡 Knowledge Graph", kg_db_id))
        print(f"   ✅ Knowledge Graph: {kg_db_id}")

    # 4. Documentation
    print("📚 创建 Documentation 数据库...")
    doc_db_id = create_database(main_page_id, get_documentation_schema())
    if doc_db_id:
        databases.append(("📚 Documentation", doc_db_id))
        print(f"   ✅ Documentation: {doc_db_id}")

    return databases

def setup_database_relations(databases: List[str]):
    """设置数据库之间的关联关系"""
    print("🔗 设置数据库关联关系...")

    # 这里可以添加代码来设置 Relation 字段
    # 由于需要 database_id，我们可以在创建完成后通过更新数据库来添加这些字段

    ai_db_id = None
    issues_db_id = None
    kg_db_id = None

    for name, db_id in databases:
        if "AI Command Center" in name:
            ai_db_id = db_id
        elif "Issues" in name:
            issues_db_id = db_id
        elif "Knowledge Graph" in name:
            kg_db_id = db_id

    # TODO: 添加 relation 字段到 AI Command Center
    # 这需要额外的 API 调用来更新数据库 schema

def update_env_file(ai_db_id: str):
    """更新 .env 文件中的 NOTION_DB_ID"""
    env_file = "/opt/mt5-crs/.env"

    if not os.path.exists(env_file):
        print(f"⚠️ {env_file} 文件不存在，将创建新文件")

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
    print("🚀 Notion Nexus 自动部署脚本")
    print("=" * 60)

    # 检查配置
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN 未配置")
        print("请在 .env 文件中设置您的 Notion Integration Token")
        return

    print("✅ Notion Token 已配置")
    print("📋 即将创建以下 4 个数据库:")
    print("   1. 🧠 AI Command Center (AI 协同控制台)")
    print("   2. 📋 Issues (工单管理)")
    print("   3. 💡 Knowledge Graph (知识图谱)")
    print("   4. 📚 Documentation (文档归档)")

    # 获取或创建主页面
    print("\n🔧 创建主页面...")
    main_page_id = get_or_create_main_page()

    if not main_page_id:
        print("❌ 无法创建主页面，部署失败")
        return

    # 创建所有数据库
    print("\n🏗️ 创建数据库架构...")
    databases = create_all_databases(main_page_id)

    if len(databases) == 4:
        print("\n✅ 所有数据库创建成功！")

        # 找到 AI Command Center 的 ID
        ai_db_id = None
        for name, db_id in databases:
            if "AI Command Center" in name:
                ai_db_id = db_id
                break

        # 更新环境变量
        if ai_db_id:
            update_env_file(ai_db_id)

        print("\n📊 数据库 IDs:")
        for name, db_id in databases:
            print(f"   {name}: {db_id}")

        print("\n🎯 下一步:")
        print("1. 在 Notion 中访问您的 MT5-CRS Nexus 页面")
        print("2. 连接 MT5-CRS-Bot 到 🧠 AI Command Center 数据库")
        print("3. 运行 python nexus_with_proxy.py 开始监控")

    else:
        print(f"\n⚠️ 只创建了 {len(databases)}/4 个数据库")
        print("请检查错误信息并手动创建失败的数据库")

if __name__ == "__main__":
    main()