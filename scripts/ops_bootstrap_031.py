#!/usr/bin/env python3
"""
Emergency Bootstrap: Fix Task #031 Itself
==========================================

Task #031 is designed to fix empty tickets, but it's EMPTY ITSELF.
This creates a "chicken-and-egg" problem.

This script performs a self-healing bootstrap:
1. Finds Task #031 in Notion
2. Injects the implementation plan
3. Updates status to "进行中" (In Progress)

Protocol: v2.5 Emergency Bootstrap
"""

import os
import sys
from pathlib import Path
import requests

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

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

# The Implementation Plan for #031
TASK_031_PLAN = """## 🎯 目标

1. **历史回填**: 修复 #014-#029 的空心工单问题，注入 Git 历史中的技术细节。
2. **机制硬化**: 升级 `project_cli.py`，增加 `--plan` 参数，强制要求新工单必须包含文档。

## ✅ 交付内容

### 1. 数据源 (Source of Truth)
- **文件**: `scripts/data/content_backfill_map.py`
- **内容**: 包含 #014-#029 的完整技术摘要（16个工单）
- **格式**: Python字典，中文内容

### 2. 执行脚本 (Injection Script)
- **文件**: `scripts/ops_inject_content.py`
- **功能**: 批量回填历史工单内容
- **安全特性**:
  - 仅在页面 < 5 个块时注入
  - 添加系统标记 callout
  - 保留现有手动内容
  - 详细日志和统计

### 3. 工具链升级 (CLI Hardening)
- **文件**: `scripts/project_cli.py` (修改)
- **新增**: `--plan` 参数支持
- **行为**:
  - 有 plan: 自动注入到 Notion
  - 无 plan: 黄色警告提示

### 4. 可重用工具 (Reusable Utility)
- **文件**: `scripts/utils/notion_updater.py`
- **功能**:
  - Markdown → Notion blocks 转换
  - append_markdown(), update_page_with_plan()
  - 完整的 block 创建助手

## 🛡️ 协议更新

### Before (Phase 1)
- 空工单很常见
- 没有强制机制
- 文档依赖手动

### After (Phase 2 Ready)
- CLI 警告如果无 plan
- 轻松注入规格: `--plan <file>`
- 历史工单已回填
- 文档驱动开发

## 📊 执行结果

**预期**:
- 回填 #014-#029: 14-16 个工单
- CLI 升级: ✅ 完成
- 工具创建: notion_updater.py
- 测试验证: ✅ 通过

## 🚀 使用示例

**创建带计划的工单**:
```bash
python3 scripts/project_cli.py start "Live Trading API" --plan docs/spec.md
```

**执行历史回填**:
```bash
export NOTION_TOKEN="..."
export NOTION_DB_ID="..."
python3 scripts/ops_inject_content.py
```

**使用 notion_updater 工具**:
```python
from utils.notion_updater import append_markdown
append_markdown(page_id, "## 更新\\n- 变更 1\\n- 变更 2")
```

## 🔄 自举修复 (Bootstrap Fix)

**问题**: Task #031 本身是空的，违反了它要建立的协议。

**解决**: 本脚本 (ops_bootstrap_031.py) 执行自举:
1. 查找 Task #031
2. 注入本实施计划
3. 更新状态为"进行中"
4. 然后执行完整回填

**时间戳**: 2025-12-28
**协议**: v2.5 Emergency Bootstrap
"""


def find_task_031():
    """Find Task #031 in Notion."""
    url = f"{NOTION_API_URL}/databases/{NOTION_DB_ID}/query"

    # Try with #031 pattern
    for pattern in ["#031", "#31"]:
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
            if results:
                return results[0]

    return None


def inject_plan_to_031(page_id):
    """Inject implementation plan into Task #031."""
    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    # Create blocks from plan
    blocks = []

    # Prepend bootstrap callout
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "🔄 Bootstrap Fix: Task #031 was empty (ironic!). This plan was auto-injected via ops_bootstrap_031.py to fix the chicken-and-egg problem."
                }
            }],
            "icon": {"emoji": "🔧"},
            "color": "orange_background"
        }
    })

    blocks.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })

    # Convert plan content to blocks
    for line in TASK_031_PLAN.strip().split('\n'):
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
        # Code block marker (skip)
        elif line.startswith('```'):
            continue
        # List item
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

    # Inject all blocks
    try:
        response = requests.patch(
            url,
            headers=HEADERS,
            json={"children": blocks},
            timeout=60
        )

        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  Injection failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False


def update_status_to_in_progress(page_id):
    """Update Task #031 status to '进行中' (In Progress)."""
    url = f"{NOTION_API_URL}/pages/{page_id}"

    try:
        response = requests.patch(
            url,
            headers=HEADERS,
            json={
                "properties": {
                    "状态": {
                        "status": {"name": "进行中"}
                    }
                }
            },
            timeout=30
        )

        return response.status_code == 200

    except Exception as e:
        print(f"⚠️  Error updating status: {e}")
        return False


def bootstrap():
    """Execute bootstrap fix for Task #031."""
    print("=" * 80)
    print("🔧 BOOTSTRAP FIX - Task #031 Self-Healing")
    print("=" * 80)
    print()
    print("Problem: Task #031 (Content Injection) is EMPTY - ironic!")
    print("Solution: Execute self-healing bootstrap")
    print()
    print("-" * 80)
    print()

    # Step 1: Find Task #031
    print("[1/3] Finding Task #031...", end=" ")
    page = find_task_031()

    if not page:
        print("❌ NOT FOUND")
        print()
        print("⚠️  Task #031 doesn't exist in Notion.")
        print("   Run: python3 scripts/project_cli.py start \"Task #031: Content Injection\"")
        return 1

    page_id = page["id"]
    print("✅ FOUND")
    print(f"   Page ID: {page_id[:8]}...")
    print()

    # Step 2: Inject plan
    print("[2/3] Injecting implementation plan...", end=" ")
    if inject_plan_to_031(page_id):
        print("✅ SUCCESS")
        print(f"   Injected {len(TASK_031_PLAN.split(chr(10)))} lines of content")
    else:
        print("❌ FAILED")
        return 1
    print()

    # Step 3: Update status
    print("[3/3] Updating status to '进行中'...", end=" ")
    if update_status_to_in_progress(page_id):
        print("✅ SUCCESS")
    else:
        print("⚠️  FAILED (continuing anyway)")
    print()

    # Summary
    print("=" * 80)
    print("✅ BOOTSTRAP SUCCESSFUL")
    print("=" * 80)
    print()
    print("Task #031 has been self-healed!")
    print()
    print("Next steps:")
    print("  1. Verify in Notion: Task #031 should now have content")
    print("  2. Run backfill: python3 scripts/ops_inject_content.py")
    print("  3. Finish task: python3 scripts/project_cli.py finish")
    print()

    return 0


if __name__ == "__main__":
    try:
        exit_code = bootstrap()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Bootstrap interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
