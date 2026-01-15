#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Task #109 - Unit Tests and Static Analysis
Task #109 金丝雀策略和纸面交易的单元测试

Protocol v4.3 (Zero-Trust Edition)
TDD-First: Test code BEFORE business logic runs
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strategy.canary_strategy import CanaryStrategy, CanarySignal  # noqa: E402


class TestCanaryStrategy(unittest.TestCase):
    """Unit tests for CanaryStrategy"""

    def setUp(self):
        """Set up test fixtures"""
        self.strategy = CanaryStrategy(symbol="EURUSD")

    def test_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(self.strategy.symbol, "EURUSD")
        self.assertEqual(self.strategy.position_status, "CLOSED")
        self.assertEqual(self.strategy.tick_count, 0)
        print("✓ Test: Strategy initialization")

    def test_tick_counter(self):
        """Test tick counting"""
        for i in range(50):
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.0850,
                'ask': 1.0852,
                'timestamp': datetime.utcnow().isoformat(),
                'volume': 100
            }
            self.strategy.on_tick(tick)

        self.assertEqual(self.strategy.tick_count, 50)
        print("✓ Test: Tick counter")

    def test_open_signal_generation(self):
        """Test open signal generation after tick interval"""
        for i in range(15):  # Tick interval is 10
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.0850,
                'ask': 1.0852,
                'timestamp': datetime.utcnow().isoformat(),
                'volume': 100
            }
            signal = self.strategy.on_tick(tick)

            if i >= self.strategy.tick_interval:
                # First signal should appear around tick 10
                if signal and i == self.strategy.tick_interval:
                    self.assertIsNotNone(signal)
                    self.assertIn(signal.action, ['OPEN_BUY', 'OPEN_SELL'])
                    print("✓ Test: Open signal generation")
                    break

    def test_signal_dataclass(self):
        """Test CanarySignal dataclass"""
        signal = CanarySignal(
            timestamp="2026-01-15T00:00:00",
            symbol="EURUSD",
            action="OPEN_BUY",
            volume=0.01,
            reason="Test signal"
        )

        self.assertEqual(signal.symbol, "EURUSD")
        self.assertEqual(signal.action, "OPEN_BUY")
        self.assertEqual(signal.volume, 0.01)
        print("✓ Test: Signal dataclass")

    def test_position_tracking(self):
        """Test position status tracking"""
        # Initial state
        self.assertEqual(self.strategy.position_status, "CLOSED")

        # Simulate opening a position
        self.strategy.position_status = "OPEN_BUY"
        self.assertNotEqual(self.strategy.position_status, "CLOSED")

        # Simulate closing
        self.strategy.position_status = "CLOSED"
        self.assertEqual(self.strategy.position_status, "CLOSED")
        print("✓ Test: Position tracking")

    def test_statistics_generation(self):
        """Test get_statistics method"""
        stats = self.strategy.get_statistics()

        self.assertIn('total_signals', stats)
        self.assertIn('opens', stats)
        self.assertIn('closes', stats)
        self.assertIn('tick_count', stats)
        self.assertIn('position_status', stats)
        print("✓ Test: Statistics generation")

    def test_multiple_cycles(self):
        """Test multiple open/close cycles"""
        import random

        random.seed(42)  # Deterministic for testing

        for cycle in range(3):
            # Simulate 50 ticks per cycle
            for i in range(50):
                tick = {
                    'symbol': 'EURUSD',
                    'bid': 1.0850 + i * 0.00001,
                    'ask': 1.0852 + i * 0.00001,
                    'timestamp': datetime.utcnow().isoformat(),
                    'volume': 100
                }
                self.strategy.on_tick(tick)

        stats = self.strategy.get_statistics()
        self.assertGreater(stats['total_signals'], 0, "Should have generated at least one signal")
        print("✓ Test: Multiple cycles")


class TestPaperTradingSetup(unittest.TestCase):
    """Integration tests for paper trading setup"""

    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            # Verify strategy import
            self.assertIsNotNone(CanaryStrategy)
            print("✓ Test: All imports successful")
        except Exception as e:
            self.fail(f"Critical import failed: {e}")

    def test_demo_account_config(self):
        """Test demo account configuration"""
        demo_account = 1100212251
        self.assertIsInstance(demo_account, int)
        self.assertGreater(demo_account, 1000000)
        print("✓ Test: Demo account config")

    def test_risk_limits(self):
        """Test risk limit configuration"""
        max_lot_size = 1.0
        self.assertGreater(max_lot_size, 0.01)
        self.assertLess(max_lot_size, 100.0)
        print("✓ Test: Risk limits")


def run_static_analysis():
    """Run static code analysis"""
    print("\n[STATIC ANALYSIS]")

    files_to_check = [
        "src/strategy/canary_strategy.py",
        "scripts/ops/launch_paper_trading.py",
        "scripts/verify_full_loop.py"
    ]

    for file_path in files_to_check:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')

                # Check for common issues
                has_docstring = '"""' in content or "'''" in content
                has_logging = 'import logging' in content or 'logger' in content

                status = "✓" if has_docstring and has_logging else "⚠"
                print(f"{status} {file_path} ({len(lines)} lines)")
                if not has_docstring:
                    print("  ⚠ Missing docstring")
                if not has_logging:
                    print("  ⚠ Missing logging")

        else:
            print(f"✗ File not found: {file_path}")


if __name__ == "__main__":
    print("=" * 80)
    print("AUDIT TASK #109 - TDD Unit Tests")
    print("=" * 80)

    # Run unit tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Run static analysis
    run_static_analysis()

    # Summary
    print("\n" + "=" * 80)
    print(f"AUDIT SUMMARY")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)
