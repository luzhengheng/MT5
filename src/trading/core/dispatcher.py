"""
交易调度器模块

协调多个交易轨道的运行，实现订单的路由和调度。
"""

import asyncio
from typing import Dict, Optional, Any
import logging

from src.trading.models import Order, OrderResult, AssetType, DispatcherConfig
from src.trading.utils import MetricsCollector
from .track import TradeTrack
from .limiter import ConcurrencyLimiter

logger = logging.getLogger(__name__)


class TrackDispatcher:
    """
    交易轨道调度器

    管理多个独立的交易轨道，根据订单的资产类型将其路由到相应的轨道。
    """

    def __init__(self, config: DispatcherConfig = None):
        """
        初始化调度器

        Args:
            config: 调度器配置
        """
        self.config = config or DispatcherConfig()

        # 全局并发限制
        self.global_limiter = ConcurrencyLimiter(
            global_limit=self.config.global_max_concurrent,
            track_limits={
                asset_type: track_config.max_concurrent
                for asset_type, track_config in self.config.track_configs.items()
            }
        )

        # 初始化各轨道
        self.tracks: Dict[AssetType, TradeTrack] = {}
        for asset_type, track_config in self.config.track_configs.items():
            self.tracks[asset_type] = TradeTrack(track_config, self.global_limiter)

        # 全局指标收集
        self.metrics = MetricsCollector()

        logger.info(
            f"TrackDispatcher initialized with {len(self.tracks)} tracks. "
            f"Global limit: {self.config.global_max_concurrent}"
        )

    async def dispatch(self, order: Order) -> OrderResult:
        """
        分发订单到相应的轨道

        Args:
            order: 订单对象

        Returns:
            OrderResult: 订单处理结果
        """
        # 检查资产类型是否支持
        if order.asset_type not in self.tracks:
            logger.error(f"Unsupported asset type: {order.asset_type}")
            return OrderResult(
                order_id=order.order_id,
                success=False,
                status=order.status,
                message=f"Unsupported asset type: {order.asset_type}",
                error_code="UNSUPPORTED_ASSET"
            )

        # 获取对应的轨道
        track = self.tracks[order.asset_type]

        # 检查全局并发限制
        if not self.global_limiter.is_track_available(track.track_id):
            logger.warning(
                f"Global concurrency limit exceeded for {track.track_id}"
            )
            self.metrics.record_order_rejected(track.track_id)
            return OrderResult(
                order_id=order.order_id,
                success=False,
                status=order.status,
                message="System concurrency limit exceeded",
                error_code="SYSTEM_LIMIT",
                track_id=track.track_id
            )

        # 提交订单到轨道
        result = await track.submit_order(order)

        # 记录指标
        self.metrics.record_order_submitted()
        if result.success:
            self.metrics.record_order_success(result.execution_time_ms, result.track_id)
        else:
            self.metrics.record_order_failure(result.track_id, result.error_code)

        return result

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态

        Returns:
            Dict: 包含所有轨道状态的信息
        """
        status = {
            'timestamp': asyncio.get_event_loop().time(),
            'global_concurrency': {
                'current': self.global_limiter.get_global_usage(),
                'limit': self.config.global_max_concurrent
            },
            'tracks': {}
        }

        for asset_type, track in self.tracks.items():
            status['tracks'][asset_type.value] = {
                'track_id': track.get_track_id(),
                'active_orders': track.get_active_count(),
                'max_concurrent': track.config.max_concurrent,
                'concurrency_usage': self.global_limiter.get_track_usage(track.track_id)
            }

        return status

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        获取系统指标摘要

        Returns:
            Dict: 指标摘要信息
        """
        return self.metrics.get_summary()

    def get_track_metrics(self, asset_type: AssetType) -> Dict[str, Any]:
        """
        获取特定轨道的指标

        Args:
            asset_type: 资产类型

        Returns:
            Dict: 轨道指标信息
        """
        if asset_type not in self.tracks:
            return {}

        track = self.tracks[asset_type]
        return self.metrics.get_track_summary(track.track_id)

    def shutdown_all(self) -> None:
        """关闭所有轨道"""
        logger.info("Shutting down all tracks...")
        for asset_type, track in self.tracks.items():
            track.shutdown()
            logger.info(f"Track {track.track_id} shut down")
