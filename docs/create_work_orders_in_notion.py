#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建工单 #011.7, #011.8, #011.9 到 Notion 数据库
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

if not NOTION_TOKEN or not NOTION_ISSUES_DB_ID:
    print("❌ 缺少 Notion 配置：NOTION_TOKEN 或 NOTION_ISSUES_DB_ID")
    exit(1)

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 定义三个工单
WORK_ORDERS = [
    {
        "title": "🚀 工单 #011.7 修复脚本中的硬编码路径",
        "status": "进行中",
    },
    {
        "title": "🚀 工单 #011.8 解耦 Notion 同步与交易主循环",
        "status": "未开始",
    },
    {
        "title": "🚀 工单 #011.9 提交核心 MT5 代码供深度审查",
        "status": "未开始",
    }
]

def create_work_order(work_order):
    """创建单个工单"""
    print(f"\n📝 创建工单: {work_order['title']}")

    url = f"{NOTION_API_URL}/pages"

    payload = {
        "parent": {
            "database_id": NOTION_ISSUES_DB_ID
        },
        "properties": {
            "名称": {
                "title": [
                    {
                        "text": {
                            "content": work_order["title"]
                        }
                    }
                ]
            },
            "状态": {
                "status": {
                    "name": work_order["status"]
                }
            }
        }
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            data = response.json()
            page_id = data.get('id')
            print(f"   ✅ 成功创建: {page_id}")
            return page_id
        else:
            print(f"   ❌ 创建失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return None

def main():
    print("=" * 80)
    print("🚀 创建工单 #011.7, #011.8, #011.9 到 Notion")
    print("=" * 80)

    created_count = 0

    for work_order in WORK_ORDERS:
        page_id = create_work_order(work_order)
        if page_id:
            created_count += 1

    print("\n" + "=" * 80)
    print(f"✅ 完成: {created_count}/{len(WORK_ORDERS)} 个工单已创建")
    print("=" * 80)

if __name__ == "__main__":
    main()
