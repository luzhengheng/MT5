#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feast Feature Definitions for MT5-CRS Real-Time Trading Features

This module defines:
- Entities (trading symbols)
- Feature Views (real-time market data features)
- Feature Services (grouped features for serving)
"""

from feast import Entity, FeatureView, FeatureService, Field, PushSource, FileSource, ValueType
from feast.types import Float32, Int64
from datetime import timedelta

# ============================================================================
# Entity: Trading Symbol
# ============================================================================
symbol = Entity(
    name="symbol",
    join_keys=["symbol"],
    value_type=ValueType.STRING,
    description="Trading symbol (EURUSD, GBPUSD, etc)"
)

# ============================================================================
# Batch Source: Placeholder (required for PushSource)
# ============================================================================
batch_placeholder = FileSource(
    name="batch_placeholder",
    path="data/placeholder.parquet",
    timestamp_field="event_timestamp",
)

# ============================================================================
# PushSource: Real-Time Ticks from ZMQ
# ============================================================================
realtime_ticks_source = PushSource(
    name="realtime_ticks",
    batch_source=batch_placeholder,
)

# ============================================================================
# FeatureView: Basic Market Data Features
# ============================================================================
basic_features = FeatureView(
    name="basic_features",
    entities=[symbol],
    ttl=timedelta(hours=24),
    online=True,  # Enable Redis online serving
    source=realtime_ticks_source,
    schema=[
        Field(name="price_last", dtype=Float32, description="Latest tick price"),
        Field(name="bid", dtype=Float32, description="Bid price"),
        Field(name="ask", dtype=Float32, description="Ask price"),
        Field(name="volume", dtype=Int64, description="Tick volume"),
    ],
)

# ============================================================================
# Batch Source: Historical Market Data for Training
# ============================================================================
# NOTE: Feast 0.49.0 doesn't have native PostgreSQL source support
# We configure this as FileSource for Feast compatibility, but training code
# will use Feast's PostgreSQL offline store backend (configured in feature_store.yaml)
# to retrieve historical features via get_historical_features() API
market_data_batch = FileSource(
    name="market_data_batch",
    path="data/market_data.parquet",  # Placeholder - actual data from PostgreSQL offline store
    timestamp_field="time",
)

# ============================================================================
# BatchFeatureView: Historical Market Data Features for Training
# ============================================================================
# This feature view is registered with Feast for compatibility with SDK
# During training, get_historical_features() will query PostgreSQL (offline store)
# automatically through the configured FeatureStore instance
market_data_features = FeatureView(
    name="market_data_features",
    entities=[symbol],
    ttl=timedelta(days=30),  # Keep features for 30 days
    online=False,  # Only offline (training) - use realtime_ticks for online serving
    source=market_data_batch,
    schema=[
        # OHLCV features from raw market data (from PostgreSQL market_data table)
        Field(name="open", dtype=Float32, description="Opening price"),
        Field(name="high", dtype=Float32, description="High price"),
        Field(name="low", dtype=Float32, description="Low price"),
        Field(name="close", dtype=Float32, description="Closing price"),
        Field(name="volume", dtype=Int64, description="Trading volume"),
        Field(name="adjusted_close", dtype=Float32, description="Adjusted closing price"),
    ],
)

# ============================================================================
# FeatureService: Trading Features (expanded)
# ============================================================================
trading_features = FeatureService(
    name="trading_features",
    features=[basic_features, market_data_features]
)
