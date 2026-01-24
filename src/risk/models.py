"""
Risk Management Data Models
RFC-135: Dynamic Risk Management System

定义风险管理系统的核心数据结构
Protocol v4.4 compliant
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Any

from .enums import RiskLevel, RiskAction, TrackType, OrderSide, CircuitState


@dataclass
class RiskContext:
    """
    风险检查上下文

    包含进行风险检查所需的所有信息
    每次订单验证时构建此对象
    """
    # 订单信息
    symbol: str                          # 交易品种
    track: TrackType                     # 所属轨道
    order_side: OrderSide                # 订单方向
    order_size: Decimal                  # 订单数量
    order_price: Decimal                 # 订单价格

    # 账户状态
    account_equity: Decimal              # 账户权益
    available_margin: Decimal            # 可用保证金

    # 持仓信息
    positions: Dict[str, 'PositionInfo'] = field(default_factory=dict)

    # 当日统计
    daily_pnl: Decimal = Decimal("0")    # 当日盈亏
    daily_trades: int = 0                # 当日交易次数

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def order_value(self) -> Decimal:
        """计算订单价值"""
        return self.order_size * self.order_price

    @property
    def is_opening(self) -> bool:
        """判断是否为开仓订单"""
        position = self.positions.get(self.symbol)
        if position is None:
            return True
        # 如果订单方向与持仓方向相同，则为加仓（开仓）
        if position.quantity > 0 and self.order_side == OrderSide.BUY:
            return True
        if position.quantity < 0 and self.order_side == OrderSide.SELL:
            return True
        return False


@dataclass
class PositionInfo:
    """
    持仓信息
    """
    symbol: str                          # 品种
    quantity: Decimal                    # 数量（正为多头，负为空头）
    avg_price: Decimal                   # 平均成本
    current_price: Decimal               # 当前价格
    unrealized_pnl: Decimal              # 未实现盈亏
    track: TrackType                     # 所属轨道

    @property
    def market_value(self) -> Decimal:
        """计算市值"""
        return abs(self.quantity) * self.current_price

    @property
    def is_long(self) -> bool:
        """是否为多头"""
        return self.quantity > 0


@dataclass
class RiskDecision:
    """
    风险决策结果

    风险检查的输出，包含决策动作和详细信息
    """
    action: RiskAction                   # 决策动作
    level: RiskLevel                     # 风险级别
    reason: str                          # 决策原因
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    # 可选的调整建议
    suggested_size: Optional[Decimal] = None  # 建议的订单大小

    @property
    def is_allowed(self) -> bool:
        """订单是否被允许"""
        return self.action == RiskAction.ALLOW

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "action": self.action.name,
            "level": self.level.name,
            "reason": self.reason,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "suggested_size": str(self.suggested_size) if self.suggested_size else None
        }


@dataclass
class RiskEvent:
    """
    风险事件

    用于记录和通知风险相关事件
    """
    event_type: str                      # 事件类型
    severity: RiskLevel                  # 严重程度
    message: str                         # 事件消息
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    # 预定义事件类型常量
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    CIRCUIT_BREAKER_RESET = "circuit_breaker_reset"
    DRAWDOWN_WARNING = "drawdown_warning"
    DRAWDOWN_LIMIT_HIT = "drawdown_limit_hit"
    EXPOSURE_WARNING = "exposure_warning"
    EXPOSURE_LIMIT_HIT = "exposure_limit_hit"
    DAILY_RESET = "daily_reset"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_type": self.event_type,
            "severity": self.severity.name,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SymbolRiskState:
    """
    单品种风险状态

    跟踪单个品种的风险指标
    """
    symbol: str
    circuit_state: CircuitState = CircuitState.CLOSED
    consecutive_losses: int = 0          # 连续亏损次数
    loss_amount: Decimal = Decimal("0")  # 累计亏损金额
    last_trade_time: Optional[datetime] = None
    trip_count: int = 0                  # 熔断触发次数

    # 熔断恢复相关
    open_time: Optional[datetime] = None  # 熔断开始时间
    half_open_trades: int = 0             # 半开状态下的交易次数


@dataclass
class AccountRiskState:
    """
    账户风险状态

    跟踪账户级别的风险指标
    """
    # 每日统计
    daily_starting_equity: Decimal = Decimal("0")
    daily_high_equity: Decimal = Decimal("0")
    daily_realized_pnl: Decimal = Decimal("0")
    daily_unrealized_pnl: Decimal = Decimal("0")

    # 回撤计算
    current_drawdown: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")

    # 交易统计
    daily_trade_count: int = 0
    daily_win_count: int = 0
    daily_loss_count: int = 0

    # 状态
    risk_level: RiskLevel = RiskLevel.NORMAL
    last_update: datetime = field(default_factory=datetime.now)

    @property
    def daily_total_pnl(self) -> Decimal:
        """当日总盈亏"""
        return self.daily_realized_pnl + self.daily_unrealized_pnl

    @property
    def drawdown_percentage(self) -> Decimal:
        """回撤百分比"""
        if self.daily_high_equity == 0:
            return Decimal("0")
        return (self.daily_high_equity - (self.daily_starting_equity + self.daily_total_pnl)) / self.daily_high_equity * 100


@dataclass
class TrackRiskState:
    """
    轨道风险状态

    跟踪单个轨道的风险指标
    """
    track: TrackType
    total_exposure: Decimal = Decimal("0")      # 总敞口
    position_count: int = 0                      # 持仓数量
    unrealized_pnl: Decimal = Decimal("0")      # 未实现盈亏
    risk_level: RiskLevel = RiskLevel.NORMAL

    # 轨道特定限制
    max_exposure: Decimal = Decimal("0")        # 最大敞口限制
    max_positions: int = 0                       # 最大持仓数限制
