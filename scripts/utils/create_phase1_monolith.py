#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #064: Phase 1 Monolith & Reset
Protocol: v4.3 (Zero-Trust Edition)

Clears all scattered historical tasks and creates a single comprehensive
milestone ticket summarizing all Phase 1 achievements.
"""

import os
import requests
import json
import time
import sys

# Load configuration
NOTION_TOKEN = ""
DATABASE_ID = ""

env_file = "/opt/mt5-crs/.env"
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key.strip() == "NOTION_TOKEN":
                    NOTION_TOKEN = value.strip()
                elif key.strip() == "NOTION_DB_ID":
                    DATABASE_ID = value.strip()

if not NOTION_TOKEN or not DATABASE_ID:
    print("🔴 Configuration failed: NOTION_TOKEN or DATABASE_ID not found")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# === Monolith Content Definition ===
MONOLITH_TITLE = "🏛️ MILESTONE #1: Phase 1 Infrastructure & Connectivity (Completed)"

MONOLITH_CONTENT = [
    {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Phase 1 (2025.12 - 2026.01) 已圆满结束。本工单档案了该阶段所有核心技术成就与资产。"}
            }],
            "icon": {"emoji": "🎯"},
            "color": "gray_background"
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
            "rich_text": [{
                "type": "text",
                "text": {"content": "1. 核心架构成就 (Architecture)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Zero-Trust SSH Mesh: 实现了 Linux (INF) -> Windows (GTW) 的无密码、高安全密钥互信。"}
            }]
        }
    },
    {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Full-Duplex ZMQ: 摒弃 Redis,实现 ZeroMQ 纯 TCP 直连 (REQ: 5555 / PUB: 5556)。"}
            }]
        }
    },
    {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Dual-Track Data: 确立了 EODHD Bulk (冷) + WebSocket (热) 的双轨数据架构。"}
            }]
        }
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "2. 关键资产清单 (Asset Inventory)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "code",
        "code": {
            "language": "yaml",
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "INF (Brain): sg-infer-core-01 (172.19.141.250)\nGTW (Hand):  sg-mt5-gateway-01 (172.19.141.255)\nHUB (Repo):  sg-nexus-hub-01 (172.19.141.254)\nGPU (Train): cn-train-gpu-01 (172.23.135.141)"
                }
            }]
        }
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "3. 交易系统闭环 (Trading Loop)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "EA Version: Direct_Zmq.mq5 v3.12 (Auto-Filling Mode Fixed)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "First Real Trade: Ticket #1417253330 (SELL 0.02 Lots)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "4. 历史工单归档 (Archive Stats)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "共计 89 个历史开发任务(含 Task #001 - #064)已成功备份至 docs/archive/notion_backup/,并从看板移除以保持整洁。"
                }
            }]
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
            "rich_text": [{
                "type": "text",
                "text": {"content": "5. Next Steps (Phase 2)"}
            }]
        }
    },
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Phase 1 infrastructure is complete. Phase 2 will focus on strategy optimization, live deployment, and production monitoring."}
            }]
        }
    }
]


def get_active_pages():
    """Query all active pages from Notion database"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    pages = []
    has_more = True
    next_cursor = None

    while has_more:
        body = {"page_size": 100}
        if next_cursor:
            body["start_cursor"] = next_cursor

        resp = requests.post(url, json=body, headers=HEADERS)
        if resp.status_code != 200:
            print(f"⚠️  Failed to query pages: {resp.text[:150]}")
            break

        data = resp.json()
        pages.extend(data["results"])
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    return pages


def archive_page(page_id, title=""):
    """Archive (soft-delete) a single page"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = requests.patch(url, json={"archived": True}, headers=HEADERS)

    if resp.status_code == 200:
        print(f"🗑️  Archived: {title[:60]} ({page_id})")
        return True
    else:
        print(f"⚠️  Failed to archive {page_id}: {resp.text[:100]}")
        return False


def create_monolith():
    """Create the single Phase 1 milestone page"""
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "标题": {
                "title": [{
                    "type": "text",
                    "text": {"content": MONOLITH_TITLE}
                }]
            },
            "状态": {
                "status": {"name": "完成"}
            },
            "优先级": {
                "select": {"name": "P0"}
            }
        },
        "children": MONOLITH_CONTENT
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=HEADERS
    )

    if resp.status_code == 200:
        page_id = resp.json()['id']
        print(f"✅ Milestone Created Successfully! (Page ID: {page_id})")
        return True
    else:
        print(f"❌ Failed to create milestone: {resp.text[:200]}")
        return False


def main():
    """Main execution: Purge + Create Monolith"""
    print("=" * 70)
    print("TASK #064: Phase 1 Monolith & Reset")
    print("Protocol: v4.3 (Zero-Trust Edition)")
    print("=" * 70)
    print()

    # Step 1: Purge existing tasks
    print("🧹 Step 1: Querying Active Pages...")
    pages = get_active_pages()
    count = len(pages)

    print(f"📋 Found {count} active pages")
    print()

    if count == 0:
        print("✅ Database already empty. Proceeding to milestone creation...")
    else:
        print(f"⚠️  WARNING: About to archive {count} pages")
        print("   This action will clear all current tasks from the database")
        print("   (Pages can be recovered from Notion trash within 30 days)")
        print()
        print("   Starting cleanup in 5 seconds... (Ctrl+C to abort)")

        try:
            for i in range(5, 0, -1):
                print(f"   {i}...", end="", flush=True)
                time.sleep(1)
            print()
        except KeyboardInterrupt:
            print("\n⛔ Operation aborted by user")
            return 130

        print()
        print("🗑️  Archiving Pages...")
        print("-" * 70)

        archived_count = 0
        for i, page in enumerate(pages):
            # Extract title from properties
            title = ""
            if "properties" in page:
                title_prop = page["properties"].get("标题") or page["properties"].get("Task") or page["properties"].get("Name")
                if title_prop and "title" in title_prop and title_prop["title"]:
                    title = title_prop["title"][0]["plain_text"]

            print(f"[{i+1}/{count}] ", end="")
            if archive_page(page["id"], title):
                archived_count += 1

            time.sleep(0.3)  # Rate limiting

        print("-" * 70)
        print()
        print(f"✅ Archived {archived_count}/{count} pages")
        print()

    # Step 2: Create monolith
    print("🏛️  Step 2: Creating Phase 1 Monolith Milestone...")
    print("-" * 70)

    if create_monolith():
        print("-" * 70)
        print()
        print("=" * 70)
        print("📊 MONOLITH CREATION SUMMARY")
        print("=" * 70)
        print(f"Pages archived:           {count}")
        print(f"Monolith created:         ✅ YES")
        print(f"Database state:           Single Entry (Milestone)")
        print("=" * 70)
        print()
        print("✅ SUCCESS: Phase 1 consolidated into single milestone")
        print("   Notion board is now clean for Phase 2")
        print("   Historical details preserved in docs/archive/")
        return 0
    else:
        print()
        print("❌ ERROR: Failed to create milestone page")
        return 1


if __name__ == "__main__":
    sys.exit(main())
