#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 AI Command Center 页面，删除测试内容，让 MT5 置顶
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

def get_all_pages_in_db(db_id: str):
    """获取数据库中的所有页面"""
    try:
        url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
        response = requests.post(url, headers=notion_headers(), json={"page_size": 100})

        if response.status_code == 200:
            query_result = response.json()
            pages = query_result.get("results", [])
            return pages
        else:
            print(f"❌ 获取页面失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ 获取页面时出错: {e}")
        return []

def delete_page(page_id: str, title: str):
    """删除页面（归档）"""
    try:
        url = f"{NOTION_BASE_URL}/pages/{page_id}"

        # 归档页面而不是真正删除
        page_data = {
            "archived": True
        }

        response = requests.request("PATCH", url, headers=notion_headers(), json=page_data)

        if response.status_code == 200:
            print(f"✅ 已删除测试页面: {title}")
            return True
        else:
            print(f"❌ 删除页面失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 删除页面时出错: {e}")
        return False

def create_mt5_task(db_id: str):
    """创建 MT5 相关的置顶任务"""
    try:
        url = f"{NOTION_BASE_URL}/pages"

        page_data = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": "🚀 MT5 实盘交易系统开发 - 优先级任务"}}]
                },
                "Context Files": {
                    "multi_select": [
                        {"name": "src/strategy/risk_manager.py"},
                        {"name": "src/models/trainer.py"},
                        {"name": "bin/run_backtest.py"}
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📋 核心任务清单"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": "🔹 MT5 API 连接与认证\n🔹 实时行情数据接收\n🔹 订单执行与风险控制\n🔹 仓位管理与资金管理\n🔹 性能监控与日志记录"}}
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
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": "🔧 技术要求"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": "支持多品种交易 (外汇、指数、商品)"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": "实时风险监控与自动止损"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": "与现有 Kelly 资金管理模块集成"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": "支持策略热切换"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": "📊 当前优先级: P0 (最高优先级)"}}
                        ]
                    }
                }
            ]
        }

        response = requests.post(url, headers=notion_headers(), json=page_data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 已创建 MT5 置顶任务: {result['id']}")
            return result["id"]
        else:
            print(f"❌ 创建 MT5 任务失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ 创建 MT5 任务时出错: {e}")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("🧹 清理 AI Command Center 页面")
    print("=" * 60)

    # AI Command Center 数据库 ID
    ai_db_id = "2cfc8858-2b4e-817e-a4a5-fe17be413d64"

    print("\n📋 步骤 1: 获取所有页面...")
    pages = get_all_pages_in_db(ai_db_id)
    print(f"找到 {len(pages)} 个页面")

    print("\n🗑️ 步骤 2: 删除测试内容...")
    deleted_count = 0

    for page in pages:
        title = "Untitled"
        title_prop = page.get("properties", {}).get("Name", {}).get("title", [])
        if title_prop:
            title = title_prop[0].get("plain_text", "Untitled")

        page_id = page["id"]

        # 删除测试相关的页面
        if any(keyword in title.lower() for keyword in [
            "测试", "test", "自检", "系统自检", "kelly", "解释", "sample", "demo"
        ]):
            print(f"🗑️ 删除: {title}")
            if delete_page(page_id, title):
                deleted_count += 1

    print(f"\n✅ 已删除 {deleted_count} 个测试页面")

    print("\n🚀 步骤 3: 创建 MT5 置顶任务...")
    mt5_task_id = create_mt5_task(ai_db_id)

    if mt5_task_id:
        print("\n" + "=" * 60)
        print("🎉 AI Command Center 页面清理完成！")
        print("=" * 60)
        print("\n✅ 完成内容:")
        print(f"   🗑️ 删除了 {deleted_count} 个测试页面")
        print(f"   🚀 创建了 MT5 置顶任务")
        print(f"   📋 任务焦点转向实盘交易系统")

        print("\n🔗 直接访问链接:")
        print(f"   AI Command Center: https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64")

        print("\n🎯 下一步:")
        print("   1. 在 Notion 中查看清理后的页面")
        print("   2. MT5 任务现在位于顶部")
        print("   3. 开始工单 #011 的具体开发")
    else:
        print("\n❌ MT5 任务创建失败，请检查权限")

if __name__ == "__main__":
    main()