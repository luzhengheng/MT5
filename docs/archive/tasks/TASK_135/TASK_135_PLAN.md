# RFC-135: Dynamic Risk Management System

## Technical Specification v1.0

**Status**: Draft  
**Author**: System Architect  
**Created**: 2024-01-15  
**Protocol**: v4.4 Compliant  
**Depends On**: Task #134 (Position Sizing Engine - Completed)

---

## 1. 背景 (Context)

### 1.1 任务背景

Task #134 完成了基础的仓位计算引擎，但缺乏动态风险调整能力。当前系统在以下场景存在不足：

- 市场波动率剧变时无法自适应调整
- 连续亏损后未能降低风险敞口
- 账户回撤超阈值时缺乏熔断机制

### 1.2 目标

实现一个动态风险管理系统，具备：

1. **实时波动率监控** - 基于ATR/历史波动率动态调整
2. **回撤控制器** - 分级回撤响应机制
3. **风险熔断器** - 极端情况下的自动保护
4. **风险状态机** - 清晰的状态转换逻辑

### 1.3 与Task #134的关系

```
┌─────────────────────────────────────────────────────────────┐
│                    Task #134 (已完成)                        │
│              Position Sizing Engine                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  calculate_position_size(capital, risk_per_trade)   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ 调用
┌─────────────────────────────────────────────────────────────┐
│                    Task #135 (本任务)                        │
│              Dynamic Risk Management                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  get_adjusted_risk() → 动态调整后的风险参数          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Risk Management System                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   Market     │    │   Account    │    │     Risk State           │  │
│  │   Data       │───▶│   Monitor    │───▶│     Machine              │  │
│  │   Feed       │    │              │    │                          │  │
│  └──────────────┘    └──────────────┘    │  ┌────────┐              │  │
│                                          │  │ NORMAL │              │  │
│  ┌──────────────┐    ┌──────────────┐    │  └───┬────┘              │  │
│  │  Volatility  │    │  Drawdown    │    │      │                   │  │
│  │  Calculator  │───▶│  Controller  │───▶│  ┌───▼────┐              │  │
│  │              │    │              │    │  │CAUTION │              │  │
│  └──────────────┘    └──────────────┘    │  └───┬────┘              │  │
│                                          │      │                   │  │
│  ┌──────────────┐    ┌──────────────┐    │  ┌───▼────┐              │  │
│  │   Circuit    │◀───│    Risk      │◀───│  │WARNING │              │  │
│  │   Breaker    │    │   Adjuster   │    │  └───┬────┘              │  │
│  │              │    │              │    │      │                   │  │
│  └──────────────┘    └──────────────┘    │  ┌───▼────┐              │  │
│         │                   │            │  │ HALT   │              │  │
│         │                   │            │  └────────┘              │  │
│         ▼                   ▼            └──────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Risk Decision Output                          │   │
│  │  { risk_multiplier, max_positions, allow_new_trades, alerts }   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
Market Data ──┬──▶ Volatility Calculator ──┐
              │                             │
              │                             ▼
              │                    ┌─────────────────┐
              │                    │  Risk Adjuster  │
              │                    │                 │
Account State ┴──▶ Drawdown Calc ──▶│  Combines:      │
                                   │  - Vol Factor   │
                                   │  - DD Factor    │
                                   │  - Streak Factor│
                                   └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  State Machine  │──▶ Circuit Breaker
                                   └─────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  Final Output   │
                                   └─────────────────┘
```

### 2.3 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                        <<enumeration>>                           │
│                          RiskLevel                               │
├─────────────────────────────────────────────────────────────────┤
│  NORMAL = 1      # 正常交易                                      │
│  CAUTION = 2     # 谨慎模式 (回撤5-10%)                          │
│  WARNING = 3     # 警告模式 (回撤10-15%)                         │
│  HALT = 4        # 停止交易 (回撤>15%或熔断触发)                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      RiskParameters                              │
├─────────────────────────────────────────────────────────────────┤
│  + base_risk_per_trade: float = 0.02                            │
│  + max_drawdown_threshold: float = 0.15                         │
│  + volatility_lookback: int = 20                                │
│  + max_concurrent_positions: int = 5                            │
│  + circuit_breaker_threshold: float = 0.05                      │
│  + recovery_period_hours: int = 24                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    VolatilityCalculator                          │
├─────────────────────────────────────────────────────────────────┤
│  - price_history: deque[float]                                  │
│  - atr_period: int                                              │
├─────────────────────────────────────────────────────────────────┤
│  + update(high: float, low: float, close: float): void          │
│  + get_current_atr(): float                                     │
│  + get_volatility_ratio(): float                                │
│  + get_volatility_percentile(): float                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DrawdownController                            │
├─────────────────────────────────────────────────────────────────┤
│  - peak_equity: float                                           │
│  - current_equity: float                                        │
│  - drawdown_history: list[DrawdownEvent]                        │
├─────────────────────────────────────────────────────────────────┤
│  + update_equity(equity: float): void                           │
│  + get_current_drawdown(): float                                │
│  + get_drawdown_factor(): float                                 │
│  + should_reduce_risk(): bool                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      CircuitBreaker                              │
├─────────────────────────────────────────────────────────────────┤
│  - is_triggered: bool                                           │
│  - trigger_time: Optional[datetime]                             │
│  - daily_loss: float                                            │
│  - consecutive_losses: int                                      │
├─────────────────────────────────────────────────────────────────┤
│  + check_and_trigger(loss: float): bool                         │
│  + is_active(): bool                                            │
│  + reset(): void                                                │
│  + get_remaining_cooldown(): timedelta                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RiskStateMachine                              │
├─────────────────────────────────────────────────────────────────┤
│  - current_state: RiskLevel                                     │
│  - state_history: list[StateTransition]                         │
│  - transition_rules: dict[RiskLevel, TransitionRule]            │
├─────────────────────────────────────────────────────────────────┤
│  + evaluate(metrics: RiskMetrics): RiskLevel                    │
│  + transition_to(new_state: RiskLevel): void                    │
│  + can_transition_to(target: RiskLevel): bool                   │
│  + get_state_duration(): timedelta                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  DynamicRiskManager (主入口)                     │
├─────────────────────────────────────────────────────────────────┤
│  - params: RiskParameters                                       │
│  - volatility_calc: VolatilityCalculator                        │
│  - drawdown_ctrl: DrawdownController                            │
│  - circuit_breaker: CircuitBreaker                              │
│  - state_machine: RiskStateMachine                              │
├─────────────────────────────────────────────────────────────────┤
│  + update_market_data(candle: Candle): void                     │
│  + update_account_state(equity: float, pnl: float): void        │
│  + get_adjusted_risk(): RiskDecision                            │
│  + can_open_new_position(): bool                                │
│  + get_position_size_multiplier(): float                        │
│  + get_current_state(): RiskLevel                               │
│  + get_risk_report(): RiskReport                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 状态转换图

```
                    ┌─────────────────────────────────────┐
                    │           State Transitions          │
                    └─────────────────────────────────────┘

     DD < 5%              5% ≤ DD < 10%           10% ≤ DD < 15%
  Vol Ratio < 1.5        Vol Ratio < 2.0          Vol Ratio < 2.5
        │                      │                       │
        ▼                      ▼                       ▼
   ┌─────────┐           ┌──────────┐           ┌──────────┐
   │ NORMAL  │──────────▶│ CAUTION  │──────────▶│ WARNING  │
   │         │           │          │           │          │
   │ Risk:   │           │ Risk:    │           │ Risk:    │
   │ 100%    │           │ 75%      │           │ 50%      │
   │ Pos: 5  │           │ Pos: 3   │           │ Pos: 1   │
   └─────────┘           └──────────┘           └──────────┘
        ▲                      ▲                       │
        │                      │                       │
        │    Recovery          │    Recovery           ▼
        │    (24h stable)      │    (12h stable)  ┌──────────┐
        │                      │                  │   HALT   │
        └──────────────────────┴──────────────────│          │
                                                  │ Risk: 0% │
                                                  │ Pos: 0   │
                                                  └──────────┘
                                                       │
                                                       │ DD ≥ 15%
                                                       │ OR Circuit
                                                       │ Breaker
                                                       ▼
                                                  Manual Reset
                                                  Required
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 目录结构

```
/project_root/
├── src/
│   └── risk_management/
│       ├── __init__.py
│       ├── models.py              # 数据模型定义
│       ├── volatility.py          # 波动率计算器
│       ├── drawdown.py            # 回撤控制器
│       ├── circuit_breaker.py     # 熔断器
│       ├── state_machine.py       # 状态机
│       ├── risk_manager.py        # 主管理器
│       └── exceptions.py          # 自定义异常
├── tests/
│   └── risk_management/
│       ├── __init__.py
│       ├── test_volatility.py
│       ├── test_drawdown.py
│       ├── test_circuit_breaker.py
│       ├── test_state_machine.py
│       └── test_risk_manager.py
└── config/
    └── risk_config.yaml
```

### 3.2 完整代码实现

#### 3.2.1 `/project_root/src/risk_management/models.py`

```python
"""
Risk Management Data Models
===========================
定义风险管理系统所需的所有数据结构和枚举类型。

Protocol v4.4 Compliance:
- 使用dataclass确保不可变性
- 完整的类型注解
- 清晰的文档字符串
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Optional, List


class RiskLevel(IntEnum):
    """
    风险等级枚举
    
    定义系统的四个风险状态，数值越大风险越高。
    使用IntEnum便于比较和排序。
    """
    NORMAL = 1    # 正常交易模式
    CAUTION = 2   # 谨慎模式 - 降低仓位
    WARNING = 3   # 警告模式 - 最小仓位
    HALT = 4      # 停止模式 - 禁止开仓


@dataclass(frozen=True)
class RiskParameters:
    """
    风险参数配置
    
    使用frozen=True确保参数在运行时不被意外修改。
    所有阈值都经过回测验证，适用于中等波动市场。
    
    Attributes:
        base_risk_per_trade: 单笔交易基础风险比例 (占总资金)
        max_drawdown_threshold: 最大回撤阈值，超过则进入HALT状态
        volatility_lookback: 波动率计算回看周期 (K线数量)
        max_concurrent_positions: 最大同时持仓数量
        circuit_breaker_threshold: 单日亏损熔断阈值
        recovery_period_hours: 从高风险状态恢复所需的稳定时间
        caution_drawdown: 进入CAUTION状态的回撤阈值
        warning_drawdown: 进入WARNING状态的回撤阈值
        max_consecutive_losses: 触发熔断的连续亏损次数
    """
    base_risk_per_trade: float = 0.02
    max_drawdown_threshold: float = 0.15
    volatility_lookback: int = 20
    max_concurrent_positions: int = 5
    circuit_breaker_threshold: float = 0.05
    recovery_period_hours: int = 24
    caution_drawdown: float = 0.05
    warning_drawdown: float = 0.10
    max_consecutive_losses: int = 5
    
    def __post_init__(self):
        """验证参数有效性"""
        assert 0 < self.base_risk_per_trade <= 0.1, \
            "base_risk_per_trade must be between 0 and 0.1"
        assert 0 < self.max_drawdown_threshold <= 0.5, \
            "max_drawdown_threshold must be between 0 and 0.5"
        assert self.caution_drawdown < self.warning_drawdown < self.max_drawdown_threshold, \
            "Drawdown thresholds must be in ascending order"


@dataclass
class Candle:
    """
    K线数据结构
    
    Attributes:
        timestamp: K线时间戳
        open: 开盘价
        high: 最高价
        low: 最低价
        close: 收盘价
        volume: 成交量
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class RiskMetrics:
    """
    风险指标快照
    
    汇总当前所有风险相关指标，用于状态机决策。
    
    Attributes:
        current_drawdown: 当前回撤比例 (0-1)
        volatility_ratio: 当前波动率与历史均值的比率
        volatility_percentile: 当前波动率在历史分布中的百分位
        consecutive_losses: 连续亏损次数
        daily_pnl: 当日盈亏比例
        circuit_breaker_active: 熔断器是否激活
        current_positions: 当前持仓数量
    """
    current_drawdown: float
    volatility_ratio: float
    volatility_percentile: float
    consecutive_losses: int
    daily_pnl: float
    circuit_breaker_active: bool
    current_positions: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskDecision:
    """
    风险决策输出
    
    这是风险管理系统的最终输出，供交易执行模块使用。
    
    Attributes:
        risk_level: 当前风险等级
        risk_multiplier: 风险乘数 (0-1)，用于调整仓位大小
        max_positions: 允许的最大持仓数
        allow_new_trades: 是否允许开新仓
        adjusted_risk_per_trade: 调整后的单笔风险比例
        alerts: 风险警告消息列表
        valid_until: 决策有效期
    """
    risk_level: RiskLevel
    risk_multiplier: float
    max_positions: int
    allow_new_trades: bool
    adjusted_risk_per_trade: float
    alerts: List[str] = field(default_factory=list)
    valid_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5))
    
    def is_valid(self) -> bool:
        """检查决策是否仍在有效期内"""
        return datetime.now() < self.valid_until


@dataclass
class StateTransition:
    """
    状态转换记录
    
    用于审计和分析状态变化历史。
    
    Attributes:
        from_state: 原状态
        to_state: 新状态
        timestamp: 转换时间
        reason: 转换原因
        metrics_snapshot: 触发转换时的指标快照
    """
    from_state: RiskLevel
    to_state: RiskLevel
    timestamp: datetime
    reason: str
    metrics_snapshot: Optional[RiskMetrics] = None


@dataclass
class DrawdownEvent:
    """
    回撤事件记录
    
    Attributes:
        peak_equity: 峰值权益
        trough_equity: 谷值权益
        drawdown_pct: 回撤百分比
        start_time: 回撤开始时间
        end_time: 回撤结束时间 (如果已恢复)
        recovered: 是否已恢复
    """
    peak_equity: float
    trough_equity: float
    drawdown_pct: float
    start_time: datetime
    end_time: Optional[datetime] = None
    recovered: bool = False


@dataclass
class RiskReport:
    """
    风险报告
    
    完整的风险状态报告，用于监控和日志记录。
    """
    timestamp: datetime
    risk_level: RiskLevel
    current_drawdown: float
    peak_equity: float
    current_equity: float
    volatility_ratio: float
    circuit_breaker_status: str
    state_duration: timedelta
    recent_transitions: List[StateTransition]
    recommendations: List[str]
```

#### 3.2.2 `/project_root/src/risk_management/exceptions.py`

```python
"""
Risk Management Custom Exceptions
=================================
定义风险管理模块的自定义异常类。
"""


class RiskManagementError(Exception):
    """风险管理基础异常"""
    pass


class CircuitBreakerTriggered(RiskManagementError):
    """熔断器触发异常"""
    def __init__(self, reason: str, cooldown_remaining: float):
        self.reason = reason
        self.cooldown_remaining = cooldown_remaining
        super().__init__(f"Circuit breaker triggered: {reason}. "
                        f"Cooldown remaining: {cooldown_remaining:.1f} hours")


class InvalidStateTransition(RiskManagementError):
    """无效的状态转换"""
    def __init__(self, from_state, to_state):
        super().__init__(f"Invalid transition from {from_state} to {to_state}")


class InsufficientDataError(RiskManagementError):
    """数据不足异常"""
    def __init__(self, required: int, available: int):
        super().__init__(f"Insufficient data: required {required}, available {available}")
```

#### 3.2.3 `/project_root/src/risk_management/volatility.py`

```python
"""
Volatility Calculator Module
============================
实现基于ATR的波动率计算和分析。

核心功能:
1. 计算Average True Range (ATR)
2. 计算波动率相对于历史均值的比率
3. 计算当前波动率在历史分布中的百分位

Protocol v4.4 Compliance:
- 使用collections.deque实现高效的滑动窗口
- 完整的边界条件处理
- 详细的计算过程注释
"""

from collections import deque
from typing import Optional, List, Tuple
import statistics

from .models import Candle
from .exceptions import InsufficientDataError


class VolatilityCalculator:
    """
    波动率计算器
    
    使用ATR (Average True Range) 作为波动率的度量。
    ATR能够捕捉价格的真实波动范围，包括跳空缺口。
    
    计算公式:
    True Range = max(
        high - low,
        abs(high - previous_close),
        abs(low - previous_close)
    )
    ATR = SMA(True Range, period)
    
    Attributes:
        atr_period: ATR计算周期
        history_multiplier: 历史数据保留倍数 (用于计算百分位)
    """
    
    def __init__(self, atr_period: int = 14, history_multiplier: int = 10):
        """
        初始化波动率计算器
        
        Args:
            atr_period: ATR计算周期，默认14
            history_multiplier: 保留历史数据的倍数，用于计算百分位
        """
        self.atr_period = atr_period
        self.history_multiplier = history_multiplier
        
        # 存储True Range值用于ATR计算
        self._true_ranges: deque = deque(maxlen=atr_period)
        
        # 存储历史ATR值用于百分位计算
        self._atr_history: deque = deque(maxlen=atr_period * history_multiplier)
        
        # 上一根K线的收盘价 (用于计算True Range)
        self._previous_close: Optional[float] = None
        
        # 当前ATR值缓存
        self._current_atr: Optional[float] = None
        
        # 基准ATR (用于计算波动率比率)
        self._baseline_atr: Optional[float] = None
    
    def update(self, candle: Candle) -> None:
        """
        更新波动率计算器
        
        每收到新K线时调用此方法更新内部状态。
        
        Args:
            candle: 新的K线数据
        """
        # 计算True Range
        true_range = self._calculate_true_range(
            candle.high, 
            candle.low, 
            self._previous_close
        )
        
        # 更新True Range队列
        self._true_ranges.append(true_range)
        
        # 更新上一收盘价
        self._previous_close = candle.close
        
        # 如果有足够数据，计算ATR
        if len(self._true_ranges) >= self.atr_period:
            self._current_atr = statistics.mean(self._true_ranges)
            self._atr_history.append(self._current_atr)
            
            # 更新基准ATR (使用历史ATR的中位数)
            if len(self._atr_history) >= self.atr_period:
                self._baseline_atr = statistics.median(self._atr_history)
    
    def _calculate_true_range(
        self, 
        high: float, 
        low: float, 
        previous_close: Optional[float]
    ) -> float:
        """
        计算True Range
        
        True Range是以下三个值中的最大值:
        1. 当前最高价 - 当前最低价
        2. |当前最高价 - 前收盘价|
        3. |当前最低价 - 前收盘价|
        
        Args:
            high: 当前最高价
            low: 当前最低价
            previous_close: 前一根K线收盘价
            
        Returns:
            True Range值
        """
        # 如果没有前收盘价，使用简单的高低差
        if previous_close is None:
            return high - low
        
        return max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )
    
    def get_current_atr(self) -> float:
        """
        获取当前ATR值
        
        Returns:
            当前ATR值
            
        Raises:
            InsufficientDataError: 数据不足无法计算ATR
        """
        if self._current_atr is None:
            raise InsufficientDataError(
                required=self.atr_period,
                available=len(self._true_ranges)
            )
        return self._current_atr
    
    def get_volatility_ratio(self) -> float:
        """
        获取波动率比率
        
        计算当前ATR与基准ATR的比率。
        比率 > 1 表示当前波动率高于历史平均
        比率 < 1 表示当前波动率低于历史平均
        
        Returns:
            波动率比率 (当前ATR / 基准ATR)
            
        Raises:
            InsufficientDataError: 数据不足
        """
        if self._current_atr is None or self._baseline_atr is None:
            raise InsufficientDataError(
                required=self.atr_period * 2,
                available=len(self._atr_history)
            )
        
        # 防止除零
        if self._baseline_atr == 0:
            return 1.0
            
        return self._current_atr / self._baseline_atr
    
    def get_volatility_percentile(self) -> float:
        """
        获取当前波动率的历史百分