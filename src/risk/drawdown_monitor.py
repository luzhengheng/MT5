"""
Drawdown Monitor - L2 Risk Protection
RFC-135: Dynamic Risk Management System

监控每日回撤，防止账户损失过大
Protocol v4.4 compliant
"""

import threading
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

from .enums import RiskLevel, RiskAction
from .models import RiskContext, RiskDecision, AccountRiskState
from .config import DrawdownConfig

logger = logging.getLogger(__name__)


class DrawdownMonitor:
    """
    回撤监控器

    监控账户的每日回撤情况，在达到不同阈值时采取相应措施
    """

    def __init__(self, config: DrawdownConfig):
        """
        初始化回撤监控器

        Args:
            config: 回撤监控配置
        """
        self.config = config
        self.state = AccountRiskState()
        self._lock = threading.RLock()

    def check(self, context: RiskContext) -> RiskDecision:
        """
        检查回撤是否超出限制

        Args:
            context: 风险检查上下文

        Returns:
            RiskDecision: 风险决策
        """
        with self._lock:
            # 更新当前权益和回撤
            current_equity = context.account_equity
            self._update_drawdown(current_equity, context.daily_pnl)

            # 计算当前回撤百分比
            drawdown_pct = self.state.drawdown_percentage

            # 检查停止阈值
            if drawdown_pct >= self.config.halt_threshold:
                if self.config.halt_on_threshold:
                    return RiskDecision(
                        action=RiskAction.FORCE_CLOSE,
                        level=RiskLevel.HALT,
                        reason=f"Daily drawdown {drawdown_pct:.2f}% exceeds HALT threshold {self.config.halt_threshold}%",
                        details={
                            "drawdown_percentage": float(drawdown_pct),
                            "threshold": float(self.config.halt_threshold),
                            "daily_pnl": str(context.daily_pnl),
                            "daily_loss_limit": str(self.config.max_daily_loss)
                        }
                    )

            # 检查临界阈值
            if drawdown_pct >= self.config.critical_threshold:
                if self.config.reduce_only_on_critical and context.is_opening:
                    return RiskDecision(
                        action=RiskAction.REDUCE_ONLY,
                        level=RiskLevel.CRITICAL,
                        reason=f"Daily drawdown {drawdown_pct:.2f}% exceeds CRITICAL threshold {self.config.critical_threshold}%. Reduce only.",
                        details={
                            "drawdown_percentage": float(drawdown_pct),
                            "threshold": float(self.config.critical_threshold)
                        }
                    )

            # 检查警告阈值
            if drawdown_pct >= self.config.warning_threshold:
                return RiskDecision(
                    action=RiskAction.ALLOW,
                    level=RiskLevel.WARNING,
                    reason=f"Daily drawdown {drawdown_pct:.2f}% exceeds WARNING threshold {self.config.warning_threshold}%",
                    details={
                        "drawdown_percentage": float(drawdown_pct),
                        "threshold": float(self.config.warning_threshold)
                    }
                )

            # 正常状态
            return RiskDecision(
                action=RiskAction.ALLOW,
                level=RiskLevel.NORMAL,
                reason="Drawdown within limits",
                details={
                    "drawdown_percentage": float(drawdown_pct),
                    "daily_pnl": str(context.daily_pnl)
                }
            )

    def _update_drawdown(self, current_equity: Decimal, daily_pnl: Decimal) -> None:
        """
        更新回撤计算
        """
        # 更新每日最高权益
        if current_equity > self.state.daily_high_equity:
            self.state.daily_high_equity = current_equity

        # 计算当前回撤
        self.state.current_drawdown = self.state.daily_high_equity - current_equity

        # 更新最大回撤
        if self.state.current_drawdown > self.state.max_drawdown:
            self.state.max_drawdown = self.state.current_drawdown

    def update_daily_pnl(self, realized_pnl: Decimal, unrealized_pnl: Decimal) -> None:
        """
        更新每日盈亏统计
        """
        with self._lock:
            self.state.daily_realized_pnl = realized_pnl
            self.state.daily_unrealized_pnl = unrealized_pnl
            self.state.last_update = datetime.now()

    def reset_daily(self, starting_equity: Decimal) -> None:
        """
        重置每日统计
        """
        with self._lock:
            self.state.daily_starting_equity = starting_equity
            self.state.daily_high_equity = starting_equity
            self.state.daily_realized_pnl = Decimal("0")
            self.state.daily_unrealized_pnl = Decimal("0")
            self.state.current_drawdown = Decimal("0")
            self.state.max_drawdown = Decimal("0")
            self.state.daily_trade_count = 0
            self.state.daily_win_count = 0
            self.state.daily_loss_count = 0
            self.state.risk_level = RiskLevel.NORMAL
            logger.info("[DrawdownMonitor] Daily reset completed")

    def get_status(self) -> Dict[str, Any]:
        """
        获取监控状态
        """
        with self._lock:
            return {
                "daily_starting_equity": str(self.state.daily_starting_equity),
                "daily_high_equity": str(self.state.daily_high_equity),
                "daily_realized_pnl": str(self.state.daily_realized_pnl),
                "daily_unrealized_pnl": str(self.state.daily_unrealized_pnl),
                "daily_total_pnl": str(self.state.daily_total_pnl),
                "current_drawdown": str(self.state.current_drawdown),
                "max_drawdown": str(self.state.max_drawdown),
                "drawdown_percentage": float(self.state.drawdown_percentage),
                "risk_level": self.state.risk_level.name,
                "daily_trade_count": self.state.daily_trade_count,
                "daily_win_count": self.state.daily_win_count,
                "daily_loss_count": self.state.daily_loss_count
            }
