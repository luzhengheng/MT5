"""
MT5-CRS Feast Feature Repository
Task #067: Feature Store Deployment

This module initializes the Feast Feature Store for the MT5-CRS trading system.
It provides a bridge between cold path (TimescaleDB historical data) and hot path
(Redis real-time serving) as specified in the Architecture Blueprint.

The feature store enables:
1. Offline feature computation on historical data (for model training)
2. Online feature serving (for real-time trading decisions)
3. Consistent feature definitions across training and serving
4. Prevention of training-serving skew
"""

from .definitions import (
    symbol,
    ohlcv_features,
    technical_indicators_ma,
    technical_indicators_momentum,
    technical_indicators_volatility,
    volume_indicators,
    price_action,
)

__all__ = [
    "symbol",
    "ohlcv_features",
    "technical_indicators_ma",
    "technical_indicators_momentum",
    "technical_indicators_volatility",
    "volume_indicators",
    "price_action",
]
