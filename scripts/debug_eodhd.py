#!/usr/bin/env python3
"""
Work Order #026.9: EODHD API Diagnostic Probe
==============================================

Test EODHD API connectivity with proper symbol format (.FOREX suffix).
This script verifies that the API can be reached before proceeding with
refactoring the fetcher code.

Protocol: v2.0 (Strict TDD & GPU Training)
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# ============================================================================
# Configuration
# ============================================================================

API_KEY = os.environ.get("EODHD_API_KEY")
BASE_URL = "https://eodhd.com/api/eod"

TEST_SYMBOL = "EURUSD.FOREX"
TEST_PERIOD = "1h"  # Hourly data (supports 20+ years)

# Date range: Last 10 days (minimal API usage for testing)
FROM_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
TO_DATE = datetime.now().strftime("%Y-%m-%d")


# ============================================================================
# Diagnostic Functions
# ============================================================================

def test_api_connectivity():
    """Test EODHD API with proper symbol format."""
    print("=" * 70)
    print("🔍 EODHD API Diagnostic Probe - Task #026.9")
    print("=" * 70)
    print()

    # Validation
    if not API_KEY:
        print("❌ FATAL: EODHD_API_KEY environment variable not set")
        print("   Run: export EODHD_API_KEY='your_key_here'")
        return False

    print("📋 Configuration:")
    print(f"  API Key: {API_KEY[:10]}...{API_KEY[-6:]}")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Test Symbol: {TEST_SYMBOL}")
    print(f"  Test Period: {TEST_PERIOD}")
    print(f"  Date Range: {FROM_DATE} to {TO_DATE}")
    print()

    # Test 1: EURUSD.FOREX with H1 (1 hour) data
    print("-" * 70)
    print("🧪 Test 1: EURUSD.FOREX - Hourly (1h) Data")
    print("-" * 70)
    print()

    params = {
        'api_token': API_KEY,
        'symbols': TEST_SYMBOL,
        'period': TEST_PERIOD,
        'from': FROM_DATE,
        'to': TO_DATE,
        'fmt': 'json'
    }

    try:
        print(f"Sending request to: {BASE_URL}")
        print(f"Parameters: symbols={TEST_SYMBOL}, period={TEST_PERIOD}")
        print()

        response = requests.get(BASE_URL, params=params, timeout=30)

        print(f"Response Status: {response.status_code}")
        print()

        if response.status_code == 200:
            print("✅ SUCCESS - API returned 200 OK")
            print()

            # Parse response
            try:
                data = response.json()

                if isinstance(data, dict):
                    if TEST_SYMBOL in data:
                        symbol_data = data[TEST_SYMBOL]
                        print(f"✅ Symbol found in response: {TEST_SYMBOL}")

                        if isinstance(symbol_data, list):
                            print(f"✅ Data format: List of {len(symbol_data)} records")

                            if len(symbol_data) > 0:
                                first_record = symbol_data[0]
                                print(f"✅ Sample record: {first_record}")
                                print()
                                print("🎉 EODHD API is fully operational!")
                                print(f"   Ready to fetch {len(symbol_data)} hourly records")
                                return True
                            else:
                                print("⚠️  No data records returned (may be expected for short date range)")
                                print()
                                print("✅ API connection successful (no data = API working)")
                                return True
                        else:
                            print(f"❌ Unexpected data format: {type(symbol_data)}")
                            print(f"   Content: {symbol_data}")
                            return False
                    else:
                        print(f"❌ Symbol {TEST_SYMBOL} not found in response")
                        print(f"   Available keys: {list(data.keys())}")
                        return False

                elif isinstance(data, list):
                    print(f"✅ Data format: List of {len(data)} records")
                    if len(data) > 0:
                        print(f"✅ Sample record: {data[0]}")
                        print()
                        print("🎉 EODHD API is fully operational!")
                        return True
                    else:
                        print("⚠️  Empty list returned (API OK, just no data)")
                        return True

                else:
                    print(f"⚠️  Unexpected response type: {type(data)}")
                    print(f"   Content: {str(data)[:200]}")
                    return False

            except ValueError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"   Response text: {response.text[:300]}")
                return False

        else:
            print(f"❌ FAILED - API returned status {response.status_code}")
            print()
            print("Response Content:")
            print(response.text[:500])
            print()

            # Diagnostic hints
            if response.status_code == 404:
                print("📌 DIAGNOSIS: 404 Not Found")
                print("   Possible causes:")
                print("   1. Symbol format incorrect (try 'EURUSD.FOREX')")
                print("   2. API endpoint changed")
                print("   3. Period parameter invalid")

            elif response.status_code == 401 or response.status_code == 403:
                print("📌 DIAGNOSIS: Authentication Error")
                print("   Possible causes:")
                print("   1. API key invalid or expired")
                print("   2. API key has no permission")
                print("   3. API key not set correctly")

            elif response.status_code == 429:
                print("📌 DIAGNOSIS: Rate Limited")
                print("   The API is throttling requests.")
                print("   Wait a moment and retry.")

            return False

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Request took too long (>30s)")
        print("   Check network connectivity to eodhd.com")
        return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR - {e}")
        print("   Check network connectivity to eodhd.com")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR - {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run diagnostic tests."""
    success = test_api_connectivity()

    print()
    print("=" * 70)

    if success:
        print("✅ DIAGNOSTIC PASSED")
        print("=" * 70)
        print()
        print("Next Steps (Task #026.9):")
        print("  1. ✅ Diagnostic probe: PASSED")
        print("  2. → Refactor src/data_loader/eodhd_fetcher.py")
        print("  3. → Update scripts/run_deep_training.py")
        print("  4. → Execute real training on GPU node")
        print("  5. → Deploy model to INF")
        print()
        return 0

    else:
        print("❌ DIAGNOSTIC FAILED")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("  1. Check EODHD_API_KEY is set correctly")
        print("  2. Verify network connectivity to eodhd.com")
        print("  3. Check API key is valid and has permissions")
        print("  4. Review EODHD API documentation")
        print()
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()

    # Additional troubleshooting
    if exit_code != 0:
        print()
        print("📋 TROUBLESHOOTING GUIDE")
        print("=" * 70)
        print()
        print("If the API key is valid but still failing:")
        print()
        print("1. EODHD API might use different endpoints for Forex data")
        print("   - Check if Forex data requires special pricing tier")
        print("   - Free tier may have limitations on Forex symbols")
        print()
        print("2. Alternative: Use cached historical data")
        print("   - If /opt/mt5-crs/data/raw/EURUSD_d.csv exists")
        print("   - Training can proceed with cached synthetic data")
        print()
        print("3. Generate synthetic data for proof of concept")
        print("   - Run: python3 scripts/run_deep_training_synthetic.py")
        print("   - This validates the entire pipeline without API dependency")
        print()

    sys.exit(exit_code)
