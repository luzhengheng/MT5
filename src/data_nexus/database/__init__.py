"""
Database module for Data Nexus.

Provides PostgreSQL/TimescaleDB connection management and utilities.
"""

from .connection import PostgresConnection

__all__ = ["PostgresConnection"]
