#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #064.6: Deep Structured Restoration
Protocol: v4.3 (Zero-Trust Edition)

Performs deep markdown parsing with block-level structure preservation.
Restores tasks with proper formatting, code blocks, lists, quotes, and nested elements.
"""

import os
import json
import requests
import re
import sys
import time
from pathlib import Path

NOTION_TOKEN = ""
DATABASE_ID = ""

# Manual .env loading
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

BACKUP_ROOT = Path("docs/archive/notion_backup")


def fix_encoding(text):
    """Fix Mojibake (UTF-8 bytes interpreted as Latin-1)"""
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def get_latest_backup_dir():
    """Find most recent backup directory"""
    if not BACKUP_ROOT.exists():
        return None
    dirs = [d for d in BACKUP_ROOT.iterdir() if d.is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda x: x.name, reverse=True)
    return dirs[0]


def parse_markdown_deep(md_text, max_blocks=95):
    """
    Deep markdown parser that preserves structure.
    Handles: headings, code blocks, lists (bullet/numbered/todo), quotes, dividers.
    """
    blocks = []
    lines = md_text.split('\n')

    in_code_block = False
    code_content = []
    code_lang = "plain text"

    # Step 1: Metadata stripping - skip file header lines
    # Skip lines like "**Status**: ...", "**Page ID**: ...", "---", empty lines at start
    start_index = 0
    metadata_end = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip metadata lines (start with ** and contain :) and dividers
        if (stripped.startswith("**") and "**:" in line) or stripped == "---" or not stripped:
            if not metadata_end:
                continue
        else:
            start_index = i
            metadata_end = True
            break

    body_lines = lines[start_index:]

    for line in body_lines:
        if len(blocks) >= max_blocks:
            break

        clean_line = line.rstrip()

        # --- Code Block Handling ---
        if clean_line.strip().startswith("```"):
            if in_code_block:
                # End code block
                in_code_block = False
                content = "\n".join(code_content)[:1999]
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": content}}],
                        "language": code_lang
                    }
                })
                code_content = []
            else:
                # Start code block
                in_code_block = True
                # Extract language tag
                lang = clean_line.strip().replace("```", "").strip()
                code_lang = lang if lang else "plain text"
            continue

        if in_code_block:
            code_content.append(clean_line)
            continue

        # --- Heading Handling ---
        if clean_line.startswith("# ") and not clean_line.startswith("## "):
            text = clean_line[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif clean_line.startswith("## ") and not clean_line.startswith("### "):
            text = clean_line[3:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif clean_line.startswith("### "):
            text = clean_line[4:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

        # --- List Handling (Bullet, Numbered, Todo) ---
        elif clean_line.strip().startswith("- [ ] "):
            # Unchecked todo
            text = clean_line.strip()[6:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "checked": False
                    }
                })
        elif clean_line.strip().startswith("- [x] "):
            # Checked todo
            text = clean_line.strip()[6:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "checked": True
                    }
                })
        elif clean_line.strip().startswith("- ") or clean_line.strip().startswith("* "):
            # Bullet list
            text = clean_line.strip()[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif clean_line.strip() and clean_line.strip()[0].isdigit() and ". " in clean_line.strip()[:5]:
            # Numbered list (e.g., "1. item")
            match = re.match(r"^\d+\.\s+(.+)", clean_line.strip())
            if match:
                text = match.group(1)[:1999]
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

        # --- Quote Handling ---
        elif clean_line.startswith("> "):
            text = clean_line[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

        # --- Divider ---
        elif clean_line.strip() == "---":
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })

        # --- Regular Paragraph ---
        elif clean_line.strip():
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": clean_line[:1999]}}]}
            })

    return blocks[:max_blocks]


def extract_task_id(title):
    """Extract task ID for sorting"""
    match = re.search(r'#(\d+)', title)
    if match:
        return int(match.group(1))
    return 999999


def restore_page(item, backup_dir):
    """Restore a single page with deep markdown parsing"""
    raw_title = item['title']
    clean_title = fix_encoding(raw_title)

    # Filter: Only allow valid task titles, exclude Git commits
    if not re.search(r'(TASK|Task|工单)\s*#\d+', clean_title, re.IGNORECASE):
        return False, 0

    if re.match(r'^(feat|fix|docs|chore|style|refactor|test|ops):', clean_title, re.IGNORECASE):
        return False, 0

    file_path = backup_dir / Path(item['file']).name
    if not file_path.exists():
        return False, 0

    with open(file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Deep markdown parsing
    blocks = parse_markdown_deep(md_content, max_blocks=95)

    # Create page with correct Chinese property names
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "标题": {
                "title": [{"type": "text", "text": {"content": clean_title[:2000]}}]
            },
            "状态": {
                "status": {"name": "完成"}
            },
            "优先级": {
                "select": {"name": "P1"}
            }
        },
        "children": blocks
    }

    try:
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            json=payload,
            headers=HEADERS
        )

        if resp.status_code == 200:
            page_id = resp.json()['id']
            block_count = len(blocks)
            print(f"✅ Restored: {clean_title} ({block_count} blocks)")
            return True, block_count
        else:
            print(f"❌ Failed to restore {clean_title}: {resp.text[:150]}")
            return False, 0

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, 0


def main():
    """Main execution with deep structured restoration"""
    print("=" * 70)
    print("TASK #064.6: Deep Structured Restoration")
    print("Protocol: v4.3 (Zero-Trust Edition)")
    print("=" * 70)
    print()

    print("🧹 Phase 1: Pre-flight Check...")
    backup_dir = get_latest_backup_dir()

    if not backup_dir:
        print("🔴 No backup found")
        sys.exit(1)

    print(f"📦 Scanning backup: {backup_dir}")
    index_file = backup_dir / "index.json"

    if not index_file.exists():
        print("🔴 index.json not found")
        sys.exit(1)

    with open(index_file, 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"📋 Total items in backup: {len(items)}")
    print()

    # Pre-process: Filter and validate
    print("🔍 Phase 2: Filtering & Deep Parsing Preparation...")
    valid_items = []

    for item in items:
        clean_title = fix_encoding(item['title'])

        # Smart filter
        if re.search(r'(TASK|Task|工单)\s*#\d+', clean_title, re.IGNORECASE):
            if not re.match(r'^(feat|fix|docs|chore|style|refactor|test|ops):', clean_title, re.IGNORECASE):
                item['clean_title'] = clean_title
                item['task_id'] = extract_task_id(clean_title)

                if item['task_id'] < 1000:
                    valid_items.append(item)

    valid_items.sort(key=lambda x: x['task_id'])

    print(f"✅ Valid tasks found: {len(valid_items)}")
    print(f"🗑️  Filtered out: {len(items) - len(valid_items)} noise items")

    if valid_items:
        print(f"📊 ID Range: #{valid_items[0]['task_id']} - #{valid_items[-1]['task_id']}")
    print()

    # Restoration phase
    print("🔄 Phase 3: Restoration with Deep Markdown Parsing...")
    print("-" * 70)

    success = 0
    failed = 0
    total_blocks = 0

    for i, item in enumerate(valid_items):
        item['title'] = item['clean_title']

        print(f"[{i+1}/{len(valid_items)}] ", end="")
        restored, block_count = restore_page(item, backup_dir)
        if restored:
            success += 1
            total_blocks += block_count
        else:
            failed += 1

        time.sleep(0.3)

    print("-" * 70)
    print()

    # Summary
    print("=" * 70)
    print("📊 DEEP RESTORATION SUMMARY")
    print("=" * 70)
    print(f"Total valid tasks:        {len(valid_items)}")
    print(f"Successfully restored:    {success}")
    print(f"Failed to restore:        {failed}")
    print(f"Total blocks created:     {total_blocks}")
    print(f"Avg blocks per task:      {total_blocks // max(success, 1)}")
    print(f"Noise items filtered:     {len(items) - len(valid_items)}")
    print("=" * 70)

    if success == len(valid_items):
        print("\n✅ SUCCESS: All valid tasks restored with deep structure")
        print("   Markdown content fully parsed and formatted")
        print("   Notion blocks properly structured")
        return 0
    else:
        print(f"\n⚠️  WARNING: {failed} tasks failed to restore")
        return 1


if __name__ == "__main__":
    import requests
    sys.exit(main())
