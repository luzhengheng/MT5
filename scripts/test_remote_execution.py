#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Execution Test Script (TASK #029)

Sends a test trade order from Linux strategy engine to Windows MT5 gateway
and verifies the complete round-trip communication.

Protocol: ZMQ REQ-REP (tcp://172.19.141.255:5555)
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

import zmq
from src.config import GTW_HOST, GTW_PORT, ZMQ_EXECUTION_URL, GTW_TIMEOUT_MS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_test_order(magic=20260105):
    """
    Create a test order matching Task #028 format
    
    Returns:
        dict: Order JSON following MT5-CRS protocol
    """
    return {
        "action": "BUY",
        "symbol": "EURUSD",
        "type": "MARKET",
        "volume": 0.01,
        "magic": magic,
        "timestamp": time.time(),
        "confidence": 0.65,
        "strategy": "test_remote_execution"
    }


def send_order_to_gateway(order, timeout_ms=GTW_TIMEOUT_MS, retry_count=1):
    """
    Send order to Windows MT5 gateway via ZMQ REQ-REP
    
    Args:
        order: Order dict to send
        timeout_ms: ZMQ socket timeout in milliseconds
        retry_count: Number of retry attempts
    
    Returns:
        tuple: (success: bool, response: dict, latency_ms: float, error: str)
    """
    logger.info(f"[ORDER] Connecting to gateway: {ZMQ_EXECUTION_URL}")
    logger.info(f"[ORDER] Timeout: {timeout_ms}ms")
    logger.info(f"[ORDER] Order: {json.dumps(order, indent=2)}")
    
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    
    # Configure socket
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
    socket.setsockopt(zmq.SNDTIMEO, timeout_ms)
    
    try:
        # Connect
        socket.connect(ZMQ_EXECUTION_URL)
        logger.info(f"[ZMQ] Socket connected to {ZMQ_EXECUTION_URL}")
        
        # Send order
        start_time = time.time()
        socket.send_json(order)
        logger.info(f"[ORDER] Sent {len(json.dumps(order))} bytes")
        
        # Wait for response
        logger.info(f"[WAIT] Waiting for response ({timeout_ms}ms)...")
        response = socket.recv_json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(f"[RESPONSE] Received: {json.dumps(response, indent=2)}")
        logger.info(f"[METRICS] Round-trip latency: {latency_ms:.2f}ms")
        
        socket.close()
        context.term()
        
        # Check response
        if response.get('error') is None or response.get('error') == '':
            logger.info(f"✅ [SUCCESS] Order accepted by gateway")
            logger.info(f"   Ticket: {response.get('ticket')}")
            logger.info(f"   Order ID: {response.get('order_id')}")
            return (True, response, latency_ms, None)
        else:
            error_msg = response.get('error', 'Unknown error')
            logger.warning(f"⚠️  [WARNING] Gateway returned error: {error_msg}")
            return (False, response, latency_ms, error_msg)
    
    except zmq.error.Again:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = f"Timeout waiting for response ({timeout_ms}ms)"
        logger.error(f"❌ [TIMEOUT] {error_msg}")
        logger.error(f"   Latency at timeout: {latency_ms:.2f}ms")
        socket.close()
        context.term()
        return (False, None, latency_ms, error_msg)
    
    except zmq.error.ZMQError as e:
        logger.error(f"❌ [ZMQ_ERROR] {e}")
        socket.close()
        context.term()
        return (False, None, -1, str(e))
    
    except Exception as e:
        logger.error(f"❌ [ERROR] Unexpected error: {e}")
        socket.close()
        context.term()
        return (False, None, -1, str(e))


def simulate_gateway_response():
    """
    For testing when Windows gateway is unavailable,
    return a simulated response
    
    Returns:
        dict: Simulated gateway response
    """
    return {
        "status": "FILLED",
        "ticket": 123456,
        "order_id": "EURUSD_BUY_001",
        "filled_price": 1.0543,
        "filled_volume": 0.01,
        "timestamp": time.time(),
        "error": None,
        "error_code": 0
    }


def main():
    """Main test execution"""
    print("=" * 80)
    print("REMOTE EXECUTION TEST - TASK #029")
    print("=" * 80)
    
    # Create test order
    print("\n[SETUP] Creating test order...")
    order = create_test_order()
    print(f"Order: {json.dumps(order, indent=2)}")
    
    # Attempt to send to gateway
    print("\n[TEST] Attempting to send order to Windows gateway...")
    print(f"Target: {ZMQ_EXECUTION_URL}")
    
    success, response, latency_ms, error = send_order_to_gateway(
        order,
        timeout_ms=GTW_TIMEOUT_MS
    )
    
    # Results
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("\n✅ [SUCCESS] Remote order execution verified")
        print(f"\nResponse Details:")
        print(f"  Status: {response.get('status')}")
        print(f"  Ticket: {response.get('ticket')}")
        print(f"  Order ID: {response.get('order_id')}")
        print(f"  Filled Price: {response.get('filled_price')}")
        print(f"  Filled Volume: {response.get('filled_volume')}")
        print(f"  Round-trip Latency: {latency_ms:.2f}ms")
        return 0
    else:
        print("\n❌ [FAILED] Remote execution not available")
        print(f"\nError: {error}")
        print(f"Latency: {latency_ms:.2f}ms (if measured)")
        print("\nTroubleshooting:")
        print(f"  1. Check Windows gateway is running on {GTW_HOST}:{GTW_PORT}")
        print(f"  2. Verify firewall allows port {GTW_PORT}")
        print(f"  3. Verify network connectivity: ping {GTW_HOST}")
        print(f"  4. Check MT5 EA is running on Windows terminal")
        return 1


if __name__ == "__main__":
    sys.exit(main())
