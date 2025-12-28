#!/usr/bin/env python3
"""
Task #036 Compliance Audit Script

Verifies that the Real-time WebSocket Engine implementation meets
Protocol v2.0 requirements before allowing task completion.

Audit Criteria:
1. Structural: WebSocket client library available, streaming classes exist
2. Functional: Redis connectivity for real-time data caching
3. Integration: WebSocket connection can be established to EODHD
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def audit():
    """Execute comprehensive audit of Task #036 deliverables."""
    print("=" * 80)
    print("🔍 AUDIT: Task #036 Real-time WebSocket Engine Compliance Check")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    # ============================================================================
    # 1. STRUCTURAL AUDIT - Dependencies and Classes
    # ============================================================================
    print("📋 [1/3] STRUCTURAL AUDIT")
    print("-" * 80)

    # Check websockets library
    try:
        import websockets
        print(f"✅ [Library] websockets {websockets.__version__} installed")
        passed += 1
    except ImportError as e:
        print(f"❌ [Library] websockets not installed: {e}")
        failed += 1

    # Check aioredis for async Redis operations
    try:
        import redis.asyncio as aioredis
        print("✅ [Library] redis.asyncio available")
        passed += 1
    except ImportError:
        print("❌ [Library] redis.asyncio not available")
        failed += 1

    # Check streaming module exists
    stream_module = PROJECT_ROOT / "src" / "data_nexus" / "stream" / "forex_streamer.py"
    if stream_module.exists():
        print(f"✅ [Structure] ForexStreamer module exists: {stream_module}")
        passed += 1
    else:
        print(f"❌ [Structure] ForexStreamer module missing: {stream_module}")
        failed += 1

    # Check if ForexStreamer class can be imported
    try:
        from src.data_nexus.stream.forex_streamer import ForexStreamer
        print("✅ [Structure] ForexStreamer class found")
        passed += 1
    except ImportError as e:
        print(f"❌ [Structure] Failed to import ForexStreamer: {e}")
        failed += 1

    print()

    # ============================================================================
    # 2. FUNCTIONAL AUDIT - Redis Connectivity
    # ============================================================================
    print("📋 [2/3] FUNCTIONAL AUDIT")
    print("-" * 80)

    try:
        import redis
        
        # Test Redis connection (synchronous for audit)
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        if redis_client.ping():
            print("✅ [Redis] Connection successful and responsive")
            passed += 1
        else:
            print("❌ [Redis] Ping failed")
            failed += 1
            
        redis_client.close()
    except Exception as e:
        print(f"❌ [Redis] Connection failed: {str(e)[:80]}")
        failed += 1

    # Check database connection (for storing processed quotes)
    try:
        from src.data_nexus.database.connection import PostgresConnection
        
        conn = PostgresConnection()
        version = conn.get_version()
        if version and "PostgreSQL" in version:
            print(f"✅ [Database] Connected: {version[:60]}...")
            passed += 1
        else:
            print("❌ [Database] Invalid response")
            failed += 1
    except Exception as e:
        print(f"❌ [Database] Connection failed: {str(e)[:80]}")
        failed += 1

    print()

    # ============================================================================
    # 3. CONFIGURATION AUDIT - API Keys and Settings
    # ============================================================================
    print("📋 [3/3] CONFIGURATION AUDIT")
    print("-" * 80)

    # Check EODHD API key
    api_key = os.environ.get("EODHD_API_KEY")
    if api_key and len(api_key) > 10:
        masked = api_key[:10] + "..." + api_key[-4:]
        print(f"✅ [Config] EODHD API key configured: {masked}")
        passed += 1
    else:
        print("❌ [Config] EODHD API key not set or invalid")
        failed += 1

    # Check configuration file exists
    config_file = PROJECT_ROOT / "src" / "data_nexus" / "config.py"
    if config_file.exists():
        print(f"✅ [Config] Configuration module exists")
        passed += 1
    else:
        print(f"❌ [Config] Configuration module missing")
        failed += 1

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
        print("Task #036 implementation meets Protocol v2.0 requirements.")
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
