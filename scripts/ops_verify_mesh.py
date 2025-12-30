#!/usr/bin/env python3
"""
Task #011.12: Full Mesh Connectivity Verification
Purpose: Comprehensive multi-layer mesh diagnostics for distributed infrastructure
Protocol: v2.2 (Docs-as-Code)

Verifies:
- Local environment (Python, package versions, Redis, PostgreSQL)
- Git hooks configuration
- Network connectivity (ICMP to GTW and HUB)
- Application ports (ZMQ 5555/5556 on GTW, GitHub HTTPS, Notion API)
- Internet connectivity

Mesh Architecture:
- INF: Local node at 127.0.0.1 (or 172.19.141.254 for HUB)
- GTW: Gateway node at 172.19.141.255 (ZMQ broker on ports 5555/5556)
- HUB: Hub node at 172.19.141.254 (Feature store, PostgreSQL, Redis)
"""

import subprocess
import sys
import socket
import json
import time
from pathlib import Path
from typing import Tuple, Dict, List
import re

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Mesh topology
MESH_NODES = {
    "INF": {"ip": "127.0.0.1", "name": "Local Node (INF)"},
    "GTW": {"ip": "172.19.141.255", "name": "Gateway (GTW)"},
    "HUB": {"ip": "172.19.141.254", "name": "Hub (HUB)"},
}

MESH_PORTS = {
    "GTW_REQ": {"ip": "172.19.141.255", "port": 5555, "proto": "ZMQ REQ"},
    "GTW_SUB": {"ip": "172.19.141.255", "port": 5556, "proto": "ZMQ SUB"},
    "GITHUB": {"host": "github.com", "port": 443, "proto": "HTTPS"},
    "NOTION": {"host": "api.notion.com", "port": 443, "proto": "HTTPS"},
}


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


def run_cmd(cmd: List[str], timeout: int = 5) -> Tuple[bool, str]:
    """Run command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def check_python_version() -> Tuple[bool, str]:
    """Verify Python 3.9+ is running."""
    try:
        version_info = sys.version_info
        if version_info >= (3, 9):
            return True, f"Python {version_info.major}.{version_info.minor}.{version_info.micro}"
        else:
            return False, f"Python {version_info.major}.{version_info.minor} (need 3.9+)"
    except:
        return False, "Unknown version"


def check_redis_connectivity() -> Tuple[bool, str]:
    """Verify Redis is accessible."""
    try:
        import redis
        r = redis.Redis(host="127.0.0.1", port=6379, socket_connect_timeout=2)
        r.ping()
        info = r.info()
        version = info.get("redis_version", "unknown")
        return True, f"Redis {version} online"
    except Exception as e:
        return False, str(e)


def check_postgres_connectivity() -> Tuple[bool, str]:
    """Verify PostgreSQL is accessible."""
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
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        conn.close()
        # Extract version number
        version_match = re.search(r"PostgreSQL (\d+\.\d+)", version)
        if version_match:
            return True, f"PostgreSQL {version_match.group(1)} online"
        return True, "PostgreSQL online"
    except Exception as e:
        return False, str(e)


def check_git_hooks() -> Tuple[bool, str]:
    """Verify git hooks are configured."""
    hooks_dir = PROJECT_ROOT / ".git" / "hooks"
    if not hooks_dir.exists():
        return False, ".git/hooks not found"

    # Check for post-commit hook
    post_commit = hooks_dir / "post-commit"
    if post_commit.exists() and post_commit.stat().st_mode & 0o111:
        return True, "post-commit hook configured"
    else:
        return False, "post-commit hook not found or not executable"


def check_icmp_connectivity(target_ip: str, target_name: str) -> Tuple[bool, str]:
    """Check ICMP ping connectivity."""
    success, output = run_cmd(
        ["ping", "-c", "1", "-W", "2", target_ip],
        timeout=5
    )
    if success:
        # Extract RTT from output
        match = re.search(r"time=([0-9.]+)ms", output)
        rtt = match.group(1) if match else "unknown"
        return True, f"{target_name} reachable ({rtt}ms)"
    else:
        return False, f"{target_name} unreachable"


def check_tcp_port(ip: str, port: int, proto: str, timeout: int = 2) -> Tuple[bool, str]:
    """Check TCP port connectivity."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            return True, f"{proto} port {port} open"
        else:
            return False, f"{proto} port {port} closed"
    except Exception as e:
        return False, str(e)


def check_https_host(host: str, proto: str, timeout: int = 5) -> Tuple[bool, str]:
    """Check HTTPS connectivity to host."""
    try:
        import urllib.request
        import urllib.error
        url = f"https://{host}"
        request = urllib.request.Request(url, method="HEAD")
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
            return True, f"{proto} [{response.status}]"
        except urllib.error.HTTPError as e:
            # HTTP errors mean the connection worked, just got a response
            return True, f"{proto} [HTTP {e.code}]"
        except urllib.error.URLError as e:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def phase_1_local_environment() -> int:
    """Phase 1: Local Environment Checks"""
    print_header("PHASE 1: LOCAL ENVIRONMENT", "(9 checks)")

    passed = 0

    # Check 1: Python version
    status, detail = check_python_version()
    if check_status("Python version 3.9+", status, detail):
        passed += 1

    # Check 2: Redis
    status, detail = check_redis_connectivity()
    if check_status("Redis connectivity", status, detail):
        passed += 1
    else:
        check_status("Redis connectivity", False, "", "May be offline - feature store requires Redis")

    # Check 3: PostgreSQL
    status, detail = check_postgres_connectivity()
    if check_status("PostgreSQL connectivity", status, detail):
        passed += 1
    else:
        check_status("PostgreSQL connectivity", False, "", "May be offline - feature store requires PostgreSQL")

    # Check 4: Git hooks
    status, detail = check_git_hooks()
    if check_status("Git post-commit hook", status, detail):
        passed += 1

    # Check 5: Project structure
    key_files = [
        (".env exists", PROJECT_ROOT / ".env"),
        ("src/data_nexus exists", PROJECT_ROOT / "src" / "data_nexus"),
        ("scripts/project_cli.py exists", PROJECT_ROOT / "scripts" / "project_cli.py"),
        ("requirements.txt exists", PROJECT_ROOT / "requirements.txt"),
    ]

    for file_name, file_path in key_files:
        if file_path.exists():
            if check_status(file_name, True, str(file_path.relative_to(PROJECT_ROOT))):
                passed += 1
        else:
            check_status(file_name, False, "", f"Not found at {file_path}")

    return passed


def phase_2_network_layer() -> int:
    """Phase 2: Network Layer Checks"""
    print_header("PHASE 2: NETWORK LAYER", "(2 checks)")

    passed = 0

    # Check 1: ICMP to GTW
    status, detail = check_icmp_connectivity(MESH_NODES["GTW"]["ip"], MESH_NODES["GTW"]["name"])
    if check_status("ICMP to GTW", status, detail):
        passed += 1
    else:
        check_status("ICMP to GTW", False, "", "Gateway unreachable - mesh may be offline")

    # Check 2: ICMP to HUB
    status, detail = check_icmp_connectivity(MESH_NODES["HUB"]["ip"], MESH_NODES["HUB"]["name"])
    if check_status("ICMP to HUB", status, detail):
        passed += 1
    else:
        check_status("ICMP to HUB", False, "", "Hub unreachable - feature store may be offline")

    return passed


def phase_3_application_ports() -> int:
    """Phase 3: Application Port Checks"""
    print_header("PHASE 3: APPLICATION PORTS", "(4 checks)")

    passed = 0

    # Check 1: GTW ZMQ REQ (5555)
    status, detail = check_tcp_port(MESH_PORTS["GTW_REQ"]["ip"], MESH_PORTS["GTW_REQ"]["port"], "ZMQ REQ")
    if check_status("GTW ZMQ REQ (5555)", status, detail):
        passed += 1
    else:
        check_status("GTW ZMQ REQ (5555)", False, "", "ZMQ broker not responding - async messaging disabled")

    # Check 2: GTW ZMQ SUB (5556)
    status, detail = check_tcp_port(MESH_PORTS["GTW_SUB"]["ip"], MESH_PORTS["GTW_SUB"]["port"], "ZMQ SUB")
    if check_status("GTW ZMQ SUB (5556)", status, detail):
        passed += 1
    else:
        check_status("GTW ZMQ SUB (5556)", False, "", "ZMQ pubsub not responding - event publishing disabled")

    # Check 3: GitHub HTTPS
    status, detail = check_https_host(MESH_PORTS["GITHUB"]["host"], "GitHub")
    if check_status("GitHub HTTPS (443)", status, detail):
        passed += 1
    else:
        check_status("GitHub HTTPS (443)", False, "", "Cannot reach GitHub - git operations may fail")

    # Check 4: Notion API HTTPS
    status, detail = check_https_host(MESH_PORTS["NOTION"]["host"], "Notion API")
    if check_status("Notion API HTTPS (443)", status, detail):
        passed += 1
    else:
        check_status("Notion API HTTPS (443)", False, "", "Cannot reach Notion - sync pipeline may be blocked")

    return passed


def phase_4_internet_checks() -> int:
    """Phase 4: Internet Connectivity Checks"""
    print_header("PHASE 4: INTERNET CONNECTIVITY", "(2 checks)")

    passed = 0

    # Check 1: DNS resolution
    try:
        ip = socket.gethostbyname("github.com")
        if check_status("DNS resolution", True, f"github.com -> {ip}"):
            passed += 1
    except Exception as e:
        check_status("DNS resolution", False, "", str(e))

    # Check 2: Gateway to internet
    status, detail = check_icmp_connectivity("8.8.8.8", "Google DNS")
    if status:
        if check_status("Internet gateway", status, detail):
            passed += 1
    else:
        check_status("Internet gateway", False, "", "No external connectivity")

    return passed


def main():
    """Execute full mesh diagnostic."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  TASK #011.12: FULL MESH CONNECTIVITY VERIFICATION{RESET}")
    print(f"{CYAN}  Distributed Infrastructure Diagnostic (4-Phase){RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    total_checks = 0
    passed_checks = 0

    # Phase 1: Local Environment (9 checks)
    passed_checks += phase_1_local_environment()
    total_checks += 9

    # Phase 2: Network Layer (2 checks)
    passed_checks += phase_2_network_layer()
    total_checks += 2

    # Phase 3: Application Ports (4 checks)
    passed_checks += phase_3_application_ports()
    total_checks += 4

    # Phase 4: Internet Checks (2 checks)
    passed_checks += phase_4_internet_checks()
    total_checks += 2

    # Summary
    print_header("DIAGNOSTIC SUMMARY")

    print(f"  Total Checks: {total_checks}")
    print(f"  Passed: {GREEN}{passed_checks}{RESET}")
    print(f"  Failed: {RED}{total_checks - passed_checks}{RESET}")

    success_rate = (passed_checks / total_checks) * 100
    print(f"  Success Rate: {success_rate:.1f}%\n")

    if passed_checks == total_checks:
        print(f"  {GREEN}🎯 FULL MESH CONNECTED & VERIFIED{RESET}\n")
        print(f"  {GREEN}All 17 diagnostic checks passed.{RESET}")
        print(f"  {GREEN}Mesh infrastructure is 100% operational.{RESET}")
        print(f"  {GREEN}Ready for nexus_with_proxy.py activation.{RESET}\n")
        return 0
    elif passed_checks >= (total_checks * 0.9):
        print(f"  {YELLOW}⚠️  PARTIAL CONNECTIVITY{RESET}\n")
        print(f"  {YELLOW}{total_checks - passed_checks} checks failed (likely non-critical).{RESET}")
        print(f"  {YELLOW}Proceed with caution or fix failing components.{RESET}\n")
        return 1
    else:
        print(f"  {RED}❌ MESH CONNECTIVITY COMPROMISED{RESET}\n")
        print(f"  {RED}{total_checks - passed_checks} critical checks failed.{RESET}")
        print(f"  {RED}Cannot proceed - fix the above issues and retry.{RESET}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
