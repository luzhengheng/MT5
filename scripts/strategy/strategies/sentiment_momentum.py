#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sentiment-Technical Momentum Strategy
Task #100: Hybrid Factor Strategy Prototype

Strategy Logic:
- BUY Signal: sentiment_score > 0.6 (positive sentiment) AND RSI_14 < 40 (oversold)
            -> Expectation: bounce back on positive sentiment after oversold condition
- SELL Signal: sentiment_score < -0.6 (negative sentiment) AND RSI_14 > 60 (overbought)
             -> Expectation: sell-off on negative sentiment after overbought condition
- NEUTRAL: No clear signal

This strategy combines:
1. Sentiment Analysis (from news via FinBERT) - captures market sentiment
2. Technical Analysis (RSI) - captures momentum reversals

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Hub Agent
"""

import sys
import os
import logging
import argparse
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from scripts.strategy.engine import StrategyBase, SignalType
from scripts.data.fusion_engine import FusionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentMomentumStrategy(StrategyBase):
    """
    Sentiment + Technical (RSI) Momentum Strategy

    Combines sentiment scores from FinBERT with RSI momentum indicator
    to generate trading signals.
    """

    def __init__(
        self,
        symbol: str = "AAPL",
        rsi_period: int = 14,
        sentiment_buy_threshold: float = 0.6,
        sentiment_sell_threshold: float = -0.6,
        rsi_oversold: float = 40,
        rsi_overbought: float = 60,
        **kwargs
    ):
        """
        Initialize SentimentMomentum strategy.

        Args:
            symbol: Trading symbol
            rsi_period: RSI calculation period (default: 14)
            sentiment_buy_threshold: Sentiment score for buy signal (default: 0.6)
            sentiment_sell_threshold: Sentiment score for sell signal (default: -0.6)
            rsi_oversold: RSI oversold threshold (default: 40)
            rsi_overbought: RSI overbought threshold (default: 60)
        """
        super().__init__(
            name="SentimentalMomentum",
            symbol=symbol,
            **kwargs
        )

        self.rsi_period = rsi_period
        self.sentiment_buy_threshold = sentiment_buy_threshold
        self.sentiment_sell_threshold = sentiment_sell_threshold
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

        self.logger.info(
            f"🎯 Strategy parameters: "
            f"RSI({rsi_period}), "
            f"Sentiment Thresholds: [{sentiment_sell_threshold}, {sentiment_buy_threshold}], "
            f"RSI Levels: oversold={rsi_oversold}, overbought={rsi_overbought}"
        )

    def validate_input(self, df: pd.DataFrame) -> bool:
        """
        Validate that input DataFrame has required columns.

        Required columns:
        - close: Closing price
        - sentiment_score: Sentiment score from FinBERT
        """
        required_cols = ['close', 'sentiment_score']

        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            self.logger.error(
                f"❌ Missing required columns: {missing}. "
                f"Available: {list(df.columns)}"
            )
            return False

        if len(df) < self.rsi_period + 1:
            self.logger.error(
                f"❌ Not enough data: {len(df)} rows, need {self.rsi_period + 1}"
            )
            return False

        return True

    def calculate_rsi(
        self,
        prices: pd.Series,
        period: int
    ) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).

        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

        Args:
            prices: Series of closing prices
            period: RSI period (typically 14)

        Returns:
            Series with RSI values
        """
        # Calculate price changes
        deltas = prices.diff()

        # Separate gains and losses
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)

        # Calculate average gains and losses
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss.replace(0, 0.0001)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on sentiment + RSI combination.

        Logic:
        - BUY: sentiment > 0.6 AND RSI < 40 (oversold bounce on good news)
        - SELL: sentiment < -0.6 AND RSI > 60 (overbought break on bad news)
        - NEUTRAL: Otherwise

        Args:
            df: DataFrame with close and sentiment_score columns

        Returns:
            DataFrame with signal, confidence, and reason columns
        """
        try:
            # Create a copy to avoid modifying original
            result_df = df.copy()

            # Calculate RSI
            result_df['rsi'] = self.calculate_rsi(
                result_df['close'],
                self.rsi_period
            )

            # Initialize signal columns
            result_df['signal'] = SignalType.NEUTRAL
            result_df['confidence'] = 0.0
            result_df['reason'] = ''

            # Skip warm-up period (where RSI is NaN)
            valid_idx = result_df['rsi'].notna()

            # BUY Signal: Positive sentiment + Oversold
            buy_condition = (
                (result_df['sentiment_score'] > self.sentiment_buy_threshold) &
                (result_df['rsi'] < self.rsi_oversold)
            )

            result_df.loc[buy_condition & valid_idx, 'signal'] = SignalType.BUY
            result_df.loc[buy_condition & valid_idx, 'reason'] = (
                'BUY: Positive sentiment + RSI oversold'
            )

            # Confidence based on how extreme the conditions are
            buy_confidence = (
                (result_df['sentiment_score'] - self.sentiment_buy_threshold) / (1 - self.sentiment_buy_threshold)
            ).clip(0, 1)
            buy_rsi_confidence = (
                (self.rsi_oversold - result_df['rsi']) / self.rsi_oversold
            ).clip(0, 1)
            result_df.loc[buy_condition & valid_idx, 'confidence'] = (
                0.7 * buy_confidence + 0.3 * buy_rsi_confidence
            ).loc[buy_condition & valid_idx]

            # SELL Signal: Negative sentiment + Overbought
            sell_condition = (
                (result_df['sentiment_score'] < self.sentiment_sell_threshold) &
                (result_df['rsi'] > self.rsi_overbought)
            )

            result_df.loc[sell_condition & valid_idx, 'signal'] = SignalType.SELL
            result_df.loc[sell_condition & valid_idx, 'reason'] = (
                'SELL: Negative sentiment + RSI overbought'
            )

            # Confidence based on how extreme the conditions are
            sell_confidence = (
                (self.sentiment_sell_threshold - result_df['sentiment_score']) / (-1 - self.sentiment_sell_threshold)
            ).clip(0, 1)
            sell_rsi_confidence = (
                (result_df['rsi'] - self.rsi_overbought) / (100 - self.rsi_overbought)
            ).clip(0, 1)
            result_df.loc[sell_condition & valid_idx, 'confidence'] = (
                0.7 * sell_confidence + 0.3 * sell_rsi_confidence
            ).loc[sell_condition & valid_idx]

            # Select output columns
            output_df = result_df[[
                'signal', 'confidence', 'reason', 'rsi', 'sentiment_score',
                'close', 'open', 'high', 'low', 'volume'
            ]].copy()

            # Ensure index is preserved (time column)
            output_df.index.name = 'time'

            return output_df

        except Exception as e:
            self.logger.error(
                f"❌ Error in signal generation: {e}"
            )
            return None

    def print_signal_details(
        self,
        signals_df: pd.DataFrame,
        limit: int = 10
    ) -> None:
        """
        Print detailed signal information for analysis.

        Args:
            signals_df: DataFrame with signals
            limit: Number of signals to print
        """
        # Filter for non-neutral signals
        non_neutral = signals_df[signals_df['signal'] != SignalType.NEUTRAL]

        if len(non_neutral) == 0:
            self.logger.info("ℹ️ No trading signals generated in this period")
            return

        # Get most recent signals
        recent = non_neutral.tail(limit)

        self.logger.info(f"\n📊 Recent {len(recent)} Trading Signals:")
        self.logger.info("=" * 120)

        for idx, (timestamp, row) in enumerate(recent.iterrows(), 1):
            signal_type = "🟢 BUY" if row['signal'] == 1 else "🔴 SELL"
            self.logger.info(
                f"{idx}. {signal_type} | Time: {timestamp} | "
                f"Price: {row['close']:.2f} | "
                f"RSI: {row['rsi']:.1f} | "
                f"Sentiment: {row['sentiment_score']:.3f} | "
                f"Confidence: {row['confidence']:.2%} | "
                f"Reason: {row['reason']}"
            )

        self.logger.info("=" * 120)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Sentiment-Technical Momentum Strategy (Task #100)'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='AAPL',
        help='Trading symbol (default: AAPL)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Historical data in days (default: 30)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Number of recent signals to print (default: 5)'
    )

    args = parser.parse_args()

    try:
        # Get fused data from FusionEngine
        logger.info(f"📥 Loading fused data for {args.symbol}...")
        engine = FusionEngine()
        fused_data = engine.get_fused_data(
            args.symbol,
            days=args.days,
            timeframe='1h'
        )

        if fused_data is None or len(fused_data) == 0:
            logger.error(
                f"❌ No fused data available for {args.symbol}"
            )
            return 1

        logger.info(
            f"✅ Loaded {len(fused_data)} records for {args.symbol}"
        )

        # Initialize strategy
        strategy = SentimentMomentumStrategy(symbol=args.symbol)

        # Generate signals
        logger.info("🔄 Generating trading signals...")
        signals_df = strategy.run(fused_data)

        if signals_df is None:
            logger.error("❌ Signal generation failed")
            return 1

        # Print backtest summary
        summary = strategy.backtest_summary(signals_df)
        logger.info(f"\n📈 Backtest Summary:")
        logger.info(f"  Total Signals: {summary['total_signals']}")
        logger.info(f"  BUY Signals: {summary['buy_signals']}")
        logger.info(f"  SELL Signals: {summary['sell_signals']}")
        logger.info(f"  Avg Confidence: {summary['avg_confidence']:.2%}")

        # Print recent signals
        strategy.print_signal_details(signals_df, limit=args.limit)

        logger.info("\n✅ Strategy execution complete!")
        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
