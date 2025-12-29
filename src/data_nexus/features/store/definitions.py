"""
Feast Feature Definitions for MT5-CRS

Task #042: Feature Store Implementation
Date: 2025-12-29
Feast Version: 0.10.2 (latest available)

Entity: ticker (stock symbols)
FeatureView: daily_ohlcv_stats (market data statistics)

Note: Feast 0.10.2 doesn't include native PostgreSQL adapter.
For production PostgreSQL integration, consider:
1. Export PostgreSQL data to Parquet files and use FileSource
2. Use BigQuerySource as template (same API structure)
3. Upgrade to newer Feast version (when available)
"""

from datetime import timedelta
from feast import Entity, Feature, FeatureView, BigQuerySource
from feast.value_type import ValueType

# ============================================================================
# Entity Definition
# ============================================================================

# Entity: ticker (stock symbol like AAPL.US, EURUSD.s, etc.)
# This represents the primary key for joining with feature tables
ticker = Entity(
    name="ticker",
    value_type=ValueType.STRING,
    description="Stock or currency pair ticker symbol (e.g., AAPL.US, EURUSD.s)"
)

# ============================================================================
# Feature Definitions
# ============================================================================

# OHLCV (Open, High, Low, Close, Volume) features for daily market data
ohlcv_features = [
    Feature(name="open", dtype=ValueType.FLOAT),
    Feature(name="high", dtype=ValueType.FLOAT),
    Feature(name="low", dtype=ValueType.FLOAT),
    Feature(name="close", dtype=ValueType.FLOAT),
    Feature(name="adjusted_close", dtype=ValueType.FLOAT),
    Feature(name="volume", dtype=ValueType.INT64),
]

# Additional derived features that could be computed
derived_features = [
    Feature(name="daily_return", dtype=ValueType.FLOAT),
    Feature(name="volatility", dtype=ValueType.FLOAT),
]

# ============================================================================
# Data Source Definition
# ============================================================================

# NOTE: Feast 0.10.2 doesn't have PostgreSQL source
# This uses BigQuerySource as template - structure is same, just different source type
# For PostgreSQL, use this in production setup:
#
# from feast.infra.offline_stores.postgres import PostgreSQLSource
# market_data_source = PostgreSQLSource(
#     event_timestamp_column="time",
#     created_timestamp_column="created_at",
#     table="market_data",
#     database="data_nexus",
# )
#
# For now, we define the structure using BigQuerySource:

market_data_source = BigQuerySource(
    event_timestamp_column="time",
    table_ref="daily_market_data",
    query=None
)

# Alternative: FileSource for Parquet/CSV data
# This requires exporting PostgreSQL data to files first
# from feast.data_source import FileSource
# market_data_source = FileSource(
#     event_timestamp_column="time",
#     path="data/market_data/*.parquet"
# )

# ============================================================================
# Feature View Definition
# ============================================================================

# Feature view: daily_ohlcv_stats
# Maps market_data table columns to feature names
# TTL: 30 days (features older than 30 days are evicted from online store)
daily_ohlcv_stats = FeatureView(
    name="daily_ohlcv_stats",
    entities=["ticker"],
    features=ohlcv_features,
    ttl=timedelta(days=30),
    input=market_data_source,
    tags={
        "team": "ml",
        "source": "market_data",
        "description": "Daily OHLCV market statistics"
    }
)

# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ticker",
    "daily_ohlcv_stats",
    "ohlcv_features",
    "derived_features",
]
