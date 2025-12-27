#!/usr/bin/env python3
"""
Work Order #023: Live Trading Strategy Integration
====================================================

Main Entry Point - The Brain Awakens

This is the main entry point for the MT5-CRS Live Trading System,
integrating the ZmqClient (The Axon) with the TradingBot (The Brain).

Architecture:
    Linux Brain (This Process)
        ↓
    ZmqClient (The Axon)
        ↓ (TCP 172.19.141.255:5555/5556)
    Windows Gateway
        ↓
    MT5 Terminal

Workflow:
    1. Initialize ZmqClient (The Axon)
    2. Initialize TradingBot (The Conscious Loop)
    3. Start bot (blocks until KeyboardInterrupt)
    4. Graceful shutdown

Previous State (Work Order #022):
- ZeroMQ fabric established
- Windows Gateway listening
- Linux Brain has ZmqClient

Current Goal (Work Order #023):
- Demonstrate "Heartbeat -> Decision -> Execution" loop
- Drive Windows Gateway from Linux Brain
- Graceful shutdown on KeyboardInterrupt

Protocol: v2.0 (Strict TDD & Dual-Brain)

Usage:
    python3 src/main.py

    Or with custom parameters:
    MT5_SYMBOL=GBPUSD.s TRADING_INTERVAL=5 python3 src/main.py

Environment Variables:
    MT5_SYMBOL: Trading symbol (default: "EURUSD.s")
    TRADING_INTERVAL: Loop interval in seconds (default: 10)
    GATEWAY_IP: Windows Gateway IP (default: "172.19.141.255")
"""

import sys
import os
import logging

# Add project root to path
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mt5_bridge.zmq_client import ZmqClient
from src.bot.trading_bot import TradingBot
from src.strategy.live_adapter import LiveStrategyAdapter


# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'trading_brain.log')
    ]
)

logger = logging.getLogger("Brain")


# ============================================================================
# Configuration
# ============================================================================

def load_config() -> dict:
    """
    Load configuration from environment variables.

    Returns:
        Configuration dictionary

    Environment Variables:
        MT5_SYMBOL: Trading symbol (default: "EURUSD.s")
        TRADING_INTERVAL: Loop interval in seconds (default: 10)
        GATEWAY_IP: Windows Gateway IP (default: "172.19.141.255")
    """
    config = {
        'symbol': os.getenv('MT5_SYMBOL', 'EURUSD.s'),
        'interval': int(os.getenv('TRADING_INTERVAL', '10')),
        'gateway_ip': os.getenv('GATEWAY_IP', '172.19.141.255')
    }

    logger.info("Configuration loaded:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    return config


# ============================================================================
# Main Function
# ============================================================================

def main():
    """
    Main entry point for the MT5-CRS Live Trading System.

    Workflow:
        1. Load configuration
        2. Initialize ZmqClient (The Axon)
        3. Initialize TradingBot (The Brain)
        4. Start bot (blocks until KeyboardInterrupt)
        5. Graceful shutdown

    Returns:
        0 on success, 1 on error
    """
    print("=" * 70)
    print("🧠 MT5-CRS Live Trading System - The Brain Awakens")
    print("=" * 70)
    print()

    try:
        # Step 1: Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        print()

        # Step 2: Initialize ZmqClient (The Axon)
        logger.info(f"Initializing ZmqClient (Axon) to {config['gateway_ip']}...")
        client = ZmqClient(host=config['gateway_ip'])
        logger.info("✅ ZmqClient initialized")
        print()

        # Step 3a: Initialize ML Strategy Adapter (Work Order #024)
        logger.info("Initializing ML Strategy Adapter...")
        strategy = LiveStrategyAdapter()
        logger.info("✅ ML Strategy Adapter initialized")

        # Step 3b: Initialize TradingBot (The Brain)
        logger.info("Initializing TradingBot (The Conscious Loop)...")
        bot = TradingBot(
            zmq_client=client,
            strategy_engine=strategy,  # Work Order #024: Real ML strategy
            symbol=config['symbol'],
            interval=config['interval']
        )
        logger.info("✅ TradingBot initialized")
        print()

        # Step 4: Display startup info
        print("=" * 70)
        print("✅ System Ready")
        print("=" * 70)
        print()
        print("Configuration:")
        print(f"  Symbol: {config['symbol']}")
        print(f"  Interval: {config['interval']} seconds")
        print(f"  Gateway: {config['gateway_ip']}")
        print()
        print("⚠️  Important:")
        print("  - Press Ctrl+C to stop gracefully")
        print("  - Logs saved to: trading_brain.log")
        print("  - Windows Gateway must be running")
        print()
        print("=" * 70)
        print()

        # Step 5: Start bot (blocks until KeyboardInterrupt)
        logger.info("Starting TradingBot...")
        bot.start()

        # If we get here, bot stopped normally
        logger.info("✅ System shutdown complete")
        return 0

    except KeyboardInterrupt:
        # User requested shutdown
        logger.info("\n🛑 KeyboardInterrupt received - Shutting down...")
        print("\n" + "=" * 70)
        print("🛑 Shutdown Requested")
        print("=" * 70)
        print()
        logger.info("✅ Graceful shutdown complete")
        return 0

    except Exception as e:
        # Unexpected error
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

        print("\n" + "=" * 70)
        print("❌ System Error")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("Check trading_brain.log for details")
        print()

        return 1


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())
