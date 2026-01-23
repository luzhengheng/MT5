"""
速率限制和并发控制模块

提供流量控制和并发管理的机制。
"""

import threading
import time
from typing import Dict
from src.trading.utils.atomic import AtomicCounter


class RateLimiter:
    """
    速率限制器

    使用令牌桶算法实现速率限制。
    支持每秒固定请求数的限制。
    """

    def __init__(self, requests_per_second: int):
        """
        初始化速率限制器

        Args:
            requests_per_second: 每秒允许的最大请求数
        """
        self.rate = requests_per_second
        self.tokens = float(requests_per_second)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌

        Args:
            tokens: 所需令牌数

        Returns:
            bool: 是否成功获取
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # 补充令牌
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_and_acquire(self, tokens: int = 1) -> None:
        """
        等待直到获取令牌

        Args:
            tokens: 所需令牌数
        """
        while not self.acquire(tokens):
            time.sleep(0.01)  # 短暂等待后重试


class ConcurrencyLimiter:
    """
    并发限制器

    管理系统级和轨道级的并发限制。
    """

    def __init__(self, global_limit: int, track_limits: Dict[str, int] = None):
        """
        初始化并发限制器

        Args:
            global_limit: 全局最大并发数
            track_limits: 每个轨道的并发限制
        """
        self.global_limit = global_limit
        self.track_limits = track_limits or {}
        self.global_counter = AtomicCounter(0)
        self.track_counters: Dict[str, AtomicCounter] = {
            track_id: AtomicCounter(0)
            for track_id in self.track_limits.keys()
        }
        self._lock = threading.Lock()

    def acquire(self, track_id: str) -> bool:
        """
        尝试获取并发许可

        Args:
            track_id: 轨道ID

        Returns:
            bool: 是否成功获取
        """
        with self._lock:
            # 检查全局限制
            if self.global_counter.get() >= self.global_limit:
                return False

            # 检查轨道限制
            if track_id in self.track_limits:
                if track_id not in self.track_counters:
                    self.track_counters[track_id] = AtomicCounter(0)

                track_counter = self.track_counters[track_id]
                if track_counter.get() >= self.track_limits[track_id]:
                    return False

            # 获取许可
            self.global_counter.increment()
            if track_id in self.track_counters:
                self.track_counters[track_id].increment()

            return True

    def release(self, track_id: str) -> None:
        """
        释放并发许可

        Args:
            track_id: 轨道ID
        """
        with self._lock:
            self.global_counter.decrement()
            if track_id in self.track_counters:
                self.track_counters[track_id].decrement()

    def get_global_usage(self) -> int:
        """获取全局并发使用数"""
        return self.global_counter.get()

    def get_track_usage(self, track_id: str) -> int:
        """
        获取轨道并发使用数

        Args:
            track_id: 轨道ID

        Returns:
            int: 当前并发数
        """
        if track_id in self.track_counters:
            return self.track_counters[track_id].get()
        return 0

    def is_track_available(self, track_id: str) -> bool:
        """
        检查轨道是否可用

        Args:
            track_id: 轨道ID

        Returns:
            bool: 是否有可用并发槽位
        """
        if self.global_counter.get() >= self.global_limit:
            return False

        if track_id in self.track_limits:
            if track_id not in self.track_counters:
                return True
            return self.track_counters[track_id].get() < self.track_limits[track_id]

        return True
