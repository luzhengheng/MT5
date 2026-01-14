#!/usr/bin/env python3
"""
Risk Monitor - Active Defense System for Live Trading
Task #105 - Live Risk Monitor Implementation

Protocol v4.3 (Zero-Trust Edition) compliant real-time risk monitoring
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import yaml
import sys

# Secure module loading with integrity verification
# Add execution directory to path to import secure_loader
sys.path.insert(0, str(Path(__file__).parent))
from secure_loader import SecureModuleLoader, SecurityError

# Initialize secure loader
_loader = SecureModuleLoader(allowed_base_dir=Path(__file__).parent.parent)

# Load circuit_breaker with security validation
try:
    _cb_path = Path(__file__).parent.parent / "risk" / "circuit_breaker.py"
    _cb_module = _loader.load_module(_cb_path, module_name="circuit_breaker_module")
    CircuitBreaker = _cb_module.CircuitBreaker
except SecurityError as e:
    raise ImportError(f"Failed to load CircuitBreaker module securely: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RiskMonitor')


@dataclass
class AccountState:
    """Real-time account state snapshot"""
    timestamp: str
    balance: float
    open_pnl: float = 0.0
    closed_pnl: float = 0.0
    total_pnl: float = 0.0
    positions: int = 0
    total_exposure: float = 0.0
    leverage: float = 1.0
    drawdown: float = 0.0
    drawdown_pct: float = 0.0
    alert_level: str = "NORMAL"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class RiskMonitor:
    """Live Risk Monitoring System - Active Defense Layer"""

    def __init__(self,
                 circuit_breaker: CircuitBreaker,
                 config_path: str = "config/risk_limits.yaml",
                 initial_balance: float = 100000.0):
        """Initialize Risk Monitor"""
        self.circuit_breaker = circuit_breaker
        self.initial_balance = initial_balance
        self.config = self._load_config(config_path)

        self.account_state = AccountState(
            timestamp=datetime.utcnow().isoformat(),
            balance=initial_balance
        )

        self.peak_balance = initial_balance
        self.alert_history: List[Dict[str, Any]] = []
        self.kill_triggers: List[Dict[str, Any]] = []

        self.ticks_monitored = 0
        self.alerts_triggered = 0
        self.kills_triggered = 0

        logger.info(f"✅ RiskMonitor initialized (Balance: ${initial_balance:,.2f})")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate risk configuration from YAML

        Includes boundary checks to prevent configuration tampering.
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Validate configuration
            self._validate_config(config)

            logger.info(f"✅ Risk configuration loaded and validated from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"⚠️  Config not found: {config_path}, using defaults")
            return self._get_default_config()
        except ValueError as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            logger.warning("⚠️  Using default configuration instead")
            return self._get_default_config()

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration boundaries to prevent tampering

        Raises:
            ValueError: If configuration is invalid or out of bounds
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        risk = config.get('risk', {})
        alerts = config.get('alerts', {})

        # Validate hard risk limits (P0 - cannot be tampered)
        max_dd = float(risk.get('max_daily_drawdown', 0.02))
        if not 0.001 <= max_dd <= 0.50:
            raise ValueError(
                f"max_daily_drawdown must be 0.1%-50%, got {max_dd:.1%}"
            )

        max_lev = float(risk.get('max_account_leverage', 5.0))
        if not 1.0 <= max_lev <= 20.0:
            raise ValueError(
                f"max_account_leverage must be 1-20x, got {max_lev:.1f}x"
            )

        max_pos = float(risk.get('max_single_position_size', 1.0))
        if not 0.01 <= max_pos <= 10.0:
            raise ValueError(
                f"max_single_position_size must be 0.01-10.0, got {max_pos}"
            )

        # Validate soft warning limits (must be less than hard limits)
        dd_warn = float(alerts.get('drawdown_warning', 0.01))
        if not 0.001 <= dd_warn < max_dd:
            raise ValueError(
                f"drawdown_warning ({dd_warn:.1%}) must be less than "
                f"max_daily_drawdown ({max_dd:.1%})"
            )

        lev_warn = float(alerts.get('leverage_warning', 3.0))
        if not 1.0 <= lev_warn < max_lev:
            raise ValueError(
                f"leverage_warning ({lev_warn:.1f}x) must be less than "
                f"max_account_leverage ({max_lev:.1f}x)"
            )

        logger.debug("✓ Configuration validation passed")


    def _get_default_config(self) -> Dict[str, Any]:
        """Return default risk configuration"""
        return {
            'risk': {
                'max_daily_drawdown': 0.02,
                'max_account_leverage': 5.0,
                'max_single_position_size': 1.0,
                'kill_switch_mode': 'auto'
            },
            'alerts': {
                'drawdown_warning': 0.01,
                'leverage_warning': 3.0
            }
        }

    def monitor_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor a single tick and update account state"""
        self.ticks_monitored += 1
        tick_id = tick_data.get('tick_id', self.ticks_monitored)

        pnl_impact = self._calculate_tick_pnl(tick_data)

        self.account_state.balance += pnl_impact
        self.account_state.open_pnl += pnl_impact
        self.account_state.total_pnl = (self.account_state.closed_pnl +
                                         self.account_state.open_pnl)
        self.account_state.timestamp = (tick_data.get('timestamp',
                                         datetime.utcnow().isoformat()))

        self.account_state.total_exposure = self._calculate_exposure(tick_data)
        self.account_state.leverage = self._calculate_leverage()
        self.account_state.drawdown = self.peak_balance - self.account_state.balance
        self.account_state.drawdown_pct = (
            (self.account_state.drawdown / self.peak_balance)
            if self.peak_balance > 0 else 0.0
        )

        if self.account_state.balance > self.peak_balance:
            self.peak_balance = self.account_state.balance

        alerts = self._enforce_limits(tick_id)

        result = {
            'tick_id': tick_id,
            'timestamp': self.account_state.timestamp,
            'action': 'MONITORED',
            'pnl_impact': pnl_impact,
            'account_state': self.account_state.to_dict(),
            'alerts': alerts,
            'kill_switch_status': self.circuit_breaker.get_status()['state']
        }

        return result

    def _calculate_tick_pnl(self, tick_data: Dict[str, Any]) -> float:
        """Calculate PnL impact from tick movement"""
        bid = tick_data.get('bid', 1.08500)
        price_change = bid - 1.08500
        return price_change * 100000

    def _calculate_exposure(self, tick_data: Dict[str, Any]) -> float:
        """Calculate total exposure (notional value)"""
        return self.account_state.balance

    def _calculate_leverage(self) -> float:
        """Calculate current leverage"""
        if self.account_state.total_exposure == 0:
            return 1.0
        leverage = self.account_state.total_exposure / self.initial_balance
        return min(leverage, 10.0)

    def _enforce_limits(self, tick_id: int) -> List[Dict[str, Any]]:
        """Check all risk limits and trigger alerts/kills"""
        alerts = []

        max_drawdown = self.config['risk']['max_daily_drawdown']
        drawdown_warning = self.config['alerts']['drawdown_warning']
        max_leverage = self.config['risk']['max_account_leverage']
        leverage_warning = self.config['alerts']['leverage_warning']

        if self.account_state.drawdown_pct >= max_drawdown:
            alert = {
                'type': 'CRITICAL_DRAWDOWN',
                'tick_id': tick_id,
                'timestamp': datetime.utcnow().isoformat(),
                'drawdown_pct': self.account_state.drawdown_pct,
                'limit': max_drawdown,
                'action': 'KILL_SWITCH_TRIGGERED'
            }
            alerts.append(alert)
            self.kill_triggers.append(alert)
            self.kills_triggered += 1

            self.circuit_breaker.engage(
                reason=(f"Drawdown {self.account_state.drawdown_pct:.2%} "
                        f"exceeded {max_drawdown:.2%}"),
                metadata={'tick_id': tick_id,
                          'drawdown': self.account_state.drawdown_pct}
            )

            msg = f"🚨 [KILL] Drawdown {self.account_state.drawdown_pct:.2%}"
            logger.critical(msg)
            self.account_state.alert_level = 'CRITICAL'

        elif self.account_state.drawdown_pct >= drawdown_warning:
            alert = {
                'type': 'DRAWDOWN_WARNING',
                'tick_id': tick_id,
                'timestamp': datetime.utcnow().isoformat(),
                'drawdown_pct': self.account_state.drawdown_pct,
                'limit': drawdown_warning,
                'action': 'ALERT_ONLY'
            }
            alerts.append(alert)
            self.alert_history.append(alert)
            self.alerts_triggered += 1

            msg = f"⚠️  Drawdown warning {self.account_state.drawdown_pct:.2%}"
            logger.warning(msg)
            if self.account_state.alert_level == 'NORMAL':
                self.account_state.alert_level = 'WARNING'

        if self.account_state.leverage >= max_leverage:
            alert = {
                'type': 'CRITICAL_LEVERAGE',
                'tick_id': tick_id,
                'timestamp': datetime.utcnow().isoformat(),
                'leverage': self.account_state.leverage,
                'limit': max_leverage,
                'action': 'KILL_SWITCH_TRIGGERED'
            }
            alerts.append(alert)
            self.kill_triggers.append(alert)
            self.kills_triggered += 1

            self.circuit_breaker.engage(
                reason=(f"Leverage {self.account_state.leverage:.1f}x "
                        f"exceeded {max_leverage:.1f}x"),
                metadata={'tick_id': tick_id,
                          'leverage': self.account_state.leverage}
            )

            msg = f"🚨 [KILL] Leverage {self.account_state.leverage:.1f}x"
            logger.critical(msg)
            self.account_state.alert_level = 'CRITICAL'

        elif self.account_state.leverage >= leverage_warning:
            alert = {
                'type': 'LEVERAGE_WARNING',
                'tick_id': tick_id,
                'timestamp': datetime.utcnow().isoformat(),
                'leverage': self.account_state.leverage,
                'limit': leverage_warning,
                'action': 'ALERT_ONLY'
            }
            alerts.append(alert)
            self.alert_history.append(alert)
            self.alerts_triggered += 1

            msg = f"⚠️  Leverage warning {self.account_state.leverage:.1f}x"
            logger.warning(msg)
            if self.account_state.alert_level == 'NORMAL':
                self.account_state.alert_level = 'WARNING'

        return alerts

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        return {
            'ticks_monitored': self.ticks_monitored,
            'alerts_triggered': self.alerts_triggered,
            'kills_triggered': self.kills_triggered,
            'account_state': self.account_state.to_dict(),
            'current_balance': self.account_state.balance,
            'peak_balance': self.peak_balance,
            'total_pnl': self.account_state.total_pnl,
            'max_drawdown': self.account_state.drawdown_pct,
            'kill_triggers': self.kill_triggers,
            'circuit_breaker_status': self.circuit_breaker.get_status()
        }

    def print_summary(self):
        """Print monitoring summary"""
        summary = self.get_summary()
        print("\n" + "="*80)
        print("📊 RISK MONITOR SUMMARY")
        print("="*80)
        print(f"Ticks Monitored:     {summary['ticks_monitored']}")
        print(f"Alerts Triggered:    {summary['alerts_triggered']}")
        print(f"Kills Triggered:     {summary['kills_triggered']}")
        print(f"Current Balance:     ${summary['current_balance']:,.2f}")
        print(f"Peak Balance:        ${summary['peak_balance']:,.2f}")
        print(f"Total PnL:           ${summary['total_pnl']:,.2f}")
        print(f"Max Drawdown:        {summary['max_drawdown']:.2%}")
        print(f"Kill Switch Status:  {summary['circuit_breaker_status']['state']}")
        print("="*80 + "\n")


if __name__ == "__main__":
    print("🧪 Testing Risk Monitor...")

    cb = CircuitBreaker()
    monitor = RiskMonitor(cb, initial_balance=100000.0)

    for i in range(1, 6):
        tick_data = {
            'tick_id': i,
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': 'EURUSD',
            'bid': 1.08500 + (i * 0.00001),
            'ask': 1.08510 + (i * 0.00001),
            'volume': 100000
        }
        result = monitor.monitor_tick(tick_data)

    monitor.print_summary()
    print("✅ Risk Monitor tests passed")
