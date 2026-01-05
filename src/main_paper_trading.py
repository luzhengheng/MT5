#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Trading Main Loop - TASK #030

Implements the complete Signal -> Risk -> Order -> Fill cycle:
  1. StrategyEngine generates trading signals from market data
  2. PortfolioManager checks risk (position conflicts)
  3. ExecutionGateway sends orders to Windows MT5 gateway
  4. Portfolio updates based on fill responses

Integration of:
- TASK #028: StrategyEngine (real-time inference)
- TASK #029: ExecutionGateway (E2E order execution)
- TASK #030: PortfolioManager (state tracking & risk)

Protocol: v4.2 (Agentic-Loop)
"""

import os
import sys
import json
import time
import logging
import zmq
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    ZMQ_MARKET_DATA_URL,
    ZMQ_EXECUTION_URL,
    GTW_HOST,
    GTW_PORT,
    GTW_TIMEOUT_MS,
    TRADING_SYMBOL,
    DEFAULT_VOLUME
)
from src.strategy.portfolio import PortfolioManager, create_fill_response
from src.strategy.engine import StrategyEngine


# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'paper_trading.log')
    ]
)
logger = logging.getLogger("PaperTrading")


# ============================================================================
# Execution Gateway Wrapper
# ============================================================================

class ExecutionGateway:
    """
    Wrapper around ZMQ REQ socket for order execution (TASK #029)

    Sends orders to Windows MT5 gateway via tcp://172.19.141.255:5555
    """

    def __init__(self, host: str = GTW_HOST, port: int = GTW_PORT, timeout_ms: int = GTW_TIMEOUT_MS):
        """
        Initialize execution gateway

        Args:
            host: Gateway IP (default: 172.19.141.255 from config)
            port: Gateway port (default: 5555 from config)
            timeout_ms: Request timeout in milliseconds
        """
        self.host = host
        self.port = port
        self.timeout_ms = timeout_ms
        self.url = f"tcp://{host}:{port}"

        # ZMQ socket
        self.context = zmq.Context()
        self.socket = None
        self.logger = logging.getLogger("Gateway")

    def connect(self):
        """Establish connection to gateway"""
        try:
            self.socket = self.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
            self.socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
            self.socket.connect(self.url)
            self.logger.info(f"✅ Connected to {self.url}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False

    def send_order(self, order: Dict) -> Dict:
        """
        Send order to gateway and wait for response

        Args:
            order: Order dictionary with keys:
                - order_id, symbol, action, volume, price, confidence

        Returns:
            Response dictionary with keys:
                - status: "FILLED" or "REJECTED"
                - ticket: MT5 ticket number
                - filled_price: Execution price
                - filled_volume: Executed size
                - error: Error message if rejected
        """
        if not self.socket:
            if not self.connect():
                return {"status": "REJECTED", "error": "Gateway not connected"}

        try:
            # Send order as JSON
            self.socket.send_json(order)
            self.logger.info(f"[SEND] Order {order['order_id']}: {order['action']} {order['volume']} @ {order['price']}")

            # Wait for response with timeout
            response = self.socket.recv_json()
            self.logger.info(f"[RECV] Response: {response}")
            return response

        except zmq.error.Again:
            error_msg = f"Gateway timeout ({self.timeout_ms}ms) for order {order['order_id']}"
            self.logger.error(error_msg)
            return {
                "order_id": order['order_id'],
                "status": "REJECTED",
                "error": error_msg
            }

        except Exception as e:
            self.logger.error(f"Gateway error: {e}")
            return {
                "order_id": order['order_id'],
                "status": "REJECTED",
                "error": str(e)
            }

    def disconnect(self):
        """Close gateway connection"""
        if self.socket:
            self.socket.close()
        self.context.term()
        self.logger.info("Disconnected from gateway")


# ============================================================================
# Main Paper Trading Loop
# ============================================================================

def main():
    """
    Paper Trading Main Loop

    Flow:
        1. Initialize StrategyEngine, PortfolioManager, ExecutionGateway
        2. Loop forever:
            a. Wait for market tick from engine
            b. Process tick and generate signal
            c. Check risk (PortfolioManager.check_risk)
            d. If approved, create order
            e. Send to gateway
            f. Update portfolio with fill response
    """

    print("=" * 80)
    print("🚀 MT5-CRS Paper Trading System - TASK #030")
    print("=" * 80)
    print()

    # Step 1: Initialize components
    logger.info("=" * 80)
    logger.info("Initializing components...")
    logger.info("=" * 80)

    try:
        # Strategy Engine (TASK #028)
        logger.info(f"Initializing StrategyEngine...")
        engine = StrategyEngine(
            symbol=TRADING_SYMBOL,
            zmq_market_data_url=ZMQ_MARKET_DATA_URL,
            zmq_execution_url=ZMQ_EXECUTION_URL
        )
        logger.info(f"✅ StrategyEngine initialized for {TRADING_SYMBOL}")

        # Portfolio Manager (TASK #030)
        logger.info(f"Initializing PortfolioManager...")
        portfolio = PortfolioManager(symbol=TRADING_SYMBOL)
        logger.info(f"✅ PortfolioManager initialized")

        # Execution Gateway (TASK #029)
        logger.info(f"Initializing ExecutionGateway...")
        gateway = ExecutionGateway(host=GTW_HOST, port=GTW_PORT, timeout_ms=GTW_TIMEOUT_MS)
        if not gateway.connect():
            logger.warning("⚠️  Gateway connection failed - will retry per order")

        logger.info()
        logger.info("Configuration:")
        logger.info(f"  Symbol: {TRADING_SYMBOL}")
        logger.info(f"  Volume: {DEFAULT_VOLUME}L per trade")
        logger.info(f"  Market Data: {ZMQ_MARKET_DATA_URL}")
        logger.info(f"  Execution: {ZMQ_EXECUTION_URL}")
        logger.info()

    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 2: Main trading loop
    logger.info("=" * 80)
    logger.info("Starting Paper Trading Loop (Press Ctrl+C to stop)")
    logger.info("=" * 80)
    print()

    cycle_count = 0
    signal_count = 0
    order_count = 0
    fill_count = 0

    try:
        engine.start()  # This starts the ZMQ subscription loop in the engine

        # The engine's main loop is in start()
        # For this simple integration, we'll use the engine's tick processing

        while True:
            cycle_count += 1

            try:
                # Step 2a: Get next tick from engine
                # (In real deployment, this is driven by ZMQ ticks)
                # For now, we simulate tick receipt in engine

                # The engine processes ticks internally via _process_tick()
                # which calls _compute_features(), model inference, and _generate_signal()

                # Step 2b: Get signal from engine
                # (Accessing engine's internal state - in production this would be via callback)
                if hasattr(engine, '_last_signal') and engine._last_signal is not None:
                    signal, confidence = engine._last_signal
                    signal_count += 1

                    logger.info(f"\n[CYCLE {cycle_count}] Signal={signal}, Confidence={confidence:.2f}")

                    # Step 2c: Check risk
                    if portfolio.check_risk(signal):
                        # Step 2d: Create order
                        current_price = 1.0543  # Placeholder - would come from tick
                        order = portfolio.create_order(signal, price=current_price, volume=DEFAULT_VOLUME)

                        if order:
                            order_count += 1

                            # Step 2e: Send to gateway
                            order_dict = {
                                "order_id": order.order_id,
                                "symbol": order.symbol,
                                "action": order.action,
                                "volume": order.volume,
                                "price": order.entry_price,
                                "confidence": confidence
                            }

                            response = gateway.send_order(order_dict)

                            # Step 2f: Update portfolio
                            if response.get("status") == "FILLED":
                                fill_count += 1

                                fill_response = {
                                    "order_id": order.order_id,
                                    "ticket": response.get("ticket", 0),
                                    "filled_price": response.get("filled_price", order.entry_price),
                                    "filled_volume": response.get("filled_volume", order.volume),
                                    "status": "FILLED",
                                    "timestamp": time.time()
                                }

                                portfolio.on_fill(fill_response)
                                logger.info(f"[PORTFOLIO] {portfolio.get_position_summary()}")

                            else:
                                logger.warning(f"Order {order.order_id} rejected: {response.get('error')}")

                    else:
                        logger.info(f"[CYCLE {cycle_count}] Signal blocked by risk check")

                # Small delay to avoid busy loop
                time.sleep(0.1)

            except KeyboardInterrupt:
                raise  # Re-raise to be caught by outer handler

            except Exception as e:
                logger.error(f"Cycle error: {e}")
                import traceback
                traceback.print_exc()
                continue

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("🛑 Shutdown requested")
        logger.info("=" * 80)

    finally:
        # Cleanup
        gateway.disconnect()

        logger.info()
        logger.info("=" * 80)
        logger.info("Paper Trading Summary")
        logger.info("=" * 80)
        logger.info(f"Cycles: {cycle_count}")
        logger.info(f"Signals: {signal_count}")
        logger.info(f"Orders: {order_count}")
        logger.info(f"Fills: {fill_count}")
        logger.info(f"Position: {portfolio.get_position_summary()}")
        logger.info()
        logger.info("✅ Paper trading session closed")

        return 0


if __name__ == "__main__":
    sys.exit(main())
