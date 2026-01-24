"""
Risk Manager - Central Risk Management Orchestrator
RFC-135: Dynamic Risk Management System

整合 L1/L2/L3 三层风险检查，提供统一的风险管理接口
Protocol v4.4 compliant
"""

import threading
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Callable, Optional, Any
import logging

from .enums import RiskLevel, TrackType, RiskAction
from .models import (
    RiskContext, RiskDecision, RiskEvent,
    SymbolRiskState, AccountRiskState, TrackRiskState
)
from .config import RiskConfig
from .circuit_breaker import CircuitBreaker
from .drawdown_monitor import DrawdownMonitor
from .exposure_monitor import ExposureMonitor

logger = logging.getLogger(__name__)


class RiskManager:
    """
    风险管理系统主类

    整合三层风险保护：
    - L1: Per-Symbol Circuit Breakers (单品种熔断)
    - L2: Daily Drawdown Limits (每日回撤)
    - L3: Exposure Monitoring (敞口监控)

    特性：
    - 线程安全（通过 RLock）
    - Fail-Safe 模式（故障时默认拒绝）
    - 事件驱动（风险事件通知）
    - 配置热更新（支持运行时调整）
    """

    def __init__(self, config: RiskConfig):
        """
        初始化风险管理系统

        Args:
            config: 风险管理配置
        """
        self.config = config
        self._lock = threading.RLock()

        # L1: 单品种熔断器字典
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # L2: 每日回撤监控
        self.drawdown_monitor = DrawdownMonitor(config.drawdown)

        # L3: 敞口监控
        self.exposure_monitor = ExposureMonitor(config.exposure)

        # 状态追踪
        self.symbol_states: Dict[str, SymbolRiskState] = {}
        self.account_state = AccountRiskState()
        self.track_states: Dict[TrackType, TrackRiskState] = {}

        # 事件处理
        self.event_handlers: List[Callable[[RiskEvent], None]] = []

        # 初始化三个轨道状态
        for track_type in TrackType:
            track_config = config.track_limits.get(track_type)
            if track_config:
                self.track_states[track_type] = TrackRiskState(
                    track=track_type,
                    max_exposure=Decimal(str(track_config.max_exposure_pct)),
                    max_positions=track_config.max_positions
                )

        logger.info("RiskManager initialized with config: %s", config.enabled)

    def register_event_handler(self, handler: Callable[[RiskEvent], None]) -> None:
        """
        注册风险事件处理器

        Args:
            handler: 事件处理回调函数
        """
        with self._lock:
            self.event_handlers.append(handler)
            logger.info("Event handler registered: %s", handler.__name__)

    def _emit_event(self, event: RiskEvent) -> None:
        """
        发送风险事件到所有已注册的处理器

        Args:
            event: 风险事件
        """
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Error in event handler %s: %s", handler.__name__, e)

    def validate_order(self, context: RiskContext) -> RiskDecision:
        """
        验证订单的风险合规性

        执行三层风险检查（顺序执行）：
        1. L1 Circuit Breaker: 单品种熔断检查
        2. L2 Drawdown Monitor: 每日回撤检查
        3. L3 Exposure Monitor: 敞口限制检查

        任何一层拒绝则订单被拒绝。

        Args:
            context: 风险检查上下文

        Returns:
            风险决策结果

        Raises:
            Exception: 如果风险系统出故障且 fail_safe_mode 启用
        """
        if not self.config.enabled:
            return RiskDecision(
                action=RiskAction.ALLOW,
                level=RiskLevel.NORMAL,
                reason="Risk management system disabled"
            )

        with self._lock:
            try:
                # 初始化或获取品种熔断器
                if context.symbol not in self.circuit_breakers:
                    self.circuit_breakers[context.symbol] = CircuitBreaker(
                        context.symbol,
                        self.config.circuit_breaker
                    )

                # L1: Circuit Breaker Check
                cb_decision = self.circuit_breakers[context.symbol].check(context)
                if not cb_decision.is_allowed:
                    logger.warning(
                        "Order rejected by circuit breaker: %s (%s)",
                        context.symbol, cb_decision.reason
                    )
                    self._emit_event(RiskEvent(
                        event_type=RiskEvent.CIRCUIT_BREAKER_TRIGGERED,
                        severity=cb_decision.level,
                        message=f"Circuit breaker triggered for {context.symbol}",
                        data={"symbol": context.symbol, "reason": cb_decision.reason}
                    ))
                    return cb_decision

                # L2: Drawdown Monitor Check
                dd_decision = self.drawdown_monitor.check(context)
                if not dd_decision.is_allowed:
                    logger.warning(
                        "Order rejected by drawdown monitor: %s (%s)",
                        context.symbol, dd_decision.reason
                    )
                    self._emit_event(RiskEvent(
                        event_type=RiskEvent.DRAWDOWN_LIMIT_HIT,
                        severity=dd_decision.level,
                        message=f"Drawdown limit hit",
                        data={"drawdown": str(self.drawdown_monitor.get_status().get("current_drawdown"))}
                    ))
                    return dd_decision

                # L3: Exposure Monitor Check
                exp_decision = self.exposure_monitor.check(context)
                if not exp_decision.is_allowed:
                    logger.warning(
                        "Order rejected by exposure monitor: %s (%s)",
                        context.symbol, exp_decision.reason
                    )
                    self._emit_event(RiskEvent(
                        event_type=RiskEvent.EXPOSURE_LIMIT_HIT,
                        severity=exp_decision.level,
                        message=f"Exposure limit exceeded",
                        data={"exposure": str(self.exposure_monitor.get_status().get("current_exposure"))}
                    ))
                    return exp_decision

                # All checks passed
                return RiskDecision(
                    action=RiskAction.ALLOW,
                    level=RiskLevel.NORMAL,
                    reason="All risk checks passed"
                )

            except Exception as e:
                logger.error("Error in validate_order: %s", e)
                if self.config.fail_safe_mode:
                    logger.error("Fail-safe mode enabled, rejecting order")
                    return RiskDecision(
                        action=RiskAction.REJECT,
                        level=RiskLevel.HALT,
                        reason=f"Risk system error: {str(e)}"
                    )
                raise

    def record_trade(self, context: RiskContext, is_successful: bool, pnl: Decimal = Decimal("0")) -> None:
        """
        记录交易结果以更新风险状态

        Args:
            context: 风险上下文
            is_successful: 交易是否成功
            pnl: 盈亏金额
        """
        with self._lock:
            try:
                # 更新熔断器状态
                if context.symbol in self.circuit_breakers:
                    self.circuit_breakers[context.symbol].record_trade_result(pnl, is_successful)

                # 更新回撤监控
                self.drawdown_monitor.update_pnl(pnl)

                # 更新账户状态
                if is_successful and pnl != Decimal("0"):
                    if pnl > 0:
                        self.account_state.daily_win_count += 1
                    else:
                        self.account_state.daily_loss_count += 1

                logger.info("Trade recorded: symbol=%s, success=%s, pnl=%s", context.symbol, is_successful, pnl)

            except Exception as e:
                logger.error("Error in record_trade: %s", e)

    def update_exposure(self, context: RiskContext) -> None:
        """
        更新敞口状态

        Args:
            context: 风险上下文
        """
        with self._lock:
            try:
                self.exposure_monitor.update_positions(context.positions)
            except Exception as e:
                logger.error("Error in update_exposure: %s", e)

    def reset_daily(self, starting_equity: Decimal) -> None:
        """
        每日重置风险状态

        应在交易日开始时调用

        Args:
            starting_equity: 当日起始权益
        """
        with self._lock:
            try:
                # 重置回撤监控
                self.drawdown_monitor.reset_daily(starting_equity)

                # 重置账户状态
                self.account_state = AccountRiskState(
                    daily_starting_equity=starting_equity,
                    daily_high_equity=starting_equity
                )

                # 重置熔断器为半开状态（可以尝试交易）
                for cb in self.circuit_breakers.values():
                    cb.reset_daily()

                logger.info("Daily reset completed for equity: %s", starting_equity)
                self._emit_event(RiskEvent(
                    event_type=RiskEvent.DAILY_RESET,
                    severity=RiskLevel.NORMAL,
                    message="Daily risk reset completed",
                    data={"starting_equity": str(starting_equity)}
                ))

            except Exception as e:
                logger.error("Error in reset_daily: %s", e)

    def get_risk_status(self) -> Dict[str, Any]:
        """
        获取完整的风险状态摘要

        Returns:
            包含所有风险指标的字典
        """
        with self._lock:
            try:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "account_state": {
                        "daily_pnl": str(self.account_state.daily_total_pnl),
                        "drawdown_pct": str(self.account_state.drawdown_percentage),
                        "risk_level": self.account_state.risk_level.name,
                        "trade_count": self.account_state.daily_trade_count
                    },
                    "circuit_breakers": {
                        symbol: {
                            "state": state.circuit_state.name,
                            "consecutive_losses": state.consecutive_losses,
                            "loss_amount": str(state.loss_amount)
                        }
                        for symbol, state in self.symbol_states.items()
                    },
                    "drawdown_monitor": self.drawdown_monitor.get_status(),
                    "exposure_monitor": self.exposure_monitor.get_status(),
                    "track_states": {
                        track.name: {
                            "total_exposure": str(track_state.total_exposure),
                            "position_count": track_state.position_count,
                            "risk_level": track_state.risk_level.name
                        }
                        for track, track_state in self.track_states.items()
                    }
                }
            except Exception as e:
                logger.error("Error in get_risk_status: %s", e)
                return {"error": str(e)}

    def get_track_state(self, track: TrackType) -> Optional[TrackRiskState]:
        """
        获取特定轨道的风险状态

        Args:
            track: 轨道类型

        Returns:
            轨道风险状态，如果不存在则返回 None
        """
        with self._lock:
            return self.track_states.get(track)
