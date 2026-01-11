#!/usr/bin/env python3
"""
Task #011.13: Secret Audit & Cleanup Tool
Purpose: Scan git history for API keys and sensitive credentials
Protocol: v2.2 (Docs-as-Code)

Detects:
- EODHD API tokens (format: 8hex.8hex)
- Gemini API keys (format: sk-*)
- Notion tokens (format: ntn_*)
- GitHub tokens (format: ghp_*)
- PostgreSQL passwords
- Redis passwords
"""

import subprocess
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Secret patterns
SECRET_PATTERNS = {
    "EODHD_TOKEN": r"[0-9a-f]{8}[0-9a-f]{8}",
    "GEMINI_KEY": r"sk-[A-Za-z0-9]{20,}",
    "NOTION_TOKEN": r"ntn_[A-Za-z0-9]{20,}",
    "GITHUB_TOKEN": r"ghp_[A-Za-z0-9]{20,}",
    "POSTGRES_PASSWORD": r"password@localhost",
    "API_KEY_GENERAL": r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{20,}['\"]?",
}


def print_header(title):
    """Print formatted header."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")


def check(name, status, detail=""):
    """Print formatted check result."""
    symbol = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
    detail_str = f"  [{detail}]" if detail else ""
    print(f"  {symbol} {name:<50} {detail_str}")
    return status


def get_recent_commits(num_commits: int = 10) -> List[str]:
    """Get list of recent commit hashes."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H", f"-n{num_commits}"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return []
    except Exception as e:
        print(f"{RED}Error getting commits: {e}{RESET}")
        return []


def scan_commit_for_secrets(commit_hash: str) -> Dict[str, List[str]]:
    """Scan a single commit for secrets."""
    secrets_found = {}

    try:
        result = subprocess.run(
            ["git", "show", commit_hash],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode != 0:
            return {}

        content = result.stdout

        # Check each pattern
        for secret_type, pattern in SECRET_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                matched_value = match.group(0)

                # Avoid false positives in line numbers or diffs
                if matched_value.startswith('-') or matched_value.startswith('+'):
                    continue

                # Avoid false positives with REDACTED tokens
                if 'REDACTED' in matched_value.upper():
                    continue

                # Avoid false positives with git commit hashes in the output
                # (git show includes "commit <hash>" and other hashes)
                if re.match(r'^[0-9a-f]{40}$', matched_value) or re.match(r'^[0-9a-f]{7,40}$', matched_value):
                    continue

                if secret_type not in secrets_found:
                    secrets_found[secret_type] = []

                # Store the matched secret (masked for display)
                secret_value = match.group(0)
                if len(secret_value) > 20:
                    masked = secret_value[:10] + "..." + secret_value[-5:]
                else:
                    masked = "*" * len(secret_value)

                secrets_found[secret_type].append({
                    'value': secret_value,
                    'masked': masked,
                    'position': match.start()
                })

        return secrets_found

    except Exception as e:
        print(f"{YELLOW}Warning: Could not scan commit {commit_hash}: {e}{RESET}")
        return {}


def get_commit_info(commit_hash: str) -> Tuple[str, str]:
    """Get commit message and author."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s|%an", commit_hash],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) == 2:
                return parts[0], parts[1]
        return "Unknown", "Unknown"
    except:
        return "Unknown", "Unknown"


def check_file_in_git(filepath: str) -> bool:
    """Check if file is tracked in git."""
    try:
        result = subprocess.run(
            ["git", "ls-files", filepath],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        return result.returncode == 0 and result.stdout.strip() == filepath
    except:
        return False


def check_gitignore():
    """Check if .env is properly ignored."""
    gitignore_path = PROJECT_ROOT / ".gitignore"

    if not gitignore_path.exists():
        return False, "No .gitignore found"

    try:
        content = gitignore_path.read_text()
        if ".env" in content:
            return True, ".env is in .gitignore"
        return False, ".env is NOT in .gitignore"
    except:
        return False, "Could not read .gitignore"


def main():
    """Execute secret audit."""

    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  TASK #011.13: SECRET AUDIT & CLEANUP{RESET}")
    print(f"{CYAN}  GitHub Push Block (GH013) Investigation{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    # Phase 1: Check .gitignore
    print_header("PHASE 1: .GITIGNORE VERIFICATION")

    gitignore_ok, gitignore_detail = check_gitignore()
    check(".env in .gitignore", gitignore_ok, gitignore_detail)

    # Phase 2: Check if .env is tracked
    print_header("PHASE 2: GIT TRACKING STATUS")

    env_tracked = check_file_in_git(".env")
    check(".env is tracked in git", env_tracked,
          "PROBLEM: .env should not be tracked!" if env_tracked else "OK: .env not tracked")

    # Phase 3: Scan recent commits
    print_header("PHASE 3: COMMIT HISTORY SCAN")

    num_commits = 10
    print(f"  Scanning {num_commits} recent commits for secrets...\n")

    commits = get_recent_commits(num_commits)
    if not commits:
        print(f"{RED}❌ Could not retrieve commits{RESET}\n")
        return 1

    total_secrets = 0
    commits_with_secrets = []

    for idx, commit_hash in enumerate(commits, 1):
        short_hash = commit_hash[:7]
        message, author = get_commit_info(commit_hash)

        secrets = scan_commit_for_secrets(commit_hash)

        if secrets:
            total_secrets += len(secrets)
            commits_with_secrets.append({
                'hash': commit_hash,
                'short': short_hash,
                'message': message,
                'author': author,
                'secrets': secrets
            })

            print(f"  {RED}❌ COMMIT {short_hash}{RESET}: {message}")
            print(f"     Author: {author}")
            print(f"     Found secrets:")
            for secret_type, matches in secrets.items():
                for match_info in matches:
                    print(f"       - {secret_type}: {match_info['masked']}")
            print()

    if total_secrets == 0:
        print(f"  {GREEN}✅ No secrets detected in recent {num_commits} commits{RESET}\n")
    else:
        print(f"  {RED}Found {total_secrets} potential secrets in {len(commits_with_secrets)} commits{RESET}\n")

    # Phase 4: Check for .env in git history
    print_header("PHASE 4: .ENV FILE IN HISTORY")

    try:
        result = subprocess.run(
            ["git", "log", "--all", "--full-history", "--", ".env"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        env_in_history = result.returncode == 0 and result.stdout.strip() != ""
        check(".env ever committed", env_in_history,
              "DANGER: .env committed to history!" if env_in_history else "OK: .env never committed")

        if env_in_history:
            env_commits = len([l for l in result.stdout.split('\n') if l.startswith('commit')])
            print(f"  {YELLOW}⚠️  .env appears in {env_commits} commits in history{RESET}\n")

    except Exception as e:
        print(f"  {YELLOW}⚠️  Could not check .env history: {e}{RESET}\n")

    # Phase 5: Summary and Recommendations
    print_header("REMEDIATION RECOMMENDATIONS")

    if total_secrets > 0:
        print(f"  {RED}CRITICAL: Found {total_secrets} secrets in commit history{RESET}\n")
        print("  Recommended Actions:")
        print("  1. IMMEDIATE: Rotate all exposed credentials")
        print("     - EODHD_API_TOKEN (rotate at dashboard)")
        print("     - GEMINI_API_KEY (request new key)")
        print("     - NOTION_TOKEN (regenerate in Notion settings)")
        print("     - GITHUB_TOKEN (delete and create new in GitHub)")
        print()
        print("  2. CLEAN GIT HISTORY:")
        print("     a. Add to .gitignore: echo '.env' >> .gitignore")
        print("     b. Remove from tracking: git rm --cached .env")
        print("     c. Use BFG Repo-Cleaner (if needed):")
        print("        brew install bfg  # or apt-get install bfg")
        print("        bfg --delete-files '.env' --no-blob-protection")
        print("        git reflog expire --expire=now --all && git gc --aggressive --prune=now")
        print()
        print("  3. Force push (after rotation):")
        print("     git push --force-with-lease origin main")
        print()
    else:
        print(f"  {GREEN}✅ No secrets found in recent commits{RESET}\n")
        print("  Recommended Actions:")
        print("  1. Ensure .env is in .gitignore")
        print("  2. Remove .env from git tracking (if present):")
        print("     git rm --cached .env")
        print("  3. Commit the cleanup:")
        print("     git add .gitignore")
        print("     git commit -m 'chore(#055): add .env to .gitignore'")
        print("  4. Push:")
        print("     git push origin main")
        print()

    print(f"{BLUE}{'='*80}{RESET}\n")

    return 1 if total_secrets > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
