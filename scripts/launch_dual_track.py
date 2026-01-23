#!/usr/bin/env python3
"""
Task #132: Dual-Track Live Launcher
Correctly initializes TradingBot with config/trading_config.yaml
"""
import os
import sys
import yaml
import time
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bot.trading_bot import TradingBot

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'execution.log')
    ]
)
logger = logging.getLogger("Launcher")

def load_config():
    config_path = PROJECT_ROOT / "config" / "trading_config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    logger.info("🚀 Initializing Dual-Track System (Task #132)...")
    config = load_config()
    
    # Extract Active Symbols
    active_symbols = [s['symbol'] for s in config['symbols'] if s.get('active', False)]
    logger.info(f"📋 Active Symbols: {active_symbols}")
    
    # Extract Gateway Config
    gateway_conf = config.get('gateway', {})
    host = gateway_conf.get('zmq_req_host', '172.19.141.251') # Default to fixed IP
    port = gateway_conf.get('zmq_req_port', 5555)
    
    bot = TradingBot(
        symbols=active_symbols,
        model_path="models/baseline_v1.json", 
        api_url="http://localhost:8001",
        zmq_market_url=f"tcp://{host}:5556",
        zmq_execution_host=host,
        zmq_execution_port=port,
        volume=0.01
    )
    
    if bot.connect():
        logger.info("✅ Bot Connected. Entering Main Loop...")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping...")
    else:
        logger.error("❌ Failed to connect to Gateway.")
        sys.exit(1)

if __name__ == "__main__":
    main()
