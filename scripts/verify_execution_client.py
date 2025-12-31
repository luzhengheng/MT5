#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Execution Client Verification Script

Mock ZMQ Server + Client Integration Tests
Protocol: v2.2 (Hot Path Architecture)
"""

import sys
import json
import time
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import zmq
from src.gateway.mt5_client import MT5Client

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class MockMT5Gateway:
    """Mock MT5 Gateway for testing"""

    def __init__(self, port: int = 5555):
        self.port = port
        self.context = zmq.Context()
        self.socket = None
        self.running = False
        self.thread = None

    def start(self):
        """Start mock server in background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        time.sleep(0.5)  # Give server time to start

    def stop(self):
        """Stop mock server"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()

    def _run_server(self):
        """Server loop (runs in background thread)"""
        try:
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind(f"tcp://*:{self.port}")

            # Set timeout to allow periodic checking of running flag
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)

            print(f"{CYAN}🟢 Mock Gateway started on port {self.port}{RESET}")

            while self.running:
                try:
                    # Wait for request
                    message = self.socket.recv_json()

                    # Process request
                    response = self._process_request(message)

                    # Send response
                    self.socket.send_json(response)

                except zmq.Again:
                    # Timeout, check if still running
                    continue
                except Exception as e:
                    print(f"{RED}❌ Server error: {e}{RESET}")
                    break

            print(f"{CYAN}🔴 Mock Gateway stopped{RESET}")

        except Exception as e:
            print(f"{RED}❌ Failed to start server: {e}{RESET}")

    def _process_request(self, request: dict) -> dict:
        """Process client request and return mock response"""
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
            symbol = request.get("symbol")

            # Mock positions
            all_positions = [
                {
                    "ticket": 123456,
                    "symbol": "EURUSD",
                    "type": "BUY",
                    "volume": 0.1,
                    "open_price": 1.1000,
                    "current_price": 1.1020,
                    "sl": 1.0950,
                    "tp": 1.1100,
                    "profit": 20.00,
                    "magic": 0,
                    "comment": "Test position"
                },
                {
                    "ticket": 123457,
                    "symbol": "XAUUSD",
                    "type": "SELL",
                    "volume": 0.01,
                    "open_price": 2050.00,
                    "current_price": 2045.00,
                    "sl": 2060.00,
                    "tp": 2030.00,
                    "profit": 5.00,
                    "magic": 0,
                    "comment": "Gold position"
                }
            ]

            # Filter by symbol if requested
            if symbol:
                positions = [p for p in all_positions if p["symbol"] == symbol]
            else:
                positions = all_positions

            return {
                "status": "ok",
                "positions": positions,
                "count": len(positions)
            }

        elif action == "TRADE":
            # Mock trade execution
            symbol = request.get("symbol")
            side = request.get("side")
            volume = request.get("volume")
            order_type = request.get("order_type")
            price = request.get("price")

            # Simulate successful order
            return {
                "status": "ok",
                "ticket": 999888,
                "symbol": symbol,
                "type": f"{order_type}_{side}",
                "volume": volume,
                "price": price if price else 1.1000,
                "sl": request.get("sl"),
                "tp": request.get("tp"),
                "message": "Order executed successfully"
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }


def test_01_ping():
    """Test 1: PING Command"""
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}TEST 1: PING Command{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    try:
        client = MT5Client(host="localhost", port=5555)

        if not client.connect():
            print(f"{RED}❌ Failed to connect{RESET}")
            return False

        # Test ping
        result = client.ping()

        client.close()

        if result:
            print(f"{GREEN}✅ PING successful{RESET}")
            return True
        else:
            print(f"{RED}❌ PING failed{RESET}")
            return False

    except Exception as e:
        print(f"{RED}❌ Test failed: {e}{RESET}")
        return False


def test_02_get_account():
    """Test 2: GET_ACCOUNT Command"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}TEST 2: GET_ACCOUNT Command{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    try:
        with MT5Client(host="localhost", port=5555) as client:
            response = client.get_account()

            if response.get("status") == "ok":
                balance = response.get("balance")
                equity = response.get("equity")
                currency = response.get("currency")

                print(f"{GREEN}✅ Account retrieved{RESET}")
                print(f"  Balance: {balance:.2f} {currency}")
                print(f"  Equity: {equity:.2f} {currency}")

                # Verify expected values
                if balance == 10000.00 and equity == 10050.00 and currency == "USD":
                    print(f"{GREEN}✅ Account data matches expected values{RESET}")
                    return True
                else:
                    print(f"{RED}❌ Account data mismatch{RESET}")
                    return False
            else:
                print(f"{RED}❌ Failed to get account: {response}{RESET}")
                return False

    except Exception as e:
        print(f"{RED}❌ Test failed: {e}{RESET}")
        return False


def test_03_get_positions():
    """Test 3: GET_POSITIONS Command"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}TEST 3: GET_POSITIONS Command{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    try:
        with MT5Client(host="localhost", port=5555) as client:
            # Get all positions
            positions = client.get_positions()

            print(f"{GREEN}✅ Found {len(positions)} position(s){RESET}")

            for pos in positions:
                print(f"  Ticket: {pos['ticket']}, Symbol: {pos['symbol']}, "
                      f"Type: {pos['type']}, Volume: {pos['volume']}, "
                      f"Profit: {pos['profit']:.2f}")

            # Get filtered positions
            eurusd_positions = client.get_positions(symbol="EURUSD")

            print(f"{GREEN}✅ Found {len(eurusd_positions)} EURUSD position(s){RESET}")

            # Verify
            if len(positions) == 2 and len(eurusd_positions) == 1:
                print(f"{GREEN}✅ Position filtering works correctly{RESET}")
                return True
            else:
                print(f"{RED}❌ Position count mismatch{RESET}")
                return False

    except Exception as e:
        print(f"{RED}❌ Test failed: {e}{RESET}")
        return False


def test_04_send_order():
    """Test 4: TRADE Command"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}TEST 4: TRADE Command{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    try:
        with MT5Client(host="localhost", port=5555) as client:
            # Send market order
            response = client.send_order(
                symbol="EURUSD",
                side="BUY",
                volume=0.1,
                order_type="MARKET",
                sl=1.0950,
                tp=1.1100,
                magic=12345,
                comment="Test order"
            )

            if response.get("status") == "ok":
                ticket = response.get("ticket")
                print(f"{GREEN}✅ Order executed: Ticket #{ticket}{RESET}")
                print(f"  Symbol: {response.get('symbol')}")
                print(f"  Type: {response.get('type')}")
                print(f"  Volume: {response.get('volume')}")
                print(f"  Price: {response.get('price'):.5f}")

                # Verify
                if ticket == 999888:
                    print(f"{GREEN}✅ Order data matches expected values{RESET}")
                    return True
                else:
                    print(f"{RED}❌ Ticket mismatch{RESET}")
                    return False
            else:
                print(f"{RED}❌ Order failed: {response}{RESET}")
                return False

    except Exception as e:
        print(f"{RED}❌ Test failed: {e}{RESET}")
        return False


def test_05_validation():
    """Test 5: Input Validation"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}TEST 5: Input Validation{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    try:
        with MT5Client(host="localhost", port=5555) as client:
            # Test invalid side
            try:
                client.send_order(
                    symbol="EURUSD",
                    side="INVALID",
                    volume=0.1
                )
                print(f"{RED}❌ Should have raised ValueError for invalid side{RESET}")
                return False
            except ValueError as e:
                print(f"{GREEN}✅ ValueError raised for invalid side: {e}{RESET}")

            # Test invalid order type
            try:
                client.send_order(
                    symbol="EURUSD",
                    side="BUY",
                    volume=0.1,
                    order_type="INVALID"
                )
                print(f"{RED}❌ Should have raised ValueError for invalid order_type{RESET}")
                return False
            except ValueError as e:
                print(f"{GREEN}✅ ValueError raised for invalid order_type: {e}{RESET}")

            # Test LIMIT order without price
            try:
                client.send_order(
                    symbol="EURUSD",
                    side="BUY",
                    volume=0.1,
                    order_type="LIMIT"
                )
                print(f"{RED}❌ Should have raised ValueError for LIMIT without price{RESET}")
                return False
            except ValueError as e:
                print(f"{GREEN}✅ ValueError raised for LIMIT without price: {e}{RESET}")

            print(f"{GREEN}✅ All validation tests passed{RESET}")
            return True

    except Exception as e:
        print(f"{RED}❌ Test failed: {e}{RESET}")
        return False


def main():
    """Main verification workflow"""
    print(f"{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}MT5 Execution Client Verification{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}")
    print()

    # Start mock server
    print(f"{YELLOW}Starting Mock MT5 Gateway...{RESET}")
    mock_server = MockMT5Gateway(port=5555)
    mock_server.start()
    time.sleep(1)  # Ensure server is ready
    print()

    # Run tests
    results = {}

    try:
        results["test_01_ping"] = test_01_ping()
        results["test_02_get_account"] = test_02_get_account()
        results["test_03_get_positions"] = test_03_get_positions()
        results["test_04_send_order"] = test_04_send_order()
        results["test_05_validation"] = test_05_validation()

    finally:
        # Stop mock server
        print(f"\n{YELLOW}Stopping Mock MT5 Gateway...{RESET}")
        mock_server.stop()
        time.sleep(0.5)

    # Summary
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}TEST SUMMARY{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{test_name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print(f"{GREEN}{'=' * 80}{RESET}")
        print(f"{GREEN}✅ ALL TESTS PASSED{RESET}")
        print(f"{GREEN}{'=' * 80}{RESET}")
        return 0
    else:
        print(f"{RED}{'=' * 80}{RESET}")
        print(f"{RED}❌ SOME TESTS FAILED{RESET}")
        print(f"{RED}{'=' * 80}{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
