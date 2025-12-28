#!/usr/bin/env python3
"""
Notion Content Updater Utility
==============================

Reusable utility for updating Notion page content (blocks).
Designed to be used by project_cli.py and other automation scripts.

Protocol: v2.5 (Content Injection & CLI Hardening)
"""

import os
import requests
from typing import List, Dict, Any


# ============================================================================
# Configuration
# ============================================================================

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def get_headers(token: str = None):
    """Get standard Notion API headers."""
    if token is None:
        token = os.environ.get("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN not set")

    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


# ============================================================================
# Block Creation Helpers
# ============================================================================

def create_paragraph(text: str, bold: bool = False, italic: bool = False, code: bool = False) -> Dict[str, Any]:
    """Create a paragraph block."""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": text},
                "annotations": {
                    "bold": bold,
                    "italic": italic,
                    "code": code
                }
            }]
        }
    }


def create_heading(text: str, level: int = 2) -> Dict[str, Any]:
    """Create a heading block (level 1, 2, or 3)."""
    heading_type = f"heading_{level}"
    return {
        "object": "block",
        "type": heading_type,
        heading_type: {
            "rich_text": [{
                "type": "text",
                "text": {"content": text}
            }]
        }
    }


def create_bulleted_list_item(text: str, bold_prefix: str = None) -> Dict[str, Any]:
    """Create a bulleted list item, optionally with bold prefix."""
    rich_text = []

    if bold_prefix:
        rich_text.append({
            "type": "text",
            "text": {"content": f"{bold_prefix}: "},
            "annotations": {"bold": True}
        })
        rich_text.append({
            "type": "text",
            "text": {"content": text}
        })
    else:
        rich_text.append({
            "type": "text",
            "text": {"content": text}
        })

    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": rich_text
        }
    }


def create_code_block(code: str, language: str = "python") -> Dict[str, Any]:
    """Create a code block."""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{
                "type": "text",
                "text": {"content": code}
            }],
            "language": language
        }
    }


def create_callout(text: str, emoji: str = "💡", color: str = "gray_background") -> Dict[str, Any]:
    """Create a callout block."""
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {"content": text}
            }],
            "icon": {"emoji": emoji},
            "color": color
        }
    }


def create_divider() -> Dict[str, Any]:
    """Create a divider block."""
    return {
        "object": "block",
        "type": "divider",
        "divider": {}
    }


# ============================================================================
# Markdown to Notion Converter
# ============================================================================

def markdown_to_blocks(markdown: str) -> List[Dict[str, Any]]:
    """
    Convert markdown text to Notion blocks.

    Supports:
    - # Header 1
    - ## Header 2
    - ### Header 3
    - - List item
    - - **Key**: Value (bold prefix)
    - Plain paragraphs
    - ```code blocks```
    """
    blocks = []
    lines = markdown.strip().split('\n')
    in_code_block = False
    code_lines = []
    code_language = "python"

    for line in lines:
        # Code block start
        if line.strip().startswith('```'):
            if not in_code_block:
                # Starting code block
                in_code_block = True
                code_lines = []
                # Extract language if specified
                lang = line.strip()[3:].strip()
                if lang:
                    code_language = lang
            else:
                # Ending code block
                in_code_block = False
                if code_lines:
                    blocks.append(create_code_block('\n'.join(code_lines), code_language))
                code_lines = []
            continue

        # Inside code block
        if in_code_block:
            code_lines.append(line)
            continue

        line = line.strip()
        if not line:
            continue

        # Heading 1
        if line.startswith('# ') and not line.startswith('## '):
            blocks.append(create_heading(line[2:], level=1))
        # Heading 2
        elif line.startswith('## ') and not line.startswith('### '):
            blocks.append(create_heading(line[3:], level=2))
        # Heading 3
        elif line.startswith('### '):
            blocks.append(create_heading(line[4:], level=3))
        # List item with bold prefix
        elif line.startswith('- **') and '**:' in line:
            key_end = line.index('**:')
            key = line[4:key_end]
            value = line[key_end + 3:].strip()
            blocks.append(create_bulleted_list_item(value, bold_prefix=key))
        # Regular list item
        elif line.startswith('- '):
            blocks.append(create_bulleted_list_item(line[2:]))
        # Paragraph
        else:
            blocks.append(create_paragraph(line))

    return blocks


# ============================================================================
# Page Content Operations
# ============================================================================

def append_blocks(page_id: str, blocks: List[Dict[str, Any]], token: str = None) -> bool:
    """
    Append blocks to a Notion page.

    Args:
        page_id: Notion page ID
        blocks: List of block objects
        token: Optional Notion API token (uses env var if not provided)

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    try:
        response = requests.patch(
            url,
            headers=headers,
            json={"children": blocks},
            timeout=30
        )

        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  Failed to append blocks: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"⚠️  Error appending blocks: {e}")
        return False


def append_markdown(page_id: str, markdown: str, token: str = None) -> bool:
    """
    Append markdown content to a Notion page.

    Args:
        page_id: Notion page ID
        markdown: Markdown text to append
        token: Optional Notion API token

    Returns:
        True if successful, False otherwise
    """
    blocks = markdown_to_blocks(markdown)
    return append_blocks(page_id, blocks, token)


def get_page_blocks(page_id: str, token: str = None) -> List[Dict[str, Any]]:
    """
    Get all blocks from a Notion page.

    Args:
        page_id: Notion page ID
        token: Optional Notion API token

    Returns:
        List of block objects
    """
    headers = get_headers(token)
    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            print(f"⚠️  Failed to get blocks: {response.status_code}")
            return []

    except Exception as e:
        print(f"⚠️  Error getting blocks: {e}")
        return []


def clear_page_blocks(page_id: str, token: str = None) -> bool:
    """
    Clear all blocks from a Notion page.

    Args:
        page_id: Notion page ID
        token: Optional Notion API token

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    blocks = get_page_blocks(page_id, token)

    success = True
    for block in blocks:
        block_id = block["id"]
        url = f"{NOTION_API_URL}/blocks/{block_id}"

        try:
            response = requests.delete(url, headers=headers, timeout=30)
            if response.status_code != 200:
                success = False
        except Exception:
            success = False

    return success


# ============================================================================
# Convenience Functions
# ============================================================================

def update_page_with_plan(page_id: str, plan_markdown: str, prepend_callout: bool = True, token: str = None) -> bool:
    """
    Update a Notion page with a plan/spec.

    Optionally prepends a callout indicating automated content.

    Args:
        page_id: Notion page ID
        plan_markdown: Markdown text of the plan
        prepend_callout: If True, prepend a callout block
        token: Optional Notion API token

    Returns:
        True if successful, False otherwise
    """
    blocks = []

    if prepend_callout:
        blocks.append(create_callout(
            "📋 Implementation Plan (auto-generated)",
            emoji="📋",
            color="blue_background"
        ))
        blocks.append(create_divider())

    # Add plan content
    blocks.extend(markdown_to_blocks(plan_markdown))

    return append_blocks(page_id, blocks, token)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Notion Content Updater Utility")
    print("=" * 60)
    print()
    print("Usage examples:")
    print()
    print("1. Append markdown to a page:")
    print("   from notion_updater import append_markdown")
    print("   append_markdown(page_id, '## Hello\\n- Item 1\\n- Item 2')")
    print()
    print("2. Update page with plan:")
    print("   from notion_updater import update_page_with_plan")
    print("   update_page_with_plan(page_id, plan_text)")
    print()
    print("3. Create custom blocks:")
    print("   from notion_updater import create_heading, create_paragraph")
    print("   blocks = [create_heading('Title'), create_paragraph('Text')]")
    print("   append_blocks(page_id, blocks)")
