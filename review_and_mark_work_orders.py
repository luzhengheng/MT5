#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审查 Notion 工单并标记已完成的工单
"""

import os
import requests
import json
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

# 已完成的工单列表
COMPLETED_WORK_ORDERS = [
    "#011.1",
    "#011.2",
    "#011.3",
    "#011.4",
    "#011.5",
    "#011.6",
    "#011.7"
]

def query_work_orders():
    """查询所有工单"""
    print("🔍 查询 Notion 工单数据库...")

    url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}/query"

    try:
        response = requests.post(url, headers=HEADERS, json={"page_size": 100})

        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            print(f"❌ 查询失败: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return []

def get_work_order_number(page):
    """从页面中提取工单号"""
    # 尝试从标题中提取工单号
    name_prop = page.get('properties', {}).get('名称', {})
    if 'title' in name_prop:
        title_array = name_prop.get('title', [])
        if title_array and len(title_array) > 0:
            title_text = title_array[0].get('text', {}).get('content', '')
            # 提取 #011.X 格式的工单号
            import re
            match = re.search(r'#011\.\d+', title_text)
            if match:
                return match.group()
    return None

def get_current_status(page):
    """获取当前状态"""
    status_prop = page.get('properties', {}).get('状态', {})
    if 'status' in status_prop:
        status_obj = status_prop.get('status', {})
        if status_obj:
            return status_obj.get('name', 'unknown')
    return 'unknown'

def get_title(page):
    """获取工单标题"""
    name_prop = page.get('properties', {}).get('名称', {})
    if 'title' in name_prop:
        title_array = name_prop.get('title', [])
        if title_array and len(title_array) > 0:
            return title_array[0].get('text', {}).get('content', 'Unknown')
    return 'Unknown'

def update_work_order_status(page_id, new_status):
    """更新工单状态"""
    url = f"{NOTION_API_URL}/pages/{page_id}"

    payload = {
        "properties": {
            "状态": {
                "status": {
                    "name": new_status
                }
            }
        }
    }

    try:
        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            return True
        else:
            print(f"   ❌ 更新失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("📋 审查 Notion 工单并标记已完成")
    print("=" * 80)

    # 查询所有工单
    work_orders = query_work_orders()

    if not work_orders:
        print("❌ 未找到工单")
        return

    print(f"\n✅ 找到 {len(work_orders)} 个工单\n")

    # 分类显示
    completed = []
    in_progress = []
    not_started = []

    for page in work_orders:
        work_order_num = get_work_order_number(page)
        title = get_title(page)
        status = get_current_status(page)
        page_id = page.get('id')

        if work_order_num:
            print(f"📌 {work_order_num} - {title}")
            print(f"   当前状态: {status}")
            print(f"   Notion ID: {page_id}")

            # 检查是否应该标记为完成
            if work_order_num in COMPLETED_WORK_ORDERS and status != "完成":
                print(f"   ➡️  标记为完成...")
                if update_work_order_status(page_id, "完成"):
                    print(f"   ✅ 已更新为完成")
                    completed.append(work_order_num)
                else:
                    print(f"   ❌ 更新失败")
            elif status == "完成":
                completed.append(work_order_num)
            elif status == "进行中":
                in_progress.append(work_order_num)
            else:
                not_started.append(work_order_num)

            print()

    # 显示汇总
    print("=" * 80)
    print("📊 工单状态汇总")
    print("=" * 80)
    print(f"\n✅ 已完成: {len(completed)} 个")
    for wo in sorted(completed):
        print(f"   {wo}")

    if in_progress:
        print(f"\n⏳ 进行中: {len(in_progress)} 个")
        for wo in sorted(in_progress):
            print(f"   {wo}")

    if not_started:
        print(f"\n⭕ 未开始: {len(not_started)} 个")
        for wo in sorted(not_started):
            print(f"   {wo}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
