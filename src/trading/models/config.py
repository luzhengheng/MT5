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
