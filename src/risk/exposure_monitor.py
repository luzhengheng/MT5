"""
Exposure Monitor - L3 Risk Protection
RFC-135: Dynamic Risk Management System

监控敞口和持仓集中度，防止过度集中
Protocol v4.4 compliant
"""

import threading
from decimal import Decimal
from typing import Dict, Any
import logging

from .enums import RiskLevel, RiskAction
from .models import RiskContext, RiskDecision
from .config import ExposureConfig

logger = logging.getLogger(__name__)


class ExposureMonitor:
    """
    敞口监控器

    监控系统和单品种的敞口，防止过度集中和杠杆风险
    """

    def __init__(self, config: ExposureConfig):
        """
        初始化敞口监控器

        Args:
            config: 敞口监控配置
        """
        self.config = config
        self._lock = threading.RLock()

    def check(self, context: RiskContext) -> RiskDecision:
        """
        检查敞口是否超出限制

        Args:
            context: 风险检查上下文

        Returns:
            RiskDecision: 风险决策
        """
        with self._lock:
            # 计算新订单后的敞口
            new_exposure = self._calculate_exposure_after_order(context)

            # 计算敞口占权益的百分比
            exposure_pct = (new_exposure / context.account_equity * 100) if context.account_equity > 0 else Decimal("0")

            # 检查单品种敞口
            single_exposure_pct = (context.order_value / context.account_equity * 100) if context.account_equity > 0 else Decimal("0")

            # 检查是否超过单品种限制
            if single_exposure_pct > self.config.max_single_position:
                return RiskDecision(
                    action=RiskAction.REJECT,
                    level=RiskLevel.CRITICAL,
                    reason=f"Single position exposure {single_exposure_pct:.2f}% exceeds limit {self.config.max_single_position}%",
                    details={
                        "symbol": context.symbol,
                        "single_exposure_pct": float(single_exposure_pct),
                        "max_limit": float(self.config.max_single_position),
                        "order_value": str(context.order_value),
                        "account_equity": str(context.account_equity)
                    }
                )

            # 检查总敞口
            if exposure_pct > self.config.max_total_exposure:
                return RiskDecision(
                    action=RiskAction.REJECT,
                    level=RiskLevel.CRITICAL,
                    reason=f"Total exposure {exposure_pct:.2f}% exceeds limit {self.config.max_total_exposure}%",
                    details={
                        "total_exposure_pct": float(exposure_pct),
                        "max_limit": float(self.config.max_total_exposure),
                        "new_exposure": str(new_exposure),
                        "account_equity": str(context.account_equity)
                    }
                )

            # 检查敞口警告阈值
            warning_level = self.config.max_total_exposure * self.config.warning_threshold / 100
            if exposure_pct > warning_level:
                return RiskDecision(
                    action=RiskAction.ALLOW,
                    level=RiskLevel.WARNING,
                    reason=f"Total exposure {exposure_pct:.2f}% is approaching limit",
                    details={
                        "total_exposure_pct": float(exposure_pct),
                        "warning_level": float(warning_level)
                    }
                )

            # 检查持仓数量限制
            position_count = len(context.positions)
            if position_count >= self.config.max_positions and context.is_opening:
                return RiskDecision(
                    action=RiskAction.REJECT,
                    level=RiskLevel.CRITICAL,
                    reason=f"Position count {position_count} exceeds limit {self.config.max_positions}",
                    details={
                        "position_count": position_count,
                        "max_positions": self.config.max_positions
                    }
                )

            # 正常状态
            return RiskDecision(
                action=RiskAction.ALLOW,
                level=RiskLevel.NORMAL,
                reason="Exposure within limits",
                details={
                    "total_exposure_pct": float(exposure_pct),
                    "single_exposure_pct": float(single_exposure_pct),
                    "position_count": len(context.positions)
                }
            )

    def _calculate_exposure_after_order(self, context: RiskContext) -> Decimal:
        """
        计算下单后的总敞口
        """
        total_exposure = Decimal("0")

        # 累加所有现有持仓的市值
        for symbol, position in context.positions.items():
            total_exposure += position.market_value

        # 加上新订单的价值
        total_exposure += context.order_value

        return total_exposure

    def get_status(self) -> Dict[str, Any]:
        """
        获取监控状态
        """
        return {
            "max_total_exposure": float(self.config.max_total_exposure),
            "max_single_position": float(self.config.max_single_position),
            "max_positions": self.config.max_positions,
            "warning_threshold": float(self.config.warning_threshold)
        }
