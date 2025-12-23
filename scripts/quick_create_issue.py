#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Issue Creator v2.0 - Chinese Schema Standard
===================================================
严格使用简体中文属性键对接中文版 Notion API

Schema 标准:
  - 标题 (Title)
  - 状态 (Status): 未开始, 进行中, 已完成
  - 优先级 (Priority): P0, P1, P2, P3
  - 类型 (Type): 核心, 缺陷, 运维, 功能

Author: Claude Sonnet 4.5 (MT5-CRS Team)
Date: 2025-12-23
"""

import os
import sys
import requests
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
load_dotenv(PROJECT_ROOT / ".env")

# Notion API 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DB_ID")

NOTION_API_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_API_VERSION
}

# === 中文 Schema 映射标准 ===
# 英文 → 中文属性名映射
PROPERTY_MAPPING = {
    "title": "标题",
    "status": "状态",
    "priority": "优先级",
    "type": "类型",
}

# 状态值映射 (英文 → 中文)
STATUS_MAPPING = {
    "TODO": "未开始",
    "IN_PROGRESS": "进行中",
    "DONE": "已完成",
}

# 类型值映射 (英文 → 中文)
TYPE_MAPPING = {
    "Core": "核心",
    "Bug": "缺陷",
    "Ops": "运维",
    "Feature": "功能",
}

# 默认优先级选项 (直接使用)
PRIORITY_OPTIONS = ["P0", "P1", "P2", "P3"]

# === 标准工单模板 (中文) ===
TEMPLATE_BLOCKS = [
    {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": "🤖 自动化创建 - MT5-CRS DevOps Cockpit"}}],
            "icon": {"emoji": "🏗️"},
            "color": "gray_background"
        }
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🎯 目标 (Objective)"}}]}
    },
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": "描述实施目标..."}}]}
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📋 任务清单 (Tasks)"}}]}
    },
    {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": [{"type": "text", "text": {"content": "步骤 1"}}], "checked": False}
    },
    {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": [{"type": "text", "text": {"content": "步骤 2"}}], "checked": False}
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🛡️ 风险控制 (Risk Control)"}}]}
    },
    {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": [{"type": "text", "text": {"content": "幂等性检查"}}], "checked": False}
    },
    {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": [{"type": "text", "text": {"content": "回滚方案准备"}}], "checked": False}
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "✅ 完成标准 (Definition of Done)"}}]}
    },
    {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": [{"type": "text", "text": {"content": "测试通过"}}], "checked": False}
    },
    {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": [{"type": "text", "text": {"content": "文档更新"}}], "checked": False}
    }
]


class IssueCreator:
    """工单创建器 (中文 Schema 标准)"""

    def __init__(self, token: str, database_id: str):
        """
        Args:
            token: Notion Integration Token
            database_id: Issues 数据库 ID
        """
        if not token or not database_id:
            raise ValueError("缺少必要的环境变量: NOTION_TOKEN 或 NOTION_DB_ID")

        self.token = token
        self.database_id = database_id
        self.headers = HEADERS

    def check_duplicate(self, title: str) -> bool:
        """
        检查是否存在同名工单

        Args:
            title: 工单标题

        Returns:
            bool: True 表示存在重复
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"

        try:
            payload = {
                "filter": {
                    "property": "标题",  # 使用中文属性名
                    "title": {
                        "equals": title
                    }
                }
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            results = response.json().get("results", [])
            return len(results) > 0

        except requests.exceptions.RequestException as e:
            print(f"⚠️  警告: 重复检查失败 - {e}")
            return False

    def create(
        self,
        title: str,
        status: str = "TODO",
        priority: str = "P1",
        issue_type: str = "Feature",
    ) -> bool:
        """
        创建工单

        Args:
            title: 工单标题
            status: 状态 (TODO/IN_PROGRESS/DONE)
            priority: 优先级 (P0/P1/P2/P3)
            issue_type: 类型 (Core/Bug/Ops/Feature)

        Returns:
            bool: 创建成功返回 True
        """
        print("=" * 80)
        print(f"📝 创建工单: {title}")
        print("=" * 80)

        # 1. 检查重复
        if self.check_duplicate(title):
            print(f"⚠️  工单已存在: {title}")
            print("   提示: 使用不同的标题或手动删除重复工单")
            return False

        # 2. 映射为中文值
        status_cn = STATUS_MAPPING.get(status, "未开始")
        type_cn = TYPE_MAPPING.get(issue_type, "功能")

        # 3. 验证优先级
        if priority not in PRIORITY_OPTIONS:
            print(f"⚠️  警告: 优先级 '{priority}' 无效，使用默认值 'P1'")
            priority = "P1"

        # 4. 构建请求体 (严格使用中文属性名)
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "标题": {  # Title
                    "title": [{"text": {"content": title}}]
                },
                "状态": {  # Status
                    "select": {"name": status_cn}
                },
                "优先级": {  # Priority
                    "select": {"name": priority}
                },
                "类型": {  # Type
                    "select": {"name": type_cn}
                }
            },
            "children": TEMPLATE_BLOCKS
        }

        # 5. 发送请求
        url = "https://api.notion.com/v1/pages"

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            page = response.json()
            page_url = page.get("url", "")

            print()
            print("✅ 工单创建成功!")
            print(f"   标题: {title}")
            print(f"   状态: {status_cn}")
            print(f"   优先级: {priority}")
            print(f"   类型: {type_cn}")
            print(f"   链接: {page_url}")
            print()

            return True

        except requests.exceptions.RequestException as e:
            print()
            print(f"❌ 工单创建失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"   错误详情: {e.response.text}")
            print()
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="快速创建 Notion 工单 (中文 Schema 标准)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python quick_create_issue.py "修复登录 Bug"
  python quick_create_issue.py "优化数据库查询" --prio P0 --type Core
  python quick_create_issue.py "部署监控系统" --status IN_PROGRESS --type Ops

状态选项: TODO (未开始), IN_PROGRESS (进行中), DONE (已完成)
优先级选项: P0 (致命), P1 (紧急), P2 (重要), P3 (常规)
类型选项: Core (核心), Bug (缺陷), Ops (运维), Feature (功能)
        """
    )

    parser.add_argument(
        "title",
        help="工单标题 (必填)"
    )
    parser.add_argument(
        "--status",
        default="TODO",
        choices=["TODO", "IN_PROGRESS", "DONE"],
        help="状态 (默认: TODO)"
    )
    parser.add_argument(
        "--prio",
        "--priority",
        dest="priority",
        default="P1",
        choices=PRIORITY_OPTIONS,
        help="优先级 (默认: P1)"
    )
    parser.add_argument(
        "--type",
        default="Feature",
        choices=["Core", "Bug", "Ops", "Feature"],
        help="类型 (默认: Feature)"
    )

    args = parser.parse_args()

    # 创建工单
    try:
        creator = IssueCreator(
            token=NOTION_TOKEN,
            database_id=DATABASE_ID
        )

        success = creator.create(
            title=args.title,
            status=args.status,
            priority=args.priority,
            issue_type=args.type
        )

        sys.exit(0 if success else 1)

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print()
        print("💡 请检查 .env 文件是否包含以下变量:")
        print("   - NOTION_TOKEN")
        print("   - NOTION_DB_ID")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
