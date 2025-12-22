#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 Notion Issues 数据库
用于跟踪工单和任务进度
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

def create_issues_database():
    """创建 Issues 数据库"""

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # 首先获取知识库数据库作为父页面
    knowledge_db_id = "2cfc8858-2b4e-801b-b15b-d96893b7ba09"

    # 搜索一个可以作为父页面的位置
    search_response = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"page_size": 1}
    )

    if search_response.status_code != 200:
        print(f"❌ 无法搜索 Notion 工作区: {search_response.text}")
        return None

    results = search_response.json().get("results", [])
    if not results:
        print("❌ 找不到任何页面作为父页面")
        print("⚠️  请在 Notion 中手动创建 Issues 数据库，然后共享给 MT5-CRS-Bot 集成")
        return None

    parent_page = results[0]
    parent_id = parent_page["id"]

    print(f"📄 使用父页面: {parent_id}")

    # 创建 Issues 数据库
    database_data = {
        "parent": {
            "type": "page_id",
            "page_id": parent_id
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "MT5-CRS Issues"
                }
            }
        ],
        "properties": {
            "任务名称": {
                "title": {}
            },
            "ID": {
                "rich_text": {}
            },
            "状态": {
                "status": {
                    "options": [
                        {"name": "待开始", "color": "gray"},
                        {"name": "进行中", "color": "blue"},
                        {"name": "已完成", "color": "green"},
                        {"name": "已搁置", "color": "red"}
                    ],
                    "groups": [
                        {
                            "name": "待处理",
                            "color": "gray",
                            "option_ids": []
                        },
                        {
                            "name": "进行中",
                            "color": "blue",
                            "option_ids": []
                        },
                        {
                            "name": "已完成",
                            "color": "green",
                            "option_ids": []
                        }
                    ]
                }
            },
            "优先级": {
                "select": {
                    "options": [
                        {"name": "P0", "color": "red"},
                        {"name": "P1", "color": "orange"},
                        {"name": "P2", "color": "yellow"},
                        {"name": "P3", "color": "gray"}
                    ]
                }
            },
            "类型": {
                "select": {
                    "options": [
                        {"name": "Feature", "color": "blue"},
                        {"name": "Bug", "color": "red"},
                        {"name": "Docs", "color": "green"},
                        {"name": "Refactor", "color": "purple"},
                        {"name": "Test", "color": "yellow"}
                    ]
                }
            },
            "负责人": {
                "rich_text": {}
            },
            "开始时间": {
                "date": {}
            },
            "完成时间": {
                "date": {}
            },
            "代码变更行数": {
                "number": {
                    "format": "number"
                }
            },
            "最后提交": {
                "rich_text": {}
            },
            "GitHub 链接": {
                "url": {}
            },
            "描述": {
                "rich_text": {}
            }
        }
    }

    print("\n🔨 正在创建 Issues 数据库...")
    response = requests.post(
        "https://api.notion.com/v1/databases",
        headers=headers,
        json=database_data
    )

    if response.status_code == 200:
        db = response.json()
        db_id = db["id"]
        print(f"\n✅ Issues 数据库创建成功！")
        print(f"📊 数据库名称: MT5-CRS Issues")
        print(f"🆔 数据库 ID: {db_id}")
        print(f"\n📝 请将以下 ID 添加到 .env 文件:")
        print(f"NOTION_ISSUES_DB_ID={db_id}")
        print(f"\n⚠️  重要: 请在 Notion 中打开此数据库，确保 MT5-CRS-Bot 集成有访问权限")
        return db_id
    else:
        print(f"\n❌ 创建数据库失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        print(f"\n💡 备选方案: 请在 Notion 中手动创建 Issues 数据库")
        print(f"   1. 在 Notion 中创建一个新的数据库")
        print(f"   2. 命名为 'MT5-CRS Issues'")
        print(f"   3. 添加属性: 任务名称(title), ID(text), 状态(status)")
        print(f"   4. 点击右上角 '...' -> 'Add connections' -> 选择 'MT5-CRS-Bot'")
        print(f"   5. 复制数据库 URL 中的 ID，添加到 .env 文件")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 MT5-CRS Issues 数据库创建工具")
    print("=" * 80)
    print()

    db_id = create_issues_database()

    print("\n" + "=" * 80)
    if db_id:
        print("✅ 完成！")
    else:
        print("⚠️  需要手动操作，请按照上述说明在 Notion 中创建数据库")
    print("=" * 80)
