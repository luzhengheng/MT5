"""
Feast Feature Definitions

Task #041: Feast Feature Store Infrastructure

Defines:
1. Entity: ticker (trading symbol)
2. Data Source: PostgreSQL market_data table
3. Feature Views: Daily OHLCV stats, Technical indicators
"""

from datetime import timedelta

from feast import Entity, FeatureView, Field
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)
from feast.types import Float32, Float64, Int64, String

# ============================================================================
# Entity Definition: ticker
# ============================================================================

ticker = Entity(
    name="ticker",
    join_keys=["symbol"],
    description="Trading symbol (e.g., AAPL.US, EURUSD.s)"
)

# ============================================================================
# Data Source: PostgreSQL market_data table
# ============================================================================

market_data_source = PostgreSQLSource(
    name="market_data_postgres",
    table="market_data",
    timestamp_field="time",
)

# ============================================================================
# Feature View 1: Daily OHLCV Stats
# ============================================================================

daily_ohlcv_view = FeatureView(
    name="daily_ohlcv_stats",
    entities=[ticker],
    schema=[
        Field(name="symbol", dtype=String),
        Field(name="open", dtype=Float64),
        Field(name="high", dtype=Float64),
        Field(name="low", dtype=Float64),
        Field(name="close", dtype=Float64),
        Field(name="volume", dtype=Int64),
        Field(name="adjusted_close", dtype=Float64),
    ],
    source=market_data_source,
    ttl=timedelta(days=30),
    description="Daily OHLCV price data from market_data table"
)

# ============================================================================
# Feature View 2: Technical Indicators (Task #038 Integration)
# ============================================================================
#
# Note: This requires a separate table or view with technical indicators
# For now, we'll define the structure assuming indicators are calculated
# and stored in the market_data table or a derived view

# Uncomment when technical indicators are materialized to database:
#
# technical_indicators_view = FeatureView(
#     name="technical_indicators",
#     entities=[ticker],
#     schema=[
#         Field(name="symbol", dtype=String),
#         Field(name="RSI_14", dtype=Float32),
#         Field(name="MACD", dtype=Float32),
#         Field(name="MACD_Signal", dtype=Float32),
#         Field(name="MACD_Hist", dtype=Float32),
#         Field(name="BB_Upper", dtype=Float32),
#         Field(name="BB_Middle", dtype=Float32),
#         Field(name="BB_Lower", dtype=Float32),
#         Field(name="SMA_20", dtype=Float32),
#     ],
#     source=market_data_source,  # Or a different source
#     ttl=timedelta(days=30),
#     description="Technical indicator features calculated from OHLCV data"
# )
