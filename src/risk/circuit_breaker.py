"""
Circuit Breaker - L1 Risk Protection
RFC-135: Dynamic Risk Management System

实现单品种熔断机制，防止单个品种造成过度亏损
Protocol v4.4 compliant
"""

import threading
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

from .enums import RiskLevel, CircuitState, RiskAction
from .models import RiskContext, RiskDecision, SymbolRiskState, RiskEvent
from .config import CircuitBreakerConfig

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    单品种熔断器

    使用标准熔断器模式（CLOSED → OPEN → HALF_OPEN → CLOSED）
    防止单个品种的过度亏损
    """

    def __init__(self, symbol: str, config: CircuitBreakerConfig):
        """
        初始化熔断器

        Args:
            symbol: 品种代码
            config: 熔断器配置
        """
        self.symbol = symbol
        self.config = config
        self.state = SymbolRiskState(symbol=symbol)
        self._lock = threading.RLock()

    def check(self, context: RiskContext) -> RiskDecision:
        """
        检查是否触发熔断

        Args:
            context: 风险检查上下文

        Returns:
            RiskDecision: 风险决策
        """
        with self._lock:
            # 如果是半开状态且需要恢复检查
            if self.state.circuit_state == CircuitState.HALF_OPEN:
                return self._check_half_open(context)

            # 如果是断开状态
            if self.state.circuit_state == CircuitState.OPEN:
                # 检查冷却时间是否已过
                if self._is_cooldown_expired():
                    self._transition_to_half_open()
                    logger.info(f"[CircuitBreaker] {self.symbol}: Transitioning to HALF_OPEN")
                else:
                    remaining = self._get_remaining_cooldown()
                    return RiskDecision(
                        action=RiskAction.REJECT,
                        level=RiskLevel.HALT,
                        reason=f"Circuit breaker OPEN for {self.symbol}. Cooldown expires in {remaining}s",
                        details={
                            "symbol": self.symbol,
                            "state": self.state.circuit_state.name,
                            "remaining_cooldown_seconds": remaining,
                            "trip_count": self.state.trip_count
                        }
                    )

            # 状态为CLOSED，执行正常检查
            return self._check_closed(context)

    def _check_closed(self, context: RiskContext) -> RiskDecision:
        """
        在CLOSED状态下执行检查
        """
        # 这里可以添加检查逻辑，如连续亏损次数、累计亏损等
        # 当前实现为基础版本，返回允许
        return RiskDecision(
            action=RiskAction.ALLOW,
            level=RiskLevel.NORMAL,
            reason=f"Circuit breaker OK for {self.symbol}",
            details={
                "symbol": self.symbol,
                "state": CircuitState.CLOSED.name
            }
        )

    def _check_half_open(self, context: RiskContext) -> RiskDecision:
        """
        在HALF_OPEN状态下执行检查
        """
        # 半开状态下限制交易次数
        if self.state.half_open_trades >= self.config.half_open_max_trades:
            return RiskDecision(
                action=RiskAction.REJECT,
                level=RiskLevel.CRITICAL,
                reason=f"Half-open trades limit exceeded for {self.symbol}",
                details={
                    "symbol": self.symbol,
                    "state": CircuitState.HALF_OPEN.name,
                    "half_open_trades": self.state.half_open_trades,
                    "max_half_open_trades": self.config.half_open_max_trades
                }
            )

        return RiskDecision(
            action=RiskAction.ALLOW,
            level=RiskLevel.WARNING,
            reason=f"Exploratory trade allowed in HALF_OPEN for {self.symbol}",
            details={
                "symbol": self.symbol,
                "state": CircuitState.HALF_OPEN.name,
                "half_open_trades": self.state.half_open_trades
            }
        )

    def record_trade_result(self, pnl: Decimal, is_success: bool) -> None:
        """
        记录交易结果

        Args:
            pnl: 损益
            is_success: 是否盈利
        """
        with self._lock:
            # 更新最后交易时间
            self.state.last_trade_time = datetime.now()

            # 更新损失统计
            if not is_success:
                self.state.consecutive_losses += 1
                self.state.loss_amount += abs(pnl)
            else:
                self.state.consecutive_losses = 0

            # 在半开状态下，记录交易
            if self.state.circuit_state == CircuitState.HALF_OPEN:
                self.state.half_open_trades += 1

                # 如果半开状态的交易都成功，则恢复到CLOSED
                if self.state.half_open_trades >= self.config.half_open_success_threshold and is_success:
                    self._transition_to_closed()
                    logger.info(f"[CircuitBreaker] {self.symbol}: Recovery successful, back to CLOSED")

            # 检查是否需要触发熔断
            if self._should_trip():
                self._trip()
                logger.warning(f"[CircuitBreaker] {self.symbol}: TRIPPED")

    def _should_trip(self) -> bool:
        """
        判断是否应该触发熔断
        """
        # 检查连续亏损次数
        if self.state.consecutive_losses >= self.config.max_consecutive_losses:
            return True

        # 检查累计亏损金额
        if self.state.loss_amount >= self.config.max_loss_amount:
            return True

        # 检查每日熔断次数上限
        if self.state.trip_count >= self.config.max_trips_per_day:
            return True

        return False

    def _trip(self) -> None:
        """
        触发熔断
        """
        self.state.circuit_state = CircuitState.OPEN
        self.state.open_time = datetime.now()
        self.state.trip_count += 1
        self.state.half_open_trades = 0

    def _transition_to_half_open(self) -> None:
        """
        转换到HALF_OPEN状态
        """
        self.state.circuit_state = CircuitState.HALF_OPEN
        self.state.half_open_trades = 0

    def _transition_to_closed(self) -> None:
        """
        转换到CLOSED状态
        """
        self.state.circuit_state = CircuitState.CLOSED
        self.state.open_time = None
        self.state.consecutive_losses = 0
        self.state.loss_amount = Decimal("0")
        self.state.half_open_trades = 0

    def _is_cooldown_expired(self) -> bool:
        """
        检查冷却时间是否已过期
        """
        if self.state.open_time is None:
            return True

        # 计算冷却时间（考虑升级）
        cooldown = self.config.cooldown_seconds * (
            self.config.escalation_multiplier ** (self.state.trip_count - 1)
        )
        elapsed = (datetime.now() - self.state.open_time).total_seconds()

        return elapsed >= cooldown

    def _get_remaining_cooldown(self) -> int:
        """
        获取剩余冷却时间（秒）
        """
        if self.state.open_time is None:
            return 0

        cooldown = self.config.cooldown_seconds * (
            self.config.escalation_multiplier ** (self.state.trip_count - 1)
        )
        elapsed = (datetime.now() - self.state.open_time).total_seconds()

        return max(0, int(cooldown - elapsed))

    def get_status(self) -> Dict[str, Any]:
        """
        获取熔断器状态
        """
        with self._lock:
            return {
                "symbol": self.symbol,
                "state": self.state.circuit_state.name,
                "consecutive_losses": self.state.consecutive_losses,
                "loss_amount": str(self.state.loss_amount),
                "trip_count": self.state.trip_count,
                "remaining_cooldown_seconds": self._get_remaining_cooldown() if self.state.circuit_state == CircuitState.OPEN else 0,
                "last_trade_time": self.state.last_trade_time.isoformat() if self.state.last_trade_time else None
            }

    def reset(self) -> None:
        """
        重置熔断器状态
        """
        with self._lock:
            self.state = SymbolRiskState(symbol=self.symbol)
            logger.info(f"[CircuitBreaker] {self.symbol}: Reset to initial state")
