#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 MT5-CRS 主页面上的测试内容
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

def get_page_blocks(page_id: str):
    """获取页面下的所有块"""
    try:
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            print(f"❌ 获取页面块失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ 获取页面块时出错: {e}")
        return []

def delete_block(block_id: str):
    """删除块（归档）"""
    try:
        url = f"{NOTION_BASEION_BASE_URL}/blocks/{block_id}"

        # 归档块而不是真正删除
        block_data = {
            "archived": True
        }

        response = requests.request("PATCH", url, headers=notion_headers(), json=block_data)

        if response.status_code == 200:
            return True
        else:
            print(f"❌ 删除块失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 删除块时出错: {e}")
        return False

def add_clean_content(page_id: str):
    """添加清理后的内容"""
    try:
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"

        # 清理后的内容
        clean_children = [
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
                        {"text": {"content": "量化交易系统自动化知识管理平台 - 由 Claude Sonnet 4.5 & Gemini Pro 协同构建\n\n"}},
                    ]
                }
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
                        {"text": {"content": "🧠 "}},
                        {"text": {"content": "AI Command Center", "italic": True}},
                        {"text": {"content": " - AI 协同任务管理\n📋 "}},
                        {"text": {"content": "Issues", "italic": True}},
                        {"text": {"content": " - 项目工单管理\n💡 "}},
                        {"text": {"content": "Knowledge Graph", "italic": True}},
                        {"text": {"content": " - 核心知识沉淀\n📚 "}},
                        {"text": {"content": "Documentation", "italic": True}},
                        {"text": {"content": " - 文档归档管理"}}
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
                        {"text": {"content": "📋 "}},
                        {"text": {"content": "实盘交易系统对接 (MT5 API)", "bold": True}},
                        {"text": {"content": " - P1 (High Priority)\n\n专注于构建稳定的 MT5 实盘交易连接，实现自动化交易执行与风险控制。"}}
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
                    "rich_text": [{"text": {"content": "🔗 快速链接"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "• "}},
                        {"text": {"content": "AI Command Center", "url": "https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64"}},
                        {"text": {"content": "\n• "}},
                        {"text": {"content": "Issues 数据库", "url": "https://www.notion.so/2cfc88582b4e816b9a15d85908bf4a21"}},
                        {"text": {"content": "\n• "}},
                        {"text": {"content": "Knowledge Graph", "url": "https://www.notion.so/2cfc88582b4e811d83bed3bd3957adea"}},
                        {"text": {"content": "\n• "}},
                        {"text": {"content": "Documentation", "url": "https://www.notion.so/2cfc88582b4e81608466cc6e3fb527e9"}}
                    ]
                }
            }
        ]

        response = requests.patch(url, headers=notion_headers(), json={"children": clean_children})

        if response.status_code == 200:
            print("✅ 主页面内容已更新")
            return True
        else:
            print(f"❌ 更新主页面失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 更新主页面时出错: {e}")
        return False

def clear_page_content(page_id: str):
    """清空页面内容"""
    try:
        url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"

        # 传入空的 children 数组来清空内容
        response = requests.patch(url, headers=notion_headers(), json={"children": []})

        if response.status_code == 200:
            print("✅ 主页面内容已清空")
            return True
        else:
            print(f"❌ 清空主页面失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 清空主页面时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧹 清理 MT5-CRS 主页面")
    print("=" * 60)

    # 主页面 ID
    main_page_id = "2cfc8858-2b4e-81a1-8d44-dca3beb4e380"

    print("\n📋 步骤 1: 检查当前页面内容...")
    blocks = get_page_blocks(main_page_id)
    print(f"找到 {len(blocks)} 个内容块")

    if blocks:
        print("\n🗑️ 步骤 2: 清空旧内容...")
        for i, block in enumerate(blocks):
            block_type = block.get("type", "unknown")
            block_id = block.get("id")
            print(f"   {i+1}. {block_type} - {block_id}")

        if clear_page_content(main_page_id):
            print("\n📝 步骤 3: 添加新的清理内容...")
            if add_clean_content(main_page_id):
                print("\n" + "=" * 60)
                print("🎉 主页面清理完成！")
                print("=" * 60)
                print("\n✅ 完成内容:")
                print("   🗑️ 删除了所有测试内容")
                print("   📝 添加了清洁的页面布局")
                print("   🔗 更新了快速链接")
                print("   🎯 突出了工单 #011")

                print("\n🔗 访问链接:")
                print(f"   MT5-CRS Nexus: https://www.notion.so/MT5-CRS-Nexus-2cfc88582b4e81a18d44dca3beb4e380")
            else:
                print("❌ 添加新内容失败")
        else:
            print("❌ 清空内容失败")
    else:
        print("\n📝 页面已经是空的，直接添加新内容...")
        add_clean_content(main_page_id)

if __name__ == "__main__":
    main()