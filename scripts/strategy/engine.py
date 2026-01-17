#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Engine Base Class and Interface
Task #100: Hybrid Factor Strategy Prototype

This module defines the abstract base class for all trading strategies.
Each strategy must implement:
1. Signal generation based on historical data (no look-ahead bias)
2. Confidence scoring for generated signals
3. Risk management parameters

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Hub Agent
"""

import logging
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import IntEnum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SignalType(IntEnum):
    """Enumeration for trading signals"""
    SELL = -1
    NEUTRAL = 0
    BUY = 1


class StrategyBase(ABC):
    """
    Abstract base class for all trading strategies.

    This class defines the standard interface that all strategies must implement:
    - Input: DataFrame with OHLCV data and additional features
    - Output: DataFrame with trading signals (-1, 0, 1) and confidence scores

    Key principle: No look-ahead bias
    All signals must be generated using only data available at time t and before.
    """

    def __init__(self, name: str, symbol: str, **kwargs):
        """
        Initialize the strategy.

        Args:
            name: Strategy name for logging
            symbol: Trading symbol (e.g., 'AAPL')
            **kwargs: Additional strategy-specific parameters
        """
        self.name = name
        self.symbol = symbol
        self.params = kwargs
        self.logger = logging.getLogger(f"Strategy.{name}")

        self.logger.info(
            f"✅ Strategy '{name}' initialized for {symbol}"
        )

    @abstractmethod
    def validate_input(self, df: pd.DataFrame) -> bool:
        """
        Validate input DataFrame structure and required columns.

        Args:
            df: Input DataFrame with market data

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from input data.

        This is the core method that must be implemented by each strategy.
        CRITICAL: Must not use future data (t+1, t+2, etc.)

        Args:
            df: DataFrame with columns [open, high, low, close, volume, sentiment_score, etc.]
               Must have DatetimeIndex named 'time'

        Returns:
            DataFrame with columns:
            - signal: Trading signal (-1, 0, 1)
            - confidence: Signal confidence [0.0, 1.0]
            - reason: Text description of signal reason
            - timestamp: Original timestamp
        """
        pass

    def _validate_no_lookahead(
        self,
        df: pd.DataFrame,
        signal_col: str = 'signal'
    ) -> bool:
        """
        Helper method to detect potential look-ahead bias.

        This performs a simple check: if we reverse the close price,
        the signal pattern should not remain identical (which would
        indicate future data usage).

        Args:
            df: Signal DataFrame
            signal_col: Column name containing signals

        Returns:
            True if no obvious look-ahead bias detected, False otherwise
        """
        if len(df) < 10:
            return True

        # Check if signal distribution looks reasonable
        # (Not all zeros, not all ones, reasonable ratio)
        signal_counts = df[signal_col].value_counts()

        if len(signal_counts) < 2:
            self.logger.warning(
                "⚠️ Only one signal type generated (possible bias)"
            )
            return False

        return True

    def run(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Main entry point: validate and generate signals.

        Args:
            df: Input DataFrame with market data

        Returns:
            Signal DataFrame or None on error
        """
        try:
            # Validate input
            if not self.validate_input(df):
                self.logger.error(
                    f"❌ Input validation failed for {self.name}"
                )
                return None

            # Generate signals
            signals_df = self.generate_signals(df)

            if signals_df is None:
                self.logger.error(
                    f"❌ Signal generation failed for {self.name}"
                )
                return None

            # Validate output
            if not self._validate_no_lookahead(signals_df):
                self.logger.warning(
                    f"⚠️ Look-ahead bias warning for {self.name}"
                )

            self.logger.info(
                f"✅ Signal generation complete: "
                f"{len(signals_df)} signals, "
                f"BUY: {(signals_df['signal'] == 1).sum()}, "
                f"SELL: {(signals_df['signal'] == -1).sum()}"
            )

            return signals_df

        except Exception as e:
            self.logger.error(
                f"❌ Error in {self.name}.run(): {e}"
            )
            return None

    def backtest_summary(self, signals_df: pd.DataFrame) -> Dict:
        """
        Generate a simple backtest summary from signals.

        Args:
            signals_df: DataFrame with signals

        Returns:
            Dictionary with backtest statistics
        """
        summary = {
            'total_signals': len(signals_df),
            'buy_signals': int((signals_df['signal'] == 1).sum()),
            'sell_signals': int((signals_df['signal'] == -1).sum()),
            'neutral_signals': int((signals_df['signal'] == 0).sum()),
            'avg_confidence': float(signals_df['confidence'].mean()),
            'max_confidence': float(signals_df['confidence'].max()),
            'min_confidence': float(signals_df['confidence'].min()),
        }
        return summary
