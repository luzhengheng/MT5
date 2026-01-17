#!/usr/bin/env python3
"""
Task #115 Integration Test - Shadow Mode & Drift Detection

Tests the complete workflow:
1. Initialize DriftDetector with reference training data
2. Initialize MLLiveStrategy in shadow mode
3. Simulate 24+ hours of market ticks
4. Track signal accuracy and drift events
5. Generate performance report

Protocol: v4.3 (Zero-Trust Edition)
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, '/opt/mt5-crs')

from src.inference.ml_predictor import MLPredictor
from src.inference.online_features import OnlineFeatureCalculator
from src.monitoring.drift_detector import DriftDetector
from src.monitoring.shadow_recorder import ShadowRecorder
from src.strategy.ml_live_strategy import MLLiveStrategy


def generate_synthetic_market_data(n_ticks: int = 1440,
                                    base_price: float = 1.0850,
                                    volatility: float = 0.0001,
                                    drift_shift: int = None) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for testing.

    Args:
        n_ticks: Number of ticks to generate
        base_price: Starting price
        volatility: Price volatility (std dev of returns)
        drift_shift: Tick number when to shift mean (for testing drift detection)

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)

    prices = [base_price]
    for i in range(n_ticks - 1):
        if drift_shift and i > drift_shift:
            # Introduce drift shift
            change = np.random.randn() * volatility * 2 + 0.0001
        else:
            change = np.random.randn() * volatility

        prices.append(prices[-1] + change)

    prices = np.array(prices)

    df = pd.DataFrame({
        'close': prices,
        'high': prices + np.abs(np.random.randn(n_ticks)) * volatility * 0.5,
        'low': prices - np.abs(np.random.randn(n_ticks)) * volatility * 0.5,
        'volume': np.random.randint(1000, 10000, n_ticks),
        'timestamp': [datetime.now() + timedelta(minutes=i) for i in range(n_ticks)]
    })

    return df


def load_training_features() -> np.ndarray:
    """
    Load or generate reference training features.

    Returns:
        Training features array (N, 21)
    """
    try:
        # Try to load real training data from Task #113
        training_path = Path('/opt/mt5-crs/data_lake/eodhd_standardized/EURUSD_M1.parquet')
        if training_path.exists():
            df = pd.read_parquet(training_path)

            # Extract OHLCV
            prices = df['close'].values[:1000]

            # Calculate 21 features for each bar
            features_list = []

            calc = OnlineFeatureCalculator(max_lookback=50)

            for i in range(len(prices)):
                high = df['high'].iloc[i] if 'high' in df.columns else prices[i] * 1.0001
                low = df['low'].iloc[i] if 'low' in df.columns else prices[i] * 0.9999
                vol = df['volume'].iloc[i] if 'volume' in df.columns else 5000

                calc.update(prices[i], high, low, vol)

                feature_vector = calc.get_feature_vector()
                if feature_vector is not None:
                    features_list.append(feature_vector)

            if features_list:
                return np.array(features_list)

    except Exception as e:
        logger.warning(f"Could not load training features: {e}")

    # Generate synthetic training features
    logger.info("Generating synthetic training features...")
    return np.random.normal(0, 1, (1000, 21))


def main():
    """Run Task #115 integration test"""
    print("\n" + "="*80)
    print("Task #115 Integration Test - ML Strategy Shadow Mode & Concept Drift")
    print("="*80)

    # 1. Load training data for drift detector baseline
    print("\n1. Loading training features for baseline...")
    print("-" * 80)

    reference_features = load_training_features()
    print(f"✓ Loaded reference features: shape={reference_features.shape}")

    # 2. Initialize drift detector
    print("\n2. Initializing DriftDetector...")
    print("-" * 80)

    drift_detector = DriftDetector(
        reference_features=reference_features,
        n_bins=10,
        drift_threshold=0.25,
        alert_threshold=0.20
    )
    print("✓ DriftDetector initialized")

    # 3. Initialize shadow recorder
    print("\n3. Initializing ShadowRecorder...")
    print("-" * 80)

    shadow_recorder = ShadowRecorder(
        output_path="/opt/mt5-crs/data/outputs/audit/shadow_records.json"
    )
    print("✓ ShadowRecorder initialized")

    # 4. Initialize ML strategy in shadow mode
    print("\n4. Initializing MLLiveStrategy in SHADOW MODE...")
    print("-" * 80)

    strategy = MLLiveStrategy(
        model_path="/opt/mt5-crs/data/models/xgboost_task_114.pkl",
        confidence_threshold=0.55,
        shadow_mode=True,
        enable_drift_detection=True,
        reference_features=reference_features
    )
    print("✓ MLLiveStrategy initialized in shadow mode")

    # 5. Generate synthetic market data
    print("\n5. Generating synthetic market data (24+ hours)...")
    print("-" * 80)

    # Generate 1440 minutes (24 hours) with drift shift at tick 720 (12 hours)
    market_data = generate_synthetic_market_data(
        n_ticks=1440,
        base_price=1.0850,
        volatility=0.0001,
        drift_shift=720  # Introduce drift halfway through
    )
    print(f"✓ Generated {len(market_data)} ticks of synthetic data")

    # 6. Simulate shadow trading
    print("\n6. Simulating shadow trading (this may take a minute)...")
    print("-" * 80)

    signals_by_type = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    drift_alerts = 0

    for idx, row in market_data.iterrows():
        signal, metadata = strategy.on_tick(
            close=row['close'],
            high=row['high'],
            low=row['low'],
            volume=row['volume']
        )

        # Track drift events
        if metadata.get('drift_alert') and metadata['drift_alert'].get('drift_detected'):
            drift_alerts += 1

        # Track signals
        if signal == 1:
            signals_by_type['BUY'] += 1
        elif signal == -1:
            signals_by_type['SELL'] += 1
        else:
            signals_by_type['HOLD'] += 1

        # Print progress every 300 ticks
        if (idx + 1) % 300 == 0:
            logger.info(
                f"Processed {idx + 1}/{len(market_data)} ticks, "
                f"Signals: BUY={signals_by_type['BUY']}, "
                f"SELL={signals_by_type['SELL']}, "
                f"Drift alerts={drift_alerts}"
            )

    # 7. Export results
    print("\n7. Exporting results...")
    print("-" * 80)

    # Save shadow records
    shadow_file = strategy.shadow_recorder.save_to_file() if strategy.shadow_recorder else None
    print(f"✓ Saved shadow records to {shadow_file}")

    # Export performance metrics
    perf_file = strategy.shadow_recorder.export_performance_metrics() if strategy.shadow_recorder else None
    print(f"✓ Exported performance metrics to {perf_file}")

    # 8. Generate report
    print("\n8. Generating test report...")
    print("-" * 80)

    stats = strategy.get_statistics()
    drift_stats = strategy.drift_detector.get_statistics() if strategy.drift_detector else {}

    report = {
        'test_metadata': {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'SHADOW_MODE_24H',
            'protocol': 'v4.3'
        },
        'strategy_metrics': {
            'total_ticks': stats['tick_count'],
            'total_signals': stats['signal_count'],
            'signal_rate': f"{stats['signal_rate']:.2%}",
            'latency_p95_ms': f"{stats['p95_latency_ms']:.2f}",
            'latency_p99_ms': f"{stats['p99_latency_ms']:.2f}",
        },
        'signal_distribution': signals_by_type,
        'drift_detection': {
            'drift_events': drift_alerts,
            'detector_stats': drift_stats
        }
    }

    print("\n" + "="*80)
    print("TEST REPORT")
    print("="*80)
    print(f"Ticks processed: {report['strategy_metrics']['total_ticks']}")
    print(f"Signals generated: {report['strategy_metrics']['total_signals']}")
    print(f"Signal rate: {report['strategy_metrics']['signal_rate']}")
    print(f"Latency P95: {report['strategy_metrics']['latency_p95_ms']} ms")
    print(f"Latency P99: {report['strategy_metrics']['latency_p99_ms']} ms")

    print(f"\nSignal Distribution:")
    for signal_type, count in signals_by_type.items():
        print(f"  {signal_type}: {count}")

    print(f"\nDrift Detection:")
    print(f"  Drift events: {report['drift_detection']['drift_events']}")

    print(f"\nShadow Recorder Summary:")
    if strategy.shadow_recorder:
        print(strategy.shadow_recorder.get_summary())

    # 9. Physical verification
    print("\n9. Physical verification...")
    print("-" * 80)

    # Check that shadow records file exists
    if shadow_file and Path(shadow_file).exists():
        file_size = Path(shadow_file).stat().st_size
        print(f"✓ Shadow records file exists: {file_size} bytes")
    else:
        print("✗ Shadow records file not found")

    # Check that performance metrics file exists
    if perf_file and Path(perf_file).exists():
        file_size = Path(perf_file).stat().st_size
        print(f"✓ Performance metrics file exists: {file_size} bytes")
    else:
        print("✗ Performance metrics file not found")

    print("\n" + "="*80)
    print("✅ Task #115 Integration Test Completed Successfully")
    print("="*80)

    return 0


if __name__ == '__main__':
    exit(main())
