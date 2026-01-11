#!/usr/bin/env python3
"""
GitHub API Connectivity Test (Task #042.5)

Test the GITHUB_TOKEN against GitHub API to verify authentication
and obtain user information.

Usage:
    python3 scripts/test_github_api.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
load_dotenv(PROJECT_ROOT / ".env")

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


def test_github_api():
    """Test GitHub API connectivity with token."""
    section("🔧 GITHUB API CONNECTIVITY TEST (Task #042.5)")

    # Step 1: Load token
    print()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log("GITHUB_TOKEN: NOT CONFIGURED", "ERROR")
        return False

    log(f"GITHUB_TOKEN: Found (length: {len(token)})", "INFO")
    log(f"Token preview: {token[:10]}...{token[-4:]}", "INFO")

    # Step 2: Prepare request
    section("1️⃣  PREPARING REQUEST")

    import requests

    endpoint = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MT5-CRS-Diagnostic/1.0"
    }

    log(f"Endpoint: GET {endpoint}", "INFO")
    log(f"Authorization: token {token[:10]}...{token[-4:]}", "INFO")
    log(f"Headers prepared", "SUCCESS")

    # Step 3: Make request
    section("2️⃣  SENDING REQUEST")

    try:
        log(f"Connecting to GitHub API...", "INFO")
        response = requests.get(
            endpoint,
            headers=headers,
            timeout=10
        )

        log(f"HTTP Status: {response.status_code}", "INFO")
        log(f"Response Headers:", "INFO")
        for key, value in response.headers.items():
            if key in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-OAuth-Scopes"]:
                log(f"  {key}: {value}", "INFO")

        # Step 4: Handle response
        section("3️⃣  RESPONSE ANALYSIS")

        if response.status_code == 200:
            # Successful authentication
            data = response.json()
            log(f"Authentication: SUCCESSFUL ✅", "SUCCESS")

            # Extract key information
            login = data.get("login", "Unknown")
            name = data.get("name", "N/A")
            email = data.get("email", "N/A")
            public_repos = data.get("public_repos", 0)
            followers = data.get("followers", 0)

            print()
            log(f"GitHub User Information:", "INFO")
            log(f"  Login: {login}", "SUCCESS")
            log(f"  Name: {name}", "SUCCESS")
            log(f"  Email: {email}", "INFO")
            log(f"  Public Repos: {public_repos}", "INFO")
            log(f"  Followers: {followers}", "INFO")

            # Token scopes
            scopes = response.headers.get("X-OAuth-Scopes", "")
            if scopes:
                scope_list = [s.strip() for s in scopes.split(",")]
                log(f"  Token Scopes: {', '.join(scope_list) if scope_list else 'None'}", "INFO")
            else:
                log(f"  Token Scopes: No scopes (read-only access)", "WARN")

            # Rate limit info
            rate_limit = response.headers.get("X-RateLimit-Remaining", "Unknown")
            rate_limit_max = response.headers.get("X-RateLimit-Limit", "Unknown")
            log(f"  Rate Limit: {rate_limit}/{rate_limit_max} remaining", "INFO")

            print()
            log(f"GitHub Token Status: VALID & OPERATIONAL ✅", "SUCCESS")
            return True

        elif response.status_code == 401:
            # Authentication failed
            log(f"Authentication: FAILED (HTTP 401)", "ERROR")
            error_data = response.json()
            error_msg = error_data.get("message", "Unknown error")
            log(f"Error: {error_msg}", "ERROR")
            return False

        elif response.status_code == 403:
            # Rate limited or access denied
            log(f"Authentication: DENIED (HTTP 403)", "ERROR")
            error_data = response.json()
            error_msg = error_data.get("message", "Unknown error")
            log(f"Error: {error_msg}", "ERROR")

            # Check if it's rate limiting
            if "API rate limit exceeded" in error_msg:
                reset_time = response.headers.get("X-RateLimit-Reset", "Unknown")
                log(f"Rate limit reset: {reset_time}", "INFO")
            return False

        else:
            # Other error
            log(f"Request Failed: HTTP {response.status_code}", "ERROR")
            try:
                error_data = response.json()
                log(f"Error: {error_data}", "ERROR")
            except:
                log(f"Response: {response.text[:300]}", "ERROR")
            return False

    except requests.exceptions.Timeout:
        log(f"Request TIMEOUT: GitHub API not responding", "ERROR")
        return False
    except requests.exceptions.ConnectionError as e:
        log(f"Connection ERROR: Cannot reach GitHub API", "ERROR")
        log(f"Details: {str(e)}", "ERROR")
        return False
    except json.JSONDecodeError as e:
        log(f"JSON Parse ERROR: Response not valid JSON", "ERROR")
        return False
    except Exception as e:
        log(f"Unexpected ERROR: {type(e).__name__}", "ERROR")
        log(f"Details: {str(e)}", "ERROR")
        return False


def main():
    """Execute GitHub API test."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}🔐 GITHUB API CONNECTIVITY TEST{RESET}")
    print(f"{BLUE}Task #042.5: Verify GitHub Token{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

    success = test_github_api()

    # Final verdict
    print()
    print(f"{BLUE}{'=' * 70}{RESET}")
    if success:
        print(f"{GREEN}🎯 VERDICT: GITHUB TOKEN VALID & OPERATIONAL ✅{RESET}")
        print(f"{GREEN}Ready for GitHub API integration{RESET}")
    else:
        print(f"{RED}🎯 VERDICT: GITHUB TOKEN INVALID OR UNREACHABLE ❌{RESET}")
        print(f"{RED}Check token format and GitHub API status{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
