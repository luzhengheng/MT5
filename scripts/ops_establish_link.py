#!/usr/bin/env python3
"""
Task #011.12: Full Mesh Link Activation
Purpose: Activate the complete distributed mesh and start sync daemon
Protocol: v2.2 (Docs-as-Code)

4-Phase Activation:
1. Local verification (Python, environment, imports)
2. Gateway detection (wait for GTW ZMQ ports 5555/5556 to open)
3. Nexus daemon activation (start nexus_with_proxy.py)
4. Connectivity verification (confirm full mesh is operational)

Expected Outcome: "FULL MESH CONNECTED & OPERATIONAL"
"""

import subprocess
import sys
import socket
import time
import signal
from pathlib import Path
from typing import Tuple, List
import json
import os

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Mesh configuration
GTW_IP = "172.19.141.255"
GTW_REQ_PORT = 5555
GTW_SUB_PORT = 5556
MAX_GTW_WAIT_ATTEMPTS = 120  # 10 minutes with 5s intervals
GTW_WAIT_INTERVAL = 5


def print_header(title: str, phase: str = ""):
    """Print formatted section header."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    if phase:
        print(f"{CYAN}  {phase}{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")


def check_status(name: str, status: bool, detail: str = "", error: str = ""):
    """Print formatted status check."""
    symbol = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
    detail_str = f"  [{detail}]" if detail else ""
    if error:
        print(f"  {symbol} {name:<50} {detail_str}")
        print(f"     {RED}Error: {error}{RESET}")
    else:
        print(f"  {symbol} {name:<50} {detail_str}")
    return status


def run_cmd(cmd: List[str], timeout: int = 5, cwd: Path = None) -> Tuple[bool, str]:
    """Run command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def phase_1_local_verification() -> bool:
    """Phase 1: Verify local environment"""
    print_header("PHASE 1: LOCAL VERIFICATION", "(Initialize activation)")

    all_ok = True

    # Check Python version
    try:
        if sys.version_info >= (3, 9):
            check_status("Python version", True, f"Python {sys.version_info.major}.{sys.version_info.minor}")
        else:
            check_status("Python version", False, f"Python {sys.version_info.major}.{sys.version_info.minor}", "Need 3.9+")
            all_ok = False
    except:
        check_status("Python version", False, "", "Unknown error")
        all_ok = False

    # Check .env file
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        check_status(".env file", True, "Configuration loaded")
    else:
        check_status(".env file", False, "", f"Not found at {env_file}")
        all_ok = False

    # Check project structure
    required_files = [
        ("scripts/nexus_with_proxy.py", "Sync daemon"),
        ("src/data_nexus", "Data nexus module"),
        ("scripts/project_cli.py", "Project CLI"),
    ]

    for file_path, desc in required_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            check_status(f"{desc} exists", True, file_path)
        else:
            check_status(f"{desc} exists", False, file_path, "Not found")
            all_ok = False

    # Try importing redis and other required packages
    try:
        import redis
        import psycopg2
        check_status("Required packages", True, "redis, psycopg2 available")
    except ImportError as e:
        check_status("Required packages", False, "", f"Missing: {e}")
        all_ok = False

    return all_ok


def check_gtw_port(port: int, port_name: str) -> bool:
    """Check if GTW port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((GTW_IP, port))
        sock.close()
        return result == 0
    except:
        return False


def phase_2_gateway_detection() -> bool:
    """Phase 2: Wait for GTW to come online"""
    print_header("PHASE 2: GATEWAY DETECTION", "(Wait for GTW ZMQ ports)")

    print(f"  Waiting for GTW ({GTW_IP}) to come online...")
    print(f"  Checking ZMQ REQ ({GTW_REQ_PORT}) and SUB ({GTW_SUB_PORT}) ports...")
    print(f"  Max wait: {MAX_GTW_WAIT_ATTEMPTS * GTW_WAIT_INTERVAL}s (timeout)\n")

    for attempt in range(1, MAX_GTW_WAIT_ATTEMPTS + 1):
        req_open = check_gtw_port(GTW_REQ_PORT, "REQ")
        sub_open = check_gtw_port(GTW_SUB_PORT, "SUB")

        if req_open and sub_open:
            elapsed = (attempt - 1) * GTW_WAIT_INTERVAL
            print(f"\n  {GREEN}✅ Gateway online at attempt {attempt}{RESET}")
            check_status("GTW ZMQ REQ (5555)", True, "Port open")
            check_status("GTW ZMQ SUB (5556)", True, "Port open")
            print(f"  {GREEN}GTW is operational (elapsed: {elapsed}s){RESET}\n")
            return True

        # Progress indicator every 10 attempts
        if attempt % 10 == 0:
            elapsed = (attempt - 1) * GTW_WAIT_INTERVAL
            print(f"  ⏳ Waiting... (attempt {attempt}/{MAX_GTW_WAIT_ATTEMPTS}, elapsed: {elapsed}s)")

        # Wait before next attempt
        try:
            time.sleep(GTW_WAIT_INTERVAL)
        except KeyboardInterrupt:
            print(f"\n  {YELLOW}⚠️  Interrupted by user{RESET}\n")
            return False

    # Timeout reached
    print(f"\n  {RED}❌ Gateway not detected (timeout after {MAX_GTW_WAIT_ATTEMPTS * GTW_WAIT_INTERVAL}s){RESET}")
    check_status("GTW ZMQ REQ (5555)", False, "", "Port not responding")
    check_status("GTW ZMQ SUB (5556)", False, "", "Port not responding")
    print(f"  {YELLOW}Proceeding anyway - GTW may be starting{RESET}\n")

    return False  # Strict mode: fail if GTW not ready


def phase_3_daemon_activation() -> Tuple[bool, str]:
    """Phase 3: Start nexus sync daemon"""
    print_header("PHASE 3: DAEMON ACTIVATION", "(Start nexus_with_proxy.py)")

    nexus_script = PROJECT_ROOT / "scripts" / "nexus_with_proxy.py"

    if not nexus_script.exists():
        check_status("nexus_with_proxy.py exists", False, "", f"Not found at {nexus_script}")
        return False, "Script not found"

    check_status("nexus_with_proxy.py exists", True, "Script ready")

    # Check if nexus is already running
    try:
        result = subprocess.run(
            ["pgrep", "-f", "nexus_with_proxy.py"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            pid = result.stdout.strip().split('\n')[0]
            check_status("nexus daemon already running", True, f"PID {pid}")
            return True, f"Already running (PID {pid})"
    except:
        pass

    # Start the daemon
    print(f"  Starting nexus_with_proxy.py...\n")

    try:
        # Start as background process
        process = subprocess.Popen(
            [sys.executable, str(nexus_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(PROJECT_ROOT),
            start_new_session=True  # Detach from current session
        )

        # Wait a moment for process to start
        time.sleep(2)

        # Verify it's running
        try:
            result = subprocess.run(
                ["pgrep", "-f", "nexus_with_proxy.py"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                pid = result.stdout.strip().split('\n')[0]
                check_status("nexus daemon started", True, f"PID {pid}")
                return True, f"Started (PID {pid})"
            else:
                check_status("nexus daemon started", False, "", "Process exited")
                return False, "Process failed to start"
        except:
            check_status("nexus daemon started", False, "", "Could not verify")
            return False, "Verification failed"

    except Exception as e:
        check_status("nexus daemon started", False, "", str(e))
        return False, str(e)


def phase_4_connectivity_verification() -> bool:
    """Phase 4: Verify full mesh is operational"""
    print_header("PHASE 4: CONNECTIVITY VERIFICATION", "(Confirm operational status)")

    all_ok = True

    # Check 1: Redis (feature store)
    try:
        import redis
        r = redis.Redis(host="127.0.0.1", port=6379, socket_connect_timeout=2)
        r.ping()
        check_status("Redis connectivity", True, "Feature store online")
    except Exception as e:
        check_status("Redis connectivity", False, "", str(e))
        all_ok = False

    # Check 2: PostgreSQL (feature store offline)
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user="trader",
            password="password",
            database="mt5_crs",
            connect_timeout=2
        )
        conn.close()
        check_status("PostgreSQL connectivity", True, "Offline store online")
    except Exception as e:
        check_status("PostgreSQL connectivity", False, "", str(e))
        all_ok = False

    # Check 3: GTW ZMQ REQ port
    if check_gtw_port(GTW_REQ_PORT, "REQ"):
        check_status("GTW ZMQ REQ (5555)", True, "Async messaging ready")
    else:
        check_status("GTW ZMQ REQ (5555)", False, "", "Not responding")
        all_ok = False

    # Check 4: GTW ZMQ SUB port
    if check_gtw_port(GTW_SUB_PORT, "SUB"):
        check_status("GTW ZMQ SUB (5556)", True, "Event publishing ready")
    else:
        check_status("GTW ZMQ SUB (5556)", False, "", "Not responding")
        all_ok = False

    # Check 5: nexus daemon
    try:
        result = subprocess.run(
            ["pgrep", "-f", "nexus_with_proxy.py"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            pid = result.stdout.strip().split('\n')[0]
            check_status("nexus daemon running", True, f"PID {pid}")
        else:
            check_status("nexus daemon running", False, "", "Process not found")
            all_ok = False
    except:
        check_status("nexus daemon running", False, "", "Could not verify")
        all_ok = False

    # Check 6: GitHub connectivity
    try:
        import urllib.request
        urllib.request.urlopen("https://github.com", timeout=3)
        check_status("GitHub HTTPS", True, "Reachable")
    except:
        check_status("GitHub HTTPS", False, "", "Not reachable")
        all_ok = False

    # Check 7: Notion API connectivity
    try:
        import urllib.request
        urllib.request.urlopen("https://api.notion.com", timeout=3)
        check_status("Notion API HTTPS", True, "Reachable")
    except:
        check_status("Notion API HTTPS", False, "", "Not reachable")
        all_ok = False

    return all_ok


def main():
    """Execute full mesh activation."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  TASK #011.12: FULL MESH LINK ACTIVATION{RESET}")
    print(f"{CYAN}  4-Phase Distributed System Initialization{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    # Phase 1: Local verification
    if not phase_1_local_verification():
        print(f"\n  {RED}❌ Local verification failed - cannot proceed{RESET}\n")
        return 1

    # Phase 2: Gateway detection
    gtw_ready = phase_2_gateway_detection()
    if not gtw_ready:
        print(f"  {YELLOW}⚠️  Gateway not ready, but continuing...{RESET}\n")
        # Continue anyway - GTW might be starting

    # Phase 3: Daemon activation
    daemon_ok, daemon_detail = phase_3_daemon_activation()

    # Phase 4: Connectivity verification
    connectivity_ok = phase_4_connectivity_verification()

    # Final status
    print_header("ACTIVATION SUMMARY")

    if daemon_ok and connectivity_ok:
        print(f"  {GREEN}🎯 FULL MESH CONNECTED & OPERATIONAL{RESET}\n")
        print(f"  {GREEN}Phase 1: ✅ Local environment verified{RESET}")
        print(f"  {GREEN}Phase 2: {'✅' if gtw_ready else '⚠️'} Gateway {'online' if gtw_ready else 'detection completed'}{RESET}")
        print(f"  {GREEN}Phase 3: ✅ Nexus daemon activated{RESET}")
        print(f"  {GREEN}Phase 4: ✅ Connectivity verified{RESET}\n")
        print(f"  {GREEN}System is 100% operational and ready for trading.{RESET}\n")
        return 0
    elif daemon_ok:
        print(f"  {YELLOW}⚠️  PARTIAL OPERATIONAL{RESET}\n")
        print(f"  {YELLOW}Daemon is running but some connectivity checks failed.{RESET}")
        print(f"  {YELLOW}Monitor the system for issues.{RESET}\n")
        return 1
    else:
        print(f"  {RED}❌ ACTIVATION FAILED{RESET}\n")
        print(f"  {RED}Could not start nexus daemon or establish connectivity.{RESET}")
        print(f"  {RED}Check logs and retry.{RESET}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
