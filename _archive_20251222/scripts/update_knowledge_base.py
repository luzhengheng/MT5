#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 Notion 知识库 - 当前开发状态
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
KNOWLEDGE_DB_ID = os.getenv("NOTION_KNOWLEDGE_DB_ID")

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def find_page_by_title(title_keyword):
    """查找指定标题的页面"""
    response = requests.post(
        f"https://api.notion.com/v1/databases/{KNOWLEDGE_DB_ID}/query",
        headers=notion_headers(),
        json={"page_size": 100}
    )

    if response.status_code == 200:
        pages = response.json().get("results", [])
        for page in pages:
            props = page.get("properties", {})
            title_data = props.get("名称", props.get("Name", {}))
            if "title" in title_data and title_data["title"]:
                title = title_data["title"][0].get("plain_text", "")
                if title_keyword in title:
                    return page["id"]
    return None

def update_current_status_page(page_id):
    """更新当前开发状态页面"""

    # 先删除现有内容
    blocks_response = requests.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=notion_headers()
    )

    if blocks_response.status_code == 200:
        existing_blocks = blocks_response.json().get("results", [])
        for block in existing_blocks:
            requests.delete(
                f"https://api.notion.com/v1/blocks/{block['id']}",
                headers=notion_headers()
            )

    # 创建新内容
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": f"📅 最后更新时间: {current_date}"}}],
                "icon": {"emoji": "🔄"},
                "color": "blue_background"
            }
        },
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "🎯 MT5-CRS 项目当前状态"}}]
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
                "rich_text": [{"text": {"content": "📊 总体进度"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "总工单数: ", "link": None}, "annotations": {"bold": True}},
                    {"text": {"content": "16 个"}},
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "已完成: ", "link": None}, "annotations": {"bold": True}},
                    {"text": {"content": "14 个 (87.5%)"}},
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "进行中: ", "link": None}, "annotations": {"bold": True}},
                    {"text": {"content": "2 个 (#011 MT5实盘系统, #P2)"}},
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
                "rich_text": [{"text": {"content": "🚀 当前焦点工单"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": "#011 - MT5 实盘交易系统对接"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "状态: 🔄 进行中"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "优先级: P0 (最高)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "目标: MT5 API 对接，实盘交易系统集成"}}]
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
                "rich_text": [{"text": {"content": "✅ 已完成的核心功能"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ #008 - MT5-CRS 数据管线与特征工程平台 (14,500+ 行代码, 75+ 特征)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ #009 - 机器学习模型训练 (LightGBM, XGBoost, RF)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ #010 - 回测系统 (Kelly 仓位, 风险控制)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ #010.9 - Notion Nexus 知识库与自动化架构"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ #011.1 - AI 跨会话持久化规则 (Git-Notion 自动同步)"}}]
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
                "rich_text": [{"text": {"content": "🔧 三方协同系统"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "已实现 GitHub + Notion 双数据库自动同步："}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ GitHub 远程仓库 - 代码版本控制"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Notion 知识库 - 技术知识沉淀"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Notion Issues - 工单进度跟踪 (16个工单已同步)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Git Hook - 自动触发同步"}}]
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
                "rich_text": [{"text": {"content": "📈 项目统计"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "总代码量: 14,500+ 行"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "特征维度: 75+ 个"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "完成迭代: 6/6 (数据管线)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "测试覆盖: 95+ 测试方法"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "监控系统: Prometheus + Grafana"}}]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": "🎯 下一步: 完成 MT5 实盘系统对接，进入实盘交易阶段"}}],
                "icon": {"emoji": "🚀"},
                "color": "green_background"
            }
        }
    ]

    response = requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=notion_headers(),
        json={"children": blocks}
    )

    return response

def main():
    print("=" * 80)
    print("🔄 更新 Notion 知识库 - 当前开发状态")
    print("=" * 80)
    print()

    # 查找"当前开发状态"页面
    print("🔍 查找页面...")
    page_id = find_page_by_title("当前开发状态")

    if not page_id:
        print("❌ 未找到页面")
        sys.exit(1)

    print(f"✅ 找到页面 ID: {page_id}")
    print()

    # 更新页面内容
    print("🔧 更新页面内容...")
    response = update_current_status_page(page_id)

    if response.status_code == 200:
        print("✅ 更新成功！")
        print()
        print("=" * 80)
        print("🎉 知识库已更新最新项目状态！")
        print(f"🔗 查看: https://www.notion.so/{KNOWLEDGE_DB_ID.replace('-', '')}")
        print("=" * 80)
    else:
        print(f"❌ 更新失败: {response.status_code}")
        print(f"错误: {response.text}")

if __name__ == "__main__":
    main()
