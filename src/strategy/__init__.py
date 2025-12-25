"""
策略模块 - 包含 Backtrader 策略和风险管理
"""

# 技术指标模块（Task #018）
from .indicators import TechnicalIndicators, get_technical_indicators

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
    # 'MLStrategy',
    # 'KellySizer',
    # 'DynamicRiskManager',
    # 'HierarchicalSignalFusion',
    # 'TimeframeSignal',
    # 'FusionResult',
    # 'SignalDirection',
    # 'SignalPriority',
]
