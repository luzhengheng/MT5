#!/usr/bin/env python3
"""
Task #030.5: Content Injection - Backfill Empty Notion Tickets
==============================================================

Inject structured Markdown content into Tickets #014-#029 that are
currently empty shells.

Safety features:
- Only injects if page has < 5 blocks (likely empty)
- Prepends system callout indicating backfill
- Preserves existing manual content

Protocol: v2.5 (Content Injection & CLI Hardening)
"""

import os
import sys
from pathlib import Path
import requests
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import backfill data
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from data.content_backfill_map import BACKFILL_DATA, get_backfill_ticket_range

# ============================================================================
# Configuration
# ============================================================================

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DB_ID")

if not NOTION_TOKEN or not NOTION_DB_ID:
    print("❌ FATAL: Missing Notion credentials")
    print("   Export: NOTION_TOKEN and NOTION_DB_ID")
    sys.exit(1)

# Notion API configuration
NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Safety threshold: only inject if page has fewer than this many blocks
SAFETY_BLOCK_THRESHOLD = 5


# ============================================================================
# Helper Functions
# ============================================================================

def query_database(filter_query=None):
    """Query the Notion database."""
    url = f"{NOTION_API_URL}/databases/{NOTION_DB_ID}/query"

    payload = {}
    if filter_query:
        payload["filter"] = filter_query

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)

        if response.status_code != 200:
            print(f"  ⚠️  Query failed: {response.status_code}")
            return []

        data = response.json()
        return data.get("results", [])

    except Exception as e:
        print(f"  ⚠️  Error querying database: {e}")
        return []


def find_ticket_by_pattern(ticket_id: int):
    """Find a Notion page by ticket ID pattern."""
    ticket_pattern = f"#{ticket_id:03d}"

    # Try exact pattern first
    pages = query_database({
        "property": "标题",  # Chinese: "Title"
        "title": {
            "contains": ticket_pattern
        }
    })

    if pages:
        return pages[0]

    # Try without leading zeros
    alt_pattern = f"#{ticket_id}"
    pages = query_database({
        "property": "标题",
        "title": {
            "contains": alt_pattern
        }
    })

    if pages:
        return pages[0]

    return None


def get_page_blocks(page_id: str):
    """Get all blocks (content) from a Notion page."""
    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            print(f"  ⚠️  Failed to fetch blocks: {response.status_code}")
            return []

        data = response.json()
        return data.get("results", [])

    except Exception as e:
        print(f"  ⚠️  Error fetching blocks: {e}")
        return []


def markdown_to_notion_blocks(markdown_text: str):
    """
    Convert markdown text to Notion block format.

    This is a simple converter that handles:
    - Headers (##)
    - Lists (-)
    - Paragraphs
    """
    blocks = []
    lines = markdown_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Header
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
        # List item
        elif line.startswith('- **') and '**:' in line:
            # Format: - **Key**: Value
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

    return blocks


def inject_content(page_id: str, content: str):
    """
    Inject content into a Notion page.

    Prepends a callout indicating system backfill, then adds the content.
    """
    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    # Create callout block
    callout = {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "🤖 System Backfill: Content generated from Git History audit (Task #030.5)"
                }
            }],
            "icon": {
                "emoji": "📜"
            },
            "color": "blue_background"
        }
    }

    # Convert markdown to Notion blocks
    content_blocks = markdown_to_notion_blocks(content)

    # Combine: callout + divider + content
    all_blocks = [
        callout,
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    ] + content_blocks

    try:
        response = requests.patch(
            url,
            headers=HEADERS,
            json={"children": all_blocks},
            timeout=30
        )

        if response.status_code == 200:
            return True
        else:
            print(f"  ⚠️  Injection failed: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"  ⚠️  Error injecting content: {e}")
        return False


# ============================================================================
# Main Injection Logic
# ============================================================================

def inject_all_content():
    """Inject content into all tickets in the backfill range."""
    print("=" * 80)
    print("💉 CONTENT INJECTION - Backfill Empty Tickets")
    print("=" * 80)
    print()
    print(f"Target Range: #{min(BACKFILL_DATA.keys()):03d} to #{max(BACKFILL_DATA.keys()):03d}")
    print(f"Total tickets: {len(BACKFILL_DATA)}")
    print(f"Safety threshold: {SAFETY_BLOCK_THRESHOLD} blocks")
    print(f"Database ID: {NOTION_DB_ID[:8]}...")
    print()
    print("⚠️  NOTE: Only injects into pages with < 5 blocks (likely empty).")
    print("   Existing manual content will be preserved.")
    print()

    # Statistics
    total = len(BACKFILL_DATA)
    found = 0
    injected = 0
    skipped_has_content = 0
    not_found = 0
    errors = 0

    print(f"Processing {total} tickets...")
    print("-" * 80)
    print()

    for ticket_id in get_backfill_ticket_range():
        ticket_pattern = f"#{ticket_id:03d}"
        content = BACKFILL_DATA[ticket_id]

        print(f"[{ticket_id - 13}/{total}] {ticket_pattern}", end=" ")

        # Find the ticket
        page = find_ticket_by_pattern(ticket_id)

        if not page:
            print(f"❌ NOT FOUND")
            not_found += 1
            continue

        found += 1
        page_id = page["id"]

        # Safety check: count existing blocks
        existing_blocks = get_page_blocks(page_id)
        block_count = len(existing_blocks)

        if block_count >= SAFETY_BLOCK_THRESHOLD:
            print(f"⏭️  SKIP (has {block_count} blocks - likely has content)")
            skipped_has_content += 1
            continue

        # Inject content
        print(f"💉 Injecting ({block_count} blocks → +{len(content.split(chr(10)))} lines)", end=" ")

        if inject_content(page_id, content):
            print("✅")
            injected += 1
        else:
            print("❌ Injection failed")
            errors += 1

    # Summary
    print()
    print("=" * 80)
    print("📊 INJECTION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total tickets: {total}")
    print(f"  Found: {found} ({found * 100 / total:.1f}%)")
    print(f"  Not found: {not_found}")
    print()
    print(f"Content injection:")
    print(f"  ✅ Injected: {injected}")
    print(f"  ⏭️  Skipped (has content): {skipped_has_content}")
    print(f"  ❌ Errors: {errors}")
    print()

    # Success check
    if errors > 0:
        print(f"⚠️  INJECTION COMPLETED WITH ERRORS")
        print(f"   {errors} tickets failed to inject")
        return 1
    elif not_found > 5:
        print(f"⚠️  INJECTION COMPLETED WITH WARNINGS")
        print(f"   {not_found} tickets not found in Notion")
        return 1
    else:
        print(f"✅ INJECTION SUCCESSFUL")
        print(f"   {injected} tickets backfilled")
        print(f"   {skipped_has_content} tickets already had content (preserved)")
        print()
        print("💡 All empty tickets now have historical context!")
        print("   Check Notion to see the backfilled content.")
        return 0


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = inject_all_content()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Injection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
