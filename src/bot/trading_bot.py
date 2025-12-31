#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Bot - Real-time Inference & Execution Loop

Task #018.01: Integrates MT5Client, XGBoost Model, and Feature API
into a unified real-time trading system.

Protocol: v2.2 (Hot Path Architecture)
"""

import zmq
import json
import logging
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import numpy as np
import requests
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

# Add project root to path
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.mt5_client import MT5Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class TradingBot:
    """
    Real-time Trading Bot

    Integrates:
    - ZMQ PUB/SUB for market data (Port 5556)
    - Feature Serving API (HTTP)
    - XGBoost model for inference
    - MT5Client for order execution (ZMQ REQ, Port 5555)

    Architecture:
        Market Data (ZMQ PUB) -> on_tick()
            -> fetch_features() (HTTP API)
            -> predict_signal() (XGBoost)
            -> execute_signal() (MT5Client)

    Features:
    - Real-time tick processing
    - Feature fetching from API
    - ML-based signal generation
    - Order execution with error handling
    - Comprehensive logging
    """

    def __init__(
        self,
        symbols: List[str],
        model_path: str,
        api_url: str = "http://localhost:8000",
        zmq_market_url: str = "tcp://localhost:5556",
        zmq_execution_host: str = "localhost",
        zmq_execution_port: int = 5555,
        volume: float = 0.1
    ):
        """
        Initialize Trading Bot

        Args:
            symbols: List of trading symbols (e.g., ['EURUSD', 'XAUUSD'])
            model_path: Path to XGBoost model file
            api_url: Feature Serving API URL
            zmq_market_url: ZMQ market data publisher URL
            zmq_execution_host: MT5 Gateway host
            zmq_execution_port: MT5 Gateway port
            volume: Default trading volume (lots)
        """
        self.symbols = symbols
        self.model_path = model_path
        self.api_url = api_url
        self.zmq_market_url = zmq_market_url
        self.volume = volume

        # Components
        self.model = None
        self.scaler = StandardScaler()
        self.mt5_client = MT5Client(
            host=zmq_execution_host,
            port=zmq_execution_port
        )
        self.zmq_context = zmq.Context()
        self.zmq_subscriber = None

        # State
        self.running = False
        self.order_lock = threading.Lock()  # Prevent concurrent orders

        # Feature columns (must match training)
        self.feature_cols = [
            'sma_20', 'sma_50', 'sma_200',
            'rsi_14',
            'macd_line', 'macd_signal', 'macd_histogram',
            'atr_14',
            'bb_upper', 'bb_middle', 'bb_lower',
            'bb_position', 'rsi_momentum', 'macd_strength',
            'sma_trend', 'volatility_ratio', 'returns_1d', 'returns_5d'
        ]

        logger.info(f"{GREEN}✅ TradingBot initialized{RESET}")
        logger.info(f"  Symbols: {symbols}")
        logger.info(f"  Model: {model_path}")
        logger.info(f"  API: {api_url}")
        logger.info(f"  Market Data: {zmq_market_url}")
        logger.info(f"  Execution: {zmq_execution_host}:{zmq_execution_port}")

    def connect(self) -> bool:
        """
        Connect to all external services

        Returns:
            True if all connections successful, False otherwise
        """
        logger.info(f"{CYAN}🔌 Connecting to services...{RESET}")

        try:
            # 1. Load XGBoost model
            logger.info(f"  Loading model: {self.model_path}")
            self.model = XGBClassifier()
            self.model.load_model(self.model_path)
            logger.info(f"{GREEN}  ✅ Model loaded{RESET}")

            # 2. Connect to MT5 Gateway
            logger.info(f"  Connecting to MT5 Gateway...")
            if not self.mt5_client.connect():
                raise ConnectionError("MT5 Gateway connection failed")
            logger.info(f"{GREEN}  ✅ MT5 Gateway connected{RESET}")

            # 3. Test Feature API
            logger.info(f"  Testing Feature API...")
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Feature API unhealthy: {response.status_code}")
            logger.info(f"{GREEN}  ✅ Feature API accessible{RESET}")

            # 4. Subscribe to market data
            logger.info(f"  Subscribing to market data...")
            self.zmq_subscriber = self.zmq_context.socket(zmq.SUB)
            self.zmq_subscriber.connect(self.zmq_market_url)

            # Subscribe to all symbols
            for symbol in self.symbols:
                self.zmq_subscriber.setsockopt_string(zmq.SUBSCRIBE, symbol)

            logger.info(f"{GREEN}  ✅ Market data subscription ready{RESET}")

            logger.info(f"{GREEN}✅ All services connected{RESET}")
            return True

        except Exception as e:
            logger.error(f"{RED}❌ Connection failed: {e}{RESET}")
            return False

    def fetch_features(self, symbol: str, timestamp: str) -> Optional[np.ndarray]:
        """
        Fetch features from Feature Serving API

        Args:
            symbol: Trading symbol
            timestamp: Current timestamp

        Returns:
            Feature array (18 features) or None if failed
        """
        try:
            # Call Feature API
            payload = {
                "symbol": symbol,
                "timestamp": timestamp
            }

            response = requests.post(
                f"{self.api_url}/features/latest",
                json=payload,
                timeout=2
            )

            if response.status_code != 200:
                logger.warning(f"{YELLOW}⚠️  API returned {response.status_code}{RESET}")
                return None

            data = response.json()

            if data.get('status') != 'success':
                logger.warning(f"{YELLOW}⚠️  API error: {data.get('message')}{RESET}")
                return None

            # Extract feature values
            feature_values = data.get('features', {})

            # Build feature array in correct order
            features = []
            for col in self.feature_cols:
                value = feature_values.get(col)
                if value is None:
                    logger.warning(f"{YELLOW}⚠️  Missing feature: {col}{RESET}")
                    return None
                features.append(value)

            features_array = np.array(features).reshape(1, -1)

            logger.info(f"{GREEN}[FEAT] Fetched {len(features)} features for {symbol}{RESET}")

            return features_array

        except requests.Timeout:
            logger.error(f"{RED}❌ Feature API timeout{RESET}")
            return None
        except Exception as e:
            logger.error(f"{RED}❌ Feature fetch error: {e}{RESET}")
            return None

    def predict_signal(self, features: np.ndarray) -> int:
        """
        Generate trading signal using XGBoost model

        Args:
            features: Feature array (1, 18)

        Returns:
            Signal: 1 (BUY), 0 (HOLD), -1 (SELL)
        """
        try:
            # Scale features
            features_scaled = self.scaler.fit_transform(features)

            # Predict
            prediction = self.model.predict(features_scaled)[0]
            proba = self.model.predict_proba(features_scaled)[0]

            # Convert to signal
            # prediction = 1 means price up -> BUY
            # prediction = 0 means price down -> SELL
            if prediction == 1:
                signal = 1  # BUY
                confidence = proba[1]
            else:
                signal = -1  # SELL
                confidence = proba[0]

            logger.info(
                f"{CYAN}[PRED] Signal: "
                f"{'BUY' if signal == 1 else 'SELL'} "
                f"(confidence: {confidence:.2f}){RESET}"
            )

            return signal

        except Exception as e:
            logger.error(f"{RED}❌ Prediction error: {e}{RESET}")
            return 0  # HOLD on error

    def execute_signal(self, symbol: str, signal: int, price: float):
        """
        Execute trading signal

        Args:
            symbol: Trading symbol
            signal: 1 (BUY), 0 (HOLD), -1 (SELL)
            price: Current market price
        """
        if signal == 0:
            logger.info(f"{YELLOW}[HOLD] No action for {symbol}{RESET}")
            return

        with self.order_lock:
            try:
                side = "BUY" if signal == 1 else "SELL"

                logger.info(f"{BLUE}[EXEC] Sending order: {side} {self.volume} {symbol} @ MARKET{RESET}")

                response = self.mt5_client.send_order(
                    symbol=symbol,
                    side=side,
                    volume=self.volume,
                    order_type="MARKET"
                )

                if response.get("status") == "ok":
                    ticket = response.get("ticket")
                    fill_price = response.get("price", price)
                    logger.info(
                        f"{GREEN}[FILL] Order #{ticket} filled @ {fill_price}{RESET}"
                    )
                else:
                    error_msg = response.get("message", "Unknown error")
                    logger.error(f"{RED}[REJECT] Order rejected: {error_msg}{RESET}")

            except Exception as e:
                logger.error(f"{RED}❌ Execution error: {e}{RESET}")

    def on_tick(self, tick: Dict[str, Any]):
        """
        Handle incoming market tick

        Args:
            tick: Tick data dictionary
        """
        try:
            symbol = tick.get("symbol")
            timestamp = tick.get("timestamp")
            price = tick.get("last", tick.get("bid", 0.0))

            logger.info(f"{CYAN}[TICK] {symbol} @ {price} ({timestamp}){RESET}")

            # 1. Fetch features
            features = self.fetch_features(symbol, timestamp)
            if features is None:
                logger.warning(f"{YELLOW}⚠️  Skipping tick (no features){RESET}")
                return

            # 2. Generate signal
            signal = self.predict_signal(features)

            # 3. Execute signal
            self.execute_signal(symbol, signal, price)

        except Exception as e:
            logger.error(f"{RED}❌ Tick processing error: {e}{RESET}")

    def run(self, duration_seconds: int = 60):
        """
        Main event loop

        Args:
            duration_seconds: Run duration in seconds (0 = infinite)
        """
        logger.info(f"{BLUE}{'=' * 80}{RESET}")
        logger.info(f"{BLUE}🤖 Trading Bot Started{RESET}")
        logger.info(f"{BLUE}{'=' * 80}{RESET}")

        if not self.connect():
            logger.error(f"{RED}❌ Failed to connect services{RESET}")
            return

        self.running = True
        start_time = time.time()

        logger.info(f"{CYAN}🔄 Entering main loop...{RESET}")
        logger.info(f"  Duration: {duration_seconds} seconds")
        print()

        try:
            while self.running:
                # Check duration
                if duration_seconds > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= duration_seconds:
                        logger.info(f"{YELLOW}⏰ Duration limit reached{RESET}")
                        break

                # Poll for market data (timeout 1 second)
                try:
                    if self.zmq_subscriber.poll(1000):
                        message = self.zmq_subscriber.recv_string()
                        tick_data = json.loads(message.split(' ', 1)[1])
                        self.on_tick(tick_data)

                except zmq.Again:
                    # Timeout, continue
                    pass

        except KeyboardInterrupt:
            logger.info(f"\n{YELLOW}🛑 KeyboardInterrupt received{RESET}")

        finally:
            self.shutdown()

        logger.info(f"{GREEN}{'=' * 80}{RESET}")
        logger.info(f"{GREEN}✅ Trading Bot Stopped{RESET}")
        logger.info(f"{GREEN}{'=' * 80}{RESET}")

    def shutdown(self):
        """Clean shutdown of all connections"""
        logger.info(f"{CYAN}🔌 Shutting down...{RESET}")

        self.running = False

        if self.zmq_subscriber:
            self.zmq_subscriber.close()

        if self.mt5_client:
            self.mt5_client.close()

        if self.zmq_context:
            self.zmq_context.term()

        logger.info(f"{GREEN}✅ Shutdown complete{RESET}")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("🤖 TradingBot - Task #018.01")
    print("=" * 80)
    print()
    print("This module provides the TradingBot class for real-time trading.")
    print()
    print("To run paper trading simulation:")
    print("  python3 scripts/run_paper_trading.py")
    print()
    print("=" * 80)
