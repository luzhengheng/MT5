#!/usr/bin/env python3
"""
Task #029: Precision Notion State Synchronization
==================================================

Batch-update Work Orders #001 through #027 to "Done" status in Notion.
Ensure Work Order #028 remains untouched (should be "Not Started").

Protocol: v2.0 (Precision State Sync)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from notion_client import Client
except ImportError:
    print("❌ FATAL: notion_client not installed")
    print("   Run: pip install notion-client")
    sys.exit(1)


# ============================================================================
# Configuration
# ============================================================================

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DB_ID")

if not NOTION_TOKEN or not NOTION_DB_ID:
    print("❌ FATAL: Missing Notion credentials")
    print("   Export: NOTION_TOKEN and NOTION_DB_ID")
    sys.exit(1)

# Target range: #001 to #027 (inclusive)
START_TICKET = 1
END_TICKET = 27

# Target status
TARGET_STATUS = "Done"  # or "已完成" depending on your Notion setup


# ============================================================================
# Notion Client
# ============================================================================

notion = Client(auth=NOTION_TOKEN)


# ============================================================================
# Helper Functions
# ============================================================================

def find_ticket_by_id(ticket_id: int):
    """
    Find a Notion page by ticket ID (e.g., #001, #027).

    Args:
        ticket_id: Ticket number (1-27)

    Returns:
        Page object or None if not found
    """
    # Format as #XXX (e.g., #001, #027)
    ticket_name = f"#{ticket_id:03d}"

    try:
        # Query the database
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={
                "property": "Name",
                "title": {
                    "contains": ticket_name
                }
            }
        )

        if results.get("results"):
            # Return first match (should be unique)
            return results["results"][0]
        else:
            return None

    except Exception as e:
        print(f"  ⚠️  Error querying ticket {ticket_name}: {e}")
        return None


def get_page_status(page):
    """
    Get the current status of a Notion page.

    Args:
        page: Notion page object

    Returns:
        Status string or None
    """
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


def update_page_status(page_id: str, status: str):
    """
    Update the status of a Notion page.

    Args:
        page_id: Notion page ID
        status: Target status (e.g., "Done")

    Returns:
        True if successful, False otherwise
    """
    try:
        # Try both "Status" and "状态" property names
        for status_key in ["Status", "状态"]:
            try:
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        status_key: {
                            "status": {
                                "name": status
                            }
                        }
                    }
                )
                return True
            except:
                # Try select type if status type fails
                try:
                    notion.pages.update(
                        page_id=page_id,
                        properties={
                            status_key: {
                                "select": {
                                    "name": status
                                }
                            }
                        }
                    )
                    return True
                except:
                    continue

        return False

    except Exception as e:
        print(f"  ⚠️  Error updating status: {e}")
        return False


# ============================================================================
# Main Sync Logic
# ============================================================================

def sync_completed_tickets():
    """Sync tickets #001-#027 to 'Done' status."""
    print("=" * 80)
    print("🔄 PRECISION NOTION STATE SYNC")
    print("=" * 80)
    print()
    print(f"Target Range: #{START_TICKET:03d} to #{END_TICKET:03d}")
    print(f"Target Status: {TARGET_STATUS}")
    print(f"Database ID: {NOTION_DB_ID[:8]}...")
    print()

    # Statistics
    total = END_TICKET - START_TICKET + 1
    found = 0
    updated = 0
    already_done = 0
    not_found = 0
    errors = 0

    print(f"Processing {total} tickets...")
    print("-" * 80)
    print()

    for ticket_id in range(START_TICKET, END_TICKET + 1):
        ticket_name = f"#{ticket_id:03d}"
        print(f"[{ticket_id}/{END_TICKET}] {ticket_name}", end=" ")

        # Find the ticket
        page = find_ticket_by_id(ticket_id)

        if not page:
            print(f"❌ NOT FOUND")
            not_found += 1
            continue

        found += 1
        page_id = page["id"]

        # Get current status
        current_status = get_page_status(page)

        if current_status is None:
            print(f"⚠️  Cannot read status")
            errors += 1
            continue

        # Check if already done
        if current_status in ["Done", "已完成", "Completed", "完成"]:
            print(f"✓ Already {current_status}")
            already_done += 1
            continue

        # Update to Done
        print(f"📝 {current_status} → {TARGET_STATUS}", end=" ")

        if update_page_status(page_id, TARGET_STATUS):
            print("✅")
            updated += 1
        else:
            print("❌ Update failed")
            errors += 1

    # Summary
    print()
    print("=" * 80)
    print("📊 SYNC SUMMARY")
    print("=" * 80)
    print()
    print(f"Total tickets: {total}")
    print(f"  Found: {found} ({found * 100 / total:.1f}%)")
    print(f"  Not found: {not_found}")
    print()
    print(f"Status updates:")
    print(f"  ✅ Updated: {updated}")
    print(f"  ✓ Already done: {already_done}")
    print(f"  ❌ Errors: {errors}")
    print()

    # Success check
    if errors > 0:
        print(f"⚠️  SYNC COMPLETED WITH ERRORS")
        print(f"   {errors} tickets failed to update")
        return 1
    elif not_found > 10:
        print(f"⚠️  SYNC COMPLETED WITH WARNINGS")
        print(f"   {not_found} tickets not found in Notion")
        return 1
    else:
        print(f"✅ SYNC SUCCESSFUL")
        print(f"   All found tickets ({found}) are now marked as {TARGET_STATUS}")
        return 0


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = sync_completed_tickets()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
