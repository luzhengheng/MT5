#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Verification Tests

Task #019.01: Signal Verification Dashboard

Tests dashboard components in headless mode without launching browser.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.reporting.log_parser import TradeLogParser

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


def print_result(name, success, message=""):
    """Print test result"""
    if success:
        print(f"{GREEN}✅ PASS{RESET}: {name}")
        if message:
            print(f"  {message}")
    else:
        print(f"{RED}❌ FAIL{RESET}: {name}")
        if message:
            print(f"  {message}")
    print()


def test_log_parser_import():
    """Test 1: Log Parser can be imported"""
    print_header("TEST 1: Log Parser Import")

    try:
        from src.reporting.log_parser import TradeLogParser
        print_result("Import TradeLogParser", True, "Module imported successfully")
        return True
    except Exception as e:
        print_result("Import TradeLogParser", False, f"Import error: {e}")
        return False


def test_parse_sample_log():
    """Test 2: Parse sample log file"""
    print_header("TEST 2: Parse Sample Log File")

    # Create sample log
    sample_log = PROJECT_ROOT / "logs" / "trading.log"

    if not sample_log.exists():
        print_result(
            "Parse log file",
            False,
            f"Log file not found: {sample_log}"
        )
        return False

    try:
        parser = TradeLogParser(str(sample_log))
        df = parser.parse_log()

        if df.empty:
            print_result("Parse log file", False, "No events parsed from log")
            return False

        # Check event types
        event_counts = df['event_type'].value_counts().to_dict()
        print_result(
            "Parse log file",
            True,
            f"Parsed {len(df)} events: {event_counts}"
        )
        return True

    except Exception as e:
        print_result("Parse log file", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ohlc_generation():
    """Test 3: OHLC generation"""
    print_header("TEST 3: OHLC Generation")

    sample_log = PROJECT_ROOT / "logs" / "trading.log"

    if not sample_log.exists():
        print_result("OHLC generation", False, "Log file not found")
        return False

    try:
        parser = TradeLogParser(str(sample_log))
        ohlc = parser.generate_ohlc(symbol='EURUSD', timeframe='1H')

        if ohlc.empty:
            print_result("OHLC generation", False, "No candles generated")
            return False

        # Verify columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [c for c in required_cols if c not in ohlc.columns]

        if missing_cols:
            print_result(
                "OHLC generation",
                False,
                f"Missing columns: {missing_cols}"
            )
            return False

        print_result(
            "OHLC generation",
            True,
            f"Generated {len(ohlc)} candles with columns: {list(ohlc.columns)}"
        )
        return True

    except Exception as e:
        print_result("OHLC generation", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_extraction():
    """Test 4: Trade extraction"""
    print_header("TEST 4: Trade Extraction")

    sample_log = PROJECT_ROOT / "logs" / "trading.log"

    if not sample_log.exists():
        print_result("Trade extraction", False, "Log file not found")
        return False

    try:
        parser = TradeLogParser(str(sample_log))
        trades = parser.extract_trades()

        # It's okay if no trades (log may not have fills)
        if trades.empty:
            print_result(
                "Trade extraction",
                True,
                "No completed trades (expected for simulation)"
            )
            return True

        # Verify columns
        required_cols = ['entry_time', 'entry_price', 'symbol', 'side', 'status']
        missing_cols = [c for c in required_cols if c not in trades.columns]

        if missing_cols:
            print_result(
                "Trade extraction",
                False,
                f"Missing columns: {missing_cols}"
            )
            return False

        print_result(
            "Trade extraction",
            True,
            f"Extracted {len(trades)} trades: "
            f"{len(trades[trades['status']=='OPEN'])} open, "
            f"{len(trades[trades['status']=='CLOSED'])} closed"
        )
        return True

    except Exception as e:
        print_result("Trade extraction", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_import():
    """Test 5: Streamlit app can be imported"""
    print_header("TEST 5: Streamlit App Import")

    try:
        import streamlit
        print_result("Streamlit import", True, f"Version: {streamlit.__version__}")

        # Try importing dashboard app module
        from src.dashboard import app
        print_result("Dashboard app import", True, "Module imported successfully")

        return True

    except ImportError as e:
        if 'streamlit' in str(e):
            print_result(
                "Streamlit import",
                False,
                "Streamlit not installed. Run: pip install streamlit"
            )
        else:
            print_result("Dashboard app import", False, f"Import error: {e}")
        return False
    except Exception as e:
        print_result("Dashboard app import", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summary_generation():
    """Test 6: Summary generation"""
    print_header("TEST 6: Summary Generation")

    sample_log = PROJECT_ROOT / "logs" / "trading.log"

    if not sample_log.exists():
        print_result("Summary generation", False, "Log file not found")
        return False

    try:
        parser = TradeLogParser(str(sample_log))
        summary = parser.get_summary()

        # Verify required keys
        required_keys = [
            'total_ticks', 'total_signals', 'buy_signals', 'sell_signals',
            'total_trades', 'win_rate', 'avg_pnl'
        ]
        missing_keys = [k for k in required_keys if k not in summary]

        if missing_keys:
            print_result(
                "Summary generation",
                False,
                f"Missing keys: {missing_keys}"
            )
            return False

        print_result(
            "Summary generation",
            True,
            f"Summary keys: {list(summary.keys())}"
        )
        print(f"    Total Ticks: {summary['total_ticks']}")
        print(f"    Total Signals: {summary['total_signals']}")
        print(f"    Total Trades: {summary['total_trades']}")
        print(f"    Win Rate: {summary['win_rate']:.1f}%")
        print()

        return True

    except Exception as e:
        print_result("Summary generation", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print()
    print("=" * 80)
    print(f"{CYAN}🧪 DASHBOARD VERIFICATION TESTS{RESET}")
    print(f"{CYAN}Task #019.01: Signal Verification Dashboard{RESET}")
    print("=" * 80)
    print()

    # Run all tests
    tests = [
        ("Log Parser Import", test_log_parser_import),
        ("Parse Sample Log", test_parse_sample_log),
        ("OHLC Generation", test_ohlc_generation),
        ("Trade Extraction", test_trade_extraction),
        ("Streamlit App Import", test_dashboard_import),
        ("Summary Generation", test_summary_generation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
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
        print(f"{GREEN}✅ ALL TESTS PASSED - Dashboard is ready{RESET}")
        print("=" * 80)
        print()
        print("You can now launch the dashboard:")
        print(f"  streamlit run src/dashboard/app.py")
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
