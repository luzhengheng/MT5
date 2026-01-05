#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for StateReconciler - TASK #031

Tests state reconciliation functionality:
- Startup recovery (zombie positions)
- Continuous drift detection
- Force position operations

Run with: python3 scripts/test_reconciliation.py
"""

import sys
import time
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.strategy.portfolio import PortfolioManager, OrderStatus, create_fill_response
from src.strategy.reconciler import StateReconciler, RemotePosition, SyncStatus


# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("TEST")


# ============================================================================
# Test Functions
# ============================================================================

def test_startup_recovery_zombie_positions():
    """Test recovery of zombie positions on startup"""
    logger.info("=" * 80)
    logger.info("TEST 1: Startup Recovery - Zombie Positions")
    logger.info("=" * 80)

    # Create portfolio (FLAT on startup)
    pm = PortfolioManager(symbol="EURUSD")
    assert pm.position is None, "Portfolio should be FLAT on startup"

    # Mock gateway with zombie positions
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": [
            {
                "ticket": 123456,
                "symbol": "EURUSD",
                "type": "buy",
                "volume": 0.01,
                "price_open": 1.0543,
                "profit": 10.5,
                "time": int(time.time())
            }
        ]
    }

    # Create reconciler
    reconciler = StateReconciler(pm, mock_gateway)

    # Run startup recovery
    result = reconciler.startup_recovery()

    # Verify recovery
    assert result.status == SyncStatus.SUCCESS, f"Recovery should succeed, got {result.status}"
    assert result.recovered == 1, f"Should recover 1 position, got {result.recovered}"
    assert pm.position is not None, "Portfolio should have position after recovery"
    assert pm.position.net_volume == 0.01, f"Position should be LONG 0.01L, got {pm.position.net_volume}"
    assert pm.position.avg_entry_price == 1.0543, "Entry price should match remote"

    logger.info("✅ PASS: Startup recovery correctly loads zombie positions")
    print()


def test_continuous_sync_detects_mismatch():
    """Test continuous sync detects state mismatch"""
    logger.info("=" * 80)
    logger.info("TEST 2: Continuous Sync - Detects Mismatch")
    logger.info("=" * 80)

    # Setup: Local state = FLAT, Remote state = LONG
    pm = PortfolioManager(symbol="EURUSD")
    assert pm.position is None

    # Mock gateway with position
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": [
            {
                "ticket": 123456,
                "symbol": "EURUSD",
                "type": "buy",
                "volume": 0.01,
                "price_open": 1.0543,
                "profit": 10.5,
                "time": int(time.time())
            }
        ]
    }

    # Create reconciler
    reconciler = StateReconciler(pm, mock_gateway, sync_interval_sec=0)  # Sync immediately

    # Run continuous sync
    result = reconciler.sync_continuous()

    # Verify sync occurred and recovered position
    assert result is not None, "sync_continuous should return result"
    assert result.recovered == 1, f"Should recover 1 position, got {result.recovered}"
    assert pm.position is not None, "Position should exist after sync"
    assert pm.position.net_volume == 0.01, "Position should be LONG 0.01L"

    logger.info("✅ PASS: Continuous sync detects and fixes mismatch")
    print()


def test_detect_drift_zombie():
    """Test drift detection for zombie positions"""
    logger.info("=" * 80)
    logger.info("TEST 3: Detect Drift - Zombie Position")
    logger.info("=" * 80)

    pm = PortfolioManager(symbol="EURUSD")

    # Mock gateway with position
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": [
            {
                "ticket": 999,
                "symbol": "EURUSD",
                "type": "sell",
                "volume": 0.02,
                "price_open": 1.0555,
                "profit": -5.0,
                "time": int(time.time())
            }
        ]
    }

    reconciler = StateReconciler(pm, mock_gateway)

    # Detect drift
    drift = reconciler.detect_drift()

    assert drift is not None, "Should detect drift"
    assert "Zombie" in drift or "999" in drift, f"Should mention zombie position, got {drift}"

    logger.info(f"✅ PASS: Drift detection found: {drift}")
    print()


def test_detect_drift_ghost():
    """Test drift detection for ghost positions"""
    logger.info("=" * 80)
    logger.info("TEST 4: Detect Drift - Ghost Position")
    logger.info("=" * 80)

    pm = PortfolioManager(symbol="EURUSD")

    # Create local position
    order = pm.create_order(signal=1, price=1.0543, volume=0.01)
    pm.on_fill(create_fill_response(order.order_id, 888, 1.0543, 0.01))
    assert pm.position is not None

    # Mock gateway with NO positions
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": []
    }

    reconciler = StateReconciler(pm, mock_gateway)

    # Detect drift
    drift = reconciler.detect_drift()

    assert drift is not None, "Should detect drift"
    assert "Ghost" in drift or "888" in drift, f"Should mention ghost position, got {drift}"

    logger.info(f"✅ PASS: Drift detection found: {drift}")
    print()


def test_volume_drift_correction():
    """Test correction of volume drift"""
    logger.info("=" * 80)
    logger.info("TEST 5: Volume Drift Correction")
    logger.info("=" * 80)

    pm = PortfolioManager(symbol="EURUSD")

    # Create local position 0.01L
    order = pm.create_order(signal=1, price=1.0543, volume=0.01)
    pm.on_fill(create_fill_response(order.order_id, 777, 1.0543, 0.01))
    assert pm.position.net_volume == 0.01

    # Mock gateway showing 0.02L (drift!)
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": [
            {
                "ticket": 777,
                "symbol": "EURUSD",
                "type": "buy",
                "volume": 0.02,  # Drifted from 0.01 to 0.02
                "price_open": 1.0543,
                "profit": 20.0,
                "time": int(time.time())
            }
        ]
    }

    reconciler = StateReconciler(pm, mock_gateway)

    # Run sync
    result = reconciler.sync_positions()

    # Verify correction
    assert len(result.drifts) > 0, "Should detect drift"
    assert pm.position.net_volume == 0.02, f"Position should be corrected to 0.02L, got {pm.position.net_volume}"
    assert result.status in [SyncStatus.SUCCESS, SyncStatus.PARTIAL], f"Sync should succeed, got {result.status}"

    logger.info(f"✅ PASS: Volume drift corrected from 0.01L to 0.02L")
    print()


def test_gateway_offline_degraded_mode():
    """Test graceful degradation when gateway is offline"""
    logger.info("=" * 80)
    logger.info("TEST 6: Gateway Offline - Degraded Mode")
    logger.info("=" * 80)

    pm = PortfolioManager(symbol="EURUSD")

    # Mock offline gateway
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = None  # Gateway timeout/offline

    reconciler = StateReconciler(pm, mock_gateway)

    # Try startup recovery
    result = reconciler.startup_recovery()

    # Should degrade gracefully
    assert result.status == SyncStatus.DEGRADED, f"Should degrade, got {result.status}"
    assert len(result.errors) > 0, "Should have error message"
    assert pm.position is None, "Local state should remain unchanged"

    logger.info("✅ PASS: Graceful degradation when gateway offline")
    print()


def test_audit_trail_logging():
    """Test audit trail logging of state changes"""
    logger.info("=" * 80)
    logger.info("TEST 7: Audit Trail Logging")
    logger.info("=" * 80)

    pm = PortfolioManager(symbol="EURUSD")

    # Mock gateway
    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": [
            {
                "ticket": 555,
                "symbol": "EURUSD",
                "type": "buy",
                "volume": 0.01,
                "price_open": 1.0543,
                "profit": 10.5,
                "time": int(time.time())
            }
        ]
    }

    reconciler = StateReconciler(pm, mock_gateway)

    # Clear audit trail, run recovery
    reconciler.audit_trail = []
    reconciler.startup_recovery()

    # Check audit trail
    trail = reconciler.get_audit_trail()
    assert len(trail) > 0, "Audit trail should have entries"
    assert any(e['action'] == 'RECOVERY' for e in trail), "Should log recovery action"

    logger.info(f"✅ PASS: Audit trail recorded {len(trail)} actions")
    print()


def test_zero_sync_interval_immediate():
    """Test sync_continuous with zero interval (immediate)"""
    logger.info("=" * 80)
    logger.info("TEST 8: Sync Continuous - Zero Interval")
    logger.info("=" * 80)

    pm = PortfolioManager(symbol="EURUSD")

    mock_gateway = Mock()
    mock_gateway.get_positions.return_value = {
        "status": "SUCCESS",
        "positions": []
    }

    # Create reconciler with zero interval
    reconciler = StateReconciler(pm, mock_gateway, sync_interval_sec=0)

    # First call should sync
    result1 = reconciler.sync_continuous()
    assert result1 is not None, "First call should return result"

    logger.info("✅ PASS: Zero interval allows immediate sync")
    print()


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all reconciliation tests"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "State Reconciler Unit Tests (TASK #031)" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        test_startup_recovery_zombie_positions,
        test_continuous_sync_detects_mismatch,
        test_detect_drift_zombie,
        test_detect_drift_ghost,
        test_volume_drift_correction,
        test_gateway_offline_degraded_mode,
        test_audit_trail_logging,
        test_zero_sync_interval_immediate,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            logger.error(f"❌ FAIL: {e}")
            failed += 1
            print()
        except Exception as e:
            logger.error(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
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
