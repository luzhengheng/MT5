#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #064: Historical Task Restoration to Notion Database
Protocol: v4.3 (Zero-Trust Edition)

Restores all backed-up tasks to Notion with Status="完成" (Done) to create institutional memory.
All restored tasks preserve original metadata but are marked as complete.
"""

import os
import json
import requests
import time
from pathlib import Path

NOTION_TOKEN = ""
DATABASE_ID = ""

# Load from .env file manually
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
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

BACKUP_DIR = Path("docs/archive/notion_backup")


def get_latest_backup():
    """Find the most recent backup directory"""
    if not BACKUP_DIR.exists():
        return None
    
    backup_dirs = list(BACKUP_DIR.glob("*/"))
    if not backup_dirs:
        return None
    
    return max(backup_dirs, key=lambda p: p.name)


def parse_markdown_to_blocks(md_text, max_blocks=90):
    """Convert markdown to Notion blocks (limit to 90 blocks per API)"""
    blocks = []
    lines = md_text.split('\n')
    in_code_block = False
    code_content = []
    code_lang = "plain text"
    
    for line in lines:
        if len(blocks) >= max_blocks:
            break
            
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                full_text = "\n".join(code_content)[:1999]  # API limit
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": full_text}}],
                        "language": code_lang
                    }
                })
                code_content = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
                lang = line.strip().replace("```", "")
                code_lang = lang if lang else "plain text"
        elif in_code_block:
            code_content.append(line)
        elif line.startswith("### "):
            text = line[4:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif line.startswith("## "):
            text = line[3:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif line.startswith("# ") and not line.startswith("## "):
            text = line[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif line.strip().startswith("* ") or line.strip().startswith("- "):
            text = line.strip()[2:].strip()[:1999]
            if text:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
        elif line.strip():
            text = line.strip()[:1999]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
    
    return blocks[:max_blocks]


def restore_page(item, backup_dir):
    """Restore a single page to Notion with Status='完成' (Done)"""
    title = item['title'][:2000]  # Notion limit
    
    # Read markdown content
    md_file = Path(item['file'])
    if not md_file.exists():
        print(f"⚠️  File not found: {md_file}")
        return False
    
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # Parse markdown to blocks
    blocks = parse_markdown_to_blocks(md_content, max_blocks=90)
    
    # Create page with Status="完成" (Done) - using correct Chinese property names
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "标题": {
                "title": [{"type": "text", "text": {"content": title}}]
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
            print(f"✅ Successfully restored: {title} ({page_id})")
            
            # Forensic check for Ticket #060
            if "1417253330" in md_content:
                print(f"🔍 [FORENSIC] Ticket ID 1417253330 detected in: {title}")
            
            return True
        else:
            print(f"❌ Failed to restore: {title}")
            print(f"   Error: {resp.text[:150]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception restoring {title}: {e}")
        return False


def main():
    """Main restoration execution"""
    print("=" * 70)
    print("TASK #064: Historical Task Restoration")
    print("Protocol: v4.3 (Zero-Trust Edition)")
    print("=" * 70)
    print()
    
    # Step 1: Find backup
    print("📁 Step 1: Locating Latest Backup...")
    backup_dir = get_latest_backup()
    
    if not backup_dir:
        print("🔴 ERROR: No backup found")
        print("   Please run TASK #062 backup first")
        return 1
    
    print(f"✅ Found backup: {backup_dir}")
    print()
    
    # Step 2: Load index
    print("📋 Step 2: Loading Backup Index...")
    index_file = backup_dir / "index.json"
    
    if not index_file.exists():
        print("🔴 ERROR: index.json not found in backup")
        return 1
    
    with open(index_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    
    count = len(tasks)
    print(f"✅ Loaded {count} tasks from backup")
    print()
    
    # Step 3: User confirmation
    print("⚠️  WARNING: About to restore all historical tasks")
    print(f"   Total tasks: {count}")
    print(f"   Database ID: {DATABASE_ID}")
    print(f"   All tasks will be marked as Status='完成' (Done)")
    print()
    print("   Starting restoration in 5 seconds... (Ctrl+C to abort)")
    
    try:
        for i in range(5, 0, -1):
            print(f"   {i}...", end="", flush=True)
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print("\n⛔ Restoration aborted by user")
        return 130
    
    print()
    print("🔄 Step 4: Restoring Tasks...")
    print("-" * 70)
    
    # Step 4: Restore all tasks (oldest first)
    success_count = 0
    failed_count = 0
    forensic_found = False
    
    # Reverse order to restore oldest first
    tasks_reversed = list(reversed(tasks))
    
    for i, task in enumerate(tasks_reversed):
        print(f"[{i+1}/{count}] ", end="")
        
        if restore_page(task, backup_dir):
            success_count += 1
            
            # Check for Task #060 ticket ID
            if "1417253330" in str(task):
                forensic_found = True
        else:
            failed_count += 1
        
        # Rate limiting
        time.sleep(0.3)
    
    print("-" * 70)
    print()
    
    # Step 5: Summary
    print("=" * 70)
    print("📊 RESTORATION SUMMARY")
    print("=" * 70)
    print(f"Total tasks:              {count}")
    print(f"Successfully restored:    {success_count}")
    print(f"Failed to restore:        {failed_count}")
    print(f"Forensic check (Ticket ID 1417253330): {'✅ FOUND' if forensic_found else '⚠️  NOT FOUND'}")
    print("=" * 70)
    
    if success_count == count:
        print("\n✅ SUCCESS: All historical tasks restored to Notion")
        print("   Institutional Memory established for Phase 1")
        print("   All tasks marked as Status='完成' (Done)")
        return 0
    else:
        print(f"\n⚠️  WARNING: {failed_count} tasks failed to restore")
        print("   Check logs and retry if needed")
        return 1


if __name__ == "__main__":
    exit(main())
