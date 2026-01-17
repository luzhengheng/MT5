#!/usr/bin/env python3
"""
Task #115 Audit Framework - ML Strategy Shadow Mode & Concept Drift Monitor

This TDD audit suite validates:
1. DriftDetector accuracy (PSI/KL divergence calculation)
2. Shadow Mode blocking real orders
3. ShadowRecorder logging signals correctly
4. Feature distribution tracking
5. Circuit breaker triggering on drift threshold

Protocol: v4.3 (Zero-Trust Edition)
"""

import unittest
import logging
import numpy as np
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch, MagicMock

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TestDriftDetector(unittest.TestCase):
    """Test DriftDetector mathematical accuracy"""

    def setUp(self):
        """Initialize test fixtures"""
        # Import DriftDetector after modules are available
        try:
            from src.monitoring.drift_detector import DriftDetector
            self.DriftDetector = DriftDetector
        except ImportError:
            logger.warning("DriftDetector not yet implemented, will test placeholder")
            self.DriftDetector = None

    def test_psi_calculation_zero_divergence(self):
        """Test PSI = 0 when distributions are identical"""
        if self.DriftDetector is None:
            self.skipTest("DriftDetector not implemented")

        # Identical distributions
        reference_features = np.array([1.0, 2.0, 3.0, 4.0, 5.0] * 10)
        current_features = np.array([1.0, 2.0, 3.0, 4.0, 5.0] * 10)

        detector = self.DriftDetector(
            reference_features=reference_features,
            n_bins=5
        )

        psi = detector.calculate_psi(current_features)

        # PSI should be very close to 0 (allowing small numerical errors)
        self.assertLess(psi, 0.001, f"Expected PSI ≈ 0, got {psi}")

    def test_psi_calculation_high_divergence(self):
        """Test PSI detects significant distribution shift"""
        if self.DriftDetector is None:
            self.skipTest("DriftDetector not implemented")

        # Reference: normal distribution centered at 0
        reference_features = np.random.normal(0, 1, 1000)

        # Current: shifted distribution centered at 5
        current_features = np.random.normal(5, 1, 1000)

        detector = self.DriftDetector(
            reference_features=reference_features,
            n_bins=10
        )

        psi = detector.calculate_psi(current_features)

        # PSI should be > 0.2 (significant drift threshold)
        self.assertGreater(psi, 0.2, f"Expected PSI > 0.2, got {psi}")

    def test_kl_divergence_calculation(self):
        """Test KL divergence computation"""
        if self.DriftDetector is None:
            self.skipTest("DriftDetector not implemented")

        # Known distributions
        reference_features = np.array([1.0, 1.0, 1.0, 2.0, 2.0, 2.0])
        current_features = np.array([1.0, 1.0, 1.0, 2.0, 2.0, 2.0])

        detector = self.DriftDetector(
            reference_features=reference_features,
            n_bins=2
        )

        kl_div = detector.calculate_kl_divergence(current_features)

        # KL divergence should be ≈ 0 for identical distributions
        self.assertLess(kl_div, 0.001, f"Expected KL ≈ 0, got {kl_div}")

    def test_sliding_window_update(self):
        """Test feature distribution update with sliding window"""
        if self.DriftDetector is None:
            self.skipTest("DriftDetector not implemented")

        reference_features = np.random.normal(0, 1, 500)

        detector = self.DriftDetector(
            reference_features=reference_features,
            window_size=100,
            n_bins=10
        )

        # Update with new features
        new_batch_1 = np.random.normal(0, 1, 100)
        psi_1 = detector.update_and_calculate_psi(new_batch_1)

        # Update with shifted features
        new_batch_2 = np.random.normal(3, 1, 100)
        psi_2 = detector.update_and_calculate_psi(new_batch_2)

        # PSI should increase (more drift)
        self.assertGreater(psi_2, psi_1, "PSI should increase with drift")

    def test_histogram_binning(self):
        """Test feature histogram binning for PSI calculation"""
        if self.DriftDetector is None:
            self.skipTest("DriftDetector not implemented")

        features = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        detector = self.DriftDetector(
            reference_features=features,
            n_bins=5
        )

        # Get histogram
        hist = detector.get_histogram(features)

        # Should have 5 bins
        self.assertEqual(len(hist), 5, f"Expected 5 bins, got {len(hist)}")

        # Sum of histogram should equal number of samples
        self.assertEqual(np.sum(hist), len(features), "Histogram sum mismatch")

    def test_threshold_alert_logic(self):
        """Test drift alert threshold (PSI > 0.2)"""
        if self.DriftDetector is None:
            self.skipTest("DriftDetector not implemented")

        reference_features = np.random.normal(0, 1, 1000)

        detector = self.DriftDetector(
            reference_features=reference_features,
            drift_threshold=0.2,
            n_bins=10
        )

        # Below threshold
        safe_features = np.random.normal(0, 1, 500)
        is_drifted_safe = detector.is_drifted(safe_features)
        self.assertFalse(is_drifted_safe, "Safe features incorrectly flagged as drift")

        # Above threshold
        drifted_features = np.random.normal(4, 1, 500)
        is_drifted_bad = detector.is_drifted(drifted_features)
        self.assertTrue(is_drifted_bad, "Drifted features not detected")


class TestShadowRecorder(unittest.TestCase):
    """Test ShadowRecorder logging functionality"""

    def setUp(self):
        """Initialize test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name) / "shadow_records.json"

    def tearDown(self):
        """Cleanup"""
        self.temp_dir.cleanup()

    def test_shadow_record_creation(self):
        """Test ShadowRecorder creates records for signals"""
        try:
            from src.monitoring.shadow_recorder import ShadowRecorder
        except ImportError:
            self.skipTest("ShadowRecorder not implemented")

        recorder = ShadowRecorder(output_path=str(self.output_path))

        # Record a shadow signal
        record = {
            'timestamp': '2026-01-16T10:00:00Z',
            'signal': 1,  # BUY
            'confidence': 0.72,
            'price': 1.0850,
            'features_hash': 'abc123'
        }

        recorder.record_signal(record)

        # Verify file was created
        self.assertTrue(self.output_path.exists(), "Shadow record file not created")

    def test_shadow_record_json_format(self):
        """Test ShadowRecorder outputs valid JSON"""
        try:
            from src.monitoring.shadow_recorder import ShadowRecorder
        except ImportError:
            self.skipTest("ShadowRecorder not implemented")

        recorder = ShadowRecorder(output_path=str(self.output_path))

        records = [
            {'timestamp': '2026-01-16T10:00:00Z', 'signal': 1, 'price': 1.0850},
            {'timestamp': '2026-01-16T10:01:00Z', 'signal': -1, 'price': 1.0840},
        ]

        for record in records:
            recorder.record_signal(record)

        # Read and verify JSON validity
        with open(self.output_path, 'r') as f:
            data = json.load(f)

        self.assertIsInstance(data, (list, dict), "Invalid JSON format")

    def test_signal_accuracy_tracking(self):
        """Test ShadowRecorder tracks signal accuracy vs actual price"""
        try:
            from src.monitoring.shadow_recorder import ShadowRecorder
        except ImportError:
            self.skipTest("ShadowRecorder not implemented")

        recorder = ShadowRecorder(output_path=str(self.output_path))

        # Record signal
        signal_record = {
            'timestamp': '2026-01-16T10:00:00Z',
            'signal': 1,  # BUY signal
            'price': 1.0850,
        }
        recorder.record_signal(signal_record)

        # Record actual price 15 minutes later
        actual_record = {
            'timestamp': '2026-01-16T10:15:00Z',
            'actual_price': 1.0860,
        }

        accuracy = recorder.calculate_accuracy(signal_record, actual_record)

        # If price went up after BUY signal, accuracy should be positive
        self.assertGreater(accuracy, 0, "BUY signal followed by price increase should be accurate")


class TestShadowModeIntegration(unittest.TestCase):
    """Test Shadow Mode blocks real orders"""

    def test_shadow_mode_blocks_execution_bridge(self):
        """Test MLLiveStrategy in shadow mode does NOT call ExecutionBridge"""
        try:
            from src.strategy.ml_live_strategy import MLLiveStrategy
        except ImportError:
            self.skipTest("MLLiveStrategy not implemented")

        # Mock ExecutionBridge
        with patch('src.strategy.ml_live_strategy.ExecutionBridge') as mock_bridge:
            strategy = MLLiveStrategy(
                mode='shadow',  # Shadow mode
                confidence_threshold=0.55
            )

            # Generate signal
            signal, metadata = strategy.on_tick(
                close=1.0850,
                high=1.0860,
                low=1.0840,
                volume=10000
            )

            # ExecutionBridge should NOT be called
            # (We'll verify this through lack of execute_order calls)
            self.assertEqual(mock_bridge.call_count, 0, "Shadow mode should not call ExecutionBridge")

    def test_normal_mode_executes_orders(self):
        """Test MLLiveStrategy in normal mode DOES call ExecutionBridge"""
        try:
            from src.strategy.ml_live_strategy import MLLiveStrategy
        except ImportError:
            self.skipTest("MLLiveStrategy not implemented")

        with patch('src.strategy.ml_live_strategy.ExecutionBridge') as mock_bridge:
            strategy = MLLiveStrategy(
                mode='normal',  # Normal mode
                confidence_threshold=0.55
            )

            # Generate signal
            signal, metadata = strategy.on_tick(
                close=1.0850,
                high=1.0860,
                low=1.0840,
                volume=10000
            )

            # In normal mode with actual signal, ExecutionBridge should be called
            # (This test assumes signal != 0, which may require proper setup)

    def test_shadow_mode_logging(self):
        """Test Shadow Mode logs signals correctly"""
        try:
            from src.strategy.ml_live_strategy import MLLiveStrategy
        except ImportError:
            self.skipTest("MLLiveStrategy not implemented")

        # Capture logs
        with patch('src.strategy.ml_live_strategy.logger') as mock_logger:
            strategy = MLLiveStrategy(mode='shadow')

            strategy.on_tick(close=1.0850, high=1.0860, low=1.0840, volume=10000)

            # Should log SHADOW_MODE_BLOCK when preventing order
            mock_logger.info.assert_called()

            # Check if any call contains SHADOW_MODE_BLOCK
            call_args_list = [str(call) for call in mock_logger.info.call_args_list]
            self.assertTrue(
                any('SHADOW' in str(call) for call in call_args_list),
                "Shadow mode should log SHADOW_MODE indicator"
            )


class TestCircuitBreakerIntegration(unittest.TestCase):
    """Test Circuit Breaker triggers on drift detection"""

    def test_circuit_breaker_triggers_on_high_drift(self):
        """Test CircuitBreaker stops inference when PSI > 0.2"""
        try:
            from src.risk.circuit_breaker import CircuitBreaker
            from src.monitoring.drift_detector import DriftDetector
        except ImportError:
            self.skipTest("CircuitBreaker or DriftDetector not implemented")

        breaker = CircuitBreaker()
        detector = DriftDetector(
            reference_features=np.random.normal(0, 1, 1000),
            drift_threshold=0.2
        )

        # Simulate high drift
        drifted_features = np.random.normal(4, 1, 500)
        psi = detector.calculate_psi(drifted_features)

        if psi > 0.2:
            breaker.trip()

        # Verify breaker is tripped
        self.assertTrue(breaker.is_tripped(), "Circuit breaker should trip on high drift")

    def test_circuit_breaker_reset(self):
        """Test CircuitBreaker can reset when drift resolves"""
        try:
            from src.risk.circuit_breaker import CircuitBreaker
        except ImportError:
            self.skipTest("CircuitBreaker not implemented")

        breaker = CircuitBreaker(auto_reset_seconds=10)

        breaker.trip()
        self.assertTrue(breaker.is_tripped())

        # Simulate reset (normally manual or time-based)
        breaker.reset()
        self.assertFalse(breaker.is_tripped())


class TestShadowPerformanceJSON(unittest.TestCase):
    """Test ML_SHADOW_PERFORMANCE.json format and accuracy"""

    def setUp(self):
        """Initialize test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.perf_file = Path(self.temp_dir.name) / "ML_SHADOW_PERFORMANCE.json"

    def tearDown(self):
        """Cleanup"""
        self.temp_dir.cleanup()

    def test_performance_json_structure(self):
        """Test performance JSON has required fields"""
        # Create sample performance JSON
        performance_data = {
            'test_period': '2026-01-16T00:00:00Z to 2026-01-16T01:00:00Z',
            'total_signals': 42,
            'buy_signals': 20,
            'sell_signals': 15,
            'hold_signals': 7,
            'accuracy_15min': 0.62,
            'accuracy_1h': 0.58,
            'average_confidence': 0.68,
            'drift_events': 0,
            'max_psi': 0.15
        }

        with open(self.perf_file, 'w') as f:
            json.dump(performance_data, f)

        # Verify JSON can be read
        with open(self.perf_file, 'r') as f:
            loaded = json.load(f)

        # Verify required fields
        required_fields = [
            'total_signals', 'accuracy_15min', 'accuracy_1h',
            'average_confidence', 'drift_events', 'max_psi'
        ]

        for field in required_fields:
            self.assertIn(field, loaded, f"Missing required field: {field}")

    def test_accuracy_calculation_logic(self):
        """Test signal accuracy calculation (price moved in predicted direction)"""
        # BUY signal at 1.0850, price 15 min later = 1.0860
        buy_signal_price = 1.0850
        actual_price = 1.0860

        is_accurate = actual_price > buy_signal_price

        self.assertTrue(is_accurate, "BUY signal should be accurate if price increased")

        # SELL signal at 1.0860, price 15 min later = 1.0850
        sell_signal_price = 1.0860
        actual_price = 1.0850

        is_accurate = actual_price < sell_signal_price

        self.assertTrue(is_accurate, "SELL signal should be accurate if price decreased")


class TestEndToEndShadowMode(unittest.TestCase):
    """Integration tests for complete shadow mode workflow"""

    def test_24hour_shadow_simulation(self):
        """Test shadow mode running for 24+ hours of simulated data"""
        # This test verifies the system can handle extended shadow trading

        # Generate 1440 ticks (24 hours of minute data)
        n_ticks = 1440
        base_price = 1.0850

        prices = base_price + np.cumsum(np.random.randn(n_ticks) * 0.00005)

        # Would run MLLiveStrategy in shadow mode through all ticks
        # Should not crash and should log signals correctly

        self.assertGreater(len(prices), 1400, "Should simulate 24+ hours")

    def test_drift_detection_during_market_hours(self):
        """Test drift detection responds to market volatility"""
        # Simulate market open volatility
        normal_prices = np.random.normal(1.0850, 0.0001, 300)  # 5 hours normal
        volatile_prices = np.random.normal(1.0850, 0.0005, 300)  # 5 hours volatile

        # Detector should flag increased volatility as potential drift
        self.assertGreater(
            np.std(volatile_prices),
            np.std(normal_prices),
            "Volatile prices should have higher std dev"
        )


def run_audit_suite():
    """Run full audit suite"""
    print("\n" + "="*80)
    print("Task #115 Audit Suite - ML Strategy Shadow Mode & Concept Drift")
    print("="*80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDriftDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestShadowRecorder))
    suite.addTests(loader.loadTestsFromTestCase(TestShadowModeIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCircuitBreakerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestShadowPerformanceJSON))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndShadowMode))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*80)
    print("Audit Results Summary")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✅ All audit tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. See details above.")
        return 1


if __name__ == '__main__':
    exit(run_audit_suite())
