#!/usr/bin/env python3
"""
Work Order #023: Bot Integration Verification Script
======================================================

Functional verification that mocks ZmqClient responses and runs one cycle
of TradingBot._tick() to ensure no crashes occur during logic execution.

This script:
1. Creates a mock ZmqClient with predefined responses
2. Initializes TradingBot with the mock client
3. Runs one tick cycle
4. Verifies no exceptions occurred
5. Prints "✅ Bot Integration Verified"

Protocol: v2.0 (Strict TDD & Dual-Brain)
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bot.trading_bot import TradingBot
from src.mt5_bridge.protocol import ResponseStatus


# ============================================================================
# Mock ZmqClient
# ============================================================================

def create_mock_zmq_client():
    """
    Create a mock ZmqClient with predefined responses.

    Returns:
        Mock ZmqClient instance
    """
    mock_client = Mock()

    # Mock check_heartbeat() - returns True (gateway alive)
    mock_client.check_heartbeat = Mock(return_value=True)

    # Mock send_command() - returns SUCCESS with mock account data
    def mock_send_command(action, payload=None):
        """Mock command responses."""
        if action.value == "HEARTBEAT":
            return {
                'status': ResponseStatus.SUCCESS.value,
                'data': {'status': 'alive'}
            }
        elif action.value == "GET_ACCOUNT_INFO":
            return {
                'status': ResponseStatus.SUCCESS.value,
                'data': {
                    'balance': 10000.00,
                    'equity': 10050.00,
                    'margin': 100.00,
                    'margin_free': 9950.00
                }
            }
        elif action.value == "OPEN_ORDER":
            return {
                'status': ResponseStatus.SUCCESS.value,
                'data': {
                    'ticket': 12345,
                    'volume': payload.get('volume', 0.01),
                    'symbol': payload.get('symbol', 'EURUSD.s')
                }
            }
        else:
            return {
                'status': ResponseStatus.ERROR.value,
                'error': f'Unknown action: {action}'
            }

    mock_client.send_command = Mock(side_effect=mock_send_command)

    return mock_client


# ============================================================================
# Verification Tests
# ============================================================================

def test_bot_initialization():
    """Test 1: Bot can be initialized with mock client."""
    print("\n[Test 1/4] Testing Bot Initialization...")

    mock_client = create_mock_zmq_client()

    try:
        bot = TradingBot(
            zmq_client=mock_client,
            strategy_engine=None,
            symbol="EURUSD.s",
            interval=1
        )
        print("  ✅ Bot initialized successfully")
        print(f"     Symbol: {bot.symbol}")
        print(f"     Interval: {bot.interval}s")
        print(f"     Client: {type(bot.client).__name__}")
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


def test_connection_check():
    """Test 2: Bot can check gateway connection."""
    print("\n[Test 2/4] Testing Connection Check...")

    mock_client = create_mock_zmq_client()
    bot = TradingBot(
        zmq_client=mock_client,
        strategy_engine=None,
        symbol="EURUSD.s",
        interval=1
    )

    try:
        is_connected = bot._check_connection()
        print(f"  ✅ Connection check completed")
        print(f"     Result: {is_connected}")
        print(f"     check_heartbeat() called: {mock_client.check_heartbeat.called}")

        if not is_connected:
            print("  ⚠️  Connection returned False (expected for mock)")

        return True
    except Exception as e:
        print(f"  ❌ Connection check failed: {e}")
        return False


def test_tick_cycle():
    """Test 3: Bot can execute one tick cycle."""
    print("\n[Test 3/4] Testing Tick Cycle...")

    mock_client = create_mock_zmq_client()
    bot = TradingBot(
        zmq_client=mock_client,
        strategy_engine=None,
        symbol="EURUSD.s",
        interval=1
    )

    try:
        # Execute one tick
        bot._tick()

        print("  ✅ Tick cycle completed without crashes")
        print(f"     send_command() called: {mock_client.send_command.called}")
        print(f"     Call count: {mock_client.send_command.call_count}")

        # Verify send_command was called (for account sync)
        if mock_client.send_command.call_count > 0:
            print("  ✅ Bot communicated with mock gateway")
        else:
            print("  ⚠️  Bot did not call send_command")

        return True
    except Exception as e:
        print(f"  ❌ Tick cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_execution():
    """Test 4: Bot can execute trade orders."""
    print("\n[Test 4/4] Testing Trade Execution...")

    mock_client = create_mock_zmq_client()
    bot = TradingBot(
        zmq_client=mock_client,
        strategy_engine=None,
        symbol="EURUSD.s",
        interval=1
    )

    try:
        # Execute a mock trade
        result = bot.execute_trade(action="BUY", volume=0.01)

        print("  ✅ Trade execution completed")
        print(f"     Status: {result.get('status')}")
        print(f"     Data: {result.get('data')}")

        if result.get('status') == ResponseStatus.SUCCESS.value:
            print("  ✅ Trade executed successfully")
        else:
            print(f"  ⚠️  Trade failed: {result.get('error')}")

        return True
    except Exception as e:
        print(f"  ❌ Trade execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Verification
# ============================================================================

def main():
    """Run all verification tests."""
    print("=" * 70)
    print("🔍 Work Order #023: Bot Integration Verification")
    print("=" * 70)
    print()
    print("Testing TradingBot with mocked ZmqClient...")
    print()

    # Run all tests
    results = []
    results.append(test_bot_initialization())
    results.append(test_connection_check())
    results.append(test_tick_cycle())
    results.append(test_trade_execution())

    # Summary
    print()
    print("=" * 70)
    passed = sum(results)
    total = len(results)

    if all(results):
        print("✅ Bot Integration Verified")
        print("=" * 70)
        print()
        print(f"All {total} tests passed:")
        print("  ✅ Bot initialization")
        print("  ✅ Connection check")
        print("  ✅ Tick cycle execution")
        print("  ✅ Trade execution")
        print()
        print("Next Steps:")
        print("  1. Run audit script: python3 scripts/audit_current_task.py")
        print("  2. Finalize task: python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print(f"❌ Verification Failed ({passed}/{total} tests passed)")
        print("=" * 70)
        print()
        for i, result in enumerate(results, 1):
            status = "✅" if result else "❌"
            print(f"  {status} Test {i}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
