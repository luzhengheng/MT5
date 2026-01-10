#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #076: Lightweight Feature Builder for INF Node

Builds trading features from raw OHLCV data using pure Python/Pandas.
Designed for minimal memory footprint (INF has only 4GB RAM).

NO heavy ML libraries on INF:
- No scikit-learn
- No PyTorch/TensorFlow
- No LightGBM
- Pure pandas/numpy operations only

Protocol: v4.3 (Zero-Trust Edition)
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureBuilder:
    """
    Builds trading features from OHLCV data using lightweight operations

    Features include:
    - Price-based indicators (returns, volatility)
    - Technical indicators (SMA, EMA, RSI, MACD)
    - Volume indicators
    - Time-based features

    Memory-efficient design:
    - Works with fixed-size windows
    - Minimal intermediate storage
    - No model artifacts
    """

    def __init__(
        self,
        lookback_period: int = 60,
        feature_names: Optional[List[str]] = None
    ):
        """
        Initialize FeatureBuilder

        Args:
            lookback_period: Number of historical bars to use
            feature_names: Expected feature names (for validation)
        """
        self.lookback_period = lookback_period
        self.feature_names = feature_names or self._default_feature_names()

        logger.info(f"FeatureBuilder initialized")
        logger.info(f"  Lookback period: {lookback_period}")
        logger.info(f"  Features: {len(self.feature_names)}")

    @staticmethod
    def _default_feature_names() -> List[str]:
        """Return default feature names (23 features to match model)"""
        return [
            f"feature_{i}" for i in range(23)
        ]

    def calculate_returns(self, prices: pd.Series, periods: int = 1) -> pd.Series:
        """
        Calculate percentage returns

        Args:
            prices: Price series
            periods: Number of periods for return calculation

        Returns:
            Returns series
        """
        return prices.pct_change(periods=periods)

    def calculate_sma(self, prices: pd.Series, window: int) -> pd.Series:
        """
        Calculate Simple Moving Average

        Args:
            prices: Price series
            window: Window size

        Returns:
            SMA series
        """
        return prices.rolling(window=window, min_periods=window).mean()

    def calculate_ema(self, prices: pd.Series, span: int) -> pd.Series:
        """
        Calculate Exponential Moving Average

        Args:
            prices: Price series
            span: Span for EMA

        Returns:
            EMA series
        """
        return prices.ewm(span=span, adjust=False).mean()

    def calculate_volatility(
        self,
        returns: pd.Series,
        window: int = 20
    ) -> pd.Series:
        """
        Calculate rolling volatility (std dev of returns)

        Args:
            returns: Returns series
            window: Window size

        Returns:
            Volatility series
        """
        return returns.rolling(window=window, min_periods=window).std()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            prices: Price series
            period: RSI period

        Returns:
            RSI series (0-100)
        """
        delta = prices.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def build_features(
        self,
        df: pd.DataFrame,
        symbol: str = "EURUSD"
    ) -> Optional[pd.DataFrame]:
        """
        Build complete feature set from OHLCV data

        Task #081 Fix: Uses vectorized calculation on full history to ensure
        consistency with sequential feature building. History-dependent indicators
        (EMA, MACD, RSI) must be calculated on the same data window.

        Args:
            df: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            symbol: Symbol name (for logging)

        Returns:
            DataFrame with features (last row only), or None if insufficient data
        """
        # Use vectorized calculation on FULL dataframe
        # This ensures consistency with build_features_vectorized
        full_features = self.build_features_vectorized(df, symbol)

        if full_features is None or len(full_features) == 0:
            logger.error(f"Failed to build features for {symbol}")
            return None

        # Return only the last row as a DataFrame (preserving column names)
        latest_features = full_features.iloc[-1:].copy()

        logger.info(f"  ✓ Features built (latest row from full history): {latest_features.shape}")
        logger.info(f"  Sample values: {latest_features.iloc[0, :5].values}")

        return latest_features

    def build_features_vectorized(
        self,
        df: pd.DataFrame,
        symbol: str = "EURUSD"
    ) -> Optional[pd.DataFrame]:
        """
        Build features for ENTIRE dataframe at once (TRUE vectorization)

        Unlike build_features which returns only the latest row,
        this returns features for ALL rows in the dataframe.

        Args:
            df: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            symbol: Symbol name (for logging)

        Returns:
            DataFrame with shape (len(df), n_features), or None if insufficient data
        """
        logger.info(f"Building vectorized features for {symbol}...")

        # Validate input
        required_cols = ['close', 'high', 'low', 'volume']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.error(f"Missing columns: {missing}")
            return None

        if len(df) < self.lookback_period:
            logger.error(f"Insufficient data: {len(df)} rows (need {self.lookback_period})")
            return None

        # Remove duplicate columns if any
        df_clean = df.loc[:, ~df.columns.duplicated()].copy()

        # Extract price series
        close = df_clean['close']
        high = df_clean['high']
        low = df_clean['low']
        volume = df_clean['volume']

        logger.info(f"  Data: {len(df_clean)} rows, price range: {close.min():.5f} - {close.max():.5f}")

        # Build features (vectorized operations on entire series)
        features = {}

        # 1. Returns (3 features)
        features['return_1'] = self.calculate_returns(close, periods=1)
        features['return_5'] = self.calculate_returns(close, periods=5)
        features['return_10'] = self.calculate_returns(close, periods=10)

        # 2. Moving Averages (4 features)
        features['sma_10'] = self.calculate_sma(close, window=10)
        features['sma_20'] = self.calculate_sma(close, window=20)
        features['ema_10'] = self.calculate_ema(close, span=10)
        features['ema_20'] = self.calculate_ema(close, span=20)

        # 3. Volatility (2 features)
        returns = self.calculate_returns(close)
        features['volatility_10'] = self.calculate_volatility(returns, window=10)
        features['volatility_20'] = self.calculate_volatility(returns, window=20)

        # 4. RSI (1 feature)
        features['rsi_14'] = self.calculate_rsi(close, period=14)

        # 5. MACD (3 features)
        macd, signal, hist = self.calculate_macd(close)
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_hist'] = hist

        # 6. Price position (3 features)
        features['high_low_ratio'] = high / low
        features['close_high_ratio'] = close / high
        features['close_low_ratio'] = close / low

        # 7. Volume features (2 features)
        features['volume_sma'] = self.calculate_sma(volume, window=20)
        features['volume_ratio'] = volume / features['volume_sma']

        # 8. Time-based (if timestamp available)
        if 'timestamp' in df_clean.columns:
            timestamps = df_clean['timestamp'].tolist()
            try:
                # Try to parse as datetime string first (from EODHD API)
                dt = pd.to_datetime(timestamps)
            except (ValueError, TypeError):
                try:
                    # Fall back to Unix timestamp interpretation
                    dt = pd.to_datetime(timestamps, unit='s')
                except (ValueError, TypeError):
                    logger.warning("Could not parse timestamps, using defaults")
                    dt = None

            if dt is not None:
                features['hour'] = dt.hour
                features['day_of_week'] = dt.dayofweek
            else:
                features['hour'] = 0
                features['day_of_week'] = 0
        else:
            features['hour'] = 0
            features['day_of_week'] = 0

        # 9. Additional features to reach 23
        features['price_momentum'] = close.diff(5)
        features['price_acceleration'] = close.diff(5).diff(5)

        # Combine into DataFrame
        feature_df = pd.DataFrame(features)

        # Handle NaN values (from rolling operations)
        feature_df = feature_df.bfill().fillna(0)

        # Rename columns to match expected format
        if len(feature_df.columns) >= 23:
            feature_df = feature_df.iloc[:, :23]
        else:
            # Pad with zeros if needed
            for i in range(len(feature_df.columns), 23):
                feature_df[f'feature_{i}'] = 0.0

        feature_df.columns = [f'feature_{i}' for i in range(23)]

        logger.info(f"  ✓ Vectorized features built: {feature_df.shape}")

        return feature_df

    def build_sequence(
        self,
        df: pd.DataFrame,
        sequence_length: int = 60
    ) -> Optional[np.ndarray]:
        """
        Build sequence of features for LSTM input (TRUE Vectorization - Task #077.5)

        Performance: O(N) - calculates features once, then slices

        This is the CORRECT implementation that:
        1. Calls build_features_vectorized ONCE to get all features
        2. Slices the last N rows directly (no loops)

        Args:
            df: DataFrame with columns ['close', 'high', 'low', 'volume']
            sequence_length: Length of sequence

        Returns:
            Array of shape (sequence_length, n_features) or None
        """
        logger.info(f"Building feature sequence (TRUE vectorization)...")

        # Check if we have enough data
        min_required = sequence_length + self.lookback_period
        if len(df) < min_required:
            logger.error(f"Insufficient data for sequence: {len(df)} < {min_required} required")
            return None

        # TRUE vectorization: calculate ALL features at once (O(N) operation)
        full_features_df = self.build_features_vectorized(df)

        if full_features_df is None:
            logger.error("Vectorized feature building failed")
            return None

        # Handle NaN values that may exist from early indicators
        # Drop initial rows that have NaNs due to insufficient history
        full_features_df = full_features_df.dropna()

        if len(full_features_df) < sequence_length:
            logger.error(f"Insufficient valid features after dropna: {len(full_features_df)} < {sequence_length}")
            return None

        # Simply slice the last N rows (O(1) operation)
        sequence_df = full_features_df.tail(sequence_length)

        if len(sequence_df) != sequence_length:
            logger.error(f"Sequence length mismatch: {len(sequence_df)} != {sequence_length}")
            return None

        sequence_array = sequence_df.values.astype(np.float32)

        logger.info(f"  ✓ Sequence built: {sequence_array.shape}")

        return sequence_array


def main():
    """Test feature builder with synthetic data"""
    logger.info("Testing FeatureBuilder...")

    # Create synthetic OHLCV data
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')

    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 1.1000,
        'high': np.random.randn(100).cumsum() + 1.1010,
        'low': np.random.randn(100).cumsum() + 1.0990,
        'close': np.random.randn(100).cumsum() + 1.1000,
        'volume': np.random.randint(1000, 10000, 100)
    })

    # Build features
    builder = FeatureBuilder(lookback_period=60)
    features = builder.build_features(df)

    if features is not None:
        logger.info(f"✓ Features: {features.shape}")
        logger.info(f"  Columns: {list(features.columns)}")
        logger.info(f"  Sample:\n{features.head()}")
    else:
        logger.error("✗ Feature building failed")

    # Build sequence
    sequence = builder.build_sequence(df, sequence_length=60)

    if sequence is not None:
        logger.info(f"✓ Sequence: {sequence.shape}")
    else:
        logger.error("✗ Sequence building failed")


if __name__ == "__main__":
    main()
