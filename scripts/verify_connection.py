#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS Live Connection Test (Task #004)
Verifies connectivity to Windows MT5 Server at 172.19.141.255:5555
via ZeroMQ REQ-REP socket pattern.

Protocol: v3.9 (Double-Gated Audit)
Status: Live Connection Test
"""

import os
import sys
import time
import zmq

# Hardcoded target configuration (Task #004 requirement)
# Target: Windows Gateway (GTW) MT5 Server
MT5_HOST = "172.19.141.255"
MT5_PORT = 5555
TIMEOUT_MS = 5000  # 5 second timeout


def verify_connection():
    """
    Verify live connection to MT5 Server using ZeroMQ REQ-REP pattern.

    Returns:
        bool: True if connection successful and "OK_FROM_MT5" received, False otherwise
    """
    print("=" * 60)
    print("MT5-CRS Live Connection Verification (Task #004)")
    print("=" * 60)
    print()

    print("[Config]")
    print(f"  MT5_HOST: {MT5_HOST}")
    print(f"  MT5_PORT: {MT5_PORT}")
    print(f"  Timeout: {TIMEOUT_MS}ms")
    print()

    context = None
    socket = None

    try:
        # Create ZeroMQ context and REQ socket
        context = zmq.Context()
        socket = context.socket(zmq.REQ)

        # Set socket options for timeout protection
        socket.setsockopt(zmq.RCVTIMEO, TIMEOUT_MS)
        socket.setsockopt(zmq.SNDTIMEO, TIMEOUT_MS)

        # Build server address string
        server_address = f"tcp://{MT5_HOST}:{MT5_PORT}"

        # Attempt connection
        print(f"[*] Connecting to MT5 Server at {server_address}...")
        socket.connect(server_address)
        print(f"[✓] Connected to {server_address}")
        print()

        # Send test message
        test_message = "Hello"
        print(f"[*] Sending test message '{test_message}'...")
        socket.send_string(test_message)

        # Receive response with timeout protection
        print(f"[*] Waiting for response (timeout: {TIMEOUT_MS}ms)...")
        start_time = time.time()
        response = socket.recv_string()
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"[✓] Received reply: {response}")
        print(f"[✓] Round-trip time: {elapsed_ms:.2f}ms")
        print()

        # Verify response is "OK_FROM_MT5"
        if response == "OK_FROM_MT5":
            print("[✓] Connection test PASSED")
            print("    MT5 Server responded with correct handshake")
            return True
        else:
            print(f"[✘] Unexpected response: '{response}'")
            print(f"    Expected: 'OK_FROM_MT5'")
            return False

    except zmq.error.Again:
        print("[✗] Connection timeout - no response from MT5 Server")
        print(f"    Waited {TIMEOUT_MS}ms without receiving response")
        print()
        print("    Troubleshooting:")
        print("    1. Check if MT5 Server is running on Windows GTW")
        print("    2. Verify firewall allows port 5555")
        print("    3. Confirm network connectivity: ping 172.19.141.255")
        return False

    except zmq.error.ZMQError as e:
        if "Connection refused" in str(e):
            print(f"[✗] Connection refused: {e}")
            print()
            print("    Troubleshooting:")
            print("    1. MT5 Server may not be running")
            print("    2. Port 5555 may be blocked by firewall")
            print("    3. Network may be unreachable")
        else:
            print(f"[✗] ZeroMQ Error: {e}")
        return False

    except Exception as e:
        print(f"[✗] Unexpected error: {e}")
        return False

    finally:
        # Cleanup resources
        if socket:
            socket.close()
        if context:
            context.term()
        print()

    return False


if __name__ == "__main__":
    success = verify_connection()

    # Exit with appropriate code for audit system
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
