#!/usr/bin/env python3
"""
Read task context from Notion database
Usage: python3 scripts/read_task_context.py <task_id>
Example: python3 scripts/read_task_context.py 093.1
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def get_notion_headers():
    """Get Notion API headers"""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN not found in environment")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def search_task_in_notion(task_id: str):
    """Search for a task in Notion issues database"""
    db_id = os.getenv("NOTION_ISSUES_DB_ID")
    if not db_id:
        raise ValueError("NOTION_ISSUES_DB_ID not found in environment")

    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = get_notion_headers()

    # Search for task by ID (using Chinese property name)
    payload = {
        "filter": {
            "or": [
                {
                    "property": "标题",
                    "title": {
                        "contains": task_id
                    }
                },
                {
                    "property": "标题",
                    "title": {
                        "contains": f"#{task_id}"
                    }
                },
                {
                    "property": "标题",
                    "title": {
                        "contains": f"Task #{task_id}"
                    }
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()

def extract_task_info(page_data):
    """Extract task information from Notion page"""
    if not page_data or "results" not in page_data or len(page_data["results"]) == 0:
        return None

    page = page_data["results"][0]
    properties = page.get("properties", {})

    # Extract title (Chinese property name)
    title_prop = properties.get("标题", {})
    title = ""
    if title_prop.get("title"):
        title = "".join([t.get("plain_text", "") for t in title_prop["title"]])

    # Extract status (Chinese property name)
    status_prop = properties.get("状态", {})
    status = status_prop.get("status", {}).get("name", "Unknown")

    # Extract priority (Chinese property name)
    priority_prop = properties.get("优先级", {})
    priority = priority_prop.get("select", {}).get("name", "Medium")

    # Get page URL
    page_url = page.get("url", "")

    return {
        "title": title,
        "status": status,
        "priority": priority,
        "url": page_url,
        "page_id": page.get("id", "")
    }

def get_page_content(page_id: str):
    """Get the content blocks of a Notion page with pagination support"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = get_notion_headers()

    all_blocks = []
    has_more = True
    start_cursor = None

    while has_more:
        params = {"page_size": 100}
        if start_cursor:
            params["start_cursor"] = start_cursor

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        all_blocks.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return {"results": all_blocks}

def get_child_blocks(block_id: str):
    """Recursively get child blocks"""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    headers = get_notion_headers()

    all_blocks = []
    has_more = True
    start_cursor = None

    while has_more:
        params = {"page_size": 100}
        if start_cursor:
            params["start_cursor"] = start_cursor

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        all_blocks.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return all_blocks

def extract_text_from_blocks(blocks_data, indent_level=0):
    """Extract text content from Notion blocks with recursive child block support"""
    if not blocks_data or "results" not in blocks_data:
        return ""

    indent = "  " * indent_level
    text_content = []

    for block in blocks_data["results"]:
        block_type = block.get("type")
        block_id = block.get("id")
        has_children = block.get("has_children", False)

        if block_type == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text:
                text_content.append(f"{indent}{text}")

        elif block_type == "heading_1":
            rich_text = block.get("heading_1", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text:
                text_content.append(f"\n# {text}\n")

        elif block_type == "heading_2":
            rich_text = block.get("heading_2", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text:
                text_content.append(f"\n## {text}\n")

        elif block_type == "heading_3":
            rich_text = block.get("heading_3", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text:
                text_content.append(f"\n### {text}\n")

        elif block_type == "bulleted_list_item":
            rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text:
                text_content.append(f"{indent}• {text}")

        elif block_type == "numbered_list_item":
            rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text:
                text_content.append(f"{indent}• {text}")

        elif block_type == "to_do":
            rich_text = block.get("to_do", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            checked = block.get("to_do", {}).get("checked", False)
            checkbox = "☑" if checked else "☐"
            if text:
                text_content.append(f"{indent}{checkbox} {text}")

        elif block_type == "code":
            rich_text = block.get("code", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            language = block.get("code", {}).get("language", "")
            if text:
                text_content.append(f"\n```{language}\n{text}\n```\n")

        # Recursively get child blocks
        if has_children:
            try:
                child_blocks = get_child_blocks(block_id)
                if child_blocks:
                    child_content = extract_text_from_blocks(
                        {"results": child_blocks},
                        indent_level + 1
                    )
                    if child_content:
                        text_content.append(child_content)
            except Exception as e:
                print(f"Warning: Could not fetch children for block {block_id}: {e}")

    return "\n".join(text_content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/read_task_context.py <task_id>")
        print("Example: python3 scripts/read_task_context.py 093.1")
        sys.exit(1)

    task_id = sys.argv[1]

    print(f"🔍 Searching for Task #{task_id} in Notion...")

    try:
        # Search for task
        results = search_task_in_notion(task_id)
        task_info = extract_task_info(results)

        if not task_info:
            print(f"❌ Task #{task_id} not found in Notion database")
            sys.exit(1)

        print(f"\n✅ Found Task: {task_info['title']}")
        print(f"   Status: {task_info['status']}")
        print(f"   Priority: {task_info['priority']}")
        print(f"   URL: {task_info['url']}")

        # Get page content
        print(f"\n📄 Fetching task details...")
        blocks = get_page_content(task_info['page_id'])
        content = extract_text_from_blocks(blocks)

        if content:
            print(f"\n{'='*80}")
            print("TASK CONTENT:")
            print(f"{'='*80}")
            print(content)
            print(f"{'='*80}\n")
        else:
            print("\n⚠️  No detailed content found in task page")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
