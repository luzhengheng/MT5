"""
Work Order #022: Windows ZeroMQ Service Adapter
================================================

Binds to 0.0.0.0 to accept connections from Linux Brain.

This service runs on the Windows side (GTW) and handles incoming commands
from the Linux Brain, routing them to the MT5 handler.

Architecture:
- REP Socket: Listens on port 5555 for commands
- PUB Socket: Publishes on port 5556 for tick data
- Runs in daemon thread for non-blocking operation
- Routes actions to MT5 handler

Usage (Windows side):
    from src.gateway.zmq_service import ZmqGatewayService
    from src.gateway.mt5_service import MT5Service

    mt5 = MT5Service()
    mt5.connect()

    gateway = ZmqGatewayService(mt5_handler=mt5)
    gateway.start()

    # Keep running...
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        gateway.stop()
"""

import zmq
import logging
import threading
from typing import Optional, Dict, Any

from src.mt5_bridge.protocol import (
    ZMQ_PORT_CMD,
    ZMQ_PORT_DATA,
    ResponseStatus,
    create_response,
    validate_request
)

logger = logging.getLogger(__name__)


# ============================================================================
# ZeroMQ Gateway Service (Windows Side)
# ============================================================================

class ZmqGatewayService:
    """
    ZeroMQ service adapter for Windows Gateway.

    This service:
    1. Listens for commands from Linux Brain (REP socket)
    2. Publishes tick data to subscribers (PUB socket)
    3. Routes commands to MT5 handler
    4. Runs in background daemon thread

    Thread Safety:
        - Command loop runs in separate daemon thread
        - MT5 handler calls are serialized
        - publish_tick() is thread-safe

    Attributes:
        mt5: MT5 handler instance (e.g., MT5Service)
        context (zmq.Context): ZeroMQ context
        rep_socket (zmq.Socket): Command channel socket
        pub_socket (zmq.Socket): Data channel socket
        running (bool): Service running flag
    """

    def __init__(self, mt5_handler):
        """
        Initialize ZeroMQ Gateway Service.

        Args:
            mt5_handler: Object with methods like:
                - execute_order(payload) -> Dict
                - get_account_info() -> Dict
                - get_positions() -> List[Dict]
                - close_position(ticket) -> Dict

        Example:
            >>> from src.gateway.mt5_service import MT5Service
            >>> mt5 = MT5Service()
            >>> gateway = ZmqGatewayService(mt5_handler=mt5)
        """
        self.mt5 = mt5_handler
        self.context = zmq.Context()
        self.running = False
        self._command_thread: Optional[threading.Thread] = None

        # ====================================================================
        # Command Channel (REP) - Bind to all interfaces
        # ====================================================================
        self.rep_socket = self.context.socket(zmq.REP)
        cmd_addr = f"tcp://0.0.0.0:{ZMQ_PORT_CMD}"
        self.rep_socket.bind(cmd_addr)
        logger.info(f"[ZMQ Gateway] Command Channel bound to {cmd_addr}")

        # ====================================================================
        # Data Channel (PUB) - Bind to all interfaces
        # ====================================================================
        self.pub_socket = self.context.socket(zmq.PUB)
        data_addr = f"tcp://0.0.0.0:{ZMQ_PORT_DATA}"
        self.pub_socket.bind(data_addr)
        logger.info(f"[ZMQ Gateway] Data Channel bound to {data_addr}")

    # ========================================================================
    # Service Lifecycle
    # ========================================================================

    def start(self):
        """
        Start the gateway service.

        Launches background daemon thread to handle incoming commands.

        Example:
            >>> gateway = ZmqGatewayService(mt5_handler=mt5)
            >>> gateway.start()
            >>> # Service is now running in background
        """
        if self.running:
            logger.warning("[ZMQ Gateway] Already running")
            return

        self.running = True
        self._command_thread = threading.Thread(
            target=self._command_loop,
            daemon=True,
            name="ZMQ-Gateway-Thread"
        )
        self._command_thread.start()

        logger.info("[ZMQ Gateway] Service started")

    def stop(self):
        """
        Stop the gateway service.

        Gracefully shuts down command loop and closes sockets.

        Example:
            >>> gateway.stop()
            >>> # Service is now stopped
        """
        if not self.running:
            logger.warning("[ZMQ Gateway] Not running")
            return

        logger.info("[ZMQ Gateway] Stopping service...")
        self.running = False

        # Wait for thread to finish (with timeout)
        if self._command_thread:
            self._command_thread.join(timeout=2.0)

        # Close sockets
        self.rep_socket.close()
        self.pub_socket.close()
        self.context.term()

        logger.info("[ZMQ Gateway] Service stopped")

    # ========================================================================
    # Command Processing Loop
    # ========================================================================

    def _command_loop(self):
        """
        Main command processing loop (runs in daemon thread).

        Continuously receives requests, routes them to MT5 handler,
        and sends responses.

        This method runs until self.running is set to False.
        """
        logger.info("[ZMQ Gateway] Command loop started")

        while self.running:
            try:
                # Receive request (with timeout to allow graceful shutdown)
                self.rep_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second
                req = self.rep_socket.recv_json()

                # Validate request structure
                if not validate_request(req):
                    logger.warning(f"[ZMQ Gateway] Invalid request structure: {req}")
                    error_resp = create_response(
                        req_id=req.get('req_id', 'unknown'),
                        status=ResponseStatus.ERROR,
                        error="Invalid request structure"
                    )
                    self.rep_socket.send_json(error_resp)
                    continue

                # Process request
                response = self._process_request(req)

                # Send response
                self.rep_socket.send_json(response)

            except zmq.Again:
                # Timeout - continue loop to check self.running
                continue

            except Exception as e:
                logger.error(f"[ZMQ Gateway] Loop error: {e}")
                # Try to send error response if possible
                try:
                    error_resp = create_response(
                        req_id="unknown",
                        status=ResponseStatus.ERROR,
                        error=str(e)
                    )
                    self.rep_socket.send_json(error_resp)
                except:
                    pass

        logger.info("[ZMQ Gateway] Command loop stopped")

    def _process_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single request and return response.

        Args:
            req: Request dictionary with validated structure

        Returns:
            Response dictionary

        Routing Table:
            HEARTBEAT -> {"status": "alive"}
            OPEN_ORDER -> mt5.execute_order(payload)
            CLOSE_POSITION -> mt5.close_position(payload)
            GET_ACCOUNT_INFO -> mt5.get_account_info()
            GET_POSITIONS -> mt5.get_positions()
            KILL_SWITCH -> Emergency stop logic
        """
        action = req.get('action')
        req_id = req.get('req_id')
        payload = req.get('payload', {})

        logger.debug(f"[ZMQ Gateway] Processing: {action} (req_id={req_id})")

        response_data = None
        error_msg = None
        status = ResponseStatus.SUCCESS

        try:
            # ================================================================
            # Routing Logic
            # ================================================================

            if action == "HEARTBEAT":
                # Simple health check
                response_data = {"status": "alive", "service": "MT5 Gateway"}

            elif action == "OPEN_ORDER":
                # Execute new order
                response_data = self.mt5.execute_order(payload)

            elif action == "CLOSE_POSITION":
                # Close existing position
                ticket = payload.get('ticket')
                if not ticket:
                    raise ValueError("Missing 'ticket' in payload")
                response_data = self.mt5.close_position(ticket)

            elif action == "GET_ACCOUNT_INFO":
                # Query account information
                response_data = self.mt5.get_account_info()

            elif action == "GET_POSITIONS":
                # Query open positions
                response_data = self.mt5.get_positions()

            elif action == "KILL_SWITCH":
                # Emergency stop all trading
                logger.critical("[ZMQ Gateway] KILL SWITCH ACTIVATED!")
                response_data = self._activate_kill_switch()

            else:
                # Unknown action
                status = ResponseStatus.ERROR
                error_msg = f"Unknown action: {action}"
                logger.warning(f"[ZMQ Gateway] {error_msg}")

        except Exception as e:
            # Handler error
            status = ResponseStatus.ERROR
            error_msg = str(e)
            logger.error(f"[ZMQ Gateway] Handler error: {error_msg} (action={action})")

        # Create response
        response = create_response(req_id, status, response_data, error_msg)
        logger.debug(f"[ZMQ Gateway] Response: {status.value} (req_id={req_id})")

        return response

    # ========================================================================
    # Data Publishing
    # ========================================================================

    def publish_tick(self, tick_data: Dict[str, Any]):
        """
        Publish tick data to all subscribers.

        This is non-blocking and thread-safe.

        Args:
            tick_data: Tick data dictionary (e.g., {"symbol": "EURUSD", "bid": 1.05, ...})

        Example:
            >>> gateway.publish_tick({
            ...     'symbol': 'EURUSD.s',
            ...     'bid': 1.05123,
            ...     'ask': 1.05125,
            ...     'timestamp': time.time()
            ... })
        """
        if not self.running:
            logger.warning("[ZMQ Gateway] Cannot publish - service not running")
            return

        try:
            self.pub_socket.send_json(tick_data)
            logger.debug(f"[ZMQ Gateway] Published tick: {tick_data.get('symbol')}")
        except Exception as e:
            logger.error(f"[ZMQ Gateway] Publish error: {e}")

    # ========================================================================
    # Emergency Controls
    # ========================================================================

    def _activate_kill_switch(self) -> Dict[str, Any]:
        """
        Activate emergency kill switch.

        This should:
        1. Close all open positions
        2. Cancel all pending orders
        3. Disable new order placement

        Returns:
            Status report
        """
        logger.critical("[ZMQ Gateway] Executing KILL SWITCH protocol...")

        try:
            # Get all open positions
            positions = self.mt5.get_positions()

            # Close all positions
            closed_count = 0
            for pos in positions:
                try:
                    self.mt5.close_position(pos['ticket'])
                    closed_count += 1
                except Exception as e:
                    logger.error(f"[ZMQ Gateway] Failed to close position {pos['ticket']}: {e}")

            result = {
                "positions_closed": closed_count,
                "total_positions": len(positions),
                "timestamp": import_time().time()
            }

            logger.critical(f"[ZMQ Gateway] KILL SWITCH complete: {result}")
            return result

        except Exception as e:
            logger.error(f"[ZMQ Gateway] KILL SWITCH error: {e}")
            raise


# ============================================================================
# Helper Imports (to avoid circular dependencies)
# ============================================================================

def import_time():
    """Lazy import to avoid issues."""
    import time
    return time
