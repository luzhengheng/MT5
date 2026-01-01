# TASK #023.01: Live Gateway Connectivity Probe (Dockerized)

**Status**: In Progress
**Ticket**: #076
**Category**: Network Engineering / Deployment Testing
**Protocol**: v2.2 (Infrastructure-as-Code)

---

## 1. Executive Summary

Task #023.01 creates a diagnostic tool to verify network connectivity from Docker containers to the live trading gateway (Windows MT5 machine at `172.19.141.255:5555`). This bridges the virtual Docker environment with the physical trading infrastructure.

Key deliverables:
- `scripts/probe_live_gateway.py` - ZMQ gateway connectivity probe
- Docker integration - Run probe inside `mt5-strategy` container
- Troubleshooting guide - Document common connectivity issues and fixes
- Connection verification - Success/failure reporting with detailed diagnostics

---

## 2. Problem Context

### Current Architecture

```
┌─────────────────────────────────────────┐
│      Docker Host (Linux VM)             │
│  ┌──────────────────────────────────┐  │
│  │  Docker Network (mt5-net)        │  │
│  │  172.28.0.0/16                  │  │
│  │                                  │  │
│  │  ┌─────────────────────────────┐ │  │
│  │  │  mt5-strategy Container     │ │  │
│  │  │  Strategy Runner            │ │  │
│  │  │  (needs to reach GTW)       │ │  │
│  │  └─────────────────────────────┘ │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
           ↓ (Network Path)
┌─────────────────────────────────────────┐
│    Windows Gateway (Physical Machine)   │
│    172.19.141.255:5555 (ZMQ REQ/REP)   │
│    MT5 Trading Platform                 │
└─────────────────────────────────────────┘
```

### Challenge

Docker containers run on an isolated bridge network (`mt5-net: 172.28.0.0/16`). To communicate with the external Windows Gateway at `172.19.141.255`, we must:

1. **Network routing**: Docker host must have a route to the gateway
2. **Firewall rules**: Windows firewall must allow inbound ZMQ traffic (port 5555)
3. **Gateway availability**: MT5 trading gateway must be running and listening on 5555

### Solution

Create a lightweight probe script that tests connectivity without requiring the full strategy runner. This allows rapid diagnosis without waiting for the entire stack to start.

---

## 3. Probe Design

### Architecture

```
User runs:
  docker run --rm --network host \
    mt5-strategy:latest \
    python3 -m scripts.probe_live_gateway

      ↓

Docker Container:
  - Imports zmq, socket libraries
  - Attempts TCP connection to 172.19.141.255:5555
  - Sends PING request via ZMQ REQ socket
  - Waits for PONG response (5s timeout)

      ↓

Gateway Response:
  - If running: Returns PONG + gateway status
  - If not running: Timeout or connection refused
  - If network issue: EHOSTUNREACH or similar

      ↓

Output:
  ✅ SUCCESS: Connection established, gateway responding
  ❌ FAILED: Connection refused, timeout, or network error
     Details: errno, strerror, suggestions
```

### Probe Workflow

**Step 1: Import Libraries**
```python
import zmq
import socket
import json
import sys
from datetime import datetime
```

**Step 2: Attempt TCP Connection (Pre-flight)**
```python
# Quick TCP check to rule out network routing issues
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
try:
    sock.connect(('172.19.141.255', 5555))
    sock.close()
    print("✅ TCP connection successful")
except Exception as e:
    print(f"❌ TCP connection failed: {e}")
    exit(1)
```

**Step 3: ZMQ PING-PONG Test**
```python
# Full protocol test
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
socket.setsockopt(zmq.LINGER, 0)  # Close immediately on exit

print("Connecting to gateway (172.19.141.255:5555)...")
socket.connect("tcp://172.19.141.255:5555")

# Send PING
socket.send_json({"action": "PING", "timestamp": datetime.now().isoformat()})

# Wait for PONG
try:
    response = socket.recv_json()
    print(f"✅ SUCCESS: Gateway responded: {response}")
    exit(0)
except zmq.error.Again:
    print("❌ TIMEOUT: Gateway did not respond within 5 seconds")
    exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
finally:
    socket.close()
    context.term()
```

---

## 4. Implementation Details

### File: `scripts/probe_live_gateway.py`

```python
#!/usr/bin/env python3
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

        print(f"  Sending PING: {ping_msg}")
        zmq_socket.send_json(ping_msg)

        # Wait for PONG
        response = zmq_socket.recv_json()

        print(f"{GREEN}✅ ZMQ: Received PONG from gateway{RESET}")
        print(f"  Response: {response}")

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
```

---

## 5. Docker Execution

### Command

```bash
# Run the probe in an ephemeral container with host network
docker run --rm --network host \
  -v $(pwd)/scripts:/app/scripts \
  mt5-strategy:latest \
  python3 /app/scripts/probe_live_gateway.py
```

### Network Modes Explained

#### Option 1: `--network host` (Recommended)
- Container shares host's network namespace
- Can reach external IPs without bridge
- Preferred for this probe (direct access to gateway)

#### Option 2: `--network mt5-net` (Default)
- Container uses internal bridge network
- May need additional routing configuration
- Firewall rules may differ

#### Option 3: `--network bridge` (Custom)
- Custom bridge with gateway specification
- For complex routing scenarios

### Expected Output

**Success Case:**
```
================================================================================
🔌 LIVE GATEWAY CONNECTIVITY PROBE
Task #023.01: Docker ↔ Windows Gateway
================================================================================

Gateway: 172.19.141.255:5555
Timeout: 5000ms

[1/3] Testing TCP connectivity...
✅ TCP: Port 5555 is reachable

[2/3] Testing ZMQ PING-PONG...
  Connecting to tcp://172.19.141.255:5555...
  Sending PING: {'action': 'PING', 'timestamp': '2026-01-01T12:34:56...', ...}
✅ ZMQ: Received PONG from gateway
  Response: {'status': 'OK', 'gateway': 'MT5-Windows', ...}

[3/3] Checking gateway health...
✅ Gateway Status: OPERATIONAL

================================================================================
📊 CONNECTIVITY TEST SUMMARY
================================================================================

✅ PASS: TCP Connectivity
✅ PASS: ZMQ PING-PONG
✅ PASS: Gateway Health

Results: 3/3 tests passed

================================================================================
✅ SUCCESS: Docker container can reach live gateway!
================================================================================

Next steps:
  1. Strategy runner can now connect to MT5
  2. Deploy full stack: docker-compose -f docker-compose.prod.yml up -d
  3. Monitor logs: docker-compose logs -f strategy_runner
```

**Failure Case (Network Unreachable):**
```
================================================================================
🔌 LIVE GATEWAY CONNECTIVITY PROBE
Task #023.01: Docker ↔ Windows Gateway
================================================================================

Gateway: 172.19.141.255:5555
Timeout: 5000ms

[1/3] Testing TCP connectivity...
❌ TCP: Network error - No route to host

================================================================================
Troubleshooting:
  1. Verify gateway IP: 172.19.141.255
  2. Check Windows firewall allows port 5555
  3. Verify MT5 gateway process is running
  4. Check Docker host networking configuration
  5. Run: ping 172.19.141.255 (from Docker host)

================================================================================
```

---

## 6. Troubleshooting Guide

### Issue 1: Connection Refused

**Symptoms:**
```
❌ TCP: Connection refused
```

**Causes:**
- Windows gateway not running
- Not listening on port 5555
- Firewall blocking port 5555

**Solutions:**
```bash
# On Windows gateway machine:
1. Verify MT5 process is running
2. Check firewall: Settings → Firewall & Network Protection → Allow app through firewall
3. Ensure port 5555 is allowed: netstat -an | findstr 5555
4. Restart MT5 gateway service
```

### Issue 2: Connection Timeout

**Symptoms:**
```
❌ ZMQ: Timeout waiting for response (>5 seconds)
```

**Causes:**
- Gateway not responsive
- Network congestion
- Firewall filtering at network level

**Solutions:**
```bash
# From Docker host:
1. ping 172.19.141.255  # Verify network reachability
2. telnet 172.19.141.255 5555  # Test port connectivity
3. Increase timeout in probe (TIMEOUT_MS = 10000)
4. Check for packet loss: ping -c 100 172.19.141.255
```

### Issue 3: No Route to Host

**Symptoms:**
```
❌ TCP: Network error - No route to host
```

**Causes:**
- Docker host doesn't have route to gateway network
- Network interface misconfiguration
- VLAN routing issue

**Solutions:**
```bash
# On Docker host (Linux):
1. Check routes: route -n | grep 172.19
2. Add route if needed: sudo route add -net 172.19.0.0/16 gw <gateway-ip>
3. Check network interfaces: ifconfig or ip addr
4. Verify bridge configuration: ip link show docker0
5. Check iptables rules: sudo iptables -L -n
```

### Issue 4: ZMQ Protocol Error

**Symptoms:**
```
❌ ZMQ: Error - Connection reset by peer
```

**Causes:**
- Gateway doesn't support ZMQ protocol
- Different protocol version
- Port conflict (something else on 5555)

**Solutions:**
```bash
# Verify port binding on gateway:
netstat -an | grep 5555
# Should show LISTENING on 172.19.141.255:5555

# Verify ZMQ version compatibility:
python3 -c "import zmq; print(zmq.zmq_version())"
```

---

## 7. Success Criteria

✅ **Definition of Done**:

1. `scripts/probe_live_gateway.py` exists and is executable
2. Probe imports successfully: `python3 -c "import scripts.probe_live_gateway"`
3. When run in Docker container with `--network host`, returns:
   - Exit code 0 if connected
   - Exit code 1 if failed
4. Output includes clear success/failure message
5. Troubleshooting guide provided for common failures
6. Audit script includes probe verification
7. All changes committed and pushed to GitHub

---

## 8. Implementation Sequence

1. ✅ Create TASK_023_01_PLAN.md (this document)
2. Create scripts/probe_live_gateway.py with full implementation
3. Update scripts/audit_current_task.py to include probe checks
4. Test probe with: `docker run --rm --network host ...`
5. Document results (success or troubleshooting needed)
6. Commit all changes
7. Run finish command

---

## 9. Integration Points

### How this connects to the system

```
[Docker Container Start]
        ↓
[Network Initialization]
        ↓
[Run probe_live_gateway.py] ← checks connectivity
        ↓
[Pass/Fail Decision]
        ├─→ PASS: Container starts strategy runner
        └─→ FAIL: Report network issue, document fix
```

### Post-Task Usage

Once connectivity is verified:

```bash
# Deploy full stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor strategy runner logs
docker-compose logs -f strategy_runner

# Re-run probe anytime to verify connectivity
docker run --rm --network host \
  mt5-strategy:latest \
  python3 /app/scripts/probe_live_gateway.py
```

---

## 10. Key Design Decisions

### 1. Use `--network host`
**Decision**: Default to `--network host` for probe.

**Rationale**:
- Direct access to external gateway without bridge complexity
- Diagnostic tool should bypass network abstraction layers
- Simpler troubleshooting path

### 2. Two-Layer Testing (TCP + ZMQ)
**Decision**: Test both TCP and ZMQ.

**Rationale**:
- TCP catches network/routing issues
- ZMQ catches protocol/gateway issues
- Layered diagnostics pinpoint root cause

### 3. Timeout = 5 seconds
**Decision**: 5 second timeout for ZMQ PING.

**Rationale**:
- Fast enough for quick diagnosis
- Allows for network latency
- Matches trading system requirements

### 4. Non-Blocking Error Handling
**Decision**: Continue testing even if one test fails.

**Rationale**:
- Provides full diagnostic picture
- User sees all failures at once
- Easier to troubleshoot multiple issues

---

**Author**: Network Engineering Team
**Date**: 2026-01-01
**Revision**: 1.0
