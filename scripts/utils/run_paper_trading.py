#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Trading Simulation Runner

Task #018.01: Real-time Inference & Execution Loop

Runs a complete simulation with:
- Mock Market Data Publisher (ZMQ PUB)
- Mock MT5 Gateway (ZMQ REP)
- Real TradingBot (with real model and API calls)

Protocol: v2.2 (Hot Path Architecture)
"""

import sys
import zmq
import json
import time
import threading
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bot.trading_bot import TradingBot

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class MockMarketPublisher:
    """
    Mock Market Data Publisher (ZMQ PUB)

    Publishes simulated market ticks to ZMQ PUB socket.
    """

    def __init__(self, port: int = 5556, symbols: List[str] = None):
        """
        Initialize Mock Market Publisher

        Args:
            port: ZMQ PUB port
            symbols: List of symbols to publish
        """
        self.port = port
        self.symbols = symbols or ["EURUSD", "XAUUSD"]
        self.running = False
        self.thread = None

        self.context = zmq.Context()
        self.socket = None

        # Starting prices
        self.prices = {
            "EURUSD": 1.10000,
            "XAUUSD": 2050.00
        }

    def start(self):
        """Start publisher in background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        time.sleep(0.5)  # Give time to bind
        print(f"{GREEN}✅ Mock Market Publisher started (Port {self.port}){RESET}")

    def stop(self):
        """Stop publisher"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        if self.thread:
            self.thread.join(timeout=2)
        print(f"{CYAN}🔴 Mock Market Publisher stopped{RESET}")

    def _run(self):
        """Publisher loop (runs in background thread)"""
        try:
            self.socket = self.context.socket(zmq.PUB)
            self.socket.bind(f"tcp://*:{self.port}")

            print(f"{CYAN}🟢 Publisher listening on port {self.port}{RESET}")

            while self.running:
                # Publish tick for each symbol
                for symbol in self.symbols:
                    # Simulate price movement
                    change = random.uniform(-0.0005, 0.0005)
                    self.prices[symbol] += change

                    # Create tick
                    tick = {
                        "type": "tick",
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat(),
                        "bid": round(self.prices[symbol], 5),
                        "ask": round(self.prices[symbol] + 0.00005, 5),
                        "last": round(self.prices[symbol] + 0.000025, 5),
                        "volume": random.randint(50, 200)
                    }

                    # Publish: "SYMBOL {json}"
                    message = f"{symbol} {json.dumps(tick)}"
                    self.socket.send_string(message)

                # Sleep 1 second (1 tick/s per symbol)
                time.sleep(1)

        except Exception as e:
            print(f"{RED}❌ Publisher error: {e}{RESET}")


class MockMT5Gateway:
    """
    Mock MT5 Gateway (ZMQ REP)

    Simulates order execution with realistic delays.
    """

    def __init__(self, port: int = 5555):
        """
        Initialize Mock MT5 Gateway

        Args:
            port: ZMQ REP port
        """
        self.port = port
        self.running = False
        self.thread = None
        self.order_counter = 100000

        self.context = zmq.Context()
        self.socket = None

    def start(self):
        """Start gateway in background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        time.sleep(0.5)  # Give time to bind
        print(f"{GREEN}✅ Mock MT5 Gateway started (Port {self.port}){RESET}")

    def stop(self):
        """Stop gateway"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        if self.thread:
            self.thread.join(timeout=2)
        print(f"{CYAN}🔴 Mock MT5 Gateway stopped{RESET}")

    def _run(self):
        """Gateway loop (runs in background thread)"""
        try:
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind(f"tcp://*:{self.port}")

            # Set timeout to allow periodic checking
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)

            print(f"{CYAN}🟢 Gateway listening on port {self.port}{RESET}")

            while self.running:
                try:
                    # Wait for request
                    message = self.socket.recv_json()

                    # Process request
                    response = self._process_request(message)

                    # Simulate execution delay (50-200ms)
                    time.sleep(random.uniform(0.05, 0.2))

                    # Send response
                    self.socket.send_json(response)

                except zmq.Again:
                    # Timeout, check if still running
                    continue

        except Exception as e:
            print(f"{RED}❌ Gateway error: {e}{RESET}")

    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process client request and return response"""
        action = request.get("action")

        if action == "PING":
            return {
                "status": "ok",
                "message": "pong",
                "timestamp": request.get("timestamp")
            }

        elif action == "GET_ACCOUNT":
            return {
                "status": "ok",
                "balance": 10000.00,
                "equity": 10050.00,
                "margin": 200.00,
                "free_margin": 9850.00,
                "margin_level": 5025.00,
                "currency": "USD"
            }

        elif action == "GET_POSITIONS":
            # Return empty positions for simulation
            return {
                "status": "ok",
                "positions": [],
                "count": 0
            }

        elif action == "TRADE":
            # Simulate order execution
            self.order_counter += 1

            symbol = request.get("symbol")
            side = request.get("side")
            volume = request.get("volume")
            order_type = request.get("order_type")

            # Mock execution price
            base_price = 1.10000 if "EUR" in symbol else 2050.00
            fill_price = base_price + random.uniform(-0.0001, 0.0001)

            return {
                "status": "ok",
                "ticket": self.order_counter,
                "symbol": symbol,
                "type": f"{order_type}_{side}",
                "volume": volume,
                "price": round(fill_price, 5),
                "sl": request.get("sl"),
                "tp": request.get("tp"),
                "message": "Order executed successfully"
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }


def run_simulation(duration: int = 60):
    """
    Run complete paper trading simulation

    Args:
        duration: Simulation duration in seconds
    """
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}🤖 Paper Trading Simulation{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")
    print()

    # 1. Start Mock Services
    print(f"{YELLOW}Starting Mock Services...{RESET}")
    publisher = MockMarketPublisher(port=5556, symbols=["EURUSD"])
    gateway = MockMT5Gateway(port=5555)

    publisher.start()
    gateway.start()
    print()

    # 2. Initialize Trading Bot
    print(f"{YELLOW}Initializing Trading Bot...{RESET}")

    # Check if model exists
    model_path = PROJECT_ROOT / "models" / "baseline_v1.json"
    if not model_path.exists():
        print(f"{RED}❌ Model not found: {model_path}{RESET}")
        print(f"{YELLOW}Please train the model first:{RESET}")
        print(f"  python3 scripts/run_baseline_training.py")
        publisher.stop()
        gateway.stop()
        return

    bot = TradingBot(
        symbols=["EURUSD"],
        model_path=str(model_path),
        api_url="http://localhost:8000",
        zmq_market_url="tcp://localhost:5556",
        zmq_execution_host="localhost",
        zmq_execution_port=5555,
        volume=0.1
    )
    print()

    # 3. Run Bot
    print(f"{YELLOW}Running for {duration} seconds...{RESET}")
    print()

    try:
        bot.run(duration_seconds=duration)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}🛑 KeyboardInterrupt received{RESET}")

    finally:
        # 4. Stop Mock Services
        print()
        print(f"{YELLOW}Stopping Mock Services...{RESET}")
        publisher.stop()
        gateway.stop()

    print()
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}📊 Simulation Complete{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")
    print()
    print(f"📝 Logs saved to: logs/trading.log")
    print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Paper Trading Simulation (Task #018.01)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Simulation duration in seconds (default: 60)"
    )

    args = parser.parse_args()

    run_simulation(duration=args.duration)


if __name__ == "__main__":
    main()
