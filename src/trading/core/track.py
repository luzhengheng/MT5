"""
交易轨道模块

每个轨道代表一个独立的交易资产类型（EUR、BTC、GBP）的处理通道。
"""

import asyncio
import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from src.trading.models import Order, OrderResult, OrderStatus, TrackConfig
from src.trading.utils import AtomicCounter, MetricsCollector
from .limiter import RateLimiter, ConcurrencyLimiter


class TradeTrack:
    """
    单个交易轨道

    每个轨道独立处理特定资产类型的订单。
    实现了资源隔离和并发控制。
    """

    def __init__(self, config: TrackConfig, global_limiter: ConcurrencyLimiter = None):
        """
        初始化交易轨道

        Args:
            config: 轨道配置
            global_limiter: 全局并发限制器
        """
        self.config = config
        self.track_id = config.track_id
        self.asset_type = config.asset_type

        # 执行线程池
        self.executor_pool = ThreadPoolExecutor(
            max_workers=config.executor_pool_size,
            thread_name_prefix=f"track-{self.track_id}"
        )

        # 速率限制器
        self.rate_limiter = RateLimiter(config.rate_limit_per_second)

        # 本地并发限制
        self.local_semaphore = asyncio.Semaphore(config.max_concurrent)

        # 全局并发限制
        self.global_limiter = global_limiter

        # 订单队列
        self.order_queue: asyncio.Queue = None

        # 活跃订单计数
        self.active_orders = AtomicCounter(0)

        # 指标收集
        self.metrics = MetricsCollector()

    async def submit_order(self, order: Order) -> OrderResult:
        """
        提交订单到轨道

        Args:
            order: 订单对象

        Returns:
            OrderResult: 订单处理结果
        """
        start_time = time.time()
        self.metrics.record_order_submitted()

        try:
            # 检查资产类型匹配
            if order.asset_type != self.asset_type:
                error_msg = f"Asset mismatch: order for {order.asset_type} sent to {self.asset_type} track"
                self.metrics.record_order_rejected(self.track_id)
                return OrderResult(
                    order_id=order.order_id,
                    success=False,
                    status=OrderStatus.REJECTED,
                    message=error_msg,
                    track_id=self.track_id,
                    error_code="ASSET_MISMATCH"
                )

            # 尝试获取本地并发许可
            try:
                async with asyncio.timeout(self.config.timeout_seconds):
                    async with self.local_semaphore:
                        # 尝试获取全局并发许可
                        if self.global_limiter:
                            if not self.global_limiter.acquire(self.track_id):
                                error_msg = "Global concurrency limit exceeded"
                                self.metrics.record_order_rejected(self.track_id)
                                return OrderResult(
                                    order_id=order.order_id,
                                    success=False,
                                    status=OrderStatus.REJECTED,
                                    message=error_msg,
                                    track_id=self.track_id,
                                    error_code="GLOBAL_LIMIT"
                                )

                        try:
                            # 更新订单状态为已入队
                            order.update_status(OrderStatus.QUEUED)

                            # 应用速率限制
                            self.rate_limiter.wait_and_acquire()

                            # 更新订单状态为处理中
                            order.update_status(OrderStatus.PROCESSING)
                            self.active_orders.increment()

                            # 执行订单
                            result = await self._process_order(order)

                            execution_time = (time.time() - start_time) * 1000
                            result.execution_time_ms = execution_time
                            result.track_id = self.track_id

                            if result.success:
                                self.metrics.record_order_success(execution_time, self.track_id)
                            else:
                                self.metrics.record_order_failure(self.track_id, result.error_code)

                            return result

                        finally:
                            self.active_orders.decrement()
                            if self.global_limiter:
                                self.global_limiter.release(self.track_id)

            except asyncio.TimeoutError:
                error_msg = f"Order processing timeout after {self.config.timeout_seconds}s"
                self.metrics.record_order_failure(self.track_id, "TIMEOUT")
                return OrderResult(
                    order_id=order.order_id,
                    success=False,
                    status=OrderStatus.FAILED,
                    message=error_msg,
                    track_id=self.track_id,
                    error_code="TIMEOUT"
                )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.metrics.record_order_failure(self.track_id, "INTERNAL_ERROR")
            return OrderResult(
                order_id=order.order_id,
                success=False,
                status=OrderStatus.FAILED,
                message=error_msg,
                track_id=self.track_id,
                error_code="INTERNAL_ERROR"
            )

    async def _process_order(self, order: Order) -> OrderResult:
        """
        实际处理订单

        Args:
            order: 订单对象

        Returns:
            OrderResult: 处理结果
        """
        # 这里是实际的交易执行逻辑
        # 在实际系统中，这会调用MT5 API或其他执易引擎

        try:
            # 模拟订单执行
            order.update_status(OrderStatus.EXECUTED)
            return OrderResult(
                order_id=order.order_id,
                success=True,
                status=OrderStatus.EXECUTED,
                message="Order executed successfully",
                track_id=self.track_id
            )
        except Exception as e:
            order.update_status(OrderStatus.FAILED)
            return OrderResult(
                order_id=order.order_id,
                success=False,
                status=OrderStatus.FAILED,
                message=str(e),
                track_id=self.track_id,
                error_code="EXECUTION_ERROR"
            )

    def get_active_count(self) -> int:
        """获取当前活跃订单数"""
        return self.active_orders.get()

    def get_track_id(self) -> str:
        """获取轨道ID"""
        return self.track_id

    def shutdown(self) -> None:
        """关闭轨道"""
        self.executor_pool.shutdown(wait=True)
