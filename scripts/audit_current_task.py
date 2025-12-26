#!/usr/bin/env python3
"""
Audit Script for Task #022: ZeroMQ Fabric
==========================================

Verifies protocol integrity and client instantiation.

This audit ensures:
1. Protocol constants match Infrastructure Doc
2. Action enum contains required actions
3. Request/response constructors work correctly
4. ZmqClient can instantiate without errors
5. All critical components are present

Audit Checklist:
- [x] Protocol constants (ports, IP)
- [x] Action enum completeness
- [x] Message constructors
- [x] Client instantiation
- [x] Validation functions
"""

import sys
import os
import unittest
import logging

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress debug logs during audit
    format='%(message)s'
)

# ============================================================================
# Import Components to Audit
# ============================================================================

try:
    import zmq
except ImportError:
    print("❌ CRITICAL: pyzmq not installed")
    print("   Install: pip3 install pyzmq")
    sys.exit(1)

from src.mt5_bridge.protocol import (
    Action,
    ResponseStatus,
    ZMQ_PORT_CMD,
    ZMQ_PORT_DATA,
    GATEWAY_IP_INTERNAL,
    create_request,
    create_response,
    validate_request,
    validate_response
)

from src.mt5_bridge.zmq_client import ZmqClient


# ============================================================================
# Audit Test Suite
# ============================================================================

class TestZeroMQFabric(unittest.TestCase):
    """
    Comprehensive audit for Work Order #022.
    """

    # ========================================================================
    # Test 1: Protocol Constants
    # ========================================================================

    def test_protocol_constants(self):
        """Verify protocol constants match Infrastructure Doc."""
        print("\n[Test 1/7] Checking Protocol Constants...")

        # Port numbers
        self.assertEqual(ZMQ_PORT_CMD, 5555, "Command port must be 5555")
        self.assertEqual(ZMQ_PORT_DATA, 5556, "Data port must be 5556")

        # Gateway IP
        self.assertEqual(
            GATEWAY_IP_INTERNAL,
            "172.19.141.255",
            "Gateway IP must be 172.19.141.255"
        )

        print("  ✅ Port 5555 (Command Channel)")
        print("  ✅ Port 5556 (Data Channel)")
        print("  ✅ Gateway IP: 172.19.141.255")

    # ========================================================================
    # Test 2: Action Enum Completeness
    # ========================================================================

    def test_action_enum_completeness(self):
        """Verify Action enum contains all required actions."""
        print("\n[Test 2/7] Checking Action Enum...")

        required_actions = [
            "HEARTBEAT",
            "OPEN_ORDER",
            "CLOSE_POSITION",
            "GET_ACCOUNT_INFO",
            "GET_POSITIONS",
            "KILL_SWITCH"
        ]

        for action_name in required_actions:
            self.assertTrue(
                hasattr(Action, action_name),
                f"Action.{action_name} must exist"
            )
            print(f"  ✅ Action.{action_name}")

        # Verify KILL_SWITCH is present (critical safety feature)
        self.assertEqual(Action.KILL_SWITCH.value, "KILL_SWITCH")
        print("  ✅ KILL_SWITCH (Critical Safety Feature)")

    # ========================================================================
    # Test 3: Response Status Enum
    # ========================================================================

    def test_response_status_enum(self):
        """Verify ResponseStatus enum."""
        print("\n[Test 3/7] Checking ResponseStatus Enum...")

        self.assertTrue(hasattr(ResponseStatus, "SUCCESS"))
        self.assertTrue(hasattr(ResponseStatus, "ERROR"))
        self.assertTrue(hasattr(ResponseStatus, "PENDING"))

        print("  ✅ ResponseStatus.SUCCESS")
        print("  ✅ ResponseStatus.ERROR")
        print("  ✅ ResponseStatus.PENDING")

    # ========================================================================
    # Test 4: Request Constructor
    # ========================================================================

    def test_create_request(self):
        """Verify request constructor."""
        print("\n[Test 4/7] Checking Request Constructor...")

        # Create request without payload
        req1 = create_request(Action.HEARTBEAT)
        self.assertIn("req_id", req1)
        self.assertIn("timestamp", req1)
        self.assertIn("action", req1)
        self.assertIn("payload", req1)
        self.assertEqual(req1["action"], "HEARTBEAT")
        self.assertIsInstance(req1["payload"], dict)

        # Create request with payload
        payload = {"symbol": "EURUSD.s", "volume": 0.01}
        req2 = create_request(Action.OPEN_ORDER, payload)
        self.assertEqual(req2["action"], "OPEN_ORDER")
        self.assertEqual(req2["payload"]["symbol"], "EURUSD.s")

        print("  ✅ create_request(Action.HEARTBEAT)")
        print("  ✅ create_request(Action.OPEN_ORDER, payload)")
        print(f"  ✅ req_id generated: {req1['req_id'][:8]}...")
        print(f"  ✅ timestamp: {req1['timestamp']}")

    # ========================================================================
    # Test 5: Response Constructor
    # ========================================================================

    def test_create_response(self):
        """Verify response constructor."""
        print("\n[Test 5/7] Checking Response Constructor...")

        # Success response
        resp1 = create_response(
            req_id="test-123",
            status=ResponseStatus.SUCCESS,
            data={"ticket": 12345}
        )
        self.assertEqual(resp1["req_id"], "test-123")
        self.assertEqual(resp1["status"], "SUCCESS")
        self.assertEqual(resp1["data"]["ticket"], 12345)
        self.assertIsNone(resp1["error"])

        # Error response
        resp2 = create_response(
            req_id="test-456",
            status=ResponseStatus.ERROR,
            error="Connection failed"
        )
        self.assertEqual(resp2["status"], "ERROR")
        self.assertEqual(resp2["error"], "Connection failed")

        print("  ✅ create_response(SUCCESS)")
        print("  ✅ create_response(ERROR)")

    # ========================================================================
    # Test 6: Validation Functions
    # ========================================================================

    def test_validation_functions(self):
        """Verify validation functions."""
        print("\n[Test 6/7] Checking Validation Functions...")

        # Valid request
        valid_req = create_request(Action.HEARTBEAT)
        self.assertTrue(validate_request(valid_req))

        # Invalid request (missing fields)
        invalid_req = {"action": "TEST"}
        self.assertFalse(validate_request(invalid_req))

        # Valid response
        valid_resp = create_response("test", ResponseStatus.SUCCESS)
        self.assertTrue(validate_response(valid_resp))

        # Invalid response (missing fields)
        invalid_resp = {"status": "SUCCESS"}
        self.assertFalse(validate_response(invalid_resp))

        print("  ✅ validate_request(valid_req) = True")
        print("  ✅ validate_request(invalid_req) = False")
        print("  ✅ validate_response(valid_resp) = True")
        print("  ✅ validate_response(invalid_resp) = False")

    # ========================================================================
    # Test 7: Client Instantiation
    # ========================================================================

    def test_client_instantiation(self):
        """Verify ZmqClient can instantiate without errors."""
        print("\n[Test 7/7] Checking ZmqClient Instantiation...")

        try:
            # Instantiate client (use localhost to avoid network issues)
            # This tests structural integrity, not actual connectivity
            client = ZmqClient(host="127.0.0.1", req_port=5555, sub_port=5556)

            # Verify attributes
            self.assertIsInstance(client.context, zmq.Context)
            self.assertIsInstance(client.req_socket, zmq.Socket)
            self.assertIsInstance(client.sub_socket, zmq.Socket)
            self.assertEqual(client.host, "127.0.0.1")
            self.assertEqual(client.timeout_ms, 2000)

            print("  ✅ ZmqClient instantiated successfully")
            print(f"  ✅ Context type: {type(client.context).__name__}")
            print(f"  ✅ REQ socket type: {client.req_socket.socket_type}")
            print(f"  ✅ SUB socket type: {client.sub_socket.socket_type}")
            print(f"  ✅ Timeout: {client.timeout_ms}ms")

            # Cleanup
            client.close()
            print("  ✅ Client closed successfully")

        except Exception as e:
            self.fail(f"Client instantiation failed: {e}")


# ============================================================================
# Main Audit Execution
# ============================================================================

def main():
    """Run the audit suite."""
    print("=" * 70)
    print("🛡️  AUDIT: Work Order #022 - ZeroMQ Fabric")
    print("=" * 70)
    print()
    print("Components under audit:")
    print("  1. src/mt5_bridge/protocol.py")
    print("  2. src/mt5_bridge/zmq_client.py")
    print("  3. src/gateway/zmq_service.py")
    print()

    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    suite = unittest.makeSuite(TestZeroMQFabric)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ AUDIT PASSED - All checks successful")
        print("=" * 70)
        print()
        print("Verified Components:")
        print("  ✅ Protocol constants (ports 5555/5556, IP 172.19.141.255)")
        print("  ✅ Action enum (6 actions including KILL_SWITCH)")
        print("  ✅ ResponseStatus enum (SUCCESS/ERROR/PENDING)")
        print("  ✅ Request constructor (with UUID and timestamp)")
        print("  ✅ Response constructor (with error handling)")
        print("  ✅ Validation functions (request/response)")
        print("  ✅ ZmqClient instantiation (context, sockets, timeout)")
        print()
        print("Next Steps:")
        print("  1. Install pyzmq on Windows Gateway: pip install pyzmq")
        print("  2. Deploy src/gateway/zmq_service.py to Windows")
        print("  3. Test heartbeat: client.check_heartbeat()")
        print("  4. Run: python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print("❌ AUDIT FAILED")
        print("=" * 70)
        print()
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
