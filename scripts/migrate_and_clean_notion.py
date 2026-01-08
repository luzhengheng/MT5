#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Workspace Cleanup - Archive All Tasks
TASK #063: Clean workspace by archiving all pages to Notion's built-in trash
Protocol: v4.3 (Zero-Trust Edition)

WARNING: This operation will archive (soft-delete) all pages in the database.
Pages can be recovered from Notion trash within 30 days.
"""

import os
import requests
import json
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration loading (try multiple sources)
try:
    import settings
    NOTION_TOKEN = settings.NOTION_TOKEN
    DATABASE_ID = settings.NOTION_DB_ID
except ImportError:
    # Fallback to environment variables
    try:
        sys.path.insert(0, '/opt/mt5-crs')
        NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
        DATABASE_ID = os.getenv("NOTION_DB_ID", "")

        if not NOTION_TOKEN or not DATABASE_ID:
            print("🔴 Configuration failed: NOTION_TOKEN or DATABASE_ID not found")
            print("   Please set environment variables or create settings.py")
            exit(1)
    except Exception as e:
        print(f"🔴 Configuration loading failed: {e}")
        exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

BACKUP_DIR = Path("docs/archive/notion_backup")


def check_backup_exists():
    """Verify that backup exists before proceeding with cleanup"""
    if not BACKUP_DIR.exists():
        return False, "Backup directory does not exist"

    # Check for recent backup files
    backup_dirs = list(BACKUP_DIR.glob("*/"))
    if not backup_dirs:
        return False, "No backup sessions found"

    # Find most recent backup
    latest_backup = max(backup_dirs, key=lambda p: p.name)
    md_files = list(latest_backup.glob("*.md"))

    if len(md_files) < 50:  # Expect at least 50 tasks
        return False, f"Backup incomplete: only {len(md_files)} files found"

    return True, f"Backup verified: {len(md_files)} files in {latest_backup.name}"


def get_all_pages():
    """Retrieve all pages from database (without filter)"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    pages = []
    has_more = True
    next_cursor = None

    print(f"📡 Querying database: {DATABASE_ID}...")

    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        resp = requests.post(url, json=payload, headers=HEADERS)
        if resp.status_code != 200:
            print(f"❌ Query Error: {resp.text}")
            return []

        data = resp.json()
        pages.extend(data["results"])
        has_more = data["has_more"]
        next_cursor = data.get("next_cursor")
        print(f"   Retrieved {len(pages)} pages...")

    return pages


def archive_page(page_id, title):
    """Archive a page using Notion API (soft delete to trash)"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"archived": True}

    resp = requests.patch(url, json=payload, headers=HEADERS)
    if resp.status_code == 200:
        print(f"🗑️  Successfully archived: {title} ({page_id})")
        return True
    else:
        print(f"⚠️  Archive Failed for {page_id}: {resp.text}")
        return False


def extract_title(page):
    """Extract title from page properties"""
    props = page.get("properties", {})

    # Try common title property names
    for title_key in ["Name", "Task", "Title", "名称", "标题"]:
        if title_key in props:
            prop = props[title_key]
            if prop.get("type") == "title" and prop.get("title"):
                return prop["title"][0]["plain_text"]

    return "Untitled"


def main():
    """Main execution with safety checks"""
    print("=" * 70)
    print("TASK #063: Notion Workspace Cleanup (Archive All Pages)")
    print("Protocol: v4.3 (Zero-Trust Edition)")
    print("=" * 70)
    print()

    # Step 1: Safety check - verify backup exists
    print("🛡️  Step 1: Safety Check - Verifying Backup...")
    backup_ok, backup_msg = check_backup_exists()

    if not backup_ok:
        print(f"🔴 CRITICAL ERROR: {backup_msg}")
        print("   For data safety, cleanup operation has been ABORTED.")
        print("   Please run Task #062 backup first.")
        sys.exit(1)

    print(f"✅ {backup_msg}")
    print()

    # Step 2: Query all pages
    print("📊 Step 2: Querying Active Pages...")
    pages = get_all_pages()
    count = len(pages)

    if count == 0:
        print("✨ Database is already empty. No cleanup needed.")
        return 0

    print(f"📋 Found {count} active pages")
    print()

    # Step 3: User confirmation (with countdown)
    print("⚠️  WARNING: About to archive (soft-delete) all pages")
    print(f"   Total pages: {count}")
    print(f"   Database ID: {DATABASE_ID}")
    print("   Pages will be moved to Notion trash (recoverable for 30 days)")
    print()
    print("   Starting cleanup in 5 seconds... (Ctrl+C to abort)")

    try:
        for i in range(5, 0, -1):
            print(f"   {i}...", end="", flush=True)
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print("\n⛔ Cleanup aborted by user")
        return 130

    print()
    print("🧹 Step 3: Archiving Pages...")
    print("-" * 70)

    # Step 4: Archive each page
    success_count = 0
    failed_pages = []

    for i, page in enumerate(pages):
        page_id = page["id"]
        title = extract_title(page)

        print(f"[{i+1}/{count}] ", end="")
        if archive_page(page_id, title):
            success_count += 1
        else:
            failed_pages.append((page_id, title))

    print("-" * 70)
    print()

    # Step 5: Final verification
    print("🔍 Step 4: Final Verification...")
    remaining_pages = get_all_pages()
    remaining_count = len(remaining_pages)

    print()
    print("=" * 70)
    print("📊 CLEANUP SUMMARY")
    print("=" * 70)
    print(f"Total pages found:        {count}")
    print(f"Successfully archived:    {success_count}")
    print(f"Failed to archive:        {len(failed_pages)}")
    print(f"Remaining pages:          {remaining_count}")
    print("=" * 70)

    if failed_pages:
        print("\n⚠️  Failed Pages:")
        for pid, title in failed_pages:
            print(f"   - {title} ({pid})")

    if remaining_count == 0:
        print("\n✅ SUCCESS: Notion workspace is clean (0 active pages)")
        print("   All pages have been archived to Notion trash")
        print("   Recovery: Pages can be restored from trash within 30 days")
        return 0
    else:
        print(f"\n⚠️  WARNING: {remaining_count} pages still active")
        print("   Please check logs and retry if needed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
