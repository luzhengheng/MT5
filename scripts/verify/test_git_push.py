#!/usr/bin/env python3
"""
Git Push Capability Verification (Task #042.6)

Test git push capability using --dry-run to verify write permissions
without actually pushing to the remote repository.

Usage:
    python3 scripts/test_git_push.py
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(msg, level="INFO"):
    """Print formatted log message."""
    colors = {
        "SUCCESS": GREEN,
        "ERROR": RED,
        "WARN": YELLOW,
        "INFO": CYAN,
        "HEADER": BLUE
    }
    prefix = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARN": "⚠️",
        "INFO": "ℹ️",
        "HEADER": "═"
    }.get(level, "•")
    color = colors.get(level, RESET)
    print(f"{color}{prefix} {msg}{RESET}")


def section(title):
    """Print section header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'-' * 70}{RESET}")


def mask_url(url):
    """Mask sensitive parts of URL for privacy."""
    if not url:
        return "N/A"

    # For SSH URLs (git@github.com:user/repo.git)
    if url.startswith("git@"):
        parts = url.split(":")
        if len(parts) == 2:
            host = parts[0]  # git@github.com
            path = parts[1]  # user/repo.git
            path_parts = path.split("/")
            if len(path_parts) >= 2:
                # Mask username
                user = path_parts[0]
                masked_user = user[:2] + "***" + user[-2:] if len(user) > 4 else "***"
                path_parts[0] = masked_user
                return f"{host}:{'/'.join(path_parts)}"

    # For HTTPS URLs (https://github.com/user/repo.git)
    if url.startswith("http"):
        parts = url.split("/")
        if len(parts) >= 5:
            # Mask username (parts[3])
            user = parts[3]
            masked_user = user[:2] + "***" + user[-2:] if len(user) > 4 else "***"
            parts[3] = masked_user
            return "/".join(parts)

    return url


def run_command(cmd, timeout=10):
    """Run shell command and capture output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_current_branch():
    """Get current git branch name."""
    code, stdout, stderr = run_command("git rev-parse --abbrev-ref HEAD")
    if code == 0:
        return stdout.strip()
    return None


def test_git_push():
    """Test git push capability using --dry-run."""
    section("🔧 GIT PUSH CAPABILITY TEST (Task #042.6)")

    # Step 1: Check git repository
    print()
    log("Checking git repository status...", "INFO")
    code, stdout, stderr = run_command("git status")
    if code != 0:
        log("Not a git repository or git not configured", "ERROR")
        return False

    log("Git repository: FOUND", "SUCCESS")

    # Step 2: Get remote information
    section("1️⃣  REMOTE CONFIGURATION")

    code, stdout, stderr = run_command("git remote -v")
    if code != 0:
        log("Cannot read git remotes", "ERROR")
        return False

    remotes = {}
    for line in stdout.strip().split('\n'):
        if line:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                url = parts[1]
                remote_type = parts[2].strip('()') if len(parts) >= 3 else "unknown"
                if name not in remotes:
                    remotes[name] = {}
                remotes[name][remote_type] = url

    if not remotes:
        log("No git remotes configured", "ERROR")
        return False

    log(f"Git remotes found: {len(remotes)}", "INFO")
    for remote_name, remote_info in remotes.items():
        for remote_type, url in remote_info.items():
            masked = mask_url(url)
            log(f"  {remote_name} ({remote_type}): {masked}", "INFO")

    # Determine URL type
    origin_url = remotes.get('origin', {}).get('push', remotes.get('origin', {}).get('fetch', ''))
    if origin_url:
        if origin_url.startswith('git@'):
            url_type = "SSH"
        elif origin_url.startswith('http'):
            url_type = "HTTPS"
        else:
            url_type = "UNKNOWN"
        log(f"Authentication type: {url_type}", "INFO")

    # Step 3: Get current branch
    section("2️⃣  BRANCH INFORMATION")

    current_branch = get_current_branch()
    if not current_branch:
        log("Cannot determine current branch", "ERROR")
        return False

    log(f"Current branch: {current_branch}", "SUCCESS")

    # Check if branch has upstream
    code, stdout, stderr = run_command(f"git rev-parse --abbrev-ref {current_branch}@{{upstream}}")
    if code == 0:
        upstream = stdout.strip()
        log(f"Upstream branch: {upstream}", "INFO")
    else:
        log(f"No upstream configured for {current_branch}", "WARN")
        log(f"Will attempt push to origin/{current_branch}", "INFO")

    # Step 4: Dry-run push test
    section("3️⃣  DRY-RUN PUSH TEST (CRITICAL)")

    log(f"Testing push capability (no actual push will occur)...", "INFO")
    log(f"Command: git push --dry-run origin {current_branch}", "INFO")

    # Run the dry-run push
    code, stdout, stderr = run_command(
        f"git push --dry-run origin {current_branch}",
        timeout=30
    )

    # Combine stdout and stderr for analysis
    output = stdout + stderr

    # Step 5: Analyze results
    section("4️⃣  RESULT ANALYSIS")

    log(f"Exit code: {code}", "INFO")

    if output.strip():
        log(f"Output:", "INFO")
        for line in output.strip().split('\n'):
            if line:
                log(f"  {line}", "INFO")

    # Determine success/failure
    success = False

    if code == 0:
        # Dry-run succeeded
        if "Everything up-to-date" in output:
            log("Push Status: Everything up-to-date (no changes to push)", "SUCCESS")
            success = True
        elif "Would" in output or "dry run" in output.lower():
            log("Push Status: Dry-run successful (changes would be pushed)", "SUCCESS")
            success = True
        else:
            log("Push Status: Command completed successfully", "SUCCESS")
            success = True
    else:
        # Dry-run failed
        if "Permission denied" in output or "permission denied" in output.lower():
            log("Push Status: PERMISSION DENIED", "ERROR")
            log("Authentication failed - SSH key or credentials invalid", "ERROR")
        elif "authentication failed" in output.lower() or "auth" in output.lower():
            log("Push Status: AUTHENTICATION FAILED", "ERROR")
            log("Credentials are invalid or not configured", "ERROR")
        elif "Could not read from remote" in output:
            log("Push Status: CANNOT READ FROM REMOTE", "ERROR")
            log("Network issue or authentication problem", "ERROR")
        elif "fatal" in output.lower():
            log("Push Status: FATAL ERROR", "ERROR")
            for line in output.split('\n'):
                if 'fatal' in line.lower():
                    log(f"  {line}", "ERROR")
        else:
            log("Push Status: FAILED (unknown reason)", "ERROR")

    # Step 6: Provide recommendations
    section("5️⃣  AUTHENTICATION STATUS")

    if success:
        log("Git Push Access: GRANTED ✅", "SUCCESS")
        log("Authentication mechanism: WORKING", "SUCCESS")

        if url_type == "SSH":
            log("SSH key is configured and accepted", "SUCCESS")
        elif url_type == "HTTPS":
            log("Credentials are cached or configured", "SUCCESS")

        log("Repository write permissions: CONFIRMED", "SUCCESS")

    else:
        log("Git Push Access: DENIED ❌", "ERROR")
        log("Authentication mechanism: NOT WORKING", "ERROR")

        print()
        log("Troubleshooting suggestions:", "WARN")
        if url_type == "SSH":
            log("  1. Check SSH key: ssh -T git@github.com", "INFO")
            log("  2. Add SSH key: ssh-add ~/.ssh/id_rsa", "INFO")
            log("  3. Generate new key: ssh-keygen -t ed25519", "INFO")
        elif url_type == "HTTPS":
            log("  1. Configure credentials: git config credential.helper store", "INFO")
            log("  2. Update remote URL: git remote set-url origin <url>", "INFO")
            log("  3. Use personal access token instead of password", "INFO")
        else:
            log("  1. Check remote URL: git remote -v", "INFO")
            log("  2. Reconfigure remote: git remote set-url origin <url>", "INFO")

    return success


def main():
    """Execute git push capability test."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}🚀 GIT PUSH CAPABILITY VERIFICATION{RESET}")
    print(f"{BLUE}Task #042.6: Verify Git Write Access{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

    success = test_git_push()

    # Final verdict
    print()
    print(f"{BLUE}{'=' * 70}{RESET}")
    if success:
        print(f"{GREEN}🎯 VERDICT: GIT PUSH CAPABILITY VERIFIED ✅{RESET}")
        print(f"{GREEN}Write access to repository is active{RESET}")
        print(f"{GREEN}Authentication mechanism is working{RESET}")
    else:
        print(f"{RED}🎯 VERDICT: GIT PUSH ACCESS DENIED ❌{RESET}")
        print(f"{RED}Authentication or permissions issue detected{RESET}")
        print(f"{RED}See troubleshooting suggestions above{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
