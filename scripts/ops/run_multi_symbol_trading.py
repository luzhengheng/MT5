#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Symbol Trading Engine Launcher (Task #123)

Main entry point for concurrent multi-symbol trading with asyncio orchestration.
Supports command-line configuration and graceful shutdown.

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import asyncio
import logging
import argparse
import signal
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.concurrent_trading_engine import (
    ConcurrentTradingEngine
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - %(name)s - "
        "%(levelname)s - %(message)s"
    ),
    handlers=[
        logging.FileHandler(
            PROJECT_ROOT / "logs" / "multi_symbol_trading.log"
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class MultiSymbolTradingLauncher:
    """Launcher for multi-symbol concurrent trading engine."""

    def __init__(
        self,
        config_path: str,
        zmq_host: str = "172.19.141.255",
        zmq_port: int = 5555,
        duration: int = 0
    ):
        """
        Initialize launcher.

        Args:
            config_path: Path to trading config YAML
            zmq_host: ZMQ gateway host
            zmq_port: ZMQ gateway port
            duration: Duration in seconds per symbol (0 = infinite)
        """
        self.config_path = config_path
        self.zmq_host = zmq_host
        self.zmq_port = zmq_port
        self.duration = duration
        self.engine = None
        self.running = False

    async def run(self) -> int:
        """
        Run the trading engine.

        Returns:
            Exit code (0 = success, 1 = error)
        """
        logger.info(f"{BLUE}{'=' * 80}{RESET}")
        logger.info(
            f"{BLUE}🚀 Multi-Symbol Trading Engine Launcher (Task #123)"
            f"{RESET}"
        )
        logger.info(f"{BLUE}{'=' * 80}{RESET}")

        # Validate config file
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.error(
                f"{RED}❌ Config file not found: "
                f"{self.config_path}{RESET}"
            )
            return 1

        logger.info(f"\n📋 Configuration:")
        logger.info(f"  Config: {self.config_path}")
        logger.info(f"  ZMQ: {self.zmq_host}:{self.zmq_port}")
        logger.info(f"  Duration: {'∞' if self.duration == 0 else f'{self.duration}s'}")
        logger.info(f"  Started: {datetime.now().isoformat()}")
        logger.info()

        try:
            # Initialize engine
            self.engine = ConcurrentTradingEngine(
                config_path=self.config_path,
                zmq_host=self.zmq_host,
                zmq_port=self.zmq_port
            )
            self.running = True

            # Run trading
            await self.engine.run_concurrent_trading(
                duration_s=self.duration
            )

            logger.info(
                f"{GREEN}✅ Trading completed successfully{RESET}"
            )
            return 0

        except KeyboardInterrupt:
            logger.info(
                f"\n{YELLOW}🛑 Interrupted by user{RESET}"
            )
            return 0

        except Exception as e:
            logger.error(
                f"{RED}❌ Fatal error: {e}{RESET}"
            )
            return 1

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        logger.info(
            f"\n{YELLOW}Received signal {signum}{RESET}"
        )
        if self.engine:
            asyncio.create_task(self.engine.shutdown())


async def async_main(args) -> int:
    """
    Async main entry point.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    launcher = MultiSymbolTradingLauncher(
        config_path=args.config,
        zmq_host=args.zmq_host,
        zmq_port=args.zmq_port,
        duration=args.duration
    )

    # Setup signal handlers
    signal.signal(signal.SIGINT, launcher.signal_handler)

    return await launcher.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Symbol Trading Engine Launcher (Task #123)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python3 scripts/ops/run_multi_symbol_trading.py

  # Run with custom config
  python3 scripts/ops/run_multi_symbol_trading.py \\
    --config custom_config.yaml

  # Run with custom ZMQ endpoint
  python3 scripts/ops/run_multi_symbol_trading.py \\
    --zmq-host 192.168.1.100 --zmq-port 5555

  # Run for 60 seconds
  python3 scripts/ops/run_multi_symbol_trading.py \\
    --duration 60
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/trading_config.yaml",
        help="Path to trading configuration YAML "
             "(default: config/trading_config.yaml)"
    )

    parser.add_argument(
        "--zmq-host",
        type=str,
        default="172.19.141.255",
        help="ZMQ gateway host (default: 172.19.141.255)"
    )

    parser.add_argument(
        "--zmq-port",
        type=int,
        default=5555,
        help="ZMQ gateway port (default: 5555)"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Duration in seconds per symbol (0 = infinite) "
             "(default: 0)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0 (Task #123)"
    )

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(
        getattr(logging, args.log_level)
    )

    logger.info(
        f"{GREEN}✅ Launcher initialized{RESET}"
    )
    logger.info(f"  Log level: {args.log_level}")

    # Run async main
    try:
        exit_code = asyncio.run(async_main(args))
        sys.exit(exit_code)
    except Exception as e:
        logger.error(
            f"{RED}❌ Unexpected error: {e}{RESET}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
