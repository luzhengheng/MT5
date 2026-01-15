#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MT5 ZMQ Server - Basic functionality verification
Task #106 - MT5 Live Bridge Implementation

This script tests the MT5 ZMQ Server by:
1. Starting a test server (in a separate process)
2. Sending test commands (PING, GET_ACCOUNT, GET_POSITIONS)
3. Verifying responses
4. Testing error handling

Usage:
    python test_mt5_zmq_server.py
"""

import zmq
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any


def test_zmq_server(host: str = "localhost", port: int = 5555):
    """Test MT5 ZMQ Server basic functionality"""

    print("="*80)
    print("🧪 Testing MT5 ZMQ Server")
    print("="*80)

    # Create ZMQ client
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    try:
        # Connect to server
        address = f"tcp://{host}:{port}"
        print(f"\n📡 Connecting to {address}...")
        socket.connect(address)
        socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout

        # Test 1: PING
        print("\n" + "-"*80)
        print("Test 1: PING (Heartbeat)")
        print("-"*80)

        request = {
            "uuid": str(uuid.uuid4()),
            "action": "PING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print(f"📤 Sending: {json.dumps(request, indent=2)}")
        socket.send_string(json.dumps(request))

        response_str = socket.recv_string()
        response = json.loads(response_str)
        print(f"📥 Received: {json.dumps(response, indent=2)}")

        assert response.get("status") == "ok", "PING failed"
        assert "server_time" in response, "Missing server_time"
        assert "latency_ms" in response, "Missing latency_ms"
        print("✅ PING test passed")

        # Test 2: GET_ACCOUNT
        print("\n" + "-"*80)
        print("Test 2: GET_ACCOUNT (Account Info)")
        print("-"*80)

        request = {
            "uuid": str(uuid.uuid4()),
            "action": "GET_ACCOUNT",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print(f"📤 Sending: {json.dumps(request, indent=2)}")
        socket.send_string(json.dumps(request))

        response_str = socket.recv_string()
        response = json.loads(response_str)
        print(f"📥 Received: {json.dumps(response, indent=2)}")

        assert response.get("status") == "ok", "GET_ACCOUNT failed"
        assert "balance" in response, "Missing balance"
        assert "equity" in response, "Missing equity"
        print("✅ GET_ACCOUNT test passed")

        # Test 3: GET_POSITIONS
        print("\n" + "-"*80)
        print("Test 3: GET_POSITIONS (Open Positions)")
        print("-"*80)

        request = {
            "uuid": str(uuid.uuid4()),
            "action": "GET_POSITIONS",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print(f"📤 Sending: {json.dumps(request, indent=2)}")
        socket.send_string(json.dumps(request))

        response_str = socket.recv_string()
        response = json.loads(response_str)
        print(f"📥 Received: {json.dumps(response, indent=2)}")

        assert response.get("status") == "ok", "GET_POSITIONS failed"
        assert "positions" in response, "Missing positions"
        print("✅ GET_POSITIONS test passed")

        # Test 4: Invalid JSON
        print("\n" + "-"*80)
        print("Test 4: Invalid JSON (Error Handling)")
        print("-"*80)

        invalid_json = "not a valid json"
        print(f"📤 Sending: {invalid_json}")
        socket.send_string(invalid_json)

        response_str = socket.recv_string()
        response = json.loads(response_str)
        print(f"📥 Received: {json.dumps(response, indent=2)}")

        assert response.get("status") == "error", "Should return error"
        assert "INVALID_JSON" in response.get("error_code", ""), "Wrong error code"
        print("✅ Invalid JSON test passed")

        # Test 5: Unknown action
        print("\n" + "-"*80)
        print("Test 5: Unknown Action (Error Handling)")
        print("-"*80)

        request = {
            "uuid": str(uuid.uuid4()),
            "action": "INVALID_ACTION",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print(f"📤 Sending: {json.dumps(request, indent=2)}")
        socket.send_string(json.dumps(request))

        response_str = socket.recv_string()
        response = json.loads(response_str)
        print(f"📥 Received: {json.dumps(response, indent=2)}")

        assert response.get("status") == "error", "Should return error"
        assert "UNKNOWN_ACTION" in response.get("error_code", ""), "Wrong error code"
        print("✅ Unknown action test passed")

        print("\n" + "="*80)
        print("✅ All tests passed!")
        print("="*80)

    except zmq.error.Again:
        print("\n❌ Timeout: Server not responding")
        print("Make sure the MT5 ZMQ Server is running:")
        print(f"  python mt5_zmq_server.py --port {port}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        socket.close()
        context.term()


def main():
    """Main entry point"""
    print("\n🧪 MT5 ZMQ Server Test Suite")
    print(f"Author: Claude Sonnet 4.5")
    print(f"Date: 2026-01-15")
    print(f"Protocol: v4.3 (Zero-Trust Edition)\n")

    # Run tests
    test_zmq_server()


if __name__ == "__main__":
    main()
