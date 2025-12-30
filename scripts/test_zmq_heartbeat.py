#!/usr/bin/env python3
"""
Task #011.25: ZMQ Heartbeat Test
Test connectivity to GTW ZMQ Gateway by sending HEARTBEAT request
"""

import zmq
import json
import sys
import time

# GTW ZMQ REQ endpoint
GTW_ZMQ_REQ = "tcp://172.19.141.255:5555"

def test_heartbeat():
    """Send HEARTBEAT to GTW and print response."""
    print(f"🔌 Connecting to GTW ZMQ REQ: {GTW_ZMQ_REQ}")

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout

    try:
        socket.connect(GTW_ZMQ_REQ)
        print(f"✅ Connected to {GTW_ZMQ_REQ}")

        # Send HEARTBEAT request (protocol v1.0 format)
        request = {
            "action": "HEARTBEAT",
            "req_id": f"hb-{int(time.time())}",
            "timestamp": time.time(),
            "payload": {}
        }
        print(f"\n📤 Sending request: {json.dumps(request, indent=2)}")
        socket.send_json(request)

        # Receive response
        print(f"⏳ Waiting for response (timeout: 5s)...")
        response = socket.recv_json()

        print(f"\n📥 Received response:")
        print(json.dumps(response, indent=2))

        # Validate response
        if response.get("status") == "SUCCESS":
            print(f"\n✅ Heartbeat successful!")
            print(f"   Gateway is alive and responding")
            if response.get("data"):
                print(f"   MT5 Account: {response['data'].get('account', 'N/A')}")
                print(f"   Server: {response['data'].get('server', 'N/A')}")
            return True
        elif response.get("status") == "ERROR":
            print(f"\n⚠️  Gateway returned error: {response.get('error', 'Unknown')}")
            return False
        else:
            print(f"\n⚠️  Unexpected response format")
            return False

    except zmq.error.Again:
        print(f"\n❌ Timeout: No response from gateway (5s)")
        print(f"   Gateway may not be running or ZMQ port blocked")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    finally:
        socket.close()
        context.term()

if __name__ == "__main__":
    success = test_heartbeat()
    sys.exit(0 if success else 1)
