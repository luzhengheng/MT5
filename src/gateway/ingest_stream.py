#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feast Feature Ingestion Service

Consumes real-time market data from ZMQ PUB (port 5556) and pushes features to Feast.

Architecture:
  ZMQ PUB (port 5556)
    ↓
  FeatureIngestionService (this)
    ↓
  Feast PushSource → Redis Online Store
"""

import zmq
import json
import asyncio
import pandas as pd
from feast import FeatureStore, PushMode
from datetime import datetime, timezone
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class FeatureIngestionService:
    def __init__(self):
        self.fs = FeatureStore(repo_path="src/feature_store")
        self.zmq_context = zmq.Context()
        self.zmq_sub = self.zmq_context.socket(zmq.SUB)
        self.zmq_sub.connect("tcp://localhost:5556")
        self.zmq_sub.subscribe(b"")  # Subscribe to all topics

        print("[INFO] Feature Ingestion Service initialized")
        print(f"[INFO] Feast project: {self.fs.project}")

    async def consume_and_ingest(self):
        """
        Main loop: consume ZMQ ticks → transform → push to Feast
        """
        print("[INFO] Starting feature ingestion service...")
        print("[INFO] Subscribed to ZMQ PUB on tcp://localhost:5556")

        tick_count = 0

        while True:
            try:
                # Receive Multipart: [symbol, json_payload]
                topic, payload = self.zmq_sub.recv_multipart(zmq.NOBLOCK)
                symbol = topic.decode("utf-8")
                tick_data = json.loads(payload.decode("utf-8"))

                # Construct feature DataFrame
                features_df = pd.DataFrame([{
                    "symbol": symbol,
                    "price_last": float(tick_data.get("price", 0)),
                    "bid": float(tick_data.get("bid", 0)),
                    "ask": float(tick_data.get("ask", 0)),
                    "volume": int(tick_data.get("volume", 0)),
                    "event_timestamp": datetime.fromtimestamp(
                        tick_data.get("timestamp", datetime.now().timestamp()),
                        tz=timezone.utc
                    )
                }])

                # Push to Feast (online store only)
                self.fs.push("realtime_ticks", features_df, to=PushMode.ONLINE)
                
                tick_count += 1
                if tick_count % 10 == 0:  # Log every 10 ticks
                    print(f"[INFO] Pushed {tick_count} features | Latest: {symbol}={tick_data.get('price')}")

            except zmq.Again:
                await asyncio.sleep(0.01)  # No data, sleep briefly
            except Exception as e:
                print(f"[ERROR] Ingestion failed: {e}")
                await asyncio.sleep(1)  # Backoff on error

async def main():
    service = FeatureIngestionService()
    await service.consume_and_ingest()

if __name__ == "__main__":
    asyncio.run(main())
