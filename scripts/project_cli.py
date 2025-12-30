#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS Project CLI Tool v1.0
==============================
Unified command-line interface for automated project workflows.

Commands:
  start <task_name>  - Create new Notion ticket and start development
  finish             - Complete task (bridge + Notion update + GitHub push)
  status             - Show current project status
  help               - Display this message

Examples:
  python3 scripts/project_cli.py start "Order Placement Service"
  python3 scripts/project_cli.py finish
  python3 scripts/project_cli.py status
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/opt/mt5-crs")

NOTION_API_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log(msg, level="INFO"):
    """Print colored log message"""
    colors = {
        "SUCCESS": GREEN,
        "ERROR": RED,
        "WARN": YELLOW,
        "INFO": CYAN,
        "PHASE": BLUE
    }
    prefix = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARN": "⚠️",
        "INFO": "ℹ️",
        "PHASE": "🔹"
    }
    color = colors.get(level, RESET)
    symbol = prefix.get(level, "")
    print(f"{color}{symbol} {msg}{RESET}")

def get_next_ticket_number():
    """Query Notion to find the next available ticket number"""
    log("Fetching latest ticket number from Notion...", "PHASE")

    url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}/query"

    try:
        response = requests.post(url, headers=HEADERS, json={})

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            # Extract ticket numbers from all results
            ticket_numbers = []
            for item in results:
                title = item.get('properties', {}).get('标题', {}).get('title', [])
                if title:
                    title_text = title[0]['text']['content']
                    # Extract number from "#NNN" format
                    match = re.search(r'#(\d+)', title_text)
                    if match:
                        ticket_numbers.append(int(match.group(1)))

            if ticket_numbers:
                next_num = max(ticket_numbers) + 1
            else:
                next_num = 15  # Default if no tickets found

            log(f"Next ticket number: #{next_num:03d}", "INFO")
            return next_num
        else:
            log(f"Failed to query database: {response.status_code}", "ERROR")
            return None

    except Exception as e:
        log(f"Exception: {str(e)}", "ERROR")
        return None

def create_notion_ticket(ticket_num, task_name):
    """Create new ticket in Notion"""
    log(f"Creating Ticket #{ticket_num:03d}: {task_name}", "PHASE")

    url = f"{NOTION_API_URL}/pages"

    ticket_title = f"#{ticket_num:03d} {task_name}"

    payload = {
        "parent": {
            "database_id": NOTION_ISSUES_DB_ID
        },
        "properties": {
            "标题": {
                "title": [{"text": {"content": ticket_title}}]
            },
            "状态": {
                "status": {"name": "未开始"}
            },
            "类型": {
                "select": {"name": "Feature"}
            }
        }
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            data = response.json()
            page_id = data.get('id')
            page_url = data.get('url')
            notion_link = f"https://www.notion.so/{page_id.replace('-', '')}"

            log(f"✅ Ticket created successfully!", "SUCCESS")
            print(f"\n{CYAN}Ticket Details:{RESET}")
            print(f"  ID: #{ticket_num:03d}")
            print(f"  Title: {task_name}")
            print(f"  Status: 未开始 (Not Started)")
            print(f"  Notion URL: {notion_link}")
            print()

            return page_id
        else:
            log(f"Failed to create ticket: {response.status_code}", "ERROR")
            print(f"  {response.text[:300]}")
            return None

    except Exception as e:
        log(f"Exception: {str(e)}", "ERROR")
        return None

def run_code_review():
    """Execute gemini_review_bridge.py with visible output"""
    print("=" * 80)
    log("Running External AI Review (gemini_review_bridge.py)...", "PHASE")
    print("=" * 80)
    print()

    try:
        # Run with output visible to user (no capture)
        result = subprocess.run(
            ["python3", os.path.join(PROJECT_ROOT, "gemini_review_bridge.py")],
            cwd=PROJECT_ROOT,
            timeout=120
        )

        print()
        print("=" * 80)
        if result.returncode == 0:
            log("✅ AI REVIEW PASSED - Task can proceed!", "SUCCESS")
            print("=" * 80)
            print()
            return True
        else:
            log("❌ AI REVIEW FAILED - Fix issues before proceeding!", "ERROR")
            print("=" * 80)
            print()
            log("The AI review must pass before the task can be completed.", "ERROR")
            log("Fix the identified issues and run 'finish' again.", "ERROR")
            return False

    except subprocess.TimeoutExpired:
        print()
        print("=" * 80)
        log("⏱️  AI review timeout (>120s)", "ERROR")
        print("=" * 80)
        return False
    except Exception as e:
        print()
        print("=" * 80)
        log(f"Exception during AI review: {str(e)}", "ERROR")
        print("=" * 80)
        return False

def push_to_github():
    """Push code to GitHub"""
    log("Pushing code to GitHub...", "PHASE")

    try:
        # git push origin main
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )

        if result.returncode == 0:
            log("✅ Code pushed to GitHub!", "SUCCESS")
            return True
        else:
            log("❌ Git push failed!", "ERROR")
            print(f"  {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        log("Git push timeout", "ERROR")
        return False
    except Exception as e:
        log(f"Exception: {str(e)}", "ERROR")
        return False

def update_notion_status_done(page_id):
    """Update Notion ticket status to Done"""
    log("Updating Notion status to Done...", "PHASE")

    url = f"{NOTION_API_URL}/pages/{page_id}"

    payload = {
        "properties": {
            "状态": {
                "status": {"name": "完成"}
            }
        }
    }

    try:
        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            log("✅ Notion status updated to Done!", "SUCCESS")
            return True
        else:
            log(f"Failed to update status: {response.status_code}", "ERROR")
            return False

    except Exception as e:
        log(f"Exception: {str(e)}", "ERROR")
        return False

def append_release_summary(page_id):
    """Append release summary to Notion page"""
    log("Appending release summary to Notion page...", "PHASE")

    url = f"{NOTION_API_URL}/blocks/{page_id}/children"

    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📋 Release Summary"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "Task completed and merged to main branch"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]
            }
        }
    ]

    payload = {"children": blocks}

    try:
        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            log("✅ Release summary appended!", "SUCCESS")
            return True
        else:
            log(f"Failed to append summary: {response.status_code}", "WARN")
            return False

    except Exception as e:
        log(f"Exception: {str(e)}", "WARN")
        return False

def get_project_status():
    """Get current project status"""
    log("Fetching project status...", "PHASE")

    url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}/query"

    try:
        response = requests.post(url, headers=HEADERS, json={})

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            print(f"\n{CYAN}Project Status:{RESET}")
            print(f"Total Tickets: {len(results)}")
            print()

            # Count by status
            status_counts = {}
            for item in results:
                status = item.get('properties', {}).get('状态', {}).get('status', {}).get('name', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            print("Breakdown by Status:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")

            print()
            print("Recent Tickets:")
            for i, item in enumerate(results[:5]):
                title = item.get('properties', {}).get('标题', {}).get('title', [])
                status = item.get('properties', {}).get('状态', {}).get('status', {}).get('name', 'Unknown')
                if title:
                    title_text = title[0]['text']['content']
                    print(f"  {i+1}. {title_text} [{status}]")

            print()

        else:
            log(f"Failed to fetch status: {response.status_code}", "ERROR")

    except Exception as e:
        log(f"Exception: {str(e)}", "ERROR")

def show_help():
    """Display help message"""
    help_text = f"""
{CYAN}╔════════════════════════════════════════════════════════════════════════════╗{RESET}
{CYAN}║                    MT5-CRS Project CLI Tool v1.0                           ║{RESET}
{CYAN}║                   One-Click Workflow Automation                            ║{RESET}
{CYAN}╚════════════════════════════════════════════════════════════════════════════╝{RESET}

{CYAN}USAGE:{RESET}
  python3 scripts/project_cli.py <command> [options]

{CYAN}COMMANDS:{RESET}

  {GREEN}start <task_name> [--plan <file>]{RESET}
    Create a new ticket and start development

    • Auto-generates next ticket number (e.g., #015)
    • Creates ticket in Notion database
    • Sets status to "未开始" (Not Started)
    • Displays ticket URL for access
    • Optionally injects implementation plan from file

    Examples:
      python3 scripts/project_cli.py start "Order Placement Service"
      python3 scripts/project_cli.py start "API Refactor" --plan plan.md

  {GREEN}finish{RESET}
    Complete current task and sync everything

    • Runs code review (gemini_review_bridge.py v3.3)
    • Updates Notion status to "完成" (Done) on success
    • Pushes code to GitHub (main branch)
    • Appends release summary to Notion page

    Example:
      python3 scripts/project_cli.py finish

  {GREEN}status{RESET}
    Show current project status

    • Displays total ticket count
    • Shows tickets grouped by status
    • Lists 5 most recent tickets

    Example:
      python3 scripts/project_cli.py status

  {GREEN}help / --help / -h{RESET}
    Display this help message

{CYAN}OPTIONS:{RESET}
  --help, -h        Show this help message
  --verbose, -v     Enable verbose output (future)
  --dry-run         Simulate without making changes (future)

{CYAN}ENVIRONMENT VARIABLES:{RESET}
  NOTION_TOKEN          - Notion API token (required)
  NOTION_ISSUES_DB_ID   - Notion database ID (required)
  PROJECT_ROOT          - Project root directory (default: /opt/mt5-crs)

{CYAN}WORKFLOWS:{RESET}

  {YELLOW}Typical Development Cycle:{RESET}
    1. python3 scripts/project_cli.py start "Feature Name"
       → Creates #015 ticket in Notion
    2. Implement code (reference #015 in commits)
    3. python3 scripts/project_cli.py finish
       → Runs code review, syncs Notion, pushes GitHub

  {YELLOW}Check Progress:{RESET}
    python3 scripts/project_cli.py status
    → See all tickets and their statuses

{CYAN}FEATURES:{RESET}
  ✅ Auto-generates next ticket number
  ✅ Notion integration (create/update/append)
  ✅ Code review automation (gemini_review_bridge.py v3.3)
  ✅ GitHub push automation
  ✅ One-click finish (review + Notion + Git)
  ✅ Project status dashboard
  ✅ Colored output and progress indication

{CYAN}INTEGRATION WITH:{RESET}
  • Notion API (database + page management)
  • Gemini Review Bridge v3.3 (AI code review)
  • Git / GitHub (code sync)
  • Environment variables (.env)

{CYAN}VERSION:{RESET}
  1.0 (2025-12-24)

{CYAN}AUTHOR:{RESET}
  MT5-CRS Toolsmith

{CYAN}DOCUMENTATION:{RESET}
  For more details, see scripts/project_cli.py source code

────────────────────────────────────────────────────────────────────────────────

{GREEN}Ready to automate your workflow! 🚀{RESET}

"""
    print(help_text)

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    # Help commands
    if command in ["help", "--help", "-h"]:
        show_help()
        sys.exit(0)

    # Start command
    elif command == "start":
        if len(sys.argv) < 3:
            log("Error: task_name required", "ERROR")
            print("Usage: python3 scripts/project_cli.py start <task_name> [--plan <file>]")
            sys.exit(1)

        # Parse arguments
        task_name_parts = []
        plan_file = None

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--plan" and i + 1 < len(sys.argv):
                plan_file = sys.argv[i + 1]
                i += 2
            else:
                task_name_parts.append(sys.argv[i])
                i += 1

        task_name = " ".join(task_name_parts)

        print()
        print("=" * 80)
        print("🚀 STARTING NEW TASK")
        print("=" * 80)
        print()

        # Get next ticket number
        ticket_num = get_next_ticket_number()
        if not ticket_num:
            sys.exit(1)

        # Create Notion ticket
        page_id = create_notion_ticket(ticket_num, task_name)
        if not page_id:
            sys.exit(1)

        # If plan file provided, inject it into the Notion page
        if plan_file:
            log(f"Injecting plan from: {plan_file}", "PHASE")
            try:
                # Import notion_updater utility
                sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
                from utils.notion_updater import update_page_with_plan

                # Read plan file
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plan_content = f.read()

                # Update Notion page
                if update_page_with_plan(page_id, plan_content, prepend_callout=True):
                    log("✅ Plan injected successfully!", "SUCCESS")
                else:
                    log("⚠️  Failed to inject plan (continuing anyway)", "WARN")
            except FileNotFoundError:
                log(f"⚠️  Plan file not found: {plan_file}", "WARN")
            except Exception as e:
                log(f"⚠️  Error injecting plan: {str(e)}", "WARN")
        else:
            # Warn if no plan provided
            log("⚠️  Starting task without a spec/plan", "WARN")
            print(f"{YELLOW}   Consider documenting implementation plan in Notion{RESET}")
            print(f"{YELLOW}   or run with: --plan <file>{RESET}")

        print("=" * 80)
        log(f"✅ Task #{ticket_num:03d} is ready to start!", "SUCCESS")
        print("=" * 80)
        print()
        print(f"{GREEN}Next steps:{RESET}")
        print(f"  1. Implement your code")
        print(f"  2. Reference #{ticket_num:03d} in your commit messages")
        print(f"  3. Run: python3 scripts/project_cli.py finish")
        print()

    # Finish command
    elif command == "finish":
        print()
        print("=" * 80)
        print("🎯 FINISHING TASK")
        print("=" * 80)
        print()

        # Step 1: Code review
        if not run_code_review():
            log("Task finish aborted - code review failed", "ERROR")
            sys.exit(1)

        print()

        # Step 2: Get current ticket from git log
        log("Fetching latest ticket from git history...", "PHASE")
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%B"],
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            commit_msg = result.stdout
            match = re.search(r'#(\d+)', commit_msg)
            ticket_num = int(match.group(1)) if match else None

            if ticket_num:
                log(f"Found ticket #{ticket_num:03d} in git history", "INFO")
            else:
                log("Could not find ticket number in recent commits", "WARN")

        except Exception as e:
            log(f"Could not fetch git info: {str(e)}", "WARN")
            ticket_num = None

        # Step 3: Push to GitHub
        print()
        if not push_to_github():
            log("GitHub push failed - continuing with Notion updates", "WARN")
        print()

        # Step 4: Update Notion (optional if we have ticket)
        if ticket_num:
            # Try to find the Notion page ID
            url = f"{NOTION_API_URL}/databases/{NOTION_ISSUES_DB_ID}/query"
            payload = {
                "filter": {
                    "property": "标题",
                    "title": {"contains": f"{ticket_num:03d}"}
                }
            }

            try:
                response = requests.post(url, headers=HEADERS, json=payload)
                if response.status_code == 200:
                    results = response.json().get('results', [])
                    if results:
                        page_id = results[0].get('id')

                        update_notion_status_done(page_id)
                        print()
                        append_release_summary(page_id)
                        print()

            except Exception as e:
                log(f"Could not update Notion: {str(e)}", "WARN")

        print("=" * 80)
        log("✅ Task completed successfully!", "SUCCESS")
        print("=" * 80)
        print()

    # Status command
    elif command == "status":
        print()
        print("=" * 80)
        print("📊 PROJECT STATUS")
        print("=" * 80)
        print()

        get_project_status()

        print("=" * 80)
        print()

    else:
        log(f"Unknown command: {command}", "ERROR")
        print("\nTry: python3 scripts/project_cli.py --help")
        sys.exit(1)

if __name__ == "__main__":
    main()
