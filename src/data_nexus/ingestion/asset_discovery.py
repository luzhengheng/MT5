"""
Asset Discovery Service

Fetches exchange symbol lists from EODHD and ingests them into the assets table.

Design:
- Async HTTP requests using aiohttp
- Upsert logic: New assets marked with last_synced=NULL
- Reactivates existing assets if they were previously inactive
"""

import asyncio
import csv
import io
import logging
from datetime import datetime
from typing import Optional

import aiohttp
from sqlalchemy.orm import Session

from src.data_nexus.config import DatabaseConfig
from src.data_nexus.database.connection import PostgresConnection
from src.data_nexus.models import Asset

logger = logging.getLogger(__name__)

# EODHD API endpoint
EODHD_API_URL = "https://eodhistoricaldata.com/api"

# Standard timeout for HTTP requests
REQUEST_TIMEOUT = 30


class AssetDiscovery:
    """
    Discovers and ingests assets from EODHD exchange symbol lists.

    Endpoint: /api/exchange-symbol-list/{exchange}
    Response: CSV format with columns: [Code, Exchange, Name, Type, Country, Currency, ISIN, ...]

    Example:
        discovery = AssetDiscovery(api_key, db_config)
        count = await discovery.discover_exchange('US')
    """

    def __init__(self, api_key: str, db_config: Optional[DatabaseConfig] = None):
        """
        Initialize asset discovery service.

        Args:
            api_key: EODHD API key
            db_config: Database configuration (uses default if None)
        """
        self.api_key = api_key
        self.db_config = db_config or DatabaseConfig()
        self.timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async def discover_exchange(self, exchange: str) -> int:
        """
        Discover and ingest symbols for an exchange.

        Args:
            exchange: Exchange code (e.g., 'US', 'LSE', 'TSE')

        Returns:
            Number of newly added or reactivated assets

        Logic:
            1. Fetch symbol list from EODHD API
            2. Parse CSV response
            3. Upsert each symbol into assets table:
               - New symbol: Insert with last_synced=NULL
               - Existing symbol: Update is_active=True
            4. Commit to database
            5. Return count
        """
        logger.info(f"Starting discovery for exchange: {exchange}")

        try:
            # Fetch symbol list from API
            symbols = await self._fetch_symbol_list(exchange)
            if not symbols:
                logger.warning(f"No symbols fetched for {exchange}")
                return 0

            # Upsert to database
            count = self._upsert_assets(exchange, symbols)
            logger.info(f"Discovery complete for {exchange}: {count} assets added/updated")
            return count

        except Exception as e:
            logger.error(f"Asset discovery failed for {exchange}: {e}")
            raise

    async def _fetch_symbol_list(self, exchange: str) -> list[dict]:
        """
        Fetch symbol list from EODHD API.

        Args:
            exchange: Exchange code

        Returns:
            List of symbol dictionaries with keys: code, exchange, name, type, ...

        Raises:
            ValueError: If API returns error or invalid response
            asyncio.TimeoutError: If request times out
        """
        url = f"{EODHD_API_URL}/exchange-symbol-list/{exchange}"
        params = {
            "api_token": self.api_key,
            "fmt": "csv",
        }

        logger.debug(f"Fetching symbol list from {url}")

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 404:
                        raise ValueError(f"Exchange {exchange} not found (404)")
                    elif resp.status == 403:
                        raise ValueError(f"Access denied to {exchange} (403) - check API subscription")
                    elif resp.status >= 500:
                        raise ValueError(f"Server error {resp.status} from EODHD")
                    elif resp.status != 200:
                        raise ValueError(f"Unexpected status {resp.status}")

                    text = await resp.text()

            # Parse CSV
            symbols = self._parse_symbol_csv(text)
            logger.info(f"Fetched {len(symbols)} symbols for {exchange}")
            return symbols

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching symbols for {exchange}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch symbols for {exchange}: {e}")
            raise

    def _parse_symbol_csv(self, csv_text: str) -> list[dict]:
        """
        Parse CSV response from EODHD.

        Expected columns: Code, Exchange, Name, Type, Country, Currency, ISIN, ...

        Args:
            csv_text: CSV response body

        Returns:
            List of dictionaries with at least: code, exchange, name, type
        """
        symbols = []
        reader = csv.DictReader(io.StringIO(csv_text))

        for row in reader:
            try:
                # Extract required fields (handle case variations)
                code = row.get("Code") or row.get("code")
                exchange = row.get("Exchange") or row.get("exchange")
                name = row.get("Name") or row.get("name") or ""
                asset_type = row.get("Type") or row.get("type") or "Common Stock"

                if not code or not exchange:
                    logger.warning(f"Skipping row with missing code/exchange: {row}")
                    continue

                symbols.append({
                    "code": code,
                    "exchange": exchange,
                    "name": name,
                    "type": asset_type,
                })

            except Exception as e:
                logger.warning(f"Error parsing CSV row: {e}")
                continue

        return symbols

    def _upsert_assets(self, exchange: str, symbols: list[dict]) -> int:
        """
        Upsert symbols into assets table.

        Logic:
        - New symbol: Insert with is_active=True, last_synced=NULL
        - Existing symbol: Update is_active=True (reactivate if was inactive)

        Args:
            exchange: Exchange code
            symbols: List of symbol dictionaries

        Returns:
            Number of newly added assets
        """
        conn = PostgresConnection()
        count = 0

        with conn.get_session() as session:
            for sym in symbols:
                try:
                    code = f"{sym['code']}.{exchange}"  # e.g., AAPL.US

                    # Check if asset exists
                    asset = session.query(Asset).filter_by(symbol=code).first()

                    if asset:
                        # Asset exists, reactivate if needed
                        if not asset.is_active:
                            asset.is_active = True
                            session.commit()
                            logger.debug(f"Reactivated {code}")
                    else:
                        # New asset, create with last_synced=NULL
                        asset = Asset(
                            symbol=code,
                            exchange=exchange,
                            asset_type=sym.get("type", "Common Stock"),
                            is_active=True,
                            last_synced=None,  # Signals: needs historical data
                        )
                        session.add(asset)
                        count += 1
                        logger.debug(f"Added new asset {code}")

                except Exception as e:
                    logger.error(f"Error upserting {sym.get('code')}: {e}")
                    session.rollback()
                    continue

            # Final commit
            session.commit()

        logger.info(f"Upserted {count} new assets for {exchange}")
        return count
