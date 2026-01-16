#!/usr/bin/env python3
"""
Task #115: Shadow Recorder Module

Records ML strategy signals in shadow mode without executing real orders.
Tracks signal accuracy by comparing predicted direction with actual price movement.

Protocol: v4.3 (Zero-Trust Edition)
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class ShadowRecorder:
    """
    Records shadow trading signals and calculates accuracy metrics.

    In shadow mode, the strategy generates signals but does NOT execute orders.
    This allows monitoring model performance in production before risking real capital.
    """

    def __init__(self,
                 output_path: str = "/opt/mt5-crs/data/outputs/audit/shadow_records.json",
                 max_records: int = 10000):
        """
        Initialize shadow recorder.

        Args:
            output_path: Path to store shadow records JSON
            max_records: Maximum records to keep in memory
        """
        self.output_path = Path(output_path)
        self.max_records = max_records

        # In-memory storage
        self.records = deque(maxlen=max_records)
        self.signal_records = {}  # Map signal ID to record for accuracy calculation
        self.price_history = deque(maxlen=1000)  # Historical prices for accuracy check

        # Statistics
        self.total_signals = 0
        self.buy_signals = 0
        self.sell_signals = 0
        self.hold_signals = 0

        # Create output directory if needed
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"ShadowRecorder initialized: "
            f"output_path={output_path}, "
            f"max_records={max_records}"
        )

    def record_price(self, price: float, timestamp: Optional[str] = None) -> str:
        """
        Record market price for accuracy calculations.

        Args:
            price: Market price
            timestamp: ISO format timestamp (use current time if None)

        Returns:
            Unique price record ID
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat() + 'Z'

        price_id = f"price_{len(self.price_history)}"

        price_record = {
            'id': price_id,
            'timestamp': timestamp,
            'price': price
        }

        self.price_history.append(price_record)

        return price_id

    def record_signal(self,
                      signal: Dict) -> str:
        """
        Record a shadow trading signal.

        Args:
            signal: Dictionary with keys:
                - timestamp: ISO format timestamp
                - signal: 1 (BUY), -1 (SELL), 0 (HOLD)
                - price: Entry price
                - confidence: Model confidence [0, 1]
                - features_hash: Hash of feature vector (for tracing)
                - feature_values: Optional dict of feature values
                - model_info: Optional model metadata

        Returns:
            Unique signal record ID
        """
        signal_id = f"signal_{self.total_signals}_{datetime.now().timestamp()}"

        record = {
            'id': signal_id,
            'timestamp': signal.get('timestamp', datetime.now().isoformat() + 'Z'),
            'signal': signal.get('signal', 0),
            'price': signal.get('price', 0.0),
            'confidence': signal.get('confidence', 0.0),
            'features_hash': signal.get('features_hash', ''),
            'feature_values': signal.get('feature_values', {}),
            'model_info': signal.get('model_info', {}),
            'mode': 'SHADOW_MODE',  # Mark as shadow mode
            'accuracy_15min': None,  # To be filled later
            'accuracy_1h': None,
            'accuracy_4h': None
        }

        self.records.append(record)
        self.signal_records[signal_id] = record

        # Update statistics
        self.total_signals += 1
        if record['signal'] == 1:
            self.buy_signals += 1
        elif record['signal'] == -1:
            self.sell_signals += 1
        else:
            self.hold_signals += 1

        logger.debug(
            f"[SHADOW_RECORD] Signal {signal_id}: "
            f"signal={record['signal']}, confidence={record['confidence']:.4f}, "
            f"price={record['price']:.5f}"
        )

        return signal_id

    def update_signal_accuracy(self,
                               signal_id: str,
                               actual_price: float,
                               timeframe_minutes: int = 15) -> Optional[bool]:
        """
        Update signal accuracy with actual price movement after timeframe.

        Args:
            signal_id: Signal ID to update
            actual_price: Actual price at timeframe end
            timeframe_minutes: Timeframe for accuracy check (15, 60, 240)

        Returns:
            True if signal was accurate, False if inaccurate, None if not applicable
        """
        if signal_id not in self.signal_records:
            logger.warning(f"Signal {signal_id} not found for accuracy update")
            return None

        record = self.signal_records[signal_id]
        signal_type = record['signal']
        entry_price = record['price']

        # Calculate accuracy
        is_accurate = None

        if signal_type == 1:  # BUY signal
            is_accurate = actual_price > entry_price

        elif signal_type == -1:  # SELL signal
            is_accurate = actual_price < entry_price

        else:  # HOLD
            is_accurate = None

        # Store in appropriate timeframe field
        if timeframe_minutes == 15:
            record['accuracy_15min'] = is_accurate
        elif timeframe_minutes == 60:
            record['accuracy_1h'] = is_accurate
        elif timeframe_minutes == 240:
            record['accuracy_4h'] = is_accurate

        if is_accurate is not None:
            logger.info(
                f"[SHADOW_ACCURACY] Signal {signal_id}: "
                f"{'ACCURATE' if is_accurate else 'INACCURATE'} "
                f"({entry_price:.5f} → {actual_price:.5f})"
            )

        return is_accurate

    def calculate_statistics(self) -> Dict:
        """
        Calculate performance statistics from shadow records.

        Returns:
            Dictionary with metrics:
            - total_signals, buy_signals, sell_signals, hold_signals
            - accuracy_15min, accuracy_1h, accuracy_4h (% correct)
            - average_confidence
            - win_rate_buy, win_rate_sell
        """
        records_list = list(self.records)

        if not records_list:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'accuracy_15min': 0.0,
                'accuracy_1h': 0.0,
                'accuracy_4h': 0.0,
                'average_confidence': 0.0
            }

        # Count signal types
        buy_count = sum(1 for r in records_list if r['signal'] == 1)
        sell_count = sum(1 for r in records_list if r['signal'] == -1)

        # Calculate accuracy rates
        acc_15min_records = [r for r in records_list if r['accuracy_15min'] is not None]
        acc_1h_records = [r for r in records_list if r['accuracy_1h'] is not None]
        acc_4h_records = [r for r in records_list if r['accuracy_4h'] is not None]

        acc_15min_rate = (sum(1 for r in acc_15min_records if r['accuracy_15min']) /
                         len(acc_15min_records) * 100) if acc_15min_records else 0.0

        acc_1h_rate = (sum(1 for r in acc_1h_records if r['accuracy_1h']) /
                      len(acc_1h_records) * 100) if acc_1h_records else 0.0

        acc_4h_rate = (sum(1 for r in acc_4h_records if r['accuracy_4h']) /
                      len(acc_4h_records) * 100) if acc_4h_records else 0.0

        # Average confidence
        avg_conf = np.mean([r['confidence'] for r in records_list if r['signal'] != 0])

        # Win rates by signal type
        buy_wins = sum(1 for r in records_list if r['signal'] == 1 and r['accuracy_15min'] is True)
        sell_wins = sum(1 for r in records_list if r['signal'] == -1 and r['accuracy_15min'] is True)

        win_rate_buy = (buy_wins / buy_count * 100) if buy_count > 0 else 0.0
        win_rate_sell = (sell_wins / sell_count * 100) if sell_count > 0 else 0.0

        return {
            'total_signals': self.total_signals,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'hold_signals': self.hold_signals,
            'accuracy_15min': round(acc_15min_rate, 2),
            'accuracy_1h': round(acc_1h_rate, 2),
            'accuracy_4h': round(acc_4h_rate, 2),
            'average_confidence': round(float(avg_conf), 4),
            'win_rate_buy': round(win_rate_buy, 2),
            'win_rate_sell': round(win_rate_sell, 2),
            'test_period_start': records_list[0]['timestamp'] if records_list else None,
            'test_period_end': records_list[-1]['timestamp'] if records_list else None
        }

    def save_to_file(self, filename: Optional[str] = None) -> str:
        """
        Save all shadow records to JSON file.

        Args:
            filename: Output filename (use default if None)

        Returns:
            Path to saved file
        """
        output_file = Path(filename) if filename else self.output_path

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data with JSON-serializable types
        records_clean = []
        for r in self.records:
            record_dict = dict(r)
            # Convert numpy types to native Python types
            for key in record_dict:
                if isinstance(record_dict[key], (np.float32, np.float64)):
                    record_dict[key] = float(record_dict[key])
                elif isinstance(record_dict[key], (np.int32, np.int64)):
                    record_dict[key] = int(record_dict[key])
            records_clean.append(record_dict)

        data = {
            'metadata': {
                'timestamp': datetime.now().isoformat() + 'Z',
                'mode': 'SHADOW_MODE',
                'total_records': len(self.records),
                'max_records': self.max_records
            },
            'statistics': self.calculate_statistics(),
            'records': records_clean
        }

        # Write JSON
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self.records)} shadow records to {output_file}")

        return str(output_file)

    def export_performance_metrics(self,
                                    filename: str = "/opt/mt5-crs/data/outputs/audit/ML_SHADOW_PERFORMANCE.json") -> str:
        """
        Export ML shadow performance metrics for analysis.

        Args:
            filename: Output filename

        Returns:
            Path to exported file
        """
        stats = self.calculate_statistics()

        performance_data = {
            'test_metadata': {
                'test_type': 'ML_SHADOW_MODE',
                'timestamp': datetime.now().isoformat() + 'Z',
                'protocol_version': 'v4.3'
            },
            'performance_metrics': {
                'total_signals': stats['total_signals'],
                'buy_signals': stats['buy_signals'],
                'sell_signals': stats['sell_signals'],
                'hold_signals': stats['hold_signals'],
                'signal_distribution': {
                    'buy_pct': round(stats['buy_signals'] / max(stats['total_signals'], 1) * 100, 2),
                    'sell_pct': round(stats['sell_signals'] / max(stats['total_signals'], 1) * 100, 2),
                    'hold_pct': round(stats['hold_signals'] / max(stats['total_signals'], 1) * 100, 2)
                }
            },
            'accuracy_metrics': {
                'accuracy_15min': stats['accuracy_15min'],
                'accuracy_1h': stats['accuracy_1h'],
                'accuracy_4h': stats['accuracy_4h'],
                'average_confidence': stats['average_confidence'],
                'win_rate_buy': stats['win_rate_buy'],
                'win_rate_sell': stats['win_rate_sell']
            },
            'test_period': {
                'start': stats['test_period_start'],
                'end': stats['test_period_end']
            },
            'drift_events': 0,  # To be updated by DriftDetector
            'max_psi': 0.0     # To be updated by DriftDetector
        }

        output_file = Path(filename)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(performance_data, f, indent=2)

        logger.info(f"Exported ML shadow performance to {output_file}")

        return str(output_file)

    def get_summary(self) -> str:
        """Get summary string of shadow recorder state."""
        stats = self.calculate_statistics()

        summary = (
            f"ShadowRecorder Summary:\n"
            f"  Total Signals: {stats['total_signals']}\n"
            f"  Buy/Sell/Hold: {stats['buy_signals']}/{stats['sell_signals']}/{stats['hold_signals']}\n"
            f"  Accuracy (15m): {stats['accuracy_15min']:.1f}%\n"
            f"  Accuracy (1h): {stats['accuracy_1h']:.1f}%\n"
            f"  Avg Confidence: {stats['average_confidence']:.4f}"
        )

        return summary


def main():
    """Test harness for ShadowRecorder"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\n" + "="*80)
    print("ShadowRecorder - Test Harness")
    print("="*80)

    # Initialize recorder
    recorder = ShadowRecorder()

    print("\n1. Simulating shadow trading signals")
    print("-" * 80)

    # Simulate trading signals
    base_price = 1.0850
    signals_list = [
        (1, 0.72, base_price + 0.0001),      # BUY at 1.0851
        (0, 0.40, base_price + 0.0002),      # HOLD at 1.0852
        (-1, 0.68, base_price + 0.0000),     # SELL at 1.0850
        (1, 0.65, base_price - 0.0001),      # BUY at 1.0849
        (-1, 0.70, base_price + 0.0003),     # SELL at 1.0853
    ]

    for signal_type, confidence, price in signals_list:
        signal_record = {
            'timestamp': datetime.now().isoformat() + 'Z',
            'signal': signal_type,
            'price': price,
            'confidence': confidence,
            'features_hash': 'test_hash_123'
        }

        signal_id = recorder.record_signal(signal_record)

        # Simulate price movement 15 minutes later
        actual_price = price + np.random.randn() * 0.0002

        recorder.update_signal_accuracy(signal_id, actual_price, timeframe_minutes=15)

    print(f"Recorded {recorder.total_signals} signals")

    print("\n2. Shadow Recorder Statistics")
    print("-" * 80)
    print(recorder.get_summary())

    print("\n3. Detailed Statistics")
    print("-" * 80)
    stats = recorder.calculate_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n4. Exporting performance metrics")
    print("-" * 80)
    perf_file = recorder.export_performance_metrics()
    print(f"   Saved to: {perf_file}")

    print("\n✅ ShadowRecorder test harness completed")


if __name__ == '__main__':
    main()
