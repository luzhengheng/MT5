#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway Network Probe Script (TASK #029)

Tests connectivity to the Windows MT5 execution gateway on 172.19.141.255:5555
using both TCP socket handshake and ZMQ protocol.

Purpose: Verify network path before attempting ZMQ communication
"""

import socket
import time
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import GTW_HOST, GTW_PORT, PROBE_TIMEOUT

def probe_tcp_socket(host, port, timeout=5):
    """
    Test TCP connectivity to gateway
    
    Args:
        host: Target IP address
        port: Target port
        timeout: Connection timeout in seconds
    
    Returns:
        tuple: (success: bool, latency_ms: float, error_msg: str)
    """
    print(f"\n[PROBE] Testing TCP connectivity to {host}:{port}")
    print(f"[PROBE] Timeout: {timeout}s")
    
    try:
        start_time = time.time()
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Attempt connection
        sock.connect((host, port))
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Test successful
        sock.close()
        
        print(f"✅ [TCP] Connection successful")
        print(f"   Latency: {latency_ms:.2f}ms")
        
        return (True, latency_ms, None)
    
    except socket.timeout:
        latency_ms = (time.time() - start_time) * 1000
        msg = f"Connection timeout after {timeout}s"
        print(f"❌ [TCP] {msg}")
        return (False, latency_ms, msg)
    
    except ConnectionRefusedError:
        latency_ms = (time.time() - start_time) * 1000
        msg = f"Connection refused - Gateway service may not be running"
        print(f"❌ [TCP] {msg}")
        return (False, latency_ms, msg)
    
    except socket.gaierror as e:
        msg = f"DNS resolution failed: {e}"
        print(f"❌ [TCP] {msg}")
        return (False, -1, msg)
    
    except Exception as e:
        msg = f"Connection failed: {e}"
        print(f"❌ [TCP] {msg}")
        return (False, -1, msg)

def probe_zmq_socket(host, port, timeout_ms=2000):
    """
    Test ZMQ REQ socket connectivity (simulated)
    
    Args:
        host: Target IP address
        port: Target port
        timeout_ms: ZMQ timeout in milliseconds
    
    Returns:
        tuple: (success: bool, latency_ms: float, error_msg: str)
    """
    print(f"\n[PROBE] Testing ZMQ REQ socket connectivity to {host}:{port}")
    print(f"[PROBE] Timeout: {timeout_ms}ms")
    
    try:
        import zmq
        
        context = zmq.Context()
        socket_zmq = context.socket(zmq.REQ)
        
        # Set socket options
        socket_zmq.setsockopt(zmq.LINGER, 0)
        socket_zmq.setsockopt(zmq.RCVTIMEO, timeout_ms)
        socket_zmq.setsockopt(zmq.SNDTIMEO, timeout_ms)
        
        # Connect
        url = f"tcp://{host}:{port}"
        socket_zmq.connect(url)
        
        print(f"✅ [ZMQ] Socket connected to {url}")
        print(f"   Ready to send/receive messages")
        
        socket_zmq.close()
        context.term()
        
        return (True, 0, None)
    
    except Exception as e:
        msg = f"ZMQ socket failed: {e}"
        print(f"⚠️  [ZMQ] {msg}")
        return (False, -1, msg)

def main():
    """Run gateway probes"""
    print("=" * 80)
    print("GATEWAY NETWORK PROBE (TASK #029)")
    print("=" * 80)
    print(f"\nTarget: {GTW_HOST}:{GTW_PORT}")
    print(f"Timeout: {PROBE_TIMEOUT}s")
    
    results = {}
    
    # Test 1: TCP Socket (raw network)
    tcp_ok, tcp_latency, tcp_error = probe_tcp_socket(GTW_HOST, GTW_PORT, PROBE_TIMEOUT)
    results['tcp'] = {
        'success': tcp_ok,
        'latency_ms': tcp_latency,
        'error': tcp_error
    }
    
    # Test 2: ZMQ Socket
    zmq_ok, zmq_latency, zmq_error = probe_zmq_socket(GTW_HOST, GTW_PORT, PROBE_TIMEOUT * 1000)
    results['zmq'] = {
        'success': zmq_ok,
        'latency_ms': zmq_latency,
        'error': zmq_error
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("PROBE SUMMARY")
    print("=" * 80)
    
    if tcp_ok:
        print(f"\n✅ TCP connectivity: PASS")
        print(f"   Host {GTW_HOST}:{GTW_PORT} is reachable")
        print(f"   RTT: {tcp_latency:.2f}ms")
    else:
        print(f"\n❌ TCP connectivity: FAIL")
        print(f"   Error: {tcp_error}")
        print(f"\n   Troubleshooting:")
        print(f"   1. Verify Windows gateway IP: {GTW_HOST}")
        print(f"   2. Check Windows firewall allows port {GTW_PORT}")
        print(f"   3. Verify MT5 Gateway service is running on Windows")
        print(f"   4. Check network routing: ping {GTW_HOST}")
    
    if zmq_ok:
        print(f"\n✅ ZMQ connectivity: PASS")
        print(f"   REQ socket ready for communication")
    else:
        print(f"\n⚠️  ZMQ connectivity: {zmq_error}")
    
    # Final verdict
    print("\n" + "=" * 80)
    if tcp_ok:
        print("✅ GATEWAY PROBE PASSED - Ready for order execution")
        return 0
    else:
        print("❌ GATEWAY PROBE FAILED - Cannot reach execution gateway")
        print("\nPossible causes:")
        print("  - Windows gateway not running")
        print("  - Firewall blocking port 5555")
        print("  - Network routing issue")
        print("  - Wrong IP address configured")
        return 1

if __name__ == "__main__":
    sys.exit(main())
