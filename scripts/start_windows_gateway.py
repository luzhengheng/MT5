"""
Task #083: Windows Gateway Service Starter

This script will be run on Windows to properly initialize and start the ZMQ gateway service.

SECURITY:
- Writes PID to gateway.pid for graceful shutdown
- Uses proper signal handling (SIGTERM) for clean termination
- Implements proper logging to both file and console
"""

import sys
import os
import signal
import threading
import logging
from pathlib import Path

# Configure logging
log_file = Path(__file__).parent.parent / "logs" / "gateway_service.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger.info(f"Python path: {project_root}")
logger.info(f"Python version: {sys.version}")

# Global references for signal handling
gateway_instance = None
should_exit = threading.Event()


def signal_handler(signum, frame):
    """Handle SIGTERM and SIGINT for graceful shutdown."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    should_exit.set()
    if gateway_instance:
        try:
            gateway_instance.stop()
        except Exception as e:
            logger.error(f"Error stopping gateway: {e}")


def write_pid_file():
    """Write process ID to file for external monitoring."""
    pid_file = Path(project_root) / "gateway.pid"
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))
    logger.info(f"PID file written: {pid_file}")
    return pid_file


def remove_pid_file():
    """Clean up PID file on exit."""
    pid_file = Path(project_root) / "gateway.pid"
    try:
        if pid_file.exists():
            pid_file.unlink()
            logger.info(f"PID file removed: {pid_file}")
    except Exception as e:
        logger.warning(f"Failed to remove PID file: {e}")


def main():
    """Main entry point for gateway service."""
    global gateway_instance

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Import dependencies
        from src.gateway.zmq_service import ZmqGatewayService
        from src.gateway.mt5_service import MT5Service
        import time

        logger.info("Starting Windows Gateway Service...")
        logger.info("Initializing MT5 Service...")

        # Create MT5 service (handles trading)
        mt5 = MT5Service()

        logger.info("Initializing ZMQ Gateway...")
        # Create ZMQ gateway
        gateway_instance = ZmqGatewayService(mt5_handler=mt5)

        logger.info("Starting gateway...")
        gateway_instance.start()

        # Write PID for external process management
        pid_file = write_pid_file()

        logger.info("=" * 70)
        logger.info("✅ Windows Gateway Service started successfully!")
        logger.info("   - Listening on port 5555 (Commands)")
        logger.info("   - Publishing on port 5556 (Market Data)")
        logger.info("   - PID: %d", os.getpid())
        logger.info("   - Log file: %s", log_file)
        logger.info("=" * 70)

        # Keep running until signal received
        try:
            while not should_exit.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")

        logger.info("Shutting down gateway...")
        gateway_instance.stop()
        logger.info("Gateway stopped")

    except Exception as e:
        logger.error(f"Failed to start gateway: {e}", exc_info=True)
        sys.exit(1)
    finally:
        remove_pid_file()
        logger.info("Service shutdown complete")


if __name__ == "__main__":
    main()
