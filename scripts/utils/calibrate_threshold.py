#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #081: Threshold Calibration Script

Monitors mt5-sentinel logs to collect real model predictions,
analyzes distribution, and recommends threshold adjustment.

Protocol v4.3 - Threshold Calibration
"""

import subprocess
import re
import sys
import time
from collections import defaultdict
from statistics import mean, stdev, median
from typing import List, Dict

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def get_recent_predictions(lines: int = 500) -> List[float]:
    """
    Extract real predictions from mt5-sentinel logs

    Args:
        lines: Number of recent log lines to check

    Returns:
        List of prediction values (0.0 to 1.0)
    """
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'mt5-sentinel', '-n', str(lines), '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )

        log_text = result.stdout

        # Pattern for real predictions (from app.py inference output)
        # Format: ✓ Prediction: [0.xxxx]
        pattern = r'✓ Prediction: \[([0-9.]+)\]'
        matches = re.findall(pattern, log_text)

        predictions = []
        for match in matches:
            try:
                pred = float(match)
                # Validate range
                if 0.0 <= pred <= 1.0:
                    predictions.append(pred)
            except ValueError:
                continue

        return predictions

    except Exception as e:
        print(f"{RED}❌ Failed to fetch logs: {e}{RESET}")
        return []


def analyze_distribution(predictions: List[float]) -> Dict:
    """
    Analyze prediction distribution statistics

    Args:
        predictions: List of prediction values

    Returns:
        Dict with statistics
    """
    if not predictions:
        return {}

    predictions.sort()

    stats = {
        'count': len(predictions),
        'min': min(predictions),
        'max': max(predictions),
        'mean': mean(predictions),
        'median': median(predictions),
        'stdev': stdev(predictions) if len(predictions) > 1 else 0,
        'p25': predictions[len(predictions) // 4],
        'p75': predictions[(3 * len(predictions)) // 4],
        'raw_values': predictions
    }

    return stats


def recommend_threshold(stats: Dict, current_threshold: float = 0.65) -> Dict:
    """
    Recommend new threshold based on distribution

    Args:
        stats: Distribution statistics
        current_threshold: Current threshold value

    Returns:
        Dict with recommendation
    """
    if not stats or stats['count'] == 0:
        return {'status': 'insufficient_data'}

    max_pred = stats['max']
    p75 = stats['p75']
    mean_pred = stats['mean']
    median_pred = stats['median']

    # Strategy: Set threshold to allow ~25% of predictions to trigger
    # This is the 75th percentile value
    recommended = p75

    # Clamp to reasonable range [0.1, 0.9]
    recommended = max(0.1, min(0.9, recommended))

    # Check if current threshold is realistic
    if current_threshold > max_pred:
        signal_rate = 0.0
        severity = "CRITICAL"
    else:
        # Count how many predictions would trigger
        signals = sum(1 for p in stats['raw_values'] if p >= current_threshold)
        signal_rate = signals / stats['count']

        if signal_rate == 0:
            severity = "CRITICAL"
        elif signal_rate < 0.05:
            severity = "WARNING"
        else:
            severity = "OK"

    return {
        'status': 'ok',
        'current_threshold': current_threshold,
        'recommended_threshold': recommended,
        'signal_rate': signal_rate,
        'severity': severity,
        'max_prediction': max_pred,
        'mean_prediction': mean_pred,
        'median_prediction': median_pred,
        'p75_prediction': p75,
        'reason': (
            f"Current threshold ({current_threshold:.2f}) is above max prediction "
            f"({max_pred:.4f})" if current_threshold > max_pred
            else f"With current threshold, only {signal_rate:.1%} of predictions trigger"
        )
    }


def main():
    """
    Main calibration routine
    """
    print("=" * 80)
    print(f"{CYAN}TASK #081: THRESHOLD CALIBRATION & ANALYSIS{RESET}")
    print("=" * 80)

    # Step 1: Collect predictions
    print(f"\n{CYAN}1. Collecting predictions from mt5-sentinel logs...{RESET}")
    print(f"   Scanning recent logs for prediction values...")

    predictions = get_recent_predictions(lines=1000)

    if not predictions:
        print(f"   {RED}❌ No predictions found in logs{RESET}")
        print(f"   Make sure mt5-sentinel is running and has executed at least one cycle")
        return 1

    print(f"   {GREEN}✓{RESET} Found {len(predictions)} predictions")

    # Step 2: Analyze distribution
    print(f"\n{CYAN}2. Analyzing prediction distribution...{RESET}")
    stats = analyze_distribution(predictions)

    print(f"   Sample predictions (first 5): {stats['raw_values'][:5]}")
    print(f"   Min: {stats['min']:.4f}")
    print(f"   Max: {stats['max']:.4f}")
    print(f"   Mean: {stats['mean']:.4f}")
    print(f"   Median: {stats['median']:.4f}")
    print(f"   Std Dev: {stats['stdev']:.4f}")
    print(f"   P75 (75th percentile): {stats['p75']:.4f}")

    # Step 3: Recommend threshold
    print(f"\n{CYAN}3. Analyzing threshold mismatch...{RESET}")
    current_threshold = 0.65
    recommendation = recommend_threshold(stats, current_threshold)

    if recommendation['status'] == 'insufficient_data':
        print(f"   {RED}❌ Insufficient data for recommendation{RESET}")
        return 1

    print(f"   Current threshold: {recommendation['current_threshold']:.4f}")
    print(f"   Signal trigger rate: {recommendation['signal_rate']:.1%}")
    print(f"   Severity: {recommendation['severity']}")
    print(f"   {RED}Problem: {recommendation['reason']}{RESET}")

    # Step 4: Recommendation
    print(f"\n{CYAN}4. Threshold Recommendation...{RESET}")
    recommended = recommendation['recommended_threshold']

    if recommendation['severity'] == "CRITICAL":
        print(f"   {RED}🔴 CRITICAL: Current threshold is unreachable!{RESET}")
        print(f"   Maximum prediction: {recommendation['max_prediction']:.4f}")
        print(f"   Current threshold: {recommendation['current_threshold']:.4f}")
        print(f"   ")
        print(f"   {YELLOW}IMMEDIATE ACTION REQUIRED:{RESET}")
        print(f"   Recommended threshold: {recommended:.4f}")
        print(f"   ")
        print(f"   This allows ~25% of predictions to trigger (signal rate: ~0.25)")
    else:
        print(f"   {YELLOW}⚠️  WARNING: Low signal trigger rate{RESET}")
        print(f"   Recommended threshold: {recommended:.4f}")

    # Step 5: Show adjustment command
    print(f"\n{CYAN}5. How to adjust threshold...{RESET}")
    print(f"   ")
    print(f"   {YELLOW}Edit /etc/systemd/system/mt5-sentinel.service{RESET}")
    print(f"   Change the --threshold parameter:")
    print(f"   ")
    print(f"   FROM: --threshold {current_threshold}")
    print(f"   TO:   --threshold {recommended:.4f}")
    print(f"   ")
    print(f"   Then reload and restart:")
    print(f"   ")
    print(f"   {GREEN}sudo systemctl daemon-reload{RESET}")
    print(f"   {GREEN}sudo systemctl restart mt5-sentinel{RESET}")

    # Final verdict
    print("\n" + "=" * 80)
    if recommendation['severity'] == "CRITICAL":
        print(f"{RED}❌ THRESHOLD MISMATCH DETECTED: Immediate adjustment required{RESET}")
        print(f"   The system will not execute ANY trades with current settings")
        return 1
    else:
        print(f"{YELLOW}⚠️  SUBOPTIMAL THRESHOLD: Adjustment recommended{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
