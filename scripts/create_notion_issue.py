#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接在 Notion Issues 数据库中创建新工单
"""

import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

def create_issue_in_notion(
    issue_id: str,
    title: str,
    priority: str = "P1",
    issue_type: str = "Refactor",
    status: str = "未开始",
    description: str = ""
):
    """在 Notion Issues 数据库中创建新工单"""

    if not NOTION_TOKEN or not NOTION_ISSUES_DB_ID:
        print("❌ 缺少 NOTION_TOKEN 或 NOTION_ISSUES_DB_ID 环境变量")
        return False

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # 构建工单数据
    data = {
        "parent": {"database_id": NOTION_ISSUES_DB_ID},
        "properties": {
            "名称": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "状态": {
                "status": {
                    "name": status
                }
            },
            "日期": {
                "date": {
                    "start": datetime.now().strftime("%Y-%m-%d")
                }
            }
        }
    }

    # 如果有描述，添加到页面内容中
    if description:
        data["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": description
                            }
                        }
                    ]
                }
            }
        ]

    try:
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            print(f"✅ 工单 {issue_id} 已成功创建到 Notion")
            print(f"   标题: {title}")
            print(f"   优先级: {priority}")
            print(f"   类型: {issue_type}")
            print(f"   状态: {status}")
            return True
        else:
            print(f"❌ 创建工单失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 创建工单时出错: {e}")
        return False


if __name__ == "__main__":
    # 创建工单 #011.3
    create_issue_in_notion(
        issue_id="#011.3",
        title="🚀 工单 #011.3: 升级 Gemini Review Bridge (适配 Gemini 3 Pro & ROI 最大化)",
        priority="P1",
        issue_type="Refactor",
        status="未开始",
        description="重构 gemini_review_bridge.py，移除 Token 限制，利用 Gemini 3 Pro 超长上下文窗口，实现智能聚焦和一次调用四重产出"
    )
