"""
Risk Management Module
RFC-135: Dynamic Risk Management System

Protocol v4.4 compliant risk management for 3-Track trading system
"""

from .enums import RiskLevel, CircuitState, RiskAction, TrackType, OrderSide
from .models import (
    RiskContext,
    PositionInfo,
    RiskDecision,
    RiskEvent,
    SymbolRiskState,
    AccountRiskState,
    TrackRiskState
)
from .config import (
    CircuitBreakerConfig,
    DrawdownConfig,
    ExposureConfig,
    TrackLimits,
    RiskConfig
)
from .circuit_breaker import CircuitBreaker
from .drawdown_monitor import DrawdownMonitor
from .exposure_monitor import ExposureMonitor
from .risk_manager import RiskManager
from .events import (
    RiskEventBus,
    RiskAlertHandler,
    RiskEventLogger,
    initialize_global_event_system,
    get_event_bus,
    get_alert_handler,
    get_event_logger
)

__all__ = [
    # Enums
    'RiskLevel',
    'CircuitState',
    'RiskAction',
    'TrackType',
    'OrderSide',
    # Models
    'RiskContext',
    'PositionInfo',
    'RiskDecision',
    'RiskEvent',
    'SymbolRiskState',
    'AccountRiskState',
    'TrackRiskState',
    # Config
    'CircuitBreakerConfig',
    'DrawdownConfig',
    'ExposureConfig',
    'TrackLimits',
    'RiskConfig',
    # Components
    'CircuitBreaker',
    'DrawdownMonitor',
    'ExposureMonitor',
    'RiskManager',
    # Events
    'RiskEventBus',
    'RiskAlertHandler',
    'RiskEventLogger',
    'initialize_global_event_system',
    'get_event_bus',
    'get_alert_handler',
    'get_event_logger',
]

__version__ = "1.0.0"
