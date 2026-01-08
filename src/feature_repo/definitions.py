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
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64

# Define the Symbol entity - represents a tradable instrument (e.g., AAPL.US)
symbol = Entity(
    name="symbol",
    description="Trading symbol identifier (e.g., AAPL.US, MSFT.US)",
    join_keys=["symbol"],
)

# Use FileSource as placeholder for MVP
# This will be replaced with PostgreSQL source in Task #068
ohlcv_source = FileSource(
    name="ohlcv_file_source",
    path="data/ohlcv_features.parquet",  # Placeholder path
    timestamp_field="event_timestamp",
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
# (Placeholder for Task #068)
technical_indicators_ma = FeatureView(
    name="technical_indicators_ma",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="sma_5", dtype=Float64, description="5-day Simple Moving Average"),
        Field(name="sma_10", dtype=Float64, description="10-day Simple Moving Average"),
        Field(name="sma_20", dtype=Float64, description="20-day Simple Moving Average"),
        Field(name="sma_50", dtype=Float64, description="50-day Simple Moving Average"),
        Field(name="sma_200", dtype=Float64, description="200-day Simple Moving Average"),
        Field(name="ema_12", dtype=Float64, description="12-day Exponential Moving Average"),
        Field(name="ema_26", dtype=Float64, description="26-day Exponential Moving Average"),
    ],
    online=True,
    source=ohlcv_source,
    tags={"category": "trend", "task": "068"},
)

# Feature View 3: Technical Indicators - Momentum
# (Placeholder for Task #068)
technical_indicators_momentum = FeatureView(
    name="technical_indicators_momentum",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="rsi_14", dtype=Float64, description="14-day Relative Strength Index"),
        Field(name="macd", dtype=Float64, description="MACD Line (12-26)"),
        Field(name="macd_signal", dtype=Float64, description="MACD Signal Line (9-day EMA)"),
        Field(name="macd_histogram", dtype=Float64, description="MACD Histogram"),
        Field(name="stoch_k", dtype=Float64, description="Stochastic %K"),
        Field(name="stoch_d", dtype=Float64, description="Stochastic %D"),
    ],
    online=True,
    source=ohlcv_source,
    tags={"category": "momentum", "task": "068"},
)

# Feature View 4: Technical Indicators - Volatility
# (Placeholder for Task #068)
technical_indicators_volatility = FeatureView(
    name="technical_indicators_volatility",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="atr_14", dtype=Float64, description="14-day Average True Range"),
        Field(name="bb_upper", dtype=Float64, description="Bollinger Band Upper"),
        Field(name="bb_middle", dtype=Float64, description="Bollinger Band Middle"),
        Field(name="bb_lower", dtype=Float64, description="Bollinger Band Lower"),
        Field(name="bb_width", dtype=Float64, description="Bollinger Band Width"),
        Field(name="std_20", dtype=Float64, description="20-day Standard Deviation"),
    ],
    online=True,
    source=ohlcv_source,
    tags={"category": "volatility", "task": "068"},
)

# Feature View 5: Volume Indicators
# (Placeholder for Task #068)
volume_indicators = FeatureView(
    name="volume_indicators",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="volume_sma_20", dtype=Float64, description="20-day Volume SMA"),
        Field(name="volume_ratio", dtype=Float64, description="Current Volume / SMA"),
        Field(name="obv", dtype=Float64, description="On-Balance Volume"),
        Field(name="vwap", dtype=Float64, description="Volume Weighted Average Price"),
    ],
    online=True,
    source=ohlcv_source,
    tags={"category": "volume", "task": "068"},
)

# Feature View 6: Price Action Features
# (Placeholder for Task #068)
price_action = FeatureView(
    name="price_action",
    entities=[symbol],
    ttl=timedelta(days=365),
    schema=[
        Field(name="daily_return", dtype=Float64, description="Daily return %"),
        Field(name="log_return", dtype=Float64, description="Log return"),
        Field(name="price_range", dtype=Float64, description="High - Low"),
        Field(name="body_size", dtype=Float64, description="abs(Close - Open)"),
        Field(name="upper_shadow", dtype=Float64, description="High - max(Open, Close)"),
        Field(name="lower_shadow", dtype=Float64, description="min(Open, Close) - Low"),
        Field(name="is_green_candle", dtype=Int64, description="1 if Close > Open"),
    ],
    online=True,
    source=ohlcv_source,
    tags={"category": "price_action", "task": "068"},
)
