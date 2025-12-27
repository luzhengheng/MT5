#!/usr/bin/env python3
"""
Audit Script for Task #023: Live Trading Strategy Integration
===============================================================

Structural audit to verify Work Order #023 implementation.

This audit ensures:
1. File existence (src/bot/trading_bot.py, src/main.py)
2. Code structure (TradingBot.__init__ accepts zmq_client)
3. Import verification (src/main.py imports ZmqClient)
4. Unit test (Mock ZmqClient and assert TradingBot calls check_heartbeat())

Critical TDD Requirement:
- The finish command runs this audit first
- If this audit fails, the task will fail validation
- All assertions must pass for task completion

Protocol: v2.0 (Strict TDD & Dual-Brain)
"""

import sys
import os
import unittest
import inspect
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Audit Test Suite
# ============================================================================

class TestTask023Integration(unittest.TestCase):
    """
    Comprehensive audit for Work Order #023.
    """

    # ========================================================================
    # Test 1: File Existence
    # ========================================================================

    def test_file_existence(self):
        """Verify required files exist."""
        print("\n[Test 1/5] Checking File Existence...")

        # Check src/bot/trading_bot.py
        bot_file = PROJECT_ROOT / "src" / "bot" / "trading_bot.py"
        self.assertTrue(bot_file.exists(), "src/bot/trading_bot.py must exist")
        print("  ✅ src/bot/trading_bot.py exists")

        # Check src/main.py
        main_file = PROJECT_ROOT / "src" / "main.py"
        self.assertTrue(main_file.exists(), "src/main.py must exist")
        print("  ✅ src/main.py exists")

    # ========================================================================
    # Test 2: TradingBot Structure
    # ========================================================================

    def test_trading_bot_structure(self):
        """Verify TradingBot class structure."""
        print("\n[Test 2/5] Checking TradingBot Structure...")

        from src.bot.trading_bot import TradingBot

        # Check TradingBot class exists
        self.assertTrue(inspect.isclass(TradingBot), "TradingBot must be a class")
        print("  ✅ TradingBot class exists")

        # Check __init__ signature
        init_sig = inspect.signature(TradingBot.__init__)
        params = list(init_sig.parameters.keys())

        self.assertIn('zmq_client', params, "TradingBot.__init__ must accept zmq_client")
        print("  ✅ TradingBot.__init__ accepts 'zmq_client' parameter")

        # Check for required methods
        self.assertTrue(hasattr(TradingBot, 'start'), "TradingBot must have start() method")
        print("  ✅ TradingBot.start() method exists")

        self.assertTrue(hasattr(TradingBot, '_tick'), "TradingBot must have _tick() method")
        print("  ✅ TradingBot._tick() method exists")

        self.assertTrue(hasattr(TradingBot, '_check_connection'), "TradingBot must have _check_connection() method")
        print("  ✅ TradingBot._check_connection() method exists")

    # ========================================================================
    # Test 3: main.py Imports
    # ========================================================================

    def test_main_imports(self):
        """Verify src/main.py imports ZmqClient."""
        print("\n[Test 3/5] Checking main.py Imports...")

        main_file = PROJECT_ROOT / "src" / "main.py"
        content = main_file.read_text()

        # Check for ZmqClient import
        self.assertIn('from src.mt5_bridge.zmq_client import ZmqClient', content,
                      "main.py must import ZmqClient")
        print("  ✅ main.py imports ZmqClient")

        # Check for TradingBot import
        self.assertIn('from src.bot.trading_bot import TradingBot', content,
                      "main.py must import TradingBot")
        print("  ✅ main.py imports TradingBot")

        # Check for ZmqClient instantiation
        self.assertIn('ZmqClient(', content,
                      "main.py must instantiate ZmqClient")
        print("  ✅ main.py instantiates ZmqClient")

        # Check for TradingBot instantiation with zmq_client
        self.assertIn('zmq_client=', content,
                      "main.py must pass zmq_client to TradingBot")
        print("  ✅ main.py passes zmq_client to TradingBot")

    # ========================================================================
    # Test 4: Unit Test with Mock ZmqClient
    # ========================================================================

    def test_bot_with_mock_client(self):
        """Mock ZmqClient and assert TradingBot calls check_heartbeat()."""
        print("\n[Test 4/5] Testing Bot with Mock ZmqClient...")

        from src.bot.trading_bot import TradingBot

        # Create mock client
        mock_client = Mock()
        mock_client.check_heartbeat = Mock(return_value=True)

        # Initialize bot
        bot = TradingBot(
            zmq_client=mock_client,
            strategy_engine=None,
            symbol="EURUSD.s",
            interval=1
        )

        print("  ✅ Bot initialized with mock client")

        # Verify bot has client
        self.assertEqual(bot.client, mock_client, "Bot must store zmq_client")
        print("  ✅ Bot stores zmq_client reference")

        # Call _check_connection and verify it calls check_heartbeat()
        result = bot._check_connection()

        self.assertTrue(mock_client.check_heartbeat.called,
                        "Bot must call client.check_heartbeat()")
        print("  ✅ Bot calls client.check_heartbeat()")

        self.assertTrue(result, "_check_connection() should return True for mock")
        print("  ✅ _check_connection() returns True")

    # ========================================================================
    # Test 5: Integration Verification
    # ========================================================================

    def test_integration_components(self):
        """Verify integration components work together."""
        print("\n[Test 5/5] Testing Integration Components...")

        from src.bot.trading_bot import TradingBot
        from src.mt5_bridge.protocol import Action, ResponseStatus

        # Create mock client with full command support
        mock_client = Mock()
        mock_client.check_heartbeat = Mock(return_value=True)
        mock_client.send_command = Mock(return_value={
            'status': ResponseStatus.SUCCESS.value,
            'data': {'balance': 10000.00}
        })

        # Initialize bot
        bot = TradingBot(
            zmq_client=mock_client,
            strategy_engine=None,
            symbol="EURUSD.s",
            interval=1
        )

        print("  ✅ Bot initialized")

        # Run one tick cycle
        try:
            bot._tick()
            print("  ✅ Tick cycle executed without errors")
        except Exception as e:
            self.fail(f"Tick cycle failed: {e}")

        # Verify send_command was called
        self.assertTrue(mock_client.send_command.called,
                        "Bot must call client.send_command() during tick")
        print("  ✅ Bot calls client.send_command()")

        # Verify Action.GET_ACCOUNT_INFO was used
        call_args = mock_client.send_command.call_args
        if call_args:
            action_arg = call_args[0][0] if call_args[0] else None
            if action_arg:
                self.assertEqual(action_arg, Action.GET_ACCOUNT_INFO,
                                 "Bot should use Action.GET_ACCOUNT_INFO")
                print("  ✅ Bot uses Action.GET_ACCOUNT_INFO")


# ============================================================================
# Main Audit Execution
# ============================================================================

def main():
    """Run the audit suite."""
    print("=" * 70)
    print("🛡️  AUDIT: Work Order #023 - Live Trading Strategy Integration")
    print("=" * 70)
    print()
    print("Components under audit:")
    print("  1. src/bot/trading_bot.py")
    print("  2. src/main.py")
    print("  3. Integration with ZmqClient")
    print()

    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    suite = unittest.makeSuite(TestTask023Integration)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ AUDIT PASSED - All checks successful")
        print("=" * 70)
        print()
        print("Verified Components:")
        print("  ✅ File existence (trading_bot.py, main.py)")
        print("  ✅ TradingBot structure (zmq_client parameter)")
        print("  ✅ main.py imports (ZmqClient, TradingBot)")
        print("  ✅ Mock unit test (check_heartbeat() called)")
        print("  ✅ Integration test (tick cycle execution)")
        print()
        print("Next Steps:")
        print("  1. Verify: python3 scripts/verify_bot_integration.py")
        print("  2. Finalize: python3 scripts/project_cli.py finish")
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
