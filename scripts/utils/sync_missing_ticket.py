#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill Missing Ticket #014 in Notion
=====================================
Creates a new Page in the Issues database for Task #014
(MT5 Gateway Core Service) which was implemented but not recorded in Notion.

Steps:
1. Connect to Notion using NOTION_TOKEN
2. CREATE a new Page in NOTION_ISSUES_DB_ID
3. Set properties: Title, Status (Done), Type (Feature)
4. Display the created ticket URL
"""

import os
import sys
import requests
import json
from datetime import datetime
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

def get_db_properties():
    """Retrieve database structure to understand available properties"""
    print("🔍 Inspecting Notion database structure...")

    url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            db_info = response.json()
            properties = db_info.get("properties", {})
            print(f"   ✅ Found {len(properties)} properties:")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "unknown")
                print(f"      • {prop_name}: {prop_type}")
            return properties
        else:
            print(f"   ❌ Failed to fetch database: {response.status_code}")
            print(f"      {response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return None

def create_ticket_014():
    """Create Ticket #014 in Notion Issues database"""
    print("\n📝 Creating Ticket #014: MT5 Gateway Core Service")

    url = f"{NOTION_API_URL}/pages"

    # Build properties based on actual database schema
    properties = {
        "标题": {
            "title": [
                {
                    "text": {
                        "content": "#014 MT5 Gateway Core Service"
                    }
                }
            ]
        },
        "状态": {
            "status": {
                "name": "完成"  # Task completed (Chinese: 完成)
            }
        },
        "类型": {
            "select": {
                "name": "Feature"  # Feature implementation
            }
        }
    }

    payload = {
        "parent": {
            "database_id": NOTION_ISSUES_DB_ID
        },
        "properties": properties
    }

    # Optional: Add description/content if supported
    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            data = response.json()
            page_id = data.get('id')
            page_url = data.get('url')

            print(f"\n✅ SUCCESS: Ticket #014 created!")
            print(f"   Page ID: {page_id}")
            print(f"   URL: {page_url}")

            # Extract Notion page ID in standard format (without hyphens)
            notion_url_id = page_id.replace('-', '')
            notion_link = f"https://www.notion.so/{notion_url_id}"
            print(f"   Direct Link: {notion_link}")

            return page_id, page_url
        else:
            print(f"\n❌ FAILED to create ticket: {response.status_code}")
            print(f"   Error: {response.text}")
            return None, None

    except Exception as e:
        print(f"\n❌ Exception during creation: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def verify_ticket():
    """Query the database to verify the new ticket exists"""
    print("\n🔍 Verifying ticket creation...")

    url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}/query"

    # Search for items with "014" in the title
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
                print(f"   ✅ Verification successful!")
                print(f"   Found {len(results)} item(s) matching '014':")
                for item in results:
                    title = item.get('properties', {}).get('标题', {}).get('title', [])
                    title_text = title[0]['text']['content'] if title else "N/A"
                    status = item.get('properties', {}).get('状态', {}).get('status', {}).get('name', 'N/A')
                    print(f"      • {title_text} [{status}]")
                return True
            else:
                print(f"   ⚠️  No items found matching '014'")
                return False
        else:
            print(f"   ❌ Verification failed: {response.status_code}")
            print(f"      {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🎯 BACKFILL MISSING TICKET #014 IN NOTION")
    print("=" * 80)
    print()

    # Step 1: Inspect database
    properties = get_db_properties()
    if not properties:
        print("\n⚠️  Could not inspect database, continuing anyway...")

    # Step 2: Create the ticket
    page_id, page_url = create_ticket_014()

    if not page_id:
        print("\n❌ Failed to create ticket. Exiting.")
        sys.exit(1)

    # Step 3: Verify creation
    success = verify_ticket()

    # Step 4: Final report
    print("\n" + "=" * 80)
    print("✅ BACKFILL COMPLETE")
    print("=" * 80)
    print()
    print("📋 Ticket #014 Summary:")
    print(f"   Title: #014 MT5 Gateway Core Service")
    print(f"   Status: Done")
    print(f"   Type: Feature")
    print(f"   Description: Implemented MT5Service singleton, Bridge v3.3, and verification scripts")
    print()
    print("📍 Access the ticket:")
    print(f"   Notion URL: {page_url}")
    print()
    print("📝 Implementation Details:")
    print("   ✅ src/gateway/mt5_service.py - Singleton MT5Service class")
    print("   ✅ gemini_review_bridge.py v3.3 - AI code review with curl_cffi penetration")
    print("   ✅ scripts/verify_mt5_connection.py - Connectivity verification")
    print("   ✅ scripts/audit_current_task.py - TDD validation framework")
    print()
    print("🎯 Git Commits:")
    print("   • e342d9a - feat(gateway): 工单 #014.1 完成 - MT5 Service 核心实现")
    print("   • 3a5bcd8 - docs: Task #014 Release Summary - MT5 Gateway Service Complete")
    print()
    print("=" * 80)
    print()

    if success:
        print("✅ All steps completed successfully!")
        print("   Ticket #014 is now visible in the Notion Issues database.")
        sys.exit(0)
    else:
        print("⚠️  Ticket created but verification inconclusive.")
        print("   Check Notion manually to confirm.")
        sys.exit(0)

if __name__ == "__main__":
    main()
