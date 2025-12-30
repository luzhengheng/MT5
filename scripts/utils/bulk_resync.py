#!/usr/bin/env python3
"""
Task #012.02: Bulk Resync & Repair Notion Tickets
==================================================

Replays Git commit history to repair Notion tickets that were created
but left empty or with incorrect status due to previous 400 errors.

Source of Truth: Git commit log
Target: Notion Issues Database

Usage:
    python3 scripts/utils/bulk_resync.py --dry-run   # Preview changes
    python3 scripts/utils/bulk_resync.py --force     # Execute repairs
"""

import os
import sys
import re
import subprocess
import argparse
from collections import defaultdict
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import requests

# Load environment
load_dotenv()

# Notion API configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Schema mapping (from Task #012.00)
TITLE_FIELD = "标题"
STATUS_FIELD = "状态"
DATE_FIELD = "日期"

# Status mapping
COMMIT_TYPE_TO_STATUS = {
    "feat": "完成",      # Features are complete
    "fix": "完成",       # Fixes are complete
    "docs": "完成",      # Documentation is complete
    "test": "完成",      # Tests are complete
    "refactor": "完成",  # Refactoring is complete
    "chore": "完成",     # Chores are complete
    "perf": "完成",      # Performance is complete
    "style": "完成",     # Style is complete
    "task": "完成",      # Tasks are complete
}

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print formatted section header"""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def get_git_commits() -> List[Dict]:
    """
    Extract all commits from Git history.

    Returns:
        List of commit dictionaries with hash, message, author, date
    """
    print(f"{BLUE}[Step 1]{RESET} Scanning Git commit history...")

    try:
        # Get all commits in format: hash|subject|author|date
        result = subprocess.run(
            ["git", "log", "--all", "--format=%H|%s|%an|%cd", "--date=iso"],
            capture_output=True,
            text=True,
            check=True
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3]
                })

        print(f"   ✅ Found {len(commits)} total commits")
        return commits

    except Exception as e:
        print(f"   {RED}❌ Error scanning Git history: {e}{RESET}")
        return []


def extract_ticket_info(commits: List[Dict]) -> Dict[str, Dict]:
    """
    Extract ticket information from commit messages.

    Args:
        commits: List of commit dictionaries

    Returns:
        Dictionary mapping ticket ID to latest commit info
        {
            "066": {"title": "...", "status": "...", "commit_hash": "...", "date": "..."},
            "040.10": {"title": "...", "status": "...", "commit_hash": "...", "date": "..."}
        }
    """
    print(f"\n{BLUE}[Step 2]{RESET} Extracting ticket information...")

    # Ticket ID patterns
    # Matches: #066, #040.10, #011.23, Task #042, etc.
    ticket_pattern = re.compile(r'#(\d+(?:\.\d+)?)')

    # Commit type pattern
    # Matches: feat(...), fix(...), docs(...), etc.
    type_pattern = re.compile(r'^(feat|fix|docs|test|refactor|chore|perf|style|task)[\(\:]')

    ticket_map = {}

    for commit in commits:
        msg = commit["message"]

        # Extract ticket IDs from commit message
        ticket_ids = ticket_pattern.findall(msg)

        if not ticket_ids:
            continue

        # Determine commit type and status
        type_match = type_pattern.match(msg.lower())
        commit_type = type_match.group(1) if type_match else "chore"
        status = COMMIT_TYPE_TO_STATUS.get(commit_type, "完成")

        # Extract title (use commit message as title)
        title = msg

        # Store info for each ticket ID found in this commit
        for ticket_id in ticket_ids:
            # Use latest commit for each ticket (commits are in reverse chronological order)
            if ticket_id not in ticket_map:
                ticket_map[ticket_id] = {
                    "title": title,
                    "status": status,
                    "commit_hash": commit["hash"][:8],
                    "commit_type": commit_type,
                    "date": commit["date"]
                }

    print(f"   ✅ Found {len(ticket_map)} unique tickets")

    return ticket_map


def query_notion_ticket(ticket_id: str) -> Dict:
    """
    Query Notion for a specific ticket.

    Args:
        ticket_id: Ticket ID (e.g., "066", "040.10")

    Returns:
        Notion page object or None if not found
    """
    url = f"{NOTION_API_URL}/databases/{NOTION_DB_ID}/query"

    # Format ticket ID with # prefix
    search_term = f"#{ticket_id}"

    payload = {
        "filter": {
            "property": TITLE_FIELD,
            "title": {"contains": search_term}
        }
    }

    try:
        response = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=10)

        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0]  # Return first match

        return None

    except Exception as e:
        print(f"      {RED}Query error: {e}{RESET}")
        return None


def update_notion_ticket(page_id: str, title: str, status: str) -> bool:
    """
    Update a Notion ticket with new title and status.

    Args:
        page_id: Notion page ID
        title: New title
        status: New status

    Returns:
        True if successful, False otherwise
    """
    url = f"{NOTION_API_URL}/pages/{page_id}"

    payload = {
        "properties": {
            TITLE_FIELD: {
                "title": [{
                    "text": {"content": title}
                }]
            },
            STATUS_FIELD: {
                "status": {"name": status}
            }
        }
    }

    try:
        response = requests.patch(url, headers=NOTION_HEADERS, json=payload, timeout=10)

        if response.status_code == 200:
            return True
        else:
            print(f"      {RED}Update failed: {response.status_code}{RESET}")
            print(f"      {RED}Response: {response.text[:200]}{RESET}")
            return False

    except Exception as e:
        print(f"      {RED}Update error: {e}{RESET}")
        return False


def repair_tickets(ticket_map: Dict[str, Dict], dry_run: bool = True):
    """
    Repair Notion tickets based on Git history.

    Args:
        ticket_map: Dictionary of ticket ID -> info
        dry_run: If True, only preview changes without updating
    """
    mode = "DRY RUN - Preview Only" if dry_run else "FORCE MODE - Executing Updates"
    print_header(f"Step 3: Repair Tickets ({mode})")

    success_count = 0
    not_found_count = 0
    skipped_count = 0
    error_count = 0

    # Sort ticket IDs for consistent output
    sorted_tickets = sorted(ticket_map.items(), key=lambda x: x[0])

    for ticket_id, info in sorted_tickets:
        print(f"\n{YELLOW}[{ticket_id}]{RESET} #{ticket_id}")

        # Query Notion for this ticket
        page = query_notion_ticket(ticket_id)

        if not page:
            print(f"   {RED}❌ Not found in Notion{RESET}")
            not_found_count += 1
            continue

        # Get current title and status
        page_id = page["id"]
        props = page.get("properties", {})

        current_title_prop = props.get(TITLE_FIELD, {}).get("title", [])
        current_title = current_title_prop[0]["text"]["content"] if current_title_prop else "Untitled"

        current_status = props.get(STATUS_FIELD, {}).get("status", {}).get("name", "Unknown")

        # New values from Git history
        new_title = info["title"]
        new_status = info["status"]

        # Check if update needed
        title_needs_update = current_title != new_title
        status_needs_update = current_status != new_status

        if not title_needs_update and not status_needs_update:
            print(f"   {GREEN}✓ Already correct{RESET}")
            print(f"      Title: {current_title}")
            print(f"      Status: {current_status}")
            skipped_count += 1
            continue

        # Show what will change
        print(f"   {CYAN}Current:{RESET}")
        print(f"      Title: {current_title}")
        print(f"      Status: {current_status}")
        print(f"   {CYAN}New:{RESET}")
        print(f"      Title: {new_title}")
        print(f"      Status: {new_status}")
        print(f"      Commit: {info['commit_hash']} ({info['commit_type']})")

        if dry_run:
            print(f"   {YELLOW}➜ Would update (dry-run){RESET}")
            success_count += 1
        else:
            # Execute update
            if update_notion_ticket(page_id, new_title, new_status):
                print(f"   {GREEN}✅ Updated successfully{RESET}")
                success_count += 1
            else:
                print(f"   {RED}❌ Update failed{RESET}")
                error_count += 1

    # Summary
    print_header("Repair Summary")
    print(f"Total Tickets: {len(ticket_map)}")
    print(f"{GREEN}✅ Processed: {success_count}{RESET}")
    print(f"{YELLOW}⊘ Skipped (already correct): {skipped_count}{RESET}")
    print(f"{RED}❌ Not found: {not_found_count}{RESET}")
    print(f"{RED}❌ Errors: {error_count}{RESET}")

    if dry_run:
        print(f"\n{YELLOW}💡 This was a dry run. Use --force to execute updates.{RESET}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Bulk resync and repair Notion tickets from Git history"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating Notion"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Execute updates to Notion"
    )
    args = parser.parse_args()

    # Validate environment
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print(f"{RED}❌ Missing NOTION_TOKEN or NOTION_DB_ID environment variable{RESET}")
        return 1

    # Determine mode
    if args.force:
        dry_run = False
    elif args.dry_run:
        dry_run = True
    else:
        # Default to dry-run
        print(f"{YELLOW}⚠️  No mode specified. Running in dry-run mode.{RESET}")
        print(f"{YELLOW}   Use --dry-run or --force{RESET}\n")
        dry_run = True

    # Execute repair workflow
    print_header("Task #012.02: Bulk Resync & Repair Notion Tickets")
    print(f"Mode: {'DRY RUN' if dry_run else 'FORCE (EXECUTING)'}")

    # Step 1: Get commits
    commits = get_git_commits()
    if not commits:
        print(f"{RED}❌ No commits found{RESET}")
        return 1

    # Step 2: Extract ticket info
    ticket_map = extract_ticket_info(commits)
    if not ticket_map:
        print(f"{YELLOW}⚠️  No tickets found in commit messages{RESET}")
        return 0

    # Step 3: Repair tickets
    repair_tickets(ticket_map, dry_run=dry_run)

    print_header("Complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
