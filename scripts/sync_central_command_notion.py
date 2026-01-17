#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion API Sync: Central Command Database
Task #099 Post-Completion Update

Updates the Central Command database in Notion with the latest system state
and task progress information from the local markdown document.

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Hub Agent
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")  # Central Command DB ID

# Notion API Headers
NOTION_API_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

NOTION_API_BASE = "https://api.notion.com/v1"


class NotionCentralCommandSync:
    """Sync Central Command markdown to Notion database."""

    def __init__(self):
        self.token = NOTION_TOKEN
        self.db_id = NOTION_DB_ID
        self.headers = NOTION_API_HEADERS

    def read_markdown(self, md_file_path: str) -> dict:
        """Parse the Central Command markdown file."""
        print(f"📖 Reading markdown from: {md_file_path}")

        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract key sections
            data = {
                'timestamp': datetime.now().isoformat(),
                'file_path': md_file_path,
                'raw_content': content,
            }

            # Parse current status
            if "当前状态 (Current Status)" in content:
                status_section = content[content.find("当前状态"):content.find("## 2.")]
                if "系统已完成" in status_section:
                    data['current_status'] = "数据融合完成"
                    data['last_task'] = "Task #099 (Cross-Domain Data Fusion)"
                    print("✅ Current Status: 数据融合完成")

            # Extract completed tasks
            if "已完成任务链" in content:
                tasks = []
                for line in content.split('\n'):
                    if "Task #" in line and "Done" in line:
                        task_num = line.split('Task #')[1].split(' ')[0].split('(')[0]
                        tasks.append(f"Task #{task_num}")
                data['completed_tasks'] = tasks
                print(f"✅ Completed Tasks: {', '.join(tasks)}")

            # Extract next strategy
            if "下一步战略" in content:
                if "Task #100" in content:
                    data['next_goal'] = "Task #100 (Strategy Engine Activation)"
                    print("✅ Next Goal: Task #100")

            # Extract data pipeline status
            pipeline_status = {}
            if "Data Pipeline Status" in content:
                lines = content[content.find("Data Pipeline"):content.find("```")].split('\n')
                for line in lines:
                    if "[x]" in line or "[ ]" in line:
                        status = "Ready" if "[x]" in line else "Pending"
                        if "Cold Data" in line:
                            pipeline_status['cold_data'] = status
                        elif "Features" in line:
                            pipeline_status['features'] = status
                        elif "Sentiment" in line:
                            pipeline_status['sentiment'] = status
                        elif "Fusion" in line:
                            pipeline_status['fusion'] = status
                        elif "Strategy" in line:
                            pipeline_status['strategy'] = status
                data['pipeline_status'] = pipeline_status
                print(f"✅ Pipeline Status: {pipeline_status}")

            return data

        except Exception as e:
            print(f"❌ Failed to read markdown: {e}")
            raise

    def find_or_create_page(self, title: str) -> str:
        """Find existing Central Command page or create new one."""
        print(f"\n🔍 Looking for page: {title}")

        try:
            # Query existing pages
            query_url = f"{NOTION_API_BASE}/databases/{self.db_id}/query"

            filter_obj = {
                "filter": {
                    "property": "标题",
                    "title": {
                        "equals": title
                    }
                }
            }

            response = requests.post(
                query_url,
                headers=self.headers,
                json=filter_obj
            )

            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    page_id = results[0]['id']
                    print(f"✅ Found existing page: {page_id}")
                    return page_id

            # Create new page if not found
            print("📝 Creating new page...")
            create_url = f"{NOTION_API_BASE}/pages"

            new_page = {
                "parent": {"database_id": self.db_id},
                "properties": {
                    "标题": {
                        "title": [{"text": {"content": title}}]
                    },
                    "状态": {
                        "status": {"name": "进行中"}
                    },
                    "日期": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "类型": {
                        "select": {"name": "核心"}
                    },
                    "优先级": {
                        "select": {"name": "P0"}
                    }
                },
                "children": []
            }

            response = requests.post(
                create_url,
                headers=self.headers,
                json=new_page
            )

            if response.status_code == 200:
                page_id = response.json()['id']
                print(f"✅ Created new page: {page_id}")
                return page_id
            else:
                print(f"❌ Failed to create page: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error finding/creating page: {e}")
            raise

    def update_page_content(self, page_id: str, data: dict) -> bool:
        """Update Notion page with markdown data."""
        print(f"\n📤 Updating page: {page_id}")

        try:
            url = f"{NOTION_API_BASE}/pages/{page_id}"

            properties = {
                "状态": {
                    "status": {"name": "完成"}
                },
                "日期": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "类型": {
                    "select": {"name": "核心"}
                },
                "优先级": {
                    "select": {"name": "P0"}
                }
            }

            update_payload = {"properties": properties}

            response = requests.patch(
                url,
                headers=self.headers,
                json=update_payload
            )

            if response.status_code == 200:
                print("✅ Page updated successfully")
                return True
            else:
                print(f"⚠️  Update response: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error updating page: {e}")
            return False

    def sync(self, md_file_path: str) -> bool:
        """Perform complete sync operation."""
        print("=" * 80)
        print("🔄 Starting Notion Central Command Sync (Protocol v4.3)")
        print("=" * 80)

        try:
            # Validate credentials
            if not self.token or not self.db_id:
                print("❌ Missing Notion credentials: NOTION_TOKEN or NOTION_DB_ID")
                return False

            print("✅ Notion credentials found")

            # Read markdown
            data = self.read_markdown(md_file_path)

            # Find or create page
            page_id = self.find_or_create_page("Central Command")
            if not page_id:
                print("❌ Failed to find or create Central Command page")
                return False

            # Update page
            success = self.update_page_content(page_id, data)

            print("\n" + "=" * 80)
            if success:
                print("✅ Sync completed successfully!")
                print(f"   Page ID: {page_id}")
                print(f"   Timestamp: {datetime.now().isoformat()}")
                print("=" * 80)
                return True
            else:
                print("⚠️  Sync completed with warnings")
                print("=" * 80)
                return False

        except Exception as e:
            print(f"\n❌ Sync failed: {e}")
            print("=" * 80)
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync Central Command markdown to Notion"
    )
    parser.add_argument(
        "--md-file",
        default="docs/archive/tasks/[MT5-CRS] Central Command 2e7c88582b4e802e872cc424cf0bf278.md",
        help="Path to Central Command markdown file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without updating"
    )

    args = parser.parse_args()

    # Resolve file path
    md_file = Path(args.md_file)
    if not md_file.is_absolute():
        md_file = Path("/opt/mt5-crs") / md_file

    if not md_file.exists():
        print(f"❌ File not found: {md_file}")
        sys.exit(1)

    # Run sync
    syncer = NotionCentralCommandSync()

    if args.dry_run:
        print("📋 DRY RUN: Reading markdown file...")
        data = syncer.read_markdown(str(md_file))
        print("\n📊 Would sync the following data:")
        for key, value in data.items():
            if key != 'raw_content':
                print(f"  {key}: {value}")
        sys.exit(0)

    success = syncer.sync(str(md_file))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
