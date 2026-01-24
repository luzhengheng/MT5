"""
Risk Management Configuration
RFC-135: Dynamic Risk Management System

定义风险管理系统的配置结构和默认值
Protocol v4.4 compliant
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any
from pathlib import Path
import yaml

from .enums import TrackType


@dataclass
class CircuitBreakerConfig:
    """
    熔断器配置

    控制单品种熔断器的行为参数
    """
    # 触发条件
    max_consecutive_losses: int = 3              # 连续亏损次数阈值
    max_loss_amount: Decimal = Decimal("1000")   # 累计亏损金额阈值
    max_loss_percentage: Decimal = Decimal("2")  # 单品种最大亏损百分比

    # 恢复参数
    cooldown_seconds: int = 300                  # 熔断冷却时间（秒）
    half_open_max_trades: int = 2                # 半开状态最大交易次数
    half_open_success_threshold: int = 2         # 半开状态成功阈值

    # 升级机制
    max_trips_per_day: int = 3                   # 每日最大熔断次数
    escalation_multiplier: float = 2.0           # 冷却时间升级倍数


@dataclass
class DrawdownConfig:
    """
    回撤限制配置

    控制每日回撤限制的参数
    """
    # 回撤阈值（百分比）
    warning_threshold: Decimal = Decimal("3")    # 警告阈值
    critical_threshold: Decimal = Decimal("5")   # 临界阈值
    halt_threshold: Decimal = Decimal("7")       # 停止阈值

    # 绝对金额限制
    max_daily_loss: Decimal = Decimal("5000")    # 最大每日亏损金额

    # 恢复条件
    recovery_threshold: Decimal = Decimal("2")   # 恢复阈值（回撤降至此值以下）

    # 行为控制
    reduce_only_on_critical: bool = True         # 临界状态时仅允许减仓
    halt_on_threshold: bool = True               # 达到停止阈值时完全停止


@dataclass
class ExposureConfig:
    """
    敞口监控配置

    控制敞口限制的参数
    """
    # 账户级别限制（占权益百分比）
    max_total_exposure: Decimal = Decimal("100")      # 最大总敞口
    max_single_position: Decimal = Decimal("20")      # 单品种最大敞口
    max_correlated_exposure: Decimal = Decimal("40")  # 相关品种最大敞口

    # 持仓数量限制
    max_positions: int = 20                           # 最大持仓数量
    max_positions_per_symbol: int = 1                 # 单品种最大持仓数

    # 集中度限制
    max_sector_exposure: Decimal = Decimal("30")      # 单行业最大敞口

    # 警告阈值（占限制的百分比）
    warning_threshold: Decimal = Decimal("80")        # 警告阈值


@dataclass
class TrackLimits:
    """
    轨道特定限制

    每个轨道的风险限制参数
    """
    max_exposure_pct: Decimal          # 最大敞口（占账户权益百分比）
    max_positions: int                  # 最大持仓数
    max_single_position_pct: Decimal   # 单品种最大敞口百分比
    max_daily_loss_pct: Decimal        # 最大每日亏损百分比

    # 熔断器参数覆盖
    circuit_breaker_override: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskConfig:
    """
    风险管理总配置

    汇总所有风险管理配置
    """
    # 组件配置
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    drawdown: DrawdownConfig = field(default_factory=DrawdownConfig)
    exposure: ExposureConfig = field(default_factory=ExposureConfig)

    # 轨道特定限制
    track_limits: Dict[TrackType, TrackLimits] = field(default_factory=dict)

    # 全局开关
    enabled: bool = True
    fail_safe_mode: bool = True  # Fail-Safe模式：故障时拒绝所有订单

    def __post_init__(self):
        """初始化默认轨道限制"""
        if not self.track_limits:
            # EUR轨道 (保守)
            self.track_limits[TrackType.EUR] = TrackLimits(
                max_exposure_pct=Decimal("30"),
                max_positions=5,
                max_single_position_pct=Decimal("10"),
                max_daily_loss_pct=Decimal("2")
            )

            # BTC轨道 (中等)
            self.track_limits[TrackType.BTC] = TrackLimits(
                max_exposure_pct=Decimal("40"),
                max_positions=7,
                max_single_position_pct=Decimal("15"),
                max_daily_loss_pct=Decimal("3")
            )

            # GBP轨道 (激进)
            self.track_limits[TrackType.GBP] = TrackLimits(
                max_exposure_pct=Decimal("30"),
                max_positions=5,
                max_single_position_pct=Decimal("10"),
                max_daily_loss_pct=Decimal("2")
            )

    @classmethod
    def from_yaml(cls, config_path: Path) -> "RiskConfig":
        """
        从YAML文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            RiskConfig: 配置实例
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        risk_data = data.get('risk', {})

        # 解析CircuitBreakerConfig
        cb_data = risk_data.get('circuit_breaker', {})
        circuit_breaker = CircuitBreakerConfig(
            max_consecutive_losses=cb_data.get('max_consecutive_losses', 3),
            max_loss_amount=Decimal(str(cb_data.get('max_loss_amount', 1000))),
            max_loss_percentage=Decimal(str(cb_data.get('max_loss_percentage', 2))),
            cooldown_seconds=cb_data.get('cooldown_seconds', 300),
            half_open_max_trades=cb_data.get('half_open_max_trades', 2),
            half_open_success_threshold=cb_data.get('half_open_success_threshold', 2),
            max_trips_per_day=cb_data.get('max_trips_per_day', 3),
            escalation_multiplier=cb_data.get('escalation_multiplier', 2.0)
        )

        # 解析DrawdownConfig
        dd_data = risk_data.get('drawdown', {})
        drawdown = DrawdownConfig(
            warning_threshold=Decimal(str(dd_data.get('warning_threshold', 3))),
            critical_threshold=Decimal(str(dd_data.get('critical_threshold', 5))),
            halt_threshold=Decimal(str(dd_data.get('halt_threshold', 7))),
            max_daily_loss=Decimal(str(dd_data.get('max_daily_loss', 5000))),
            recovery_threshold=Decimal(str(dd_data.get('recovery_threshold', 2))),
            reduce_only_on_critical=dd_data.get('reduce_only_on_critical', True),
            halt_on_threshold=dd_data.get('halt_on_threshold', True)
        )

        # 解析ExposureConfig
        exp_data = risk_data.get('exposure', {})
        exposure = ExposureConfig(
            max_total_exposure=Decimal(str(exp_data.get('max_total_exposure', 100))),
            max_single_position=Decimal(str(exp_data.get('max_single_position', 20))),
            max_correlated_exposure=Decimal(str(exp_data.get('max_correlated_exposure', 40))),
            max_positions=exp_data.get('max_positions', 20),
            max_positions_per_symbol=exp_data.get('max_positions_per_symbol', 1),
            max_sector_exposure=Decimal(str(exp_data.get('max_sector_exposure', 30))),
            warning_threshold=Decimal(str(exp_data.get('warning_threshold', 80)))
        )

        return cls(
            circuit_breaker=circuit_breaker,
            drawdown=drawdown,
            exposure=exposure,
            enabled=risk_data.get('enabled', True),
            fail_safe_mode=risk_data.get('fail_safe_mode', True)
        )
