#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-Time Strategy Engine for MT5-CRS

This module implements the hot path: Ticks -> Features -> Signal -> Order
Designed for millisecond-level latency with proper feature consistency.

CRITICAL (TASK #028):
- MUST use src.features.engineering.compute_features() for real-time data
- MUST maintain feature consistency with training (prevent skew)
- Target latency: <50ms from tick receipt to order send
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Dict, Optional, Deque

import zmq
import pandas as pd
import numpy as np
import xgboost as xgb
from dotenv import load_dotenv

# Shared feature engineering (CRITICAL: prevents training-serving skew)
from src.features.engineering import compute_features, FeatureConfig, get_feature_names
from src.model.predict import PricePredictor

# Task #108: State Synchronization & Crash Recovery
from src.live_loop.reconciler import StateReconciler, SystemHaltException

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Real-time strategy engine implementing the hot inference path
    
    Architecture:
        ZMQ SUB (5556) -> Tick Buffer -> Feature Computation -> 
        Model Inference -> Signal Generation -> ZMQ REQ (5555) -> Order Execution
    
    Key Design Principles:
        1. Feature Consistency: Uses shared compute_features() module
        2. Cold Start Handling: Buffers minimum ticks before inference
        3. Latency Optimization: Efficient state management with deque
        4. Error Resilience: Graceful degradation on NaN features
    """
    
    def __init__(
        self,
        symbol: str = "EURUSD",
        model_path: Optional[str] = None,
        zmq_market_data_url: str = "tcp://localhost:5556",
        zmq_execution_url: str = "tcp://localhost:5555",
        buffer_size: int = 100,
        min_buffer_size: int = 30
    ):
        """
        Initialize the strategy engine

        Args:
            symbol: Trading symbol (e.g., "EURUSD", "AUDCAD.FOREX")
            model_path: Path to trained XGBoost model (default: models/xgboost_price_predictor.json)
            zmq_market_data_url: ZMQ PUB endpoint for market data ticks
            zmq_execution_url: ZMQ REQ endpoint for order execution
            buffer_size: Maximum number of ticks to keep in rolling window
            min_buffer_size: Minimum ticks needed before computing features (cold start)
        """
        self.symbol = symbol
        self.buffer_size = buffer_size
        self.min_buffer_size = min_buffer_size

        # ZMQ endpoints
        self.zmq_market_data_url = zmq_market_data_url
        self.zmq_execution_url = zmq_execution_url

        # State: Rolling window buffer for feature computation
        self.tick_buffer: Deque[Dict] = deque(maxlen=buffer_size)

        # Feature configuration (must match training)
        self.feature_config = FeatureConfig()
        self.feature_names = get_feature_names(self.feature_config)

        # Model loading
        self.predictor = PricePredictor(model_path=model_path)

        # ZMQ sockets (initialized in start())
        self.zmq_context = None
        self.market_data_socket = None
        self.execution_socket = None

        # Task #108: State Synchronization & Crash Recovery
        # Initialize reconciler for startup state synchronization (blocking gate)
        self.reconciler = StateReconciler()
        self.recovered_state = None

        # Metrics
        self.ticks_processed = 0
        self.signals_generated = 0
        self.orders_sent = 0

        logger.info(f"[INIT] Strategy Engine initialized for {symbol}")
        logger.info(f"[INIT] Model: {self.predictor.model_path}")
        logger.info(f"[INIT] Buffer: max={buffer_size}, min={min_buffer_size}")
        logger.info(f"[INIT] Features: {len(self.feature_names)} dimensions")

        # Task #108: Perform startup state synchronization
        logger.info("[INIT] Performing startup state synchronization...")
        try:
            self.recovered_state = self.reconciler.perform_startup_sync()
            logger.info(
                f"[INIT] ✅ State synchronized: "
                f"{len(self.recovered_state.positions)} positions recovered"
            )
        except SystemHaltException as e:
            logger.error(f"[INIT] ❌ State synchronization failed: {e}")
            raise
    
    def start(self):
        """
        Start the strategy engine main loop
        
        This is the HOT PATH - optimized for millisecond latency
        """
        logger.info("="*80)
        logger.info("[START] Starting Real-Time Strategy Engine")
        logger.info("="*80)
        
        # Initialize ZMQ sockets
        self._init_zmq()
        
        try:
            # Main event loop
            while True:
                self._process_tick()
        except KeyboardInterrupt:
            logger.info("\n[SHUTDOWN] Received interrupt signal")
            self._shutdown()
        except Exception as e:
            logger.error(f"[ERROR] Fatal error in main loop: {e}", exc_info=True)
            self._shutdown()
            raise
    
    def _init_zmq(self):
        """Initialize ZMQ sockets for market data and execution"""
        self.zmq_context = zmq.Context()
        
        # SUB socket for market data (ticks)
        self.market_data_socket = self.zmq_context.socket(zmq.SUB)
        self.market_data_socket.connect(self.zmq_market_data_url)
        self.market_data_socket.subscribe(f"tick.{self.symbol}".encode())
        logger.info(f"[ZMQ] Connected to market data: {self.zmq_market_data_url}")
        logger.info(f"[ZMQ] Subscribed to topic: tick.{self.symbol}")
        
        # REQ socket for order execution
        self.execution_socket = self.zmq_context.socket(zmq.REQ)
        self.execution_socket.connect(self.zmq_execution_url)
        logger.info(f"[ZMQ] Connected to execution gateway: {self.zmq_execution_url}")
    
    def _process_tick(self):
        """
        Process a single tick through the inference pipeline
        
        Hot Path Sequence:
            1. Receive tick from ZMQ
            2. Add to rolling buffer
            3. Compute features using shared module
            4. Run model inference
            5. Generate signal
            6. Send order (if signal != 0)
        """
        start_time = time.time()
        
        try:
            # Step 1: Receive tick from ZMQ
            topic, payload = self.market_data_socket.recv_multipart(zmq.NOBLOCK)
            
            # Parse tick data
            tick_data = json.loads(payload.decode('utf-8'))
            tick_data['time'] = datetime.fromtimestamp(tick_data.get('timestamp', time.time()))
            
            # Step 2: Add to buffer
            self.tick_buffer.append(tick_data)
            self.ticks_processed += 1
            
            # Cold start check
            if len(self.tick_buffer) < self.min_buffer_size:
                logger.warning(
                    f"[COLD START] Buffer: {len(self.tick_buffer)}/{self.min_buffer_size} "
                    f"- Skipping inference (need {self.min_buffer_size - len(self.tick_buffer)} more ticks)"
                )
                return
            
            # Step 3: Compute features using shared module
            features_df = self._compute_features()
            
            if features_df is None or len(features_df) == 0:
                logger.warning("[SKIP] Feature computation returned empty DataFrame (likely NaN)")
                return
            
            # Step 4: Model inference
            features_vector = features_df.iloc[-1][self.feature_names].values.reshape(1, -1)
            prediction = self.predictor.model.predict(features_vector)[0]
            probability = self.predictor.model.predict_proba(features_vector)[0]
            
            # Step 5: Signal generation
            signal = self._generate_signal(prediction, probability)
            
            if signal != 0:
                self.signals_generated += 1
                logger.info(f"[SIGNAL] Generated: {signal} (prob={probability[int(prediction)]:.4f})")
                
                # Step 6: Send order
                self._send_order(signal, tick_data, probability[int(prediction)])
            
            # Latency measurement
            latency_ms = (time.time() - start_time) * 1000
            
            if self.ticks_processed % 100 == 0:
                logger.info(f"[METRICS] Ticks={self.ticks_processed}, Signals={self.signals_generated}, "
                           f"Orders={self.orders_sent}, Latency={latency_ms:.2f}ms")
            
            # Latency check (CRITICAL: <50ms requirement)
            if latency_ms > 50:
                logger.warning(f"[LATENCY] Tick->Signal processing took {latency_ms:.2f}ms (>50ms threshold)")
        
        except zmq.Again:
            # No data available (non-blocking mode)
            time.sleep(0.001)  # 1ms sleep to avoid CPU spin
        except Exception as e:
            logger.error(f"[ERROR] Tick processing failed: {e}", exc_info=True)
    
    def _compute_features(self) -> Optional[pd.DataFrame]:
        """
        Compute features from tick buffer using shared engineering module
        
        CRITICAL: This MUST use src.features.engineering.compute_features()
        to ensure training-serving consistency
        
        Returns:
            pd.DataFrame with computed features, or None if computation fails
        """
        try:
            # Convert tick buffer to DataFrame
            df = pd.DataFrame(list(self.tick_buffer))
            
            # Ensure required columns exist
            required_cols = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            
            # Map tick fields to OHLCV format
            if 'price' in df.columns and 'close' not in df.columns:
                df['close'] = df['price']
                df['open'] = df['price']
                df['high'] = df['price']
                df['low'] = df['price']
            
            if 'adjusted_close' not in df.columns:
                df['adjusted_close'] = df['close']
            
            # Use shared feature engineering module (CRITICAL)
            features_df = compute_features(
                df,
                config=self.feature_config,
                include_target=False  # Inference mode
            )
            
            return features_df
        
        except Exception as e:
            logger.error(f"[ERROR] Feature computation failed: {e}", exc_info=True)
            return None
    
    def _generate_signal(self, prediction: int, probability: np.ndarray) -> int:
        """
        Generate trading signal from model prediction
        
        Args:
            prediction: Model prediction (0=DOWN, 1=UP)
            probability: Prediction probabilities [prob_down, prob_up]
        
        Returns:
            Signal: -1 (SELL), 0 (HOLD), +1 (BUY)
        """
        # Simple threshold-based signal
        confidence = probability[int(prediction)]
        
        if confidence < 0.6:
            return 0  # Low confidence -> HOLD
        
        if prediction == 1:
            return 1  # UP prediction -> BUY
        else:
            return -1  # DOWN prediction -> SELL
    
    def _send_order(self, signal: int, tick_data: Dict, confidence: float):
        """
        Send order to execution gateway via ZMQ REQ
        
        Args:
            signal: Trading signal (-1=SELL, +1=BUY)
            tick_data: Current tick data
            confidence: Model confidence level
        """
        try:
            order = {
                "symbol": self.symbol,
                "action": "BUY" if signal > 0 else "SELL",
                "price": tick_data.get('price', tick_data.get('close')),
                "volume": 0.01,  # Minimum lot size
                "timestamp": time.time(),
                "confidence": float(confidence),
                "strategy": "ml_xgboost"
            }
            
            # Send order to execution gateway
            self.execution_socket.send_json(order)
            logger.info(f"[ORDER] Sent: {order['action']} {order['symbol']} @ {order['price']:.5f}")
            
            # Wait for acknowledgment
            response = self.execution_socket.recv_json()
            logger.info(f"[ORDER] Response: {response}")
            
            self.orders_sent += 1
        
        except Exception as e:
            logger.error(f"[ERROR] Order execution failed: {e}", exc_info=True)
    
    def _shutdown(self):
        """Clean shutdown of ZMQ sockets"""
        logger.info("[SHUTDOWN] Closing ZMQ sockets...")
        
        if self.market_data_socket:
            self.market_data_socket.close()
        if self.execution_socket:
            self.execution_socket.close()
        if self.zmq_context:
            self.zmq_context.term()
        
        logger.info(f"[SHUTDOWN] Final metrics: Ticks={self.ticks_processed}, "
                   f"Signals={self.signals_generated}, Orders={self.orders_sent}")
        logger.info("[SHUTDOWN] Engine stopped")


def main():
    """Main entry point for standalone execution"""
    engine = StrategyEngine(
        symbol=os.getenv("TRADING_SYMBOL", "EURUSD"),
        zmq_market_data_url=os.getenv("ZMQ_MARKET_DATA_URL", "tcp://localhost:5556"),
        zmq_execution_url=os.getenv("ZMQ_EXECUTION_URL", "tcp://localhost:5555")
    )
    
    engine.start()


if __name__ == "__main__":
    main()
