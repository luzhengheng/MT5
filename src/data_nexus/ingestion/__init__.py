"""
Data Nexus Ingestion Module

Async ETL pipeline for EODHD data ingestion.

Components:
- AssetDiscovery: Exchange symbol list discovery
- EODHistoryLoader: Async OHLCV data downloader
- Retry policies and error handling
"""

from .asset_discovery import AssetDiscovery
from .history_loader import EODHistoryLoader

__all__ = ["AssetDiscovery", "EODHistoryLoader"]
