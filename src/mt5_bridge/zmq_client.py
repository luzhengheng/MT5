"""
Work Order #022: Linux ZeroMQ Client
=====================================

Handles low-latency commands to the Windows Gateway.

This client runs on the Linux side (INF) and communicates with the Windows
Gateway (GTW) using ZeroMQ for high-performance, low-latency message passing.

Architecture:
- Command Channel: REQ/REP pattern (synchronous, blocking)
- Data Channel: SUB pattern (asynchronous, streaming)
- Fail-Fast: 2 second timeout on commands
- Zero-Copy: Minimal serialization overhead

Usage:
    from src.mt5_bridge.zmq_client import ZmqClient
    from src.mt5_bridge.protocol import Action

    client = ZmqClient()

    # Check connectivity
    if client.check_heartbeat():
        # Send order
        response = client.send_command(Action.OPEN_ORDER, {
            'symbol': 'EURUSD.s',
            'volume': 0.01,
            'side': 'BUY'
        })

    # Stream real-time data
    for tick in client.stream_data():
        print(tick)
"""

import zmq
import logging
from typing import Optional, Dict, Generator, Any

from .protocol import (
    Action,
    ResponseStatus,
    create_request,
    validate_response,
    GATEWAY_IP_INTERNAL,
    ZMQ_PORT_CMD,
    ZMQ_PORT_DATA
)

logger = logging.getLogger(__name__)


# ============================================================================
# ZeroMQ Client (Linux Brain Side)
# ============================================================================

class ZmqClient:
    """
    ZeroMQ client for communicating with MT5 Gateway.

    This client provides:
    1. Command Channel (REQ/REP): Synchronous commands with timeout
    2. Data Channel (SUB): Asynchronous tick data streaming
    3. Health Checks: Heartbeat verification
    4. Fail-Fast: Connection errors raise immediately

    Thread Safety:
        - Command Channel: NOT thread-safe (use locks if multi-threaded)
        - Data Channel: Safe for single consumer

    Attributes:
        context (zmq.Context): ZeroMQ context
        host (str): Gateway IP address
        req_socket (zmq.Socket): Command channel socket
        sub_socket (zmq.Socket): Data channel socket
    """

    def __init__(
        self,
        host: str = GATEWAY_IP_INTERNAL,
        req_port: int = ZMQ_PORT_CMD,
        sub_port: int = ZMQ_PORT_DATA,
        timeout_ms: int = 2000
    ):
        """
        Initialize ZeroMQ client.

        Args:
            host: Gateway IP address (default: 172.19.141.255)
            req_port: Command channel port (default: 5555)
            sub_port: Data channel port (default: 5556)
            timeout_ms: Command timeout in milliseconds (default: 2000)

        Example:
            >>> client = ZmqClient()
            >>> client = ZmqClient(host="192.168.1.100", timeout_ms=5000)
        """
        self.context = zmq.Context()
        self.host = host
        self.timeout_ms = timeout_ms

        # ====================================================================
        # 1. Command Channel (REQ/REP) - Synchronous & Blocking
        # ====================================================================
        self.req_socket = self.context.socket(zmq.REQ)
        req_addr = f"tcp://{self.host}:{req_port}"
        logger.info(f"[ZMQ Client] Connecting Command Channel to {req_addr}")
        self.req_socket.connect(req_addr)

        # Timeout Configuration (Fail Fast)
        self.req_socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        self.req_socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close

        # ====================================================================
        # 2. Data Channel (SUB) - Asynchronous
        # ====================================================================
        self.sub_socket = self.context.socket(zmq.SUB)
        sub_addr = f"tcp://{self.host}:{sub_port}"
        logger.info(f"[ZMQ Client] Connecting Data Channel to {sub_addr}")
        self.sub_socket.connect(sub_addr)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all

        logger.info(f"[ZMQ Client] Initialized (timeout={timeout_ms}ms)")

    # ========================================================================
    # Command Channel Operations
    # ========================================================================

    def send_command(
        self,
        action: Action,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send command and await acknowledgement.

        This is a synchronous, blocking call with timeout protection.

        Args:
            action: Action to perform (from Action enum)
            payload: Optional command data

        Returns:
            Response dictionary with structure:
            {
                'req_id': str,
                'status': 'SUCCESS' | 'ERROR' | 'PENDING',
                'timestamp': float,
                'data': Any,
                'error': Optional[str]
            }

        Raises:
            ConnectionError: If gateway doesn't respond within timeout
            ValueError: If response is malformed

        Example:
            >>> client = ZmqClient()
            >>> resp = client.send_command(Action.GET_ACCOUNT_INFO)
            >>> if resp['status'] == 'SUCCESS':
            ...     print(resp['data'])
        """
        request = create_request(action, payload)
        req_id = request['req_id']

        logger.debug(f"[ZMQ Client] Sending command: {action.value} (req_id={req_id})")

        try:
            # Send request
            self.req_socket.send_json(request)

            # Await response (with timeout)
            response = self.req_socket.recv_json()

            # Validate response structure
            if not validate_response(response):
                raise ValueError(f"Malformed response: {response}")

            # Log errors
            if response.get('status') == ResponseStatus.ERROR.value:
                error_msg = response.get('error', 'Unknown error')
                logger.error(f"[ZMQ Client] Gateway Error: {error_msg} (req_id={req_id})")

            logger.debug(f"[ZMQ Client] Received response: {response['status']} (req_id={req_id})")
            return response

        except zmq.Again:
            # Timeout occurred
            error_msg = (
                f"Gateway Timeout ({self.host})! "
                f"No response within {self.timeout_ms}ms. "
                f"Possible network partition or gateway offline."
            )
            logger.critical(f"[ZMQ Client] {error_msg}")
            raise ConnectionError(error_msg)

        except Exception as e:
            logger.error(f"[ZMQ Client] Command failed: {str(e)} (req_id={req_id})")
            raise

    # ========================================================================
    # Data Channel Operations
    # ========================================================================

    def stream_data(self, max_messages: Optional[int] = None) -> Generator[Dict, None, None]:
        """
        Yields real-time tick data from the PUB stream.

        This is a blocking generator that continuously receives messages
        from the data channel until stopped or an error occurs.

        Args:
            max_messages: Optional limit on number of messages (for testing)

        Yields:
            Tick data dictionaries

        Example:
            >>> client = ZmqClient()
            >>> for tick in client.stream_data():
            ...     print(f"Price: {tick['bid']}")
            ...     if some_condition:
            ...         break
        """
        count = 0
        logger.info("[ZMQ Client] Starting data stream...")

        while True:
            try:
                msg = self.sub_socket.recv_json()
                yield msg

                count += 1
                if max_messages and count >= max_messages:
                    logger.info(f"[ZMQ Client] Reached max messages ({max_messages})")
                    break

            except zmq.ZMQError as e:
                logger.error(f"[ZMQ Client] Stream Error: {e}")
                break
            except Exception as e:
                logger.error(f"[ZMQ Client] Unexpected error in stream: {e}")
                break

        logger.info("[ZMQ Client] Data stream stopped")

    # ========================================================================
    # Health Check
    # ========================================================================

    def check_heartbeat(self) -> bool:
        """
        Verify connectivity to Gateway.

        Sends a HEARTBEAT command and expects SUCCESS response.

        Returns:
            True if gateway is alive and responding
            False if gateway is unreachable or returns error

        Example:
            >>> client = ZmqClient()
            >>> if client.check_heartbeat():
            ...     print("Gateway is healthy")
            ... else:
            ...     print("Gateway is down")
        """
        try:
            logger.debug("[ZMQ Client] Checking heartbeat...")
            response = self.send_command(Action.HEARTBEAT)
            is_alive = response.get('status') == ResponseStatus.SUCCESS.value

            if is_alive:
                logger.info("[ZMQ Client] Heartbeat: OK")
            else:
                logger.warning(f"[ZMQ Client] Heartbeat: FAILED ({response.get('error')})")

            return is_alive

        except Exception as e:
            logger.error(f"[ZMQ Client] Heartbeat check failed: {e}")
            return False

    # ========================================================================
    # Cleanup
    # ========================================================================

    def close(self):
        """
        Close sockets and terminate context.

        Always call this when done to avoid resource leaks.

        Example:
            >>> client = ZmqClient()
            >>> try:
            ...     client.send_command(Action.HEARTBEAT)
            ... finally:
            ...     client.close()
        """
        logger.info("[ZMQ Client] Closing connections...")

        self.req_socket.close()
        self.sub_socket.close()
        self.context.term()

        logger.info("[ZMQ Client] Closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============================================================================
# Singleton Instance (Optional Convenience)
# ============================================================================

_client_instance: Optional[ZmqClient] = None


def get_zmq_client(**kwargs) -> ZmqClient:
    """
    Get or create singleton ZeroMQ client instance.

    Args:
        **kwargs: Passed to ZmqClient constructor

    Returns:
        Singleton ZmqClient instance

    Example:
        >>> client1 = get_zmq_client()
        >>> client2 = get_zmq_client()
        >>> client1 is client2
        True
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = ZmqClient(**kwargs)
    return _client_instance
