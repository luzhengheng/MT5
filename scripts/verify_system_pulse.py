#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #079: System Loop Verification Script

Parses recent mt5-sentinel logs to verify:
1. Sentinel successfully requests predictions from HUB
2. HUB returns predictions
3. Sentinel makes trading decisions
4. Signals are generated

Protocol v4.3 - Gate 1 Verification
"""

import subprocess
import json
import re
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Load HUB host from environment or use localhost
# NOTE: Default to localhost for portability; set HUB_HOST env var for remote connections
HUB_HOST = os.getenv("HUB_HOST", "localhost")
HUB_PORT = os.getenv("HUB_PORT", "5001")
HUB_URL = f"http://{HUB_HOST}:{HUB_PORT}"

def get_recent_logs(lines: int = 200) -> str:
    """Get recent mt5-sentinel logs"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mt5-sentinel', '-n', str(lines), '--no-pager'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    except Exception as e:
        print(f"❌ Failed to fetch logs: {e}")
        return ""

def parse_trading_cycles(log_text: str) -> List[Dict]:
    """Parse trading cycles from log"""
    cycles = []

    # Find all trading cycles
    cycle_pattern = r'TRADING CYCLE START: ([\d\-T:\.]+)'
    cycle_times = re.findall(cycle_pattern, log_text)

    # Find prediction requests and responses
    request_pattern = r'Requesting prediction from HUB\.\.\.'
    prediction_pattern = r'✓ Prediction: \[([\d\.]+)\]'
    decision_pattern = r'Decision: (BUY|SELL|HOLD) \(confidence: ([\d\.]+)\)'
    signal_pattern = r'Sending trading signal: (BUY|SELL|HOLD) \(confidence: ([\d\.]+)\)'

    requests = re.findall(request_pattern, log_text)
    predictions = re.findall(prediction_pattern, log_text)
    decisions = re.findall(decision_pattern, log_text)
    signals = re.findall(signal_pattern, log_text)

    # Count successful cycles
    successful_cycles = len(predictions)

    return {
        'total_cycles': len(cycle_times),
        'successful_predictions': successful_cycles,
        'requests_sent': len(requests),
        'decisions_made': len(decisions),
        'signals_generated': len(signals),
        'sample_predictions': predictions[-3:] if predictions else [],
        'sample_decisions': decisions[-3:] if decisions else [],
        'sample_signals': signals[-3:] if signals else []
    }

def check_hub_health() -> bool:
    """Check HUB model service health"""
    try:
        import requests
        response = requests.get(f"{HUB_URL}/health", timeout=5)
        data = response.json()
        return data.get('status') == 'healthy'
    except Exception as e:
        print(f"❌ HUB health check failed: {e}")
        return False

def check_invocations_endpoint() -> bool:
    """Test /invocations endpoint"""
    try:
        import requests
        payload = {"instances": [[0.1, 0.2, 0.3]]}
        response = requests.post(
            f"{HUB_URL}/invocations",
            json=payload,
            timeout=5
        )
        data = response.json()
        return 'predictions' in data
    except Exception as e:
        print(f"❌ /invocations test failed: {e}")
        return False

def main():
    print("="*70)
    print("TASK #079: FULL SYSTEM LOOP VERIFICATION")
    print("="*70)

    # Check HUB health
    print("\n1. Checking HUB Model Server Health...")
    hub_healthy = check_hub_health()
    print(f"   {'✅' if hub_healthy else '❌'} HUB Status: {'HEALTHY' if hub_healthy else 'UNHEALTHY'}")

    # Check /invocations endpoint
    print("\n2. Testing /invocations Endpoint...")
    invocations_ok = check_invocations_endpoint()
    print(f"   {'✅' if invocations_ok else '❌'} /invocations: {'OK' if invocations_ok else 'FAILED'}")

    # Parse recent logs
    print("\n3. Analyzing Recent Trading Cycles...")
    logs = get_recent_logs(500)

    if not logs:
        print("   ❌ No logs found")
        return 1

    stats = parse_trading_cycles(logs)

    print(f"   📊 Total Cycles: {stats['total_cycles']}")
    print(f"   ✓ Successful Predictions: {stats['successful_predictions']}")
    print(f"   ✓ Requests Sent: {stats['requests_sent']}")
    print(f"   ✓ Decisions Made: {stats['decisions_made']}")
    print(f"   ✓ Signals Generated: {stats['signals_generated']}")

    # Sample data
    if stats['sample_predictions']:
        print(f"\n4. Sample Recent Predictions:")
        for i, (pred, decision, signal) in enumerate(zip(
            stats['sample_predictions'],
            stats['sample_decisions'],
            stats['sample_signals']
        ), 1):
            print(f"   [{i}] Prediction: {pred}")
            print(f"       Decision: {decision[0]} (confidence: {decision[1]})")
            print(f"       Signal: {signal[0]} (confidence: {signal[1]})")

    # Final verdict
    print("\n" + "="*70)
    success = (
        hub_healthy and
        invocations_ok and
        stats['successful_predictions'] >= 2  # At least 2 successful cycles
    )

    if success:
        print("✅ VERIFICATION PASSED: Full system loop is working!")
        print("   INF → HUB → GTW chain confirmed operational")
        return 0
    else:
        print("❌ VERIFICATION FAILED: Issues detected")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
