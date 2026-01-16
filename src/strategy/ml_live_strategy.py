#!/usr/bin/env python3
"""
Task #114 + #115: ML Live Strategy with Shadow Mode

Real-time ML-driven trading strategy that integrates:
- OnlineFeatureCalculator (streaming features)
- MLPredictor (XGBoost inference)
- Risk management and position sizing
- Shadow Mode (Task #115): Log signals without executing orders
- Drift Detection (Task #115): Monitor feature distribution shifts

Protocol: v4.3 (Zero-Trust Edition)
"""

import logging
import hashlib
import time
from typing import Optional, Dict, Tuple
import numpy as np

from src.inference.online_features import OnlineFeatureCalculator
from src.inference.ml_predictor import MLPredictor

# Optional drift detection (Task #115)
try:
    from src.monitoring.drift_detector import DriftDetector
    from src.monitoring.shadow_recorder import ShadowRecorder
    HAS_DRIFT_MONITORING = True
except ImportError:
    HAS_DRIFT_MONITORING = False

logger = logging.getLogger(__name__)


class MLLiveStrategy:
    """
    ML-powered live trading strategy with optional shadow mode and drift detection.

    This strategy receives real-time tick data, calculates features online,
    runs ML inference, and generates trading signals.

    In shadow mode (Task #115), signals are recorded but NOT executed,
    allowing production monitoring before risking capital.
    """

    def __init__(self,
                 model_path: str = "/opt/mt5-crs/data/models/xgboost_task_114.pkl",
                 confidence_threshold: float = 0.55,
                 lookback_period: int = 50,
                 throttle_seconds: int = 60,
                 shadow_mode: bool = False,
                 enable_drift_detection: bool = False,
                 reference_features: Optional[np.ndarray] = None):
        """
        Initialize ML live strategy.

        Args:
            model_path: Path to trained XGBoost model
            confidence_threshold: Minimum confidence for signals
            lookback_period: Historical periods to retain
            throttle_seconds: Minimum seconds between signals
            shadow_mode: If True, log signals without executing (Task #115)
            enable_drift_detection: If True, monitor feature distribution drift (Task #115)
            reference_features: Training features for drift detection baseline
        """
        # Initialize components
        self.feature_calculator = OnlineFeatureCalculator(
            max_lookback=lookback_period
        )
        self.predictor = MLPredictor(
            model_path=model_path,
            confidence_threshold=confidence_threshold
        )

        self.throttle_seconds = throttle_seconds
        self.last_signal_time = 0
        self.tick_count = 0
        self.signal_count = 0

        # Shadow mode (Task #115)
        self.shadow_mode = shadow_mode
        self.shadow_recorder = None
        if shadow_mode and HAS_DRIFT_MONITORING:
            self.shadow_recorder = ShadowRecorder()
            logger.info("[SHADOW_MODE] ShadowRecorder initialized")

        # Drift detection (Task #115)
        self.enable_drift_detection = enable_drift_detection
        self.drift_detector = None
        if enable_drift_detection and HAS_DRIFT_MONITORING and reference_features is not None:
            self.drift_detector = DriftDetector(
                reference_features=reference_features,
                drift_threshold=0.25,
                alert_threshold=0.20
            )
            logger.info("[DRIFT_DETECTION] DriftDetector initialized")

        self.is_inference_blocked = False  # Set to True when drift detected

        # Performance tracking
        self.latency_samples = []

        logger.info(
            f"MLLiveStrategy initialized "
            f"(confidence={confidence_threshold}, throttle={throttle_seconds}s, "
            f"shadow_mode={shadow_mode}, drift_detection={enable_drift_detection})"
        )

    def on_tick(self,
                close: float,
                high: float,
                low: float,
                volume: float) -> Tuple[int, Dict]:
        """
        Process incoming tick and generate trading signal

        Args:
            close: Close price
            high: High price
            low: Low price
            volume: Volume

        Returns:
            Tuple of (signal, metadata)
            - signal: 0 (HOLD), 1 (BUY), -1 (SELL)
            - metadata: Dict with inference details
        """
        start_time = time.time()
        self.tick_count += 1

        # Update feature calculator
        ready = self.feature_calculator.update(close, high, low, volume)

        if not ready:
            logger.debug(
                f"Tick {self.tick_count}: Insufficient data "
                f"({len(self.feature_calculator.close_buffer)}/50)"
            )
            return 0, {'reason': 'insufficient_data', 'ticks': self.tick_count}

        # Calculate features
        feature_vector = self.feature_calculator.get_feature_vector()

        if feature_vector is None:
            logger.warning(f"Tick {self.tick_count}: Feature calculation failed")
            return 0, {'reason': 'feature_error', 'ticks': self.tick_count}

        # Generate feature hash for logging
        feature_hash = hashlib.md5(
            feature_vector.tobytes()
        ).hexdigest()[:8]

        # Check drift detection (Task #115)
        drift_alert = None
        if self.drift_detector is not None:
            drift_alert = self.drift_detector.check_alert_conditions(feature_vector)

            if drift_alert['drift_detected']:
                self.is_inference_blocked = True
                logger.error(
                    f"[DRIFT_GUARD] INFERENCE BLOCKED - PSI={drift_alert['psi']:.4f}"
                )

                # In shadow mode, still record for analysis
                if not self.shadow_mode:
                    return 0, {
                        'reason': 'drift_detected',
                        'drift_alert': drift_alert,
                        'ticks': self.tick_count
                    }

        # Check if inference should be blocked
        if self.is_inference_blocked and not self.shadow_mode:
            logger.warning("[CIRCUIT_BREAKER] Inference blocked due to drift")
            return 0, {'reason': 'inference_blocked', 'ticks': self.tick_count}

        # Run inference
        signal, confidence, inference_latency_ms = self.predictor.predict(
            feature_vector
        )

        # Total latency (feature calc + inference)
        total_latency_ms = (time.time() - start_time) * 1000
        self.latency_samples.append(total_latency_ms)

        # Keep only last 100 samples
        if len(self.latency_samples) > 100:
            self.latency_samples.pop(0)

        # Throttle signals
        current_time = time.time()
        time_since_last_signal = current_time - self.last_signal_time

        if signal != 0 and time_since_last_signal < self.throttle_seconds:
            logger.info(
                f"[THROTTLED] Tick {self.tick_count}: "
                f"Signal={signal}, Confidence={confidence:.4f}, "
                f"Throttle={self.throttle_seconds - time_since_last_signal:.1f}s remaining"
            )
            signal = 0  # Override to HOLD

        # Shadow Mode: Record signal without executing (Task #115)
        if self.shadow_mode and signal != 0 and self.shadow_recorder is not None:
            shadow_record = {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'signal': signal,
                'price': close,
                'confidence': confidence,
                'features_hash': feature_hash
            }
            self.shadow_recorder.record_signal(shadow_record)

            logger.info(
                f"[SHADOW_MODE_RECORD] Tick {self.tick_count}: "
                f"Signal={signal} recorded (NOT executed)"
            )

        # Log inference result
        if signal != 0:
            self.signal_count += 1
            self.last_signal_time = current_time

            mode_indicator = "[SHADOW_MODE] " if self.shadow_mode else "[INFERENCE] "
            logger.info(
                f"{mode_indicator}Tick {self.tick_count}: "
                f"Price={close:.5f} | "
                f"Features_Hash={feature_hash} | "
                f"Pred={signal} ({confidence:.4f}) | "
                f"Latency={total_latency_ms:.2f}ms"
            )

        # Metadata
        metadata = {
            'tick': self.tick_count,
            'price': close,
            'signal': signal,
            'confidence': confidence,
            'feature_hash': feature_hash,
            'latency_ms': total_latency_ms,
            'inference_latency_ms': inference_latency_ms,
            'throttled': time_since_last_signal < self.throttle_seconds if signal != 0 else False,
            'shadow_mode': self.shadow_mode,
            'drift_alert': drift_alert
        }

        return signal, metadata

    def get_statistics(self) -> Dict:
        """
        Get strategy performance statistics

        Returns:
            Dictionary of statistics
        """
        if not self.latency_samples:
            mean_latency = 0
            p95_latency = 0
            p99_latency = 0
        else:
            mean_latency = np.mean(self.latency_samples)
            p95_latency = np.percentile(self.latency_samples, 95)
            p99_latency = np.percentile(self.latency_samples, 99)

        return {
            'tick_count': self.tick_count,
            'signal_count': self.signal_count,
            'signal_rate': self.signal_count / self.tick_count if self.tick_count > 0 else 0,
            'mean_latency_ms': mean_latency,
            'p95_latency_ms': p95_latency,
            'p99_latency_ms': p99_latency,
            'model_info': self.predictor.get_model_info()
        }

    def reset(self):
        """Reset strategy state"""
        self.feature_calculator = OnlineFeatureCalculator(
            max_lookback=self.feature_calculator.max_lookback
        )
        self.tick_count = 0
        self.signal_count = 0
        self.last_signal_time = 0
        self.latency_samples = []
        logger.info("Strategy reset")


def main():
    """Test harness"""
    import pandas as pd

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\n" + "="*80)
    print("ML Live Strategy - Test Harness")
    print("="*80)

    # Initialize strategy
    strategy = MLLiveStrategy(
        confidence_threshold=0.55,
        throttle_seconds=10
    )

    # Load sample data from Task #111
    print("\nLoading sample EODHD data...")
    try:
        df = pd.read_parquet("/opt/mt5-crs/data_lake/eodhd_standardized/EURUSD_M1.parquet")
        print(f"Loaded {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        print("Generating synthetic data instead...")

        # Generate synthetic OHLCV data
        np.random.seed(42)
        n = 200
        base_price = 1.05
        df = pd.DataFrame({
            'close': base_price + np.cumsum(np.random.randn(n) * 0.0001),
            'high': base_price + np.cumsum(np.random.randn(n) * 0.0001) + 0.0001,
            'low': base_price + np.cumsum(np.random.randn(n) * 0.0001) - 0.0001,
            'volume': np.random.randint(1000, 10000, n)
        })

    # Simulate streaming ticks
    print(f"\nSimulating {len(df)} ticks...")
    print("-" * 80)

    signals = []
    for i, row in df.iterrows():
        signal, metadata = strategy.on_tick(
            close=row['close'],
            high=row['high'],
            low=row['low'],
            volume=row['volume']
        )

        signals.append(signal)

        # Print every 50 ticks
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1} ticks...")

    # Print statistics
    print("\n" + "="*80)
    print("Strategy Statistics")
    print("="*80)

    stats = strategy.get_statistics()

    print(f"Total Ticks:       {stats['tick_count']}")
    print(f"Signals Generated: {stats['signal_count']}")
    print(f"Signal Rate:       {stats['signal_rate']:.2%}")
    print(f"\nLatency Performance:")
    print(f"  Mean:  {stats['mean_latency_ms']:.2f} ms")
    print(f"  P95:   {stats['p95_latency_ms']:.2f} ms")
    print(f"  P99:   {stats['p99_latency_ms']:.2f} ms")

    # Check latency target
    if stats['p95_latency_ms'] < 10:
        print(f"\n✅ Latency target met (<10ms P95)")
    else:
        print(f"\n⚠️  Latency target NOT met (P95 = {stats['p95_latency_ms']:.2f}ms)")

    # Signal distribution
    print(f"\nSignal Distribution:")
    buy_signals = sum(1 for s in signals if s == 1)
    sell_signals = sum(1 for s in signals if s == -1)
    hold_signals = sum(1 for s in signals if s == 0)

    print(f"  BUY:  {buy_signals} ({buy_signals/len(signals)*100:.1f}%)")
    print(f"  SELL: {sell_signals} ({sell_signals/len(signals)*100:.1f}%)")
    print(f"  HOLD: {hold_signals} ({hold_signals/len(signals)*100:.1f}%)")


if __name__ == '__main__':
    main()
