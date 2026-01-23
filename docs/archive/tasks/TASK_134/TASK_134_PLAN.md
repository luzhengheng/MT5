# RFC-134: 三轨道交易系统扩展技术规格书

**Protocol Version**: v4.4  
**Task ID**: #134  
**Status**: Draft  
**Author**: System Architect  
**Date**: 2024-01-XX  
**Depends On**: Task #133 (Completed)

---

## 1. 背景 (Context)

### 1.1 前置任务回顾

Task #133 已完成基础交易引擎的实现，包括：
- 单轨道交易处理能力
- 基础并发控制机制
- 订单生命周期管理

### 1.2 任务目标

本任务将交易系统从单轨道扩展至三轨道并行处理架构，支持：
- **EUR (欧元)** 交易轨道
- **BTC (比特币)** 交易轨道  
- **GBP (英镑)** 交易轨道

同时验证并发限制机制在多轨道场景下的正确性。

### 1.3 核心挑战

```
┌─────────────────────────────────────────────────────────┐
│  Challenge Matrix                                        │
├─────────────────────────────────────────────────────────┤
│  1. 轨道隔离: 确保各轨道数据不交叉污染                    │
│  2. 资源竞争: 共享资源(数据库连接池)的公平分配            │
│  3. 并发上限: 系统级与轨道级并发限制的协调                │
│  4. 故障隔离: 单轨道故障不影响其他轨道                    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
                            ┌─────────────────────────────────┐
                            │      Load Balancer / Gateway     │
                            └───────────────┬─────────────────┘
                                            │
                            ┌───────────────▼─────────────────┐
                            │      TrackDispatcher            │
                            │   (Route by Asset Type)         │
                            └───────────────┬─────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              │                             │                             │
    ┌─────────▼─────────┐       ┌───────────▼───────────┐     ┌───────────▼───────────┐
    │   EUR Track       │       │    BTC Track          │     │    GBP Track          │
    │   ┌───────────┐   │       │   ┌───────────┐       │     │   ┌───────────┐       │
    │   │ Executor  │   │       │   │ Executor  │       │     │   │ Executor  │       │
    │   │ Pool (10) │   │       │   │ Pool (10) │       │     │   │ Pool (10) │       │
    │   └─────┬─────┘   │       │   └─────┬─────┘       │     │   └─────┬─────┘       │
    │         │         │       │         │             │     │         │             │
    │   ┌─────▼─────┐   │       │   ┌─────▼─────┐       │     │   ┌─────▼─────┐       │
    │   │ Rate      │   │       │   │ Rate      │       │     │   │ Rate      │       │
    │   │ Limiter   │   │       │   │ Limiter   │       │     │   │ Limiter   │       │
    │   └─────┬─────┘   │       │   └─────┬─────┘       │     │   └─────┬─────┘       │
    │         │         │       │         │             │     │         │             │
    │   ┌─────▼─────┐   │       │   ┌─────▼─────┐       │     │   ┌─────▼─────┐       │
    │   │ Order     │   │       │   │ Order     │       │     │   │ Order     │       │
    │   │ Queue     │   │       │   │ Queue     │       │     │   │ Queue     │       │
    │   └───────────┘   │       │   └───────────┘       │     │   └───────────┘       │
    └─────────┬─────────┘       └───────────┬───────────┘     └───────────┬───────────┘
              │                             │                             │
              └─────────────────────────────┼─────────────────────────────┘
                                            │
                            ┌───────────────▼─────────────────┐
                            │     Shared Resource Pool        │
                            │  ┌─────────────────────────┐    │
                            │  │ DB Connection Pool (30) │    │
                            │  └─────────────────────────┘    │
                            │  ┌─────────────────────────┐    │
                            │  │ Global Rate Limiter     │    │
                            │  │ (100 req/sec)           │    │
                            │  └─────────────────────────┘    │
                            └─────────────────────────────────┘
```

### 2.2 数据流图

```
Order Request
      │
      ▼
┌─────────────────┐     ┌─────────────────┐
│ Validate Order  │────▶│ Extract Asset   │
└─────────────────┘     │ Type            │
                        └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │ EUR                   │ BTC                   │ GBP
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ EUR Track Queue │     │ BTC Track Queue │     │ GBP Track Queue │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Check Track     │     │ Check Track     │     │ Check Track     │
│ Concurrency     │     │ Concurrency     │     │ Concurrency     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │ Check Global        │
                    │ Concurrency Limit   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Execute Trade       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Update State &      │
                    │ Release Semaphore   │
                    └─────────────────────┘
```

### 2.3 类图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              <<interface>>                               │
│                              ITradeTrack                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ + submit_order(order: Order) -> OrderResult                             │
│ + get_active_count() -> int                                             │
│ + get_track_id() -> str                                                 │
│ + shutdown() -> None                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                      △
                                      │
                                      │ implements
                                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                            TradeTrack                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ - track_id: str                                                         │
│ - asset_type: AssetType                                                 │
│ - executor_pool: ThreadPoolExecutor                                     │
│ - rate_limiter: RateLimiter                                             │
│ - order_queue: asyncio.Queue                                            │
│ - semaphore: asyncio.Semaphore                                          │
│ - active_orders: AtomicCounter                                          │
│ - config: TrackConfig                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ + __init__(config: TrackConfig)                                         │
│ + submit_order(order: Order) -> OrderResult                             │
│ + get_active_count() -> int                                             │
│ + get_track_id() -> str                                                 │
│ + shutdown() -> None                                                    │
│ - _process_order(order: Order) -> OrderResult                           │
│ - _acquire_resources() -> bool                                          │
│ - _release_resources() -> None                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          TrackDispatcher                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ - tracks: Dict[AssetType, ITradeTrack]                                  │
│ - global_semaphore: asyncio.Semaphore                                   │
│ - global_rate_limiter: RateLimiter                                      │
│ - metrics: MetricsCollector                                             │
├─────────────────────────────────────────────────────────────────────────┤
│ + __init__(config: DispatcherConfig)                                    │
│ + dispatch(order: Order) -> OrderResult                                 │
│ + get_system_status() -> SystemStatus                                   │
│ + shutdown_all() -> None                                                │
│ - _route_to_track(order: Order) -> ITradeTrack                          │
│ - _check_global_limits() -> bool                                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         ConcurrencyLimiter                               │
├─────────────────────────────────────────────────────────────────────────┤
│ - track_limits: Dict[str, int]                                          │
│ - global_limit: int                                                     │
│ - track_counters: Dict[str, AtomicCounter]                              │
│ - global_counter: AtomicCounter                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ + acquire(track_id: str) -> bool                                        │
│ + release(track_id: str) -> None                                        │
│ + get_track_usage(track_id: str) -> int                                 │
│ + get_global_usage() -> int                                             │
│ + is_track_available(track_id: str) -> bool                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              <<enum>>                                    │
│                              AssetType                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ EUR = "EUR"                                                             │
│ BTC = "BTC"                                                             │
│ GBP = "GBP"                                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 项目结构

```
/project_root/
├── src/
│   └── trading/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── order.py
│       │   ├── enums.py
│       │   └── config.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── track.py
│       │   ├── dispatcher.py
│       │   └── limiter.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── atomic.py
│       │   └── metrics.py
│       └── exceptions.py
├── tests/
│   ├── __init__.py
│   ├── test_track.py
│   ├── test_dispatcher.py
│   ├── test_concurrency.py
│   └── test_integration.py
├── config/
│   └── trading_config.yaml
├── requirements.txt
└── README.md
```

### 3.2 完整代码实现

#### 3.2.1 `/project_root/src/trading/models/enums.py`

```python
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
```

#### 3.2.2 `/project_root/src/trading/models/config.py`

```python
"""
配置模型模块

定义系统配置的数据结构，支持从YAML文件加载配置。
所有配置项都有合理的默认值和验证逻辑。
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from pathlib import Path
import yaml

from .enums import AssetType


@dataclass
class TrackConfig:
    """
    单个交易轨道的配置
    
    Attributes:
        track_id: 轨道唯一标识符
        asset_type: 资产类型
        max_concurrent: 最大并发订单数
        rate_limit_per_second: 每秒最大请求数
        queue_size: 订单队列最大容量
        executor_pool_size: 执行器线程池大小
        timeout_seconds: 订单处理超时时间
    """
    track_id: str
    asset_type: AssetType
    max_concurrent: int = 10
    rate_limit_per_second: int = 50
    queue_size: int = 1000
    executor_pool_size: int = 10
    timeout_seconds: float = 30.0
    
    def __post_init__(self):
        """配置验证"""
        if self.max_concurrent <= 0:
            raise ValueError(f"max_concurrent must be positive, got {self.max_concurrent}")
        if self.rate_limit_per_second <= 0:
            raise ValueError(f"rate_limit_per_second must be positive")
        if self.queue_size <= 0:
            raise ValueError(f"queue_size must be positive")
        if self.executor_pool_size <= 0:
            raise ValueError(f"executor_pool_size must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be positive")


@dataclass
class DispatcherConfig:
    """
    调度器配置
    
    Attributes:
        global_max_concurrent: 全局最大并发数
        global_rate_limit_per_second: 全局每秒最大请求数
        track_configs: 各轨道配置映射
        db_pool_size: 数据库连接池大小
        enable_metrics: 是否启用指标收集
    """
    global_max_concurrent: int = 30
    global_rate_limit_per_second: int = 100
    track_configs: Dict[AssetType, TrackConfig] = field(default_factory=dict)
    db_pool_size: int = 30
    enable_metrics: bool = True
    
    def __post_init__(self):
        """初始化默认轨道配置"""
        if not self.track_configs:
            # 创建三个默认轨道配置
            for asset_type in AssetType.get_all_types():
                self.track_configs[asset_type] = TrackConfig(
                    track_id=f"TRACK_{asset_type.value}",
                    asset_type=asset_type,
                    max_concurrent=10,
                    rate_limit_per_second=50
                )
        
        # 验证全局并发数不小于各轨道之和
        total_track_concurrent = sum(
            tc.max_concurrent for tc in self.track_configs.values()
        )
        if self.global_max_concurrent < total_track_concurrent:
            # 自动调整为轨道并发数之和
            self.global_max_concurrent = total_track_concurrent
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "DispatcherConfig":
        """
        从YAML文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            DispatcherConfig: 配置实例
        """
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        track_configs = {}
        for asset_str, track_data in data.get('tracks', {}).items():
            asset_type = AssetType(asset_str)
            track_configs[asset_type] = TrackConfig(
                track_id=track_data.get('track_id', f"TRACK_{asset_str}"),
                asset_type=asset_type,
                max_concurrent=track_data.get('max_concurrent', 10),
                rate_limit_per_second=track_data.get('rate_limit_per_second', 50),
                queue_size=track_data.get('queue_size', 1000),
                executor_pool_size=track_data.get('executor_pool_size', 10),
                timeout_seconds=track_data.get('timeout_seconds', 30.0)
            )
        
        return cls(
            global_max_concurrent=data.get('global_max_concurrent', 30),
            global_rate_limit_per_second=data.get('global_rate_limit_per_second', 100),
            track_configs=track_configs,
            db_pool_size=data.get('db_pool_size', 30),
            enable_metrics=data.get('enable_metrics', True)
        )
```

#### 3.2.3 `/project_root/src/trading/models/order.py`

```python
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
```

#### 3.2.4 `/project_root/src/trading/utils/atomic.py`

```python
"""
原子操作工具模块

提供线程安全的原子计数器和其他并发原语。
"""

import threading
from typing import Optional


class AtomicCounter:
    """
    线程安全的原子计数器
    
    使用锁机制确保计数操作的原子性。
    支持增加、减少、获取当前值等操作。
    """
    
    def __init__(self, initial_value: int = 0):
        """
        初始化计数器
        
        Args:
            initial_value: 初始值
        """
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, delta: int = 1) -> int:
        """
        原子增加计数器
        
        Args:
            delta: 增加量
            
        Returns:
            int: 增加后的值
        """
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        """
        原子减少计数器
        
        Args:
            delta: 减少量
            
        Returns:
            int: 减少后的值
        """
        with self._lock:
            self._value -= delta
            return self._value
    
    def get(self) -> int:
        """
        获取当前值
        
        Returns:
            int: 当前计数值
        """
        with self._lock:
            return self._value
    
    def set(self, value: int) -> None:
        """
        设置计数器值
        
        Args:
            value: 新值
        """
        with self._lock:
            self._value = value
    
    def compare_and_set(self, expected: int, new_value: int) -> bool:
        """
        比较并设置（CAS操作）
        
        Args:
            expected: 期望的当前值
            new_value: 要设置的新值
            
        Returns:
            bool: 如果当前值等于期望值则设置成功返回True
        """
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False
    
    def increment_if_less_than(self, limit: int) -> bool:
        """
        如果当前值小于限制则增加
        
        用于实现有上限的计数器。
        
        Args:
            limit: 上限值
            
        Returns:
            bool: 是否成功增加
        """
        with self._lock:
            if self._value < limit:
                self._value += 1
                return True
            return False


class AtomicFlag:
    """
    线程安全的原子标志
    
    用于实现简单的开关状态。
    """
    
    def __init__(self, initial_value: bool = False):
        """
        初始化标志
        
        Args:
            initial_value: 初始值
        """
        self._value = initial_value
        self._lock = threading.Lock()
    
    def set(self) -> bool:
        """
        设置标志为True
        
        Returns:
            bool: 之前的值
        """
        with self._lock:
            old_value = self._value
            self._value = True
            return old_value
    
    def clear(self) -> bool:
        """
        清除标志（设为False）
        
        Returns:
            bool: 之前的值
        """
        with self._lock:
            old_value = self._value
            self._value = False
            return