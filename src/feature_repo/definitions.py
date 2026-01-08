"""
Task #067: Feast Feature Definitions
Protocol: v4.3 (Zero-Trust Edition)

Defines technical indicator features for MT5-CRS trading system.
These features bridge the Cold Path (TimescaleDB historical data) and
Hot Path (Redis real-time serving) as per Architecture Blueprint.

This file defines feature schemas and entities. The actual feature values
will be computed and materialized in Task #068.

Note: For MVP purposes, we define schemas without requiring the underlying
data source to exist. The real data will be populated when Task #066.1
data becomes available.
"""

from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource, PostgreSQLSource
from feast.types import Float64, Int64

# Define the Symbol entity - represents a tradable instrument (e.g., AAPL.US)
symbol = Entity(
    name="symbol",
    description="Trading symbol identifier (e.g., AAPL.US, MSFT.US)",
    join_keys=["symbol"],
)

# Use FileSource as placeholder for OHLCV MVP
# This will be replaced with PostgreSQL source when data ingestion is complete
ohlcv_source = FileSource(
    name="ohlcv_file_source",
    path="data/ohlcv_features.parquet",  # Placeholder path
    timestamp_field="event_timestamp",
)

# PostgreSQL source for technical indicators (Task #068)
# Points to features.technical_indicators table in TimescaleDB
# This is populated by scripts/compute_features.py
technical_indicators_source = PostgreSQLSource(
    name="technical_indicators_postgres_source",
    database="mt5_crs",
    schema="features",
    table="technical_indicators",
    timestamp_field="time",
    created_timestamp_column="created_at",
)

# Feature View 1: Basic OHLCV Features
# These are the raw validated features from Task #066.1
ohlcv_features = FeatureView(
    name="ohlcv_features",
    entities=[symbol],
    ttl=timedelta(days=365 * 2),  # Keep 2 years of historical data
    schema=[
        Field(name="open", dtype=Float64, description="Opening price"),
        Field(name="high", dtype=Float64, description="Highest price"),
        Field(name="low", dtype=Float64, description="Lowest price"),
        Field(name="close", dtype=Float64, description="Closing price"),
        Field(name="volume", dtype=Int64, description="Trading volume"),
        Field(name="adjusted_close", dtype=Float64, description="Adjusted closing price"),
    ],
    online=True,
    source=ohlcv_source,
    tags={"team": "data-engineering", "task": "066.1"},
)

# Feature View 2: Technical Indicators - Moving Averages
# Task #068: Computed from market_data.ohlcv_daily and stored in features.technical_indicators
technical_indicators_ma = FeatureView(
    name="technical_indicators_ma",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="sma_5", dtype=Float64, description="5-day Simple Moving Average"),
        Field(name="sma_10", dtype=Float64, description="10-day Simple Moving Average"),
        Field(name="sma_20", dtype=Float64, description="20-day Simple Moving Average"),
        Field(name="ema_12", dtype=Float64, description="12-day Exponential Moving Average"),
        Field(name="ema_26", dtype=Float64, description="26-day Exponential Moving Average"),
    ],
    online=True,
    source=technical_indicators_source,
    tags={"category": "trend", "task": "068"},
)

# Feature View 3: Technical Indicators - Momentum
# Task #068: Computed and stored in features.technical_indicators
technical_indicators_momentum = FeatureView(
    name="technical_indicators_momentum",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="rsi_14", dtype=Float64, description="14-day Relative Strength Index"),
        Field(name="roc_1", dtype=Float64, description="1-day Rate of Change"),
        Field(name="roc_5", dtype=Float64, description="5-day Rate of Change"),
        Field(name="roc_10", dtype=Float64, description="10-day Rate of Change"),
        Field(name="macd", dtype=Float64, description="MACD Line (12-26)"),
        Field(name="macd_signal", dtype=Float64, description="MACD Signal Line (9-day EMA)"),
        Field(name="macd_hist", dtype=Float64, description="MACD Histogram"),
    ],
    online=True,
    source=technical_indicators_source,
    tags={"category": "momentum", "task": "068"},
)

# Feature View 4: Technical Indicators - Volatility
# Task #068: Computed and stored in features.technical_indicators
technical_indicators_volatility = FeatureView(
    name="technical_indicators_volatility",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="atr_14", dtype=Float64, description="14-day Average True Range"),
        Field(name="bb_upper_20", dtype=Float64, description="Bollinger Band Upper (20-day)"),
        Field(name="bb_middle_20", dtype=Float64, description="Bollinger Band Middle (20-day)"),
        Field(name="bb_lower_20", dtype=Float64, description="Bollinger Band Lower (20-day)"),
        Field(name="high_low_ratio", dtype=Float64, description="(High - Low) / Close ratio"),
        Field(name="close_open_ratio", dtype=Float64, description="(Close - Open) / Open ratio"),
    ],
    online=True,
    source=technical_indicators_source,
    tags={"category": "volatility", "task": "068"},
)

# Feature View 5: Volume Indicators
# Task #068: Computed and stored in features.technical_indicators
volume_indicators = FeatureView(
    name="volume_indicators",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="volume_sma_5", dtype=Float64, description="5-day Volume SMA"),
        Field(name="volume_sma_20", dtype=Float64, description="20-day Volume SMA"),
        Field(name="volume_change", dtype=Float64, description="Daily volume percentage change"),
    ],
    online=True,
    source=technical_indicators_source,
    tags={"category": "volume", "task": "068"},
)

# Feature View 6: Price Action Features (simple price-based ratios)
# Task #068: Computed from OHLCV and stored in features.technical_indicators
# Note: Comprehensive price action analysis (candle patterns, support/resistance, etc.)
# can be added in future iterations
price_action = FeatureView(
    name="price_action",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="high_low_ratio", dtype=Float64, description="(High - Low) / Close ratio"),
        Field(name="close_open_ratio", dtype=Float64, description="(Close - Open) / Open ratio"),
    ],
    online=True,
    source=technical_indicators_source,
    tags={"category": "price_action", "task": "068"},
)
