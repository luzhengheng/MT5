#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Notion Page Body for Ticket #014
========================================
Injects content into the Notion page for Task #014 (MT5 Gateway Core Service).

This script:
1. Queries the database to find Ticket #014
2. Appends rich content blocks (headings, bullets, paragraphs, quotes)
3. Verifies the content was added successfully
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

if not NOTION_TOKEN or not NOTION_ISSUES_DB_ID:
    print("❌ Error: Missing NOTION_TOKEN or NOTION_ISSUES_DB_ID in .env")
    sys.exit(1)

# Notion API Configuration
NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def find_ticket_014():
    """Find the Notion page for Ticket #014"""
    print("🔍 Searching for Ticket #014 in Notion database...")

    url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}/query"

    payload = {
        "filter": {
            "property": "标题",
            "title": {
                "contains": "014"
            }
        }
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            if results:
                page = results[0]
                page_id = page.get('id')
                title = page.get('properties', {}).get('标题', {}).get('title', [])
                title_text = title[0]['text']['content'] if title else "Unknown"

                print(f"   ✅ Found: {title_text}")
                print(f"   Page ID: {page_id}")
                return page_id
            else:
                print(f"   ❌ Ticket #014 not found in database")
                return None
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            print(f"      {response.text[:200]}")
            return None

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return None

def append_blocks(page_id):
    """Append content blocks to the Notion page"""
    print(f"\n📝 Appending content blocks to page {page_id}...")

    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    # Define blocks to append
    blocks = [
        # Release Summary Section
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📋 Release Summary"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Core Component: MT5Service (Singleton)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "AI Engine: Gemini Review Bridge v3.3 (Insightful Edition)"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Verification: verify_mt5_connection.py"
                        }
                    }
                ]
            }
        },
        # Status Section
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "✅ Status"
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Code pushed to GitHub. Linux logic verification passed. Ready for Windows deployment."
                        }
                    }
                ]
            }
        },
        # Important Note
        {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Note: The connection failure on Linux is expected. Physical connection will be verified in Task #015."
                        }
                    }
                ]
            }
        }
    ]

    payload = {
        "children": blocks
    }

    try:
        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   ✅ Successfully appended {len(results)} blocks")
            return True
        else:
            print(f"   ❌ Failed to append blocks: {response.status_code}")
            print(f"      Error: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_content(page_id):
    """Verify that content was added to the page"""
    print(f"\n🔍 Verifying content was added...")

    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    try:
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            blocks = data.get('results', [])

            if blocks:
                print(f"   ✅ Page now contains {len(blocks)} blocks")
                print(f"\n   Block Summary:")
                for i, block in enumerate(blocks[:7]):  # Show first 7 blocks
                    block_type = block.get('type', 'unknown')
                    print(f"      {i+1}. {block_type}")
                return True
            else:
                print(f"   ⚠️  Page has no child blocks")
                return False
        else:
            print(f"   ❌ Verification failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("📝 NOTION PAGE BODY UPDATE - Ticket #014")
    print("=" * 80)
    print()

    # Step 1: Find the ticket
    page_id = find_ticket_014()
    if not page_id:
        print("\n❌ Cannot proceed without finding Ticket #014")
        sys.exit(1)

    # Step 2: Append content blocks
    success = append_blocks(page_id)
    if not success:
        print("\n❌ Failed to append content blocks")
        sys.exit(1)

    # Step 3: Verify content
    verify_content(page_id)

    # Final summary
    print("\n" + "=" * 80)
    print("✅ NOTION PAGE BODY UPDATE COMPLETE")
    print("=" * 80)
    print()
    print("📋 Content Added to Ticket #014:")
    print("   ✅ Release Summary section")
    print("      • Core Component: MT5Service (Singleton)")
    print("      • AI Engine: Gemini Review Bridge v3.3 (Insightful Edition)")
    print("      • Verification: verify_mt5_connection.py")
    print()
    print("   ✅ Status section")
    print("      • Status paragraph")
    print("      • Important note (Linux vs Windows)")
    print()
    print("📍 Access the page:")
    print("   https://www.notion.so/2d2c88582b4e81d9bcb7d3f0e3d63980")
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
