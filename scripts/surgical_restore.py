#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #064.7: Surgical Restoration
Protocol: v4.3 (Zero-Trust Edition)

Performs surgical precision restoration:
- Amputates metadata headers (Status, Page ID, Properties)
- Strict ID filtering (only Task #001-#064)
- Anchor slicing (extracts content after ## Content or last ---)
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


def get_latest_backup_dir():
    """Find most recent backup directory"""
    if not BACKUP_ROOT.exists():
        return None
    dirs = [d for d in BACKUP_ROOT.iterdir() if d.is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda x: x.name, reverse=True)
    return dirs[0]


def extract_real_content(md_text):
    """
    SURGICAL CORE: Extract only real content, discard Notion export metadata headers.

    Strategy 1: Find "## Content" marker (common Notion export format)
    Strategy 2: Find last "---" divider (metadata ends with divider)
    Strategy 3: If contains **Status**: or **Page ID**: reject all (pure metadata)
    """
    lines = md_text.split('\n')

    # Strategy 1: Locate "## Content" marker
    content_marker_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "## Content":
            content_marker_idx = i
            break

    if content_marker_idx != -1:
        # Return everything after "## Content"
        return "\n".join(lines[content_marker_idx + 1:]).strip()

    # Strategy 2: Find last "---" divider
    # Notion exports typically: metadata --- properties --- actual content
    last_divider_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            last_divider_idx = i

    if last_divider_idx != -1 and last_divider_idx < len(lines) - 1:
        return "\n".join(lines[last_divider_idx + 1:]).strip()

    # Strategy 3: If contains metadata markers, return empty (reject polluted content)
    if "**Status**:" in md_text or "**Page ID**:" in md_text or "**URL**:" in md_text:
        return ""  # Safer to return empty than polluted

    # Fallback: appears to be clean text, return as-is
    return md_text


def parse_markdown_blocks(clean_text):
    """Convert surgically cleaned text to Notion blocks"""
    if not clean_text:
        return []

    blocks = []
    lines = clean_text.split('\n')

    in_code = False
    code_buf = []
    code_lang = "plain text"

    for line in lines:
        if len(blocks) >= 95:
            break

        stripped = line.strip()

        # Code block handling
        if stripped.startswith("```"):
            if in_code:
                # Close code block
                in_code = False
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": "\n".join(code_buf)[:1999]}}],
                        "language": code_lang
                    }
                })
                code_buf = []
            else:
                # Open code block
                in_code = True
                code_lang = stripped.replace("```", "").strip() or "plain text"
            continue

        if in_code:
            code_buf.append(line)
            continue

        # Heading parsing
        if line.startswith("# ") and not line.startswith("## "):
            text = line[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif line.startswith("## ") and not line.startswith("### "):
            text = line[3:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif line.startswith("### "):
            text = line[4:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

        # List parsing
        elif stripped.startswith("- [ ] "):
            text = stripped[6:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "checked": False
                    }
                })
        elif stripped.startswith("- [x] "):
            text = stripped[6:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": text}}],
                        "checked": True
                    }
                })
        elif stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

        # Quote parsing
        elif line.startswith("> "):
            text = line[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })

        # Divider
        elif stripped == "---":
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })

        # Paragraph
        elif stripped:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": stripped[:1999]}}]}
            })

    return blocks[:95]


def fix_encoding(text):
    """Fix Mojibake (UTF-8 bytes interpreted as Latin-1)"""
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def restore_clean_page(item, backup_dir):
    """Restore a single page with surgical precision"""
    # Title processing
    title = item['title']
    title = fix_encoding(title)

    # Extract task ID
    match = re.search(r'#(\d+)', title)
    if not match:
        return False, 0, "no_id"

    task_id = int(match.group(1))

    # 🚫 CORE FILTER: Only restore tasks with ID <= 64
    if task_id > 64:
        return False, task_id, "id_too_high"

    # 🚫 Exclude Git commits
    if re.match(r'^(feat|fix|docs|chore|style|refactor|test|ops):', title, re.IGNORECASE):
        return False, task_id, "git_commit"

    # Check if task contains "Task" or "工单" keywords
    if not re.search(r'(TASK|Task|工单)', title, re.IGNORECASE):
        return False, task_id, "no_task_keyword"

    file_path = backup_dir / Path(item['file']).name
    if not file_path.exists():
        return False, task_id, "file_not_found"

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_md = f.read()

    # ✂️ SURGICAL EXTRACTION: Remove metadata headers
    clean_content = extract_real_content(raw_md)
    blocks = parse_markdown_blocks(clean_content)

    # If no content extracted, create placeholder
    if not blocks:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "(This historical task has no content body)"}}]}
        })

    # Create page with correct Chinese property names
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "标题": {
                "title": [{"type": "text", "text": {"content": title[:2000]}}]
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
            print(f"✅ Restored: {title} (ID: {task_id}, Blocks: {block_count}) - Content extracted.")
            return True, task_id, "success"
        else:
            print(f"❌ Failed: {title} - {resp.text[:100]}")
            return False, task_id, "api_error"

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, task_id, "exception"


def main():
    """Main surgical restoration execution"""
    print("=" * 70)
    print("TASK #064.7: Surgical Restoration")
    print("Protocol: v4.3 (Zero-Trust Edition)")
    print("=" * 70)
    print()

    print("⚠️  WARNING: This script assumes database has been cleaned.")
    print("   If not, please run scripts/migrate_and_clean_notion.py first.")
    print()

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

    # Pre-process: Extract task IDs and sort
    print("🔍 Phase 1: Filtering & ID Extraction...")
    valid_items = []

    for item in items:
        title = fix_encoding(item['title'])
        match = re.search(r'#(\d+)', title)
        if match:
            item['clean_title'] = title
            item['task_id'] = int(match.group(1))
            valid_items.append(item)

    valid_items.sort(key=lambda x: x['task_id'])

    print(f"✅ Items with extractable IDs: {len(valid_items)}")
    if valid_items:
        print(f"📊 ID Range: #{valid_items[0]['task_id']} - #{valid_items[-1]['task_id']}")
    print()

    # Surgical restoration
    print("🔄 Phase 2: Surgical Restoration (ID <= 64 only)...")
    print("-" * 70)

    success = 0
    skipped_high_id = 0
    skipped_git = 0
    skipped_other = 0
    failed = 0

    for item in valid_items:
        item['title'] = item['clean_title']

        restored, task_id, reason = restore_clean_page(item, backup_dir)

        if restored:
            success += 1
        else:
            if reason == "id_too_high":
                skipped_high_id += 1
                print(f"⏩ Skipped (ID > 64): {item['clean_title']} (ID: {task_id})")
            elif reason == "git_commit":
                skipped_git += 1
            elif reason in ["no_id", "no_task_keyword", "file_not_found"]:
                skipped_other += 1
            else:
                failed += 1

        time.sleep(0.3)

    print("-" * 70)
    print()

    # Summary
    print("=" * 70)
    print("📊 SURGICAL RESTORATION SUMMARY")
    print("=" * 70)
    print(f"Total items scanned:      {len(valid_items)}")
    print(f"Successfully restored:    {success}")
    print(f"Skipped (ID > 64):        {skipped_high_id}")
    print(f"Skipped (Git commits):    {skipped_git}")
    print(f"Skipped (other):          {skipped_other}")
    print(f"Failed (errors):          {failed}")
    print("=" * 70)

    if success > 0:
        print(f"\n✅ Operation Complete. Restored: {success} historical tasks (ID <= 64)")
        print(f"   Skipped {skipped_high_id} ghost tasks (ID > 64)")
        print(f"   Content extracted with metadata amputation")
        return 0
    else:
        print("\n⚠️  WARNING: No tasks were successfully restored")
        return 1


if __name__ == "__main__":
    import requests
    sys.exit(main())
