#!/usr/bin/env python3
"""
Work Order #023: Live Trading Strategy Integration
====================================================

Trading Bot - The Conscious Loop (Brain Wakes Up)

This module integrates the ZmqClient (The Axon) with the TradingBot (The Brain),
creating a real-time "Heartbeat -> Decision -> Execution" loop that drives the
Windows Gateway.

Architecture:
- ZmqClient: Communication fabric to Windows Gateway
- TradingBot: Decision-making and execution orchestration
- Strategy Engine: Signal generation (optional, can be None for now)
- Main Loop: Continuous operation with graceful shutdown

Previous State (Work Order #022):
- ZeroMQ fabric established (ports 5555/5556)
- Windows Gateway listening and ready
- Linux Brain has functioning ZmqClient

Current Goal:
- Upgrade TradingBot to actively use ZmqClient
- Demonstrate "Heartbeat -> Decision -> Execution" loop
- Drive Windows Gateway from Linux Brain

Protocol: v2.0 (Strict TDD & Dual-Brain)
"""

import time
import logging
from typing import Optional, Dict, Any

from src.mt5_bridge.protocol import Action, ResponseStatus

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Trading Bot - The Conscious Loop
# ============================================================================

class TradingBot:
    """
    Trading Bot with ZeroMQ Integration (Work Order #023)

    The "conscious loop" that orchestrates trading decisions and executes
    them via the ZmqClient (The Axon) to the Windows Gateway.

    Architecture:
        Brain (Linux) -> ZmqClient (Axon) -> Windows Gateway -> MT5

    Core Loop:
        1. Heartbeat Check: Verify gateway connectivity
        2. Account Sync: Fetch account info from gateway
        3. Strategy Signal: Generate trading decision (placeholder)
        4. Trade Execution: Send orders via ZmqClient
        5. Sleep & Repeat

    Attributes:
        client (ZmqClient): The communication axon to Windows Gateway
        strategy: Strategy engine for signal generation (optional)
        symbol (str): Trading symbol (e.g., "EURUSD.s")
        interval (int): Loop interval in seconds
        running (bool): Control flag for main loop
    """

    def __init__(
        self,
        zmq_client,
        strategy_engine: Optional[Any] = None,
        symbol: str = "EURUSD.s",
        interval: int = 10
    ):
        """
        Initialize Trading Bot with ZmqClient integration.

        Args:
            zmq_client: ZmqClient instance (The Axon)
            strategy_engine: Optional strategy for signal generation
            symbol: Trading symbol (default: "EURUSD.s")
            interval: Loop interval in seconds (default: 10)

        Example:
            >>> from src.mt5_bridge import ZmqClient
            >>> client = ZmqClient(host="172.19.141.255")
            >>> bot = TradingBot(zmq_client=client)
            >>> bot.start()
        """
        self.client = zmq_client
        self.strategy = strategy_engine
        self.symbol = symbol
        self.interval = interval
        self.running = False

        logger.info(
            f"🤖 TradingBot initialized "
            f"(symbol={symbol}, interval={interval}s)"
        )

    # ========================================================================
    # Main Control Loop
    # ========================================================================

    def start(self):
        """
        Start the trading bot main loop.

        Loop Sequence:
            1. Check connection (heartbeat)
            2. Run tick cycle (account sync + decision + execution)
            3. Sleep for interval
            4. Repeat until stopped

        Handles:
            - KeyboardInterrupt: Graceful shutdown
            - Exceptions: Log error and continue (5-second backoff)

        Example:
            >>> bot = TradingBot(zmq_client=client)
            >>> bot.start()  # Blocks until KeyboardInterrupt
        """
        logger.info(f"🚀 Starting Trading Bot for {self.symbol}...")
        self.running = True

        # Initial connection check
        if not self._check_connection():
            logger.critical("❌ Connection Failed - Cannot start bot")
            return

        logger.info("✅ Gateway connection verified")
        logger.info(f"⏱️  Loop interval: {self.interval} seconds")
        logger.info("🔄 Entering main trading loop...")
        print()

        # Main trading loop
        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"{'='*60}")
                logger.info(f"🔄 Cycle #{cycle_count} starting...")

                # Execute one tick
                self._tick()

                # Wait for next cycle
                logger.info(f"⏳ Waiting {self.interval} seconds...")
                time.sleep(self.interval)

            except KeyboardInterrupt:
                # Graceful shutdown requested
                logger.info("\n🛑 KeyboardInterrupt received")
                self.stop()
                break

            except Exception as e:
                # Error in cycle - log and continue with backoff
                logger.error(f"❌ Loop Error: {e}")
                import traceback
                traceback.print_exc()
                logger.info("⏳ Backing off 5 seconds before retry...")
                time.sleep(5)

        logger.info(f"🏁 Trading Bot stopped after {cycle_count} cycles")

    def stop(self):
        """
        Stop the trading bot gracefully.

        Sets running flag to False, which will exit the main loop
        on the next iteration.

        Example:
            >>> bot.stop()
        """
        logger.info("🛑 Stopping Bot...")
        self.running = False

    # ========================================================================
    # Connection Management
    # ========================================================================

    def _check_connection(self) -> bool:
        """
        Verify connection to Windows Gateway via heartbeat.

        Returns:
            True if gateway responds to heartbeat
            False if gateway is unreachable

        Example:
            >>> if bot._check_connection():
            ...     print("Gateway is alive")
        """
        logger.info("🔍 Checking gateway connection...")

        try:
            is_alive = self.client.check_heartbeat()

            if is_alive:
                logger.info("✅ Gateway heartbeat: OK")
            else:
                logger.error("❌ Gateway heartbeat: FAILED")

            return is_alive

        except Exception as e:
            logger.error(f"❌ Connection check error: {e}")
            return False

    # ========================================================================
    # Trading Cycle (The Tick)
    # ========================================================================

    def _tick(self):
        """
        Execute one trading cycle (tick).

        Workflow:
            1. Sync account info from gateway
            2. Log current balance/equity
            3. [Placeholder] Generate strategy signal
            4. [Placeholder] Execute trade if signal present

        This is the "conscious moment" where the bot:
        - Perceives (account sync)
        - Decides (strategy signal)
        - Acts (trade execution)

        Note:
            Strategy integration is a placeholder for now.
            Work Order #024 will add real strategy logic.
        """
        logger.info("📡 Syncing account info...")

        # Step 1: Fetch account info from gateway
        try:
            response = self.client.send_command(Action.GET_ACCOUNT_INFO)

            if response.get('status') == ResponseStatus.SUCCESS.value:
                account_data = response.get('data', {})
                balance = account_data.get('balance', 'N/A')
                equity = account_data.get('equity', 'N/A')
                margin = account_data.get('margin', 'N/A')

                logger.info(
                    f"💰 Pulse. Balance: {balance}, "
                    f"Equity: {equity}, Margin: {margin}"
                )
            else:
                error_msg = response.get('error', 'Unknown error')
                logger.warning(f"⚠️  Account sync failed: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Account sync error: {e}")

        # Step 2: Strategy signal generation (placeholder)
        # TODO: Work Order #024 will integrate real strategy
        if self.strategy:
            logger.debug("🧠 Strategy analysis (placeholder)...")
            # signal = self.strategy.analyze(...)
            # if signal == 'BUY': self.execute_trade('BUY', 0.01)
        else:
            logger.debug("🧠 No strategy engine configured")

        logger.info("✅ Tick completed")

    # ========================================================================
    # Trade Execution
    # ========================================================================

    def execute_trade(
        self,
        action: str,
        volume: float,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0
    ) -> Dict[str, Any]:
        """
        Execute a trade order via ZmqClient.

        Args:
            action: Trade action ("BUY" or "SELL")
            volume: Trade volume (lots)
            price: Entry price (0.0 for market order)
            sl: Stop loss price (optional)
            tp: Take profit price (optional)

        Returns:
            Response from gateway with order details

        Example:
            >>> result = bot.execute_trade(action="BUY", volume=0.01)
            >>> if result['status'] == 'SUCCESS':
            ...     print(f"Order placed: {result['data']['ticket']}")
        """
        logger.info(
            f"📤 Executing trade: {action} {volume} lots of {self.symbol}"
        )

        payload = {
            "symbol": self.symbol,
            "action": action,
            "volume": volume,
            "price": price,
            "sl": sl,
            "tp": tp
        }

        try:
            response = self.client.send_command(Action.OPEN_ORDER, payload)

            if response.get('status') == ResponseStatus.SUCCESS.value:
                logger.info(f"✅ Trade executed: {response.get('data')}")
            else:
                error_msg = response.get('error', 'Unknown error')
                logger.error(f"❌ Trade failed: {error_msg}")

            return response

        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return {
                'status': ResponseStatus.ERROR.value,
                'error': str(e)
            }


# ============================================================================
# Convenience Factory
# ============================================================================

def get_trading_bot(zmq_client, **kwargs) -> TradingBot:
    """
    Create and return TradingBot instance.

    Args:
        zmq_client: ZmqClient instance (required)
        **kwargs: Additional parameters passed to TradingBot

    Returns:
        TradingBot instance

    Example:
        >>> from src.mt5_bridge import get_zmq_client
        >>> client = get_zmq_client()
        >>> bot = get_trading_bot(zmq_client=client, symbol="GBPUSD.s")
    """
    return TradingBot(zmq_client=zmq_client, **kwargs)


# ============================================================================
# Direct Execution (for testing)
# ============================================================================

if __name__ == "__main__":
    # This is for manual testing only
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("🤖 TradingBot - Direct Execution Mode")
    print("=" * 70)
    print()
    print("⚠️  This requires:")
    print("  1. Windows Gateway running on 172.19.141.255")
    print("  2. ZMQ ports 5555/5556 accessible")
    print()
    print("To test, run:")
    print("  python3 src/main.py")
    print()
    print("=" * 70)
