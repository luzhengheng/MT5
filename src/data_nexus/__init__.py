"""
Data Nexus: Central data infrastructure for MT5-CRS.

Provides database and cache layers for persistent storage (TimescaleDB)
and real-time caching (Redis).

Modules:
    - config: Configuration management
    - database: PostgreSQL/TimescaleDB connections
    - cache: Redis caching operations
    - health: Health check utilities

Example:
    from src.data_nexus.config import DatabaseConfig, RedisConfig
    from src.data_nexus.database.connection import PostgresConnection
    from src.data_nexus.cache.redis_client import RedisClient

    # Initialize
    db = PostgresConnection()
    cache = RedisClient()

    # Health checks
    db_ok = db.health_check()
    cache_ok = cache.health_check()
"""

from .config import DatabaseConfig, RedisConfig
from .database.connection import PostgresConnection
from .cache.redis_client import RedisClient

__all__ = [
    "DatabaseConfig",
    "RedisConfig",
    "PostgresConnection",
    "RedisClient",
]

__version__ = "0.1.0"
