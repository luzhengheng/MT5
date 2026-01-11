#!/usr/bin/env python3
"""
Mock Market Data Publisher for Testing
======================================

Simulates MT5 Gateway market data publishing on port 5556.
Used for testing subscription scripts when MT5 is not available.

Usage:
    python3 scripts/mock_market_data_publisher.py              # Publish to localhost:5556
    python3 scripts/mock_market_data_publisher.py --port 5556  # Custom port
"""

import zmq
import json
import time
import argparse
import sys
import random
from datetime import datetime

# Color codes
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Sample trading symbols
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD"]

# Base prices (realistic market prices)
BASE_PRICES = {
    "EURUSD": 1.0850,
    "GBPUSD": 1.2750,
    "USDJPY": 149.50,
    "AUDUSD": 0.6650,
    "NZDUSD": 0.6100
}

# Typical spreads (in pips, depends on symbol)
SPREADS = {
    "EURUSD": 0.00015,
    "GBPUSD": 0.00020,
    "USDJPY": 0.015,
    "AUDUSD": 0.00025,
    "NZDUSD": 0.00030
}


def publish_market_data(port: int = 5556, duration: int = 30):
    """
    Publish simulated market data to ZMQ PUB socket.

    Args:
        port: ZMQ port to publish on
        duration: How long to publish (seconds)
    """
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  Mock Market Data Publisher{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")

    print(f"Configuration:")
    print(f"  Port: {port}")
    print(f"  Duration: {duration}s")
    print(f"  Symbols: {', '.join(SYMBOLS)}")
    print(f"  Publish Rate: 10 ticks/sec per symbol\n")

    # Create ZMQ context and socket
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    # Bind to all interfaces
    socket.bind(f"tcp://*:{port}")

    print(f"{GREEN}✅ Publisher started on port {port}{RESET}")
    print(f"{CYAN}Waiting 2 seconds for subscribers to connect...{RESET}\n")

    time.sleep(2)  # Wait for subscribers to connect

    print(f"Publishing market data...\n")

    start_time = time.time()
    tick_count = 0
    price_state = {symbol: BASE_PRICES[symbol] for symbol in SYMBOLS}

    try:
        while time.time() - start_time < duration:
            for symbol in SYMBOLS:
                # Simulate price movement (random walk)
                price_change = random.gauss(0, 0.0001)
                current_price = price_state[symbol] + price_change
                price_state[symbol] = current_price

                # Calculate bid/ask
                spread = SPREADS[symbol]
                bid = current_price
                ask = current_price + spread

                # Simulated market data
                tick_data = {
                    "symbol": symbol,
                    "bid": bid,
                    "ask": ask,
                    "volume": random.randint(100000, 500000),
                    "spread": spread,
                    "timestamp": time.time(),
                    "type": "tick"
                }

                # Publish
                socket.send_json(tick_data)
                tick_count += 1

                # Print progress
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                if tick_count % 50 == 0:  # Print every 50 ticks
                    print(f"   [{timestamp}] Published {tick_count} ticks")

            # Small delay to control publish rate (10 ticks/sec per symbol)
            time.sleep(0.01)

    except KeyboardInterrupt:
        print(f"\n   Interrupted by user")

    finally:
        socket.close()
        context.term()

    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{GREEN}✅ Publishing complete{RESET}")
    print(f"   Total ticks published: {tick_count}")
    print(f"   Publish rate: {tick_count / (time.time() - start_time):.2f} ticks/sec")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Publish mock market data for testing"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5556,
        help="ZMQ port to publish on (default: 5556)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="How long to publish (default: 30 seconds)"
    )

    args = parser.parse_args()

    try:
        publish_market_data(port=args.port, duration=args.duration)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
