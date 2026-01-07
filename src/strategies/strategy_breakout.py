#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Breakout Strategy - Automated Trading Loop
TASK #060: First automated strategy implementing:
Market Data (5556) -> Signal Trigger -> Trade Execution (5555) -> DingTalk Notification

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import json
import time
import zmq
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import centralized configuration (TASK #060 requirement: zero hardcoding)
from src.config import (
    ZMQ_MARKET_DATA_URL,
    ZMQ_EXECUTION_URL,
    GTW_HOST,
    GTW_PORT,
    ZMQ_MARKET_DATA_PORT,
    DINGTALK_WEBHOOK_URL,
    DINGTALK_SECRET,
    DEFAULT_SYMBOL,
    DEFAULT_VOLUME
)

# Import DingTalk notifier
try:
    from src.dashboard.notifier import send_notification
    DINGTALK_AVAILABLE = True
except ImportError:
    DINGTALK_AVAILABLE = False
    print("[STRATEGY_LOG] WARNING: DingTalk notifier not available")


def log(message, level="INFO"):
    """Structured logging with [STRATEGY_LOG] prefix for grep verification"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[STRATEGY_LOG] [{timestamp}] [{level}] {message}", flush=True)


def connect_market_data():
    """Connect to market data stream (ZMQ SUB on port 5556)"""
    try:
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(ZMQ_MARKET_DATA_URL)
        socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics
        socket.setsockopt(zmq.RCVTIMEO, 30000)  # 30 second timeout

        log(f"Connected to market data: {ZMQ_MARKET_DATA_URL}")
        return socket
    except Exception as e:
        log(f"Failed to connect to market data: {e}", "ERROR")
        raise


def connect_execution_gateway():
    """Connect to execution gateway (ZMQ REQ on port 5555)"""
    try:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(ZMQ_EXECUTION_URL)
        socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        socket.setsockopt(zmq.SNDTIMEO, 5000)

        log(f"Connected to execution gateway: {ZMQ_EXECUTION_URL}")
        return socket
    except Exception as e:
        log(f"Failed to connect to execution gateway: {e}", "ERROR")
        raise


def send_order(exec_socket, action="BUY", symbol=None, volume=None):
    """
    Send order to execution gateway and wait for response

    Args:
        exec_socket: ZMQ REQ socket
        action: "BUY" or "SELL"
        symbol: Trading symbol (defaults to config)
        volume: Order volume (defaults to config)

    Returns:
        dict: Order response with status and ticket
    """
    symbol = symbol or DEFAULT_SYMBOL
    volume = volume or DEFAULT_VOLUME

    order_request = {
        "action": action,
        "symbol": symbol,
        "volume": volume,
        "magic": 20260107,
        "comment": "TASK_060_Breakout"
    }

    try:
        log(f"Sending {action} order: {symbol} @ {volume} lots")
        exec_socket.send_json(order_request)

        # Wait for response
        response = exec_socket.recv_json()

        if response.get("status") == "FILLED":
            ticket = response.get("ticket", "UNKNOWN")
            price = response.get("price", 0.0)
            log(f"✅ Order FILLED - Ticket: {ticket}, Price: {price}", "SUCCESS")

            # Send DingTalk notification
            if DINGTALK_AVAILABLE and DINGTALK_WEBHOOK_URL:
                try:
                    send_notification(
                        f"🎯 Strategy Executed\n"
                        f"Action: {action}\n"
                        f"Symbol: {symbol}\n"
                        f"Volume: {volume}\n"
                        f"Ticket: {ticket}\n"
                        f"Price: {price}"
                    )
                except Exception as e:
                    log(f"DingTalk notification failed: {e}", "WARNING")
        else:
            log(f"❌ Order REJECTED - Response: {response}", "ERROR")

        return response

    except zmq.error.Again:
        log("Order execution timeout - gateway not responding", "ERROR")
        return {"status": "TIMEOUT", "error": "Gateway timeout"}
    except Exception as e:
        log(f"Order execution failed: {e}", "ERROR")
        return {"status": "ERROR", "error": str(e)}


def run_strategy():
    """
    Main strategy loop: Simple breakout trigger
    Logic: Receive 3 ticks -> Trigger BUY order -> Exit
    """
    log("=" * 70)
    log("Simple Breakout Strategy Starting")
    log("=" * 70)
    log(f"Market Data: {ZMQ_MARKET_DATA_URL} (Port {ZMQ_MARKET_DATA_PORT})")
    log(f"Execution Gateway: {ZMQ_EXECUTION_URL} (Host: {GTW_HOST}, Port: {GTW_PORT})")
    log(f"Symbol: {DEFAULT_SYMBOL}")
    log(f"Volume: {DEFAULT_VOLUME}")
    log("=" * 70)

    # Connect to both endpoints
    try:
        market_socket = connect_market_data()
        exec_socket = connect_execution_gateway()
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        log("Exiting strategy", "ERROR")
        return 1

    # Strategy state
    tick_counter = 0
    trigger_count = 3  # Trigger after 3 ticks

    log(f"Waiting for {trigger_count} ticks to trigger breakout...")

    try:
        while tick_counter < trigger_count:
            try:
                # Receive tick data
                message = market_socket.recv_string()
                tick_data = json.loads(message)

                tick_counter += 1

                # Log tick information
                symbol = tick_data.get("symbol", "UNKNOWN")
                bid = tick_data.get("bid", 0.0)
                ask = tick_data.get("ask", 0.0)
                timestamp = tick_data.get("timestamp", "")

                log(f"TICK #{tick_counter}: {symbol} Bid={bid:.5f} Ask={ask:.5f} Time={timestamp}")

                # Check if trigger reached
                if tick_counter >= trigger_count:
                    log(f"🚀 TRIGGER REACHED - Executing BUY order after {tick_counter} ticks")
                    break

            except zmq.error.Again:
                log("Market data timeout - no ticks received in 30 seconds", "WARNING")
                log("Please check if MT5 EA is broadcasting on port 5556", "WARNING")
                return 1
            except json.JSONDecodeError as e:
                log(f"Invalid tick data format: {e}", "WARNING")
                continue
            except Exception as e:
                log(f"Error receiving tick: {e}", "ERROR")
                continue

        # Execute trade
        log("=" * 70)
        log("EXECUTING TRADE")
        log("=" * 70)

        response = send_order(exec_socket, action="BUY")

        if response.get("status") == "FILLED":
            log("=" * 70)
            log("✅ STRATEGY EXECUTION COMPLETE", "SUCCESS")
            log(f"Ticket: {response.get('ticket', 'N/A')}")
            log(f"Price: {response.get('price', 'N/A')}")
            log("=" * 70)
            return 0
        else:
            log("=" * 70)
            log("❌ STRATEGY EXECUTION FAILED", "ERROR")
            log(f"Response: {response}")
            log("=" * 70)
            return 1

    except KeyboardInterrupt:
        log("Strategy interrupted by user", "WARNING")
        return 130
    except Exception as e:
        log(f"Unexpected error in strategy loop: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        return 1
    finally:
        # Cleanup
        try:
            market_socket.close()
            exec_socket.close()
        except:
            pass


def main():
    """Entry point with exception handling"""
    try:
        exit_code = run_strategy()
        sys.exit(exit_code)
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
