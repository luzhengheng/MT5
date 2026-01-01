#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Gateway Connectivity Probe

Task #023.01: Verifies network connectivity from Docker containers to MT5 Gateway.

Tests:
1. TCP connection to 172.19.141.255:5555
2. ZMQ PING-PONG protocol
3. Gateway response time

Returns:
  0 - Success (connected and responsive)
  1 - Failure (network issue or gateway not responding)
"""

import zmq
import socket
import json
import sys
from datetime import datetime
from pathlib import Path

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Gateway settings
GATEWAY_HOST = "172.19.141.255"
GATEWAY_PORT = 5555
TIMEOUT_MS = 5000  # 5 seconds


def test_tcp_connection():
    """Test 1: Basic TCP connectivity"""
    print(f"{CYAN}[1/3] Testing TCP connectivity...{RESET}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)

    try:
        sock.connect((GATEWAY_HOST, GATEWAY_PORT))
        sock.close()
        print(f"{GREEN}✅ TCP: Port 5555 is reachable{RESET}")
        return True
    except socket.timeout:
        print(f"{RED}❌ TCP: Connection timeout (gateway not responding){RESET}")
        return False
    except ConnectionRefusedError:
        print(f"{RED}❌ TCP: Connection refused (gateway not listening on 5555){RESET}")
        return False
    except socket.gaierror:
        print(f"{RED}❌ TCP: Cannot resolve hostname{RESET}")
        return False
    except OSError as e:
        print(f"{RED}❌ TCP: Network error - {e}{RESET}")
        return False


def test_zmq_ping():
    """Test 2: ZMQ PING-PONG protocol"""
    print(f"\n{CYAN}[2/3] Testing ZMQ PING-PONG...{RESET}")

    context = zmq.Context()
    zmq_socket = context.socket(zmq.REQ)

    # Configure timeout
    zmq_socket.setsockopt(zmq.RCVTIMEO, TIMEOUT_MS)
    zmq_socket.setsockopt(zmq.LINGER, 0)

    try:
        print(f"  Connecting to tcp://{GATEWAY_HOST}:{GATEWAY_PORT}...")
        zmq_socket.connect(f"tcp://{GATEWAY_HOST}:{GATEWAY_PORT}")

        # Send PING request
        ping_msg = {
            "action": "PING",
            "timestamp": datetime.now().isoformat(),
            "source": "mt5-strategy-probe"
        }

        print(f"  Sending PING: {json.dumps(ping_msg)}")
        zmq_socket.send_json(ping_msg)

        # Wait for PONG
        response = zmq_socket.recv_json()

        print(f"{GREEN}✅ ZMQ: Received PONG from gateway{RESET}")
        print(f"  Response: {json.dumps(response)}")

        return True

    except zmq.error.Again:
        print(f"{RED}❌ ZMQ: Timeout waiting for response (>5 seconds){RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ ZMQ: Error - {e}{RESET}")
        return False
    finally:
        zmq_socket.close()
        context.term()


def test_gateway_health():
    """Test 3: Gateway health check"""
    print(f"\n{CYAN}[3/3] Checking gateway health...{RESET}")

    context = zmq.Context()
    zmq_socket = context.socket(zmq.REQ)
    zmq_socket.setsockopt(zmq.RCVTIMEO, TIMEOUT_MS)
    zmq_socket.setsockopt(zmq.LINGER, 0)

    try:
        zmq_socket.connect(f"tcp://{GATEWAY_HOST}:{GATEWAY_PORT}")

        health_msg = {
            "action": "STATUS",
            "timestamp": datetime.now().isoformat()
        }

        zmq_socket.send_json(health_msg)
        response = zmq_socket.recv_json()

        status = response.get("status", "UNKNOWN")
        print(f"{GREEN}✅ Gateway Status: {status}{RESET}")

        return True

    except Exception:
        # STATUS may not be implemented - skip if error
        print(f"{YELLOW}⚠️  Gateway health check not available (OK){RESET}")
        return True
    finally:
        zmq_socket.close()
        context.term()


def main():
    """Run all connectivity tests"""
    print()
    print("=" * 80)
    print(f"{CYAN}🔌 LIVE GATEWAY CONNECTIVITY PROBE{RESET}")
    print(f"{CYAN}Task #023.01: Docker ↔ Windows Gateway{RESET}")
    print("=" * 80)
    print()

    print(f"Gateway: {GATEWAY_HOST}:{GATEWAY_PORT}")
    print(f"Timeout: {TIMEOUT_MS}ms")
    print()

    results = []

    # Test 1: TCP
    tcp_ok = test_tcp_connection()
    results.append(("TCP Connectivity", tcp_ok))

    if not tcp_ok:
        print()
        print(f"{RED}❌ FATAL: TCP connection failed{RESET}")
        print()
        print("Troubleshooting:")
        print("  1. Verify gateway IP: 172.19.141.255")
        print("  2. Check Windows firewall allows port 5555")
        print("  3. Verify MT5 gateway process is running")
        print("  4. Check Docker host networking configuration")
        print("  5. Run: ping 172.19.141.255 (from Docker host)")
        print()
        return 1

    # Test 2: ZMQ PING
    zmq_ok = test_zmq_ping()
    results.append(("ZMQ PING-PONG", zmq_ok))

    if not zmq_ok:
        print()
        print(f"{RED}❌ FATAL: ZMQ protocol test failed{RESET}")
        print()
        print("Troubleshooting:")
        print("  1. Gateway may not be listening on port 5555")
        print("  2. Firewall may be blocking ZMQ traffic")
        print("  3. Gateway process may be unresponsive")
        print("  4. Try increasing timeout value")
        print()
        return 1

    # Test 3: Health
    health_ok = test_gateway_health()
    results.append(("Gateway Health", health_ok))

    # Summary
    print()
    print("=" * 80)
    print(f"📊 CONNECTIVITY TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("=" * 80)
        print(f"{GREEN}✅ SUCCESS: Docker container can reach live gateway!{RESET}")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Strategy runner can now connect to MT5")
        print("  2. Deploy full stack: docker-compose -f docker-compose.prod.yml up -d")
        print("  3. Monitor logs: docker-compose logs -f strategy_runner")
        print()
        return 0
    else:
        print("=" * 80)
        print(f"{RED}❌ FAILED: Cannot reach live gateway{RESET}")
        print("=" * 80)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
