#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Engineering Module for MT5-CRS

This module contains stateless feature computation functions that are shared
between training (train.py) and inference (predict.py) to ensure consistency
and prevent training-serving skew.

CRITICAL: Any changes to feature computation logic MUST be made here and
will automatically apply to both training and inference.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FeatureConfig:
    """
    Configuration for feature computation

    Centralizes all feature engineering parameters to ensure consistency
    across training and inference.
    """
    # Moving average windows
    sma_windows: List[int] = None
    ema_windows: List[int] = None

    # Momentum windows
    momentum_windows: List[int] = None

    # Volatility windows
    volatility_windows: List[int] = None

    # Technical indicators
    rsi_window: int = 14

    # Volume windows
    volume_sma_window: int = 5

    def __post_init__(self):
        """Set defaults if not provided"""
        if self.sma_windows is None:
            self.sma_windows = [5, 10, 20]
        if self.ema_windows is None:
            self.ema_windows = [5, 10]
        if self.momentum_windows is None:
            self.momentum_windows = [5, 10]
        if self.volatility_windows is None:
            self.volatility_windows = [5, 10]


def compute_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute basic price-based features

    Args:
        df: DataFrame with OHLCV columns

    Returns:
        DataFrame with added price features
    """
    # Ensure numeric types
    for col in ['open', 'high', 'low', 'close']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Price-based features
    df['price_range'] = df['high'] - df['low']
    df['price_change'] = df['close'] - df['open']
    df['price_change_pct'] = (df['close'] - df['open']) / df['open']

    return df


def compute_moving_averages(df: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """
    Compute Simple and Exponential Moving Averages

    Args:
        df: DataFrame with 'close' column
        config: Feature configuration

    Returns:
        DataFrame with added MA features
    """
    # Simple Moving Averages
    for window in config.sma_windows:
        df[f'sma_{window}'] = df['close'].rolling(window=window).mean()

    # Exponential Moving Averages
    for window in config.ema_windows:
        df[f'ema_{window}'] = df['close'].ewm(span=window, adjust=False).mean()

    return df


def compute_momentum_features(df: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """
    Compute momentum indicators

    Args:
        df: DataFrame with 'close' column
        config: Feature configuration

    Returns:
        DataFrame with added momentum features
    """
    for window in config.momentum_windows:
        df[f'momentum_{window}'] = df['close'] - df['close'].shift(window)

    return df


def compute_volatility_features(df: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """
    Compute volatility indicators (rolling standard deviation)

    Args:
        df: DataFrame with 'close' column
        config: Feature configuration

    Returns:
        DataFrame with added volatility features
    """
    for window in config.volatility_windows:
        df[f'volatility_{window}'] = df['close'].rolling(window=window).std()

    return df


def compute_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Compute Relative Strength Index (RSI)

    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss

    Args:
        df: DataFrame with 'close' column
        window: RSI window (default: 14)

    Returns:
        Series with RSI values
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    # Avoid division by zero
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi


def compute_technical_indicators(df: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """
    Compute technical indicators (RSI, etc.)

    Args:
        df: DataFrame with 'close' column
        config: Feature configuration

    Returns:
        DataFrame with added technical indicator features
    """
    # RSI
    df[f'rsi_{config.rsi_window}'] = compute_rsi(df, window=config.rsi_window)

    return df


def compute_volume_features(df: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """
    Compute volume-based features

    Args:
        df: DataFrame with 'volume' column
        config: Feature configuration

    Returns:
        DataFrame with added volume features
    """
    if 'volume' in df.columns:
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df[f'volume_sma_{config.volume_sma_window}'] = df['volume'].rolling(
            window=config.volume_sma_window
        ).mean()
        df['volume_change'] = df['volume'] - df['volume'].shift(1)

    return df


def compute_features(
    df: pd.DataFrame,
    config: Optional[FeatureConfig] = None,
    include_target: bool = False
) -> pd.DataFrame:
    """
    Compute all features for a given OHLCV DataFrame

    This is the MAIN entry point for feature engineering, used by both
    training and inference to ensure consistency.

    Args:
        df: DataFrame with OHLCV columns (time, open, high, low, close, volume)
        config: Feature configuration (uses defaults if None)
        include_target: If True, compute target variable (for training only)

    Returns:
        DataFrame with all computed features
    """
    if config is None:
        config = FeatureConfig()

    # Make a copy to avoid modifying the original
    df_features = df.copy()

    # Compute feature groups
    df_features = compute_price_features(df_features)
    df_features = compute_moving_averages(df_features, config)
    df_features = compute_momentum_features(df_features, config)
    df_features = compute_volatility_features(df_features, config)
    df_features = compute_technical_indicators(df_features, config)
    df_features = compute_volume_features(df_features, config)

    # Compute target variable (for training only)
    if include_target:
        df_features['target'] = (df_features['close'].shift(-1) > df_features['close']).astype(int)

    # Drop NaN rows created by rolling windows and shifts
    df_clean = df_features.dropna()

    return df_clean


def get_feature_names(config: Optional[FeatureConfig] = None) -> List[str]:
    """
    Get list of feature names that will be computed

    This is useful for validating feature consistency between training and inference.

    Args:
        config: Feature configuration (uses defaults if None)

    Returns:
        List of feature names (excludes metadata columns like 'time', 'symbol', 'target')
    """
    if config is None:
        config = FeatureConfig()

    feature_names = [
        # Price features
        'price_range',
        'price_change',
        'price_change_pct',
    ]

    # SMA features
    for window in config.sma_windows:
        feature_names.append(f'sma_{window}')

    # EMA features
    for window in config.ema_windows:
        feature_names.append(f'ema_{window}')

    # Momentum features
    for window in config.momentum_windows:
        feature_names.append(f'momentum_{window}')

    # Volatility features
    for window in config.volatility_windows:
        feature_names.append(f'volatility_{window}')

    # Technical indicators
    feature_names.append(f'rsi_{config.rsi_window}')

    # Volume features
    feature_names.append(f'volume_sma_{config.volume_sma_window}')
    feature_names.append('volume_change')

    return feature_names
