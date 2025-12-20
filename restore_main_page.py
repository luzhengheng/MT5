#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复并重构 MT5-CRS 主页面，包含数据库块
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def restore_page_content(page_id: str):
    """恢复页面内容，包含数据库块"""
    try:
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"

        # 完整的页面内容
        page_children = [
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
                        {"text": {"content": "量化交易系统自动化知识管理平台 - 由 Claude Sonnet 4.5 & Gemini Pro 协同构建\n\n专注于 MT5 实盘交易系统的开发与部署，集成先进的资金管理、风险控制与策略执行能力。"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📊 核心数据库"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "四大核心数据库构成完整的知识管理生态系统："}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "🧠 AI Command Center"
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "📋 Issues"
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "💡 Knowledge Graph"
                }
            },
            {
                "object": "block",
                "type": "child_database",
                "child_database": {
                    "title": "📚 Documentation"
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🎯 当前焦点：工单 #011"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "📋 "}},
                        {"text": {"content": "实盘交易系统对接 (MT5 API)", "italic": True}},
                        {"text": {"content": "\n\n🔹 P1 (High Priority)\n🔹 MT5 API 连接与认证\n🔹 实时行情数据接收\n🔹 订单执行与风险控制\n🔹 集成 Kelly 资金管理\n🔹 多品种交易支持"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "🔗 快速访问"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "🧠 "}},
                        {"text": {"content": "AI Command Center", "url": "https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "📋 "}},
                        {"text": {"content": "Issues 数据库", "url": "https://www.notion.so/2cfc88582b4e816b9a15d85908bf4a21"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "💡 "}},
                        {"text": {"content": "Knowledge Graph", "url": "https://www.notion.so/2cfc88582b4e811d83bed3bd3957adea"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "📚 "}},
                        {"text": {"content": "Documentation", "url": "https://www.notion.so/2cfc88582b4e81608466cc6e3fb527e9"}}
                    ]
                }
            }
        ]

        response = requests.patch(url, headers=notion_headers(), json={"children": page_children})

        if response.status_code == 200:
            print("✅ 主页面内容已恢复")
            return True
        else:
            print(f"❌ 恢复主页面失败: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ 恢复主页面时出错: {e}")
        return False

def add_database_blocks(page_id: str):
    """添加现有的数据库块到页面"""
    try:
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"

        # 简化的内容，重点是数据库块
        simple_children = [
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
                        {"text": {"content": "量化交易系统自动化知识管理平台\n\n专注于 MT5 实盘交易系统开发与部署。"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "📊 核心数据库"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": "四大核心数据库："}}]
                }
            }
        ]

        # 添加现有的数据库块
        database_ids = [
            ("2cfc8858-2b4e-8176-b2f5-cb8749599e30", "📚 Documentation (Old)"),
            ("2cfc8858-2b4e-817e-a4a5-fe17be413d64", "🧠 AI Command Center"),
            ("2cfc8858-2b4e-816b-9a15-d85908bf4a21", "📋 Issues"),
            ("2cfc8858-2b4e-811d-83be-d3bd3957adea", "💡 Knowledge Graph"),
            ("2cfc8858-2b4e-8160-8466-cc6e3fb527e9", "📚 Documentation")
        ]

        for db_id, db_title in database_ids:
            # 获取数据库信息
            db_url = f"{NOTION_BASE_URL}/databases/{db_id}"
            db_response = requests.get(db_url, headers=notion_headers())

            if db_response.status_code == 200:
                db_info = db_response.json()
                title = db_info.get("title", [])
                if title:
                    db_title = title[0].get("plain_text", db_title)

                simple_children.append({
                    "object": "block",
                    "type": "child_database",
                    "child_database": {
                        "title": db_title
                    }
                })

        response = requests.patch(url, headers=notion_headers(), json={"children": simple_children})

        if response.status_code == 200:
            print("✅ 数据库块已添加到主页面")
            return True
        else:
            print(f"❌ 添加数据库块失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 添加数据库块时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 恢复 MT5-CRS 主页面")
    print("=" * 60)

    # 主页面 ID
    main_page_id = "2cfc8858-2b4e-81a1-8d44-dca3beb4e380"

    print("\n📝 恢复主页面内容...")
    if restore_page_content(main_page_id):
        print("\n✅ 主页面已完全恢复")
    else:
        print("\n🔄 尝试添加数据库块...")
        add_database_blocks(main_page_id)

    print("\n🔗 访问链接:")
    print(f"   MT5-CRS Nexus: https://www.notion.so/MT5-CRS-Nexus-2cfc88582b4e81a18d44dca3beb4e380")
    print("\n🎯 页面现在应该显示:")
    print("   • 🚀 清晰的标题和介绍")
    print("   • 📊 四个核心数据库")
    print("   • 🎯 工单 #011 焦点")
    print("   • 🔗 快速访问链接")

if __name__ == "__main__":
    main()