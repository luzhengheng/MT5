"""
MT5-CRS 连接模块
提供MT5实盘交易系统的连接、数据桥接和异常熔断功能
"""

from .mt5_bridge import (
    MT5Bridge,
    MT5ConnectionError,
    MT5OrderError,
    OrderType,
    OrderStatus,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    ExceptionHandler,
    BreakdownEvent,
)

__all__ = [
    # MT5 Bridge
    'MT5Bridge',
    'MT5ConnectionError',
    'MT5OrderError',
    'OrderType',
    'OrderStatus',
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerState',
    'ExceptionHandler',
    'BreakdownEvent',
]
