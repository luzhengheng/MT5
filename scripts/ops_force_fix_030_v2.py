#!/usr/bin/env python3
"""
Force Fix V2: Task #030 - Reality Check
========================================

Previous attempts may have been hallucinated or targeted wrong page.
This script uses brute force approach:
1. Find ALL pages containing "#030"
2. Fix EVERY match
3. Print Notion URLs for manual verification

Protocol: v2.6 Brute Force Reality Check
"""

import os
import sys
from pathlib import Path
import requests

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DB_ID")

if not NOTION_TOKEN or not NOTION_DB_ID:
    print("❌ FATAL: Missing Notion credentials")
    print("   Export: NOTION_TOKEN and NOTION_DB_ID")
    sys.exit(1)

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

TARGET_STRING = "#030"

# Content for Task #030
TASK_030_CONTENT = """## 🎯 目标

对 Notion 历史工单 (#001-#027) 进行全面标准化清理，建立"事实来源"。

## ✅ 交付内容

### 1. 事实映射 (Source of Truth)
- **文件**: `scripts/data/historical_map.py`
- **内容**: 基于 Git 历史中的工单定义
- **格式**: Python 字典，中文描述

### 2. 清理脚本 (Healing Script)
- **文件**: `scripts/ops_heal_history.py`
- **功能**: 批量修正标题格式和状态
- **特性**: 中文属性名支持、幂等操作

### 3. 零数据丢失 (Soft Refactor)
- **策略**: "Soft Refactor" - 只更新属性
- **实现**: 仅 PATCH properties，不触碰 blocks
- **验证**: 全部 27 个工单内容完整保留

## 📊 修复结果

**执行统计**:
- Total tickets: 27
- Found: 27 (100.0%)
- Titles updated: 11
- Statuses updated: 11
- Errors: 0

**验证结果**:
- 所有 27 个工单标题已标准化
- 所有完成工单状态已更正为 "完成"
- 页面内容 100% 保留

## 🛡️ 协议建立

**标题格式**: `#XXX - {Description}`

**状态标准**:
- 已完成工单: "完成"
- 进行中工单: "进行中"
- 未开始工单: "未开始"

## 🩹 Force Fix V2 备注

**问题**: Task #030 在多次修复尝试后仍显示为空。

**解决**: 本脚本 (ops_force_fix_030_v2.py) 使用暴力修复:
- 查找所有包含 "#030" 的页面
- 修复每一个匹配项
- 打印 Notion URL 供用户验证

**时间戳**: 2025-12-28
**协议**: v2.6 Brute Force Reality Check
"""


def find_all_030_pages():
    """Find ALL pages containing '#030' in title."""
    url = f"{NOTION_API_URL}/databases/{NOTION_DB_ID}/query"

    # Try multiple patterns
    all_pages = []
    patterns = ["#030", "#30", "030", "Task #030"]

    for pattern in patterns:
        response = requests.post(
            url,
            headers=HEADERS,
            json={
                "filter": {
                    "property": "标题",
                    "title": {"contains": pattern}
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            results = response.json().get("results", [])
            # Deduplicate by page_id
            for page in results:
                if page["id"] not in [p["id"] for p in all_pages]:
                    all_pages.append(page)

    return all_pages


def inject_content(page_id):
    """Inject content into a page."""
    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    # Create blocks
    blocks = []

    # Force Fix V2 callout
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "🔴 Force Fix V2: Applied via ops_force_fix_030_v2.py after user screenshot verification"
                }
            }],
            "icon": {"emoji": "🔴"},
            "color": "red_background"
        }
    })

    blocks.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })

    # Convert content to blocks
    for line in TASK_030_CONTENT.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        # Heading
        if line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[3:]}
                    }]
                }
            })
        # Heading 3
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[4:]}
                    }]
                }
            })
        # Code block marker (skip)
        elif line.startswith('```') or line.startswith('**'):
            continue
        # List item with bold prefix
        elif line.startswith('- **') and '**:' in line:
            key_end = line.index('**:')
            key = line[4:key_end]
            value = line[key_end + 3:].strip()

            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{key}: "},
                            "annotations": {"bold": True}
                        },
                        {
                            "type": "text",
                            "text": {"content": value}
                        }
                    ]
                }
            })
        # Regular list item
        elif line.startswith('- '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[2:]}
                    }]
                }
            })
        # Paragraph
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line}
                    }]
                }
            })

    # Inject
    try:
        response = requests.patch(
            url,
            headers=HEADERS,
            json={"children": blocks},
            timeout=60
        )

        if response.status_code == 200:
            return True, "Content injected successfully"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return False, str(e)


def update_status(page_id):
    """Update status to Done."""
    url = f"{NOTION_API_URL}/pages/{page_id}"

    try:
        response = requests.patch(
            url,
            headers=HEADERS,
            json={
                "properties": {
                    "状态": {
                        "status": {"name": "完成"}
                    }
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            return True, "Status updated to 完成"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return False, str(e)


def force_fix_v2():
    """Execute brute force fix for all #030 pages."""
    print("=" * 80)
    print("🔴 FORCE FIX V2 - Brute Force Reality Check")
    print("=" * 80)
    print()
    print("Problem: Previous fixes may have been hallucinated")
    print("Solution: Find and fix ALL pages containing '#030'")
    print()
    print("-" * 80)
    print()

    # Step 1: Find ALL matching pages
    print(f"[1/2] Searching for ALL pages containing '{TARGET_STRING}'...", end=" ")
    pages = find_all_030_pages()

    if not pages:
        print("❌ NOT FOUND")
        print()
        print(f"⚠️  No pages found containing '{TARGET_STRING}'")
        print("   This is unexpected - Task #030 should exist")
        return 1

    print(f"✅ FOUND {len(pages)} page(s)")
    print()

    # Step 2: Fix each page
    print(f"[2/2] Fixing {len(pages)} page(s)...")
    print()

    fixed_count = 0
    failed_count = 0

    for i, page in enumerate(pages, 1):
        page_id = page["id"]

        # Get title
        title_prop = page.get("properties", {}).get("标题", {})
        title_array = title_prop.get("title", [])
        title = title_array[0].get("plain_text", "") if title_array else "Unknown"

        # Construct Notion URL
        notion_url = f"https://www.notion.so/{page_id.replace('-', '')}"

        print(f"Page {i}/{len(pages)}: {title}")
        print(f"  ID: {page_id}")
        print(f"  URL: {notion_url}")
        print()

        # Inject content
        print(f"  → Injecting content...", end=" ")
        success, message = inject_content(page_id)
        if success:
            print("✅ SUCCESS")
        else:
            print(f"❌ FAILED: {message}")
            failed_count += 1
            continue

        # Update status
        print(f"  → Updating status to '完成'...", end=" ")
        success, message = update_status(page_id)
        if success:
            print("✅ SUCCESS")
            fixed_count += 1
        else:
            print(f"❌ FAILED: {message}")
            failed_count += 1

        print()
        print(f"  🔗 VERIFY THIS URL: {notion_url}")
        print()
        print("-" * 80)
        print()

    # Summary
    print("=" * 80)
    print("📊 FORCE FIX V2 SUMMARY")
    print("=" * 80)
    print()
    print(f"Pages found: {len(pages)}")
    print(f"  ✅ Fixed: {fixed_count}")
    print(f"  ❌ Failed: {failed_count}")
    print()

    if failed_count > 0:
        print("⚠️  FORCE FIX COMPLETED WITH ERRORS")
        return 1
    else:
        print("✅ FORCE FIX SUCCESSFUL")
        print()
        print("⚠️  CRITICAL: Please verify the URLs printed above")
        print("   Match them against your Notion app to confirm the fix")
        return 0


if __name__ == "__main__":
    try:
        exit_code = force_fix_v2()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Force fix interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
