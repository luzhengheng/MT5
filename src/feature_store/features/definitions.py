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
# FeatureService: Trading Features
# ============================================================================
trading_features = FeatureService(
    name="trading_features",
    features=[basic_features]
)
