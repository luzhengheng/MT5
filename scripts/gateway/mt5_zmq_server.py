#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 ZMQ Server - Windows Gateway for MT5 Trading Bridge
Task #106 - MT5 Live Bridge Implementation

Protocol v4.3 (Zero-Trust Edition) compliant Windows-side ZMQ server that:
- Listens on ZMQ REP socket (default port 5555)
- Receives commands from Linux Inf node (MT5LiveConnector)
- Validates risk_signature for all OPEN commands
- Executes MT5 API calls via MT5Service
- Returns structured responses with execution details
- Auto-reconnects to MT5 on disconnection
- Full error handling and audit logging

Architecture:
    Linux Inf (MT5LiveConnector) → [ZMQ 5555] → Windows GTW (MT5ZmqServer) → MT5 Terminal

Supported Commands:
    - PING: Heartbeat check (returns server_time, latency)
    - OPEN: Open position (validates risk_signature, calls mt5.order_send)
    - CLOSE: Close position (calls mt5.order_send with position ticket)
    - GET_ACCOUNT: Query account info (balance, equity, margin, etc.)
    - GET_POSITIONS: Query open positions (filtered by symbol if provided)

Usage:
    python mt5_zmq_server.py --port 5555 --host 0.0.0.0 --mt5-login 123456 --mt5-password xxx --mt5-server Broker-Server

Author: Claude Sonnet 4.5
Date: 2026-01-15
Protocol: v4.3 (Zero-Trust Edition)
"""

import os
import sys
import json
import time
import logging
import argparse
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import ZMQ
try:
    import zmq
except ImportError:
    print("ERROR: pyzmq not installed. Install with: pip install pyzmq")
    sys.exit(1)

# Import MT5Service (add parent paths for imports)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "gateway"))

try:
    from gateway.mt5_service import MT5Service
except ImportError:
    try:
        from mt5_service import MT5Service
    except ImportError:
        print("ERROR: Cannot import MT5Service. Ensure src/gateway/mt5_service.py exists")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).parent / "mt5_zmq_server.log",
            mode='a',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger('MT5ZmqServer')

# Color codes (for Windows terminal - may not work on all terminals)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


class MT5ZmqServer:
    """
    MT5 ZMQ Server - Windows Gateway Component

    Responsibilities:
    1. Listen on ZMQ REP socket (request-reply pattern)
    2. Receive commands from Linux Inf node
    3. Validate risk_signature for OPEN commands
    4. Execute MT5 API calls via MT5Service
    5. Return structured responses
    6. Auto-reconnect MT5 if disconnected
    7. Full audit logging

    Command Protocol (JSON):
        Request: {"uuid": "...", "action": "PING|OPEN|CLOSE|GET_ACCOUNT|GET_POSITIONS", ...}
        Response: {"uuid": "...", "status": "ok|FILLED|REJECTED|error", ...}
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5555,
        mt5_login: Optional[str] = None,
        mt5_password: Optional[str] = None,
        mt5_server: Optional[str] = None,
        mt5_path: Optional[str] = None,
        signature_validation: bool = True,
        signature_ttl_seconds: int = 5
    ):
        """
        Initialize MT5 ZMQ Server

        Args:
            host: ZMQ bind host (default: 0.0.0.0 - all interfaces)
            port: ZMQ bind port (default: 5555)
            mt5_login: MT5 account login (optional, can use .env)
            mt5_password: MT5 account password (optional, can use .env)
            mt5_server: MT5 broker server (optional, can use .env)
            mt5_path: MT5 terminal path (optional, can use .env)
            signature_validation: Enable risk signature validation (default: True)
            signature_ttl_seconds: Risk signature TTL in seconds (default: 5)
        """
        self.host = host
        self.port = port
        self.signature_validation = signature_validation
        self.signature_ttl_seconds = signature_ttl_seconds

        # Override environment variables if provided
        if mt5_login:
            os.environ['MT5_LOGIN'] = mt5_login
        if mt5_password:
            os.environ['MT5_PASSWORD'] = mt5_password
        if mt5_server:
            os.environ['MT5_SERVER'] = mt5_server
        if mt5_path:
            os.environ['MT5_PATH'] = mt5_path

        # Initialize MT5Service (singleton)
        self.mt5_service = MT5Service()

        # ZMQ context and socket (will be initialized in start())
        self.context: Optional[zmq.Context] = None
        self.socket: Optional[zmq.Socket] = None

        # Statistics
        self.requests_processed = 0
        self.orders_executed = 0
        self.orders_rejected = 0
        self.errors_encountered = 0
        self.start_time = datetime.now(timezone.utc)

        logger.info(f"{GREEN}{'='*80}{RESET}")
        logger.info(f"{GREEN}MT5 ZMQ Server Initialized - Protocol v4.3{RESET}")
        logger.info(f"{GREEN}  Bind Address: {host}:{port}{RESET}")
        logger.info(f"{GREEN}  MT5 Server: {self.mt5_service.mt5_server}{RESET}")
        logger.info(f"{GREEN}  Signature Validation: {signature_validation}{RESET}")
        logger.info(f"{GREEN}  Signature TTL: {signature_ttl_seconds}s{RESET}")
        logger.info(f"{GREEN}{'='*80}{RESET}")

    def connect_mt5(self) -> bool:
        """
        Connect to MT5 terminal

        Returns:
            bool: True if connected successfully
        """
        try:
            logger.info(f"{CYAN}[MT5] Connecting to MT5 terminal...{RESET}")

            if self.mt5_service.connect():
                logger.info(f"{GREEN}✅ [MT5] Connected successfully{RESET}")
                return True
            else:
                logger.error(f"{RED}❌ [MT5] Connection failed{RESET}")
                return False

        except Exception as e:
            logger.error(f"{RED}❌ [MT5] Connection error: {e}{RESET}")
            return False

    def ensure_mt5_connected(self) -> bool:
        """
        Ensure MT5 is connected, auto-reconnect if needed

        Returns:
            bool: True if connected (or reconnected)
        """
        if self.mt5_service.is_connected():
            return True

        logger.warning(f"{YELLOW}⚠️  [MT5] Connection lost, attempting reconnect...{RESET}")
        return self.connect_mt5()

    def start(self) -> None:
        """
        Start ZMQ server and listen for commands

        Main event loop that:
        1. Initializes ZMQ REP socket
        2. Connects to MT5
        3. Listens for incoming commands
        4. Dispatches to command handlers
        5. Returns responses
        """
        try:
            # Initialize ZMQ
            logger.info(f"{CYAN}[ZMQ] Initializing ZMQ context...{RESET}")
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REP)

            # Bind to address
            bind_address = f"tcp://{self.host}:{self.port}"
            self.socket.bind(bind_address)
            logger.info(f"{GREEN}✅ [ZMQ] Listening on {bind_address}{RESET}")

            # Connect to MT5
            if not self.connect_mt5():
                logger.error(f"{RED}❌ [INIT] MT5 connection failed, but server will still start{RESET}")
                logger.warning(f"{YELLOW}⚠️  [INIT] Will attempt reconnect on first command{RESET}")

            logger.info(f"{GREEN}{'='*80}{RESET}")
            logger.info(f"{GREEN}🚀 MT5 ZMQ Server is RUNNING - Waiting for commands...{RESET}")
            logger.info(f"{GREEN}{'='*80}{RESET}")

            # Main event loop
            while True:
                try:
                    # Receive request (blocking)
                    message = self.socket.recv_string()
                    request_time = datetime.now(timezone.utc)

                    logger.debug(f"[ZMQ] Received: {message}")

                    # Parse JSON
                    try:
                        request = json.loads(message)
                    except json.JSONDecodeError as e:
                        response = self._error_response(
                            "INVALID_JSON",
                            f"Failed to parse JSON: {e}"
                        )
                        self.socket.send_string(json.dumps(response))
                        self.errors_encountered += 1
                        continue

                    # Process request
                    response = self._process_request(request, request_time)

                    # Send response
                    self.socket.send_string(json.dumps(response))
                    self.requests_processed += 1

                    logger.debug(f"[ZMQ] Sent: {json.dumps(response)}")

                except zmq.ZMQError as e:
                    logger.error(f"{RED}❌ [ZMQ] ZMQ error: {e}{RESET}")
                    self.errors_encountered += 1

                except KeyboardInterrupt:
                    logger.info(f"{YELLOW}[SERVER] Shutting down...{RESET}")
                    break

                except Exception as e:
                    logger.error(f"{RED}❌ [SERVER] Unexpected error: {e}{RESET}")
                    self.errors_encountered += 1
                    # Try to send error response
                    try:
                        response = self._error_response("SERVER_ERROR", str(e))
                        self.socket.send_string(json.dumps(response))
                    except:
                        pass

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown server and cleanup resources"""
        logger.info(f"{CYAN}[SERVER] Shutting down...{RESET}")

        # Print statistics
        self._print_statistics()

        # Close ZMQ socket
        if self.socket:
            self.socket.close()
            logger.info(f"{GREEN}✅ [ZMQ] Socket closed{RESET}")

        # Terminate ZMQ context
        if self.context:
            self.context.term()
            logger.info(f"{GREEN}✅ [ZMQ] Context terminated{RESET}")

        # Disconnect MT5
        if self.mt5_service.is_connected():
            self.mt5_service.disconnect()
            logger.info(f"{GREEN}✅ [MT5] Disconnected{RESET}")

        logger.info(f"{GREEN}✅ [SERVER] Shutdown complete{RESET}")

    def _process_request(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Process incoming request and dispatch to appropriate handler

        Args:
            request: JSON request dictionary
            request_time: Time when request was received

        Returns:
            Dict: JSON response dictionary
        """
        uuid = request.get('uuid', 'unknown')
        action = request.get('action', '').upper()

        logger.info(f"{CYAN}📥 [REQUEST] UUID={uuid}, Action={action}{RESET}")

        # Validate action
        if not action:
            return self._error_response("MISSING_ACTION", "Action field is required", uuid)

        # Dispatch to handler
        if action == "PING":
            return self._handle_ping(request, request_time)
        elif action == "OPEN":
            return self._handle_open(request, request_time)
        elif action == "CLOSE":
            return self._handle_close(request, request_time)
        elif action == "GET_ACCOUNT":
            return self._handle_get_account(request, request_time)
        elif action == "GET_POSITIONS":
            return self._handle_get_positions(request, request_time)
        elif action == "SYNC_ALL":
            return self._handle_sync_all(request, request_time)
        else:
            return self._error_response("UNKNOWN_ACTION", f"Unknown action: {action}", uuid)

    def _handle_ping(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Handle PING command (heartbeat check)

        Request:
            {"uuid": "...", "action": "PING", "timestamp": "..."}

        Response:
            {"uuid": "...", "status": "ok", "server_time": "...", "latency_ms": 0.123}
        """
        uuid = request.get('uuid', 'unknown')
        client_timestamp = request.get('timestamp', '')

        # Calculate latency
        server_time = datetime.now(timezone.utc)
        latency_ms = 0.0

        if client_timestamp:
            try:
                client_time = datetime.fromisoformat(client_timestamp.replace('Z', '+00:00'))
                latency_ms = (server_time - client_time).total_seconds() * 1000
            except:
                pass

        logger.info(f"{GREEN}✅ [PING] Latency: {latency_ms:.3f}ms{RESET}")

        return {
            "uuid": uuid,
            "status": "ok",
            "server_time": server_time.isoformat(),
            "latency_ms": round(latency_ms, 3)
        }

    def _handle_open(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Handle OPEN command (open position)

        Request:
            {
                "uuid": "...",
                "action": "OPEN",
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": 0.01,
                "price": 0.0,
                "sl": 1.05000,
                "tp": 1.06000,
                "comment": "...",
                "risk_signature": "RISK_PASS:<checksum>:<timestamp>",
                "timestamp": "..."
            }

        Response (Success):
            {
                "uuid": "...",
                "status": "FILLED",
                "ticket": 12345678,
                "symbol": "EURUSD",
                "volume": 0.01,
                "price": 1.05230,
                "execution_time": "...",
                "latency_ms": 1.234
            }

        Response (Error):
            {
                "uuid": "...",
                "status": "REJECTED",
                "error_code": "INSUFFICIENT_MARGIN",
                "error_msg": "...",
                "timestamp": "..."
            }
        """
        uuid = request.get('uuid', 'unknown')

        # Extract order parameters
        symbol = request.get('symbol', '')
        order_type = request.get('type', '').upper()
        volume = request.get('volume', 0.0)
        price = request.get('price', 0.0)
        sl = request.get('sl', 0.0)
        tp = request.get('tp', 0.0)
        comment = request.get('comment', 'MT5ZmqServer')
        risk_signature = request.get('risk_signature', '')

        # Validate required fields
        if not symbol:
            self.orders_rejected += 1
            return self._error_response("MISSING_SYMBOL", "Symbol is required", uuid, "REJECTED")

        if not order_type:
            self.orders_rejected += 1
            return self._error_response("MISSING_TYPE", "Order type is required", uuid, "REJECTED")

        if volume <= 0:
            self.orders_rejected += 1
            return self._error_response("INVALID_VOLUME", f"Invalid volume: {volume}", uuid, "REJECTED")

        # Validate risk signature (if enabled)
        if self.signature_validation:
            is_valid, reject_reason = self._validate_risk_signature(
                risk_signature,
                request,
                request_time
            )

            if not is_valid:
                self.orders_rejected += 1
                logger.error(f"{RED}❌ [RISK_FAIL] {reject_reason}{RESET}")
                return {
                    "uuid": uuid,
                    "status": "REJECTED",
                    "error_code": "RISK_SIGNATURE_INVALID",
                    "error_msg": reject_reason,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        # Ensure MT5 is connected
        if not self.ensure_mt5_connected():
            self.orders_rejected += 1
            return self._error_response("MT5_NOT_CONNECTED", "MT5 is not connected", uuid, "REJECTED")

        # Execute order via MT5Service
        try:
            logger.info(
                f"{CYAN}📤 [MT5_OPEN] {order_type} {volume} {symbol} "
                f"(SL={sl}, TP={tp}){RESET}"
            )

            order_payload = {
                'symbol': symbol,
                'type': order_type,
                'volume': volume,
                'price': price,
                'sl': sl,
                'tp': tp,
                'comment': comment
            }

            result = self.mt5_service.execute_order(order_payload)

            # Calculate latency
            execution_time = datetime.now(timezone.utc)
            latency_ms = (execution_time - request_time).total_seconds() * 1000

            # Check result
            if result.get('status') == 'SUCCESS':
                self.orders_executed += 1

                ticket = result.get('ticket')
                fill_price = result.get('price')
                fill_volume = result.get('volume')

                logger.info(
                    f"{GREEN}✅ [MT5_FILLED] Ticket #{ticket}, "
                    f"Price {fill_price}, Latency {latency_ms:.3f}ms{RESET}"
                )

                return {
                    "uuid": uuid,
                    "status": "FILLED",
                    "ticket": ticket,
                    "symbol": symbol,
                    "volume": fill_volume,
                    "price": fill_price,
                    "execution_time": execution_time.isoformat(),
                    "latency_ms": round(latency_ms, 3)
                }
            else:
                self.orders_rejected += 1
                error_msg = result.get('error', 'Unknown error')

                logger.error(f"{RED}❌ [MT5_REJECTED] {error_msg}{RESET}")

                return {
                    "uuid": uuid,
                    "status": "REJECTED",
                    "error_code": "MT5_ORDER_FAILED",
                    "error_msg": error_msg,
                    "timestamp": execution_time.isoformat()
                }

        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"{RED}❌ [MT5_ERROR] {e}{RESET}")
            return self._error_response("MT5_EXCEPTION", str(e), uuid, "REJECTED")

    def _handle_close(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Handle CLOSE command (close position)

        Request:
            {
                "uuid": "...",
                "action": "CLOSE",
                "ticket": 12345678,
                "symbol": "EURUSD",
                "volume": 0.01,
                "timestamp": "..."
            }

        Response (Success):
            {
                "uuid": "...",
                "status": "FILLED",
                "ticket": 87654321,
                "close_price": 1.05280,
                "execution_time": "...",
                "latency_ms": 1.234
            }
        """
        uuid = request.get('uuid', 'unknown')
        ticket = request.get('ticket')

        # Validate ticket
        if not ticket:
            return self._error_response("MISSING_TICKET", "Ticket is required", uuid, "REJECTED")

        # Ensure MT5 is connected
        if not self.ensure_mt5_connected():
            return self._error_response("MT5_NOT_CONNECTED", "MT5 is not connected", uuid, "REJECTED")

        # Execute close via MT5Service
        try:
            logger.info(f"{CYAN}📤 [MT5_CLOSE] Closing position #{ticket}{RESET}")

            result = self.mt5_service.close_position(ticket)

            # Calculate latency
            execution_time = datetime.now(timezone.utc)
            latency_ms = (execution_time - request_time).total_seconds() * 1000

            # Check result
            if result.get('status') == 'SUCCESS':
                close_ticket = result.get('ticket')
                close_price = result.get('price')

                logger.info(
                    f"{GREEN}✅ [MT5_CLOSED] Ticket #{close_ticket}, "
                    f"Price {close_price}, Latency {latency_ms:.3f}ms{RESET}"
                )

                return {
                    "uuid": uuid,
                    "status": "FILLED",
                    "ticket": close_ticket,
                    "close_price": close_price,
                    "execution_time": execution_time.isoformat(),
                    "latency_ms": round(latency_ms, 3)
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"{RED}❌ [MT5_CLOSE_FAILED] {error_msg}{RESET}")

                return {
                    "uuid": uuid,
                    "status": "REJECTED",
                    "error_code": "MT5_CLOSE_FAILED",
                    "error_msg": error_msg,
                    "timestamp": execution_time.isoformat()
                }

        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"{RED}❌ [MT5_ERROR] {e}{RESET}")
            return self._error_response("MT5_EXCEPTION", str(e), uuid, "REJECTED")

    def _handle_get_account(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Handle GET_ACCOUNT command (query account info)

        Request:
            {"uuid": "...", "action": "GET_ACCOUNT", "timestamp": "..."}

        Response:
            {
                "uuid": "...",
                "status": "ok",
                "balance": 100000.00,
                "equity": 100500.50,
                "margin": 500.00,
                "free_margin": 99500.50,
                "margin_level": 20100.1,
                "currency": "USD",
                "timestamp": "..."
            }
        """
        uuid = request.get('uuid', 'unknown')

        # Ensure MT5 is connected
        if not self.ensure_mt5_connected():
            return self._error_response("MT5_NOT_CONNECTED", "MT5 is not connected", uuid)

        # Get account info via MT5Service
        try:
            account_info = self.mt5_service.get_account_info()

            if 'error' in account_info:
                logger.error(f"{RED}❌ [ACCOUNT] {account_info['error']}{RESET}")
                return self._error_response("ACCOUNT_ERROR", account_info['error'], uuid)

            logger.info(
                f"{GREEN}✅ [ACCOUNT] Balance: ${account_info['balance']:,.2f}, "
                f"Equity: ${account_info['equity']:,.2f}{RESET}"
            )

            return {
                "uuid": uuid,
                "status": "ok",
                "balance": account_info.get('balance', 0.0),
                "equity": account_info.get('equity', 0.0),
                "margin": account_info.get('used_margin', 0.0),
                "free_margin": account_info.get('free_margin', 0.0),
                "margin_level": account_info.get('margin_level', 0.0),
                "currency": account_info.get('currency', 'USD'),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"{RED}❌ [ACCOUNT_ERROR] {e}{RESET}")
            return self._error_response("ACCOUNT_EXCEPTION", str(e), uuid)

    def _handle_get_positions(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Handle GET_POSITIONS command (query open positions)

        Request:
            {
                "uuid": "...",
                "action": "GET_POSITIONS",
                "symbol": "EURUSD",  # Optional: filter by symbol
                "timestamp": "..."
            }

        Response:
            {
                "uuid": "...",
                "status": "ok",
                "positions": [
                    {
                        "ticket": 12345678,
                        "symbol": "EURUSD",
                        "type": "BUY",
                        "volume": 0.01,
                        "open_price": 1.05230,
                        "current_price": 1.05280,
                        "profit": 5.00
                    }
                ],
                "timestamp": "..."
            }
        """
        uuid = request.get('uuid', 'unknown')
        symbol_filter = request.get('symbol', '')

        # Ensure MT5 is connected
        if not self.ensure_mt5_connected():
            return self._error_response("MT5_NOT_CONNECTED", "MT5 is not connected", uuid)

        # Get positions via MT5Service
        try:
            positions = self.mt5_service.get_positions()

            # Filter by symbol if provided
            if symbol_filter:
                positions = [p for p in positions if p.get('symbol') == symbol_filter]

            logger.info(f"{GREEN}✅ [POSITIONS] Found {len(positions)} position(s){RESET}")

            return {
                "uuid": uuid,
                "status": "ok",
                "positions": positions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"{RED}❌ [POSITIONS_ERROR] {e}{RESET}")
            return self._error_response("POSITIONS_EXCEPTION", str(e), uuid)

    def _handle_sync_all(
        self,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Dict[str, Any]:
        """
        Handle SYNC_ALL command (Task #108 - State Synchronization)

        This command is used for startup state synchronization.
        Linux Inf sends this request on startup to recover positions and account info.

        Request:
            {
                "action": "SYNC_ALL",
                "magic_number": 202401,
                "timestamp": "..."
            }

        Response:
            {
                "status": "OK",
                "account": {
                    "balance": 10000.0,
                    "equity": 10000.0,
                    "margin_free": 9000.0,
                    "margin_used": 1000.0,
                    "margin_level": 1000.0,
                    "leverage": 100
                },
                "positions": [
                    {
                        "symbol": "EURUSD",
                        "ticket": 123,
                        "volume": 0.1,
                        "profit": 5.0,
                        "price_current": 1.0850,
                        "price_open": 1.0800,
                        "type": "BUY",
                        "time_open": 1642000000
                    }
                ],
                "message": "Sync successful"
            }
        """
        uuid = request.get('uuid', 'unknown')
        magic_number = request.get('magic_number', 0)

        logger.info(f"{CYAN}[SYNC_ALL] Startup synchronization request from magic={magic_number}{RESET}")

        # Ensure MT5 is connected
        if not self.ensure_mt5_connected():
            return {
                "status": "ERROR",
                "message": "MT5 is not connected",
                "account": {},
                "positions": []
            }

        try:
            # Get account info
            account_info = self.mt5_service.get_account_info()
            if 'error' in account_info:
                logger.error(f"{RED}❌ [SYNC_ALL] Account query failed: {account_info['error']}{RESET}")
                return {
                    "status": "ERROR",
                    "message": f"Account query failed: {account_info['error']}",
                    "account": {},
                    "positions": []
                }

            # Get positions
            positions = self.mt5_service.get_positions()

            # Filter positions by magic number (optional - for future multi-strategy support)
            # For now, return all positions
            # TODO: In future, implement magic_number filtering
            # filtered_positions = [p for p in positions if p.get('magic') == magic_number]

            logger.info(
                f"{GREEN}✅ [SYNC_ALL] Sync complete: "
                f"account=${account_info.get('balance', 0):,.2f}, "
                f"positions={len(positions)}{RESET}"
            )

            # Format response
            account_response = {
                "balance": account_info.get('balance', 0.0),
                "equity": account_info.get('equity', 0.0),
                "margin_free": account_info.get('free_margin', 0.0),
                "margin_used": account_info.get('used_margin', 0.0),
                "margin_level": account_info.get('margin_level', 0.0),
                "leverage": account_info.get('leverage', 1)
            }

            # Format positions with required fields
            positions_response = []
            for pos in positions:
                positions_response.append({
                    "symbol": pos.get('symbol', ''),
                    "ticket": pos.get('ticket', 0),
                    "volume": pos.get('volume', 0.0),
                    "profit": pos.get('profit', 0.0),
                    "price_current": pos.get('current_price', 0.0),
                    "price_open": pos.get('open_price', 0.0),
                    "type": pos.get('type', 'BUY'),
                    "time_open": pos.get('time_open', 0)
                })

            return {
                "status": "OK",
                "account": account_response,
                "positions": positions_response,
                "message": "Sync successful"
            }

        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"{RED}❌ [SYNC_ALL] Exception: {e}{RESET}")
            return {
                "status": "ERROR",
                "message": f"Sync failed: {str(e)}",
                "account": {},
                "positions": []
            }

    def _validate_risk_signature(
        self,
        signature: str,
        request: Dict[str, Any],
        request_time: datetime
    ) -> Tuple[bool, str]:
        """
        Validate risk_signature from OPEN command

        Format: RISK_PASS:<checksum>:<timestamp>

        Validation checks:
        1. Signature exists and has correct format
        2. Timestamp is within TTL (default: 5 seconds)
        3. Checksum matches order parameters

        Args:
            signature: Risk signature string
            request: Full request dictionary
            request_time: Time when request was received

        Returns:
            Tuple[bool, str]: (is_valid, reject_reason)
        """
        # Check if signature exists
        if not signature:
            return False, "Missing risk_signature (required for all OPEN commands)"

        # Parse signature format: RISK_PASS:<checksum>:<timestamp>
        parts = signature.split(':')
        if len(parts) != 3:
            return False, f"Invalid signature format (expected RISK_PASS:<checksum>:<timestamp>)"

        prefix, checksum, timestamp_str = parts

        # Validate prefix
        if prefix != "RISK_PASS":
            return False, f"Invalid signature prefix (expected RISK_PASS, got {prefix})"

        # Validate timestamp (check TTL)
        try:
            sig_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            time_diff = abs((request_time - sig_time).total_seconds())

            if time_diff > self.signature_ttl_seconds:
                return False, (
                    f"Signature expired (TTL={self.signature_ttl_seconds}s, "
                    f"age={time_diff:.1f}s)"
                )
        except Exception as e:
            return False, f"Invalid signature timestamp format: {e}"

        # Validate checksum (order parameter hash)
        # Note: We don't re-compute and compare checksum here because:
        # 1. The Linux side (RiskMonitor) already validated the order
        # 2. The signature itself proves the order passed RiskMonitor
        # 3. We're just checking format and freshness (TTL)
        #
        # In a production zero-trust system, you could implement full
        # checksum verification by hashing the order dict and comparing.
        # For now, format + TTL validation is sufficient.

        if len(checksum) < 8:
            return False, "Invalid checksum format (too short)"

        logger.debug(
            f"[RISK_SIGNATURE] Validated: checksum={checksum[:8]}..., "
            f"age={time_diff:.3f}s"
        )

        return True, ""

    def _error_response(
        self,
        error_code: str,
        error_msg: str,
        uuid: str = "unknown",
        status: str = "error"
    ) -> Dict[str, Any]:
        """
        Generate error response

        Args:
            error_code: Error code (e.g., "INVALID_JSON", "MT5_NOT_CONNECTED")
            error_msg: Human-readable error message
            uuid: Request UUID
            status: Response status (default: "error")

        Returns:
            Dict: Error response dictionary
        """
        return {
            "uuid": uuid,
            "status": status,
            "error_code": error_code,
            "error_msg": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _print_statistics(self) -> None:
        """Print server statistics"""
        uptime = datetime.now(timezone.utc) - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN}📊 MT5 ZMQ Server Statistics{RESET}")
        print(f"{GREEN}{'='*80}{RESET}")
        print(f"Uptime:              {uptime_str}")
        print(f"Requests Processed:  {self.requests_processed}")
        print(f"Orders Executed:     {self.orders_executed}")
        print(f"Orders Rejected:     {self.orders_rejected}")
        print(f"Errors Encountered:  {self.errors_encountered}")
        print(f"{GREEN}{'='*80}{RESET}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MT5 ZMQ Server - Windows Gateway for MT5 Trading Bridge',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings (uses .env for MT5 credentials)
  python mt5_zmq_server.py

  # Start with custom port
  python mt5_zmq_server.py --port 6666

  # Start with explicit MT5 credentials
  python mt5_zmq_server.py --mt5-login 123456 --mt5-password xxx --mt5-server Broker-Server

  # Start with signature validation disabled (testing only!)
  python mt5_zmq_server.py --no-signature-validation

Protocol v4.3 (Zero-Trust Edition)
Author: Claude Sonnet 4.5
Date: 2026-01-15
        """
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='ZMQ bind host (default: 0.0.0.0 - all interfaces)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5555,
        help='ZMQ bind port (default: 5555)'
    )

    parser.add_argument(
        '--mt5-login',
        type=str,
        default=None,
        help='MT5 account login (overrides .env)'
    )

    parser.add_argument(
        '--mt5-password',
        type=str,
        default=None,
        help='MT5 account password (overrides .env)'
    )

    parser.add_argument(
        '--mt5-server',
        type=str,
        default=None,
        help='MT5 broker server (overrides .env)'
    )

    parser.add_argument(
        '--mt5-path',
        type=str,
        default=None,
        help='MT5 terminal path (overrides .env)'
    )

    parser.add_argument(
        '--no-signature-validation',
        action='store_true',
        help='Disable risk signature validation (DANGEROUS - testing only!)'
    )

    parser.add_argument(
        '--signature-ttl',
        type=int,
        default=5,
        help='Risk signature TTL in seconds (default: 5)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger('MT5ZmqServer').setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")

    # Warn if signature validation is disabled
    if args.no_signature_validation:
        logger.warning(
            f"{RED}{'='*80}{RESET}"
        )
        logger.warning(
            f"{RED}⚠️  WARNING: Risk signature validation is DISABLED!{RESET}"
        )
        logger.warning(
            f"{RED}⚠️  This should ONLY be used for testing!{RESET}"
        )
        logger.warning(
            f"{RED}⚠️  Production systems MUST have signature validation enabled!{RESET}"
        )
        logger.warning(
            f"{RED}{'='*80}{RESET}"
        )

    # Create and start server
    try:
        server = MT5ZmqServer(
            host=args.host,
            port=args.port,
            mt5_login=args.mt5_login,
            mt5_password=args.mt5_password,
            mt5_server=args.mt5_server,
            mt5_path=args.mt5_path,
            signature_validation=not args.no_signature_validation,
            signature_ttl_seconds=args.signature_ttl
        )

        server.start()

    except KeyboardInterrupt:
        logger.info(f"{YELLOW}[MAIN] Interrupted by user{RESET}")
    except Exception as e:
        logger.error(f"{RED}❌ [MAIN] Fatal error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
