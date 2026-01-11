#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock Feature API for Integration Testing

Provides a minimal FastAPI server that returns mock features
for paper trading simulation without requiring Feast.

Task #018.01: Integration Test Support
"""

import random
from datetime import datetime
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Mock Feature API")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mock_feature_api",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/features/latest")
async def get_latest_features(request: dict):
    """
    Return mock features for trading bot simulation

    Returns 18 features matching the expected schema
    """
    # Generate realistic mock features
    base_price = 1.10000 if "EUR" in request.get("symbol", "EURUSD") else 2050.00

    features = {
        "symbol": request.get("symbol"),
        "timestamp": request.get("timestamp"),
        "sma_20": base_price + random.uniform(-0.0010, 0.0010),
        "sma_50": base_price + random.uniform(-0.0020, 0.0020),
        "sma_200": base_price + random.uniform(-0.0050, 0.0050),
        "rsi_14": random.uniform(30, 70),
        "macd_line": random.uniform(-0.0005, 0.0005),
        "macd_signal": random.uniform(-0.0005, 0.0005),
        "macd_histogram": random.uniform(-0.0002, 0.0002),
        "atr_14": random.uniform(0.0005, 0.0015),
        "bb_upper": base_price + random.uniform(0.0010, 0.0020),
        "bb_middle": base_price,
        "bb_lower": base_price - random.uniform(0.0010, 0.0020),
        "bb_position": random.uniform(0.3, 0.7),
        "rsi_momentum": random.uniform(-5, 5),
        "macd_strength": random.uniform(-0.5, 0.5),
        "sma_trend": random.uniform(-0.001, 0.001),
        "volatility_ratio": random.uniform(0.8, 1.2),
        "returns_1d": random.uniform(-0.002, 0.002),
        "returns_5d": random.uniform(-0.005, 0.005)
    }

    return features


@app.post("/features/historical")
async def get_historical_features(request: dict):
    """
    Return mock historical features for model training

    Expects:
    - symbols: List of trading symbols
    - features: List of feature names
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)

    Returns data with structure for model training
    """
    symbols = request.get("symbols", ["EURUSD"])
    features = request.get("features", ["sma_20", "sma_50", "rsi_14"])
    num_rows = 500  # Generate 500 rows of training data per symbol

    data = []
    for symbol in symbols:
        base_price = 1.10000 if "EUR" in symbol else 2050.00

        for i in range(num_rows):
            # Build values dict with features
            values = {}
            for feature in features:
                if "sma" in feature:
                    values[feature] = base_price + random.uniform(-0.0050, 0.0050)
                elif "rsi" in feature:
                    values[feature] = random.uniform(20, 80)
                elif "macd" in feature:
                    values[feature] = random.uniform(-0.001, 0.001)
                elif "atr" in feature:
                    values[feature] = random.uniform(0.0005, 0.0020)
                elif "bb" in feature:
                    values[feature] = base_price + random.uniform(-0.0020, 0.0020)
                else:
                    values[feature] = random.uniform(-0.01, 0.01)

            # Add label (0 = hold, 1 = buy signal)
            values["label"] = random.choice([0, 1])

            row = {
                "time": f"2025-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
                "symbol": symbol,
                "values": values
            }

            data.append(row)

    return {
        "status": "success",
        "message": f"Generated {len(data)} feature rows",
        "data": data,
        "symbols": symbols,
        "features": features,
        "rows": len(data)
    }


if __name__ == "__main__":
    print("=" * 80)
    print("🔧 Mock Feature API - Starting")
    print("=" * 80)
    print("This is a minimal API for integration testing.")
    print("Port: 8000")
    print("Endpoints:")
    print("  GET  /health")
    print("  POST /features/latest")
    print("  POST /features/historical")
    print("=" * 80)
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)
