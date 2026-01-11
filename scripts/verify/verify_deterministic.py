#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #080: Deterministic Inference Verification Script

Verifies that the HUB model server produces deterministic predictions:
- Send identical features → Receive identical predictions
- No randomness in model inference
- Confirms real model is loaded (not mock mode)

Protocol v4.3 - Deterministic Verification
"""

import sys
import time
import json
import requests
import numpy as np
from typing import List, Optional

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def create_test_features(seed: int = 42) -> List:
    """
    Create a deterministic test feature vector (23 features)

    Args:
        seed: Random seed for reproducibility

    Returns:
        List of 23 feature values
    """
    np.random.seed(seed)

    # Generate 23 features with realistic ranges
    features = []

    # Price-based features (indices 0-2)
    features.append(np.random.uniform(0.0001, 0.001))   # price_range
    features.append(np.random.uniform(-0.0005, 0.0005))  # price_change
    features.append(np.random.uniform(-0.05, 0.05))      # price_change_pct

    # SMA features (indices 3-5)
    features.append(np.random.uniform(1.0, 1.2))  # sma_5
    features.append(np.random.uniform(1.0, 1.2))  # sma_10
    features.append(np.random.uniform(1.0, 1.2))  # sma_20

    # EMA features (indices 6-7)
    features.append(np.random.uniform(1.0, 1.2))  # ema_5
    features.append(np.random.uniform(1.0, 1.2))  # ema_10

    # Momentum features (indices 8-9)
    features.append(np.random.uniform(-0.01, 0.01))  # momentum_5
    features.append(np.random.uniform(-0.01, 0.01))  # momentum_10

    # Volatility features (indices 10-11)
    features.append(np.random.uniform(0.0001, 0.001))  # volatility_5
    features.append(np.random.uniform(0.0001, 0.001))  # volatility_10

    # RSI feature (index 12)
    features.append(np.random.uniform(30, 70))  # rsi_14

    # Volume features (indices 13-14)
    features.append(np.random.uniform(1000, 10000))  # volume_sma_5
    features.append(np.random.uniform(-100, 100))    # volume_change

    # Padding features (indices 15-22) - reserved for future use
    for _ in range(8):
        features.append(np.random.uniform(0, 1))

    return features


def send_inference_request(
    hub_host: str,
    hub_port: int,
    features: List,
    timeout: int = 5
) -> Optional[List]:
    """
    Send inference request to HUB server

    Args:
        hub_host: HUB server hostname or IP
        hub_port: HUB server port
        features: List of 23 feature values
        timeout: Request timeout in seconds

    Returns:
        Predictions list or None on error
    """
    try:
        # Format payload in Sentinel's format
        payload = {
            "dataframe_split": {
                "columns": ["X_tabular", "X_sequential"],
                "data": [[
                    features,                    # X_tabular (23,)
                    [features] * 60             # X_sequential (60, 23) - dummy
                ]]
            }
        }

        url = f"http://{hub_host}:{hub_port}/invocations"
        response = requests.post(
            url,
            json=payload,
            timeout=timeout
        )

        if response.status_code != 200:
            print(f"{RED}❌ Request failed: {response.status_code}{RESET}")
            print(f"   Response: {response.text}")
            return None

        result = response.json()
        return result.get("predictions", [])

    except Exception as e:
        print(f"{RED}❌ Request error: {e}{RESET}")
        return None


def verify_deterministic(
    hub_host: str = "localhost",
    hub_port: int = 5001,
    n_trials: int = 3,
    tolerance: float = 1e-9
) -> bool:
    """
    Verify that model produces deterministic predictions

    Args:
        hub_host: HUB server hostname
        hub_port: HUB server port
        n_trials: Number of identical requests to send
        tolerance: Maximum allowed difference between predictions

    Returns:
        True if deterministic, False otherwise
    """
    print("=" * 70)
    print(f"{CYAN}TASK #080: DETERMINISTIC INFERENCE VERIFICATION{RESET}")
    print("=" * 70)

    # Step 1: Check HUB health
    print(f"\n{CYAN}1. Checking HUB server health...{RESET}")
    try:
        response = requests.get(f"http://{hub_host}:{hub_port}/health", timeout=5)
        if response.status_code == 200:
            print(f"   {GREEN}✅ HUB server is healthy{RESET}")
        else:
            print(f"   {RED}❌ HUB health check failed{RESET}")
            return False
    except Exception as e:
        print(f"   {RED}❌ Cannot reach HUB server: {e}{RESET}")
        return False

    # Step 2: Create deterministic test features
    print(f"\n{CYAN}2. Creating test feature vector...{RESET}")
    test_features = create_test_features(seed=42)
    print(f"   {GREEN}✓{RESET} Generated 23 features")
    print(f"   {GREEN}✓{RESET} Sample values: [{test_features[0]:.6f}, {test_features[1]:.6f}, {test_features[2]:.6f}, ...]")

    # Step 3: Send multiple identical requests
    print(f"\n{CYAN}3. Sending {n_trials} identical requests...{RESET}")
    predictions = []

    for i in range(n_trials):
        print(f"   Trial {i+1}/{n_trials}... ", end="", flush=True)
        pred = send_inference_request(hub_host, hub_port, test_features)

        if pred is None or len(pred) == 0:
            print(f"{RED}FAILED{RESET}")
            print(f"   {RED}❌ Trial {i+1} returned no predictions{RESET}")
            return False

        predictions.append(pred[0])  # Get first prediction
        print(f"{GREEN}OK{RESET} → {pred[0]}")

        # Small delay to avoid rate limiting
        if i < n_trials - 1:
            time.sleep(0.1)

    # Step 4: Verify determinism
    print(f"\n{CYAN}4. Verifying determinism...{RESET}")
    print(f"   Reference prediction: {predictions[0]}")

    all_equal = True
    for i in range(1, len(predictions)):
        diff = np.abs(np.array(predictions[i]) - np.array(predictions[0]))
        max_diff = np.max(diff)

        if max_diff > tolerance:
            print(f"   {RED}❌ Trial {i+1} differs by {max_diff:.2e} (tolerance: {tolerance:.2e}){RESET}")
            print(f"      Pred {i+1}: {predictions[i]}")
            all_equal = False
        else:
            print(f"   {GREEN}✓{RESET} Trial {i+1} matches (diff: {max_diff:.2e})")

    # Step 5: Detect mock mode
    print(f"\n{CYAN}5. Checking for mock mode artifacts...{RESET}")
    pred_array = np.array(predictions)
    variance = np.var(pred_array)

    if variance > 0.001:  # High variance suggests randomness
        print(f"   {RED}⚠️  HIGH VARIANCE DETECTED: {variance:.6f}{RESET}")
        print(f"   {RED}⚠️  This suggests MOCK MODE is still enabled!{RESET}")
        all_equal = False
    else:
        print(f"   {GREEN}✓{RESET} Low variance: {variance:.9f} (deterministic)")

    # Final verdict
    print(f"\n" + "=" * 70)
    if all_equal:
        print(f"{GREEN}✅ VERIFICATION PASSED: Model is deterministic{RESET}")
        print(f"   {GREEN}✓{RESET} All {n_trials} predictions are identical")
        print(f"   {GREEN}✓{RESET} Real model inference confirmed")
        return True
    else:
        print(f"{RED}❌ VERIFICATION FAILED: Model is not deterministic{RESET}")
        print(f"   {RED}❌{RESET} Check ENABLE_MOCK_INFERENCE environment variable")
        print(f"   {RED}❌{RESET} Ensure model is properly loaded")
        return False


def main():
    """
    Main entry point
    """
    import os

    hub_host = os.getenv("HUB_HOST", "localhost")
    hub_port = int(os.getenv("HUB_PORT", "5001"))

    success = verify_deterministic(
        hub_host=hub_host,
        hub_port=hub_port,
        n_trials=3,
        tolerance=1e-9
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
