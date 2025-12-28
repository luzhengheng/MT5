"""
Configuration Management for Data Nexus Infrastructure

Provides DatabaseConfig and RedisConfig dataclasses that load settings from
environment variables, with sensible defaults for local development.

Usage:
    from src.data_nexus.config import DatabaseConfig, RedisConfig

    db_config = DatabaseConfig()
    redis_config = RedisConfig()

    db_conn_string = db_config.connection_string()
    redis_url = redis_config.connection_url()
"""

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """TimescaleDB/PostgreSQL configuration."""

    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "trader")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    database: str = os.getenv("POSTGRES_DB", "mt5_crs")

    def connection_string(self) -> str:
        """
        Generate PostgreSQL connection string.

        Format: postgresql://user:password@host:port/database

        Returns:
            str: SQLAlchemy-compatible connection string
        """
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def __repr__(self) -> str:
        """String representation (without exposing password)."""
        return (
            f"DatabaseConfig(host={self.host}, port={self.port}, "
            f"user={self.user}, database={self.database})"
        )


@dataclass
class RedisConfig:
    """Redis cache configuration."""

    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))

    def connection_url(self) -> str:
        """
        Generate Redis connection URL.

        Format: redis://host:port/db

        Returns:
            str: Redis connection URL
        """
        return f"redis://{self.host}:{self.port}/{self.db}"

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RedisConfig(host={self.host}, port={self.port}, db={self.db})"
        )


# Factory functions for convenience
def get_database_config() -> DatabaseConfig:
    """Get database configuration instance."""
    return DatabaseConfig()


def get_redis_config() -> RedisConfig:
    """Get Redis configuration instance."""
    return RedisConfig()
