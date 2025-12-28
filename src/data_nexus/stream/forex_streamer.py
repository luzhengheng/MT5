"""
Real-time Forex Streaming Engine via EODHD WebSocket API

Provides async WebSocket client for streaming live Forex quotes from EODHD.
Data is cached in Redis for real-time access and optionally persisted to TimescaleDB.

Task #036: Real-time WebSocket Engine Implementation
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Callable, List
import websockets
import redis.asyncio as aioredis
from src.data_nexus.config import DatabaseConfig, RedisConfig

logger = logging.getLogger(__name__)


class ForexStreamer:
    """
    EODHD WebSocket client for real-time Forex streaming.

    Features:
    - Async WebSocket connection to EODHD streaming API
    - Real-time quote caching in Redis
    - Automatic reconnection on disconnect
    - Configurable quote handler callbacks

    Usage:
        streamer = ForexStreamer(api_key="your_key", symbols=["EURUSD", "GBPUSD"])
        await streamer.start()
    """

    def __init__(
        self,
        api_key: str,
        symbols: List[str],
        redis_config: Optional[RedisConfig] = None,
        db_config: Optional[DatabaseConfig] = None,
        on_quote: Optional[Callable] = None
    ):
        """
        Initialize Forex streamer.

        Args:
            api_key: EODHD API key
            symbols: List of Forex symbols to subscribe (e.g., ["EURUSD", "GBPUSD"])
            redis_config: Redis configuration (default: localhost:6379)
            db_config: Database configuration (optional, for persistence)
            on_quote: Callback function called on each quote received
        """
        self.api_key = api_key
        self.symbols = symbols
        self.redis_config = redis_config or RedisConfig()
        self.db_config = db_config
        self.on_quote = on_quote

        # Connection state
        self.ws = None
        self.redis_client = None
        self.running = False

        # WebSocket URL for EODHD streaming
        self.ws_url = f"wss://ws.eodhistoricaldata.com/ws/forex?api_token={self.api_key}"

    async def connect_redis(self):
        """Establish Redis connection for caching."""
        redis_url = self.redis_config.connection_url()
        self.redis_client = await aioredis.from_url(
            redis_url,
            decode_responses=True
        )
        logger.info(f"Connected to Redis: {redis_url}")

    async def disconnect_redis(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def subscribe(self):
        """Send subscription message to WebSocket."""
        if not self.ws:
            raise RuntimeError("WebSocket not connected")

        # EODHD subscription format
        subscribe_msg = {
            "action": "subscribe",
            "symbols": ",".join(self.symbols)
        }

        await self.ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to symbols: {self.symbols}")

    async def handle_quote(self, quote: dict):
        """
        Process incoming quote.

        Args:
            quote: Parsed quote data from EODHD
        """
        # Cache in Redis with 60-second expiry
        symbol = quote.get("s")  # Symbol
        if symbol and self.redis_client:
            cache_key = f"forex:quote:{symbol}"
            await self.redis_client.setex(
                cache_key,
                60,  # TTL: 60 seconds
                json.dumps(quote)
            )
            logger.debug(f"Cached quote for {symbol}")

        # Call custom handler if provided
        if self.on_quote:
            await self.on_quote(quote)

    async def message_loop(self):
        """Main message processing loop."""
        try:
            async for message in self.ws:
                try:
                    quote = json.loads(message)
                    await self.handle_quote(quote)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse quote: {message}")
                except Exception as e:
                    logger.error(f"Error handling quote: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Message loop error: {e}")

    async def start(self, auto_reconnect: bool = True, max_reconnect_attempts: int = 10):
        """
        Start the WebSocket streaming connection with auto-reconnect.

        This will:
        1. Connect to Redis for caching
        2. Establish WebSocket connection to EODHD
        3. Subscribe to configured symbols
        4. Enter message processing loop
        5. Auto-reconnect on disconnect (if enabled)

        Args:
            auto_reconnect: Enable automatic reconnection on disconnect
            max_reconnect_attempts: Maximum reconnection attempts (0 = infinite)
        """
        self.running = True
        reconnect_count = 0

        # Connect to Redis once
        await self.connect_redis()

        try:
            while self.running:
                try:
                    # Establish WebSocket connection
                    async with websockets.connect(
                        self.ws_url,
                        ping_interval=20,
                        ping_timeout=10
                    ) as ws:
                        self.ws = ws
                        logger.info(f"Connected to EODHD WebSocket: {self.ws_url}")

                        # Reset reconnect counter on successful connection
                        reconnect_count = 0

                        # Subscribe to symbols
                        await self.subscribe()

                        # Enter message loop (blocks until disconnect)
                        await self.message_loop()

                except websockets.exceptions.ConnectionClosed as e:
                    logger.warning(f"WebSocket connection closed: {e}")

                    if not auto_reconnect or not self.running:
                        break

                    reconnect_count += 1
                    if max_reconnect_attempts > 0 and reconnect_count > max_reconnect_attempts:
                        logger.error(f"Max reconnection attempts ({max_reconnect_attempts}) exceeded")
                        break

                    # Exponential backoff: 2^n seconds (max 60s)
                    delay = min(2 ** reconnect_count, 60)
                    logger.info(f"Reconnecting in {delay}s... (attempt {reconnect_count})")
                    await asyncio.sleep(delay)

                except Exception as e:
                    logger.error(f"Streaming error: {e}")

                    if not auto_reconnect:
                        break

                    # Wait before retry
                    await asyncio.sleep(5)

        finally:
            await self.disconnect_redis()
            self.running = False
            logger.info("ForexStreamer shutdown complete")

    async def stop(self):
        """Stop the streaming connection gracefully."""
        self.running = False
        if self.ws:
            await self.ws.close()
        await self.disconnect_redis()
        logger.info("ForexStreamer stopped")

    def is_running(self) -> bool:
        """Check if streamer is active."""
        return self.running


# Example usage function
async def example_usage():
    """Example of how to use ForexStreamer."""

    async def on_quote_received(quote: dict):
        """Custom handler for quotes."""
        symbol = quote.get("s")
        price = quote.get("p")
        timestamp = quote.get("t")
        print(f"[{timestamp}] {symbol}: {price}")

    # Create streamer for major Forex pairs
    streamer = ForexStreamer(
        api_key="your_api_key_here",
        symbols=["EURUSD", "GBPUSD", "USDJPY"],
        on_quote=on_quote_received
    )

    # Start streaming (runs until stopped)
    try:
        await streamer.start()
    except KeyboardInterrupt:
        await streamer.stop()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
