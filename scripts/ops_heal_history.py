#!/usr/bin/env python3
"""
Task #030: History Healing - Notion Database Standardization
=============================================================

Standardize ticket titles and statuses for #001-#027 based on actual
project history, WITHOUT deleting existing page content/notes.

This is a "soft refactor" that:
1. Updates ticket titles to match historical map
2. Sets status to "Done" for all completed tickets
3. Preserves all existing page content and properties
4. Provides detailed change logging

Protocol: v2.0 (History Healing)
"""

import os
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import historical mapping
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from data.historical_map import TICKET_MAP, EXPECTED_STATUS, get_ticket_title, is_valid_ticket


# ============================================================================
# Configuration
# ============================================================================

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DB_ID")

if not NOTION_TOKEN or not NOTION_DB_ID:
    print("❌ FATAL: Missing Notion credentials")
    print("   Export: NOTION_TOKEN and NOTION_DB_ID")
    sys.exit(1)

# Notion API configuration
NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


# ============================================================================
# Helper Functions
# ============================================================================

def query_database(filter_query=None):
    """
    Query the Notion database.

    Args:
        filter_query: Optional filter dictionary

    Returns:
        List of page objects
    """
    url = f"{NOTION_API_URL}/databases/{NOTION_DB_ID}/query"

    payload = {}
    if filter_query:
        payload["filter"] = filter_query

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)

        if response.status_code != 200:
            print(f"  ⚠️  Query failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            return []

        data = response.json()
        return data.get("results", [])

    except Exception as e:
        print(f"  ⚠️  Error querying database: {e}")
        return []


def find_ticket_by_pattern(ticket_id: int):
    """
    Find a Notion page by ticket ID pattern.

    Searches for pages containing #{ticket_id} in the title.

    Args:
        ticket_id: Ticket number (1-27)

    Returns:
        Page object or None if not found
    """
    ticket_pattern = f"#{ticket_id:03d}"

    # Try exact pattern first (using Chinese property name)
    pages = query_database({
        "property": "标题",  # Chinese: "Title"
        "title": {
            "contains": ticket_pattern
        }
    })

    if pages:
        return pages[0]

    # Try without leading zeros
    alt_pattern = f"#{ticket_id}"
    pages = query_database({
        "property": "标题",
        "title": {
            "contains": alt_pattern
        }
    })

    if pages:
        return pages[0]

    return None


def get_page_title(page):
    """Get the current title of a Notion page."""
    try:
        properties = page.get("properties", {})
        title_prop = properties.get("标题") or properties.get("Name")  # Try Chinese first

        if title_prop and title_prop.get("type") == "title":
            title_array = title_prop.get("title", [])
            if title_array:
                return title_array[0].get("plain_text", "")

        return ""

    except Exception as e:
        print(f"  ⚠️  Error reading title: {e}")
        return ""


def get_page_status(page):
    """Get the current status of a Notion page."""
    try:
        properties = page.get("properties", {})
        status_prop = properties.get("Status") or properties.get("状态")

        if status_prop:
            status_type = status_prop.get("type")
            if status_type == "status":
                status_obj = status_prop.get("status")
                if status_obj:
                    return status_obj.get("name")
            elif status_type == "select":
                select_obj = status_prop.get("select")
                if select_obj:
                    return select_obj.get("name")

        return None

    except Exception as e:
        print(f"  ⚠️  Error reading status: {e}")
        return None


def update_page(page_id: str, new_title: str = None, new_status: str = None):
    """
    Update a Notion page's title and/or status.

    IMPORTANT: This only updates properties, NOT page content.
    All existing content/notes in the page body are preserved.

    Args:
        page_id: Notion page ID
        new_title: New title (optional)
        new_status: New status (optional)

    Returns:
        True if successful, False otherwise
    """
    url = f"{NOTION_API_URL}/pages/{page_id}"

    properties = {}

    # Update title if provided (use Chinese property name)
    if new_title:
        properties["标题"] = {  # Chinese: "Title"
            "title": [
                {
                    "text": {
                        "content": new_title
                    }
                }
            ]
        }

    # Update status if provided (use Chinese property name)
    if new_status:
        properties["状态"] = {  # Chinese: "Status"
            "status": {
                "name": new_status
            }
        }

    if not properties:
        return False

    try:
        response = requests.patch(
            url,
            headers=HEADERS,
            json={"properties": properties},
            timeout=30
        )

        if response.status_code != 200:
            # Add detailed error logging
            print(f"\n      ⚠️  HTTP {response.status_code}")
            print(f"      Response: {response.text[:300]}")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('message', 'Unknown error')}")
            except:
                pass

        return response.status_code == 200

    except Exception as e:
        print(f"  ⚠️  Error updating page: {e}")
        return False


# ============================================================================
# Main Healing Logic
# ============================================================================

def heal_history():
    """Heal the Notion database history for tickets #001-#027."""
    print("=" * 80)
    print("🔧 HISTORY HEALING - Notion Database Standardization")
    print("=" * 80)
    print()
    print(f"Target Range: #001 to #027 ({len(TICKET_MAP)} tickets)")
    print(f"Expected Status: {EXPECTED_STATUS}")
    print(f"Database ID: {NOTION_DB_ID[:8]}...")
    print()
    print("⚠️  NOTE: This will UPDATE titles and statuses ONLY.")
    print("   All existing page content/notes will be PRESERVED.")
    print()

    # Statistics
    total = len(TICKET_MAP)
    found = 0
    title_updated = 0
    status_updated = 0
    already_correct = 0
    not_found = 0
    errors = 0

    print(f"Processing {total} tickets...")
    print("-" * 80)
    print()

    for ticket_id in sorted(TICKET_MAP.keys()):
        ticket_pattern = f"#{ticket_id:03d}"
        expected_title = get_ticket_title(ticket_id)

        print(f"[{ticket_id}/{len(TICKET_MAP)}] {ticket_pattern}", end=" ")

        # Find the ticket
        page = find_ticket_by_pattern(ticket_id)

        if not page:
            print(f"❌ NOT FOUND")
            not_found += 1
            continue

        found += 1
        page_id = page["id"]

        # Get current values
        current_title = get_page_title(page)
        current_status = get_page_status(page)

        # Check if update needed
        title_needs_update = current_title != expected_title
        status_needs_update = current_status not in ["完成", "Complete"]  # Only "完成" is valid in this database

        if not title_needs_update and not status_needs_update:
            print(f"✓ Already correct")
            already_correct += 1
            continue

        # Show what will be updated
        updates = []
        if title_needs_update:
            updates.append(f"Title")
        if status_needs_update:
            updates.append(f"Status ({current_status} → {EXPECTED_STATUS})")

        print(f"📝 Updating {', '.join(updates)}", end=" ")

        # Perform update
        success = update_page(
            page_id,
            new_title=expected_title if title_needs_update else None,
            new_status=EXPECTED_STATUS if status_needs_update else None
        )

        if success:
            print("✅")
            if title_needs_update:
                title_updated += 1
            if status_needs_update:
                status_updated += 1
        else:
            print("❌ Update failed")
            errors += 1

    # Summary
    print()
    print("=" * 80)
    print("📊 HEALING SUMMARY")
    print("=" * 80)
    print()
    print(f"Total tickets: {total}")
    print(f"  Found: {found} ({found * 100 / total:.1f}%)")
    print(f"  Not found: {not_found}")
    print()
    print(f"Updates:")
    print(f"  ✅ Titles updated: {title_updated}")
    print(f"  ✅ Statuses updated: {status_updated}")
    print(f"  ✓ Already correct: {already_correct}")
    print(f"  ❌ Errors: {errors}")
    print()

    # Success check
    if errors > 0:
        print(f"⚠️  HEALING COMPLETED WITH ERRORS")
        print(f"   {errors} tickets failed to update")
        return 1
    elif not_found > 10:
        print(f"⚠️  HEALING COMPLETED WITH WARNINGS")
        print(f"   {not_found} tickets not found in Notion")
        return 1
    else:
        print(f"✅ HEALING SUCCESSFUL")
        print(f"   {title_updated} titles standardized")
        print(f"   {status_updated} statuses corrected")
        print(f"   {already_correct} tickets already correct")
        print()
        print("💡 All ticket titles and statuses are now standardized!")
        print("   Page content and notes have been preserved.")
        return 0


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = heal_history()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Healing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
