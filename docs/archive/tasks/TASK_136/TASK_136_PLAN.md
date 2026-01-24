# RFC-136: Risk Modules 部署与熔断器功能验证技术规格书

**Protocol Version**: v4.4  
**Status**: Draft  
**Author**: System Architect  
**Created**: 2024-01-15  
**Depends-On**: RFC-135 (Completed)

---

## 1. 背景 (Context)

### 1.1 前置任务回顾

Task #135 已完成 Risk Modules 的核心开发，包括：
- 风险评估引擎 (Risk Assessment Engine)
- 熔断器模式实现 (Circuit Breaker Pattern)
- 风险指标采集器 (Risk Metrics Collector)
- 告警通知系统 (Alert Notification System)

### 1.2 当前任务目标

将 Task #135 产出的 Risk Modules 部署至 INF (Infrastructure) 节点，并在生产环境中验证 Circuit Breaker 的功能正确性、性能表现及故障恢复能力。

### 1.3 部署范围

```
┌─────────────────────────────────────────────────────────┐
│                    INF Node Cluster                      │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  inf-node-1 │  inf-node-2 │  inf-node-3 │  inf-node-4   │
│  (Primary)  │  (Secondary)│  (Secondary)│   (Standby)   │
└─────────────┴─────────────┴─────────────┴───────────────┘
```

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                         Load Balancer (L7)                          │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Rate Limiter │  │ Auth Filter  │  │ Route Filter │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Risk Modules Layer                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Circuit Breaker                           │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐                  │   │
│  │  │ CLOSED  │───▶│  OPEN   │───▶│HALF-OPEN│                  │   │
│  │  └─────────┘    └─────────┘    └─────────┘                  │   │
│  │       ▲                              │                       │   │
│  │       └──────────────────────────────┘                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │Risk Assessor │  │Metrics Store │  │Alert Manager │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Downstream Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Service A    │  │ Service B    │  │ Service C    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
Request Flow:
─────────────

[Client] ──▶ [Gateway] ──▶ [Circuit Breaker] ──┬──▶ [Service] ──▶ [Response]
                               │               │
                               │ (if OPEN)     │ (if CLOSED/HALF-OPEN)
                               ▼               │
                         [Fallback Response]   │
                               │               │
                               ▼               ▼
                         [Metrics Collector] ◀─┘
                               │
                               ▼
                         [Risk Assessor]
                               │
                               ▼
                         [Alert Manager] ──▶ [Notification Channels]
```

### 2.3 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                        CircuitBreaker                            │
├─────────────────────────────────────────────────────────────────┤
│ - state: CircuitState                                            │
│ - failureCount: int                                              │
│ - successCount: int                                              │
│ - lastFailureTime: datetime                                      │
│ - config: CircuitBreakerConfig                                   │
├─────────────────────────────────────────────────────────────────┤
│ + execute(func: Callable) -> Result                              │
│ + getState() -> CircuitState                                     │
│ + reset() -> void                                                │
│ + trip() -> void                                                 │
│ - evaluateState() -> void                                        │
│ - recordSuccess() -> void                                        │
│ - recordFailure() -> void                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CircuitBreakerConfig                         │
├─────────────────────────────────────────────────────────────────┤
│ + failureThreshold: int = 5                                      │
│ + successThreshold: int = 3                                      │
│ + timeout: int = 30                                              │
│ + halfOpenMaxCalls: int = 3                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        RiskAssessor                              │
├─────────────────────────────────────────────────────────────────┤
│ - metricsStore: MetricsStore                                     │
│ - thresholds: RiskThresholds                                     │
├─────────────────────────────────────────────────────────────────┤
│ + assessRisk(metrics: Metrics) -> RiskLevel                      │
│ + calculateScore(metrics: Metrics) -> float                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       DeploymentManager                          │
├─────────────────────────────────────────────────────────────────┤
│ - nodes: List[InfNode]                                           │
│ - deploymentConfig: DeploymentConfig                             │
├─────────────────────────────────────────────────────────────────┤
│ + deploy(artifact: Artifact) -> DeploymentResult                 │
│ + rollback(version: str) -> RollbackResult                       │
│ + healthCheck(node: InfNode) -> HealthStatus                     │
│ + verifyCircuitBreaker() -> VerificationResult                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 目录结构

```
/opt/inf-platform/
├── deployments/
│   └── risk-modules/
│       ├── config/
│       │   ├── circuit_breaker_config.yaml
│       │   ├── deployment_config.yaml
│       │   └── alert_config.yaml
│       ├── scripts/
│       │   ├── deploy.sh
│       │   ├── rollback.sh
│       │   ├── health_check.sh
│       │   └── verify_circuit_breaker.py
│       ├── src/
│       │   ├── circuit_breaker.py
│       │   ├── risk_assessor.py
│       │   ├── metrics_collector.py
│       │   ├── alert_manager.py
│       │   └── deployment_manager.py
│       ├── tests/
│       │   ├── test_circuit_breaker_live.py
│       │   ├── test_failover.py
│       │   └── test_recovery.py
│       └── kubernetes/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── configmap.yaml
│           └── hpa.yaml
└── logs/
    └── risk-modules/
```

### 3.2 核心配置文件

#### 3.2.1 `/opt/inf-platform/deployments/risk-modules/config/circuit_breaker_config.yaml`

```yaml
# Circuit Breaker Configuration for INF Node Deployment
# Protocol v4.4 Compliant
# RFC-136 Specification

version: "1.0.0"
metadata:
  name: "risk-modules-circuit-breaker"
  environment: "production"
  deployed_by: "rfc-136"
  
circuit_breaker:
  # 默认熔断器配置
  default:
    failure_threshold: 5          # 触发熔断的连续失败次数
    success_threshold: 3          # 从半开状态恢复需要的连续成功次数
    timeout_seconds: 30           # 熔断器开启后的超时时间
    half_open_max_calls: 3        # 半开状态允许的最大请求数
    failure_rate_threshold: 0.5   # 失败率阈值 (50%)
    slow_call_duration_threshold: 2000  # 慢调用阈值 (毫秒)
    slow_call_rate_threshold: 0.8       # 慢调用率阈值 (80%)
    
  # 按服务定制的熔断器配置
  services:
    payment_service:
      failure_threshold: 3        # 支付服务更敏感
      success_threshold: 5
      timeout_seconds: 60
      
    inventory_service:
      failure_threshold: 10       # 库存服务容忍度更高
      success_threshold: 3
      timeout_seconds: 20
      
    notification_service:
      failure_threshold: 15       # 通知服务非关键路径
      success_threshold: 2
      timeout_seconds: 10

# 监控与告警配置
monitoring:
  metrics_interval_seconds: 10
  health_check_interval_seconds: 30
  
alerts:
  channels:
    - type: "slack"
      webhook_url: "${SLACK_WEBHOOK_URL}"
      severity_filter: ["critical", "high"]
    - type: "pagerduty"
      integration_key: "${PAGERDUTY_KEY}"
      severity_filter: ["critical"]
    - type: "email"
      recipients: ["oncall@company.com"]
      severity_filter: ["critical", "high", "medium"]

# 降级策略
fallback:
  default_response:
    status_code: 503
    body:
      error: "Service temporarily unavailable"
      retry_after: 30
  cache_fallback:
    enabled: true
    max_age_seconds: 300
```

#### 3.2.2 `/opt/inf-platform/deployments/risk-modules/config/deployment_config.yaml`

```yaml
# Deployment Configuration for Risk Modules
# Protocol v4.4 Compliant

version: "1.0.0"
metadata:
  task_id: "136"
  depends_on: "135"
  
deployment:
  strategy: "rolling"
  max_surge: "25%"
  max_unavailable: "25%"
  
nodes:
  - name: "inf-node-1"
    role: "primary"
    host: "10.0.1.10"
    port: 8080
    weight: 100
    
  - name: "inf-node-2"
    role: "secondary"
    host: "10.0.1.11"
    port: 8080
    weight: 100
    
  - name: "inf-node-3"
    role: "secondary"
    host: "10.0.1.12"
    port: 8080
    weight: 100
    
  - name: "inf-node-4"
    role: "standby"
    host: "10.0.1.13"
    port: 8080
    weight: 0

health_check:
  endpoint: "/health"
  interval_seconds: 10
  timeout_seconds: 5
  healthy_threshold: 2
  unhealthy_threshold: 3

rollback:
  auto_rollback: true
  failure_threshold: 3
  observation_period_seconds: 300
```

### 3.3 核心源代码

#### 3.3.1 `/opt/inf-platform/deployments/risk-modules/src/circuit_breaker.py`

```python
#!/usr/bin/env python3
"""
Circuit Breaker Implementation for Risk Modules
Protocol v4.4 Compliant - RFC-136

This module implements the Circuit Breaker pattern to prevent cascade failures
in distributed systems. It monitors service calls and automatically opens the
circuit when failure thresholds are exceeded.

Author: System Architect
Version: 1.0.0
"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """
    熔断器状态枚举
    
    CLOSED: 正常状态，请求正常通过
    OPEN: 熔断状态，请求被拒绝
    HALF_OPEN: 半开状态，允许有限请求通过以测试服务恢复
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """
    熔断器配置类
    
    Attributes:
        failure_threshold: 触发熔断的连续失败次数
        success_threshold: 从半开恢复到关闭需要的连续成功次数
        timeout_seconds: 熔断器开启后的超时时间
        half_open_max_calls: 半开状态允许的最大请求数
        failure_rate_threshold: 失败率阈值
        slow_call_duration_threshold_ms: 慢调用阈值（毫秒）
        slow_call_rate_threshold: 慢调用率阈值
    """
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 30
    half_open_max_calls: int = 3
    failure_rate_threshold: float = 0.5
    slow_call_duration_threshold_ms: int = 2000
    slow_call_rate_threshold: float = 0.8
    
    def validate(self) -> bool:
        """验证配置有效性"""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")
        if not 0 < self.failure_rate_threshold <= 1:
            raise ValueError("failure_rate_threshold must be in (0, 1]")
        return True


@dataclass
class CircuitBreakerMetrics:
    """
    熔断器指标类
    
    用于收集和存储熔断器的运行时指标
    """
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    slow_calls: int = 0
    state_transitions: list = field(default_factory=list)
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "slow_calls": self.slow_calls,
            "failure_rate": self.failure_rate,
            "state_transitions": [
                {"from": t[0], "to": t[1], "time": t[2].isoformat()}
                for t in self.state_transitions[-10:]  # 只保留最近10次
            ]
        }
    
    @property
    def failure_rate(self) -> float:
        """计算失败率"""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls


class CircuitBreakerError(Exception):
    """熔断器异常基类"""
    pass


class CircuitOpenError(CircuitBreakerError):
    """熔断器开启时抛出的异常"""
    def __init__(self, circuit_name: str, remaining_time: float):
        self.circuit_name = circuit_name
        self.remaining_time = remaining_time
        super().__init__(
            f"Circuit '{circuit_name}' is OPEN. "
            f"Retry after {remaining_time:.1f} seconds."
        )


class CircuitBreaker:
    """
    熔断器核心实现类
    
    实现了完整的熔断器模式，包括：
    - 状态管理（CLOSED -> OPEN -> HALF_OPEN -> CLOSED）
    - 失败计数和阈值检测
    - 超时自动恢复
    - 线程安全操作
    - 指标收集
    
    Usage:
        >>> config = CircuitBreakerConfig(failure_threshold=5)
        >>> cb = CircuitBreaker("my_service", config)
        >>> result = cb.execute(lambda: external_service_call())
        
        # 或使用装饰器
        >>> @cb.decorator
        ... def my_function():
        ...     return external_service_call()
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ):
        """
        初始化熔断器
        
        Args:
            name: 熔断器名称，用于标识和日志
            config: 熔断器配置，如果为None则使用默认配置
            fallback: 降级函数，当熔断器开启时调用
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.config.validate()
        self.fallback = fallback
        
        # 状态管理
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        
        # 线程安全锁
        self._lock = threading.RLock()
        
        # 指标收集
        self._metrics = CircuitBreakerMetrics()
        
        # 事件回调
        self._on_state_change_callbacks: list = []
        
        logger.info(f"CircuitBreaker '{name}' initialized with config: {config}")
    
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            self._evaluate_state()
            return self._state
    
    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """获取指标"""
        return self._metrics
    
    def _evaluate_state(self) -> None:
        """
        评估并更新熔断器状态
        
        检查是否需要从OPEN状态转换到HALF_OPEN状态
        """
        if self._state == CircuitState.OPEN:
            if self._opened_at is not None:
                elapsed = (datetime.now() - self._opened_at).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    self._transition_to(CircuitState.HALF_OPEN)
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """
        状态转换
        
        Args:
            new_state: 目标状态
        """
        old_state = self._state
        self._state = new_state
        
        # 记录状态转换
        transition_time = datetime.now()
        self._metrics.state_transitions.append(
            (old_state.value, new_state.value, transition_time)
        )
        
        # 重置计数器
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        elif new_state == CircuitState.OPEN:
            self._opened_at = datetime.now()
        
        logger.warning(
            f"CircuitBreaker '{self.name}' state transition: "
            f"{old_state.value} -> {new_state.value}"
        )
        
        # 触发回调
        for callback in self._on_state_change_callbacks:
            try:
                callback(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def _record_success(self) -> None:
        """记录成功调用"""
        with self._lock:
            self._metrics.successful_calls += 1
            self._metrics.last_success_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                # 在CLOSED状态下，成功调用重置失败计数
                self._failure_count = 0
    
    def _record_failure(self) -> None:
        """记录失败调用"""
        with self._lock:
            self._failure_count += 1
            self._metrics.failed_calls += 1
            self._metrics.last_failure_time = datetime.now()
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # 半开状态下任何失败都触发熔断
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                # 检查是否达到失败阈值
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                # 检查失败率
                elif self._metrics.failure_rate >= self.config.failure_rate_threshold:
                    if self._metrics.total_calls >= 10:  # 最小样本量
                        self._transition_to(CircuitState.OPEN)
    
    def _can_execute(self) -> bool:
        """
        检查是否可以执行请求
        
        Returns:
            bool: True表示可以执行，False表示被拒绝
        """
        with self._lock:
            self._evaluate_state()
            
            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.OPEN:
                return False
            elif self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        return False
    
    def _get_remaining_timeout(self) -> float:
        """获取剩余超时时间"""
        if self._opened_at is None:
            return 0.0
        elapsed = (datetime.now() - self._opened_at).total_seconds()
        remaining = self.config.timeout_seconds - elapsed
        return max(0.0, remaining)
    
    def execute(
        self,
        func: Callable[[], Any],
        *args,
        **kwargs
    ) -> Any:
        """
        执行受熔断器保护的函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果或降级结果
            
        Raises:
            CircuitOpenError: 当熔断器开启且无降级函数时
        """
        self._metrics.total_calls += 1
        
        if not self._can_execute():
            self._metrics.rejected_calls += 1
            
            if self.fallback is not None:
                logger.info(
                    f"CircuitBreaker '{self.name}' is OPEN, "
                    f"executing fallback"
                )
                return self.fallback(*args, **kwargs)
            
            raise CircuitOpenError(
                self.name,
                self._get_remaining_timeout()
            )
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # 检查慢调用
            duration_ms = (time.time() - start_time) * 1000
            if duration_ms > self.config.slow_call_duration_threshold_ms:
                self._metrics.slow_calls += 1
                logger.warning(
                    f"CircuitBreaker '{self.name}' slow call detected: "
                    f"{duration_ms:.0f}ms"
                )
            
            self._record_success()
            return result
            
        except Exception as e:
            logger.error(
                f"CircuitBreaker '{self.name}' call failed: {e}"
            )
            self._record_failure()
            raise
    
    def decorator(self, func: Callable) -> Callable:
        """
        装饰器方式使用熔断器
        
        Usage:
            >>> @circuit_breaker.decorator
            ... def my_function():
            ...     return external_call()
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(lambda: func(*args, **kwargs))
        return wrapper
    
    def reset(self) -> None:
        """重置熔断器到初始状态"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._opened_at = None
            logger.info(f"CircuitBreaker '{self.name}' has been reset")
    
    def force_open(self) -> None:
        """强制开启熔断器"""
        with self._lock:
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"CircuitBreaker '{self.name}' forced OPEN")
    
    def on_state_change(self, callback: Callable) -> None:
        """注册状态变更回调"""
        self._on_state_change_callbacks.append(callback)
    
    def get_status(self) -> Dict:
        """获取熔断器状态信息"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout_seconds": self.config.timeout_seconds
                },
                "metrics": self._metrics.to_dict()
            }


class CircuitBreakerRegistry:
    """
    熔断器注册表
    
    管理多个熔断器实例，提供统一的访问接口
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers: Dict[str, CircuitBreaker] = {}
        return cls._instance
    
    def register(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ) -> CircuitBreaker:
        """注册新的熔断器"""
        if name in self._breakers:
            logger.warning(f"CircuitBreaker '{name}' already exists, returning existing instance")
            return self._breakers[name]
        
        breaker