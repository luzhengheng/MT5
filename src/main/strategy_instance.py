#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Instance - Isolated Execution Context

Task #021.01: Multi-Strategy Orchestration Engine

Wrapper around TradingBot with isolated execution context. Each instance:
- Has its own LiveStrategyAdapter
- Maintains independent state
- Executes independently
- Logs separately
- Fails gracefully without affecting others
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.strategy import LiveStrategyAdapter

# Configure logging
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class StrategyInstance:
    """
    Isolated execution context for a single strategy.

    Responsibilities:
    - Encapsulate strategy configuration and state
    - Manage its own LiveStrategyAdapter
    - Process market ticks independently
    - Track metrics and errors
    - Fail gracefully without affecting other strategies
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy instance from configuration.

        Args:
            config: Dictionary with:
                - name: Strategy identifier
                - symbol: Trading symbol (e.g., 'EURUSD')
                - model_path: Path to XGBoost model
                - enabled: Whether strategy is active
                - threshold: Probability threshold for signals
                - risk_config: Risk management parameters
        """
        self.config = config
        self.name = config['name']
        self.symbol = config['symbol']
        self.enabled = config.get('enabled', True)

        # Initialize adapter with custom configuration
        self.adapter = LiveStrategyAdapter(
            model_path=config['model_path'],
            threshold=config.get('threshold', 0.5),
            risk_config=config.get('risk_config', {})
        )

        # Metrics and state
        self.signals_generated = 0
        self.buy_signals = 0
        self.sell_signals = 0
        self.hold_signals = 0
        self.ticks_processed = 0
        self.errors = []
        self.last_tick_time = None
        self.last_signal = 0
        self.last_signal_time = None

        logger.info(
            f"{GREEN}✅ Strategy {self.name} initialized{RESET}"
        )
        logger.info(
            f"   Symbol: {self.symbol}"
        )
        logger.info(
            f"   Model: {self.adapter.model_type}"
        )
        logger.info(
            f"   Threshold: {self.adapter.threshold}"
        )

    def on_tick(self, tick: Dict[str, Any]) -> bool:
        """
        Process market tick. Returns True if successful, False on error.

        Args:
            tick: Dictionary with:
                - symbol: Trading symbol
                - timestamp: Tick timestamp
                - price: Current market price
                - [other tick data]

        Returns:
            bool: True if processed successfully, False on error
        """
        try:
            # Skip if strategy disabled
            if not self.enabled:
                return True

            # Skip if not for this strategy's symbol
            if tick.get('symbol') != self.symbol:
                return True

            # Track tick processing
            self.ticks_processed += 1
            self.last_tick_time = tick.get('timestamp', datetime.now().isoformat())

            # Mock feature generation (in real system, would fetch from API)
            # For now, generate random features for testing
            import numpy as np
            features = np.random.randn(1, 18)

            # Generate signal using adapter
            signal = self.adapter.generate_signal(features)

            # Track signal
            self.signals_generated += 1
            if signal == 1:
                self.buy_signals += 1
            elif signal == -1:
                self.sell_signals += 1
            else:
                self.hold_signals += 1

            self.last_signal = signal
            self.last_signal_time = self.last_tick_time

            # Log signal
            signal_name = "BUY" if signal == 1 else ("SELL" if signal == -1 else "HOLD")
            logger.debug(
                f"{CYAN}[{self.name}] Tick {self.symbol} @ {tick.get('price', '?')} "
                f"-> Signal: {signal_name}{RESET}"
            )

            return True

        except Exception as e:
            # Record error but don't propagate
            error_msg = str(e)
            self.errors.append(error_msg)

            logger.error(
                f"{RED}❌ {self.name} error on tick: {error_msg}{RESET}"
            )

            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status and metrics for this strategy.

        Returns:
            Dictionary with:
            - name: Strategy identifier
            - symbol: Trading symbol
            - enabled: Whether active
            - ticks_processed: Number of ticks processed
            - signals_generated: Total signals generated
            - buy_signals, sell_signals, hold_signals: Breakdown
            - last_tick_time: When last tick was received
            - last_signal: Most recent signal value
            - error_count: Number of errors encountered
            - adapter_status: Model loading status
        """
        return {
            'name': self.name,
            'symbol': self.symbol,
            'enabled': self.enabled,
            'ticks_processed': self.ticks_processed,
            'signals_generated': self.signals_generated,
            'buy_signals': self.buy_signals,
            'sell_signals': self.sell_signals,
            'hold_signals': self.hold_signals,
            'last_tick_time': self.last_tick_time,
            'last_signal': self.last_signal,
            'last_signal_time': self.last_signal_time,
            'error_count': len(self.errors),
            'adapter_status': 'loaded' if self.adapter.is_model_loaded() else 'failed',
            'model_type': self.adapter.model_type
        }

    def shutdown(self):
        """Clean shutdown of this strategy."""
        try:
            logger.info(
                f"{CYAN}Shutting down {self.name}...{RESET}"
            )

            # Log final metrics
            logger.info(
                f"  Ticks processed: {self.ticks_processed}"
            )
            logger.info(
                f"  Signals generated: {self.signals_generated} "
                f"(BUY={self.buy_signals}, SELL={self.sell_signals}, HOLD={self.hold_signals})"
            )
            logger.info(
                f"  Errors: {len(self.errors)}"
            )

            logger.info(
                f"{GREEN}✅ {self.name} shut down successfully{RESET}"
            )

        except Exception as e:
            logger.error(
                f"{RED}❌ Shutdown error for {self.name}: {e}{RESET}"
            )
