#!/usr/bin/env python3
"""
Task #012.01: Market Data Subscription & Verification
====================================================

Subscribe to MT5 Gateway's ZMQ PUB socket (port 5556) and verify
live market data (tick information: Symbol, Bid, Ask, Spread, etc.)

Usage:
    python3 scripts/test_market_data.py              # Default: 30 second test
    python3 scripts/test_market_data.py --duration 60  # Custom duration
    python3 scripts/test_market_data.py --host <ip>   # Different host
    python3 scripts/test_market_data.py --port 5556    # Different port
"""

import zmq
import json
import time
import argparse
import sys
from datetime import datetime

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print formatted section header"""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def subscribe_to_market_data(host: str = "127.0.0.1", port: int = 5556, duration: int = 30):
    """
    Subscribe to ZMQ market data and print ticks for specified duration.

    Args:
        host: ZMQ server host (default: 127.0.0.1 for local tunnel)
        port: ZMQ server port (default: 5556 for PUB socket)
        duration: How long to listen (seconds)
    """
    print_header("Task #012.01: Market Data Subscription")
    print(f"Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Duration: {duration}s")
    print(f"  Protocol: ZMQ SUB socket\n")

    # Create ZMQ context and socket
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    # Set socket options
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second receive timeout
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    # Connection string
    connection_string = f"tcp://{host}:{port}"
    print(f"{BLUE}[Step 1]{RESET} Connecting to {connection_string}...\n")

    try:
        socket.connect(connection_string)
        print(f"   {GREEN}✅ Connected successfully{RESET}\n")

    except Exception as e:
        print(f"   {RED}❌ Connection failed: {e}{RESET}")
        return False

    # Receive market data
    print(f"{BLUE}[Step 2]{RESET} Receiving market data stream...\n")
    print(f"   {YELLOW}Listening for ticks (timeout: 5s per message)...{RESET}\n")

    start_time = time.time()
    tick_count = 0
    tick_types = {}
    symbols = set()
    min_bid = float('inf')
    max_bid = float('-inf')
    error_count = 0

    # Column headers
    print(f"   {'Time':<12} {'Symbol':<12} {'Bid':<12} {'Ask':<12} {'Spread':<12} {'Volume':<12}")
    print(f"   {'-' * 12} {'-' * 12} {'-' * 12} {'-' * 12} {'-' * 12} {'-' * 12}")

    try:
        while time.time() - start_time < duration:
            try:
                # Receive JSON message
                msg = socket.recv_json()

                tick_count += 1

                # Extract fields
                symbol = msg.get("symbol", "N/A")
                bid = msg.get("bid", 0.0)
                ask = msg.get("ask", 0.0)
                spread = ask - bid if bid > 0 else 0.0
                volume = msg.get("volume", 0)
                msg_type = msg.get("type", "tick")

                # Track stats
                symbols.add(symbol)
                if bid > 0:
                    min_bid = min(min_bid, bid)
                    max_bid = max(max_bid, bid)
                tick_types[msg_type] = tick_types.get(msg_type, 0) + 1

                # Print tick
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"   {timestamp:<12} {symbol:<12} {bid:<12.5f} {ask:<12.5f} {spread:<12.5f} {volume:<12}")

            except zmq.error.Again:
                # Timeout occurred - no message received
                elapsed = time.time() - start_time
                remaining = duration - elapsed
                if remaining > 0:
                    print(f"   {YELLOW}⏳ Waiting for data... ({remaining:.0f}s remaining){RESET}")
                continue

            except json.JSONDecodeError as e:
                error_count += 1
                print(f"   {RED}❌ JSON decode error: {e}{RESET}")

            except Exception as e:
                error_count += 1
                print(f"   {RED}❌ Error: {e}{RESET}")

    except KeyboardInterrupt:
        print(f"\n   {YELLOW}⚠️  Interrupted by user{RESET}")

    finally:
        socket.close()
        context.term()

    # Print statistics
    print_header("Statistics")

    elapsed = time.time() - start_time

    print(f"Duration: {elapsed:.2f}s")
    print(f"Ticks Received: {GREEN}{tick_count}{RESET}")
    print(f"Tick Rate: {GREEN}{tick_count / elapsed:.2f} ticks/sec{RESET}" if elapsed > 0 else "")
    print(f"Errors: {RED if error_count > 0 else GREEN}{error_count}{RESET}")
    print(f"\nSymbols Received: {len(symbols)}")
    if symbols:
        print(f"  {', '.join(sorted(symbols))}")

    if tick_types:
        print(f"\nMessage Types:")
        for msg_type, count in sorted(tick_types.items()):
            print(f"  {msg_type}: {count}")

    if min_bid != float('inf') and max_bid != float('-inf'):
        print(f"\nPrice Range (Bid):")
        print(f"  Min: {GREEN}{min_bid:.5f}{RESET}")
        print(f"  Max: {GREEN}{max_bid:.5f}{RESET}")

    print_header("Verification Result")

    if tick_count > 0:
        print(f"{GREEN}✅ SUCCESS{RESET}")
        print(f"   Live market data verified!")
        print(f"   Received {tick_count} ticks from {len(symbols)} symbol(s)")
        print(f"   Data flow confirmed: GTW → ZMQ SUB → HUB")
        return True
    else:
        print(f"{RED}❌ FAILURE{RESET}")
        print(f"   No market data received")
        print(f"   Check:")
        print(f"   1. SSH tunnel is running: ssh -L 5556:localhost:5556 gtw")
        print(f"   2. GTW Gateway is running: netstat -ano | findstr :5556")
        print(f"   3. Firewall allows port 5556")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Subscribe to MT5 Gateway market data via ZMQ"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="ZMQ server host (default: 127.0.0.1 for SSH tunnel)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5556,
        help="ZMQ server port (default: 5556)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="How long to listen in seconds (default: 30)"
    )

    args = parser.parse_args()

    # Run subscription
    success = subscribe_to_market_data(
        host=args.host,
        port=args.port,
        duration=args.duration
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
