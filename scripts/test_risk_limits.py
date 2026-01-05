#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chaos Testing for Risk Monitor & Kill Switch (TASK #032)

Tests risk limit enforcement:
- Daily loss limit (stop loss)
- Order rate limiting
- Kill switch activation and reset
- Webhook alert delivery
"""

import sys
import time
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.risk.monitor import RiskMonitor, RiskViolationError
from src.risk.kill_switch import KillSwitch, get_kill_switch
from src.strategy.portfolio import PortfolioManager, Position, OrderStatus, Order
from src.strategy.reconciler import StateReconciler, SyncStatus
from datetime import datetime


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("TEST_RISK")


def test_kill_switch_activation():
    """Test 1: Kill Switch activation and state persistence"""
    logger.info("=" * 80)
    logger.info("TEST 1: Kill Switch Activation")
    logger.info("=" * 80)

    # Create fresh kill switch
    kill_switch = KillSwitch("/tmp/test_kill_switch.lock")

    # Clean state
    if kill_switch.lock_file.exists():
        kill_switch.lock_file.unlink()

    # Initially inactive
    assert not kill_switch.is_active(), "Kill switch should start inactive"
    logger.info("✅ Kill switch starts inactive")

    # Activate
    result = kill_switch.activate("Test activation: Daily loss exceeded")
    assert result is True, "First activation should succeed"
    assert kill_switch.is_active(), "Kill switch should be active after activation"
    logger.info("✅ Kill switch activated successfully")

    # Try to activate again (should be no-op)
    result = kill_switch.activate("Second attempt")
    assert result is False, "Second activation should fail (already active)"
    logger.info("✅ Kill switch prevents re-activation (one-way)")

    # Reset
    result = kill_switch.reset()
    assert result is True, "Reset should succeed"
    assert not kill_switch.is_active(), "Kill switch should be inactive after reset"
    logger.info("✅ Kill switch reset successfully")

    # Cleanup
    if kill_switch.lock_file.exists():
        kill_switch.lock_file.unlink()

    print()


def test_order_rate_limiting():
    """Test 2: Order rate limit enforcement"""
    logger.info("=" * 80)
    logger.info("TEST 2: Order Rate Limiting")
    logger.info("=" * 80)

    # Create RiskMonitor with low rate limit for testing
    monitor = RiskMonitor(max_order_rate=3)  # Only 3 orders per minute

    # Record orders and check rate AFTER adding
    monitor.record_order()
    monitor.record_order()
    assert monitor._check_order_rate(), "2 orders should be allowed (< 3)"
    logger.info("✅ 2 orders allowed (within limit)")

    # Record 3rd order
    monitor.record_order()
    # At 3 orders, we're at the limit, so check should fail (not <, but >=)
    assert not monitor._check_order_rate(), "3 orders should NOT exceed limit but order rate check uses <"
    logger.info("✅ 3 orders reaches limit (rate limit check working)")

    # Clear and test single order
    monitor.order_times.clear()
    monitor.record_order()
    assert monitor._check_order_rate(), "Single order should be allowed"
    logger.info("✅ Order rate resets correctly after clearing")

    print()


def test_daily_pnl_limit():
    """Test 3: Daily PnL limit triggers kill switch"""
    logger.info("=" * 80)
    logger.info("TEST 3: Daily PnL Limit (Stop Loss)")
    logger.info("=" * 80)

    # Setup
    kill_switch = KillSwitch("/tmp/test_kill_switch2.lock")
    if kill_switch.lock_file.exists():
        kill_switch.lock_file.unlink()

    monitor = RiskMonitor(max_daily_loss=-50.0)  # Stop loss at -$50

    # Create mock portfolio with negative PnL
    portfolio = Mock()
    position = Mock()
    position.unrealized_pnl = -75.0  # Exceeded stop loss
    position.net_volume = 0.1  # Add this so abs() won't fail
    portfolio.position = position

    # Create mock reconciler
    reconciler = Mock()
    reconciler.detect_drift.return_value = None  # No drift

    # Check signal (should be blocked due to PnL limit)
    result = monitor.check_signal(1, portfolio, reconciler)
    assert result is False, "Signal should be blocked when PnL < limit"
    assert kill_switch.is_active(), "Kill switch should be activated"
    logger.info("✅ Kill switch activated when daily loss exceeded")

    # Try another signal (should still be blocked)
    result = monitor.check_signal(1, portfolio, reconciler)
    assert result is False, "Signal should still be blocked (kill switch active)"
    logger.info("✅ Kill switch blocks all new signals")

    # Reset for next test
    kill_switch.reset()
    if kill_switch.lock_file.exists():
        kill_switch.lock_file.unlink()

    print()


def test_position_size_limit():
    """Test 4: Position size limit enforcement"""
    logger.info("=" * 80)
    logger.info("TEST 4: Position Size Limit")
    logger.info("=" * 80)

    # Clean Kill Switch from previous test
    ks = KillSwitch("/tmp/test_kill_switch2.lock")
    if ks.lock_file.exists():
        ks.lock_file.unlink()

    monitor = RiskMonitor(max_position_size=0.5)  # Max 0.5 lots

    # Create portfolio with small position
    portfolio = Mock()
    position = Mock()
    position.net_volume = 0.3  # Under limit
    position.unrealized_pnl = 10.0
    portfolio.position = position

    # Create reconciler
    reconciler = Mock()
    reconciler.detect_drift.return_value = None

    # Should allow signal (under limit)
    result = monitor.check_signal(1, portfolio, reconciler)
    assert result is True, "Signal should be allowed (under position limit)"
    logger.info("✅ Signal allowed: position size 0.3L < limit 0.5L")

    # Increase position to exceed limit
    position.net_volume = 0.6  # Over limit
    result = monitor.check_signal(1, portfolio, reconciler)
    assert result is False, "Signal should be blocked (exceeds position limit)"
    logger.info("✅ Signal blocked: position size 0.6L >= limit 0.5L")

    print()


def test_reconciler_health_check():
    """Test 5: Reconciler health status check"""
    logger.info("=" * 80)
    logger.info("TEST 5: Reconciler Health Status")
    logger.info("=" * 80)

    monitor = RiskMonitor()

    # Create portfolio
    portfolio = Mock()
    portfolio.position = None

    # Create healthy reconciler (no drift)
    reconciler = Mock()
    reconciler.detect_drift.return_value = None

    result = monitor.check_signal(1, portfolio, reconciler)
    assert result is True, "Signal should be allowed (reconciler healthy)"
    logger.info("✅ Signal allowed: reconciler healthy (no drift)")

    # Create unhealthy reconciler (detects drift)
    reconciler.detect_drift.return_value = "Zombie position detected"

    result = monitor.check_signal(1, portfolio, reconciler)
    assert result is False, "Signal should be blocked (reconciler degraded)"
    logger.info("✅ Signal blocked: reconciler unhealthy (drift detected)")

    print()


def test_system_state_check():
    """Test 6: Comprehensive system state check"""
    logger.info("=" * 80)
    logger.info("TEST 6: System State Check")
    logger.info("=" * 80)

    monitor = RiskMonitor()

    # Create mock portfolio
    portfolio = Mock()
    position = Mock()
    position.net_volume = 0.1
    position.unrealized_pnl = 5.0
    portfolio.position = position

    # Create mock reconciler
    reconciler = Mock()
    reconciler.detect_drift.return_value = None

    # Get status
    status = monitor.check_state(portfolio, reconciler)

    assert status["kill_switch_active"] is False
    assert status["reconciler_healthy"] is True
    assert status["daily_pnl"] == 5.0
    assert "violations_count" in status

    logger.info(f"✅ System state check complete:")
    logger.info(f"   - Kill Switch: {status['kill_switch_active']}")
    logger.info(f"   - Reconciler: {status['reconciler_healthy']}")
    logger.info(f"   - Daily PnL: {status['daily_pnl']}")
    logger.info(f"   - Violations: {status['violations_count']}")

    print()


def test_webhook_alert():
    """Test 7: Webhook alert delivery (mock)"""
    logger.info("=" * 80)
    logger.info("TEST 7: Webhook Alert Delivery")
    logger.info("=" * 80)

    monitor = RiskMonitor(webhook_url="http://localhost:8888/risk_alert")

    # Send mock alert
    alert = {
        "severity": "HIGH",
        "type": "ORDER_RATE_EXCEEDED",
        "message": "Order rate limit exceeded",
        "timestamp": datetime.now().isoformat()
    }

    result = monitor._send_alert(alert)
    assert result is True, "Mock webhook should succeed"
    logger.info("✅ Mock webhook alert sent successfully")

    print()


def main():
    """Run all risk limit tests"""
    print()
    print(f"{'='*80}")
    print(f"{'Risk Monitor & Kill Switch Chaos Tests (TASK #032)'.center(80)}")
    print(f"{'='*80}")
    print()

    tests = [
        ("Kill Switch Activation", test_kill_switch_activation),
        ("Order Rate Limiting", test_order_rate_limiting),
        ("Daily PnL Limit (Stop Loss)", test_daily_pnl_limit),
        ("Position Size Limit", test_position_size_limit),
        ("Reconciler Health Check", test_reconciler_health_check),
        ("System State Check", test_system_state_check),
        ("Webhook Alert Delivery", test_webhook_alert),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            logger.error(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            logger.error(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print(f"{'='*80}")
    print(f"Test Summary")
    print(f"{'='*80}")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
