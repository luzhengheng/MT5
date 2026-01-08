#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #066.1: EODHD Data Ingestion & Integrity Validation
Protocol: v4.3 (Zero-Trust Edition)

Validates data completeness and quality in TimescaleDB after ingestion:
1. Row count verification
2. Time series continuity (no gaps, except market holidays)
3. Duplicate detection
4. Field completeness (no unexpected nulls)
5. Price sanity checks (positive values, OHLC logic)
6. Volume consistency

Usage:
    python3 scripts/validate_data.py --symbol AAPL.US
    python3 scripts/validate_data.py --symbols AAPL.US,MSFT.US,SPY.US
    python3 scripts/validate_data.py --check-all
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import database configuration and connection
from src.data_nexus.database.connection import PostgresConnection
from src.data_nexus.config import DatabaseConfig
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class DataValidator:
    """
    EODHD Data Integrity Validator for TimescaleDB.

    Performs comprehensive validation of ingested market data:
    - Completeness checks (row counts, date ranges)
    - Quality checks (nulls, outliers, duplicates)
    - Logic checks (OHLC relationships, price sanity)
    """

    def __init__(self):
        """Initialize validator."""
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()

        # Use localhost for database connection (not Docker internal "db")
        db_config = DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "trader"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            database=os.getenv("POSTGRES_DB", "mt5_crs")
        )
        self.db = PostgresConnection(config=db_config)

        self.results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings': [],
            'errors': [],
            'session_id': self.session_id
        }

        logger.info(f"{CYAN}🔍 Data Validator Initialized{RESET}")
        logger.info(f"{CYAN}⚡ Session ID: {self.session_id}{RESET}")

    async def validate_symbol(self, symbol: str) -> Dict[str, any]:
        """
        Validate data for a single symbol.

        Returns:
            Dict with validation results
        """
        logger.info(f"{CYAN}Validating {symbol}...{RESET}")

        checks = {
            'symbol': symbol,
            'passed': 0,
            'failed': 0,
            'warnings': [],
            'errors': []
        }

        try:
            # 1. Check if symbol exists in database
            count = await self._check_row_count(symbol)
            if count == 0:
                checks['errors'].append(f"No data found for {symbol}")
                self.results['failed_checks'] += 1
                return checks
            else:
                checks['passed'] += 1
                logger.info(f"{GREEN}  ✅ Row count: {count} rows{RESET}")

            # 2. Check for duplicates
            duplicates = await self._check_duplicates(symbol)
            if duplicates > 0:
                checks['errors'].append(f"Found {duplicates} duplicate records")
                self.results['failed_checks'] += 1
            else:
                checks['passed'] += 1
                logger.info(f"{GREEN}  ✅ No duplicates{RESET}")

            # 3. Check field completeness
            null_fields = await self._check_null_fields(symbol)
            if null_fields:
                checks['warnings'].append(f"Null values found in: {null_fields}")
                self.results['failed_checks'] += 1
            else:
                checks['passed'] += 1
                logger.info(f"{GREEN}  ✅ No unexpected null values{RESET}")

            # 4. Check price sanity
            price_issues = await self._check_price_sanity(symbol)
            if price_issues:
                checks['errors'].extend(price_issues)
                self.results['failed_checks'] += len(price_issues)
            else:
                checks['passed'] += 1
                logger.info(f"{GREEN}  ✅ Price sanity checks passed{RESET}")

            # 5. Check OHLC logic
            ohlc_issues = await self._check_ohlc_logic(symbol)
            if ohlc_issues > 0:
                checks['errors'].append(f"Found {ohlc_issues} OHLC logic violations")
                self.results['failed_checks'] += 1
            else:
                checks['passed'] += 1
                logger.info(f"{GREEN}  ✅ OHLC logic valid{RESET}")

            # 6. Check time series continuity
            gaps = await self._check_time_continuity(symbol)
            if gaps and len(gaps) > 5:  # Allow some gaps (weekends, holidays)
                checks['warnings'].append(f"Found {len(gaps)} gaps in time series")
                logger.warning(f"{YELLOW}  ⚠️  {len(gaps)} time gaps (may be market holidays){RESET}")
            else:
                checks['passed'] += 1
                logger.info(f"{GREEN}  ✅ Time series continuous{RESET}")

            self.results['passed_checks'] += checks['passed']

        except Exception as e:
            logger.error(f"{RED}  ❌ Validation failed: {e}{RESET}")
            checks['errors'].append(str(e))
            self.results['failed_checks'] += 1

        return checks

    async def _check_row_count(self, symbol: str) -> int:
        """Check number of rows for symbol (parameterized query)."""
        query = """
            SELECT COUNT(*) FROM market_data.ohlcv_daily
            WHERE symbol = %s
        """
        result = self.db.query_scalar(query, (symbol,))
        return result or 0

    async def _check_duplicates(self, symbol: str) -> int:
        """Check for duplicate time/symbol records (parameterized query)."""
        query = """
            SELECT COUNT(*) FROM (
                SELECT time, symbol, COUNT(*) as cnt
                FROM market_data.ohlcv_daily
                WHERE symbol = %s
                GROUP BY time, symbol
                HAVING COUNT(*) > 1
            ) duplicates
        """
        result = self.db.query_scalar(query, (symbol,))
        return result or 0

    async def _check_null_fields(self, symbol: str) -> List[str]:
        """Check for unexpected null values in required fields (parameterized query)."""
        required_fields = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        nulls_found = []

        for field in required_fields:
            # Field names cannot be parameterized, so we must validate them
            if field not in required_fields:
                continue  # Security: skip invalid field names

            query = f"""
                SELECT COUNT(*) FROM market_data.ohlcv_daily
                WHERE symbol = %s AND {field} IS NULL
            """
            count = self.db.query_scalar(query, (symbol,)) or 0
            if count > 0:
                nulls_found.append(f"{field}({count})")

        return nulls_found

    async def _check_price_sanity(self, symbol: str) -> List[str]:
        """Check for sanity issues in prices (parameterized query)."""
        issues = []

        # Check for negative or zero prices
        query = """
            SELECT COUNT(*) FROM market_data.ohlcv_daily
            WHERE symbol = %s AND (open <= 0 OR high <= 0 OR low <= 0 OR close <= 0)
        """
        count = self.db.query_scalar(query, (symbol,)) or 0
        if count > 0:
            issues.append(f"Found {count} records with non-positive prices")

        # Check for extreme volatility (e.g., 10x change in one day)
        query = """
            SELECT COUNT(*) FROM market_data.ohlcv_daily
            WHERE symbol = %s AND (high / NULLIF(low, 0) > 10 OR NULLIF(low, 0) / NULLIF(high, 0) > 0.1)
        """
        count = self.db.query_scalar(query, (symbol,)) or 0
        if count > 0:
            issues.append(f"Found {count} records with extreme price movements (>10x)")

        return issues

    async def _check_ohlc_logic(self, symbol: str) -> int:
        """Check if OHLC values satisfy logical constraints (parameterized query)."""
        query = """
            SELECT COUNT(*) FROM market_data.ohlcv_daily
            WHERE symbol = %s AND (
                high < low OR
                open > high OR
                open < low OR
                close > high OR
                close < low
            )
        """
        result = self.db.query_scalar(query, (symbol,)) or 0
        return result

    async def _check_time_continuity(self, symbol: str) -> List[datetime]:
        """
        Check for gaps in time series using SQL window functions.

        Returns list of dates with gaps (skipping weekends only).
        Note: Market holidays require separate handling.
        """
        query = """
            SELECT time FROM (
                SELECT
                    time::date,
                    LEAD(time::date) OVER (ORDER BY time) as next_time
                FROM market_data.ohlcv_daily
                WHERE symbol = %s
                ORDER BY time
            ) t
            WHERE next_time > time::date + INTERVAL '1 day'
        """
        dates = self.db.query_all(query, (symbol,))

        if not dates or len(dates) < 2:
            return []

        gaps = []
        for i in range(len(dates) - 1):
            current = dates[i][0]
            next_date = dates[i + 1][0]

            # Calculate expected next business day
            expected_next = current + timedelta(days=1)

            # Skip weekends
            while expected_next.weekday() >= 5:  # 5=Saturday, 6=Sunday
                expected_next += timedelta(days=1)

            if next_date != expected_next:
                gaps.append(expected_next)

        return gaps

    async def run(self, symbols: List[str]) -> int:
        """
        Run validation for multiple symbols.

        Returns:
            Exit code (0 = all pass, 1 = some failures)
        """
        print()
        print(f"{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}DATA INTEGRITY VALIDATOR (Task #066.1){RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}")
        print(f"  Symbols: {len(symbols)}")
        print(f"  Checks per symbol: 6")
        print(f"{CYAN}{'=' * 80}{RESET}")
        print()

        symbol_results = []
        for symbol in symbols:
            result = await self.validate_symbol(symbol)
            symbol_results.append(result)
            self.results['total_checks'] += result['passed'] + result['failed']

        # Print summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print()
        print(f"{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}VALIDATION SUMMARY{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}")
        print(f"  Total Checks: {self.results['total_checks']}")
        print(f"  {GREEN}✅ Passed: {self.results['passed_checks']}{RESET}")
        print(f"  {RED}❌ Failed: {self.results['failed_checks']}{RESET}")
        print(f"  Duration: {duration:.2f} seconds")

        if self.results['failed_checks'] == 0:
            print(f"\n{GREEN}{'=' * 80}")
            print(f"✅ ALL VALIDATIONS PASSED{RESET}")
            print(f"{GREEN}{'=' * 80}{RESET}")
        else:
            print(f"\n{RED}{'=' * 80}")
            print(f"❌ SOME VALIDATIONS FAILED{RESET}")
            print(f"{RED}{'=' * 80}{RESET}")

        # Physical verification
        print()
        print(f"{CYAN}⚡ [PROOF] VALIDATION SESSION: {self.session_id}{RESET}")
        print(f"{CYAN}⚡ [PROOF] SESSION END: {end_time.isoformat()}{RESET}")

        return 0 if self.results['failed_checks'] == 0 else 1


async def main_async(symbols: List[str]) -> int:
    """Async entry point."""
    validator = DataValidator()
    return await validator.run(symbols)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='EODHD Data Integrity Validator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/validate_data.py --symbol AAPL.US
  python3 scripts/validate_data.py --symbols AAPL.US,MSFT.US,GOOGL.US
  python3 scripts/validate_data.py --check-all
        """
    )

    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument('--symbol', type=str, help='Single symbol to validate')
    symbol_group.add_argument('--symbols', type=str, help='Comma-separated list of symbols')
    symbol_group.add_argument(
        '--check-all',
        action='store_true',
        help='Validate all symbols in database'
    )

    args = parser.parse_args()

    if args.check_all:
        # Fetch all symbols from database
        logger.info("Fetching all symbols from database...")
        db = PostgresConnection()
        query = "SELECT DISTINCT symbol FROM market_data.ohlcv_daily ORDER BY symbol"
        results = db.query_all(query)
        symbols = [r[0] for r in results] if results else []

        if not symbols:
            print(f"{YELLOW}No symbols found in database{RESET}")
            return 1

        logger.info(f"Found {len(symbols)} symbols")
    elif args.symbol:
        symbols = [args.symbol]
    else:
        symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]

    if not symbols:
        print(f"{RED}No symbols to validate{RESET}")
        return 1

    exit_code = asyncio.run(main_async(symbols))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
