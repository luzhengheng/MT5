#!/usr/bin/env python3
"""
Task #026.99: Critical Raw API Debugger
========================================

Direct EODHD API test - NO FALLBACKS, NO LIES.
Print exact URL and raw response to identify the real problem.

Protocol: v2.0 (Strict TDD & Real Data Only)
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

# Test parameters
TEST_SYMBOL = "EURUSD.FOREX"
TEST_PERIOD = "1h"  # hourly
FROM_DATE = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
TO_DATE = datetime.now().strftime("%Y-%m-%d")

# ============================================================================
# Raw API Test (No Fallback, No Excuses)
# ============================================================================

def test_raw_api():
    """Test EODHD API with raw debugging output."""
    print("=" * 80)
    print("🔍 TASK #026.99: Critical Raw API Debug")
    print("=" * 80)
    print()

    # Validation
    if not API_KEY:
        print("❌ FATAL: EODHD_API_KEY not set")
        print("   Export: export EODHD_API_KEY='your_key_here'")
        return False

    # Build URL
    params = {
        'api_token': API_KEY,
        'symbols': TEST_SYMBOL,
        'period': TEST_PERIOD,
        'from': FROM_DATE,
        'to': TO_DATE,
        'fmt': 'json'
    }

    # Print the exact request
    print("📋 REQUEST DETAILS")
    print("-" * 80)
    print(f"Endpoint: {BASE_URL}")
    print(f"Symbol: {TEST_SYMBOL}")
    print(f"Period: {TEST_PERIOD}")
    print(f"Date range: {FROM_DATE} to {TO_DATE}")
    print()

    # MASK the API key for security but show length
    masked_key = API_KEY[:5] + "****" + API_KEY[-5:]
    print(f"API Key: {masked_key} (length: {len(API_KEY)})")
    print()

    # Build full URL (for debugging)
    full_url = f"{BASE_URL}?api_token={API_KEY}&symbols={TEST_SYMBOL}&period={TEST_PERIOD}&from={FROM_DATE}&to={TO_DATE}&fmt=json"
    masked_url = f"{BASE_URL}?api_token={masked_key}&symbols={TEST_SYMBOL}&period={TEST_PERIOD}&from={FROM_DATE}&to={TO_DATE}&fmt=json"
    print(f"Full URL (masked): {masked_url}")
    print()

    # Make the request
    print("📡 MAKING REQUEST")
    print("-" * 80)
    print()

    try:
        print(f"Connecting to {BASE_URL}...")
        response = requests.get(BASE_URL, params=params, timeout=30)

        # Print status
        print(f"Status Code: {response.status_code}")
        print(f"Status Text: {response.reason}")
        print()

        # Print headers
        print("📌 RESPONSE HEADERS")
        print("-" * 80)
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'content-length', 'server', 'date']:
                print(f"  {key}: {value}")
        print()

        # Print body
        print("📄 RESPONSE BODY (First 1000 chars)")
        print("-" * 80)
        body_text = response.text[:1000]
        print(body_text)
        print()

        if len(response.text) > 1000:
            print(f"  [Response truncated - total length: {len(response.text)} chars]")
            print()

        # Analysis
        print("=" * 80)
        print("🔍 ANALYSIS")
        print("=" * 80)
        print()

        if response.status_code == 200:
            print("✅ HTTP 200 OK - Response returned successfully")
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"✅ Response is JSON dict with keys: {list(data.keys())}")
                    if TEST_SYMBOL in data:
                        symbol_data = data[TEST_SYMBOL]
                        if isinstance(symbol_data, list):
                            print(f"✅ Found symbol data: {len(symbol_data)} records")
                            if len(symbol_data) > 0:
                                print(f"   First record: {symbol_data[0]}")
                                return True
                            else:
                                print("❌ Symbol data is empty list")
                                return False
                        else:
                            print(f"⚠️  Symbol data is not a list: {type(symbol_data)}")
                    else:
                        print(f"❌ Symbol '{TEST_SYMBOL}' not in response")
                        print(f"   Available keys: {list(data.keys())}")
                        return False
                elif isinstance(data, list):
                    print(f"✅ Response is JSON list with {len(data)} records")
                    if len(data) > 0:
                        print(f"   First record: {data[0]}")
                        return True
                    else:
                        print("❌ Response list is empty")
                        return False
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
                return False

        elif response.status_code == 404:
            print("❌ HTTP 404 NOT FOUND")
            print("   Possible causes:")
            print("   1. Symbol format incorrect (should be 'EURUSD.FOREX')")
            print("   2. Endpoint URL incorrect")
            print("   3. API endpoint moved or deprecated")
            print()
            print("   Response suggests API endpoint or symbol not found")
            return False

        elif response.status_code == 401 or response.status_code == 403:
            print(f"❌ HTTP {response.status_code} - AUTHENTICATION ERROR")
            print("   Possible causes:")
            print("   1. API key invalid or expired")
            print("   2. API key has insufficient permissions")
            print("   3. API key doesn't support this endpoint")
            print()
            print("   Check EODHD account and API key validity")
            return False

        elif response.status_code == 429:
            print("❌ HTTP 429 - RATE LIMITED")
            print("   API is throttling requests. Wait and retry.")
            return False

        else:
            print(f"❌ HTTP {response.status_code} - UNEXPECTED ERROR")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Request took >30 seconds")
        print("   Check network connectivity to eodhd.com")
        return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR - {e}")
        print("   Check network connectivity and firewall")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR - {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print()
        print("=" * 80)


# ============================================================================
# Alternative Tests (Try different endpoints)
# ============================================================================

def test_alternative_endpoints():
    """Try different EODHD endpoints to find which works."""
    print()
    print("=" * 80)
    print("🧪 TESTING ALTERNATIVE ENDPOINTS")
    print("=" * 80)
    print()

    endpoints = [
        ("EOD Endpoint", "https://eodhd.com/api/eod", "d"),
        ("Intraday Endpoint", "https://eodhd.com/api/intraday", "1h"),
        ("Forex Endpoint", "https://eodhd.com/api/forex", "1h"),
    ]

    for name, url, period in endpoints:
        print(f"Testing: {name}")
        print(f"  URL: {url}")
        print(f"  Symbol: {TEST_SYMBOL}, Period: {period}")

        params = {
            'api_token': API_KEY,
            'symbols': TEST_SYMBOL,
            'period': period,
            'fmt': 'json'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and TEST_SYMBOL in data:
                        records = data[TEST_SYMBOL]
                        if isinstance(records, list) and len(records) > 0:
                            print(f"  ✅ SUCCESS! Got {len(records)} records")
                        else:
                            print(f"  ⚠️  Got data but empty or wrong format")
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"  ✅ SUCCESS! Got {len(data)} records")
                    else:
                        print(f"  ⚠️  Unexpected format")
                except:
                    print(f"  ⚠️  Response is not JSON")
            else:
                print(f"  ❌ Error response")

        except Exception as e:
            print(f"  ❌ Exception: {e}")

        print()


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all diagnostic tests."""
    success = test_raw_api()

    if not success:
        test_alternative_endpoints()

    print()
    print("=" * 80)

    if success:
        print("✅ API TEST PASSED - Ready to train with real data!")
        print("=" * 80)
        return 0
    else:
        print("❌ API TEST FAILED - See error details above")
        print("=" * 80)
        print()
        print("NEXT STEPS:")
        print("  1. Check API key validity: EODHD_API_KEY=... python3 scripts/debug_raw_api.py")
        print("  2. Verify endpoint: https://eodhd.com/docs/")
        print("  3. Check symbol format: Must use .FOREX suffix for Forex pairs")
        print("  4. Verify subscription tier supports Forex intraday data")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
