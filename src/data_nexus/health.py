"""
Health Check Utilities for Data Nexus

Provides functions to check the health of database and cache connections.

Usage:
    from src.data_nexus.health import check_all_services, check_database, check_cache

    # Check all services
    results = check_all_services()
    if all(results.values()):
        print("All services healthy")

    # Check individual services
    if check_database():
        print("Database is healthy")
    if check_cache():
        print("Cache is healthy")
"""

from typing import Dict
from .database.connection import PostgresConnection
from .cache.redis_client import RedisClient


def check_database(verbose: bool = False) -> bool:
    """
    Check if database connection is healthy.

    Args:
        verbose: If True, print status messages

    Returns:
        True if database is healthy, False otherwise
    """
    try:
        with PostgresConnection() as db:
            healthy = db.health_check()
            if verbose:
                if healthy:
                    version = db.get_version()
                    print(f"✅ Database: {version[:50]}...")
                else:
                    print("❌ Database: Health check failed")
            return healthy
    except Exception as e:
        if verbose:
            print(f"❌ Database Error: {e}")
        return False


def check_cache(verbose: bool = False) -> bool:
    """
    Check if Redis cache connection is healthy.

    Args:
        verbose: If True, print status messages

    Returns:
        True if cache is healthy, False otherwise
    """
    try:
        with RedisClient() as cache:
            healthy = cache.health_check()
            if verbose:
                if healthy:
                    print("✅ Redis: Connection successful")
                else:
                    print("❌ Redis: Health check failed")
            return healthy
    except Exception as e:
        if verbose:
            print(f"❌ Redis Error: {e}")
        return False


def check_all_services(verbose: bool = False) -> Dict[str, bool]:
    """
    Check health of all Data Nexus services.

    Args:
        verbose: If True, print status messages

    Returns:
        Dictionary with service names as keys and health status as values
    """
    results = {
        "database": check_database(verbose=verbose),
        "cache": check_cache(verbose=verbose),
    }
    return results


def is_all_healthy(verbose: bool = False) -> bool:
    """
    Check if all services are healthy.

    Args:
        verbose: If True, print status messages

    Returns:
        True if all services healthy, False otherwise
    """
    results = check_all_services(verbose=verbose)
    return all(results.values())
