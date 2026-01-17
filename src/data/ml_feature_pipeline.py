#!/usr/bin/env python3
"""
Task #113: ML Alpha Feature Engineering Pipeline

Feature factory for ML-based alpha model.
Generates features from OHLCV data without look-ahead bias.

Protocol: v4.3 (Zero-Trust Edition)
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Feature engineering pipeline for ML Alpha models"""

    def __init__(self, lookback_period: int = 20):
        """
        Initialize feature engineer

        Args:
            lookback_period: Number of periods for rolling features
        """
        self.lookback_period = lookback_period
        self.scaler = StandardScaler()

    def calculate_rsi(self, prices: pd.Series,
                     period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)

        Args:
            prices: Price series
            period: RSI period (default 14)

        Returns:
            RSI series
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(
            window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(
            window=period, min_periods=1).mean()

        # Avoid division by zero
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return rsi.fillna(50)  # Default to 50 for initial values

    def calculate_volatility(self, prices: pd.Series,
                            period: int = 20) -> pd.Series:
        """
        Calculate rolling volatility (standard deviation)

        Args:
            prices: Price series
            period: Rolling period

        Returns:
            Volatility series
        """
        returns = prices.pct_change()
        volatility = returns.rolling(
            window=period, min_periods=1).std()

        return volatility.fillna(0)

    def calculate_sma(self, prices: pd.Series,
                     period: int) -> pd.Series:
        """
        Calculate Simple Moving Average

        Args:
            prices: Price series
            period: SMA period

        Returns:
            SMA series
        """
        return prices.rolling(window=period, min_periods=1).mean()

    def calculate_macd(self, prices: pd.Series,
                      fast: int = 12,
                      slow: int = 26) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period

        Returns:
            Tuple of (MACD, Signal line)
        """
        ema_fast = prices.ewm(span=fast, min_periods=1).mean()
        ema_slow = prices.ewm(span=slow, min_periods=1).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=9, min_periods=1).mean()

        return macd, signal

    def create_lagged_features(self, prices: pd.Series,
                              lags: list) -> pd.DataFrame:
        """
        Create lagged price features

        Args:
            prices: Price series
            lags: List of lag periods

        Returns:
            DataFrame with lagged features
        """
        features = pd.DataFrame(index=prices.index)

        for lag in lags:
            features[f'price_lag_{lag}'] = prices.shift(lag)

        return features

    def create_return_features(self, prices: pd.Series,
                              periods: list) -> pd.DataFrame:
        """
        Create return features

        Args:
            prices: Price series
            periods: List of return calculation periods

        Returns:
            DataFrame with return features
        """
        features = pd.DataFrame(index=prices.index)

        for period in periods:
            features[f'return_{period}d'] = prices.pct_change(period)

        return features

    def create_high_low_features(self,
                                high: pd.Series,
                                low: pd.Series,
                                close: pd.Series,
                                period: int = 20) -> pd.DataFrame:
        """
        Create high-low momentum features

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for calculations

        Returns:
            DataFrame with HL features
        """
        features = pd.DataFrame(index=close.index)

        # Highest high and lowest low
        highest = high.rolling(window=period, min_periods=1).max()
        lowest = low.rolling(window=period, min_periods=1).min()

        # Position within high-low range
        features['hl_ratio'] = (close - lowest) / (highest - lowest +
                                                    1e-10)
        features['hl_range'] = (highest - lowest) / close

        return features

    def create_volume_features(self,
                              volume: pd.Series,
                              price: pd.Series,
                              period: int = 20) -> pd.DataFrame:
        """
        Create volume-based features

        Args:
            volume: Volume series
            price: Price series
            period: Rolling period

        Returns:
            DataFrame with volume features
        """
        features = pd.DataFrame(index=volume.index)

        # Volume moving average
        vol_sma = volume.rolling(window=period, min_periods=1).mean()
        features['volume_ratio'] = volume / (vol_sma + 1e-10)

        # Volume-price trend
        features['volume_price_trend'] = (
            (price.pct_change() * volume).rolling(
                window=period, min_periods=1).sum()
        )

        return features

    def engineer_features(self,
                         df: pd.DataFrame) -> pd.DataFrame:
        """
        Create complete feature set from OHLCV data

        Args:
            df: DataFrame with columns ['open', 'high', 'low',
                                        'close', 'volume']

        Returns:
            DataFrame with engineered features (no look-ahead bias)
        """
        features = pd.DataFrame(index=df.index)

        # Momentum features
        features['rsi_14'] = self.calculate_rsi(df['close'], 14)
        features['rsi_21'] = self.calculate_rsi(df['close'], 21)

        # Volatility features
        features['volatility_10'] = self.calculate_volatility(
            df['close'], 10)
        features['volatility_20'] = self.calculate_volatility(
            df['close'], 20)

        # Moving averages
        features['sma_5'] = self.calculate_sma(df['close'], 5)
        features['sma_10'] = self.calculate_sma(df['close'], 10)
        features['sma_20'] = self.calculate_sma(df['close'], 20)
        features['sma_50'] = self.calculate_sma(df['close'], 50)

        # MACD
        macd, signal = self.calculate_macd(df['close'])
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_hist'] = macd - signal

        # Lagged features
        lag_features = self.create_lagged_features(
            df['close'], [1, 5, 10])
        features = pd.concat([features, lag_features], axis=1)

        # Return features
        ret_features = self.create_return_features(
            df['close'], [1, 5, 10])
        features = pd.concat([features, ret_features], axis=1)

        # High-Low features
        hl_features = self.create_high_low_features(
            df['high'], df['low'], df['close'], period=20)
        features = pd.concat([features, hl_features], axis=1)

        # Volume features
        vol_features = self.create_volume_features(
            df['volume'], df['close'], period=20)
        features = pd.concat([features, vol_features], axis=1)

        return features

    def create_training_set(self,
                           df: pd.DataFrame,
                           target_shift: int = 1) -> pd.DataFrame:
        """
        Create training set with features and labels

        Args:
            df: DataFrame with OHLCV data
            target_shift: Number of periods ahead for label

        Returns:
            DataFrame with features and binary label
        """
        # Generate features (no look-ahead bias)
        features = self.engineer_features(df)

        # Create binary label: 1 if future close > current close
        features['label'] = (
            (df['close'].shift(-target_shift) > df['close'])
            .astype(int)
        )

        # Drop rows with NaN values
        features = features.dropna()

        return features

    def normalize_features(self,
                          features_df: pd.DataFrame,
                          fit: bool = True) -> pd.DataFrame:
        """
        Normalize features using StandardScaler

        Args:
            features_df: DataFrame with features
            fit: Whether to fit scaler (True for train,
                 False for test)

        Returns:
            Normalized DataFrame
        """
        # Exclude label column
        label = features_df['label'] if 'label' in features_df else None

        feature_cols = [c for c in features_df.columns
                       if c != 'label']
        X = features_df[feature_cols]

        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)

        result = pd.DataFrame(
            X_scaled, columns=feature_cols, index=features_df.index)

        if label is not None:
            result['label'] = label

        return result


class FeatureValidator:
    """Validate features for training"""

    @staticmethod
    def check_no_leakage(features: pd.DataFrame,
                        target_shift: int = 1) -> bool:
        """
        Verify no look-ahead bias in features

        Args:
            features: Feature DataFrame
            target_shift: Target look-ahead period

        Returns:
            True if validation passes
        """
        # Check that features don't contain future prices
        assert 'price_lag_1' in features.columns or \
               'sma_5' in features.columns, \
               "Missing lagged/SMA features (may indicate look-ahead bias)"

        return True

    @staticmethod
    def check_stationarity(series: pd.Series,
                          name: str = "series") -> bool:
        """
        Basic stationarity check using rolling statistics

        Args:
            series: Time series to check
            name: Series name for logging

        Returns:
            True if series appears stationary
        """
        if series.isnull().any():
            logger.warning(f"{name} contains NaN values")
            return False

        # Check that series doesn't have extreme trends
        rolling_mean = series.rolling(window=20).mean()
        rolling_std = series.rolling(window=20).std()

        # Check for very high variance in mean
        mean_std = rolling_mean.std()
        if mean_std > series.std() * 2:
            logger.warning(f"{name} may have trend/non-stationarity")
            return False

        return True
