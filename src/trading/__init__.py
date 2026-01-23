"""
MT5-CRS 交易系统

三轨并发交易系统，支持 EUR、BTC、GBP 资产类型。
Protocol v4.4 完全兼容。
"""

from .models import (
    AssetType,
    OrderStatus,
    OrderType,
    OrderSide,
    TrackStatus,
    Order,
    OrderResult,
    TrackConfig,
    DispatcherConfig,
)

from .core import (
    RateLimiter,
    ConcurrencyLimiter,
    TradeTrack,
    TrackDispatcher,
)

from .utils import (
    AtomicCounter,
    AtomicFlag,
    MetricsCollector,
)

__all__ = [
    # Models
    'AssetType',
    'OrderStatus',
    'OrderType',
    'OrderSide',
    'TrackStatus',
    'Order',
    'OrderResult',
    'TrackConfig',
    'DispatcherConfig',
    # Core
    'RateLimiter',
    'ConcurrencyLimiter',
    'TradeTrack',
    'TrackDispatcher',
    # Utils
    'AtomicCounter',
    'AtomicFlag',
    'MetricsCollector',
]

__version__ = "0.1.0"
