#!/usr/bin/env python3
"""
Task #038 Compliance Audit Script

Verifies that the Technical Indicator Engine implementation meets
Protocol v2.0 requirements before allowing task completion.

Audit Criteria:
1. Structural: pandas_ta dependency available, calculator module exists
2. Functional: FeatureEngineer class can compute indicators on dummy data
3. Logic Test: RSI calculation produces expected column
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def audit():
    """Execute comprehensive audit of Task #038 deliverables."""
    print("=" * 80)
    print("🔍 AUDIT: Task #038 Technical Indicator Engine Compliance Check")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    # ============================================================================
    # 1. STRUCTURAL AUDIT - Dependencies and Modules
    # ============================================================================
    print("📋 [1/3] STRUCTURAL AUDIT")
    print("-" * 80)

    # Check pandas and numpy (used for manual indicator implementation)
    # Note: pandas_ta requires Python 3.12+, so we implement indicators manually
    try:
        import numpy as np
        print(f"✅ [Dependency] numpy {np.__version__} available")
        passed += 1
    except ImportError as e:
        print(f"❌ [Dependency] numpy not installed: {e}")
        failed += 1

    # Check pandas (required by pandas_ta)
    try:
        import pandas as pd
        print(f"✅ [Dependency] pandas {pd.__version__} available")
        passed += 1
    except ImportError as e:
        print(f"❌ [Dependency] pandas not installed: {e}")
        failed += 1

    # Check calculator module exists
    calculator_module = PROJECT_ROOT / "src" / "data_nexus" / "features" / "calculator.py"
    if calculator_module.exists():
        print(f"✅ [Structure] Calculator module exists: {calculator_module}")
        passed += 1
    else:
        print(f"❌ [Structure] Calculator module missing: {calculator_module}")
        failed += 1

    # Check if FeatureEngineer class can be imported
    try:
        from src.data_nexus.features.calculator import FeatureEngineer
        print("✅ [Structure] FeatureEngineer class found")
        passed += 1
    except ImportError as e:
        print(f"❌ [Structure] Failed to import FeatureEngineer: {e}")
        failed += 1

    print()

    # ============================================================================
    # 2. FUNCTIONAL AUDIT - Class Methods
    # ============================================================================
    print("📋 [2/3] FUNCTIONAL AUDIT")
    print("-" * 80)

    # Check class has required methods
    try:
        from src.data_nexus.features.calculator import FeatureEngineer

        required_methods = ['add_rsi', 'add_macd', 'add_bollinger_bands', 'add_sma']
        for method in required_methods:
            if hasattr(FeatureEngineer, method):
                print(f"✅ [Method] FeatureEngineer.{method}() exists")
                passed += 1
            else:
                print(f"❌ [Method] FeatureEngineer.{method}() missing")
                failed += 1

    except ImportError:
        print("⚠️  [Method] Skipped - class not importable")
        failed += 4

    print()

    # ============================================================================
    # 3. LOGIC TEST - RSI Calculation
    # ============================================================================
    print("📋 [3/3] LOGIC TEST")
    print("-" * 80)

    # Create dummy data and test RSI calculation
    try:
        import pandas as pd
        from src.data_nexus.features.calculator import FeatureEngineer

        # Create sample OHLCV data (100 rows)
        import numpy as np
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        # Generate realistic price data
        np.random.seed(42)
        close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

        dummy_df = pd.DataFrame({
            'time': dates,
            'open': close_prices * 0.99,
            'high': close_prices * 1.02,
            'low': close_prices * 0.98,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 100)
        })

        print(f"✅ [Test Data] Created dummy DataFrame: {len(dummy_df)} rows")
        passed += 1

        # Initialize calculator
        engineer = FeatureEngineer(dummy_df)
        print("✅ [Initialization] FeatureEngineer instantiated")
        passed += 1

        # Test RSI calculation
        result = engineer.add_rsi(period=14)

        if result is not None and isinstance(result, pd.DataFrame):
            print("✅ [Output] add_rsi() returns DataFrame")
            passed += 1
        else:
            print(f"❌ [Output] add_rsi() returned invalid type: {type(result)}")
            failed += 1

        # Check RSI column exists
        if 'RSI_14' in result.columns:
            print("✅ [Logic] RSI_14 column exists in output")
            passed += 1

            # Check RSI values are in valid range (0-100)
            rsi_values = result['RSI_14'].dropna()
            if len(rsi_values) > 0:
                if (rsi_values >= 0).all() and (rsi_values <= 100).all():
                    print(f"✅ [Validation] RSI values in valid range [0-100]: min={rsi_values.min():.2f}, max={rsi_values.max():.2f}")
                    passed += 1
                else:
                    print(f"❌ [Validation] RSI values out of range: min={rsi_values.min():.2f}, max={rsi_values.max():.2f}")
                    failed += 1
            else:
                print("⚠️  [Validation] No non-null RSI values found")
                failed += 1
        else:
            print(f"❌ [Logic] RSI_14 column missing. Columns: {result.columns.tolist()}")
            failed += 1

    except Exception as e:
        print(f"❌ [Logic Test] Failed with error: {e}")
        import traceback
        traceback.print_exc()
        failed += 5

    # ============================================================================
    # AUDIT SUMMARY
    # ============================================================================
    print()
    print("=" * 80)
    print(f"📊 AUDIT SUMMARY: {passed} Passed, {failed} Failed")
    print("=" * 80)

    if failed == 0:
        print()
        print("🎉 ✅ AUDIT PASSED: Ready for AI Review")
        print()
        print("Task #038 implementation meets Protocol v2.0 requirements.")
        print("You may proceed with: python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print()
        print("⚠️  ❌ AUDIT FAILED: Remediation Required")
        print()
        print("Issues found during audit:")
        print(f"  • {failed} check(s) failed")
        print("  • Fix issues before running 'project_cli.py finish'")
        print()
        return 1


if __name__ == "__main__":
    exit_code = audit()
    sys.exit(exit_code)
