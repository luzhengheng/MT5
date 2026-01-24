"""
Risk Management Enumerations
RFC-135: Dynamic Risk Management System

定义风险管理系统中使用的所有枚举类型
Protocol v4.4 compliant
"""

from enum import Enum, auto


class RiskLevel(Enum):
    """
    风险级别枚举

    用于表示当前系统或组件的风险状态
    级别从低到高: NORMAL < WARNING < CRITICAL < HALT
    """
    NORMAL = auto()      # 正常状态，所有操作允许
    WARNING = auto()     # 警告状态，记录日志但允许操作
    CRITICAL = auto()    # 临界状态，限制新开仓
    HALT = auto()        # 停止状态，禁止所有交易


class CircuitState(Enum):
    """
    熔断器状态枚举

    实现标准熔断器模式的三态机制:
    - CLOSED: 正常状态��允许交易
    - OPEN: 熔断状态，拒绝交易
    - HALF_OPEN: 半开状态，允许探测性交易
    """
    CLOSED = auto()      # 闭合状态 - 正常运行
    HALF_OPEN = auto()   # 半开状态 - 尝试恢复
    OPEN = auto()        # 断开状态 - 熔断中


class RiskAction(Enum):
    """
    风险决策动作枚举

    表示风险检查后系统应采取的动作
    """
    ALLOW = auto()       # 允许订单通过
    REJECT = auto()      # 拒绝订单
    REDUCE_ONLY = auto() # 仅允许减仓操作
    FORCE_CLOSE = auto() # 强制平仓


class TrackType(Enum):
    """
    交易轨道类型枚举

    对应3-Track系统的三个轨道
    """
    EUR = "EUR"              # 欧元轨道 (保守)
    BTC = "BTC"              # 比特币轨道 (中等)
    GBP = "GBP"              # 英镑轨道 (激进)


class OrderSide(Enum):
    """
    订单方向枚举
    """
    BUY = "buy"
    SELL = "sell"
