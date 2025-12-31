#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Strategy Runner - Orchestrator for Multiple Concurrent Strategies

Task #021.01: Multi-Strategy Orchestration Engine

Manages multiple StrategyInstance objects running concurrently, routing
market data by symbol and isolating errors between strategies.

Architecture:
    Market Data (ZMQ) -> MultiStrategyRunner -> [StrategyInstance, StrategyInstance, ...]
                            ^
                            |
                         YAML Config
"""

import logging
import time
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.main.strategy_instance import StrategyInstance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / 'trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class MultiStrategyRunner:
    """
    Orchestrator for managing multiple concurrent trading strategies.

    Responsibilities:
    1. Load strategy configurations from YAML
    2. Instantiate StrategyInstance for each strategy
    3. Subscribe to market data (ZMQ PUB/SUB)
    4. Route ticks to appropriate strategies by symbol
    5. Isolate errors: one strategy failure doesn't crash others
    6. Provide unified logging and monitoring
    7. Handle graceful shutdown of all strategies

    Architecture:
        ZMQ Subscriber (port 5556)
            ↓
        [Route by Symbol]
            ↓
        [Strategy 1, Strategy 2, Strategy 3, ...]
            ↓
        [Independent Processing]
            ↓
        [Error Isolation]
    """

    def __init__(self, config_path: str):
        """
        Initialize runner with strategy configuration.

        Args:
            config_path: Path to strategies.yaml configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load YAML configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.global_config = config.get('global', {})
        self.strategies: List[StrategyInstance] = []

        # Instantiate enabled strategies
        for strat_config in config.get('strategies', []):
            if strat_config.get('enabled', True):
                try:
                    instance = StrategyInstance(strat_config)
                    self.strategies.append(instance)
                except Exception as e:
                    logger.error(
                        f"{RED}❌ Failed to initialize strategy {strat_config.get('name')}: {e}{RESET}"
                    )

        logger.info(
            f"{GREEN}✅ MultiStrategyRunner initialized{RESET}"
        )
        logger.info(
            f"   Loaded {len(self.strategies)} enabled strategies"
        )

        for strat in self.strategies:
            logger.info(f"   - {strat.name} ({strat.symbol})")

    def run(self, duration_seconds: int = 60):
        """
        Main event loop. Subscribe to ZMQ market data and dispatch to strategies.

        Args:
            duration_seconds: How long to run (0 = infinite)

        Architecture:
        1. Connect to ZMQ PUB/SUB
        2. Subscribe to symbols of all strategies
        3. Poll for incoming ticks
        4. Route each tick to matching strategies
        5. Isolate errors and log failures
        6. Clean shutdown after duration
        """
        try:
            import zmq

            context = zmq.Context()
            subscriber = context.socket(zmq.SUB)

            # Connect to market data publisher
            zmq_url = self.global_config.get('zmq_market_url', 'tcp://localhost:5556')
            logger.info(f"{CYAN}🔌 Connecting to market data: {zmq_url}{RESET}")

            subscriber.connect(zmq_url)

            # Subscribe to all relevant symbols
            for strat in self.strategies:
                subscriber.setsockopt_string(zmq.SUBSCRIBE, strat.symbol)
                logger.info(f"   ✅ Subscribed to {strat.symbol}")

            logger.info(f"{GREEN}✅ Market data subscription ready{RESET}")

            # Main event loop
            logger.info(f"{CYAN}🔄 Entering main loop ({duration_seconds}s)...{RESET}")
            start_time = time.time()

            ticks_received = 0
            errors_encountered = 0

            while True:
                # Check duration
                if duration_seconds > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= duration_seconds:
                        logger.info(f"{YELLOW}⏰ Duration limit reached{RESET}")
                        break

                # Poll for market data (timeout 1 second)
                try:
                    if subscriber.poll(1000):
                        message = subscriber.recv_string()

                        # Parse message: "SYMBOL json_data"
                        try:
                            parts = message.split(' ', 1)
                            if len(parts) != 2:
                                continue

                            symbol, json_data = parts
                            tick = json.loads(json_data)

                            ticks_received += 1

                            # Route to matching strategies
                            for strat in self.strategies:
                                if strat.symbol == symbol:
                                    try:
                                        success = strat.on_tick(tick)
                                        if not success:
                                            logger.warning(
                                                f"{YELLOW}⚠️  {strat.name} failed to process tick{RESET}"
                                            )
                                            errors_encountered += 1

                                    except Exception as e:
                                        logger.error(
                                            f"{RED}❌ Uncaught error in {strat.name}: {e}{RESET}"
                                        )
                                        errors_encountered += 1

                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"{YELLOW}⚠️  Failed to parse message: {e}{RESET}")

                except zmq.Again:
                    # Timeout, continue polling
                    pass

        except Exception as e:
            logger.error(f"{RED}❌ Runner error: {e}{RESET}")

        finally:
            self._shutdown_all()
            logger.info(f"   Ticks received: {ticks_received}")
            logger.info(f"   Errors encountered: {errors_encountered}")

    def _shutdown_all(self):
        """Gracefully shutdown all strategies."""
        logger.info(f"{CYAN}🛑 Shutting down all strategies...{RESET}")

        for strat in self.strategies:
            try:
                strat.shutdown()
            except Exception as e:
                logger.error(
                    f"{RED}❌ Shutdown error for {strat.name}: {e}{RESET}"
                )

        logger.info(f"{GREEN}✅ All strategies shut down{RESET}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all strategies.

        Returns:
            Dictionary with:
            - total_strategies: Number of loaded strategies
            - strategies: List of status dicts for each strategy
        """
        return {
            'total_strategies': len(self.strategies),
            'strategies': [s.get_status() for s in self.strategies]
        }

    def print_status(self):
        """Print formatted status report."""
        print()
        print("=" * 80)
        print("📊 MULTI-STRATEGY RUNNER STATUS")
        print("=" * 80)
        print()

        status = self.get_status()

        print(f"Total Strategies: {status['total_strategies']}")
        print()

        for strat_status in status['strategies']:
            print(f"Strategy: {strat_status['name']}")
            print(f"  Symbol: {strat_status['symbol']}")
            print(f"  Enabled: {strat_status['enabled']}")
            print(f"  Ticks: {strat_status['ticks_processed']}")
            print(f"  Signals: {strat_status['signals_generated']} "
                  f"(BUY={strat_status['buy_signals']}, "
                  f"SELL={strat_status['sell_signals']}, "
                  f"HOLD={strat_status['hold_signals']})")
            print(f"  Last Tick: {strat_status['last_tick_time']}")
            print(f"  Errors: {strat_status['error_count']}")
            print()

        print("=" * 80)


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("🤖 MultiStrategyRunner - Task #021.01")
    print("=" * 80)
    print()

    print("This module provides the MultiStrategyRunner for orchestrating")
    print("multiple concurrent trading strategies.")
    print()

    print("To run multi-strategy simulation:")
    print("  python3 scripts/test_multi_strategy.py")
    print()

    print("Or programmatically:")
    print("  runner = MultiStrategyRunner('config/strategies.yaml')")
    print("  runner.run(duration_seconds=60)")
    print()

    print("=" * 80)
