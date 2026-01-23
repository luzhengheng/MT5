"""
枚举类型定义模块

定义交易系统中使用的所有枚举类型，包括资产类型、订单状态、订单类型等。
遵循Protocol v4.4的类型安全原则。
"""

from enum import Enum, auto
from typing import Set


class AssetType(str, Enum):
    """
    资产类型枚举

    定义系统支持的三种交易资产类型。
    继承str使其可以直接用于字符串比较和序列化。
    """
    EUR = "EUR"  # 欧元
    BTC = "BTC"  # 比特币
    GBP = "GBP"  # 英镑

    @classmethod
    def get_all_types(cls) -> Set["AssetType"]:
        """获取所有支持的资产类型"""
        return {cls.EUR, cls.BTC, cls.GBP}

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """验证字符串是否为有效的资产类型"""
        return value in [item.value for item in cls]


class OrderStatus(str, Enum):
    """
    订单状态枚举

    定义订单在生命周期中的所有可能状态。
    状态转换遵循有限状态机模型。
    """
    PENDING = "PENDING"          # 待处理
    QUEUED = "QUEUED"            # 已入队
    PROCESSING = "PROCESSING"    # 处理中
    EXECUTED = "EXECUTED"        # 已执行
    FAILED = "FAILED"            # 失败
    CANCELLED = "CANCELLED"      # 已取消
    REJECTED = "REJECTED"        # 被拒绝（并发限制）

    def can_transition_to(self, target: "OrderStatus") -> bool:
        """
        检查是否可以转换到目标状态

        Args:
            target: 目标状态

        Returns:
            bool: 是否允许状态转换
        """
        valid_transitions = {
            OrderStatus.PENDING: {OrderStatus.QUEUED, OrderStatus.REJECTED},
            OrderStatus.QUEUED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
            OrderStatus.PROCESSING: {OrderStatus.EXECUTED, OrderStatus.FAILED},
            OrderStatus.EXECUTED: set(),  # 终态
            OrderStatus.FAILED: set(),    # 终态
            OrderStatus.CANCELLED: set(), # 终态
            OrderStatus.REJECTED: set(),  # 终态
        }
        return target in valid_transitions.get(self, set())


class OrderType(str, Enum):
    """订单类型枚举"""
    MARKET = "MARKET"    # 市价单
    LIMIT = "LIMIT"      # 限价单
    STOP = "STOP"        # 止损单


class OrderSide(str, Enum):
    """订单方向枚举"""
    BUY = "BUY"
    SELL = "SELL"


class TrackStatus(str, Enum):
    """轨道状态枚举"""
    ACTIVE = "ACTIVE"        # 活跃
    PAUSED = "PAUSED"        # 暂停
    DRAINING = "DRAINING"    # 排空中
    STOPPED = "STOPPED"      # 已停止
