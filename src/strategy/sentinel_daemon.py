#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #076: Sentinel Daemon - Trading Strategy Orchestrator

Main trading loop daemon that coordinates:
1. Market data fetching (EODHD API or ZMQ cache)
2. Feature engineering (lightweight pandas operations)
3. Model inference (HTTP requests to HUB server)
4. Trading execution (ZMQ commands to GTW server)

Critical Design Principles:
- Memory efficient (INF has only 4GB RAM)
- No local model loading (all inference via HUB HTTP)
- Robust error handling (never crash the loop)
- Scheduled execution (runs every minute at :58 seconds)

Execution Node: INF Server (172.19.141.250)
Protocol: v4.3 (Zero-Trust Edition)
"""

import os
import sys
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import schedule
import requests
import zmq
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.feature_builder import FeatureBuilder
from strategy.metrics_exporter import get_metrics_exporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sentinel_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SentinelDaemon:
    """
    Trading strategy orchestrator daemon

    Runs continuously, executing trading logic at scheduled intervals
    """

    def __init__(
        self,
        hub_host: str = "172.19.141.254",
        hub_port: int = 5001,
        gtw_host: str = "172.19.141.255",
        gtw_port: int = 5555,
        eodhd_api_key: Optional[str] = None,
        symbol: str = "EURUSD",
        threshold: float = 0.6,
        lookback_bars: int = 200,  # Increased from 100 to fix data starvation (Task #077.5)
        dry_run: bool = True,
        metrics_port: int = 8000  # Prometheus metrics endpoint (Task #085)
    ):
        """
        Initialize Sentinel Daemon

        Args:
            hub_host: HUB server IP (model serving)
            hub_port: HUB server port
            gtw_host: GTW server IP (trading gateway)
            gtw_port: GTW server ZMQ port
            eodhd_api_key: EODHD API key (from .env)
            symbol: Trading symbol
            threshold: Probability threshold for trading
            lookback_bars: Number of historical bars to fetch
            dry_run: If True, don't send actual trades
            metrics_port: Port for Prometheus metrics endpoint (Task #085)
        """
        self.hub_host = hub_host
        self.hub_port = hub_port
        self.gtw_host = gtw_host
        self.gtw_port = gtw_port
        self.eodhd_api_key = eodhd_api_key or os.getenv('EODHD_API_TOKEN')
        self.symbol = symbol
        self.threshold = threshold
        self.lookback_bars = lookback_bars
        self.dry_run = dry_run
        self.metrics_port = metrics_port

        self.hub_url = f"http://{hub_host}:{hub_port}"
        self.start_time = time.time()

        # Initialize feature builder
        self.feature_builder = FeatureBuilder(lookback_period=60)

        # Initialize metrics exporter (Task #085)
        self.metrics = get_metrics_exporter(port=metrics_port)

        # ZMQ context (created per-request to avoid leaks)
        self.zmq_context = None

        logger.info("=" * 80)
        logger.info("Sentinel Daemon Initialized")
        logger.info("=" * 80)
        logger.info(f"HUB: {self.hub_url}")
        logger.info(f"GTW: tcp://{gtw_host}:{gtw_port}")
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Threshold: {threshold}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info(f"Metrics Port: {metrics_port}")
        logger.info(f"API Key: {'SET' if self.eodhd_api_key else 'NOT SET'}")
        logger.info("=" * 80)

    def fetch_market_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch market data from EODHD API

        Returns:
            DataFrame with OHLCV data or None on error
        """
        logger.info(f"Fetching market data for {self.symbol}...")
        fetch_start = time.time()

        if not self.eodhd_api_key:
            logger.error("EODHD API key not set")
            self.metrics.record_data_fetch(time.time() - fetch_start, success=False)
            self.metrics.record_api_error('eodhd', 'no_api_key')
            return None

        try:
            # EODHD Intraday API
            url = f"https://eodhistoricaldata.com/api/intraday/{self.symbol}.FOREX"
            params = {
                'api_token': self.eodhd_api_key,
                'interval': '1h',
                'fmt': 'json'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                self.metrics.record_data_fetch(time.time() - fetch_start, success=False)
                self.metrics.record_api_error('eodhd', str(response.status_code))
                return None

            data = response.json()

            if not data:
                logger.error("Empty response from API")
                self.metrics.record_data_fetch(time.time() - fetch_start, success=False)
                self.metrics.record_api_error('eodhd', 'empty_response')
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Standardize column names
            if 'datetime' in df.columns:
                df.rename(columns={'datetime': 'timestamp'}, inplace=True)

            logger.info(f"✓ Fetched {len(df)} bars")
            logger.info(f"  Latest: {df.iloc[-1]['timestamp'] if len(df) > 0 else 'N/A'}")

            # Record successful fetch
            self.metrics.record_data_fetch(time.time() - fetch_start, success=True)

            return df.tail(self.lookback_bars)

        except requests.exceptions.Timeout:
            logger.error("API request timeout")
            self.metrics.record_data_fetch(time.time() - fetch_start, success=False)
            self.metrics.record_api_error('eodhd', 'timeout')
            return None
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            traceback.print_exc()
            self.metrics.record_data_fetch(time.time() - fetch_start, success=False)
            self.metrics.record_api_error('eodhd', 'exception')
            return None

    def request_prediction(
        self,
        features_tabular: np.ndarray,
        features_sequential: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Request prediction from HUB model server

        Args:
            features_tabular: (1, 23) tabular features
            features_sequential: (1, 60, 23) sequential features

        Returns:
            (1, 3) prediction probabilities or None
        """
        logger.info("Requesting prediction from HUB...")
        pred_start = time.time()

        try:
            # Format for MLflow serving
            data = {
                "dataframe_split": {
                    "columns": ["X_tabular", "X_sequential"],
                    "data": [[
                        features_tabular.tolist(),
                        features_sequential[0].tolist()  # First window
                    ]]
                }
            }

            url = f"{self.hub_url}/invocations"
            headers = {"Content-Type": "application/json"}

            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=1  # 1 second timeout as specified
            )

            if response.status_code != 200:
                logger.error(f"Inference error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                self.metrics.record_prediction(
                    time.time() - pred_start,
                    success=False
                )
                self.metrics.record_api_error('hub', str(response.status_code))
                return None

            predictions = response.json()

            # Convert to numpy array
            if isinstance(predictions, dict) and 'predictions' in predictions:
                pred_array = np.array(predictions['predictions'])
            else:
                pred_array = np.array(predictions)

            logger.info(f"✓ Prediction: {pred_array[0]}")

            # Record successful prediction
            confidence = float(np.max(pred_array[0]))
            self.metrics.record_prediction(
                time.time() - pred_start,
                success=True,
                confidence=confidence
            )

            return pred_array

        except requests.exceptions.Timeout:
            logger.error("HUB request timeout (>1s)")
            self.metrics.record_prediction(time.time() - pred_start, success=False)
            self.metrics.record_api_error('hub', 'timeout')
            return None
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            traceback.print_exc()
            self.metrics.record_prediction(time.time() - pred_start, success=False)
            self.metrics.record_api_error('hub', 'exception')
            return None

    def send_trading_signal(
        self,
        action: str,
        confidence: float
    ) -> bool:
        """
        Send trading signal to GTW via ZMQ

        Args:
            action: Trading action (BUY/SELL/HOLD)
            confidence: Signal confidence (0-1)

        Returns:
            True if successful
        """
        logger.info(f"Sending trading signal: {action} (confidence: {confidence:.4f})")

        # Record signal generation
        self.metrics.record_trading_signal(action)

        if self.dry_run:
            logger.info("  [DRY RUN] Signal not actually sent")
            return True

        zmq_context = None
        zmq_socket = None
        zmq_start = time.time()

        try:
            # Create ZMQ context and socket
            zmq_context = zmq.Context()
            zmq_socket = zmq_context.socket(zmq.REQ)
            zmq_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5s timeout
            zmq_socket.setsockopt(zmq.SNDTIMEO, 5000)

            gtw_addr = f"tcp://{self.gtw_host}:{self.gtw_port}"
            zmq_socket.connect(gtw_addr)

            # Prepare trading command
            command = {
                "action": "place_order" if action != "HOLD" else "check_connection",
                "symbol": self.symbol,
                "signal": action,
                "confidence": float(confidence),
                "timestamp": datetime.now().isoformat()
            }

            # Send command
            zmq_socket.send_json(command)

            # Wait for response
            response = zmq_socket.recv_json()

            logger.info(f"  GTW Response: {response}")

            # Record successful send
            zmq_duration = time.time() - zmq_start
            self.metrics.record_zmq_send(zmq_duration, success=True)
            self.metrics.record_trading_signal(action, executed=True)

            return True

        except zmq.error.Again:
            logger.error("  ZMQ timeout - GTW may not be running")
            self.metrics.record_zmq_send(time.time() - zmq_start, success=False)
            return False
        except zmq.error.ZMQError as e:
            logger.error(f"  ZMQ error: {e}")
            self.metrics.record_zmq_send(time.time() - zmq_start, success=False)
            return False
        except Exception as e:
            logger.error(f"  Error sending signal: {e}")
            traceback.print_exc()
            self.metrics.record_zmq_send(time.time() - zmq_start, success=False)
            return False
        finally:
            # Cleanup ZMQ resources
            if zmq_socket:
                try:
                    zmq_socket.close()
                except:
                    pass

            if zmq_context:
                try:
                    zmq_context.term()
                except:
                    pass

    def execute_trading_cycle(self):
        """
        Execute one complete trading cycle

        This is the main job that runs on schedule:
        1. Fetch market data
        2. Build features
        3. Request prediction from HUB
        4. Execute trade if threshold exceeded
        """
        logger.info("=" * 80)
        logger.info(f"TRADING CYCLE START: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        cycle_start = time.time()
        success = True

        try:
            # Update daemon uptime
            uptime = time.time() - self.start_time
            self.metrics.set_uptime(uptime)

            # Step 1: Fetch market data
            df = self.fetch_market_data()
            if df is None or len(df) == 0:
                logger.warning("No market data - skipping cycle")
                self.metrics.record_cycle_end(cycle_start, success=False)
                return

            # Step 2: Build features
            logger.info("Building features...")
            feat_start = time.time()

            # Tabular features (latest)
            features_tabular_df = self.feature_builder.build_features(df, self.symbol)
            if features_tabular_df is None:
                logger.error("Feature building failed - skipping cycle")
                self.metrics.record_cycle_end(cycle_start, success=False)
                return

            features_tabular = features_tabular_df.values  # (1, 23)

            # Sequential features (60-bar window)
            features_sequential = self.feature_builder.build_sequence(df, sequence_length=60)
            if features_sequential is None:
                logger.error("Sequence building failed - skipping cycle")
                self.metrics.record_cycle_end(cycle_start, success=False)
                return

            features_sequential = features_sequential.reshape(1, 60, 23)  # (1, 60, 23)

            logger.info(f"✓ Features ready:")
            logger.info(f"  Tabular: {features_tabular.shape}")
            logger.info(f"  Sequential: {features_sequential.shape}")

            # Record feature build time
            self.metrics.record_feature_build(time.time() - feat_start)

            # Step 3: Request prediction from HUB
            predictions = self.request_prediction(features_tabular, features_sequential)
            if predictions is None:
                logger.error("Prediction failed - skipping cycle")
                self.metrics.record_cycle_end(cycle_start, success=False)
                return

            # Step 4: Make trading decision
            # Predictions: [prob_sell, prob_hold, prob_buy]
            action_idx = np.argmax(predictions[0])
            actions = ['SELL', 'HOLD', 'BUY']
            action = actions[action_idx]
            confidence = predictions[0][action_idx]

            logger.info(f"Decision: {action} (confidence: {confidence:.4f})")

            # Step 5: Execute trade if confidence > threshold
            if confidence > self.threshold and action != 'HOLD':
                exec_success = self.send_trading_signal(action, confidence)
                if exec_success:
                    logger.info(f"✓ Trade executed: {action}")
                else:
                    logger.error(f"✗ Trade execution failed")
                    success = False
            else:
                logger.info(f"No trade (confidence {confidence:.4f} <= {self.threshold})")

            logger.info("=" * 80)
            logger.info(f"TRADING CYCLE COMPLETE")
            logger.info("=" * 80)

            # Record successful cycle
            self.metrics.record_cycle_end(cycle_start, success=success)

        except Exception as e:
            # NEVER crash the daemon
            logger.error(f"!!! CYCLE ERROR: {e}")
            logger.error(traceback.format_exc())
            logger.error("Daemon continues running...")
            self.metrics.record_cycle_end(cycle_start, success=False)

    def start(self):
        """
        Start the sentinel daemon

        Runs indefinitely, executing trading cycles on schedule
        """
        logger.info("=" * 80)
        logger.info("STARTING SENTINEL DAEMON")
        logger.info("=" * 80)

        # Start metrics HTTP server (Task #085)
        try:
            self.metrics.start_http_server()
            logger.info(f"✓ Metrics endpoint available at http://0.0.0.0:{self.metrics_port}/metrics")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise

        # Schedule job to run every minute at :58 seconds
        schedule.every(1).minutes.at(":58").do(self.execute_trading_cycle)

        logger.info("Schedule configured: Every 1 minute at :58 seconds")
        logger.info("Press Ctrl+C to stop daemon")
        logger.info("=" * 80)

        # Run immediately on start
        logger.info("Running initial cycle...")
        self.execute_trading_cycle()

        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("Daemon stopped by user (Ctrl+C)")
            logger.info("=" * 80)
            # Shutdown metrics server
            try:
                self.metrics.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down metrics: {e}")
        except Exception as e:
            logger.error(f"Daemon crashed: {e}")
            logger.error(traceback.format_exc())
            raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Sentinel Trading Daemon")
    parser.add_argument(
        "--hub-host",
        default=os.getenv("HUB_HOST", "172.19.141.254"),
        help="HUB server host"
    )
    parser.add_argument(
        "--hub-port",
        type=int,
        default=int(os.getenv("HUB_PORT", "5001")),
        help="HUB server port"
    )
    parser.add_argument(
        "--gtw-host",
        default=os.getenv("GTW_HOST", "172.19.141.255"),
        help="GTW server host"
    )
    parser.add_argument(
        "--gtw-port",
        type=int,
        default=int(os.getenv("GTW_PORT", "5555")),
        help="GTW server port"
    )
    parser.add_argument(
        "--symbol",
        default="EURUSD",
        help="Trading symbol"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.6,
        help="Probability threshold for trading"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (no actual trades)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Live trading mode (disables dry-run)"
    )
    parser.add_argument(
        "--metrics-port",
        type=int,
        default=int(os.getenv("METRICS_PORT", "8000")),
        help="Prometheus metrics endpoint port (Task #085)"
    )

    args = parser.parse_args()

    # Initialize daemon
    daemon = SentinelDaemon(
        hub_host=args.hub_host,
        hub_port=args.hub_port,
        gtw_host=args.gtw_host,
        gtw_port=args.gtw_port,
        symbol=args.symbol,
        threshold=args.threshold,
        dry_run=not args.live,  # Dry run unless --live specified
        metrics_port=args.metrics_port  # Prometheus metrics port (Task #085)
    )

    # Start daemon
    daemon.start()


if __name__ == "__main__":
    main()
