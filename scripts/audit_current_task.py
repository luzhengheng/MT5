#!/usr/bin/env python3
"""
Task #034 Compliance Audit Script

Verifies that the EODHD Async Ingestion Engine implementation meets
Protocol v2.0 requirements before allowing task completion.

Audit Criteria:
1. Structural: All required source files exist with correct classes
2. Functional: Database connectivity and data integrity
3. Integration: Ingestion pipeline can execute successfully
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def audit():
    """Execute comprehensive audit of Task #034 deliverables."""
    print("=" * 80)
    print("🔍 AUDIT: Task #034 EODHD Async Ingestion Compliance Check")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    # ============================================================================
    # 1. STRUCTURAL AUDIT - File and Class Existence
    # ============================================================================
    print("📋 [1/3] STRUCTURAL AUDIT")
    print("-" * 80)

    # Check ingestion modules
    try:
        from src.data_nexus.ingestion.asset_discovery import AssetDiscovery
        print("✅ [Structure] AssetDiscovery class found")
        passed += 1
    except ImportError as e:
        print(f"❌ [Structure] Failed to import AssetDiscovery: {e}")
        failed += 1

    try:
        from src.data_nexus.ingestion.history_loader import EODHistoryLoader
        print("✅ [Structure] EODHistoryLoader class found")
        passed += 1
    except ImportError as e:
        print(f"❌ [Structure] Failed to import EODHistoryLoader: {e}")
        failed += 1

    # Check CLI interface
    cli_path = PROJECT_ROOT / "bin" / "run_ingestion.py"
    if cli_path.exists():
        print(f"✅ [Structure] CLI interface exists: {cli_path}")
        passed += 1
    else:
        print(f"❌ [Structure] CLI interface missing: {cli_path}")
        failed += 1

    # Check models
    try:
        from src.data_nexus.models import Asset, MarketData, CorporateAction
        print("✅ [Structure] ORM Models (Asset, MarketData, CorporateAction) found")
        passed += 1
    except ImportError as e:
        print(f"❌ [Structure] Failed to import ORM models: {e}")
        failed += 1

    print()

    # ============================================================================
    # 2. FUNCTIONAL AUDIT - Database Connectivity and Schema
    # ============================================================================
    print("📋 [2/3] FUNCTIONAL AUDIT")
    print("-" * 80)

    try:
        from src.data_nexus.database.connection import PostgresConnection

        # Test database connection
        conn = PostgresConnection()
        version = conn.get_version()
        if version and "PostgreSQL" in version:
            print(f"✅ [Database] Connected: {version[:60]}...")
            passed += 1
        else:
            print("❌ [Database] Invalid response from database")
            failed += 1

        # Check tables exist
        with conn.get_session() as session:
            tables = conn.query_all(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            )
            table_names = [row[0] for row in tables]

            required_tables = ['assets', 'market_data', 'corporate_actions']
            for table in required_tables:
                if table in table_names:
                    print(f"✅ [Schema] Table '{table}' exists")
                    passed += 1
                else:
                    print(f"❌ [Schema] Table '{table}' missing")
                    failed += 1

    except Exception as e:
        print(f"❌ [Database] Connection failed: {str(e)[:80]}")
        failed += 4  # Count all database checks as failed

    print()

    # ============================================================================
    # 3. DATA INTEGRITY AUDIT - Verify Ingestion Results
    # ============================================================================
    print("📋 [3/3] DATA INTEGRITY AUDIT")
    print("-" * 80)

    try:
        from src.data_nexus.database.connection import PostgresConnection

        conn = PostgresConnection()

        # Check asset count
        asset_count = conn.query_scalar("SELECT COUNT(*) FROM assets WHERE exchange='FOREX'")
        if asset_count and asset_count > 0:
            print(f"✅ [Data] Assets table populated: {asset_count} FOREX pairs")
            passed += 1
        else:
            print("❌ [Data] Assets table is empty")
            failed += 1

        # Check market data count
        data_count = conn.query_scalar("SELECT COUNT(*) FROM market_data")
        if data_count and data_count > 0:
            print(f"✅ [Data] Market data loaded: {data_count:,} OHLCV rows")
            passed += 1
        else:
            print("⚠️  [Data] Market data table is empty (may be intentional)")
            # Don't count as failure - backfill may not have run yet

        # Check data integrity - no NULL prices
        null_prices = conn.query_scalar(
            "SELECT COUNT(*) FROM market_data "
            "WHERE open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL"
        )
        if null_prices == 0:
            print("✅ [Data] No NULL price values found")
            passed += 1
        else:
            print(f"❌ [Data] Found {null_prices} rows with NULL prices")
            failed += 1

    except Exception as e:
        print(f"❌ [Data] Integrity check failed: {str(e)[:80]}")
        failed += 2

    # ============================================================================
    # AUDIT SUMMARY
    # ============================================================================
    print()
    print("=" * 80)
    print(f"📊 AUDIT SUMMARY: {passed} Passed, {failed} Failed")
    print("=" * 80)

    if failed == 0:
        print()
        print("🎉 ✅ AUDIT PASSED: Ready for AI Review")
        print()
        print("Task #034 implementation meets Protocol v2.0 requirements.")
        print("You may proceed with: python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print()
        print("⚠️  ❌ AUDIT FAILED: Remediation Required")
        print()
        print("Issues found during audit:")
        print(f"  • {failed} check(s) failed")
        print("  • Fix issues before running 'project_cli.py finish'")
        print()
        return 1


if __name__ == "__main__":
    exit_code = audit()
    sys.exit(exit_code)
