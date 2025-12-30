#!/usr/bin/env python3
"""
Task #011.17: SSH Mesh Verification
Purpose: Validate password-less SSH access to all remote nodes
Protocol: v2.2 (Docs-as-Code)

Features:
- Batch mode SSH (no password prompts)
- "Hello World" command verification
- Cross-border connectivity test
- Summary table output
- Exit codes for automation
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Remote nodes to verify
REMOTE_NODES = {
    "gtw": {
        "description": "Gateway (Windows)",
        "address": "172.19.141.255",
        "network": "Local (Private)",
    },
    "hub": {
        "description": "Hub (Feature Store)",
        "address": "172.19.141.254",
        "network": "Local (Private)",
    },
    "gpu": {
        "description": "GPU (Compute Node)",
        "address": "www.guangzhoupeak.com",
        "network": "Remote (Internet)",
    },
}


def print_header(title: str, subtitle: str = ""):
    """Print formatted section header."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    if subtitle:
        print(f"{CYAN}  {subtitle}{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")


def test_ssh_connection(host: str) -> Tuple[bool, str, str]:
    """Test SSH connection with batch mode (no password)."""
    try:
        # SSH with batch mode to avoid password prompts
        # -o BatchMode=yes: No password prompts
        # -o ConnectTimeout=10: 10 second timeout
        # -o StrictHostKeyChecking=no: Skip host key verification
        result = subprocess.run(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                host,
                "echo 'Connection Success' && hostname && whoami"
            ],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            lines = output.split('\n')
            # Expected: "Connection Success", hostname, user
            return True, output, ""
        else:
            error = result.stderr.strip() or "SSH failed"
            return False, "", error

    except subprocess.TimeoutExpired:
        return False, "", "Timeout (>15s)"
    except FileNotFoundError:
        return False, "", "SSH command not found"
    except Exception as e:
        return False, "", str(e)


def test_latency(host: str) -> Tuple[bool, str]:
    """Measure SSH latency."""
    try:
        import time
        start = time.time()

        result = subprocess.run(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                host,
                "echo OK"
            ],
            capture_output=True,
            text=True,
            timeout=15
        )

        elapsed = (time.time() - start) * 1000  # Convert to ms

        if result.returncode == 0:
            return True, f"{elapsed:.0f}ms"
        else:
            return False, "N/A"

    except:
        return False, "N/A"


def main():
    """Execute SSH mesh verification."""
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}  TASK #011.17: SSH MESH VERIFICATION{RESET}")
    print(f"{CYAN}  Password-less SSH Access Validation{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    print("Testing SSH connectivity to all remote nodes...\n")

    # Test results
    results = []
    passed = 0
    failed = 0

    for host, info in REMOTE_NODES.items():
        print(f"  Testing {host}...", end=" ", flush=True)

        # Test connection
        success, output, error = test_ssh_connection(host)

        if success:
            # Test latency
            latency_ok, latency = test_latency(host)
            print(f"{GREEN}✅{RESET}")
            results.append({
                "host": host,
                "description": info["description"],
                "address": info["address"],
                "network": info["network"],
                "status": "✅ PASS",
                "latency": latency if latency_ok else "N/A",
                "details": f"Connected as {output.split(chr(10))[-1] if chr(10) in output else 'OK'}",
            })
            passed += 1
        else:
            print(f"{RED}❌{RESET}")
            results.append({
                "host": host,
                "description": info["description"],
                "address": info["address"],
                "network": info["network"],
                "status": "❌ FAIL",
                "latency": "N/A",
                "details": error,
            })
            failed += 1

    # Print results table
    print_header("VERIFICATION RESULTS")

    print(f"{'Host':<8} {'Description':<25} {'Network':<20} {'Status':<12} {'Latency':<10} {'Details':<20}")
    print("-" * 95)

    for result in results:
        status = result["status"]
        latency = result["latency"]
        details = result["details"][:20]  # Truncate details for table

        print(
            f"{result['host']:<8} "
            f"{result['description']:<25} "
            f"{result['network']:<20} "
            f"{status:<12} "
            f"{latency:<10} "
            f"{details:<20}"
        )

    # Summary
    print_header("SUMMARY")
    print(f"  Total Nodes: {len(REMOTE_NODES)}")
    print(f"  Passed: {GREEN}{passed}{RESET}")
    print(f"  Failed: {RED if failed > 0 else GREEN}{failed}{RESET}")
    print(f"  Success Rate: {GREEN if failed == 0 else YELLOW}{(passed / len(REMOTE_NODES)) * 100:.0f}%{RESET}")

    if failed == 0:
        print(f"\n  {GREEN}🎯 SSH MESH FULLY OPERATIONAL{RESET}")
        print(f"  {GREEN}All nodes are accessible via password-less SSH{RESET}")
        print(f"\n  {GREEN}Usage Examples:{RESET}")
        print(f"    • ssh gtw                        (shell to Gateway)")
        print(f"    • ssh hub 'systemctl status postgresql'  (command on Hub)")
        print(f"    • ssh gpu 'python3 train.py'    (job on GPU)")
        print()
        return 0
    else:
        print(f"\n  {RED}❌ SOME NODES UNREACHABLE{RESET}")
        print(f"  {RED}Check the errors above and retry.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
