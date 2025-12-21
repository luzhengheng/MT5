#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建新的 MT5-CRS Nexus 页面
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

def create_page_with_root(root_page_id: str):
    """在指定父页面下创建 MT5-CRS Nexus 页面"""
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
            return page_id, page_url
        else:
            print(f"❌ 创建页面失败: {response.status_code} - {response.text}")
            return None, None

    except Exception as e:
        print(f"❌ 创建页面时出错: {e}")
        return None, None

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 创建新的 MT5-CRS Nexus 页面")
    print("=" * 60)

    print("\n📝 我需要您提供父页面ID来创建新页面")
    print("\n请按以下步骤操作:")
    print("1. 打开您的 Notion 工作区")
    print("2. 选择一个页面作为新页面的父页面")
    print("3. 复制该页面的URL")
    print("4. 从URL中提取页面ID (例如: https://www.notion.so/PageName-xxxxxxxxxx)")
    print("5. 只复制 xxxxxxxxxx 部分")

    # 使用一个通用的父页面ID示例
    parent_page_id = input("\n请输入父页面ID: ").strip()

    if not parent_page_id:
        print("❌ 父页面ID不能为空")
        return

    print(f"\n🏗️ 在父页面 {parent_page_id} 下创建 MT5-CRS Nexus 页面...")

    page_id, page_url = create_page_with_root(parent_page_id)

    if page_id and page_url:
        print("\n" + "=" * 60)
        print("✅ MT5-CRS Nexus 页面创建成功！")
        print("=" * 60)

        print("\n🔗 页面链接:")
        print(f"   MT5-CRS Nexus: {page_url}")

        print("\n🗃️ 数据库直接链接:")
        print("   • 🧠 AI Command Center: https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64")
        print("   • 📋 Issues: https://www.notion.so/2cfc88582b4e816b9a15d85908bf4a21")
        print("   • 💡 Knowledge Graph: https://www.notion.so/2cfc88582b4e811d83bed3bd3957adea")
        print("   • 📚 Documentation: https://www.notion.so/2cfc88582b4e81608466cc6e3fb527e9")

        print("\n📝 后续操作:")
        print("1. 打开新创建的页面")
        print("2. 点击 + 号添加数据库块")
        print("3. 选择 'Link to database'")
        print("4. 搜索并添加四个核心数据库")
        print("5. 调整布局使其美观")

    else:
        print("\n❌ 页面创建失败，请检查:")
        print("   • 父页面ID是否正确")
        print("   • Notion 权限是否足够")
        print("   • 网络连接是否正常")

if __name__ == "__main__":
    main()