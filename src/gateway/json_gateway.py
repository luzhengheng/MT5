#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON Gateway Router

Handles routing of JSON trading commands to MT5 with idempotent request
handling using UUID-based deduplication.

Protocol: MT5-CRS JSON v1.0
Reference: docs/specs/PROTOCOL_JSON_v1.md
"""

import time
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict

# Import resilience module for @wait_or_die (Protocol v4.4)
try:
    from src.utils.resilience import wait_or_die
    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
CACHE_MAX_SIZE = 10000  # Maximum cached requests
CACHE_TTL_SECONDS = 3600  # Cache time-to-live: 1 hour


class JsonGatewayRouter:
    """
    Routes JSON trading commands to MT5 with idempotent request handling.

    Features:
    - UUID-based request deduplication (idempotency)
    - LRU cache cleanup when size exceeds limit
    - TTL-based cache expiration
    - Full error handling with MT5 return codes

    Attributes:
        mt5: MT5 handler instance
        req_id_ticket_cache: Dict mapping req_id -> (ticket, timestamp)

    Example:
        >>> from src.gateway.mt5_service import MT5Service
        >>> mt5 = MT5Service()
        >>> router = JsonGatewayRouter(mt5)
        >>>
        >>> request = {
        ...     "action": "ORDER_SEND",
        ...     "req_id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "payload": {
        ...         "symbol": "EURUSD",
        ...         "type": "OP_BUY",
        ...         "volume": 0.01,
        ...         "sl": 1.04500,
        ...         "tp": 1.06000
        ...     }
        ... }
        >>> response = router.process_json_request(request)
        >>> print(response["ticket"])
        100234567
    """

    def __init__(self, mt5_handler):
        """
        Initialize JSON Gateway Router.

        Args:
            mt5_handler: Object with methods like:
                - execute_order(payload) -> Dict
                - get_account_info() -> Dict
                - etc.
        """
        self.mt5 = mt5_handler

        # Idempotency cache: req_id -> (ticket, timestamp)
        self.req_id_ticket_cache: OrderedDict[str, tuple] = OrderedDict()

        logger.info("[JsonGatewayRouter] Initialized")

    # ========================================================================
    # Main Entry Point
    # ========================================================================

    def process_json_request(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process JSON trading request with idempotent handling.

        Steps:
        1. Extract req_id and action from request
        2. Check if req_id is already in cache (idempotency)
        3. If cached, return original ticket without re-executing
        4. If new, execute order and cache result
        5. Return response with error flag, ticket, and MT5 retcode

        Args:
            json_data: Request dictionary containing:
                - action: "ORDER_SEND" (v1.0 only)
                - req_id: UUID string (required for idempotency)
                - payload: Order data

        Returns:
            Response dictionary:
            {
                "error": bool,      # False = success, True = failure
                "ticket": int,      # Order number (0 if failed)
                "msg": str,         # Description or error
                "retcode": int      # MT5 return code
            }

        Example:
            >>> request = {
            ...     "action": "ORDER_SEND",
            ...     "req_id": "550e8400-...",
            ...     "payload": {"symbol": "EURUSD", ...}
            ... }
            >>> response = router.process_json_request(request)
            >>> assert response["error"] == False
            >>> assert response["ticket"] > 0
        """
        try:
            # ================================================================
            # Step 1: Extract and validate fields
            # ================================================================

            action = json_data.get("action")
            req_id = json_data.get("req_id")
            payload = json_data.get("payload", {})

            if not action:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": "Missing 'action' field",
                    "retcode": -2
                }

            if not req_id:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": "Missing 'req_id' field (required for idempotency)",
                    "retcode": -2
                }

            # ================================================================
            # Step 2: Check idempotency cache
            # ================================================================

            if req_id in self.req_id_ticket_cache:
                cached_ticket, cached_timestamp = self.req_id_ticket_cache[req_id]

                # Move to end (LRU)
                self.req_id_ticket_cache.move_to_end(req_id)

                logger.info(
                    f"[JsonGatewayRouter] ✓ IDEMPOTENT: "
                    f"Returning cached ticket {cached_ticket} for req_id={req_id[:8]}..."
                )

                return {
                    "error": False,
                    "ticket": cached_ticket,
                    "msg": f"Cached result (idempotent), original time: {cached_timestamp}",
                    "retcode": 10009
                }

            # ================================================================
            # Step 3: Process request based on action
            # ================================================================

            if action == "ORDER_SEND":
                result = self._handle_order_send(payload)
            else:
                result = {
                    "error": True,
                    "ticket": 0,
                    "msg": f"Unknown action: {action}",
                    "retcode": -2
                }

            # ================================================================
            # Step 4: Cache successful results
            # ================================================================

            ticket = result.get("ticket", 0)
            retcode = result.get("retcode")

            # Cache only successful orders
            if retcode == 10009 and ticket > 0:
                self.req_id_ticket_cache[req_id] = (ticket, time.time())

                # LRU cleanup if cache exceeds max size
                if len(self.req_id_ticket_cache) > CACHE_MAX_SIZE:
                    removed_req_id, _ = self.req_id_ticket_cache.popitem(last=False)
                    logger.warning(
                        f"[JsonGatewayRouter] Cache cleanup: removed oldest req_id "
                        f"{removed_req_id[:8]}... (cache size: {len(self.req_id_ticket_cache)})"
                    )

            return result

        except Exception as e:
            logger.error(f"[JsonGatewayRouter] Exception processing request: {e}")
            return {
                "error": True,
                "ticket": 0,
                "msg": f"Internal error: {str(e)}",
                "retcode": -4
            }

    # ========================================================================
    # MT5 Handler with Resilience (Protocol v4.4)
    # ========================================================================

    @wait_or_die(
        timeout=30,
        exponential_backoff=True,
        max_retries=5,
        initial_wait=1.0,
        max_wait=10.0
    ) if RESILIENCE_AVAILABLE else lambda f: f
    def _execute_order_with_resilience(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute order on MT5 handler with @wait_or_die resilience.

        Protocol v4.4: Implement robust MT5 API calls with automatic retry
        on transient network failures or service unavailability.

        Args:
            payload: Order data

        Returns:
            MT5 execution response

        Raises:
            ConnectionError: If MT5 handler call fails
            TimeoutError: If execution exceeds timeout
        """
        try:
            # Execute order on MT5 handler
            return self.mt5.execute_order(payload)
        except Exception as e:
            # Convert exceptions to ConnectionError for @wait_or_die
            if "timeout" in str(e).lower():
                raise TimeoutError(str(e))
            raise ConnectionError(str(e))

    # ========================================================================
    # Order Execution Handler
    # ========================================================================

    def _handle_order_send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ORDER_SEND action.

        Extracts fields from payload, validates them, calls MT5 handler,
        and returns structured response.

        Args:
            payload: Order data containing:
                - symbol: Trading pair (e.g., "EURUSD")
                - type: "OP_BUY" or "OP_SELL"
                - volume: Order volume in lots
                - magic: Strategy identifier (optional)
                - comment: Order comment (optional)
                - sl: Stop loss price (optional)
                - tp: Take profit price (optional)

        Returns:
            Response dictionary with structure:
            {
                "error": bool,
                "ticket": int,
                "msg": str,
                "retcode": int
            }
        """
        try:
            # Extract required fields
            symbol = payload.get("symbol")
            order_type = payload.get("type")
            volume = payload.get("volume")

            if not symbol:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": "Missing required field: symbol",
                    "retcode": -2
                }

            if not order_type:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": "Missing required field: type",
                    "retcode": -2
                }

            if volume is None:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": "Missing required field: volume",
                    "retcode": -2
                }

            # Extract optional fields with defaults
            magic = payload.get("magic", 123456)
            comment = payload.get("comment", "MT5-CRS-AI")
            sl = payload.get("sl", 0.0)
            tp = payload.get("tp", 0.0)

            # Validate ranges
            if not (0.01 <= float(volume) <= 100.0):
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": f"Invalid volume: {volume}. Valid range: 0.01-100.0",
                    "retcode": -3
                }

            if len(str(comment)) > 31:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": f"Comment too long: {len(comment)} chars. Max 31",
                    "retcode": -3
                }

            # ================================================================
            # Call MT5 handler to execute order (with resilience)
            # ================================================================

            logger.debug(
                f"[JsonGatewayRouter] Executing: {order_type} {volume}L {symbol} "
                f"(magic={magic}, sl={sl}, tp={tp})"
            )

            # Prepare order payload for MT5 execution
            order_payload = {
                "symbol": symbol,
                "volume": float(volume),
                "magic": int(magic),
                "comment": comment,
                "sl": float(sl),
                "tp": float(tp)
            }

            # Map "OP_BUY"/"OP_SELL" to MT5 handler method
            if order_type == "OP_BUY":
                order_payload["order_type"] = "BUY"
                if RESILIENCE_AVAILABLE:
                    logger.debug(
                        "[JsonGatewayRouter] Using @wait_or_die resilience "
                        "for MT5 order execution (5 retries, 30s timeout)"
                    )
                    result = self._execute_order_with_resilience(order_payload)
                else:
                    result = self.mt5.execute_order(**order_payload)

            elif order_type == "OP_SELL":
                order_payload["order_type"] = "SELL"
                if RESILIENCE_AVAILABLE:
                    logger.debug(
                        "[JsonGatewayRouter] Using @wait_or_die resilience "
                        "for MT5 order execution (5 retries, 30s timeout)"
                    )
                    result = self._execute_order_with_resilience(order_payload)
                else:
                    result = self.mt5.execute_order(**order_payload)
            else:
                return {
                    "error": True,
                    "ticket": 0,
                    "msg": f"Invalid order type: {order_type}. Must be OP_BUY or OP_SELL",
                    "retcode": -3
                }

            # ================================================================
            # Parse MT5 response
            # ================================================================

            ticket = result.get("ticket", 0)
            retcode = result.get("retcode")
            mt5_msg = result.get("msg", "Unknown")

            # Determine error based on retcode
            error = retcode != 10009  # 10009 = TRADE_RETCODE_DONE

            response = {
                "error": error,
                "ticket": ticket,
                "msg": mt5_msg,
                "retcode": retcode
            }

            log_level = logging.WARNING if error else logging.INFO
            logger.log(
                log_level,
                f"[JsonGatewayRouter] {'❌ FAILED' if error else '✅ SUCCESS'}: "
                f"Ticket {ticket}, Code {retcode}: {mt5_msg}"
            )

            return response

        except Exception as e:
            logger.error(f"[JsonGatewayRouter] Order execution error: {e}")
            return {
                "error": True,
                "ticket": 0,
                "msg": f"Order execution failed: {str(e)}",
                "retcode": -4
            }

    # ========================================================================
    # Cache Management
    # ========================================================================

    def cleanup_expired_cache(self) -> int:
        """
        Remove cache entries older than TTL.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        removed_count = 0

        # Create a list of expired keys (can't modify dict during iteration)
        expired_keys = [
            req_id
            for req_id, (ticket, timestamp) in self.req_id_ticket_cache.items()
            if current_time - timestamp > CACHE_TTL_SECONDS
        ]

        for req_id in expired_keys:
            del self.req_id_ticket_cache[req_id]
            removed_count += 1

        if removed_count > 0:
            logger.info(
                f"[JsonGatewayRouter] Cleaned up {removed_count} expired cache entries "
                f"(cache size now: {len(self.req_id_ticket_cache)})"
            )

        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache info:
            {
                "size": int,
                "max_size": int,
                "oldest_entry_age_seconds": float,
                "ttl_seconds": int
            }
        """
        oldest_age = None
        if self.req_id_ticket_cache:
            oldest_timestamp = list(self.req_id_ticket_cache.values())[0][1]
            oldest_age = time.time() - oldest_timestamp

        return {
            "size": len(self.req_id_ticket_cache),
            "max_size": CACHE_MAX_SIZE,
            "oldest_entry_age_seconds": oldest_age,
            "ttl_seconds": CACHE_TTL_SECONDS
        }

    def clear_cache(self):
        """Clear all cached requests."""
        self.req_id_ticket_cache.clear()
        logger.info("[JsonGatewayRouter] Cache cleared")
