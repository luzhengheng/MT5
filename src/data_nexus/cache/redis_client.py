"""
Redis Cache Client Wrapper

Provides RedisClient class for managing Redis connections and operations.
Includes JSON serialization support and convenience methods for common
caching patterns.

Usage:
    from src.data_nexus.cache.redis_client import RedisClient

    redis = RedisClient()
    redis.ping()  # Health check

    # String operations
    redis.set("key", "value")
    value = redis.get("key")

    # JSON operations
    redis.set_json("user:123", {"name": "Alice", "balance": 100.0})
    user = redis.get_json("user:123")

    # Hash operations
    redis.hset("market:EURUSD", "bid", "1.0850")
    bid = redis.hget("market:EURUSD", "bid")
"""

import json
from typing import Any, Optional, Dict, List
import redis
from redis import Redis, ConnectionPool

from ..config import RedisConfig


class RedisClient:
    """
    Redis cache client with connection pooling and JSON serialization.

    Wraps redis-py library with convenience methods for common caching
    patterns used in MT5-CRS.
    """

    def __init__(
        self,
        config: Optional[RedisConfig] = None,
        max_connections: int = 50,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis client.

        Args:
            config: Redis configuration (default: load from env)
            max_connections: Max connections in pool
            decode_responses: If True, decode bytes to strings automatically
        """
        self.config = config or RedisConfig()
        self.decode_responses = decode_responses

        # Create connection pool
        self.pool = ConnectionPool(
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            max_connections=max_connections,
            decode_responses=decode_responses,
        )

        # Create Redis client
        self.client: Redis = redis.Redis(connection_pool=self.pool)

    # ----------------------------------------------------------------------
    # Health Check
    # ----------------------------------------------------------------------

    def ping(self) -> bool:
        """
        Ping Redis server.

        Returns:
            True if PONG response received

        Raises:
            redis.ConnectionError: If connection fails
        """
        response = self.client.ping()
        return response is True

    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            return self.ping()
        except Exception:
            return False

    # ----------------------------------------------------------------------
    # String Operations
    # ----------------------------------------------------------------------

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set string value.

        Args:
            key: Cache key
            value: String value
            ex: Expiration in seconds (optional)

        Returns:
            True if successful
        """
        return self.client.set(key, value, ex=ex)

    def get(self, key: str) -> Optional[str]:
        """
        Get string value.

        Args:
            key: Cache key

        Returns:
            Value as string, or None if not found
        """
        return self.client.get(key)

    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        return self.client.delete(*keys)

    def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        return self.client.exists(key) > 0

    # ----------------------------------------------------------------------
    # JSON Operations (with serialization)
    # ----------------------------------------------------------------------

    def set_json(self, key: str, obj: Any, ex: Optional[int] = None) -> bool:
        """
        Set JSON-serialized object.

        Args:
            key: Cache key
            obj: Python object (dict, list, etc.)
            ex: Expiration in seconds (optional)

        Returns:
            True if successful
        """
        json_str = json.dumps(obj)
        return self.client.set(key, json_str, ex=ex)

    def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON-deserialized object.

        Args:
            key: Cache key

        Returns:
            Python object, or None if not found
        """
        json_str = self.client.get(key)
        if json_str is None:
            return None
        return json.loads(json_str)

    # ----------------------------------------------------------------------
    # Hash Operations
    # ----------------------------------------------------------------------

    def hset(self, name: str, key: str, value: str) -> int:
        """
        Set hash field.

        Args:
            name: Hash name
            key: Field name
            value: Field value

        Returns:
            1 if new field, 0 if updated
        """
        return self.client.hset(name, key, value)

    def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get hash field.

        Args:
            name: Hash name
            key: Field name

        Returns:
            Field value, or None if not found
        """
        return self.client.hget(name, key)

    def hgetall(self, name: str) -> Dict[str, str]:
        """
        Get all hash fields.

        Args:
            name: Hash name

        Returns:
            Dictionary of all fields
        """
        return self.client.hgetall(name)

    def hdel(self, name: str, *keys: str) -> int:
        """
        Delete hash fields.

        Args:
            name: Hash name
            *keys: Field names to delete

        Returns:
            Number of fields deleted
        """
        return self.client.hdel(name, *keys)

    # ----------------------------------------------------------------------
    # List Operations
    # ----------------------------------------------------------------------

    def lpush(self, name: str, *values: str) -> int:
        """
        Push values to list head.

        Args:
            name: List name
            *values: Values to push

        Returns:
            List length after push
        """
        return self.client.lpush(name, *values)

    def rpush(self, name: str, *values: str) -> int:
        """
        Push values to list tail.

        Args:
            name: List name
            *values: Values to push

        Returns:
            List length after push
        """
        return self.client.rpush(name, *values)

    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        Get list range.

        Args:
            name: List name
            start: Start index (0-based)
            end: End index (-1 for all)

        Returns:
            List of values
        """
        return self.client.lrange(name, start, end)

    # ----------------------------------------------------------------------
    # Expiration
    # ----------------------------------------------------------------------

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set key expiration.

        Args:
            key: Cache key
            seconds: TTL in seconds

        Returns:
            True if expiration set
        """
        return self.client.expire(key, seconds)

    def ttl(self, key: str) -> int:
        """
        Get key TTL.

        Args:
            key: Cache key

        Returns:
            TTL in seconds (-1 if no expiration, -2 if not found)
        """
        return self.client.ttl(key)

    # ----------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------

    def flushdb(self) -> bool:
        """
        Flush current database (delete all keys).

        WARNING: Use with caution!

        Returns:
            True if successful
        """
        return self.client.flushdb()

    def close(self) -> None:
        """Close connection pool."""
        self.pool.disconnect()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (close connections)."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"RedisClient(config={self.config})"
