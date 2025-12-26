"""
Work Order #022: ZeroMQ Protocol Definition
============================================

Shared constants and message structures for Brain-Gateway communication.

This module defines the "language" spoken between the Linux Brain (INF) and
Windows Gateway (GTW) using ZeroMQ.

Architecture:
- Command Channel (REQ/REP): Port 5555 - Synchronous commands
- Data Channel (PUB/SUB): Port 5556 - Asynchronous streaming data
- Target Gateway IP: 172.19.141.255

Protocol Version: 1.0
"""

from enum import Enum
from typing import Dict, Any
import time
import uuid

# ============================================================================
# Infrastructure Constants
# ============================================================================

ZMQ_PORT_CMD = 5555      # Command Channel (REQ/REP)
ZMQ_PORT_DATA = 5556     # Data Channel (PUB/SUB)
GATEWAY_IP_INTERNAL = "172.19.141.255"  # Windows Gateway IP


# ============================================================================
# Action Definitions
# ============================================================================

class Action(str, Enum):
    """
    Available actions that can be sent from Brain to Gateway.

    Usage:
        request = create_request(Action.HEARTBEAT)
    """
    HEARTBEAT = "HEARTBEAT"                 # Health check
    OPEN_ORDER = "OPEN_ORDER"               # Execute new order
    CLOSE_POSITION = "CLOSE_POSITION"       # Close existing position
    GET_ACCOUNT_INFO = "GET_ACCOUNT_INFO"   # Query account details
    GET_POSITIONS = "GET_POSITIONS"         # Query open positions
    KILL_SWITCH = "KILL_SWITCH"             # Emergency stop all trading


# ============================================================================
# Response Status
# ============================================================================

class ResponseStatus(str, Enum):
    """
    Standard response status codes.

    Usage:
        if response['status'] == ResponseStatus.SUCCESS:
            process_data(response['data'])
    """
    SUCCESS = "SUCCESS"    # Operation completed successfully
    ERROR = "ERROR"        # Operation failed with error
    PENDING = "PENDING"    # Operation queued/in-progress


# ============================================================================
# Message Constructors
# ============================================================================

def create_request(action: Action, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Construct a standard request packet.

    Args:
        action: The action to perform (from Action enum)
        payload: Optional data payload (dict)

    Returns:
        Standardized request dictionary

    Example:
        >>> req = create_request(Action.OPEN_ORDER, {
        ...     'symbol': 'EURUSD.s',
        ...     'volume': 0.01,
        ...     'side': 'BUY'
        ... })
        >>> req['action']
        'OPEN_ORDER'
        >>> 'req_id' in req
        True
    """
    return {
        "action": action.value,
        "req_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "payload": payload or {}
    }


def create_response(
    req_id: str,
    status: ResponseStatus,
    data: Any = None,
    error: str = None
) -> Dict[str, Any]:
    """
    Construct a standard response packet.

    Args:
        req_id: Request ID from the original request
        status: Response status (from ResponseStatus enum)
        data: Optional response data
        error: Optional error message (if status is ERROR)

    Returns:
        Standardized response dictionary

    Example:
        >>> resp = create_response(
        ...     req_id="abc-123",
        ...     status=ResponseStatus.SUCCESS,
        ...     data={"ticket": 12345}
        ... )
        >>> resp['status']
        'SUCCESS'
        >>> resp['data']['ticket']
        12345
    """
    return {
        "req_id": req_id,
        "status": status.value,
        "timestamp": time.time(),
        "data": data,
        "error": error
    }


# ============================================================================
# Protocol Validation
# ============================================================================

def validate_request(request: Dict[str, Any]) -> bool:
    """
    Validate request structure.

    Args:
        request: Request dictionary to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> req = create_request(Action.HEARTBEAT)
        >>> validate_request(req)
        True
        >>> validate_request({})
        False
    """
    required_fields = ["action", "req_id", "timestamp", "payload"]
    return all(field in request for field in required_fields)


def validate_response(response: Dict[str, Any]) -> bool:
    """
    Validate response structure.

    Args:
        response: Response dictionary to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> resp = create_response("abc", ResponseStatus.SUCCESS)
        >>> validate_response(resp)
        True
        >>> validate_response({"req_id": "abc"})
        False
    """
    required_fields = ["req_id", "status", "timestamp"]
    return all(field in response for field in required_fields)
