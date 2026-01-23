# RFC-131: 双轨交易激活技术规格书

**Protocol Version**: v4.4  
**Status**: Draft  
**Author**: System Architect  
**Date**: 2025-01-XX  
**Depends-On**: RFC-130 (已完成)

---

## 1. 背景 (Context)

### 1.1 任务概述

基于Task #130完成的单轨交易基础设施，本任务将系统扩展为支持双轨并行交易模式，同时处理外汇品种(EURUSD.s)和加密货币品种(BTCUSD.s)。

### 1.2 前置条件

| 依赖项 | 状态 | 说明 |
|--------|------|------|
| Task #130 | ✅ 已完成 | 单轨交易引擎基础设施 |
| MT5连接模块 | ✅ 可用 | 经纪商API连接层 |
| 风控模块 v1.0 | ✅ 可用 | 基础风险控制 |

### 1.3 业务目标

- 实现EURUSD.s与BTCUSD.s的并行交易
- 独立的风控参数配置
- 统一的信号调度与执行
- 跨品种风险敞口管理

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dual-Rail Trading System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌──────────────────────────────────────┐    │
│  │   Signal    │    │         Rail Dispatcher               │    │
│  │  Generator  │───▶│  ┌────────────┐  ┌────────────┐      │    │
│  └─────────────┘    │  │  Rail #1   │  │  Rail #2   │      │    │
│                     │  │  EURUSD.s  │  │  BTCUSD.s  │      │    │
│                     │  └─────┬──────┘  └─────┬──────┘      │    │
│                     └────────┼───────────────┼─────────────┘    │
│                              │               │                   │
│                              ▼               ▼                   │
│                     ┌────────────────────────────────────┐      │
│                     │       Execution Engine              │      │
│                     │  ┌──────────┐    ┌──────────┐      │      │
│                     │  │ Executor │    │ Executor │      │      │
│                     │  │   FX     │    │  Crypto  │      │      │
│                     │  └────┬─────┘    └────┬─────┘      │      │
│                     └───────┼───────────────┼────────────┘      │
│                             │               │                    │
│                             ▼               ▼                    │
│                     ┌────────────────────────────────────┐      │
│                     │      Risk Management Layer          │      │
│                     │  • Position Limits                  │      │
│                     │  • Correlation Monitor              │      │
│                     │  • Drawdown Control                 │      │
│                     └────────────────────────────────────┘      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
Signal Input
     │
     ▼
┌─────────────┐
│  Validator  │──── Invalid ────▶ Reject & Log
└──────┬──────┘
       │ Valid
       ▼
┌─────────────┐
│  Classifier │
└──────┬──────┘
       │
       ├──── symbol="EURUSD.s" ────▶ Rail #1 Queue
       │
       └──── symbol="BTCUSD.s" ────▶ Rail #2 Queue
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │ Risk Check  │
                                   └──────┬──────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                         Pass │                       │ Fail
                              ▼                       ▼
                       ┌─────────────┐         ┌─────────────┐
                       │   Execute   │         │   Queue/    │
                       │    Order    │         │   Reject    │
                       └─────────────┘         └─────────────┘
```

### 2.3 类图

```
┌───────────────────────────────────────┐
│           <<interface>>                │
│            IRail                       │
├───────────────────────────────────────┤
│ + symbol: str                          │
│ + is_active: bool                      │
├───────────────────────────────────────┤
│ + process_signal(signal) -> Result     │
│ + get_position() -> Position           │
│ + close_all() -> bool                  │
└───────────────────────────────────────┘
                    △
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────────────┐       ┌───────────────┐
│   ForexRail   │       │  CryptoRail   │
├───────────────┤       ├───────────────┤
│ - spread_limit│       │ - volatility  │
│ - session_hrs │       │ - funding_rate│
├───────────────┤       ├───────────────┤
│ + validate()  │       │ + validate()  │
└───────────────┘       └───────────────┘

┌───────────────────────────────────────┐
│          RailDispatcher                │
├───────────────────────────────────────┤
│ - rails: Dict[str, IRail]              │
│ - executor: ExecutionEngine            │
├───────────────────────────────────────┤
│ + register_rail(rail: IRail)           │
│ + dispatch(signal: Signal) -> Result   │
│ + get_all_positions() -> List[Position]│
│ + shutdown() -> None                   │
└───────────────────────────────────────┘
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 目录结构

```
/opt/trading-system/
├── config/
│   └── dual_rail_config.yaml
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── signal.py
│   │   ├── position.py
│   │   └── result.py
│   ├── rails/
│   │   ├── __init__.py
│   │   ├── base_rail.py
│   │   ├── forex_rail.py
│   │   └── crypto_rail.py
│   ├── dispatcher/
│   │   ├── __init__.py
│   │   └── rail_dispatcher.py
│   ├── execution/
│   │   ├── __init__.py
│   │   └── execution_engine.py
│   ├── risk/
│   │   ├── __init__.py
│   │   └── risk_manager.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_rails.py
│   └── test_dispatcher.py
└── requirements.txt
```

### 3.2 配置文件

**文件路径**: `/opt/trading-system/config/dual_rail_config.yaml`

```yaml
# Dual-Rail Trading Configuration
# Protocol v4.4 Compliant

system:
  version: "1.0.0"
  mode: "production"  # production | paper | backtest
  log_level: "INFO"

rails:
  forex:
    symbol: "EURUSD.s"
    enabled: true
    parameters:
      lot_size: 0.01
      max_positions: 3
      max_daily_trades: 10
      spread_limit_points: 20
      slippage_tolerance: 5
    session:
      # UTC时间
      start_hour: 7
      end_hour: 21
    risk:
      max_drawdown_percent: 2.0
      stop_loss_pips: 50
      take_profit_pips: 100
      
  crypto:
    symbol: "BTCUSD.s"
    enabled: true
    parameters:
      lot_size: 0.001
      max_positions: 2
      max_daily_trades: 8
      volatility_threshold: 5.0
      slippage_tolerance: 10
    session:
      # 24/7 交易
      start_hour: 0
      end_hour: 24
    risk:
      max_drawdown_percent: 3.0
      stop_loss_percent: 2.0
      take_profit_percent: 4.0

global_risk:
  max_total_exposure_percent: 5.0
  max_correlation_threshold: 0.7
  emergency_stop_drawdown: 10.0

mt5:
  server: "broker-server.com"
  login: ${MT5_LOGIN}
  password: ${MT5_PASSWORD}
  timeout: 30000
```

### 3.3 数据模型

**文件路径**: `/opt/trading-system/src/models/signal.py`

```python
"""
Signal Model - 交易信号数据结构
Protocol v4.4 Compliant
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"
    CLOSE_ALL = "CLOSE_ALL"


class SignalSource(Enum):
    """信号来源枚举"""
    STRATEGY = "STRATEGY"
    MANUAL = "MANUAL"
    RISK_MANAGER = "RISK_MANAGER"
    SYSTEM = "SYSTEM"


@dataclass
class Signal:
    """
    交易信号数据类
    
    Attributes:
        signal_id: 唯一信号标识符
        symbol: 交易品种 (EURUSD.s 或 BTCUSD.s)
        signal_type: 信号类型
        source: 信号来源
        price: 期望执行价格 (可选，None表示市价)
        lot_size: 交易手数 (可选，None使用默认配置)
        stop_loss: 止损价格 (可选)
        take_profit: 止盈价格 (可选)
        comment: 订单注释
        timestamp: 信号生成时间
        expiry_seconds: 信号有效期(秒)
        metadata: 额外元数据
    """
    symbol: str
    signal_type: SignalType
    source: SignalSource = SignalSource.STRATEGY
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    price: Optional[float] = None
    lot_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expiry_seconds: int = 30
    metadata: dict = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查信号是否已过期"""
        elapsed = (datetime.utcnow() - self.timestamp).total_seconds()
        return elapsed > self.expiry_seconds
    
    def validate(self) -> tuple[bool, str]:
        """
        验证信号有效性
        
        Returns:
            (is_valid, error_message)
        """
        # 检查品种
        valid_symbols = ["EURUSD.s", "BTCUSD.s"]
        if self.symbol not in valid_symbols:
            return False, f"Invalid symbol: {self.symbol}. Must be one of {valid_symbols}"
        
        # 检查手数
        if self.lot_size is not None and self.lot_size <= 0:
            return False, f"Invalid lot_size: {self.lot_size}. Must be positive"
        
        # 检查止损止盈逻辑
        if self.signal_type == SignalType.BUY:
            if self.stop_loss and self.take_profit:
                if self.stop_loss >= self.take_profit:
                    return False, "For BUY: stop_loss must be less than take_profit"
        elif self.signal_type == SignalType.SELL:
            if self.stop_loss and self.take_profit:
                if self.stop_loss <= self.take_profit:
                    return False, "For SELL: stop_loss must be greater than take_profit"
        
        # 检查过期
        if self.is_expired():
            return False, f"Signal expired. Age: {(datetime.utcnow() - self.timestamp).total_seconds()}s"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "source": self.source.value,
            "price": self.price,
            "lot_size": self.lot_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "comment": self.comment,
            "timestamp": self.timestamp.isoformat(),
            "expiry_seconds": self.expiry_seconds,
            "metadata": self.metadata
        }
```

**文件路径**: `/opt/trading-system/src/models/position.py`

```python
"""
Position Model - 持仓数据结构
Protocol v4.4 Compliant
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PositionSide(Enum):
    """持仓方向"""
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(Enum):
    """持仓状态"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"


@dataclass
class Position:
    """
    持仓数据类
    
    Attributes:
        ticket: MT5订单票号
        symbol: 交易品种
        side: 持仓方向
        lot_size: 持仓手数
        open_price: 开仓价格
        current_price: 当前价格
        stop_loss: 止损价格
        take_profit: 止盈价格
        profit: 当前盈亏
        swap: 隔夜利息
        commission: 手续费
        open_time: 开仓时间
        status: 持仓状态
        comment: 订单注释
        magic_number: EA魔术号
    """
    ticket: int
    symbol: str
    side: PositionSide
    lot_size: float
    open_price: float
    current_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    profit: float = 0.0
    swap: float = 0.0
    commission: float = 0.0
    open_time: datetime = field(default_factory=datetime.utcnow)
    status: PositionStatus = PositionStatus.OPEN
    comment: str = ""
    magic_number: int = 0
    
    @property
    def net_profit(self) -> float:
        """净盈亏 (含swap和commission)"""
        return self.profit + self.swap - abs(self.commission)
    
    @property
    def profit_pips(self) -> float:
        """盈亏点数 (适用于外汇)"""
        if "USD" in self.symbol and "JPY" not in self.symbol:
            pip_value = 0.0001
        else:
            pip_value = 0.01
        
        if self.side == PositionSide.LONG:
            return (self.current_price - self.open_price) / pip_value
        else:
            return (self.open_price - self.current_price) / pip_value
    
    @property
    def profit_percent(self) -> float:
        """盈亏百分比"""
        if self.side == PositionSide.LONG:
            return ((self.current_price - self.open_price) / self.open_price) * 100
        else:
            return ((self.open_price - self.current_price) / self.open_price) * 100
    
    @property
    def holding_duration_hours(self) -> float:
        """持仓时长(小时)"""
        return (datetime.utcnow() - self.open_time).total_seconds() / 3600
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "side": self.side.value,
            "lot_size": self.lot_size,
            "open_price": self.open_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "profit": self.profit,
            "net_profit": self.net_profit,
            "profit_pips": self.profit_pips,
            "profit_percent": self.profit_percent,
            "swap": self.swap,
            "commission": self.commission,
            "open_time": self.open_time.isoformat(),
            "holding_hours": self.holding_duration_hours,
            "status": self.status.value,
            "comment": self.comment,
            "magic_number": self.magic_number
        }
```

**文件路径**: `/opt/trading-system/src/models/result.py`

```python
"""
Result Model - 操作结果数据结构
Protocol v4.4 Compliant
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class ResultCode(Enum):
    """结果代码枚举"""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"
    INVALID_SIGNAL = "INVALID_SIGNAL"
    RISK_REJECTED = "RISK_REJECTED"
    MARKET_CLOSED = "MARKET_CLOSED"
    INSUFFICIENT_MARGIN = "INSUFFICIENT_MARGIN"
    CONNECTION_ERROR = "CONNECTION_ERROR"


@dataclass
class ExecutionResult:
    """
    执行结果数据类
    
    Attributes:
        signal_id: 关联的信号ID
        code: 结果代码
        message: 结果消息
        ticket: MT5订单票号 (成功时)
        executed_price: 实际执行价格
        executed_lot: 实际执行手数
        slippage: 滑点
        execution_time_ms: 执行耗时(毫秒)
        timestamp: 结果时间戳
        details: 额外详情
    """
    signal_id: str
    code: ResultCode
    message: str = ""
    ticket: Optional[int] = None
    executed_price: Optional[float] = None
    executed_lot: Optional[float] = None
    slippage: float = 0.0
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.code in [ResultCode.SUCCESS, ResultCode.PARTIAL_SUCCESS]
    
    @property
    def is_failure(self) -> bool:
        """是否失败"""
        return not self.is_success
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "signal_id": self.signal_id,
            "code": self.code.value,
            "is_success": self.is_success,
            "message": self.message,
            "ticket": self.ticket,
            "executed_price": self.executed_price,
            "executed_lot": self.executed_lot,
            "slippage": self.slippage,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
    
    @classmethod
    def success(cls, signal_id: str, ticket: int, price: float, 
                lot: float, slippage: float = 0.0, 
                execution_time_ms: int = 0) -> "ExecutionResult":
        """创建成功结果的工厂方法"""
        return cls(
            signal_id=signal_id,
            code=ResultCode.SUCCESS,
            message="Order executed successfully",
            ticket=ticket,
            executed_price=price,
            executed_lot=lot,
            slippage=slippage,
            execution_time_ms=execution_time_ms
        )
    
    @classmethod
    def failure(cls, signal_id: str, code: ResultCode, 
                message: str, details: dict = None) -> "ExecutionResult":
        """创建失败结果的工厂方法"""
        return cls(
            signal_id=signal_id,
            code=code,
            message=message,
            details=details or {}
        )
```

**文件路径**: `/opt/trading-system/src/models/__init__.py`

```python
"""
Models Package
Protocol v4.4 Compliant
"""

from .signal import Signal, SignalType, SignalSource
from .position import Position, PositionSide, PositionStatus
from .result import ExecutionResult, ResultCode

__all__ = [
    "Signal",
    "SignalType", 
    "SignalSource",
    "Position",
    "PositionSide",
    "PositionStatus",
    "ExecutionResult",
    "ResultCode"
]
```

### 3.4 Rail实现

**文件路径**: `/opt/trading-system/src/rails/base_rail.py`

```python
"""
Base Rail - 交易轨道抽象基类
Protocol v4.4 Compliant
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
import logging

from src.models import Signal, Position, ExecutionResult, ResultCode


class BaseRail(ABC):
    """
    交易轨道抽象基类
    
    每个Rail负责处理特定品种的交易信号，
    包含独立的验证逻辑、风控参数和执行策略。
    """
    
    def __init__(self, symbol: str, config: dict):
        """
        初始化Rail
        
        Args:
            symbol: 交易品种
            config: 轨道配置
        """
        self.symbol = symbol
        self.config = config
        self.is_active = config.get("enabled", True)
        self.logger = logging.getLogger(f"Rail.{symbol}")
        
        # 从配置加载参数
        params = config.get("parameters", {})
        self.lot_size = params.get("lot_size", 0.01)
        self.max_positions = params.get("max_positions", 3)
        self.max_daily_trades = params.get("max_daily_trades", 10)
        self.slippage_tolerance = params.get("slippage_tolerance", 5)
        
        # 交易时段
        session = config.get("session", {})
        self.session_start = session.get("start_hour", 0)
        self.session_end = session.get("end_hour", 24)
        
        # 风控参数
        risk = config.get("risk", {})
        self.max_drawdown_percent = risk.get("max_drawdown_percent", 2.0)
        
        # 运行时状态
        self._positions: List[Position] = []
        self._daily_trade_count = 0
        self._last_trade_date: Optional[datetime] = None
        
        self.logger.info(f"Rail initialized: {symbol}, active={self.is_active}")
    
    def _reset_daily_counter(self):
        """重置每日交易计数器"""
        today = datetime.utcnow().date()
        if self._last_trade_date != today:
            self._daily_trade_count = 0
            self._last_trade_date = today
    
    def is_in_session(self) -> bool:
        """检查当前是否在交易时段内"""
        current_hour = datetime.utcnow().hour
        if self.session_start < self.session_end:
            return self.session_start <= current_hour < self.session_end
        else:
            # 跨午夜的时段
            return current_hour >= self.session_start or current_hour < self.session_end
    
    def can_open_position(self) -> tuple[bool, str]:
        """
        检查是否可以开新仓位
        
        Returns:
            (can_open, reason)
        """
        if not self.is_active:
            return False, "Rail is not active"
        
        if not self.is_in_session():
            return False, f"Outside trading session ({self.session_start}:00 - {self.session_end}:00 UTC)"
        
        self._reset_daily_counter()
        
        if len(self._positions) >= self.max_positions:
            return False, f"Max positions reached: {len(self._positions)}/{self.max_positions}"
        
        if self._daily_trade_count >= self.max_daily_trades:
            return False, f"Max daily trades reached: {self._daily_trade_count}/{self.max_daily_trades}"
        
        return True, ""
    
    @abstractmethod
    def validate_signal(self, signal: Signal) -> tuple[bool, str]:
        """
        验证信号是否符合该Rail的规则
        
        Args:
            signal: 交易信号
            
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def calculate_lot_size(self, signal: Signal) -> float:
        """
        计算实际交易手数
        
        Args:
            signal: 交易信号
            
        Returns:
            计算后的手数
        """
        pass
    
    @abstractmethod
    def calculate_sl_tp(self, signal: Signal, current_price: float) -> tuple[Optional[float], Optional[float]]:
        """
        计算止损止盈价格
        
        Args:
            signal: 交易信号
            current_price: 当前价格
            
        Returns:
            (stop_loss, take_profit)
        """
        pass
    
    def process_signal(self, signal: Signal) -> ExecutionResult:
        """
        处理交易信号
        
        Args:
            signal: 交易信号
            
        Returns:
            执行结果
        """
        self.logger.info(f"Processing signal: {signal.signal_id} - {signal.signal_type.value}")
        
        # 基础验证
        is_valid, error = signal.validate()
        if not is_valid:
            return ExecutionResult.failure(
                signal.signal_id, 
                ResultCode.INVALID_SIGNAL, 
                error
            )
        
        # 品种验证
        if signal.symbol != self.symbol:
            return ExecutionResult.failure(
                signal.signal_id,
                ResultCode.INVALID_SIGNAL,
                f"Symbol mismatch: expected {self.symbol}, got {signal.symbol}"
            )
        
        # Rail特定验证
        is_valid, error = self.validate_signal(signal)
        if not is_valid:
            return ExecutionResult.failure(
                signal.signal_id,
                ResultCode.REJECTED,
                error
            )
        
        # 检查是否可以开仓
        can_open, reason = self.can_open_position()
        if not can_open:
            return ExecutionResult.failure(
                signal.signal_id,
                ResultCode.REJECTED,
                reason
            )
        
        # 准备执行 (实际执行由ExecutionEngine处理)
        self._daily_trade_count += 1
        
        return ExecutionResult(
            signal_id=signal.signal_id,
            code=ResultCode.SUCCESS,
            message="Signal validated and ready for execution"
        )
    
    def add_position(self, position: Position):
        """添加持仓"""
        self._positions.append(position)
        self.logger.info(f"Position added: {position.ticket}")
    
    def remove_position(self, ticket: int):
        """移除持仓"""
        self._positions = [p for p in self._positions if p.ticket != ticket]
        self.logger.info(f"Position removed: {ticket}")
    
    def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        return self._positions.copy()
    
    def get_total_exposure(self) -> float:
        """获取总敞口(手数)"""
        return sum(p.lot_size for p in self._positions)
    
    def get_total_profit(self) -> float:
        """获取总盈亏"""
        return sum(p.net_profit for p in self._positions)
```

**文件路径**: `/opt/trading-system/