"""
指标收集模块

提供系统性能和交易指标的收集和统计功能。
"""

import threading
from datetime import datetime
from typing import Dict, Any
from .atomic import AtomicCounter


class MetricsCollector:
    """
    指标收集器

    收集系统运行过程中的关键指标，包括：
    - 订单处理数量
    - 成功/失败率
    - 平均执行时间
    - 轨道级别指标
    """

    def __init__(self):
        """初始化指标收集器"""
        self._total_orders = AtomicCounter(0)
        self._successful_orders = AtomicCounter(0)
        self._failed_orders = AtomicCounter(0)
        self._rejected_orders = AtomicCounter(0)
        self._total_execution_time = 0.0
        self._track_metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._start_time = datetime.utcnow()

    def record_order_submitted(self) -> None:
        """记录提交的订单"""
        self._total_orders.increment()

    def record_order_success(self, execution_time_ms: float, track_id: str) -> None:
        """
        记录成功的订单

        Args:
            execution_time_ms: 执行时间（毫秒）
            track_id: 轨道ID
        """
        self._successful_orders.increment()
        with self._lock:
            self._total_execution_time += execution_time_ms
            self._update_track_metric(track_id, 'successful', 1)
            self._update_track_metric(track_id, 'total_execution_time', execution_time_ms)

    def record_order_failure(self, track_id: str, error_code: str = None) -> None:
        """
        记录失败的订单

        Args:
            track_id: 轨道ID
            error_code: 错误代码
        """
        self._failed_orders.increment()
        with self._lock:
            self._update_track_metric(track_id, 'failed', 1)
            if error_code:
                self._update_track_metric(track_id, f'error_{error_code}', 1)

    def record_order_rejected(self, track_id: str) -> None:
        """
        记录被拒绝的订单

        Args:
            track_id: 轨道ID
        """
        self._rejected_orders.increment()
        with self._lock:
            self._update_track_metric(track_id, 'rejected', 1)

    def _update_track_metric(self, track_id: str, metric_name: str, value: float) -> None:
        """
        更新轨道级别指标

        Args:
            track_id: 轨道ID
            metric_name: 指标名称
            value: 指标值（增量）
        """
        if track_id not in self._track_metrics:
            self._track_metrics[track_id] = {}

        if metric_name not in self._track_metrics[track_id]:
            self._track_metrics[track_id][metric_name] = 0.0

        self._track_metrics[track_id][metric_name] += value

    def get_summary(self) -> Dict[str, Any]:
        """
        获取指标摘要

        Returns:
            Dict: 包含所有关键指标的摘要
        """
        total = self._total_orders.get()
        successful = self._successful_orders.get()
        failed = self._failed_orders.get()
        rejected = self._rejected_orders.get()

        success_rate = (successful / total * 100) if total > 0 else 0.0
        avg_execution_time = (self._total_execution_time / successful) if successful > 0 else 0.0

        uptime = datetime.utcnow() - self._start_time

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_orders': total,
            'successful_orders': successful,
            'failed_orders': failed,
            'rejected_orders': rejected,
            'success_rate_percent': round(success_rate, 2),
            'avg_execution_time_ms': round(avg_execution_time, 2),
            'uptime_seconds': uptime.total_seconds(),
            'track_metrics': dict(self._track_metrics)
        }

    def get_track_summary(self, track_id: str) -> Dict[str, Any]:
        """
        获取特定轨道的指标摘要

        Args:
            track_id: 轨道ID

        Returns:
            Dict: 轨道的指标信息
        """
        with self._lock:
            metrics = self._track_metrics.get(track_id, {})
            return {
                'track_id': track_id,
                'metrics': dict(metrics)
            }

    def reset(self) -> None:
        """重置所有指标"""
        self._total_orders.set(0)
        self._successful_orders.set(0)
        self._failed_orders.set(0)
        self._rejected_orders.set(0)
        self._total_execution_time = 0.0
        with self._lock:
            self._track_metrics.clear()
        self._start_time = datetime.utcnow()
