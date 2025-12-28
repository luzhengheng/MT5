"""
TimescaleDB/PostgreSQL Connection Management

Provides PostgresConnection class for managing database connections using
SQLAlchemy. Supports connection pooling, health checks, and raw SQL execution.

Usage:
    from src.data_nexus.database.connection import PostgresConnection

    conn = PostgresConnection()
    version = conn.query_scalar("SELECT version()")
    print(f"PostgreSQL: {version}")

    with conn.engine.connect() as db_conn:
        result = db_conn.execute("SELECT * FROM market_data LIMIT 10")
        for row in result:
            print(row)
"""

from typing import Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from ..config import DatabaseConfig


class PostgresConnection:
    """
    PostgreSQL/TimescaleDB connection manager.

    Manages SQLAlchemy engine with connection pooling and provides
    convenience methods for health checks and queries.
    """

    def __init__(
        self,
        config: Optional[DatabaseConfig] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        echo: bool = False,
    ):
        """
        Initialize PostgreSQL connection.

        Args:
            config: Database configuration (default: load from env)
            pool_size: Number of connections to maintain in pool
            max_overflow: Max connections beyond pool_size
            pool_timeout: Timeout in seconds for getting connection
            echo: If True, log all SQL statements (verbose)
        """
        self.config = config or DatabaseConfig()
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout

        # Create SQLAlchemy engine
        self.engine: Engine = create_engine(
            self.config.connection_string(),
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            echo=echo,
        )

    def query_scalar(self, sql: str) -> Any:
        """
        Execute SQL query and return single scalar value.

        Args:
            sql: SQL query string

        Returns:
            Single value from first row, first column

        Example:
            >>> conn = PostgresConnection()
            >>> conn.query_scalar("SELECT COUNT(*) FROM market_data")
            42
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(sql))
            return result.scalar()

    def query_one(self, sql: str) -> Optional[tuple]:
        """
        Execute SQL query and return first row.

        Args:
            sql: SQL query string

        Returns:
            First row as tuple, or None if no results
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(sql))
            return result.fetchone()

    def query_all(self, sql: str) -> list:
        """
        Execute SQL query and return all rows.

        Args:
            sql: SQL query string

        Returns:
            List of rows (each row is a tuple)
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(sql))
            return result.fetchall()

    def execute(self, sql: str) -> None:
        """
        Execute SQL statement (INSERT, UPDATE, DELETE, etc.).

        Args:
            sql: SQL statement string
        """
        with self.engine.connect() as connection:
            connection.execute(text(sql))
            connection.commit()

    def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_version(self) -> str:
        """
        Get PostgreSQL version string.

        Returns:
            PostgreSQL version (e.g., "PostgreSQL 14.9 (TimescaleDB 2.12)")
        """
        return self.query_scalar("SELECT version()")

    def close(self) -> None:
        """Dispose of connection pool and close all connections."""
        self.engine.dispose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (close connections)."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"PostgresConnection(config={self.config})"
