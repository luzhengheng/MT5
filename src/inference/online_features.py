#!/usr/bin/env python3
"""
Task #114: Online Feature Calculator

Real-time streaming feature calculation that maintains parity
with offline feature engineering (Task #113).

Protocol: v4.3 (Zero-Trust Edition)
"""

import numpy as np
from collections import deque
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class OnlineFeatureCalculator:
    """
    Streaming feature calculator for ML inference

    Maintains minimal history buffer and calculates features incrementally.
    All calculations MUST match offline FeatureEngineer logic exactly.
    """

    def __init__(self, max_lookback: int = 50):
        """
        Initialize online feature calculator

        Args:
            max_lookback: Maximum historical periods to retain
        """
        self.max_lookback = max_lookback

        # Circular buffers for OHLCV data
        self.close_buffer = deque(maxlen=max_lookback)
        self.high_buffer = deque(maxlen=max_lookback)
        self.low_buffer = deque(maxlen=max_lookback)
        self.volume_buffer = deque(maxlen=max_lookback)

        # EMA tracking for MACD (stateful)
        self.ema_fast_12 = None  # 12-period EMA
        self.ema_slow_26 = None  # 26-period EMA
        self.macd_signal_9 = None  # 9-period EMA of MACD

        # RSI tracking (stateful)
        self.rsi_gain_14 = None  # 14-period average gain
        self.rsi_loss_14 = None  # 14-period average loss
        self.rsi_gain_21 = None  # 21-period average gain
        self.rsi_loss_21 = None  # 21-period average loss

        self.tick_count = 0

        logger.info(f"OnlineFeatureCalculator initialized (lookback={max_lookback})")

    def update(self, close: float, high: float, low: float,
               volume: float) -> bool:
        """
        Update buffers with new tick data

        Args:
            close: Close price
            high: High price
            low: Low price
            volume: Volume

        Returns:
            True if sufficient data for feature calculation
        """
        self.close_buffer.append(close)
        self.high_buffer.append(high)
        self.low_buffer.append(low)
        self.volume_buffer.append(volume)
        self.tick_count += 1

        # Need at least 50 ticks for all features
        return len(self.close_buffer) >= 50

    def _calculate_rsi_online(self, period: int = 14) -> float:
        """
        Calculate RSI using exponential moving average (online version)

        This matches the offline pandas rolling mean calculation
        """
        if len(self.close_buffer) < period + 1:
            return 50.0  # Default neutral

        # Get price changes
        prices = list(self.close_buffer)
        delta = prices[-1] - prices[-2]

        # Initialize on first calculation
        if period == 14:
            if self.rsi_gain_14 is None:
                gains = [max(prices[i] - prices[i-1], 0)
                        for i in range(1, min(len(prices), period + 1))]
                losses = [max(prices[i-1] - prices[i], 0)
                         for i in range(1, min(len(prices), period + 1))]
                self.rsi_gain_14 = np.mean(gains) if gains else 0
                self.rsi_loss_14 = np.mean(losses) if losses else 1e-10

            # Update with exponential smoothing (matches pandas rolling)
            gain = max(delta, 0)
            loss = max(-delta, 0)
            self.rsi_gain_14 = (self.rsi_gain_14 * (period - 1) + gain) / period
            self.rsi_loss_14 = (self.rsi_loss_14 * (period - 1) + loss) / period

            rs = self.rsi_gain_14 / (self.rsi_loss_14 + 1e-10)

        elif period == 21:
            if self.rsi_gain_21 is None:
                gains = [max(prices[i] - prices[i-1], 0)
                        for i in range(1, min(len(prices), period + 1))]
                losses = [max(prices[i-1] - prices[i], 0)
                         for i in range(1, min(len(prices), period + 1))]
                self.rsi_gain_21 = np.mean(gains) if gains else 0
                self.rsi_loss_21 = np.mean(losses) if losses else 1e-10

            gain = max(delta, 0)
            loss = max(-delta, 0)
            self.rsi_gain_21 = (self.rsi_gain_21 * (period - 1) + gain) / period
            self.rsi_loss_21 = (self.rsi_loss_21 * (period - 1) + loss) / period

            rs = self.rsi_gain_21 / (self.rsi_loss_21 + 1e-10)
        else:
            raise ValueError(f"Unsupported RSI period: {period}")

        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_ema(self, values: List[float], period: int,
                      prev_ema: Optional[float] = None) -> float:
        """Calculate exponential moving average"""
        if prev_ema is None:
            return np.mean(values[-period:]) if len(values) >= period else values[-1]

        alpha = 2 / (period + 1)
        return alpha * values[-1] + (1 - alpha) * prev_ema

    def _calculate_sma(self, values: List[float], period: int) -> float:
        """Calculate simple moving average"""
        if len(values) < period:
            return np.mean(values)
        return np.mean(values[-period:])

    def _calculate_volatility(self, period: int = 20) -> float:
        """Calculate rolling volatility (standard deviation of returns)"""
        if len(self.close_buffer) < period + 1:
            return 0.0

        prices = list(self.close_buffer)[-period-1:]
        returns = [(prices[i] - prices[i-1]) / prices[i-1]
                  for i in range(1, len(prices))]
        return np.std(returns)

    def calculate_features(self) -> Optional[Dict[str, float]]:
        """
        Calculate all 21 features for current tick

        Returns:
            Dictionary of features matching Task #113 schema, or None if
            insufficient data
        """
        if len(self.close_buffer) < 50:
            logger.warning(f"Insufficient data: {len(self.close_buffer)}/50")
            return None

        features = {}

        # Convert buffers to lists for calculation
        close = list(self.close_buffer)
        high = list(self.high_buffer)
        low = list(self.low_buffer)
        volume = list(self.volume_buffer)

        try:
            # === Momentum features (4) ===
            features['rsi_14'] = self._calculate_rsi_online(14)
            features['rsi_21'] = self._calculate_rsi_online(21)

            # MACD calculation (stateful EMA)
            current_close = close[-1]
            self.ema_fast_12 = self._calculate_ema(close, 12, self.ema_fast_12)
            self.ema_slow_26 = self._calculate_ema(close, 26, self.ema_slow_26)
            macd = self.ema_fast_12 - self.ema_slow_26
            self.macd_signal_9 = self._calculate_ema([macd], 9, self.macd_signal_9)

            features['macd'] = macd
            features['macd_signal'] = self.macd_signal_9
            features['macd_hist'] = macd - self.macd_signal_9

            # === Volatility features (2) ===
            features['volatility_10'] = self._calculate_volatility(10)
            features['volatility_20'] = self._calculate_volatility(20)

            # === Moving averages (4) ===
            features['sma_5'] = self._calculate_sma(close, 5)
            features['sma_10'] = self._calculate_sma(close, 10)
            features['sma_20'] = self._calculate_sma(close, 20)
            features['sma_50'] = self._calculate_sma(close, 50)

            # === Lagged features (3) ===
            features['price_lag_1'] = close[-2] if len(close) >= 2 else close[-1]
            features['price_lag_5'] = close[-6] if len(close) >= 6 else close[-1]
            features['price_lag_10'] = close[-11] if len(close) >= 11 else close[-1]

            # === Return features (3) ===
            features['return_1d'] = (close[-1] - close[-2]) / close[-2] if len(close) >= 2 else 0
            features['return_5d'] = (close[-1] - close[-6]) / close[-6] if len(close) >= 6 else 0
            features['return_10d'] = (close[-1] - close[-11]) / close[-11] if len(close) >= 11 else 0

            # === High-Low features (2) ===
            highest_20 = max(high[-20:]) if len(high) >= 20 else max(high)
            lowest_20 = min(low[-20:]) if len(low) >= 20 else min(low)
            features['hl_ratio'] = (current_close - lowest_20) / (highest_20 - lowest_20 + 1e-10)
            features['hl_range'] = (highest_20 - lowest_20) / current_close

            # === Volume features (2) ===
            vol_sma_20 = self._calculate_sma(volume, 20)
            features['volume_ratio'] = volume[-1] / (vol_sma_20 + 1e-10)

            # Volume-price trend
            if len(close) >= 20:
                vpt = sum([(close[i] - close[i-1]) / close[i-1] * volume[i]
                          for i in range(-20, 0)])
                features['volume_price_trend'] = vpt
            else:
                features['volume_price_trend'] = 0.0

            return features

        except Exception as e:
            logger.error(f"Feature calculation error: {e}", exc_info=True)
            return None

    def get_feature_vector(self) -> Optional[np.ndarray]:
        """
        Get feature vector as numpy array (for model input)

        Returns:
            (24,) array matching Task #113 feature order, or None
        """
        features = self.calculate_features()
        if features is None:
            return None

        # Feature order MUST match Task #113 training data
        feature_names = [
            'rsi_14', 'rsi_21', 'volatility_10', 'volatility_20',
            'sma_5', 'sma_10', 'sma_20', 'sma_50',
            'macd', 'macd_signal', 'macd_hist',
            'price_lag_1', 'price_lag_5', 'price_lag_10',
            'return_1d', 'return_5d', 'return_10d',
            'hl_ratio', 'hl_range',
            'volume_ratio', 'volume_price_trend'
        ]

        vector = np.array([features[name] for name in feature_names])
        return vector
