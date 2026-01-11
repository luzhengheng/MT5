#!/usr/bin/env python3
"""
Task #012.00: Notion Database Schema Debugger
==============================================

Comprehensive schema inspector that prints:
1. All property names and types
2. Sample query attempts for different ticket formats
3. Full JSON schema dump
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DB_ID")

if not NOTION_TOKEN or not DATABASE_ID:
    print("❌ Missing NOTION_TOKEN or NOTION_DB_ID in environment")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

NOTION_API_URL = "https://api.notion.com/v1"


def print_header(title):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def get_database_schema():
    """Retrieve and display full database schema"""
    print_header("STEP 1: Database Schema Inspection")

    url = f"{NOTION_API_URL}/databases/{DATABASE_ID}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            db_info = response.json()
            properties = db_info.get("properties", {})

            print("✅ Database retrieved successfully")
            print(f"Database Title: {db_info.get('title', [{}])[0].get('plain_text', 'N/A')}")
            print(f"Total Properties: {len(properties)}\n")

            print("📋 Property List (Name → Type):")
            print("-" * 80)

            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get("type", "unknown")
                print(f"  • {prop_name:<30} → {prop_type}")

            print("\n📄 Full Schema JSON:")
            print("-" * 80)
            print(json.dumps(properties, indent=2, ensure_ascii=False))

            return properties

        else:
            print(f"❌ Failed to retrieve database: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_query(filter_config, description):
    """Test a specific query filter"""
    url = f"{NOTION_API_URL}/databases/{DATABASE_ID}/query"
    payload = {"filter": filter_config}

    print(f"\n🔍 Testing: {description}")
    print(f"Filter: {json.dumps(filter_config, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)

        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"✅ Query succeeded - Found {len(results)} result(s)")

            if results:
                # Show first result's title
                first = results[0]
                title_prop = first.get("properties", {}).get("标题", {})
                if title_prop.get("title"):
                    title_text = title_prop["title"][0]["text"]["content"]
                    print(f"   First result: {title_text}")

            return True

        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_ticket_queries():
    """Test various ticket query formats"""
    print_header("STEP 2: Test Ticket Queries")

    # Test 1: Query by title containing "#063"
    test_query(
        {
            "property": "标题",
            "title": {"contains": "#063"}
        },
        'Title contains "#063"'
    )

    # Test 2: Query by title containing "063" (no #)
    test_query(
        {
            "property": "标题",
            "title": {"contains": "063"}
        },
        'Title contains "063" (without #)'
    )

    # Test 3: Query by title equals "#063"
    test_query(
        {
            "property": "标题",
            "title": {"equals": "#063"}
        },
        'Title equals "#063"'
    )

    # Test 4: Query by title starts with "#"
    test_query(
        {
            "property": "标题",
            "title": {"starts_with": "#"}
        },
        'Title starts with "#" (should return all tickets)'
    )


def query_all_tickets():
    """Query all tickets to see their structure"""
    print_header("STEP 3: Sample Ticket Data")

    url = f"{NOTION_API_URL}/databases/{DATABASE_ID}/query"

    try:
        response = requests.post(url, headers=HEADERS, json={}, timeout=10)

        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"✅ Retrieved {len(results)} total tickets\n")

            # Show first 3 tickets
            print("📝 First 3 Tickets:")
            print("-" * 80)

            for i, ticket in enumerate(results[:3], 1):
                props = ticket.get("properties", {})

                # Extract title
                title_prop = props.get("标题", {})
                title = "N/A"
                if title_prop.get("title"):
                    title = title_prop["title"][0]["text"]["content"]

                # Extract status
                status_prop = props.get("状态", {})
                status = status_prop.get("status", {}).get("name", "N/A")

                # Extract date
                date_prop = props.get("日期", {})
                date = date_prop.get("date", {})
                date_str = "N/A"
                if date:
                    date_str = date.get("start", "N/A")

                print(f"\n{i}. Title: {title}")
                print(f"   Status: {status}")
                print(f"   Date: {date_str}")
                print(f"   Page ID: {ticket.get('id')}")

            return results

        else:
            print(f"❌ Failed to query tickets: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_status_update():
    """Test updating a ticket status"""
    print_header("STEP 4: Test Status Update (Dry Run)")

    # First, find ticket #066 (current task)
    url = f"{NOTION_API_URL}/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "标题",
            "title": {"contains": "066"}
        }
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)

        if response.status_code == 200:
            results = response.json().get("results", [])

            if results:
                page_id = results[0]["id"]
                title_prop = results[0].get("properties", {}).get("标题", {})
                title = title_prop["title"][0]["text"]["content"]

                print(f"✅ Found ticket: {title}")
                print(f"   Page ID: {page_id}")
                print(f"\n💡 To update status to '进行中', use:")
                print(f'   PATCH /v1/pages/{page_id}')
                print(f'   {{"properties": {{"状态": {{"status": {{"name": "进行中"}}}}}}}}')

                # Show current status
                current_status = results[0].get("properties", {}).get("状态", {}).get("status", {}).get("name", "N/A")
                print(f"\n   Current status: {current_status}")

            else:
                print("❌ Ticket #066 not found")

        else:
            print(f"❌ Query failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all diagnostic tests"""
    print(f"\n{'#' * 80}")
    print(f"#  TASK #012.00: Notion Database Schema Debugger")
    print(f"#  Database ID: {DATABASE_ID[:10]}...")
    print(f"{'#' * 80}")

    # Step 1: Get schema
    properties = get_database_schema()

    if not properties:
        print("\n❌ Cannot proceed without database schema")
        return 1

    # Step 2: Test queries
    test_ticket_queries()

    # Step 3: Sample data
    query_all_tickets()

    # Step 4: Test status update
    test_status_update()

    print_header("DIAGNOSIS COMPLETE")
    print("✅ All schema information collected")
    print("\nNext Steps:")
    print("1. Review property names (Chinese: 标题, 状态, etc.)")
    print("2. Fix project_cli.py to use correct property names")
    print("3. Test status updates with correct schema")

    return 0


if __name__ == "__main__":
    exit(main())
