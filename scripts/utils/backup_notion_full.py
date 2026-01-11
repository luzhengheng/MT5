#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Full Workspace Backup Tool
TASK #062: Complete snapshot of all tasks, metadata, content, and code blocks

Protocol: v4.3 (Zero-Trust Edition)
"""

import os
import json
import requests
import datetime
from pathlib import Path

# Try to import configuration from multiple sources
try:
    import settings
    NOTION_TOKEN = settings.NOTION_TOKEN
    DATABASE_ID = settings.NOTION_DATABASE_ID
except ImportError:
    # Fallback to src.config structure
    try:
        import sys
        sys.path.insert(0, '/opt/mt5-crs')
        from src.config import DINGTALK_WEBHOOK_URL, DINGTALK_SECRET
        # For Notion, try environment variables
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
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
SESSION_DIR = BACKUP_DIR / TIMESTAMP


def get_all_pages():
    """Retrieve all pages from database"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    pages = []
    has_more = True
    next_cursor = None

    print(f"📡 Connecting to Notion database: {DATABASE_ID}...")

    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ API Error: {response.text}")
            return []

        data = response.json()
        pages.extend(data["results"])
        has_more = data["has_more"]
        next_cursor = data.get("next_cursor")
        print(f"   Retrieved {len(pages)} pages...")

    return pages


def get_page_blocks(block_id, depth=0, max_depth=5):
    """Retrieve page content blocks (recursive)"""
    if depth >= max_depth:
        return []

    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    blocks = []
    has_more = True
    next_cursor = None

    while has_more:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor

        try:
            response = requests.get(url, params=params, headers=HEADERS)
            if response.status_code != 200:
                break

            data = response.json()
            blocks.extend(data["results"])
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        except Exception as e:
            print(f"   ⚠️ Block fetch error: {e}")
            break

    return blocks


def parse_property(prop):
    """Parse Notion property values"""
    if not prop:
        return None

    ptype = prop.get("type")

    try:
        if ptype == "title":
            return "".join([t.get("plain_text", "") for t in prop.get("title", [])])
        elif ptype == "rich_text":
            return "".join([t.get("plain_text", "") for t in prop.get("rich_text", [])])
        elif ptype == "select":
            select = prop.get("select")
            return select.get("name") if select else None
        elif ptype == "status":
            status = prop.get("status")
            return status.get("name") if status else None
        elif ptype == "url":
            return prop.get("url")
        elif ptype == "number":
            return prop.get("number")
        elif ptype == "date":
            date = prop.get("date")
            return date.get("start") if date else None
    except Exception as e:
        print(f"   ⚠️ Property parse error: {e}")
        return str(prop)

    return str(prop)


def block_to_markdown(block, depth=0):
    """Convert Notion block to Markdown"""
    if not block:
        return ""

    btype = block.get("type")
    content = ""
    indent = "  " * depth

    try:
        if btype == "paragraph":
            text = "".join([t.get("plain_text", "") for t in block.get("paragraph", {}).get("rich_text", [])])
            content = f"{text}\n\n" if text else ""

        elif btype == "heading_1":
            text = "".join([t.get("plain_text", "") for t in block.get("heading_1", {}).get("rich_text", [])])
            content = f"# {text}\n\n"

        elif btype == "heading_2":
            text = "".join([t.get("plain_text", "") for t in block.get("heading_2", {}).get("rich_text", [])])
            content = f"## {text}\n\n"

        elif btype == "heading_3":
            text = "".join([t.get("plain_text", "") for t in block.get("heading_3", {}).get("rich_text", [])])
            content = f"### {text}\n\n"

        elif btype == "bulleted_list_item":
            text = "".join([t.get("plain_text", "") for t in block.get("bulleted_list_item", {}).get("rich_text", [])])
            content = f"{indent}* {text}\n"

        elif btype == "numbered_list_item":
            text = "".join([t.get("plain_text", "") for t in block.get("numbered_list_item", {}).get("rich_text", [])])
            content = f"{indent}1. {text}\n"

        elif btype == "code":
            text = "".join([t.get("plain_text", "") for t in block.get("code", {}).get("rich_text", [])])
            lang = block.get("code", {}).get("language", "")
            content = f"```{lang}\n{text}\n```\n\n"

        elif btype == "divider":
            content = "---\n\n"

        # Recursive processing for child blocks
        if block.get("has_children") and depth < 5:
            children = get_page_blocks(block["id"], depth + 1)
            for child in children:
                content += block_to_markdown(child, depth + 1)

    except Exception as e:
        print(f"   ⚠️ Block conversion error: {e}")

    return content


def main():
    """Main execution"""
    if not SESSION_DIR.exists():
        SESSION_DIR.mkdir(parents=True)

    print(f"📦 Starting full backup to: {SESSION_DIR}")
    print(f"🕒 Timestamp: {TIMESTAMP}")
    print()

    pages = get_all_pages()

    if not pages:
        print("❌ No pages retrieved. Check API token and database ID.")
        return 1

    print(f"✅ Retrieved {len(pages)} pages total")
    print()

    summary = []

    for i, page in enumerate(pages):
        props = page.get("properties", {})

        # Try common property names for title
        title = "Untitled"
        for title_key in ["Name", "Title", "Task", "名称", "标题"]:
            if title_key in props:
                parsed = parse_property(props[title_key])
                if parsed:
                    title = parsed
                    break

        # Try common property names for status
        status = "Unknown"
        for status_key in ["Status", "状态", "State"]:
            if status_key in props:
                parsed = parse_property(props[status_key])
                if parsed:
                    status = parsed
                    break

        print(f"[{i+1}/{len(pages)}] Processing: {title} ({status})")

        # Retrieve page content
        blocks = get_page_blocks(page["id"])

        # Build Markdown content
        md_content = f"# {title}\n\n"
        md_content += f"**Status**: {status}\n"
        md_content += f"**Page ID**: {page['id']}\n"
        md_content += f"**URL**: {page['url']}\n"
        md_content += f"**Created**: {page.get('created_time', 'Unknown')}\n"
        md_content += f"**Last Edited**: {page.get('last_edited_time', 'Unknown')}\n"
        md_content += "\n---\n\n"

        # Add all properties
        md_content += "## Properties\n\n"
        for prop_name, prop_value in props.items():
            parsed = parse_property(prop_value)
            if parsed:
                md_content += f"- **{prop_name}**: {parsed}\n"
        md_content += "\n---\n\n"

        # Add content blocks
        md_content += "## Content\n\n"
        for block in blocks:
            md_content += block_to_markdown(block)

        # Save Markdown file
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_', '#')]).strip()
        safe_title = safe_title.replace(' ', '_')[:100]  # Limit length
        filename = f"{status}_{safe_title}.md"

        filepath = SESSION_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Collect metadata for JSON index
        summary.append({
            "id": page["id"],
            "title": title,
            "status": status,
            "url": page["url"],
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "file": str(filepath)
        })

    # Save index JSON
    index_path = SESSION_DIR / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print(f"✅ Backup complete: {len(pages)} tasks exported")
    print(f"📁 Backup location: {SESSION_DIR}")
    print(f"📄 Index file: {index_path}")

    # Summary statistics
    status_counts = {}
    for item in summary:
        status = item["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print()
    print("📊 Status Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")

    return 0


if __name__ == "__main__":
    exit(main())
