"""
订单模型模块

定义订单及其相关结果的数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import uuid4

from .enums import AssetType, OrderStatus, OrderType, OrderSide


@dataclass
class Order:
    """
    交易订单数据模型

    Attributes:
        order_id: 订单唯一标识符
        asset_type: 资产类型
        order_type: 订单类型
        side: 买卖方向
        quantity: 数量
        price: 价格（限价单必填）
        status: 订单状态
        created_at: 创建时间
        updated_at: 更新时间
        metadata: 额外元数据
    """
    asset_type: AssetType
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: Optional[float] = None
    order_id: str = field(default_factory=lambda: str(uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """订单验证"""
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("price is required for LIMIT orders")
        if self.price is not None and self.price <= 0:
            raise ValueError(f"price must be positive, got {self.price}")

    def update_status(self, new_status: OrderStatus) -> None:
        """
        更新订单状态

        Args:
            new_status: 新状态

        Raises:
            ValueError: 如果状态转换不合法
        """
        if not self.status.can_transition_to(new_status):
            raise ValueError(
                f"Invalid status transition: {self.status} -> {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "order_id": self.order_id,
            "asset_type": self.asset_type.value,
            "order_type": self.order_type.value,
            "side": self.side.value,
            "quantity": self.quantity,
            "price": self.price,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class OrderResult:
    """
    订单处理结果

    Attributes:
        order_id: 订单ID
        success: 是否成功
        status: 最终状态
        message: 结果消息
        execution_time_ms: 执行时间（毫秒）
        track_id: 处理轨道ID
        error_code: 错误代码（失败时）
    """
    order_id: str
    success: bool
    status: OrderStatus
    message: str = ""
    execution_time_ms: float = 0.0
    track_id: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "order_id": self.order_id,
            "success": self.success,
            "status": self.status.value,
            "message": self.message,
            "execution_time_ms": self.execution_time_ms,
            "track_id": self.track_id,
            "error_code": self.error_code
        }
