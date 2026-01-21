# RFC-999: Logic Brain 连通性与模型准确性验证规格书

**Protocol Version**: v4.4  
**Task ID**: #999  
**Status**: Draft  
**Author**: Antigravity System Architect  
**Date**: 2024-01-XX  
**Depends On**: Task #130 (Logic Brain Core Implementation)

---

## 1. 背景 (Context)

### 1.1 前置任务回顾

Task #130 已完成 Logic Brain 核心模块的实现，包括：
- 逻辑推理引擎基础架构
- 模型加载与推理接口
- 基础 API 端点暴露

### 1.2 当前任务目标

本任务旨在建立一套完整的验证体系，确保：
1. **连通性验证**: Logic Brain 服务可达、API 响应正常、依赖服务健康
2. **模型准确性验证**: 推理结果符合预期基准、性能指标达标

### 1.3 验证范围

```
┌─────────────────────────────────────────────────────────────┐
│                    Verification Scope                        │
├─────────────────────────────────────────────────────────────┤
│  [Connectivity]          [Model Accuracy]                   │
│  ├── Health Check        ├── Inference Correctness         │
│  ├── API Reachability    ├── Benchmark Comparison          │
│  ├── Latency Metrics     ├── Edge Case Handling            │
│  └── Dependency Status   └── Confidence Threshold          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                     Verification System                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  Test Runner    │───▶│  Verification   │───▶│   Report     │ │
│  │  (Orchestrator) │    │  Engine         │    │   Generator  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                      │                      │        │
│           ▼                      ▼                      ▼        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Verification Modules                      ││
│  ├──────────────────┬──────────────────┬───────────────────────┤│
│  │ ConnectivityTest │ AccuracyTest     │ PerformanceTest       ││
│  │ ├─HealthProbe    │ ├─InferenceTest  │ ├─LatencyBenchmark    ││
│  │ ├─APIProbe       │ ├─BaselineComp   │ ├─ThroughputTest      ││
│  │ └─DependencyChk  │ └─EdgeCaseTest   │ └─ResourceMonitor     ││
│  └──────────────────┴──────────────────┴───────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Logic Brain Service                       ││
│  │                    (Target Under Test)                       ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
[Test Cases]──▶[Verification Engine]──▶[Logic Brain API]
                      │                        │
                      │                        ▼
                      │                 [Inference Result]
                      │                        │
                      ▼                        ▼
              [Result Collector]◀──────[Response Parser]
                      │
                      ▼
              [Report Generator]──▶[JSON/HTML Report]
```

### 2.3 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Class Diagram                            │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐       ┌──────────────────────┐
│   <<interface>>      │       │   <<interface>>      │
│   IVerificationTest  │       │   IReportGenerator   │
├──────────────────────┤       ├──────────────────────┤
│ + run(): TestResult  │       │ + generate(): Report │
│ + validate(): bool   │       │ + export(): void     │
└──────────────────────┘       └──────────────────────┘
          △                              △
          │                              │
    ┌─────┴─────┬─────────────┐         │
    │           │             │         │
┌───┴────┐ ┌────┴────┐ ┌──────┴──────┐ ┌┴─────────────┐
│Connect │ │Accuracy │ │Performance  │ │JSONReport    │
│Test    │ │Test     │ │Test         │ │Generator     │
├────────┤ ├─────────┤ ├─────────────┤ ├──────────────┤
│-client │ │-baseline│ │-metrics     │ │-results      │
│-timeout│ │-testData│ │-thresholds  │ │-template     │
├────────┤ ├─────────┤ ├─────────────┤ ├──────────────┤
│+probe()│ │+infer() │ │+benchmark() │ │+toJSON()     │
│+check()│ │+compare│ │+measure()   │ │+toHTML()     │
└────────┘ └─────────┘ └─────────────┘ └──────────────┘

┌────────────────────────────────────────┐
│           VerificationRunner           │
├────────────────────────────────────────┤
│ - tests: List[IVerificationTest]       │
│ - config: VerificationConfig           │
│ - reporter: IReportGenerator           │
├────────────────────────────────────────┤
│ + register_test(test): void            │
│ + run_all(): VerificationReport        │
│ + run_single(test_name): TestResult    │
└────────────────────────────────────────┘
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 目录结构

```
/project_root/
├── verification/
│   ├── __init__.py
│   ├── config.py
│   ├── runner.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── connectivity_test.py
│   │   ├── accuracy_test.py
│   │   └── performance_test.py
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── json_reporter.py
│   ├── data/
│   │   ├── baseline.json
│   │   └── test_cases.json
│   └── utils/
│       ├── __init__.py
│       └── http_client.py
├── tests/
│   └── test_verification.py
├── run_verification.py
└── requirements.txt
```

---

### 3.2 文件实现

#### 3.2.1 `/project_root/requirements.txt`

```text
# Logic Brain Verification Dependencies
# Protocol v4.4 Compliant

requests>=2.31.0
pydantic>=2.5.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
aiohttp>=3.9.0
rich>=13.7.0
numpy>=1.24.0
```

---

#### 3.2.2 `/project_root/verification/__init__.py`

```python
"""
Logic Brain Verification Package
================================

Protocol: v4.4
Task: #999
Depends: Task #130

This package provides comprehensive verification capabilities for
Logic Brain connectivity and model accuracy testing.
"""

from verification.runner import VerificationRunner
from verification.config import VerificationConfig

__version__ = "1.0.0"
__protocol__ = "v4.4"
__task_id__ = 999

__all__ = [
    "VerificationRunner",
    "VerificationConfig",
]
```

---

#### 3.2.3 `/project_root/verification/config.py`

```python
"""
Verification Configuration Module
=================================

Defines all configuration parameters for the verification system.
Supports environment variable overrides and validation.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class LogLevel(Enum):
    """Logging verbosity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class VerificationMode(Enum):
    """Verification execution modes."""
    FULL = "full"           # Run all tests
    CONNECTIVITY = "connectivity"  # Only connectivity tests
    ACCURACY = "accuracy"   # Only accuracy tests
    PERFORMANCE = "performance"  # Only performance tests


@dataclass
class EndpointConfig:
    """Configuration for a single API endpoint."""
    path: str
    method: str = "GET"
    expected_status: int = 200
    timeout: float = 30.0
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConnectivityConfig:
    """Connectivity test configuration."""
    # Logic Brain service base URL
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "LOGIC_BRAIN_URL", 
            "http://localhost:8080"
        )
    )
    
    # Health check endpoint
    health_endpoint: str = "/health"
    
    # API endpoints to verify
    api_endpoints: List[EndpointConfig] = field(default_factory=lambda: [
        EndpointConfig(path="/api/v1/status", method="GET"),
        EndpointConfig(path="/api/v1/inference", method="POST"),
        EndpointConfig(path="/api/v1/models", method="GET"),
    ])
    
    # Connection timeout in seconds
    connection_timeout: float = 10.0
    
    # Read timeout in seconds
    read_timeout: float = 30.0
    
    # Number of retry attempts
    retry_attempts: int = 3
    
    # Delay between retries in seconds
    retry_delay: float = 1.0
    
    # Maximum acceptable latency in milliseconds
    max_latency_ms: float = 1000.0


@dataclass
class AccuracyConfig:
    """Model accuracy test configuration."""
    # Path to baseline results file
    baseline_path: str = field(
        default_factory=lambda: os.getenv(
            "BASELINE_PATH",
            "/project_root/verification/data/baseline.json"
        )
    )
    
    # Path to test cases file
    test_cases_path: str = field(
        default_factory=lambda: os.getenv(
            "TEST_CASES_PATH",
            "/project_root/verification/data/test_cases.json"
        )
    )
    
    # Minimum acceptable accuracy (0.0 - 1.0)
    min_accuracy: float = 0.95
    
    # Confidence threshold for predictions
    confidence_threshold: float = 0.8
    
    # Maximum allowed deviation from baseline
    max_deviation: float = 0.05
    
    # Number of test samples to run
    sample_size: int = 100
    
    # Enable edge case testing
    test_edge_cases: bool = True


@dataclass
class PerformanceConfig:
    """Performance test configuration."""
    # Target latency percentiles
    latency_p50_ms: float = 100.0
    latency_p95_ms: float = 500.0
    latency_p99_ms: float = 1000.0
    
    # Minimum throughput (requests per second)
    min_throughput_rps: float = 10.0
    
    # Number of concurrent requests for load testing
    concurrent_requests: int = 10
    
    # Duration of load test in seconds
    load_test_duration: float = 60.0
    
    # Warmup requests before measurement
    warmup_requests: int = 5


@dataclass
class VerificationConfig:
    """
    Master configuration for the verification system.
    
    This configuration aggregates all sub-configurations and provides
    global settings for the verification process.
    
    Example:
        >>> config = VerificationConfig()
        >>> config.mode = VerificationMode.FULL
        >>> runner = VerificationRunner(config)
    """
    
    # Execution mode
    mode: VerificationMode = VerificationMode.FULL
    
    # Logging level
    log_level: LogLevel = LogLevel.INFO
    
    # Output directory for reports
    output_dir: str = field(
        default_factory=lambda: os.getenv(
            "VERIFICATION_OUTPUT_DIR",
            "/project_root/verification/reports"
        )
    )
    
    # Enable verbose output
    verbose: bool = False
    
    # Fail fast on first error
    fail_fast: bool = False
    
    # Sub-configurations
    connectivity: ConnectivityConfig = field(default_factory=ConnectivityConfig)
    accuracy: AccuracyConfig = field(default_factory=AccuracyConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate accuracy thresholds
        if not 0.0 <= self.accuracy.min_accuracy <= 1.0:
            raise ValueError(
                f"min_accuracy must be between 0.0 and 1.0, "
                f"got {self.accuracy.min_accuracy}"
            )
        
        if not 0.0 <= self.accuracy.confidence_threshold <= 1.0:
            raise ValueError(
                f"confidence_threshold must be between 0.0 and 1.0, "
                f"got {self.accuracy.confidence_threshold}"
            )
        
        # Validate performance thresholds
        if self.performance.latency_p50_ms > self.performance.latency_p95_ms:
            raise ValueError("P50 latency cannot be greater than P95")
        
        if self.performance.latency_p95_ms > self.performance.latency_p99_ms:
            raise ValueError("P95 latency cannot be greater than P99")
        
        # Validate connectivity settings
        if self.connectivity.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")
        
        return True
    
    @classmethod
    def from_env(cls) -> "VerificationConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            VerificationConfig: Configuration populated from environment
        """
        config = cls()
        
        # Override from environment
        if mode := os.getenv("VERIFICATION_MODE"):
            config.mode = VerificationMode(mode.lower())
        
        if log_level := os.getenv("LOG_LEVEL"):
            config.log_level = LogLevel(log_level.upper())
        
        config.verbose = os.getenv("VERBOSE", "false").lower() == "true"
        config.fail_fast = os.getenv("FAIL_FAST", "false").lower() == "true"
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            "mode": self.mode.value,
            "log_level": self.log_level.value,
            "output_dir": self.output_dir,
            "verbose": self.verbose,
            "fail_fast": self.fail_fast,
            "connectivity": {
                "base_url": self.connectivity.base_url,
                "health_endpoint": self.connectivity.health_endpoint,
                "connection_timeout": self.connectivity.connection_timeout,
                "retry_attempts": self.connectivity.retry_attempts,
            },
            "accuracy": {
                "min_accuracy": self.accuracy.min_accuracy,
                "confidence_threshold": self.accuracy.confidence_threshold,
                "sample_size": self.accuracy.sample_size,
            },
            "performance": {
                "latency_p50_ms": self.performance.latency_p50_ms,
                "latency_p95_ms": self.performance.latency_p95_ms,
                "latency_p99_ms": self.performance.latency_p99_ms,
                "min_throughput_rps": self.performance.min_throughput_rps,
            },
        }
```

---

#### 3.2.4 `/project_root/verification/tests/__init__.py`

```python
"""
Verification Tests Package
==========================

Contains all verification test implementations.
"""

from verification.tests.base import (
    IVerificationTest,
    TestResult,
    TestStatus,
)
from verification.tests.connectivity_test import ConnectivityTest
from verification.tests.accuracy_test import AccuracyTest
from verification.tests.performance_test import PerformanceTest

__all__ = [
    "IVerificationTest",
    "TestResult",
    "TestStatus",
    "ConnectivityTest",
    "AccuracyTest",
    "PerformanceTest",
]
```

---

#### 3.2.5 `/project_root/verification/tests/base.py`

```python
"""
Base Test Classes and Interfaces
================================

Defines the abstract base classes and data structures for all verification tests.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TestStatus(Enum):
    """Enumeration of possible test statuses."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class TestMetric:
    """A single metric measurement from a test."""
    name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    passed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary representation."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "threshold": self.threshold,
            "passed": self.passed,
        }


@dataclass
class TestResult:
    """
    Result of a single verification test.
    
    Contains all information about test execution including
    status, metrics, timing, and any error information.
    """
    # Test identification
    test_name: str
    test_category: str
    
    # Execution status
    status: TestStatus
    
    # Timing information
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Result details
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: List[TestMetric] = field(default_factory=list)
    
    # Error information (if applicable)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    def mark_completed(self) -> None:
        """Mark the test as completed and calculate duration."""
        self.completed_at = datetime.utcnow()
        self.duration_ms = (
            self.completed_at - self.started_at
        ).total_seconds() * 1000
    
    def add_metric(
        self,
        name: str,
        value: float,
        unit: str,
        threshold: Optional[float] = None
    ) -> None:
        """
        Add a metric to the test result.
        
        Args:
            name: Metric name
            value: Measured value
            unit: Unit of measurement
            threshold: Optional threshold for pass/fail
        """
        passed = True
        if threshold is not None:
            passed = value <= threshold
        
        self.metrics.append(TestMetric(
            name=name,
            value=value,
            unit=unit,
            threshold=threshold,
            passed=passed,
        ))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "test_name": self.test_name,
            "test_category": self.test_category,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() 
                if self.completed_at else None
            ),
            "duration_ms": self.duration_ms,
            "message": self.message,
            "details": self.details,
            "metrics": [m.to_dict() for m in self.metrics],
            "error": {
                "type": self.error_type,
                "message": self.error_message,
                "traceback": self.error_traceback,
            } if self.error_type else None,
        }


class IVerificationTest(ABC):
    """
    Abstract base class for all verification tests.
    
    All verification tests must implement this interface to ensure
    consistent behavior and integration with the test runner.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this test."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Return the category of this test (connectivity, accuracy, etc.)."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of what this test verifies."""
        pass
    
    @abstractmethod
    def run(self) -> TestResult:
        """
        Execute the verification test.
        
        Returns:
            TestResult: The result of the test execution
        """
        pass
    
    @abstractmethod
    def validate_prerequisites(self) -> bool:
        """
        Check if all prerequisites for this test are met.
        
        Returns:
            bool: True if prerequisites are satisfied
        """
        pass
    
    def create_result(
        self,
        status: TestStatus,
        message: str = "",
        **details: Any
    ) -> TestResult:
        """
        Helper method to create a TestResult for this test.
        
        Args:
            status: The test status
            message: Optional message describing the result
            **details: Additional details to include
            
        Returns:
            TestResult: A new TestResult instance
        """
        return TestResult(
            test_name=self.name,
            test_category=self.category,
            status=status,
            message=message,
            details=details,
        )
```

---

#### 3.2.6 `/project_root/verification/tests/connectivity_test.py`

```python
"""
Connectivity Verification Tests
===============================

Tests for verifying Logic Brain service connectivity, health,
and API endpoint availability.
"""

import time
import traceback
from typing import Optional, Tuple

import requests
from requests.exceptions import (
    ConnectionError,
    Timeout,
    RequestException,
)

from verification.config import ConnectivityConfig, EndpointConfig
from verification.tests.base import (
    IVerificationTest,
    TestResult,
    TestStatus,
)


class ConnectivityTest(IVerificationTest):
    """
    Comprehensive connectivity verification test.
    
    This test verifies:
    1. Service health endpoint is responding
    2. All configured API endpoints are reachable
    3. Response times are within acceptable thresholds
    4. Proper error handling for connection failures
    
    Example:
        >>> config = ConnectivityConfig(base_url="http://localhost:8080")
        >>> test = ConnectivityTest(config)
        >>> result = test.run()
        >>> print(result.status)
        TestStatus.PASSED
    """
    
    def __init__(self, config: ConnectivityConfig):
        """
        Initialize the connectivity test.
        
        Args:
            config: Connectivity configuration parameters
        """
        self._config = config
        self._session: Optional[requests.Session] = None
    
    @property
    def name(self) -> str:
        return "logic_brain_connectivity"
    
    @property
    def category(self) -> str:
        return "connectivity"
    
    @property
    def description(self) -> str:
        return (
            "Verifies Logic Brain service connectivity including "
            "health checks, API endpoint availability, and response latency"
        )
    
    def validate_prerequisites(self) -> bool:
        """
        Validate that configuration is properly set.
        
        Returns:
            bool: True if prerequisites are met
        """
        if not self._config.base_url:
            return False
        if not self._config.health_endpoint:
            return False
        return True
    
    def run(self) -> TestResult:
        """
        Execute the connectivity verification test.
        
        This method performs the following checks:
        1. Health endpoint probe
        2. API endpoint availability
        3. Latency measurements
        
        Returns:
            TestResult: Comprehensive test result
        """
        result = self.create_result(TestStatus.PASSED)
        
        try:
            # Initialize session
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "LogicBrain-Verification/1.0",
                "Accept": "application/json",
            })
            
            # Step 1: Health check
            health_passed, health_latency = self._check_health()
            result.add_metric(
                name="health_check_latency",
                value=health_latency,
                unit="ms",
                threshold=self._config.max_latency_ms,
            )
            
            if not health_passed:
                result.status = TestStatus.FAILED
                result.message = "Health check failed"
                result.mark_completed()
                return result
            
            # Step 2: API endpoint checks
            endpoint_results = []
            for endpoint in self._config.api_endpoints:
                ep_passed, ep_latency, ep_status = self._check_endpoint(endpoint)
                endpoint_results.append({
                    "path": endpoint.path,
                    "passed": ep_passed,
                    "latency_ms": ep_latency,
                    "status_code": ep_status,
                })
                
                result.add_metric(
                    name=f"endpoint_{endpoint.path.replace('/', '_')}_latency",
                    value=ep_latency,
                    unit="ms",
                    threshold=self._config.max_latency_ms,
                )
            
            # Aggregate results
            all_passed = all(r["passed"] for r in endpoint_results)
            result.details["endpoints"] = endpoint_results
            result.details["health_check"] = {
                "passed": health_passed,
                "latency_ms": health_latency,
            }
            
            if not all_passed:
                failed_endpoints = [
                    r["path"] for r in endpoint_results if not r["passed"]
                ]
                result.status = TestStatus.FAILED
                result.message = f"Failed endpoints: {', '.join(failed_endpoints)}"
            else:
                result.message = (
                    f"All {len(endpoint_results)} endpoints verified successfully"
                )
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_type = type(e).__name__
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            result.message = f"Unexpected error: {e}"
        
        finally:
            if self._session:
                self._session.close()
            result.mark_completed()
        
        return result
    
    def _check_health(self) -> Tuple[bool, float]:
        """
        Check the health endpoint.
        
        Returns:
            Tuple[bool, float]: (success, latency_ms)
        """
        url = f"{self._config.base_url}{self._config.health_endpoint}"
        
        for attempt in range(self._config.retry_attempts):
            try:
                start_time = time.perf_counter()
                response = self._session.get(
                    url,
                    timeout=(
                        self._config.connection_timeout,
                        self._config.read_timeout,
                    ),
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                if response.status_code == 200:
                    return True, latency_ms
                
            except (ConnectionError, Timeout) as e:
                if attempt < self._config.retry_attempts - 1:
                    time.sleep(self._config.retry_delay)
                    continue
                return False, 0.0
            
            except RequestException:
                return False, 0.0
        
        return False, 0.0
    
    def _check_endpoint(
        self,
        endpoint: EndpointConfig
    ) -> Tuple[bool, float, int]:
        """
        Check a specific API endpoint.
        
        Args:
            endpoint: Endpoint configuration
            
        Returns:
            Tuple[bool, float, int]: (success, latency_ms, status_code)
        """
        url = f"{self._config.base_url}{endpoint.path}"
        
        try:
            start_time = time.perf_counter()
            
            if endpoint.method.upper() == "GET":
                response = self._session.get(
                    url,
                    headers=endpoint.headers,
                    timeout=endpoint.timeout,
                )
            elif endpoint.method.upper() == "POST":
                # Send minimal valid payload for POST endpoints
                response = self._session.post(
                    url,
                    headers=endpoint.headers,
                    json={"test": True},
                    timeout=endpoint.timeout,
                )
            else:
                response = self._session.request(
                    endpoint.method,