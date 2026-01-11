#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #064.5: Smart Restoration & Hygiene
Protocol: v4.3 (Zero-Trust Edition)

Performs: Purge -> Filter -> Fix -> Inject
- Removes Git commit noise
- Fixes Mojibake (encoding issues)
- Restores ONLY valid task items (#001-#064)
"""

import os
import json
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


def parse_markdown_to_blocks(md_text, max_blocks=90):
    """Simplified markdown parser with length limits"""
    blocks = []
    lines = md_text.split('\n')
    
    for line in lines:
        if len(blocks) >= max_blocks:
            break
        clean = line.strip()
        if clean and len(clean) > 0:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": clean[:1999]}}]
                }
            })
    
    return blocks[:max_blocks]


def extract_task_id(title):
    """Extract task ID for sorting"""
    match = re.search(r'#(\d+)', title)
    if match:
        return int(match.group(1))
    return 999999


def restore_clean_page(item, backup_dir):
    """Restore single page with encoding fix and validation"""
    raw_title = item['title']
    
    # 1. Fix encoding
    clean_title = fix_encoding(raw_title)
    
    # 2. Filter: ONLY allow items containing "Task" or "工单" followed by #number
    if not re.search(r'(TASK|Task|工单)\s*#\d+', clean_title, re.IGNORECASE):
        # Even if contains "Task", if it's a Git commit log, skip it
        if re.match(r'^(feat|fix|docs|chore|style|refactor|test|ops):', clean_title, re.IGNORECASE):
            return False
        return False
    
    # Skip Git commit logs
    if re.match(r'^(feat|fix|docs|chore|style|refactor|test|ops):', clean_title, re.IGNORECASE):
        return False

    file_path = backup_dir / Path(item['file']).name
    if not file_path.exists():
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    blocks = parse_markdown_to_blocks(md_content, max_blocks=90)

    # Using correct Chinese property names
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
            print(f"✅ Restoring: {clean_title}")
            return True
        else:
            print(f"❌ Failed to restore {clean_title}: {resp.text[:150]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    """Main execution with smart filtering"""
    print("=" * 70)
    print("TASK #064.5: Smart Restoration & Hygiene")
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
    
    # Pre-process: Fix encoding and extract IDs
    print("🔍 Phase 2: Filtering & Encoding Fix...")
    valid_items = []
    
    for item in items:
        clean_title = fix_encoding(item['title'])
        
        # Strict filter: Must contain Task/工单 followed by #number
        if re.search(r'(TASK|Task|工单)\s*#\d+', clean_title, re.IGNORECASE):
            # Exclude Git commit logs
            if not re.match(r'^(feat|fix|docs|chore|style|refactor|test|ops):', clean_title, re.IGNORECASE):
                item['clean_title'] = clean_title
                item['task_id'] = extract_task_id(clean_title)
                
                # Exclude abnormally large IDs (might be year or hash)
                if item['task_id'] < 1000:
                    valid_items.append(item)

    # Sort by task ID (from #001 to #086)
    valid_items.sort(key=lambda x: x['task_id'])

    print(f"✅ Valid tasks found: {len(valid_items)}")
    print(f"🗑️  Filtered out: {len(items) - len(valid_items)} noise items")
    
    if valid_items:
        print(f"📊 ID Range: #{valid_items[0]['task_id']} - #{valid_items[-1]['task_id']}")
    print()
    
    # Execution
    print("🔄 Phase 3: Restoration Execution...")
    print("-" * 70)
    
    success = 0
    failed = 0
    
    for i, item in enumerate(valid_items):
        # Update title to fixed version
        item['title'] = item['clean_title']
        
        print(f"[{i+1}/{len(valid_items)}] ", end="")
        if restore_clean_page(item, backup_dir):
            success += 1
        else:
            failed += 1
        
        time.sleep(0.3)  # Rate limiting
    
    print("-" * 70)
    print()
    
    # Summary
    print("=" * 70)
    print("📊 SMART RESTORATION SUMMARY")
    print("=" * 70)
    print(f"Total valid tasks:        {len(valid_items)}")
    print(f"Successfully restored:    {success}")
    print(f"Failed to restore:        {failed}")
    print(f"Noise items filtered:     {len(items) - len(valid_items)}")
    print("=" * 70)
    
    if success == len(valid_items):
        print("\n✅ SUCCESS: All valid tasks restored with clean data")
        print("   Institutional Memory rebuilt without noise")
        return 0
    else:
        print(f"\n⚠️  WARNING: {failed} tasks failed to restore")
        return 1


if __name__ == "__main__":
    import requests  # Import here to avoid early failure
    sys.exit(main())
