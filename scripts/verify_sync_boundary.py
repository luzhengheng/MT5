#!/usr/bin/env python3
"""
Task #029: Notion Sync Boundary Verification
=============================================

Verify that:
1. Ticket #027 is marked as "Done"
2. Ticket #028 is NOT marked as "Done" (should be "Not Started" or similar)

This ensures the sync script respected the boundary correctly.

Protocol: v2.0 (Precision State Sync)
"""

import os
import sys
from pathlib import Path

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

# Boundary tickets
LAST_COMPLETED = 27
FIRST_NOT_STARTED = 28


# ============================================================================
# Notion Client
# ============================================================================

notion = Client(auth=NOTION_TOKEN)


# ============================================================================
# Helper Functions
# ============================================================================

def find_ticket_by_id(ticket_id: int):
    """Find a Notion page by ticket ID."""
    ticket_name = f"#{ticket_id:03d}"

    try:
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
            return results["results"][0]
        else:
            return None

    except Exception as e:
        print(f"  ⚠️  Error querying ticket {ticket_name}: {e}")
        return None


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


def get_page_title(page):
    """Get the title of a Notion page."""
    try:
        properties = page.get("properties", {})
        title_prop = properties.get("Name") or properties.get("名称")

        if title_prop and title_prop.get("type") == "title":
            title_array = title_prop.get("title", [])
            if title_array:
                return title_array[0].get("plain_text", "Untitled")

        return "Untitled"

    except Exception as e:
        print(f"  ⚠️  Error reading title: {e}")
        return "Error reading title"


# ============================================================================
# Verification Logic
# ============================================================================

def verify_boundary():
    """Verify the sync boundary between #027 and #028."""
    print("=" * 80)
    print("🔍 BOUNDARY VERIFICATION")
    print("=" * 80)
    print()
    print(f"Verifying sync boundary:")
    print(f"  Last completed: #{LAST_COMPLETED:03d} (should be Done)")
    print(f"  First not started: #{FIRST_NOT_STARTED:03d} (should NOT be Done)")
    print()
    print("-" * 80)
    print()

    all_passed = True

    # Test 1: Verify #027 is Done
    print(f"Test 1: Verify #{LAST_COMPLETED:03d} is marked as Done")
    print("-" * 80)

    page_027 = find_ticket_by_id(LAST_COMPLETED)

    if not page_027:
        print(f"❌ FAIL: Ticket #{LAST_COMPLETED:03d} not found in Notion")
        all_passed = False
    else:
        title_027 = get_page_title(page_027)
        status_027 = get_page_status(page_027)

        print(f"  Title: {title_027}")
        print(f"  Status: {status_027}")

        if status_027 in ["Done", "已完成", "Completed", "完成"]:
            print(f"  ✅ PASS: Ticket #{LAST_COMPLETED:03d} is correctly marked as '{status_027}'")
        else:
            print(f"  ❌ FAIL: Ticket #{LAST_COMPLETED:03d} has status '{status_027}' (expected Done)")
            all_passed = False

    print()

    # Test 2: Verify #028 is NOT Done
    print(f"Test 2: Verify #{FIRST_NOT_STARTED:03d} is NOT marked as Done")
    print("-" * 80)

    page_028 = find_ticket_by_id(FIRST_NOT_STARTED)

    if not page_028:
        print(f"  ℹ️  Ticket #{FIRST_NOT_STARTED:03d} not found in Notion")
        print(f"  ✅ PASS: No #{FIRST_NOT_STARTED:03d} to check (boundary is safe)")
    else:
        title_028 = get_page_title(page_028)
        status_028 = get_page_status(page_028)

        print(f"  Title: {title_028}")
        print(f"  Status: {status_028}")

        if status_028 in ["Done", "已完成", "Completed", "完成"]:
            print(f"  ❌ FAIL: Ticket #{FIRST_NOT_STARTED:03d} is marked as '{status_028}' (should NOT be Done)")
            all_passed = False
        else:
            print(f"  ✅ PASS: Ticket #{FIRST_NOT_STARTED:03d} has status '{status_028}' (not Done)")

    print()

    # Summary
    print("=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    print()

    if all_passed:
        print("✅ BOUNDARY VERIFIED")
        print()
        print(f"  #{LAST_COMPLETED:03d}: Done ✓")
        print(f"  #{FIRST_NOT_STARTED:03d}: Not Done ✓")
        print()
        print("Sync boundary is correct!")
        return 0
    else:
        print("❌ BOUNDARY VERIFICATION FAILED")
        print()
        print("Please check:")
        print(f"  1. Ticket #{LAST_COMPLETED:03d} should be marked as Done")
        print(f"  2. Ticket #{FIRST_NOT_STARTED:03d} should NOT be marked as Done")
        print()
        print("Run ops_sync_completed_tickets.py to fix the boundary.")
        return 1


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        exit_code = verify_boundary()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
