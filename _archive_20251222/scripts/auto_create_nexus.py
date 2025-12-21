#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动创建 MT5-CRS Nexus 页面，尝试使用根页面或工作空间根目录
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

def find_parent_page():
    """找到合适的父页面"""
    try:
        # 先尝试搜索页面
        search_url = f"{NOTION_BASE_URL}/search"
        search_data = {
            "filter": {
                "property": "object",
                "value": "page"
            },
            "page_size": 10
        }

        response = requests.post(search_url, headers=notion_headers(), json=search_data)

        if response.status_code == 200:
            results = response.json().get("results", [])

            # 寻找根页面或最近的页面
            for page in results:
                title = page.get("properties", {}).get("title", {}).get("title", [])
                if title:
                    page_title = title[0].get("plain_text", "")
                    page_id = page["id"]

                    # 优先选择看起来像根页面的页面
                    if any(keyword in page_title.lower() for keyword in ["home", "main", "root", "workspace", "工作区"]):
                        print(f"✅ 找到合适的父页面: {page_title} ({page_id})")
                        return page_id

            # 如果没找到合适的，使用第一个页面
            if results:
                page_id = results[0]["id"]
                title = results[0].get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
                print(f"📍 使用第一个页面作为父页面: {title} ({page_id})")
                return page_id

        return None

    except Exception as e:
        print(f"❌ 查找父页面失败: {e}")
        return None

def create_nexus_page(parent_page_id: str):
    """在指定父页面下创建 MT5-CRS Nexus 页���"""
    try:
        url = f"{NOTION_BASE_URL}/pages"

        page_data = {
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
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
    print("🔄 自动创建 MT5-CRS Nexus 页面")
    print("=" * 60)

    print("\n🔍 查找合适的父页面...")
    parent_page_id = find_parent_page()

    if not parent_page_id:
        print("❌ 无法找到父页面")
        print("\n📝 备选方案：")
        print("1. 在 Notion 中手动创建新页面")
        print("2. 将页面标题设置为 'MT5-CRS Nexus 知识库'")
        print("3. 复制下面的内容到页面中")

        print("\n" + "=" * 60)
        print("📋 页面内容模板")
        print("=" * 60)
        print("🚀 MT5-CRS Nexus 知识库")
        print("\n量化交易系统自动化知识管理平台")
        print("\n由 Claude Sonnet 4.5 & Gemini Pro 协同构建")
        print("\n专注于 MT5 实盘交易系统开发与部署。")
        print("\n📊 核心数据库")
        print("\n四大核心数据库构成完整的知识管理生态系统：")
        print("\n🧠 AI Command Center - AI 协同任务管理")
        print("📋 Issues - 项目工单管理")
        print("💡 Knowledge Graph - 核心知识沉淀")
        print("📚 Documentation - 文档归档管理")
        print("\n🎯 当前焦点：工单 #011")
        print("\n📋 实盘交易系统对接 (MT5 API)")
        print("\n🔹 P1 (High Priority)")
        print("🔹 MT5 API 连接与认证")
        print("🔹 实时行情数据接收")
        print("🔹 订单执行与风险控制")
        print("🔹 集成 Kelly 资金管理")
        print("🔹 多品种交易支持")

        return

    print(f"\n🏗️ 在父页面 {parent_page_id} 下创建 MT5-CRS Nexus 页面...")

    page_id, page_url = create_nexus_page(parent_page_id)

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

        # 更新 .env 文件中的主页面 ID（可选）
        print(f"\n🔧 新页面ID: {page_id}")
        print("   您可以将此ID保存以备将来使用")

    else:
        print("\n❌ 自动创建失败")
        print("\n📝 手动创建步骤:")
        print("1. 在 Notion 中手动创建新页面")
        print("2. 将页面标题设置为 'MT5-CRS Nexus 知识库'")
        print("3. 使用上面提供的内容模板")

if __name__ == "__main__":
    main()