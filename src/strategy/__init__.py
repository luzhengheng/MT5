"""
Strategy Package - Trading Strategy Implementations
===================================================

Contains strategy adapters, signal engines, technical indicators,
and risk management components.

Task #020.01: Unified Strategy Adapter (Backtest & Live)
"""

# 技术指标模块（Task #018）
from .indicators import TechnicalIndicators, get_technical_indicators

# 信号生成引擎（Task #019）
from .signal_engine import SignalEngine, get_signal_engine

# 统一策略适配器（Task #020.01）
from .live_adapter import LiveStrategyAdapter, get_live_strategy

# 以下模块将在后续任务中实现
# from .ml_strategy import MLStrategy
# from .risk_manager import KellySizer, DynamicRiskManager
# from .hierarchical_signals import (
#     HierarchicalSignalFusion,
#     TimeframeSignal,
#     FusionResult,
#     SignalDirection,
#     SignalPriority,
# )

__all__ = [
    'TechnicalIndicators',
    'get_technical_indicators',
    'SignalEngine',
    'get_signal_engine',
    'LiveStrategyAdapter',
    'get_live_strategy',
    # 'MLStrategy',
    # 'KellySizer',
    # 'DynamicRiskManager',
    # 'HierarchicalSignalFusion',
    # 'TimeframeSignal',
    # 'FusionResult',
    # 'SignalDirection',
    # 'SignalPriority',
]
