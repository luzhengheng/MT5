"""
Feast Feature Definitions for MT5-CRS (Production - Task #042.8)

This module defines:
1. Entity: ticker (Stock/Forex symbol)
2. Data Source: PostgreSQL market_data table (TimescaleDB)
3. Feature View: daily_ohlcv_stats (OHLCV features for real-time ML)

Architecture:
- Offline Store: PostgreSQL (cold path, historical data)
- Online Store: Redis (hot path, <10ms real-time serving)
"""

from datetime import timedelta
from feast import Entity, FeatureView, Feature, ValueType, PostgreSQLSource

# ============================================================================
# ENTITY: Ticker (Stock/Forex Symbol)
# Join Key for feature lookups
# ============================================================================
ticker = Entity(
    name="ticker",
    value_type=ValueType.STRING,
    description="Stock or currency pair ticker symbol (e.g., AAPL.US, EURUSD, AUDCAD.FOREX)"
)

# ============================================================================
# DATA SOURCE: PostgreSQL Market Data
# Source Table: market_data (340,494 records, 1971-2025)
# ============================================================================
market_data_source = PostgreSQLSource(
    name="market_data",
    database="${POSTGRES_DB}",
    schema="public",
    table="market_data",
    timestamp_field="time",  # Event timestamp for Feast
    created_timestamp_column="time",
)

# ============================================================================
# FEATURE VIEW: Daily OHLCV Statistics
# Maps market_data columns to servable feature vectors
# TTL: 30 days (features older than 30 days not served from Redis)
# ============================================================================
daily_ohlcv_stats = FeatureView(
    name="daily_ohlcv_stats",
    entities=["ticker"],
    ttl=timedelta(days=30),
    online=True,  # Enable materialization to Redis (hot path)
    offline_store_options={},
    source=market_data_source,
    features=[
        Feature(name="open", dtype=ValueType.DOUBLE),
        Feature(name="high", dtype=ValueType.DOUBLE),
        Feature(name="low", dtype=ValueType.DOUBLE),
        Feature(name="close", dtype=ValueType.DOUBLE),
        Feature(name="adjusted_close", dtype=ValueType.DOUBLE),
        Feature(name="volume", dtype=ValueType.INT64),
    ],
    tags={
        "team": "ml-platform",
        "source": "market_data",
        "environment": "production",
        "task": "042.8-redis-integration"
    }
)
