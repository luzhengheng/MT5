#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON Trading Client

Python strategy engine client for sending structured JSON trading commands
to the MT5 Gateway. Implements the JSON protocol v1.0 with idempotent
request handling and full error management.

Protocol: MT5-CRS JSON v1.0
Reference: docs/specs/PROTOCOL_JSON_v1.md
"""

import uuid
import time
import logging
from typing import Optional, Dict, Any

from src.mt5_bridge.zmq_client import ZmqClient

logger = logging.getLogger(__name__)


# ============================================================================
# JSON Trading Client (Linux Brain Side)
# ============================================================================

class JsonTradeClient:
    """
    Client for sending structured JSON trading commands to MT5 Gateway.

    Features:
    - Idempotent requests using UUID (req_id)
    - Structured JSON command/response format
    - Full error handling with MT5 return codes
    - Support for stop loss and take profit
    - Latency monitoring

    Attributes:
        zmq_client: ZmqClient instance for ZMQ communication

    Example:
        >>> client = JsonTradeClient()
        >>> response = client.trade(
        ...     symbol="EURUSD",
        ...     order_type="OP_BUY",
        ...     volume=0.01,
        ...     sl=1.04500,
        ...     tp=1.06000
        ... )
        >>> if not response["error"]:
        ...     print(f"Order #{response['ticket']} filled")
    """

    def __init__(self, zmq_client: Optional[ZmqClient] = None):
        """
        Initialize JSON Trade Client.

        Args:
            zmq_client: Optional existing ZmqClient instance (creates new if None)
        """
        if zmq_client:
            self.zmq_client = zmq_client
        else:
            self.zmq_client = ZmqClient()

        logger.info("[JsonTradeClient] Initialized")

    # ========================================================================
    # Main Trading Method
    # ========================================================================

    def trade(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        magic: int = 123456,
        comment: str = "MT5-CRS-AI",
        sl: float = 0.0,
        tp: float = 0.0
    ) -> Dict[str, Any]:
        """
        Send JSON trading command to execute an order.

        This is the main method for trading. It sends a structured JSON request
        to the Gateway and returns a structured response including order ticket,
        error status, and MT5 return code.

        Idempotency:
            - Generates unique UUID (req_id) for each request
            - Gateway deduplicates based on req_id
            - Safe to retry without fear of duplicate orders

        Args:
            symbol: Trading pair (e.g., "EURUSD")
            order_type: "OP_BUY" or "OP_SELL"
            volume: Order volume in lots (0.01 - 100.0)
            magic: Strategy identifier (default: 123456)
            comment: Order comment, max 31 chars (default: "MT5-CRS-AI")
            sl: Stop loss price (0 = no stop loss)
            tp: Take profit price (0 = no take profit)

        Returns:
            Dictionary with structure:
            {
                "error": bool,           # False = success, True = failure
                "ticket": int,           # Order number (0 if failed)
                "msg": str,              # Description or error message
                "retcode": int,          # MT5 return code
                "latency_ms": float      # Round-trip time in milliseconds
            }

        Raises:
            ConnectionError: If ZMQ gateway is unreachable
            ValueError: If arguments are invalid

        Example:
            >>> # Buy 0.01 lots of EURUSD with stop loss and take profit
            >>> response = client.trade(
            ...     symbol="EURUSD",
            ...     order_type="OP_BUY",
            ...     volume=0.01,
            ...     sl=1.04500,
            ...     tp=1.06000
            ... )
            >>> print(response)
            {
                "error": False,
                "ticket": 100234567,
                "msg": "Filled at 1.05123",
                "retcode": 10009,
                "latency_ms": 23.45
            }
        """
        # ====================================================================
        # Step 1: Validate inputs
        # ====================================================================

        if order_type not in ("OP_BUY", "OP_SELL"):
            raise ValueError(f"Invalid order_type: {order_type}. Must be OP_BUY or OP_SELL")

        if not (0.01 <= volume <= 100.0):
            raise ValueError(f"Invalid volume: {volume}. Must be between 0.01 and 100.0")

        if len(comment) > 31:
            raise ValueError(f"Comment too long: {len(comment)} chars. Max 31 chars")

        # ====================================================================
        # Step 2: Build JSON request with UUID
        # ====================================================================

        req_id = str(uuid.uuid4())  # Generate idempotent request ID

        request = {
            "action": "ORDER_SEND",
            "req_id": req_id,
            "payload": {
                "symbol": symbol,
                "type": order_type,
                "volume": float(volume),
                "magic": int(magic),
                "comment": comment,
                "sl": float(sl),
                "tp": float(tp)
            }
        }

        # ====================================================================
        # Step 3: Send via ZMQ and measure latency
        # ====================================================================

        logger.info(
            f"[JsonTradeClient] Sending: {order_type} {volume}L {symbol} "
            f"(req_id={req_id[:8]}..., sl={sl}, tp={tp})"
        )

        start_time = time.time()

        try:
            # Send raw JSON dictionary to Gateway
            # Gateway will route and execute
            self.zmq_client.req_socket.send_json(request)

            # Await response with timeout (2-10s)
            response = self.zmq_client.req_socket.recv_json()

            latency_ms = (time.time() - start_time) * 1000

            # ================================================================
            # Step 4: Parse response
            # ================================================================

            error = response.get("error", True)
            ticket = response.get("ticket", 0)
            msg = response.get("msg", "Unknown response")
            retcode = response.get("retcode", -4)

            # Log result
            if not error:
                logger.info(
                    f"[JsonTradeClient] ✅ SUCCESS: Order #{ticket} "
                    f"({latency_ms:.2f}ms): {msg}"
                )
            else:
                logger.warning(
                    f"[JsonTradeClient] ❌ FAILED (code={retcode}): {msg}"
                )

            return {
                "error": error,
                "ticket": ticket,
                "msg": msg,
                "retcode": retcode,
                "latency_ms": round(latency_ms, 2),
                "req_id": req_id
            }

        except Exception as e:
            logger.error(f"[JsonTradeClient] Communication error: {e}")
            raise

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def buy(
        self,
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 123456,
        comment: str = "MT5-CRS-AI"
    ) -> Dict[str, Any]:
        """
        Convenience method for buy orders.

        Args:
            symbol: Trading pair (e.g., "EURUSD")
            volume: Order volume in lots
            sl: Stop loss price
            tp: Take profit price
            magic: Strategy identifier
            comment: Order comment

        Returns:
            Response dictionary from trade()

        Example:
            >>> response = client.buy("EURUSD", 0.01, sl=1.04500, tp=1.06000)
        """
        return self.trade(
            symbol=symbol,
            order_type="OP_BUY",
            volume=volume,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment
        )

    def sell(
        self,
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 123456,
        comment: str = "MT5-CRS-AI"
    ) -> Dict[str, Any]:
        """
        Convenience method for sell orders.

        Args:
            symbol: Trading pair (e.g., "EURUSD")
            volume: Order volume in lots
            sl: Stop loss price
            tp: Take profit price
            magic: Strategy identifier
            comment: Order comment

        Returns:
            Response dictionary from trade()

        Example:
            >>> response = client.sell("EURUSD", 0.01, sl=1.06000, tp=1.04500)
        """
        return self.trade(
            symbol=symbol,
            order_type="OP_SELL",
            volume=volume,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment
        )

    # ========================================================================
    # Cleanup
    # ========================================================================

    def close(self):
        """
        Close ZMQ connection.

        Always call this when done to avoid resource leaks.

        Example:
            >>> client = JsonTradeClient()
            >>> try:
            ...     response = client.buy("EURUSD", 0.01)
            ... finally:
            ...     client.close()
        """
        self.zmq_client.close()
        logger.info("[JsonTradeClient] Closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============================================================================
# Singleton Instance
# ============================================================================

_client_instance: Optional[JsonTradeClient] = None


def get_json_trade_client(**kwargs) -> JsonTradeClient:
    """
    Get or create singleton JsonTradeClient instance.

    Args:
        **kwargs: Passed to JsonTradeClient constructor

    Returns:
        Singleton JsonTradeClient instance

    Example:
        >>> client1 = get_json_trade_client()
        >>> client2 = get_json_trade_client()
        >>> client1 is client2  # True
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = JsonTradeClient(**kwargs)
    return _client_instance
