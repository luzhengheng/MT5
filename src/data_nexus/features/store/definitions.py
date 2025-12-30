"""
Feast Feature Definitions for MT5-CRS
Task #042: Feature Store Implementation (Feast 0.10.2)

This module defines:
1. Entity: ticker (Stock/Forex symbol)
2. Data Source: PostgreSQL market_data table
3. Feature View: daily_ohlcv_stats (OHLCV features)
"""

from datetime import timedelta
from feast import Entity, FeatureView, Feature, ValueType, FileSource

# Entity: Stock/Forex symbol (ticker)
# This is the join key for feature lookups
ticker = Entity(
    name="ticker",
    value_type=ValueType.STRING,
    description="Stock or currency pair ticker symbol (e.g., AAPL.US, EURUSD)"
)

# Data Source: Parquet files as a proxy for PostgreSQL data
# Note: Feast 0.10.2 offline store configuration is different
# The PostgreSQL connection is configured in feature_store.yaml
# For now, we use FileSource pointing to exported data
market_data_source = FileSource(
    path="data/market_data_features.parquet",
    event_timestamp_column="date",
)

# Feature View: Daily OHLCV Statistics
# Maps market_data columns to servable features
# TTL: 30 days (features older than 30 days are not served)
daily_ohlcv_stats = FeatureView(
    name="daily_ohlcv_stats",
    entities=["ticker"],
    ttl=timedelta(days=30),
    features=[
        Feature(name="open", dtype=ValueType.DOUBLE),
        Feature(name="high", dtype=ValueType.DOUBLE),
        Feature(name="low", dtype=ValueType.DOUBLE),
        Feature(name="close", dtype=ValueType.DOUBLE),
        Feature(name="adjusted_close", dtype=ValueType.DOUBLE),
        Feature(name="volume", dtype=ValueType.INT64),
    ],
    online=True,
    input=market_data_source,
    tags={"team": "ml-platform", "source": "market_data"}
)
