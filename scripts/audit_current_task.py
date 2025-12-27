#!/usr/bin/env python3
"""
Audit Script for Task #024: Real ML Strategy Signal Integration
=================================================================

Structural audit to verify Work Order #024 implementation.

This audit ensures:
1. LiveStrategyAdapter exists and is properly structured
2. TradingBot integrates the strategy (calls predict)
3. main.py imports and injects the adapter
4. Feature engineering is accessible
5. All dependencies are installed

Critical TDD Requirement:
- The finish command runs this audit first
- If any critical check fails, task fails validation
- All assertions must pass for task completion

Protocol: v2.0 (Strict TDD & ML Integration)
"""

import sys
import os
import unittest
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Audit Test Suite
# ============================================================================

class TestTask024MLIntegration(unittest.TestCase):
    """
    Comprehensive audit for Work Order #024.
    """

    # ========================================================================
    # Test 1: LiveStrategyAdapter Existence and Structure
    # ========================================================================

    def test_adapter_file_exists(self):
        """Verify live_adapter.py exists."""
        print("\n[Test 1/6] Checking LiveStrategyAdapter existence...")

        adapter_file = PROJECT_ROOT / "src" / "strategy" / "live_adapter.py"
        self.assertTrue(adapter_file.exists(), "live_adapter.py must exist")
        print(f"  ✅ {adapter_file.name} exists")

    def test_adapter_class_exists(self):
        """Verify LiveStrategyAdapter class is properly defined."""
        print("\n[Test 2/6] Checking LiveStrategyAdapter class...")

        try:
            from src.strategy.live_adapter import LiveStrategyAdapter

            self.assertTrue(
                hasattr(LiveStrategyAdapter, 'predict'),
                "LiveStrategyAdapter must have predict method"
            )
            print(f"  ✅ LiveStrategyAdapter class found")
            print(f"  ✅ predict() method exists")

            # Check other critical methods
            methods = ['_load_model', '_tick_to_dataframe', '_proba_to_signal']
            for method in methods:
                self.assertTrue(
                    hasattr(LiveStrategyAdapter, method),
                    f"LiveStrategyAdapter must have {method} method"
                )
                print(f"  ✅ {method}() method exists")

        except ImportError as e:
            self.fail(f"Failed to import LiveStrategyAdapter: {e}")

    # ========================================================================
    # Test 3: TradingBot Integration
    # ========================================================================

    def test_trading_bot_strategy_integration(self):
        """Verify TradingBot uses the strategy adapter."""
        print("\n[Test 3/6] Checking TradingBot integration...")

        trading_bot_file = PROJECT_ROOT / "src" / "bot" / "trading_bot.py"
        content = trading_bot_file.read_text()

        # Check for strategy.predict call
        self.assertIn(
            "self.strategy.predict",
            content,
            "TradingBot must call strategy.predict()"
        )
        print(f"  ✅ TradingBot calls strategy.predict()")

        # Check for signal handling
        signal_keywords = ["BUY", "SELL", "HOLD"]
        for keyword in signal_keywords:
            self.assertIn(
                keyword,
                content,
                f"TradingBot must handle {keyword} signal"
            )
            print(f"  ✅ {keyword} signal handling found")

    # ========================================================================
    # Test 4: Main.py Integration
    # ========================================================================

    def test_main_imports_adapter(self):
        """Verify main.py imports LiveStrategyAdapter."""
        print("\n[Test 4/6] Checking main.py integration...")

        main_file = PROJECT_ROOT / "src" / "main.py"
        content = main_file.read_text()

        self.assertIn(
            "from src.strategy.live_adapter import LiveStrategyAdapter",
            content,
            "main.py must import LiveStrategyAdapter"
        )
        print(f"  ✅ main.py imports LiveStrategyAdapter")

        self.assertIn(
            "LiveStrategyAdapter()",
            content,
            "main.py must instantiate LiveStrategyAdapter"
        )
        print(f"  ✅ main.py instantiates adapter")

        self.assertIn(
            "strategy_engine=strategy",
            content,
            "main.py must inject strategy into TradingBot"
        )
        print(f"  ✅ main.py injects adapter into TradingBot")

    # ========================================================================
    # Test 5: Feature Engineering Availability
    # ========================================================================

    def test_feature_engineering_available(self):
        """Verify feature engineering module is accessible."""
        print("\n[Test 5/6] Checking feature engineering...")

        try:
            from src.feature_engineering import FeatureEngineer

            self.assertTrue(
                hasattr(FeatureEngineer, 'compute_features'),
                "FeatureEngineer must have compute_features method"
            )
            print(f"  ✅ FeatureEngineer class available")
            print(f"  ✅ compute_features() method exists")

        except ImportError as e:
            self.fail(f"Failed to import FeatureEngineer: {e}")

    # ========================================================================
    # Test 6: Dependencies Verification
    # ========================================================================

    def test_ml_dependencies(self):
        """Verify ML dependencies are installed."""
        print("\n[Test 6/6] Checking ML dependencies...")

        required_packages = [
            ("pandas", "pandas"),
            ("xgboost", "xgboost"),
            ("sklearn", "scikit-learn"),
            ("lightgbm", "lightgbm"),
        ]

        for import_name, package_name in required_packages:
            try:
                __import__(import_name)
                print(f"  ✅ {package_name} installed")
            except ImportError:
                self.fail(f"{package_name} not installed")


# ============================================================================
# Main Audit Execution
# ============================================================================

def main():
    """Run the audit suite."""
    print("=" * 70)
    print("🛡️  AUDIT: Work Order #024 - Real ML Strategy Signal Integration")
    print("=" * 70)
    print()
    print("Components under audit:")
    print("  1. src/strategy/live_adapter.py")
    print("  2. src/bot/trading_bot.py (strategy integration)")
    print("  3. src/main.py (adapter injection)")
    print("  4. src/feature_engineering (feature generation)")
    print("  5. ML stack dependencies")
    print()

    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    suite = unittest.makeSuite(TestTask024MLIntegration)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ AUDIT PASSED - All checks successful")
        print("=" * 70)
        print()
        print("Verified Components:")
        print("  ✅ LiveStrategyAdapter exists and is properly structured")
        print("  ✅ TradingBot integrates strategy (calls predict)")
        print("  ✅ main.py imports and injects adapter")
        print("  ✅ Feature engineering accessible")
        print("  ✅ ML dependencies installed")
        print()
        print("Next Steps:")
        print("  1. Test with sample data: python3 src/strategy/live_adapter.py")
        print("  2. Run trading bot: python3 src/main.py")
        print("  3. Monitor strategy signals in logs")
        print()
        return 0
    else:
        print("❌ AUDIT FAILED")
        print("=" * 70)
        print()
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
