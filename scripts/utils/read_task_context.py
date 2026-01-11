#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Task Context Fetcher
Retrieves task content from Notion database by Task ID for autonomous execution.
"""

import requests
import json
import sys
import os

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


def get_page_by_task_id(task_id):
    """Query Notion database for page containing task ID"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    # Search for title containing task ID (e.g., "#065" or "065")
    # Use correct Chinese property name: 标题
    payload = {
        "filter": {
            "property": "标题",
            "title": {"contains": f"#{task_id}"}
        }
    }

    resp = requests.post(url, json=payload, headers=HEADERS)

    if resp.status_code != 200:
        print(f"⚠️  API Error: {resp.status_code}")
        print(resp.text[:200])
        return None

    data = resp.json()

    if not data.get("results"):
        # Try without # prefix
        payload["filter"]["property"] = "标题"
        payload["filter"]["title"]["contains"] = task_id
        resp = requests.post(url, json=payload, headers=HEADERS)
        data = resp.json()

        if not data.get("results"):
            return None

    return data["results"][0]


def get_blocks(block_id):
    """Retrieve all content blocks from a Notion page"""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        return []

    return resp.json().get("results", [])


def block_to_markdown(block):
    """Convert Notion block to markdown format"""
    btype = block.get("type")

    if not btype:
        return ""

    try:
        if btype == "paragraph":
            if "paragraph" in block and "rich_text" in block["paragraph"]:
                return "".join([t.get("plain_text", "") for t in block["paragraph"]["rich_text"]])

        elif btype == "heading_1":
            if "heading_1" in block and "rich_text" in block["heading_1"]:
                return "# " + "".join([t.get("plain_text", "") for t in block["heading_1"]["rich_text"]])

        elif btype == "heading_2":
            if "heading_2" in block and "rich_text" in block["heading_2"]:
                return "## " + "".join([t.get("plain_text", "") for t in block["heading_2"]["rich_text"]])

        elif btype == "heading_3":
            if "heading_3" in block and "rich_text" in block["heading_3"]:
                return "### " + "".join([t.get("plain_text", "") for t in block["heading_3"]["rich_text"]])

        elif btype == "bulleted_list_item":
            if "bulleted_list_item" in block and "rich_text" in block["bulleted_list_item"]:
                return "* " + "".join([t.get("plain_text", "") for t in block["bulleted_list_item"]["rich_text"]])

        elif btype == "to_do":
            if "to_do" in block:
                checked = "[x]" if block["to_do"].get("checked", False) else "[ ]"
                text = "".join([t.get("plain_text", "") for t in block["to_do"].get("rich_text", [])])
                return f"- {checked} {text}"

        elif btype == "code":
            if "code" in block:
                lang = block["code"].get("language", "plain text")
                code = "".join([t.get("plain_text", "") for t in block["code"].get("rich_text", [])])
                return f"```{lang}\n{code}\n```"

        elif btype == "callout":
            if "callout" in block and "rich_text" in block["callout"]:
                icon = block["callout"].get("icon", {}).get("emoji", "💡")
                text = "".join([t.get("plain_text", "") for t in block["callout"]["rich_text"]])
                return f"{icon} {text}"

        elif btype == "quote":
            if "quote" in block and "rich_text" in block["quote"]:
                return "> " + "".join([t.get("plain_text", "") for t in block["quote"]["rich_text"]])

        elif btype == "divider":
            return "---"

    except Exception as e:
        print(f"⚠️  Error parsing block type {btype}: {e}", file=sys.stderr)

    return ""


def main():
    """Main execution: Fetch and display task content from Notion"""
    if len(sys.argv) < 2:
        print("Usage: python3 read_task_context.py <TASK_ID>")
        print("Example: python3 read_task_context.py 065")
        sys.exit(1)

    task_id = sys.argv[1].lstrip('#')  # Strip # if provided

    print(f"🔍 Fetching Task #{task_id} from Notion...")
    print()

    page = get_page_by_task_id(task_id)

    if not page:
        print(f"🔴 Task #{task_id} not found in database.")
        print()
        print("Possible issues:")
        print("  - Task doesn't exist in Notion")
        print("  - Task ID format incorrect")
        print("  - Database connection issue")
        sys.exit(1)

    # Extract title from correct Chinese property
    title = ""
    if "properties" in page and "标题" in page["properties"]:
        title_data = page["properties"]["标题"]
        if "title" in title_data and title_data["title"]:
            title = title_data["title"][0].get("plain_text", "Untitled")

    print(f"✅ Found: {title}")
    print("=" * 70)
    print()

    # Fetch and display content blocks
    blocks = get_blocks(page["id"])

    if not blocks:
        print("⚠️  No content blocks found in this page.")
        return

    for block in blocks:
        md = block_to_markdown(block)
        if md:
            print(md)
            print()  # Add spacing between blocks


if __name__ == "__main__":
    main()
