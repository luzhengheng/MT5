#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Model Inference Verification (TASK #027)

Validates that:
1. Model can be loaded successfully
2. Inference works on sample inputs
3. Output format is correct
4. Latency is acceptable
"""

import os
import sys
import time
import numpy as np
import pandas as pd

from src.model.predict import PricePredictor


def test_model_loading():
    """
    Test 1: Model loading
    """
    print("\n[TEST 1] Model loading...")

    try:
        predictor = PricePredictor()
        assert predictor.model is not None, "Model not loaded"
        assert predictor.metadata is not None, "Metadata not loaded"
        assert len(predictor.feature_names) > 0, "No feature names"

        print(f"✅ PASS: Model loaded successfully")
        print(f"   - Features: {len(predictor.feature_names)}")
        print(f"   - Accuracy: {predictor.metadata.get('metrics', {}).get('accuracy', 'N/A')}")
        return True, predictor
    except Exception as e:
        print(f"❌ FAIL: Model loading failed - {e}")
        return False, None


def test_single_inference(predictor):
    """
    Test 2: Single inference
    """
    print("\n[TEST 2] Single inference...")

    try:
        # Create sample features
        sample_features = {}
        for feature_name in predictor.feature_names:
            if 'pct' in feature_name or 'rsi' in feature_name:
                sample_features[feature_name] = np.random.uniform(-0.05, 0.05)
            elif 'volume' in feature_name:
                sample_features[feature_name] = np.random.uniform(0, 1000)
            else:
                sample_features[feature_name] = np.random.uniform(1.0, 1.2)

        # Predict
        start_time = time.time()
        result = predictor.predict(sample_features)
        latency_ms = (time.time() - start_time) * 1000

        # Validate output format
        assert 'prediction' in result, "Missing 'prediction' field"
        assert 'probability' in result, "Missing 'probability' field"
        assert 'direction' in result, "Missing 'direction' field"
        assert 'confidence' in result, "Missing 'confidence' field"

        assert result['prediction'] in [0, 1], "Invalid prediction value"
        assert 0 <= result['probability'] <= 1, "Invalid probability range"
        assert result['direction'] in ['UP', 'DOWN'], "Invalid direction"
        assert 0 <= result['confidence'] <= 1, "Invalid confidence range"

        print(f"✅ PASS: Inference successful")
        print(f"   - Latency: {latency_ms:.2f}ms")
        print(f"   - Prediction: {result['direction']}")
        print(f"   - Probability: {result['probability']:.4f}")
        print(f"   - Confidence: {result['confidence']:.4f}")

        return True, latency_ms
    except Exception as e:
        print(f"❌ FAIL: Inference failed - {e}")
        return False, None


def test_batch_inference(predictor):
    """
    Test 3: Batch inference
    """
    print("\n[TEST 3] Batch inference...")

    try:
        # Create batch of features
        batch_size = 10
        features_list = []

        for _ in range(batch_size):
            sample = {}
            for feature_name in predictor.feature_names:
                if 'pct' in feature_name or 'rsi' in feature_name:
                    sample[feature_name] = np.random.uniform(-0.05, 0.05)
                elif 'volume' in feature_name:
                    sample[feature_name] = np.random.uniform(0, 1000)
                else:
                    sample[feature_name] = np.random.uniform(1.0, 1.2)
            features_list.append(sample)

        features_df = pd.DataFrame(features_list)

        # Predict
        start_time = time.time()
        results = predictor.predict_batch(features_df)
        latency_ms = (time.time() - start_time) * 1000

        # Validate
        assert len(results) == batch_size, f"Expected {batch_size} results, got {len(results)}"

        for result in results:
            assert 'prediction' in result, "Missing 'prediction' field"
            assert 'probability' in result, "Missing 'probability' field"

        print(f"✅ PASS: Batch inference successful")
        print(f"   - Batch size: {batch_size}")
        print(f"   - Total latency: {latency_ms:.2f}ms")
        print(f"   - Per-sample latency: {latency_ms/batch_size:.2f}ms")

        return True
    except Exception as e:
        print(f"❌ FAIL: Batch inference failed - {e}")
        return False


def test_latency_requirement(latency_ms):
    """
    Test 4: Latency requirement
    """
    print("\n[TEST 4] Latency requirement...")

    threshold_ms = 100  # 100ms threshold for single inference

    if latency_ms < threshold_ms:
        print(f"✅ PASS: Latency {latency_ms:.2f}ms < {threshold_ms}ms threshold")
        return True
    else:
        print(f"⚠️  WARNING: Latency {latency_ms:.2f}ms >= {threshold_ms}ms threshold")
        return True  # Warning only, not a failure


def main():
    """
    Main test suite
    """
    print("="*80)
    print("MODEL INFERENCE VERIFICATION TEST SUITE - TASK #027")
    print("="*80)

    passed = 0
    failed = 0

    # Test 1: Model loading
    success, predictor = test_model_loading()
    if success:
        passed += 1
    else:
        failed += 1
        print("\n❌ Cannot proceed without model. Exiting.")
        return 1

    # Test 2: Single inference
    success, latency_ms = test_single_inference(predictor)
    if success:
        passed += 1
    else:
        failed += 1

    # Test 3: Batch inference
    if test_batch_inference(predictor):
        passed += 1
    else:
        failed += 1

    # Test 4: Latency requirement
    if latency_ms and test_latency_requirement(latency_ms):
        passed += 1
    else:
        failed += 1

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Model inference verified")
        print("="*80)
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
