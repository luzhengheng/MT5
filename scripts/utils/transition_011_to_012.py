import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DB_ID") # Target: Issues Database

# Validate required environment variables (Gemini's recommendation)
if not NOTION_TOKEN:
    print("❌ ERROR: NOTION_TOKEN environment variable is not set")
    print("   Please set it in .env file or export it")
    sys.exit(1)

if not DATABASE_ID:
    print("❌ ERROR: NOTION_DB_ID environment variable is not set")
    print("   Please set it in .env file or export it")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def query_active_issues(keyword="#011"):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Task Name", "rich_text": {"contains": keyword}},
                {"property": "Status", "select": {"does_not_equal": "Done"}}
            ]
        }
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        return response.json().get("results", [])
    except Exception as e:
        print(f"Error querying Notion: {e}")
        return []

def close_issue(page_id, title):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {"properties": {"Status": {"select": {"name": "Done"}}}}
    try:
        requests.patch(url, headers=HEADERS, json=data)
        print(f"✅ Archived Old Issue: {title}")
    except Exception as e:
        print(f"❌ Failed to archive {title}: {e}")

def create_issue(title, priority, tags):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Task Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Not Started"}},
            "Priority": {"select": {"name": priority}},
            "Tags": {"multi_select": [{"name": t} for t in tags]}
        }
    }
    try:
        requests.post(url, headers=HEADERS, json=data)
        print(f"🚀 Created New Issue: {title}")
    except Exception as e:
        print(f"❌ Failed to create {title}: {e}")

def main():
    print(">>> Starting Transition Protocol: #011 -> #012")

    # 1. Cleanup #011
    old_items = query_active_issues("#011")
    if old_items:
        print(f"Found {len(old_items)} active #011 tasks. Archiving...")
        for page in old_items:
            # Safe title extraction
            if page["properties"]["Task Name"]["title"]:
                title = page["properties"]["Task Name"]["title"][0]["plain_text"]
                close_issue(page["id"], title)
    else:
        print("No active #011 tasks found.")

    # 2. Initialize #012
    new_tasks = [
        ("#012.1 [Infra] Implement MT5 ZMQ Async Connection", "P0", ["MT5", "ZMQ", "Infra"]),
        ("#012.2 [Core] Order Executor & Idempotency", "P0", ["Trade", "Core"]),
        ("#012.3 [Risk] Live Risk Guard (KellySizer)", "P0", ["Risk", "Kelly"]),
        ("#012.4 [Integration] Live Trading Loop & CLI", "P1", ["Main", "CLI"])
    ]

    print("Initializing #012 Series...")
    for title, prio, tags in new_tasks:
        create_issue(title, prio, tags)

    print("<<< Transition Complete.")

if __name__ == "__main__":
    main()
