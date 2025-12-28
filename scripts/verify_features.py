#!/usr/bin/env python3
"""
Feature Engineering Verification Script

Creates sample OHLCV data, runs the FeatureEngineer calculator,
and verifies that all expected indicator columns are generated.

Task #038: Technical Indicator Engine
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from src.data_nexus.features.calculator import FeatureEngineer


def main():
    """Verify feature engineering functionality."""
    print("=" * 80)
    print("🧪 FEATURE ENGINEERING VERIFICATION")
    print("=" * 80)
    print()

    # Create sample OHLCV data
    print("📊 Creating sample OHLCV data (100 days)...")
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

    sample_df = pd.DataFrame({
        'time': dates,
        'open': close_prices * 0.99,
        'high': close_prices * 1.02,
        'low': close_prices * 0.98,
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    })

    print(f"✅ Created DataFrame: {len(sample_df)} rows, {len(sample_df.columns)} columns")
    print()

    # Initialize calculator
    print("🔧 Initializing FeatureEngineer...")
    engineer = FeatureEngineer(sample_df)
    print("✅ FeatureEngineer instantiated")
    print()

    # Calculate all indicators
    print("📈 Calculating technical indicators...")
    result = engineer.add_all_indicators()
    print("✅ Indicators calculated")
    print()

    # Verify columns
    print("🔍 Verifying indicator columns...")
    expected_columns = [
        'RSI_14',
        'MACD',
        'MACD_Signal',
        'MACD_Hist',
        'BB_Upper',
        'BB_Middle',
        'BB_Lower',
        'SMA_20'
    ]

    missing = []
    for col in expected_columns:
        if col in result.columns:
            print(f"  ✅ {col}")
        else:
            print(f"  ❌ {col} MISSING")
            missing.append(col)

    print()

    # Mathematical validation tests
    print("🔬 Mathematical Validation Tests...")
    validation_errors = []

    # Test 1: Bollinger Bands ordering (Upper > Middle > Lower)
    valid_bb_rows = result[['BB_Upper', 'BB_Middle', 'BB_Lower']].dropna()
    if len(valid_bb_rows) > 0:
        bb_order_valid = (
            (valid_bb_rows['BB_Upper'] >= valid_bb_rows['BB_Middle']).all() and
            (valid_bb_rows['BB_Middle'] >= valid_bb_rows['BB_Lower']).all()
        )
        if bb_order_valid:
            print("  ✅ Bollinger Bands ordering: Upper >= Middle >= Lower")
        else:
            print("  ❌ Bollinger Bands ordering invalid")
            validation_errors.append("BB ordering")

    # Test 2: RSI range (0-100)
    valid_rsi = result['RSI_14'].dropna()
    if len(valid_rsi) > 0:
        rsi_valid = (valid_rsi >= 0).all() and (valid_rsi <= 100).all()
        if rsi_valid:
            print(f"  ✅ RSI range [0-100]: min={valid_rsi.min():.2f}, max={valid_rsi.max():.2f}")
        else:
            print(f"  ❌ RSI out of range: min={valid_rsi.min():.2f}, max={valid_rsi.max():.2f}")
            validation_errors.append("RSI range")

    # Test 3: MACD Histogram = MACD - Signal
    valid_macd_rows = result[['MACD', 'MACD_Signal', 'MACD_Hist']].dropna()
    if len(valid_macd_rows) > 0:
        hist_calc = valid_macd_rows['MACD'] - valid_macd_rows['MACD_Signal']
        hist_error = (hist_calc - valid_macd_rows['MACD_Hist']).abs().max()
        if hist_error < 1e-10:
            print(f"  ✅ MACD Histogram calculation verified (error < 1e-10)")
        else:
            print(f"  ❌ MACD Histogram error: {hist_error}")
            validation_errors.append("MACD calculation")

    print()

    # Display sample results
    print("📋 Sample Results (Last 5 Rows):")
    print("-" * 80)
    display_cols = ['close', 'RSI_14', 'MACD', 'BB_Middle', 'SMA_20']
    print(result[display_cols].tail(5).to_string())
    print()

    # Summary
    print("=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total rows: {len(result)}")
    print(f"Total columns: {len(result.columns)}")
    print(f"Feature columns: {len(engineer.get_feature_columns())}")
    print(f"Expected indicators: {len(expected_columns)}")
    print(f"Missing indicators: {len(missing)}")
    print()

    if missing or validation_errors:
        if missing:
            print("❌ Verification FAILED - missing indicators:", missing)
        if validation_errors:
            print("❌ Verification FAILED - validation errors:", validation_errors)
        return 1
    else:
        print("✅ Feature Engineering Verified")
        print()
        print(f"Feature columns created: {engineer.get_feature_columns()}")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
