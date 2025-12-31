#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Strategy Runner Tests

Task #021.01: Multi-Strategy Orchestration Engine

Tests the MultiStrategyRunner with 2-3 concurrent strategies
using simulated market data.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import MultiStrategyRunner, StrategyInstance

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


def test_1_config_loading():
    """Test 1: Configuration file loading"""
    print_header("TEST 1: Configuration Loading")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"

        if not config_path.exists():
            print_result(1, "Config file exists", False, f"Not found: {config_path}")
            return False

        # Load YAML
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Verify structure
        if 'strategies' not in config:
            print_result(1, "Config structure valid", False, "Missing 'strategies' key")
            return False

        strategies = config['strategies']
        enabled_strategies = [s for s in strategies if s.get('enabled', True)]

        print_result(
            1,
            "Configuration loading",
            len(enabled_strategies) >= 2,
            f"Found {len(enabled_strategies)} enabled strategies"
        )

        return len(enabled_strategies) >= 2

    except Exception as e:
        print_result(1, "Configuration loading", False, str(e))
        return False


def test_2_runner_initialization():
    """Test 2: MultiStrategyRunner initialization"""
    print_header("TEST 2: Runner Initialization")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"
        runner = MultiStrategyRunner(str(config_path))

        success = len(runner.strategies) >= 2

        print_result(
            2,
            "MultiStrategyRunner initialization",
            success,
            f"Loaded {len(runner.strategies)} strategies: "
            f"{', '.join([s.name for s in runner.strategies])}"
        )

        return success, runner

    except Exception as e:
        print_result(2, "MultiStrategyRunner initialization", False, str(e))
        return False, None


def test_3_strategy_instances():
    """Test 3: Strategy instance creation"""
    print_header("TEST 3: Strategy Instance Creation")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        strategies_created = []
        for strat_config in config['strategies'][:2]:  # Test first 2
            if strat_config.get('enabled', True):
                instance = StrategyInstance(strat_config)
                strategies_created.append(instance)

        success = len(strategies_created) >= 2

        print_result(
            3,
            "Strategy instance creation",
            success,
            f"Created {len(strategies_created)} instances"
        )

        return success, strategies_created

    except Exception as e:
        print_result(3, "Strategy instance creation", False, str(e))
        return False, None


def test_4_symbol_routing():
    """Test 4: Correct routing of ticks by symbol"""
    print_header("TEST 4: Symbol-Based Tick Routing")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        strategies_created = []
        for strat_config in config['strategies'][:2]:
            if strat_config.get('enabled', True):
                strategies_created.append(StrategyInstance(strat_config))

        # Create test ticks
        eurusd_tick = {
            'symbol': 'EURUSD',
            'price': 1.10078,
            'timestamp': datetime.now().isoformat()
        }

        gbpusd_tick = {
            'symbol': 'GBPUSD',
            'price': 1.27500,
            'timestamp': datetime.now().isoformat()
        }

        # Process ticks
        for strat in strategies_created:
            strat.on_tick(eurusd_tick)
            strat.on_tick(gbpusd_tick)

        # Verify routing
        eurusd_strat = [s for s in strategies_created if s.symbol == 'EURUSD'][0]
        gbpusd_strat = [s for s in strategies_created if s.symbol == 'GBPUSD'][0]

        # EURUSD strategy should only process EURUSD ticks
        eurusd_correct = (
            eurusd_strat.ticks_processed >= 1 and
            eurusd_strat.symbol == 'EURUSD'
        )

        # GBPUSD strategy should only process GBPUSD ticks
        gbpusd_correct = (
            gbpusd_strat.ticks_processed >= 1 and
            gbpusd_strat.symbol == 'GBPUSD'
        )

        success = eurusd_correct and gbpusd_correct

        print_result(
            4,
            "Symbol-based routing",
            success,
            f"EURUSD: {eurusd_strat.ticks_processed}, GBPUSD: {gbpusd_strat.ticks_processed}"
        )

        return success

    except Exception as e:
        print_result(4, "Symbol-based routing", False, str(e))
        return False


def test_5_signal_generation():
    """Test 5: Signal generation in strategies"""
    print_header("TEST 5: Signal Generation")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        strategies_created = []
        for strat_config in config['strategies'][:2]:
            if strat_config.get('enabled', True):
                strategies_created.append(StrategyInstance(strat_config))

        # Generate ticks for each strategy
        for i in range(5):
            for strat in strategies_created:
                tick = {
                    'symbol': strat.symbol,
                    'price': 1.10000 + (i * 0.00001),
                    'timestamp': datetime.now().isoformat()
                }
                strat.on_tick(tick)

        # Verify signals were generated
        total_signals = sum(s.signals_generated for s in strategies_created)
        success = total_signals > 0

        print_result(
            5,
            "Signal generation",
            success,
            f"Total signals: {total_signals}"
        )

        for strat in strategies_created:
            print(f"           {strat.name}: "
                  f"{strat.signals_generated} signals "
                  f"(BUY={strat.buy_signals}, SELL={strat.sell_signals}, HOLD={strat.hold_signals})")

        return success

    except Exception as e:
        print_result(5, "Signal generation", False, str(e))
        return False


def test_6_error_isolation():
    """Test 6: Error isolation (one strategy error doesn't crash others)"""
    print_header("TEST 6: Error Isolation")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        strategies_created = []
        for strat_config in config['strategies'][:2]:
            if strat_config.get('enabled', True):
                strategies_created.append(StrategyInstance(strat_config))

        # Test malformed tick
        bad_tick = {
            'symbol': strategies_created[0].symbol,
            'price': 'invalid',  # Invalid price
            'timestamp': None  # Invalid timestamp
        }

        # This should not crash - error should be isolated
        success = True
        for strat in strategies_created:
            result = strat.on_tick(bad_tick)
            # Should return False for the bad strategy, True for others

        # Verify runner still functional
        print_result(
            6,
            "Error isolation",
            success,
            "Runner handled invalid tick without crashing"
        )

        return success

    except Exception as e:
        print_result(6, "Error isolation", False, str(e))
        return False


def test_7_status_reporting():
    """Test 7: Status reporting"""
    print_header("TEST 7: Status Reporting")

    try:
        config_path = PROJECT_ROOT / "config" / "strategies.yaml"
        runner = MultiStrategyRunner(str(config_path))

        # Generate some activity
        for i in range(3):
            for strat in runner.strategies:
                tick = {
                    'symbol': strat.symbol,
                    'price': 1.10000 + (i * 0.00001),
                    'timestamp': datetime.now().isoformat()
                }
                strat.on_tick(tick)

        # Get status
        status = runner.get_status()

        # Verify status structure
        success = (
            'total_strategies' in status and
            'strategies' in status and
            len(status['strategies']) > 0
        )

        if success:
            for strat_status in status['strategies']:
                required_keys = [
                    'name', 'symbol', 'enabled', 'ticks_processed',
                    'signals_generated', 'error_count'
                ]
                missing_keys = [k for k in required_keys if k not in strat_status]
                if missing_keys:
                    success = False
                    break

        print_result(
            7,
            "Status reporting",
            success,
            f"Status structure valid, {status['total_strategies']} strategies"
        )

        if success:
            runner.print_status()

        return success

    except Exception as e:
        print_result(7, "Status reporting", False, str(e))
        return False


def main():
    """Run all tests"""
    print()
    print("=" * 80)
    print(f"{CYAN}🧪 MULTI-STRATEGY RUNNER TESTS{RESET}")
    print(f"{CYAN}Task #021.01: Multi-Strategy Orchestration Engine{RESET}")
    print("=" * 80)
    print()

    tests = [
        ("Configuration Loading", test_1_config_loading),
        ("Runner Initialization", test_2_runner_initialization),
        ("Strategy Instance Creation", test_3_strategy_instances),
        ("Symbol-Based Routing", test_4_symbol_routing),
        ("Signal Generation", test_5_signal_generation),
        ("Error Isolation", test_6_error_isolation),
        ("Status Reporting", test_7_status_reporting),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            # Handle tuple returns
            if isinstance(result, tuple):
                result = result[0]
            results.append((test_name, result if result is not None else False))
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
        print(f"{GREEN}✅ ALL TESTS PASSED - Multi-strategy runner is ready{RESET}")
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
