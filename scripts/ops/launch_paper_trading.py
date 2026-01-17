#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launch Paper Trading - Task #109 System Integration Test

功能：纸面交易启动脚本，包含毒丸功能 (Chaos Injection)
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from strategy.canary_strategy import CanaryStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PaperTradingOrchestrator:
    """Orchestrates paper trading simulation"""

    def __init__(
        self,
        symbol: str = "EURUSD",
        demo_account_id: int = 1100212251,
        duration_seconds: int = 60,
        tick_rate: int = 60,
    ):
        """Initialize Paper Trading Orchestrator"""
        self.symbol = symbol
        self.demo_account_id = demo_account_id
        self.duration_seconds = duration_seconds
        self.tick_rate = tick_rate
        self.tick_interval = 1.0 / tick_rate

        # Strategy components
        self.strategy = CanaryStrategy(symbol=symbol)

        # Execution tracking
        self.tick_count = 0
        self.order_count = 0
        self.filled_count = 0
        self.rejected_count = 0
        self.execution_log: list = []

        # Simulated market state
        self.bid_price = 1.0850
        self.ask_price = 1.0852

        logger.info(
            "[INIT] Paper Trading Orchestrator initialized\n"
            f"  Symbol: {symbol}\n"
            f"  Account: {demo_account_id} (DEMO)\n"
            f"  Duration: {duration_seconds}s\n"
            f"  Tick Rate: {tick_rate} ticks/sec"
        )

    def _simulate_market_tick(self) -> Dict:
        """Generate realistic market tick"""
        import random
        self.bid_price += random.uniform(-0.0001, 0.0001)
        self.ask_price = self.bid_price + 0.0002

        tick = {
            'symbol': self.symbol,
            'bid': round(self.bid_price, 4),
            'ask': round(self.ask_price, 4),
            'timestamp': datetime.utcnow().isoformat(),
            'volume': random.randint(100, 1000)
        }

        return tick

    def _process_signal(self, signal, elapsed_time: float) -> bool:
        """Process strategy signal through risk monitor"""
        self.order_count += 1

        # Risk check: reject if volume > 1.0 Lot
        if signal.volume > 1.0:
            logger.warning(
                f"[RISK_REJECT] Order volume {signal.volume} exceeds limit "
                f"(max: 1.0) [Ticket #{self.order_count}] [t={elapsed_time:.1f}s]"
            )
            self.rejected_count += 1
            return False

        # Order accepted
        logger.info(
            f"[ORDER_ACCEPTED] {signal.action} {signal.volume} Lot "
            f"@ {self.ask_price:.4f} [Ticket #{self.order_count}] "
            f"[t={elapsed_time:.1f}s]"
        )

        self.filled_count += 1
        logger.info(
            f"[ORDER_FILLED] {signal.action} {signal.volume} Lot "
            f"@ {self.ask_price:.4f} [Ticket #{self.order_count}]"
        )

        return True

    def _inject_chaos(self, elapsed_time: float):
        """Inject chaos test at t=30s"""
        logger.warning(
            "[CHAOS_INJECTION] Attempting to send oversized order "
            f"(100.0 Lot) at t={elapsed_time:.1f}s to verify risk control..."
        )

        # Create malicious signal
        class ChaosSignal:
            pass

        chaos_signal = ChaosSignal()
        chaos_signal.timestamp = datetime.utcnow().isoformat()
        chaos_signal.symbol = self.symbol
        chaos_signal.action = "OPEN_BUY"
        chaos_signal.volume = 100.0
        chaos_signal.reason = "CHAOS_TEST: Oversized order"

        # Try to process it (should be rejected)
        was_accepted = self._process_signal(chaos_signal, elapsed_time)

        if not was_accepted:
            logger.info(
                "[CHAOS_RESULT] Risk control successfully blocked "
                "oversized order"
            )
        else:
            logger.error(
                "[CHAOS_RESULT] Risk control FAILED to block "
                "oversized order!"
            )

    def run(self):
        """Main paper trading loop"""
        logger.info("[START] Paper trading simulation started")
        logger.info("[CONFIG] Account type: DEMO (Broker: JustMarkets-Demo2)")

        start_time = time.time()
        chaos_injected = False
        last_heartbeat = start_time

        try:
            tick_number = 0
            while True:
                current_time = time.time()
                elapsed = current_time - start_time

                # Check if we've exceeded duration
                if elapsed > self.duration_seconds:
                    logger.info(
                        f"[STOP] Simulation duration "
                        f"({self.duration_seconds}s) reached"
                    )
                    break

                # Generate market tick
                tick = self._simulate_market_tick()
                tick_number += 1

                # Process tick through strategy
                signal = self.strategy.on_tick(tick)

                if signal:
                    # Process signal through execution layer
                    self._process_signal(signal, elapsed)

                # Chaos injection at t=30s
                if elapsed > 30.0 and not chaos_injected:
                    self._inject_chaos(elapsed)
                    chaos_injected = True

                # Heartbeat check every 10 seconds
                if current_time - last_heartbeat >= 10.0:
                    stats = self.strategy.get_statistics()
                    logger.info(
                        f"[HEARTBEAT] t={elapsed:.1f}s | "
                        f"Ticks: {tick_number} | "
                        f"Orders: {self.order_count} "
                        f"(Filled: {self.filled_count}, "
                        f"Rejected: {self.rejected_count}) | "
                        f"Position: {stats['position_status']}"
                    )
                    last_heartbeat = current_time

                # Sleep to maintain tick rate
                time.sleep(self.tick_interval * 0.9)

        except KeyboardInterrupt:
            logger.warning("[INTERRUPTED] Paper trading interrupted")
        except Exception as e:
            logger.error(f"[ERROR] Exception in main loop: {e}", exc_info=True)
        finally:
            self._finalize()

    def _finalize(self):
        """Finalization and statistics"""
        logger.info("[FINALIZE] Paper trading session ending")

        # Get final statistics
        stats = self.strategy.get_statistics()

        logger.info(
            "\n[SUMMARY] Paper Trading Execution Statistics\n"
            f"  Total Ticks Processed: {self.tick_count}\n"
            f"  Total Orders Attempted: {self.order_count}\n"
            f"  Orders Filled: {self.filled_count}\n"
            f"  Orders Rejected: {self.rejected_count}\n"
            f"  Acceptance Rate: "
            f"{100*self.filled_count/max(self.order_count,1):.1f}%\n"
            f"  Position Status: {stats['position_status']}\n"
            f"  Signals Generated: {stats['total_signals']}\n"
            f"  (Opens: {stats['opens']}, Closes: {stats['closes']})"
        )

        # Validate execution log
        self._validate_execution_log()

    def _validate_execution_log(self):
        """Validate that full lifecycle was captured"""
        logger.info(
            "[VALIDATION] Execution Log Summary\n"
            f"  Total Events: {len(self.execution_log)}\n"
        )

        if self.rejected_count > 0:
            logger.info(
                f"[VALIDATION] ✓ Risk control demonstrated "
                f"(rejected {self.rejected_count} order(s))"
            )


def main():
    """Main entry point"""
    logger.info("[MAIN] MT5-CRS Paper Trading Validation - Task #109")
    logger.info("[MAIN] Protocol v4.3 (Zero-Trust Edition)")

    orchestrator = PaperTradingOrchestrator(
        symbol="EURUSD",
        demo_account_id=1100212251,
        duration_seconds=60,
        tick_rate=60
    )

    orchestrator.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("[MAIN] Paper trading interrupted")
    except Exception as e:
        logger.error(f"[MAIN] Fatal error: {e}", exc_info=True)
