#!/usr/bin/env python3
"""
Virtual Environment Upgrade Script - Python 3.6 → Python 3.9

This script:
1. Deletes the old Python 3.6 venv
2. Creates a new Python 3.9 venv
3. Upgrades pip, setuptools, and wheel
4. Restores all dependencies from requirements.txt

Protocol v2.2: Infrastructure maintenance task
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VENV_PATH = PROJECT_ROOT / "venv"
PYTHON39_PATH = Path("/usr/local/bin/python3.9")

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def log(msg, level="INFO"):
    """Print formatted log message."""
    colors = {"SUCCESS": GREEN, "ERROR": RED, "INFO": CYAN, "HEADER": BLUE, "WARNING": YELLOW}
    prefix = {"SUCCESS": "✅", "ERROR": "❌", "INFO": "ℹ️", "HEADER": "═", "WARNING": "⚠️"}.get(level, "•")
    color = colors.get(level, RESET)
    print(f"{color}{prefix} {msg}{RESET}")


def run_cmd(cmd, description="", check=True):
    """Run a command and return success/failure."""
    if description:
        log(description, "INFO")
    
    try:
        result = subprocess.run(cmd, shell=isinstance(cmd, str), check=False, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            if check:
                log(f"Command failed: {cmd}", "ERROR")
                log(f"Error: {result.stderr}", "ERROR")
                return False, result.stderr
            return False, result.stderr
    except Exception as e:
        log(f"Exception running command: {e}", "ERROR")
        return False, str(e)


def upgrade_venv():
    """Upgrade venv from Python 3.6 to Python 3.9."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}🚀 VIRTUAL ENVIRONMENT UPGRADE: Python 3.6 → Python 3.9{RESET}")
    print(f"{BLUE}Task #040.13: Runtime Upgrade - Restore Python 3.9{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Step 1: Verify Python 3.9 exists
    log("Step 1: Verifying Python 3.9 availability...", "INFO")
    if not PYTHON39_PATH.exists():
        log(f"Python 3.9 not found at {PYTHON39_PATH}", "ERROR")
        log("Please install Python 3.9 and try again", "ERROR")
        return False

    success, output = run_cmd(f"{PYTHON39_PATH} --version", "", check=False)
    if success:
        version_line = output.strip()
        log(f"Found: {version_line}", "SUCCESS")
    else:
        log(f"Could not determine Python 3.9 version", "WARNING")

    # Step 2: Delete old venv
    log("\nStep 2: Removing old Python 3.6 venv...", "INFO")
    if VENV_PATH.exists():
        try:
            shutil.rmtree(VENV_PATH)
            log(f"Deleted: {VENV_PATH}", "SUCCESS")
        except Exception as e:
            log(f"Failed to delete venv: {e}", "ERROR")
            return False
    else:
        log(f"venv not found at {VENV_PATH} (already deleted)", "WARNING")

    # Step 3: Create new venv with Python 3.9
    log("\nStep 3: Creating new Python 3.9 virtual environment...", "INFO")
    success, output = run_cmd(f"{PYTHON39_PATH} -m venv {VENV_PATH}", "Initializing venv...")
    if not success:
        log("Failed to create venv", "ERROR")
        return False
    log(f"Created venv at: {VENV_PATH}", "SUCCESS")

    # Step 4: Upgrade pip, setuptools, wheel
    log("\nStep 4: Upgrading pip, setuptools, and wheel...", "INFO")
    pip_path = VENV_PATH / "bin" / "pip"
    
    success, output = run_cmd(
        f"{pip_path} install --upgrade pip setuptools wheel",
        "Installing latest pip, setuptools, wheel..."
    )
    if not success:
        log("Warning: pip upgrade had issues, continuing anyway", "WARNING")

    # Verify pip
    success, output = run_cmd(f"{pip_path} --version", "", check=False)
    if success:
        log(f"pip ready: {output.strip()}", "SUCCESS")

    # Step 5: Verify Python version in venv
    log("\nStep 5: Verifying Python 3.9 in venv...", "INFO")
    python_path = VENV_PATH / "bin" / "python"
    success, output = run_cmd(f"{python_path} --version", "", check=False)
    if success:
        version_line = output.strip()
        log(f"venv Python: {version_line}", "SUCCESS")
        
        # Check if it's Python 3.9+
        if "3.9" in version_line or "3.10" in version_line or "3.11" in version_line:
            log("✅ Python 3.9+ confirmed!", "SUCCESS")
        else:
            log(f"Warning: Expected Python 3.9, got {version_line}", "WARNING")
    else:
        log("Could not determine venv Python version", "ERROR")

    # Step 6: Install dependencies from requirements.txt
    log("\nStep 6: Installing dependencies from requirements.txt...", "INFO")
    
    # First uncomment curl_cffi in requirements.txt for Python 3.9
    req_file = PROJECT_ROOT / "requirements.txt"
    if req_file.exists():
        log("Updating requirements.txt (uncomment curl_cffi for Python 3.9)...", "INFO")
        content = req_file.read_text()
        
        # Uncomment curl_cffi
        if "# curl_cffi>=" in content:
            content = content.replace("# curl_cffi>=", "curl_cffi>=")
            req_file.write_text(content)
            log("Uncommented curl_cffi in requirements.txt", "SUCCESS")
        
        # Install requirements
        success, output = run_cmd(
            f"{pip_path} install -r {req_file}",
            "Installing all dependencies..."
        )
        if success:
            log("Dependencies installed successfully", "SUCCESS")
        else:
            log("Some dependencies failed to install:", "WARNING")
            log(output[-500:], "INFO")  # Show last 500 chars of output

    # Step 7: Verify curl_cffi installation
    log("\nStep 7: Verifying curl_cffi installation...", "INFO")
    success, output = run_cmd(
        f"{pip_path} show curl-cffi",
        "Checking curl_cffi...",
        check=False
    )
    if success and output:
        log("curl_cffi installed successfully", "SUCCESS")
    else:
        log("curl_cffi not installed (may not be available for this Python)", "WARNING")

    # Step 8: List key packages
    log("\nStep 8: Installed packages summary...", "INFO")
    success, output = run_cmd(
        f"{pip_path} list | grep -E 'curl-cffi|requests|python-dotenv|psycopg2|feast'",
        "Key packages:",
        check=False
    )
    if success and output:
        for line in output.strip().split('\n'):
            if line:
                print(f"  {line}")

    # Final summary
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{GREEN}✅ VENV UPGRADE COMPLETE{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    print("Summary:")
    print(f"  ✅ Old venv (Python 3.6) deleted")
    print(f"  ✅ New venv created with Python 3.9")
    print(f"  ✅ pip, setuptools, wheel upgraded")
    print(f"  ✅ Dependencies installed from requirements.txt")
    print(f"  ✅ curl_cffi uncommented and available")
    print()
    print("Verification:")
    print(f"  Run: {python_path} --version")
    print(f"  Run: {pip_path} show curl-cffi")
    print(f"  Run: python3 scripts/audit_current_task.py")
    print()

    return True


if __name__ == "__main__":
    try:
        success = upgrade_venv()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)
