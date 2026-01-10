#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #082: Physical Trade Execution Verification

Verifies that ZMQ signals from INF successfully reach GTW and trigger
real MT5 actions (account queries, order placement/cancellation).

Protocol: v4.3 (Zero-Trust Edition)
Execution Node: INF Server (172.19.141.250)

Architecture improvements:
- ZMQ Context created once and reused (not per-request)
- GTW endpoint configurable via environment or command-line args
- Proper exception handling (no silent failures)
- Graceful cleanup via __del__
"""

import json
import logging
import zmq
import time
import uuid
import os
import argparse
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Protocol Actions (from src/mt5_bridge/protocol.py)
ACTION_HEARTBEAT = "HEARTBEAT"
ACTION_OPEN_ORDER = "OPEN_ORDER"
ACTION_CLOSE_POSITION = "CLOSE_POSITION"
ACTION_GET_ACCOUNT_INFO = "GET_ACCOUNT_INFO"
ACTION_GET_POSITIONS = "GET_POSITIONS"
ACTION_KILL_SWITCH = "KILL_SWITCH"

# Response Status
STATUS_SUCCESS = "SUCCESS"
STATUS_ERROR = "ERROR"
STATUS_PENDING = "PENDING"

# ZMQ Configuration Constants
ZMQ_TIMEOUT_MS = 5000  # 5 second timeout (milliseconds)


class ExecutionLinkVerifier:
    """Verify physical execution link between INF and GTW/MT5

    Proper ZMQ lifecycle management:
    - Context created once in __init__
    - Socket reused across commands
    - Graceful cleanup in __del__
    """

    def __init__(self, gtw_host: str, gtw_port: int):
        """Initialize verifier with configurable GTW endpoint

        Args:
            gtw_host: GTW server IP address
            gtw_port: GTW ZMQ port
        """
        self.gtw_host = gtw_host
        self.gtw_port = gtw_port
        self.gtw_addr = f"tcp://{self.gtw_host}:{self.gtw_port}"

        # Create ZMQ context ONCE (not per-request)
        self.zmq_context = zmq.Context()
        self.zmq_socket = None

        logger.info(f"Execution Link Verifier initialized")
        logger.info(f"Target: {self.gtw_addr}")

        # Establish connection
        self._connect_socket()

    def _connect_socket(self) -> bool:
        """Establish or reset ZMQ socket connection

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.zmq_socket:
                try:
                    self.zmq_socket.close()
                except Exception:
                    pass

            self.zmq_socket = self.zmq_context.socket(zmq.REQ)
            self.zmq_socket.setsockopt(zmq.RCVTIMEO, ZMQ_TIMEOUT_MS)
            self.zmq_socket.setsockopt(zmq.SNDTIMEO, ZMQ_TIMEOUT_MS)
            self.zmq_socket.connect(self.gtw_addr)

            logger.debug(f"  Socket connected to {self.gtw_addr}")
            return True
        except Exception as e:
            logger.error(f"  Socket connection failed: {e}")
            return False

    def send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send ZMQ command to GTW and receive response

        Reuses persistent socket. Resets socket on errors (REQ/REP requirement).

        Args:
            command: Dictionary command to send

        Returns:
            Response dictionary or None on error
        """
        try:
            logger.debug(f"  Sending: {command.get('action', 'UNKNOWN')}")
            self.zmq_socket.send_json(command)

            response = self.zmq_socket.recv_json()
            logger.debug(f"  Received: {response.get('status', 'UNKNOWN')}")

            return response

        except zmq.error.Again:
            logger.error("  ❌ ZMQ TIMEOUT - GTW not responding")
            self._connect_socket()  # Reset socket after timeout
            return None
        except zmq.error.ZMQError as e:
            logger.error(f"  ❌ ZMQ Error: {e}")
            self._connect_socket()  # Reset socket after error
            return None
        except json.JSONDecodeError as e:
            logger.error(f"  ❌ Invalid JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"  ❌ Unexpected error: {e}")
            return None

    def close(self):
        """Gracefully shutdown ZMQ connection"""
        try:
            if self.zmq_socket:
                self.zmq_socket.close()
            if self.zmq_context:
                self.zmq_context.term()
            logger.info("  ZMQ connection closed")
        except Exception as e:
            logger.warning(f"  Error during cleanup: {e}")

    def __del__(self):
        """Destructor ensures cleanup"""
        self.close()

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Step 1: Request account information from MT5

        Returns:
            Account info dict with Balance, Equity, etc.
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Account Information Retrieval")
        logger.info("=" * 80)

        command = {
            "action": ACTION_GET_ACCOUNT_INFO,
            "req_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "payload": {}
        }

        response = self.send_command(command)

        if response and response.get("status") == STATUS_SUCCESS:
            logger.info("✓ Account information retrieved successfully")
            data = response.get("data", {})
            if "balance" in data:
                logger.info(f"  Balance: {data['balance']}")
            if "equity" in data:
                logger.info(f"  Equity: {data['equity']}")
            if "free_margin" in data:
                logger.info(f"  Free Margin: {data['free_margin']}")
            return data
        else:
            error_msg = response.get("error", "Unknown error") if response else "No response"
            logger.error(f"✗ Failed to retrieve account information: {error_msg}")
            return None

    def place_limit_order(self, symbol: str = "EURUSD") -> Optional[Dict[str, Any]]:
        """Step 2a: Place a limit order (at unfavorable price, won't execute)

        Args:
            symbol: Trading symbol

        Returns:
            Order response with ticket number
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2a: Place Limit Order (Non-Executable Price)")
        logger.info("=" * 80)

        command = {
            "action": ACTION_OPEN_ORDER,
            "req_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "payload": {
                "symbol": symbol,
                "volume": 0.01,
                "side": "BUY",
                "type": "LIMIT",
                "price": 0.5000,
                "comment": "Task #082 E2E Verification - Limit Order Test"
            }
        }

        logger.info(f"  Placing BUY LIMIT order at {symbol} @ 0.5000 (below market)")
        response = self.send_command(command)

        if response and response.get("status") == STATUS_SUCCESS:
            data = response.get("data", {})
            if "ticket" in data:
                logger.info(f"✓ Order placed successfully")
                logger.info(f"  Ticket: {data['ticket']}")
                return data

        error_msg = response.get("error", "Unknown error") if response else "No response"
        logger.error(f"✗ Failed to place order: {error_msg}")
        return None

    def close_position(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Step 2b: Close the previously placed order

        Args:
            ticket: Order ticket number to close

        Returns:
            Close response
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2b: Close Order")
        logger.info("=" * 80)

        command = {
            "action": ACTION_CLOSE_POSITION,
            "req_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "payload": {
                "ticket": ticket
            }
        }

        logger.info(f"  Closing order ticket {ticket}")
        response = self.send_command(command)

        if response and response.get("status") == STATUS_SUCCESS:
            logger.info(f"✓ Order closed successfully")
            return response.get("data")
        else:
            error_msg = response.get("error", "Unknown error") if response else "No response"
            logger.error(f"✗ Failed to close order: {error_msg}")
            return None

    def verify_account_unchanged(self, initial_state: Dict[str, Any]) -> bool:
        """Step 3: Verify account state is unchanged after order cycle

        Args:
            initial_state: Initial account info

        Returns:
            True if account state is consistent
        """
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Account State Verification")
        logger.info("=" * 80)

        final_state = self.get_account_info()

        if not final_state:
            logger.error("✗ Could not retrieve final account state")
            return False

        checks = []

        if "balance" in initial_state and "balance" in final_state:
            balance_unchanged = abs(initial_state["balance"] - final_state["balance"]) < 0.01
            checks.append(balance_unchanged)
            logger.info(f"  Balance check: {'✓ PASS' if balance_unchanged else '✗ FAIL'}")

        if "equity" in initial_state and "equity" in final_state:
            equity_unchanged = abs(initial_state["equity"] - final_state["equity"]) < 0.01
            checks.append(equity_unchanged)
            logger.info(f"  Equity check: {'✓ PASS' if equity_unchanged else '✗ FAIL'}")

        all_passed = all(checks) if checks else True
        return all_passed

    def run_full_verification(self) -> bool:
        """Execute full E2E verification sequence

        Returns:
            True if all steps passed
        """
        logger.info("\n" + "=" * 80)
        logger.info("TASK #082: PHYSICAL EXECUTION LINK VERIFICATION")
        logger.info("=" * 80)
        logger.info(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

        try:
            # Step 1: Get initial account info
            initial_account = self.get_account_info()
            if not initial_account:
                logger.error("✗ VERIFICATION FAILED: Cannot retrieve account info")
                return False

            # Step 2: Order lifecycle test
            order_response = self.place_limit_order("EURUSD")
            if not order_response or "ticket" not in order_response:
                logger.error("✗ VERIFICATION FAILED: Cannot place order")
                return False

            time.sleep(1)

            ticket = order_response["ticket"]
            close_response = self.close_position(ticket)
            if not close_response:
                logger.error("✗ VERIFICATION FAILED: Cannot close order")
                return False

            # Step 3: Verify account state
            account_verified = self.verify_account_unchanged(initial_account)

            logger.info("\n" + "=" * 80)
            logger.info("VERIFICATION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"✓ Account info retrieved: {bool(initial_account)}")
            logger.info(f"✓ Order placed: Ticket {order_response.get('ticket', 'N/A')}")
            logger.info(f"✓ Order closed: {bool(close_response)}")
            logger.info(f"✓ Account state consistent: {account_verified}")
            logger.info(f"✓ E2E verification: {'PASSED' if account_verified else 'FAILED'}")
            logger.info(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

            return account_verified

        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Task #082: Verify physical MT5 execution link via ZMQ"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("GTW_HOST", "172.19.141.255"),
        help="GTW server IP (default: env GTW_HOST or 172.19.141.255)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("GTW_PORT", "5555")),
        help="GTW ZMQ port (default: env GTW_PORT or 5555)"
    )

    args = parser.parse_args()

    logger.info("Starting Task #082: Physical Execution Link Verification")

    verifier = ExecutionLinkVerifier(args.host, args.port)
    try:
        success = verifier.run_full_verification()

        if success:
            logger.info("\n✅ TASK #082 VERIFICATION PASSED - Physical execution link confirmed")
            exit(0)
        else:
            logger.error("\n❌ TASK #082 VERIFICATION FAILED - See errors above")
            exit(1)
    finally:
        verifier.close()


if __name__ == "__main__":
    main()
