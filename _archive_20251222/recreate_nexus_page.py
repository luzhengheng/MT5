#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新创建 MT5-CRS Nexus 主页面
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

def get_root_page():
    """获取根页面或第一个可用页面"""
    try:
        search_url = f"{NOTION_BASE_URL}/search"
        search_data = {
            "filter": {
                "property": "object",
                "value": "page"
            }
        }

        response = requests.post(search_url, headers=notion_headers(), json=search_data)

        if response.status_code == 200:
            pages = response.json().get("results", [])
            if pages:
                # 选择第一个页面作为父页面
                root_page_id = pages[0]["id"]
                page_title = pages[0].get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
                print(f"📍 使用页面 '{page_title}' 作为父页面: {root_page_id}")
                return root_page_id
        return None

    except Exception as e:
        print(f"❌ 获取根页面失败: {e}")
        return None

def create_nexus_page():
    """创建 MT5-CRS Nexus 主页面"""
    root_page_id = get_root_page()
    if not root_page_id:
        print("❌ 无法找到父页面")
        return None

    try:
        url = f"{NOTION_BASE_URL}/pages"

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
                                "content": "MT5-CRS Nexus 知识库"
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
                            {"text": {"content": "量化交易系统自动化知识管理平台\n\n由 Claude Sonnet 4.5 & Gemini Pro 协同构建\n\n专注于 MT5 实盘交易系统开发与部署。"}}
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
                            {"text": {"content": "四大核心数据库构成完整的知识管理生态系统：\n\n🧠 AI Command Center - AI 协同任务管理\n📋 Issues - 项目工单管理\n💡 Knowledge Graph - 核心知识沉淀\n📚 Documentation - 文档归档管理"}}
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
                        "rich_text": [{"text": {"content": "🎯 当前焦点：工单 #011"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": "📋 实盘交易系统对接 (MT5 API)\n\n🔹 P1 (High Priority)\n🔹 MT5 API 连接与认证\n🔹 实时行情数据接收\n🔹 订单执行与风险控制\n🔹 集成 Kelly 资金管理\n🔹 多品种交易支持"}}
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
                        "rich_text": [{"text": {"content": "🔗 快速访问链接"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": "• AI Command Center: https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64\n• Issues 数据库: https://www.notion.so/2cfc88582b4e816b9a15d85908bf4a21\n• Knowledge Graph: https://www.notion.so/2cfc88582b4e811d83bed3bd3957adea\n• Documentation: https://www.notion.so/2cfc88582b4e81608466cc6e3fb527e9"}}
                        ]
                    }
                }
            ]
        }

        response = requests.post(url, headers=notion_headers(), json=page_data)

        if response.status_code == 200:
            result = response.json()
            page_id = result["id"]
            page_url = result.get("url", "")
            print(f"✅ MT5-CRS Nexus 页面创建成功!")
            print(f"   ID: {page_id}")
            print(f"   URL: {page_url}")
            return page_id, page_url
        else:
            print(f"❌ 创建页面失败: {response.status_code} - {response.text}")
            return None, None

    except Exception as e:
        print(f"❌ 创建页面时出错: {e}")
        return None, None

def add_databases_to_page(page_id: str):
    """将现有数据库添加到新页面"""
    database_ids = [
        ("2cfc8858-2b4e-8176-b2f5-cb8749599e30", "📚 Documentation (Old)"),
        ("2cfc8858-2b4e-817e-a4a5-fe17be413d64", "🧠 AI Command Center"),
        ("2cfc8858-2b4e-816b-9a15-d85908bf4a21", "📋 Issues"),
        ("2cfc8858-2b4e-811d-83be-d3bd3957adea", "💡 Knowledge Graph"),
        ("2cfc8858-2b4e-8160-8466-cc6e3fb527e9", "📚 Documentation")
    ]

    print(f"\n🔗 链接现有数据库到页面...")

    for db_id, db_title in database_ids:
        # 获取数据库信息
        try:
            db_url = f"{NOTION_BASE_URL}/databases/{db_id}"
            db_response = requests.get(db_url, headers=notion_headers())

            if db_response.status_code == 200:
                db_info = db_response.json()
                title = db_info.get("title", [])
                if title:
                    db_title = title[0].get("plain_text", db_title)

                print(f"   📊 {db_title}: {db_id}")
            else:
                print(f"   ❌ 无法访问数据库 {db_id}")
        except Exception as e:
            print(f"   ❌ 检查数据库 {db_id} 时出错: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 重新创建 MT5-CRS Nexus 主页面")
    print("=" * 60)

    print("\n🏗️ 创建主页面...")
    page_id, page_url = create_nexus_page()

    if page_id and page_url:
        add_databases_to_page(page_id)

        print("\n" + "=" * 60)
        print("✅ MT5-CRS Nexus 重新创建完成！")
        print("=" * 60)

        print("\n🔗 访问链接:")
        print(f"   主页面: {page_url}")

        print("\n🗃️ 数据库直接链接:")
        print("   • 🧠 AI Command Center: https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64")
        print("   • 📋 Issues: https://www.notion.so/2cfc88582b4e816b9a15d85908bf4a21")
        print("   • 💡 Knowledge Graph: https://www.notion.so/2cfc88582b4e811d83bed3bd3957adea")
        print("   • 📚 Documentation: https://www.notion.so/2cfc88582b4e81608466cc6e3fb527e9")

        print("\n📝 手动操作建议:")
        print("1. 在 Notion 中打开新创建的主页面")
        print("2. 点击 + 号添加数据库块")
        print("3. 选择 'Link to database'")
        print("4. 搜索并添加四个核心数据库")
        print("5. 调整布局使其美观")

    else:
        print("\n❌ 页面创建失败")

if __name__ == "__main__":
    main()