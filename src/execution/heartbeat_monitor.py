#!/usr/bin/env python3
"""
Heartbeat Monitor - Connection Health Monitor for MT5 Live Bridge
Task #106 - MT5 Live Connector Implementation

Protocol v4.3 (Zero-Trust Edition) compliant heartbeat monitoring
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# Secure module loading
sys.path.insert(0, str(Path(__file__).parent))
from secure_loader import SecureModuleLoader, SecurityError

# Initialize secure loader
_loader = SecureModuleLoader(allowed_base_dir=Path(__file__).parent.parent)

# Load circuit_breaker with security validation
try:
    _cb_path = Path(__file__).parent.parent / "risk" / "circuit_breaker.py"
    _cb_module = _loader.load_module(_cb_path, module_name="circuit_breaker_module")
    CircuitBreaker = _cb_module.CircuitBreaker
except SecurityError as e:
    raise ImportError(f"Failed to load CircuitBreaker module securely: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HeartbeatMonitor')


class ConnectionStatus(Enum):
    """连接状态枚举"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class HeartbeatMetrics:
    """心跳指标"""
    total_pings: int = 0
    successful_pings: int = 0
    failed_pings: int = 0
    consecutive_failures: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    average_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')

    @property
    def success_rate(self) -> float:
        """成功率百分比"""
        if self.total_pings == 0:
            return 0.0
        return (self.successful_pings / self.total_pings) * 100

    @property
    def is_healthy(self) -> bool:
        """是否健康（连续失败 < 3）"""
        return self.consecutive_failures < 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_pings": self.total_pings,
            "successful_pings": self.successful_pings,
            "failed_pings": self.failed_pings,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": f"{self.success_rate:.2f}%",
            "average_latency_ms": f"{self.average_latency_ms:.3f}",
            "max_latency_ms": f"{self.max_latency_ms:.3f}",
            "min_latency_ms": f"{self.min_latency_ms:.3f}" if self.min_latency_ms != float('inf') else "N/A",
            "last_success": self.last_success_time.isoformat() if self.last_success_time else "N/A",
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else "N/A"
        }


class HeartbeatMonitor:
    """
    Heartbeat Monitor - 监控 Inf ↔ GTW 连接健康度

    核心功能：
    1. 定期 PING GTW（默认 5 秒）
    2. 记录延迟和成功率
    3. 检测连续失败（3 次 = 触发熔断）
    4. 提供重连机制
    5. 线程安全

    使用示例：
        monitor = HeartbeatMonitor(
            ping_callable=mt5_client.ping,
            circuit_breaker=circuit_breaker,
            interval_seconds=5,
            failure_threshold=3
        )

        # 启动监控
        monitor.start()

        # 查看状态
        status = monitor.get_status()
        metrics = monitor.get_metrics()

        # 停止监控
        monitor.stop()
    """

    def __init__(
        self,
        ping_callable: Callable[[], Dict[str, Any]],
        circuit_breaker: CircuitBreaker,
        interval_seconds: float = 5.0,
        failure_threshold: int = 3,
        timeout_seconds: float = 2.0,
        on_failure_callback: Optional[Callable[[str], None]] = None
    ):
        """
        初始化心跳监控器

        Args:
            ping_callable: 执行 PING 的可调用对象（返回 {"status": "ok", "latency_ms": 1.23}）
            circuit_breaker: 熔断器实例（用于触发 Kill Switch）
            interval_seconds: 心跳间隔（秒）
            failure_threshold: 连续失败阈值（触发熔断）
            timeout_seconds: PING 超时时间（秒）
            on_failure_callback: 失败回调函数（可选）
        """
        self.ping_callable = ping_callable
        self.circuit_breaker = circuit_breaker
        self.interval_seconds = interval_seconds
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.on_failure_callback = on_failure_callback

        self.metrics = HeartbeatMetrics()
        self.status = ConnectionStatus.UNKNOWN
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        logger.info(
            f"✅ HeartbeatMonitor 初始化完成 "
            f"(interval={interval_seconds}s, threshold={failure_threshold})"
        )

    def start(self) -> bool:
        """
        启动心跳监控

        Returns:
            bool: 启动是否成功
        """
        with self._lock:
            if self._running:
                logger.warning("HeartbeatMonitor 已在运行中")
                return False

            self._running = True
            self._thread = threading.Thread(
                target=self._heartbeat_loop,
                name="HeartbeatMonitor",
                daemon=True
            )
            self._thread.start()

            logger.info("🚀 HeartbeatMonitor 已启动")
            return True

    def stop(self) -> None:
        """停止心跳监控"""
        with self._lock:
            if not self._running:
                logger.warning("HeartbeatMonitor 未运行")
                return

            self._running = False
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=self.interval_seconds + 1)

            logger.info("🛑 HeartbeatMonitor 已停止")

    def _heartbeat_loop(self) -> None:
        """心跳循环（在独立线程中运行）"""
        logger.info("💓 心跳循环开始")

        while self._running:
            try:
                # 执行 PING
                self._execute_ping()

                # 检查是否需要触发熔断
                if self.metrics.consecutive_failures >= self.failure_threshold:
                    self._trigger_circuit_breaker()

                # 等待下一次心跳
                time.sleep(self.interval_seconds)

            except Exception as e:
                logger.error(f"❌ 心跳循环异常: {e}")
                time.sleep(self.interval_seconds)

        logger.info("💓 心跳循环结束")

    def _execute_ping(self) -> None:
        """执行单次 PING"""
        start_time = time.time()

        try:
            # 调用 PING 函数
            response = self.ping_callable()

            # 计算延迟
            latency_ms = (time.time() - start_time) * 1000

            # 检查响应状态
            if response.get("status") == "ok":
                self._record_success(latency_ms)
            else:
                self._record_failure(f"PING failed: {response}")

        except Exception as e:
            # PING 超时或异常
            latency_ms = (time.time() - start_time) * 1000
            self._record_failure(f"PING exception: {e}")

    def _record_success(self, latency_ms: float) -> None:
        """记录成功的 PING"""
        with self._lock:
            self.metrics.total_pings += 1
            self.metrics.successful_pings += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = datetime.utcnow()

            # 更新延迟统计
            total_pings = self.metrics.total_pings
            self.metrics.average_latency_ms = (
                (self.metrics.average_latency_ms * (total_pings - 1) + latency_ms) / total_pings
            )
            self.metrics.max_latency_ms = max(self.metrics.max_latency_ms, latency_ms)
            self.metrics.min_latency_ms = min(self.metrics.min_latency_ms, latency_ms)

            # 更新状态
            if latency_ms < 50:
                self.status = ConnectionStatus.HEALTHY
            elif latency_ms < 100:
                self.status = ConnectionStatus.DEGRADED
            else:
                self.status = ConnectionStatus.DEGRADED
                logger.warning(f"⚠️  高延迟检测: {latency_ms:.3f}ms")

            logger.debug(f"💚 PING 成功 (延迟: {latency_ms:.3f}ms)")

    def _record_failure(self, error_msg: str) -> None:
        """记录失败的 PING"""
        with self._lock:
            self.metrics.total_pings += 1
            self.metrics.failed_pings += 1
            self.metrics.consecutive_failures += 1
            self.metrics.last_failure_time = datetime.utcnow()

            # 更新状态
            if self.metrics.consecutive_failures >= self.failure_threshold:
                self.status = ConnectionStatus.FAILED
            else:
                self.status = ConnectionStatus.DEGRADED

            logger.error(
                f"❌ PING 失败 (连续失败: {self.metrics.consecutive_failures}/{self.failure_threshold}) - {error_msg}"
            )

            # 触发失败回调
            if self.on_failure_callback:
                try:
                    self.on_failure_callback(error_msg)
                except Exception as e:
                    logger.error(f"❌ 失败回调执行异常: {e}")

    def _trigger_circuit_breaker(self) -> None:
        """触发熔断器（Kill Switch）"""
        with self._lock:
            logger.critical(
                f"🚨 连续失败达到阈值 ({self.metrics.consecutive_failures}/{self.failure_threshold})，"
                f"触发熔断器"
            )

            try:
                # 触发熔断
                self.circuit_breaker.engage("HEARTBEAT_FAILURE")
                logger.critical("🔥 熔断器已激活 - 所有新订单将被阻止")

                # 停止心跳监控（避免重复触发）
                self._running = False

            except Exception as e:
                logger.error(f"❌ 触发熔断器失败: {e}")

    def get_status(self) -> ConnectionStatus:
        """
        获取当前连接状态

        Returns:
            ConnectionStatus: 连接状态
        """
        with self._lock:
            return self.status

    def get_metrics(self) -> HeartbeatMetrics:
        """
        获取心跳指标

        Returns:
            HeartbeatMetrics: 心跳指标副本
        """
        with self._lock:
            # 返回副本避免并发修改
            return HeartbeatMetrics(
                total_pings=self.metrics.total_pings,
                successful_pings=self.metrics.successful_pings,
                failed_pings=self.metrics.failed_pings,
                consecutive_failures=self.metrics.consecutive_failures,
                last_success_time=self.metrics.last_success_time,
                last_failure_time=self.metrics.last_failure_time,
                average_latency_ms=self.metrics.average_latency_ms,
                max_latency_ms=self.metrics.max_latency_ms,
                min_latency_ms=self.metrics.min_latency_ms
            )

    def is_healthy(self) -> bool:
        """
        检查连接是否健康

        Returns:
            bool: 健康返回 True，否则返回 False
        """
        with self._lock:
            return self.status in [ConnectionStatus.HEALTHY, ConnectionStatus.DEGRADED]

    def reset_metrics(self) -> None:
        """重置心跳指标（用于测试）"""
        with self._lock:
            self.metrics = HeartbeatMetrics()
            self.status = ConnectionStatus.UNKNOWN
            logger.info("🔄 心跳指标已重置")

    def get_summary(self) -> str:
        """
        获取心跳监控摘要（用于日志和监控）

        Returns:
            str: 格式化的摘要字符串
        """
        with self._lock:
            metrics_dict = self.metrics.to_dict()
            return (
                f"HeartbeatMonitor Summary:\n"
                f"  Status: {self.status.value}\n"
                f"  Total Pings: {metrics_dict['total_pings']}\n"
                f"  Success Rate: {metrics_dict['success_rate']}\n"
                f"  Consecutive Failures: {metrics_dict['consecutive_failures']}\n"
                f"  Avg Latency: {metrics_dict['average_latency_ms']}ms\n"
                f"  Max Latency: {metrics_dict['max_latency_ms']}ms\n"
                f"  Min Latency: {metrics_dict['min_latency_ms']}ms\n"
                f"  Last Success: {metrics_dict['last_success']}\n"
                f"  Last Failure: {metrics_dict['last_failure']}"
            )


# ============================================================================
# 使用示例
# ============================================================================

def example_usage():
    """HeartbeatMonitor 使用示例"""
    import os

    # 模拟 PING 函数
    ping_count = [0]

    def mock_ping() -> Dict[str, Any]:
        ping_count[0] += 1
        if ping_count[0] % 5 == 0:
            # 每 5 次失败一次（模拟）
            raise TimeoutError("Mock timeout")
        return {"status": "ok", "latency_ms": 1.23}

    # 创建熔断器
    lock_dir = os.getenv("MT5_CRS_LOCK_DIR", "/tmp/mt5_crs_test")
    os.makedirs(lock_dir, exist_ok=True)
    circuit_breaker = CircuitBreaker(lock_file_path=f"{lock_dir}/circuit_breaker.lock")

    # 创建心跳监控器
    monitor = HeartbeatMonitor(
        ping_callable=mock_ping,
        circuit_breaker=circuit_breaker,
        interval_seconds=2.0,
        failure_threshold=3,
        on_failure_callback=lambda msg: logger.warning(f"失败回调: {msg}")
    )

    # 启动监控
    monitor.start()

    try:
        # 运行 30 秒
        for i in range(15):
            time.sleep(2)
            status = monitor.get_status()
            metrics = monitor.get_metrics()
            print(f"\n[{i+1}] Status: {status.value}, Success Rate: {metrics.success_rate:.2f}%")

            if not monitor.is_healthy():
                print("⚠️  连接不健康！")
                break

    except KeyboardInterrupt:
        print("\n⚠️  被用户中断")

    finally:
        monitor.stop()
        print("\n" + monitor.get_summary())


if __name__ == "__main__":
    # 运行示例
    example_usage()
