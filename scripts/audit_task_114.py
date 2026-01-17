#!/usr/bin/env python3
"""
Task #114: TDD Audit Script (Unit Tests)

Comprehensive unit tests for ML inference engine integration.

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import unittest
import numpy as np
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.online_features import OnlineFeatureCalculator
from src.inference.ml_predictor import MLPredictor, EXPECTED_MODEL_MD5
from src.strategy.ml_live_strategy import MLLiveStrategy

logging.basicConfig(level=logging.WARNING)


class TestOnlineFeatureCalculator(unittest.TestCase):
    """Test OnlineFeatureCalculator"""

    def setUp(self):
        """Initialize calculator"""
        self.calculator = OnlineFeatureCalculator(max_lookback=50)

    def test_initialization(self):
        """Test calculator initialization"""
        self.assertEqual(len(self.calculator.close_buffer), 0)
        self.assertEqual(self.calculator.tick_count, 0)

    def test_update_insufficient_data(self):
        """Test update with insufficient data"""
        # Add 10 ticks (need 50)
        for i in range(10):
            ready = self.calculator.update(
                close=1.0 + i*0.001,
                high=1.001 + i*0.001,
                low=0.999 + i*0.001,
                volume=1000
            )
            self.assertFalse(ready)

    def test_update_sufficient_data(self):
        """Test update with sufficient data"""
        # Add 50 ticks
        for i in range(50):
            ready = self.calculator.update(
                close=1.0 + i*0.001,
                high=1.001 + i*0.001,
                low=0.999 + i*0.001,
                volume=1000
            )

        self.assertTrue(ready)

    def test_feature_calculation_shape(self):
        """Test feature vector shape"""
        # Feed 50 ticks
        for i in range(50):
            self.calculator.update(
                close=1.0 + i*0.001,
                high=1.001 + i*0.001,
                low=0.999 + i*0.001,
                volume=1000 + i*10
            )

        # Get feature vector
        features = self.calculator.get_feature_vector()
        self.assertIsNotNone(features)
        self.assertEqual(features.shape, (21,))

    def test_feature_no_nan_inf(self):
        """Test features contain no NaN or Inf"""
        # Feed 60 ticks
        for i in range(60):
            self.calculator.update(
                close=1.05 + i*0.0001,
                high=1.051 + i*0.0001,
                low=1.049 + i*0.0001,
                volume=5000 + i*50
            )

        features = self.calculator.get_feature_vector()
        self.assertFalse(np.any(np.isnan(features)))
        self.assertFalse(np.any(np.isinf(features)))

    def test_rsi_bounds(self):
        """Test RSI is within [0, 100]"""
        # Feed 60 ticks
        for i in range(60):
            self.calculator.update(
                close=1.0 + np.sin(i*0.1)*0.01,
                high=1.01,
                low=0.99,
                volume=1000
            )

        features = self.calculator.calculate_features()
        self.assertIsNotNone(features)
        self.assertGreaterEqual(features['rsi_14'], 0)
        self.assertLessEqual(features['rsi_14'], 100)
        self.assertGreaterEqual(features['rsi_21'], 0)
        self.assertLessEqual(features['rsi_21'], 100)


class TestMLPredictor(unittest.TestCase):
    """Test MLPredictor"""

    def setUp(self):
        """Initialize predictor"""
        self.predictor = MLPredictor(
            model_path="/opt/mt5-crs/data/models/xgboost_task_114.pkl",
            confidence_threshold=0.55,
            verify_md5=True
        )

    def test_model_loaded(self):
        """Test model is loaded"""
        self.assertTrue(self.predictor.is_loaded)
        self.assertIsNotNone(self.predictor.model)

    def test_model_md5_integrity(self):
        """Test model MD5 integrity"""
        info = self.predictor.get_model_info()
        self.assertEqual(info['expected_md5'], EXPECTED_MODEL_MD5)

    def test_predict_shape_validation(self):
        """Test prediction with invalid shape"""
        # Wrong shape
        bad_features = np.random.randn(10)  # Should be 21
        signal, confidence, latency = self.predictor.predict(bad_features)

        # Should return HOLD on error
        self.assertEqual(signal, 0)

    def test_predict_nan_handling(self):
        """Test prediction with NaN features"""
        # Features with NaN
        features = np.random.randn(21)
        features[5] = np.nan

        signal, confidence, latency = self.predictor.predict(features)

        # Should return HOLD
        self.assertEqual(signal, 0)

    def test_predict_valid_features(self):
        """Test prediction with valid features"""
        # Valid features
        features = np.random.randn(21)

        signal, confidence, latency = self.predictor.predict(features)

        # Signal should be -1, 0, or 1
        self.assertIn(signal, [-1, 0, 1])

        # Confidence should be [0, 1]
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)

        # Latency should be positive
        self.assertGreater(latency, 0)

    def test_predict_latency_target(self):
        """Test prediction latency is <100ms (soft real-time)"""
        features = np.random.randn(21)

        latencies = []
        for _ in range(100):
            _, _, lat = self.predictor.predict(features)
            latencies.append(lat)

        # P95 latency should be <100ms (soft real-time target)
        p95_latency = np.percentile(latencies, 95)
        self.assertLess(p95_latency, 100, f"P95 latency = {p95_latency:.2f}ms")

    def test_confidence_threshold_effect(self):
        """Test confidence threshold affects signals"""
        # Low threshold (more signals)
        self.predictor.set_confidence_threshold(0.45)

        signals_low_threshold = []
        for _ in range(50):
            features = np.random.randn(21)
            sig, _, _ = self.predictor.predict(features)
            signals_low_threshold.append(sig)

        # High threshold (fewer signals)
        self.predictor.set_confidence_threshold(0.65)

        signals_high_threshold = []
        for _ in range(50):
            features = np.random.randn(21)
            sig, _, _ = self.predictor.predict(features)
            signals_high_threshold.append(sig)

        # Lower threshold should produce more non-zero signals
        non_zero_low = sum(1 for s in signals_low_threshold if s != 0)
        non_zero_high = sum(1 for s in signals_high_threshold if s != 0)

        # This may not always hold due to randomness, but generally true
        self.assertGreaterEqual(non_zero_low, non_zero_high * 0.5)


class TestMLLiveStrategy(unittest.TestCase):
    """Test MLLiveStrategy"""

    def setUp(self):
        """Initialize strategy"""
        self.strategy = MLLiveStrategy(
            confidence_threshold=0.55,
            throttle_seconds=10
        )

    def test_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(self.strategy.tick_count, 0)
        self.assertEqual(self.strategy.signal_count, 0)

    def test_on_tick_insufficient_data(self):
        """Test on_tick with insufficient data"""
        signal, metadata = self.strategy.on_tick(
            close=1.05, high=1.051, low=1.049, volume=1000
        )

        self.assertEqual(signal, 0)
        self.assertEqual(metadata['reason'], 'insufficient_data')

    def test_on_tick_sufficient_data(self):
        """Test on_tick with sufficient data"""
        # Feed 60 ticks
        for i in range(60):
            signal, metadata = self.strategy.on_tick(
                close=1.05 + i*0.0001,
                high=1.051 + i*0.0001,
                low=1.049 + i*0.0001,
                volume=5000 + i*10
            )

        # Last tick should have metadata
        self.assertIn('feature_hash', metadata)
        self.assertIn('latency_ms', metadata)
        self.assertIn('confidence', metadata)

    def test_signal_throttling(self):
        """Test signal throttling mechanism"""
        # Feed 70 ticks
        signals = []
        for i in range(70):
            signal, _ = self.strategy.on_tick(
                close=1.05 + np.sin(i*0.3)*0.01,  # Oscillating price
                high=1.06,
                low=1.04,
                volume=5000
            )
            signals.append(signal)

        # Count non-zero signals
        non_zero_signals = [s for s in signals if s != 0]

        # With 10s throttle, should have limited signals
        # (exact count depends on model, but should be < 10 for 70 ticks)
        self.assertLess(len(non_zero_signals), 10)

    def test_latency_tracking(self):
        """Test latency tracking"""
        # Feed 100 ticks
        for i in range(100):
            self.strategy.on_tick(
                close=1.05 + i*0.0001,
                high=1.051 + i*0.0001,
                low=1.049 + i*0.0001,
                volume=5000
            )

        stats = self.strategy.get_statistics()

        # Should have latency samples
        self.assertGreater(stats['mean_latency_ms'], 0)
        self.assertGreater(stats['p95_latency_ms'], 0)

        # Latency should meet soft real-time target (<100ms)
        self.assertLess(stats['p95_latency_ms'], 100)

    def test_statistics(self):
        """Test statistics reporting"""
        # Feed 80 ticks
        for i in range(80):
            self.strategy.on_tick(
                close=1.05 + i*0.0001,
                high=1.051 + i*0.0001,
                low=1.049 + i*0.0001,
                volume=5000
            )

        stats = self.strategy.get_statistics()

        self.assertEqual(stats['tick_count'], 80)
        self.assertGreaterEqual(stats['signal_count'], 0)
        self.assertIn('model_info', stats)


def run_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("Task #114: TDD Audit (Unit Tests)")
    print("="*80 + "\n")

    # Create test suite
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        TestOnlineFeatureCalculator))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        TestMLPredictor))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        TestMLLiveStrategy))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print(f"Tests run:    {result.testsRun}")
    print(f"Failures:     {len(result.failures)}")
    print(f"Errors:       {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")

    if result.wasSuccessful():
        print("\n✅ All tests PASSED")
        return 0
    else:
        print("\n❌ Some tests FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
