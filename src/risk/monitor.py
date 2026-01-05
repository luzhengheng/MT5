#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Monitor - Real-time Risk Enforcement (TASK #032)

Monitors trading system for risk violations including:
- Daily P&L limits (stop loss)
- Order rate limits (prevent runaway algorithms)
- Position size limits (prevent over-leverage)
- System state health (reconciliation status)

Integration Points:
- PortfolioManager: Daily PnL and position state
- StateReconciler: System health status
- KillSwitch: Emergency halt mechanism
"""

import logging
import json
import time
from typing import Optional, Dict, List
from collections import deque
from datetime import datetime, timedelta
import urllib.request
import urllib.error

from src.config import (
    RISK_MAX_DAILY_LOSS,
    RISK_MAX_ORDER_RATE,
    RISK_MAX_POSITION_SIZE,
    RISK_WEBHOOK_URL
)
from src.risk.kill_switch import get_kill_switch, KillSwitch


class RiskViolationError(Exception):
    """Raised when a risk limit is violated"""
    pass


class RiskMonitor:
    """
    Real-time risk monitoring and enforcement.

    Continuously checks trading system against risk limits and takes
    action when limits are breached:
    - Alerts via webhook
    - Activates KillSwitch if critical
    - Maintains audit log of violations

    Attributes:
        max_daily_loss: Maximum allowed daily loss (negative number)
        max_order_rate: Maximum orders per minute
        max_position_size: Maximum position size per symbol
        webhook_url: Webhook URL for alerts
        order_times: Deque of recent order timestamps
        kill_switch: Reference to KillSwitch instance
    """

    def __init__(
        self,
        max_daily_loss: float = RISK_MAX_DAILY_LOSS,
        max_order_rate: int = RISK_MAX_ORDER_RATE,
        max_position_size: float = RISK_MAX_POSITION_SIZE,
        webhook_url: str = RISK_WEBHOOK_URL
    ):
        """
        Initialize RiskMonitor.

        Args:
            max_daily_loss: Maximum daily loss threshold (negative, e.g., -50.0)
            max_order_rate: Maximum orders per minute
            max_position_size: Maximum position size in lots
            webhook_url: URL for risk alert webhooks
        """
        self.max_daily_loss = max_daily_loss
        self.max_order_rate = max_order_rate
        self.max_position_size = max_position_size
        self.webhook_url = webhook_url

        # Track recent orders for rate limiting
        self.order_times: deque = deque()

        # Reference to global KillSwitch
        self.kill_switch = get_kill_switch()

        # Logging
        self.logger = logging.getLogger("RiskMonitor")

        # Violation history
        self.violations: List[Dict] = []

    def check_signal(self, signal: int, portfolio_manager, reconciler) -> bool:
        """
        Check if a trading signal is allowed based on risk constraints.

        Flow:
        1. If KillSwitch active → reject signal
        2. If Reconciler unhealthy → reject signal
        3. Check order rate limit
        4. Check position size limit
        5. Check daily PnL limit

        Args:
            signal: Trading signal (1=BUY, -1=SELL, 0=HOLD)
            portfolio_manager: PortfolioManager instance
            reconciler: StateReconciler instance

        Returns:
            True if signal is allowed, False if blocked by risk limits

        Raises:
            RiskViolationError: If critical limit is breached
        """
        # Quick exit for HOLD
        if signal == 0:
            return False

        # Check 1: KillSwitch status
        if self.kill_switch.is_active():
            self.logger.warning(
                f"[RISK] Signal blocked: KillSwitch active ({self.kill_switch.activation_reason})"
            )
            return False

        # Check 2: Reconciler health
        if not self._check_reconciler_health(reconciler):
            self.logger.warning("[RISK] Signal blocked: Reconciler in DEGRADED mode")
            return False

        # Check 3: Order rate limit
        if not self._check_order_rate():
            self.logger.warning("[RISK] Signal blocked: Order rate limit exceeded")
            self._send_alert({
                "severity": "HIGH",
                "type": "ORDER_RATE_EXCEEDED",
                "message": f"Order rate {self.max_order_rate} orders/min exceeded",
                "timestamp": datetime.now().isoformat()
            })
            return False

        # Check 4: Position size limit
        position = portfolio_manager.position
        if position is not None and abs(position.net_volume) >= self.max_position_size:
            self.logger.warning(
                f"[RISK] Signal blocked: Position size {position.net_volume} >= limit {self.max_position_size}"
            )
            return False

        # Check 5: Daily PnL limit (critical)
        daily_pnl = self._calculate_daily_pnl(portfolio_manager)
        if daily_pnl < self.max_daily_loss:
            self.logger.critical(
                f"[RISK] KILL SWITCH: Daily PnL {daily_pnl} < limit {self.max_daily_loss}"
            )
            self.kill_switch.activate(f"Daily loss limit exceeded: {daily_pnl}")
            self._send_alert({
                "severity": "CRITICAL",
                "type": "MAX_DAILY_LOSS_EXCEEDED",
                "message": f"Daily PnL {daily_pnl} exceeded limit {self.max_daily_loss}",
                "timestamp": datetime.now().isoformat()
            })
            return False

        return True

    def check_state(self, portfolio_manager, reconciler) -> Dict:
        """
        Comprehensive system health check (periodic monitoring).

        Returns:
            Dict with all risk metrics and warnings
        """
        checks = {
            "timestamp": datetime.now().isoformat(),
            "kill_switch_active": self.kill_switch.is_active(),
            "reconciler_healthy": self._check_reconciler_health(reconciler),
            "order_rate_ok": self._check_order_rate(),
            "daily_pnl": self._calculate_daily_pnl(portfolio_manager),
            "position_size": abs(portfolio_manager.position.net_volume) if portfolio_manager.position else 0,
            "violations_count": len(self.violations)
        }

        # Check for warnings
        warnings = []
        if checks["kill_switch_active"]:
            warnings.append(f"KillSwitch active: {self.kill_switch.activation_reason}")
        if not checks["reconciler_healthy"]:
            warnings.append("Reconciler in DEGRADED mode")
        if checks["daily_pnl"] < self.max_daily_loss * 0.8:  # 80% of limit
            warnings.append(f"Daily PnL approaching limit: {checks['daily_pnl']}")

        if warnings:
            checks["warnings"] = warnings
            self.logger.warning(f"[RISK] System warnings: {', '.join(warnings)}")

        return checks

    def record_order(self) -> None:
        """
        Record an order for rate limiting purposes.

        Should be called whenever an order is placed.
        """
        now = time.time()
        self.order_times.append(now)

    def _check_order_rate(self) -> bool:
        """
        Check if order rate limit is exceeded.

        Uses sliding window: count orders in last 60 seconds.

        Returns:
            True if rate is OK, False if limit exceeded
        """
        now = time.time()
        one_minute_ago = now - 60

        # Remove orders older than 1 minute
        while self.order_times and self.order_times[0] < one_minute_ago:
            self.order_times.popleft()

        # Check count
        order_count = len(self.order_times)
        is_ok = order_count < self.max_order_rate

        if not is_ok:
            self.logger.warning(
                f"[RISK] Order rate limit exceeded: {order_count} orders in 60s, limit: {self.max_order_rate}"
            )

        return is_ok

    def _check_reconciler_health(self, reconciler) -> bool:
        """
        Check if reconciler is healthy.

        Returns:
            True if reconciler is OK, False if DEGRADED
        """
        if not reconciler:
            return True  # No reconciler, assume OK

        # Check if reconciler has detect_drift() method and can report status
        try:
            drift = reconciler.detect_drift()
            if drift:
                self.logger.warning(f"[RISK] Reconciler drift detected: {drift}")
                return False
            return True
        except Exception as e:
            self.logger.warning(f"[RISK] Reconciler health check failed: {e}")
            return False

    def _calculate_daily_pnl(self, portfolio_manager) -> float:
        """
        Calculate current daily P&L.

        For simplicity, uses unrealized PnL from current position.
        In production, would sum realized + unrealized.

        Args:
            portfolio_manager: PortfolioManager instance

        Returns:
            Current daily P&L (positive = profit, negative = loss)
        """
        if portfolio_manager.position is None:
            return 0.0

        return portfolio_manager.position.unrealized_pnl

    def _send_alert(self, alert: Dict) -> bool:
        """
        Send risk alert via webhook.

        Args:
            alert: Alert dict to send

        Returns:
            True if sent successfully, False if failed
        """
        try:
            # Log locally first
            self.logger.warning(f"[ALERT] {alert['type']}: {alert['message']}")

            # Try to send via webhook
            if not self.webhook_url or self.webhook_url == "http://localhost:8888/risk_alert":
                # Mock webhook (for testing)
                self.logger.info(f"[WEBHOOK_MOCK] Would send: {json.dumps(alert, indent=2)}")
                return True

            # Real webhook
            headers = {"Content-Type": "application/json"}
            data = json.dumps(alert).encode('utf-8')

            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    self.logger.info(f"[ALERT] Successfully sent to webhook")
                    return True
                else:
                    self.logger.warning(f"[ALERT] Webhook returned {response.status}")
                    return False

        except urllib.error.URLError as e:
            self.logger.warning(f"[ALERT] Webhook delivery failed: {e.reason}")
            return False
        except Exception as e:
            self.logger.error(f"[ALERT] Error sending alert: {e}")
            return False

    def get_violations(self) -> List[Dict]:
        """
        Get history of risk violations.

        Returns:
            List of violation records
        """
        return self.violations.copy()

    def get_status(self) -> Dict:
        """
        Get RiskMonitor status.

        Returns:
            Dict with current configuration and state
        """
        return {
            "max_daily_loss": self.max_daily_loss,
            "max_order_rate": self.max_order_rate,
            "max_position_size": self.max_position_size,
            "recent_orders": len(self.order_times),
            "violations_count": len(self.violations),
            "kill_switch": self.kill_switch.get_status()
        }
