#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for LiveStrategyAdapter

Task #020.01: Unified Strategy Adapter (Backtest & Live)

Tests the adapter for signal generation and position sizing.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.strategy import LiveStrategyAdapter

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print formatted header"""
    print()
    print("=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)
    print()


def print_result(test_num, name, success, message=""):
    """Print test result"""
    status = f"{GREEN}✅ PASS{RESET}" if success else f"{RED}❌ FAIL{RESET}"
    print(f"Test {test_num}: {status} | {name}")
    if message:
        print(f"           {message}")


def test_1_adapter_initialization():
    """Test 1: Adapter initialization"""
    print_header("TEST 1: Adapter Initialization")

    try:
        adapter = LiveStrategyAdapter()
        print_result(
            1,
            "Adapter initialization",
            True,
            f"Model type: {adapter.model_type}"
        )
        return True, adapter
    except Exception as e:
        print_result(1, "Adapter initialization", False, str(e))
        return False, None


def test_2_model_loading():
    """Test 2: Model loading from JSON"""
    print_header("TEST 2: Model Loading")

    try:
        model_path = PROJECT_ROOT / "models" / "baseline_v1.json"

        if not model_path.exists():
            print_result(
                2,
                "Model file existence",
                False,
                f"Model not found: {model_path}"
            )
            return False

        adapter = LiveStrategyAdapter(model_path=str(model_path))

        success = adapter.is_model_loaded()
        print_result(
            2,
            "Model loading from JSON",
            success,
            f"Loaded: {adapter.model_type}"
        )
        return success, adapter

    except Exception as e:
        print_result(2, "Model loading from JSON", False, str(e))
        return False, None


def test_3_signal_generation():
    """Test 3: Signal generation with known features"""
    print_header("TEST 3: Signal Generation")

    adapter = LiveStrategyAdapter()

    if not adapter.is_model_loaded():
        print_result(3, "Signal generation", False, "Model not loaded")
        return False

    try:
        # Create test features (18 values)
        features = np.array([[
            1.10050,   # sma_20
            1.10000,   # sma_50
            1.09950,   # sma_200
            65.0,      # rsi_14
            0.0005,    # macd_line
            0.0003,    # macd_signal
            0.0002,    # macd_histogram
            0.0010,    # atr_14
            1.10100,   # bb_upper
            1.10050,   # bb_middle
            1.10000,   # bb_lower
            0.5,       # bb_position
            5.0,       # rsi_momentum
            0.4,       # macd_strength
            0.0001,    # sma_trend
            1.05,      # volatility_ratio
            0.001,     # returns_1d
            0.005      # returns_5d
        ]])

        signal = adapter.generate_signal(features)

        # Signal should be in {-1, 0, 1}
        valid_signal = signal in [-1, 0, 1]

        print_result(
            3,
            "Signal generation",
            valid_signal,
            f"Signal: {signal} (BUY=1, SELL=-1, HOLD=0)"
        )
        return valid_signal

    except Exception as e:
        print_result(3, "Signal generation", False, str(e))
        return False


def test_4_signal_consistency():
    """Test 4: Signal consistency (same features -> same signal)"""
    print_header("TEST 4: Signal Consistency")

    adapter = LiveStrategyAdapter()

    if not adapter.is_model_loaded():
        print_result(4, "Signal consistency", False, "Model not loaded")
        return False

    try:
        features = np.array([[
            1.10050, 1.10000, 1.09950, 65.0, 0.0005, 0.0003, 0.0002, 0.0010,
            1.10100, 1.10050, 1.10000, 0.5, 5.0, 0.4, 0.0001, 1.05, 0.001, 0.005
        ]])

        signal1 = adapter.generate_signal(features)
        signal2 = adapter.generate_signal(features)
        signal3 = adapter.generate_signal(features)

        consistent = (signal1 == signal2 == signal3)

        print_result(
            4,
            "Signal consistency",
            consistent,
            f"Signals: {signal1}, {signal2}, {signal3}"
        )
        return consistent

    except Exception as e:
        print_result(4, "Signal consistency", False, str(e))
        return False


def test_5_position_sizing():
    """Test 5: Position sizing calculation"""
    print_header("TEST 5: Position Sizing")

    adapter = LiveStrategyAdapter()

    try:
        # Test 1: BUY signal with explicit volatility
        signal = 1
        balance = 10000.0
        price = 1.10078
        volatility = 0.0015  # ATR or volatility metric

        volume = adapter.calculate_position_size(signal, balance, price, volatility)

        valid_volume = (
            volume > 0 and
            volume <= (balance * 0.1) / price  # Max position check
        )

        print_result(
            5,
            "Position sizing (BUY)",
            valid_volume,
            f"Volume: {volume:.4f} lots (volatility={volatility})"
        )

        # Test 2: HOLD signal
        signal_hold = 0
        volume_hold = adapter.calculate_position_size(signal_hold, balance, price, volatility)

        hold_correct = (volume_hold == 0.0)

        print(f"         {CYAN}HOLD signal returns 0.0: {hold_correct}{RESET}")

        # Test 3: Default volatility when None is passed
        volume_default = adapter.calculate_position_size(signal, balance, price, None)
        default_works = (volume_default > 0)

        print(f"         {CYAN}Default volatility works: {default_works}{RESET}")

        return valid_volume and hold_correct and default_works

    except Exception as e:
        print_result(5, "Position sizing", False, str(e))
        return False


def test_6_risk_management_limits():
    """Test 6: Risk management limits are enforced"""
    print_header("TEST 6: Risk Management Limits")

    adapter = LiveStrategyAdapter()

    try:
        signal = 1
        balance = 10000.0
        price = 1.10078
        volatility = 0.0001  # Very small volatility

        volume = adapter.calculate_position_size(signal, balance, price, volatility)

        # Check against max position size (10%)
        max_units = (balance * 0.1) / price
        within_limits = (volume <= max_units)

        print_result(
            6,
            "Risk management limits",
            within_limits,
            f"Volume: {volume:.4f}, Max: {max_units:.4f}"
        )
        return within_limits

    except Exception as e:
        print_result(6, "Risk management limits", False, str(e))
        return False


def test_7_metadata_generation():
    """Test 7: Metadata generation and retrieval"""
    print_header("TEST 7: Metadata Generation")

    adapter = LiveStrategyAdapter()

    try:
        metadata = adapter.get_metadata()

        # Check required keys
        required_keys = [
            'model_path', 'model_type', 'model_loaded',
            'threshold', 'feature_count', 'feature_names',
            'risk_config', 'timestamp'
        ]

        missing_keys = [k for k in required_keys if k not in metadata]

        success = (len(missing_keys) == 0)

        print_result(
            7,
            "Metadata generation",
            success,
            f"Keys: {list(metadata.keys())}"
        )

        if success:
            print(f"         Model: {metadata['model_path']}")
            print(f"         Type: {metadata['model_type']}")
            print(f"         Loaded: {metadata['model_loaded']}")
            print(f"         Threshold: {metadata['threshold']}")
            print(f"         Features: {metadata['feature_count']}")

        return success

    except Exception as e:
        print_result(7, "Metadata generation", False, str(e))
        return False


def main():
    """Run all tests"""
    print()
    print("=" * 80)
    print(f"{CYAN}🧪 STRATEGY ADAPTER VERIFICATION TESTS{RESET}")
    print(f"{CYAN}Task #020.01: Unified Strategy Adapter{RESET}")
    print("=" * 80)
    print()

    # Run all tests
    tests = [
        ("Adapter Initialization", test_1_adapter_initialization),
        ("Model Loading", test_2_model_loading),
        ("Signal Generation", test_3_signal_generation),
        ("Signal Consistency", test_4_signal_consistency),
        ("Position Sizing", test_5_position_sizing),
        ("Risk Management Limits", test_6_risk_management_limits),
        ("Metadata Generation", test_7_metadata_generation),
    ]

    results = []
    for i, (test_name, test_func) in enumerate(tests, 1):
        try:
            result = test_func()
            # Handle tuple returns
            if isinstance(result, tuple):
                result = result[0]
            results.append((test_name, result))
        except Exception as e:
            print(f"{RED}⚠️  Test {test_name} crashed: {e}{RESET}")
            results.append((test_name, False))

    # Summary
    print()
    print("=" * 80)
    print(f"📊 TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("=" * 80)
        print(f"{GREEN}✅ ALL TESTS PASSED - Adapter is ready{RESET}")
        print("=" * 80)
        print()
        return 0
    else:
        print("=" * 80)
        print(f"{RED}❌ SOME TESTS FAILED - Fix issues before deployment{RESET}")
        print("=" * 80)
        print()
        print("Failed tests:")
        for test_name, result in results:
            if not result:
                print(f"  - {test_name}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
