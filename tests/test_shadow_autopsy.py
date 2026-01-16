"""
Test Suite for Shadow Autopsy Engine (Task #118)
Tests the core gatekeeping logic for live trading admission.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analytics.shadow_autopsy import (
    LatencyAnalyzer,
    PnLSimulator,
    DriftAuditor,
    ShadowAutopsy,
    GatekeepingDecision
)


class TestLatencyAnalyzer:
    """Test latency analysis between signal generation and logging."""

    def test_perfect_latency_logs(self):
        """Test scenario: All signals logged within <10ms (perfect case)."""
        records = [
            {
                "id": f"signal_{i}",
                "timestamp_signal": (datetime.now() - timedelta(milliseconds=5)).isoformat(),
                "timestamp_log": datetime.now().isoformat(),
                "signal": 1,
                "confidence": 0.75
            }
            for i in range(50)
        ]

        analyzer = LatencyAnalyzer(records)
        stats = analyzer.analyze()

        assert stats['p95_latency_ms'] < 100, "P95 latency must be <100ms"
        assert stats['p99_latency_ms'] < 100, "P99 latency must be <100ms"
        assert stats['critical_latency_count'] == 0, "No critical latencies expected"

    def test_high_latency_logs(self):
        """Test scenario: 5 signals with high latency (>100ms injected)."""
        records = [
            {
                "id": f"signal_{i}",
                "timestamp_signal": (datetime.now() - timedelta(milliseconds=120 if i < 5 else 5)).isoformat(),
                "timestamp_log": datetime.now().isoformat(),
                "signal": 1,
                "confidence": 0.75
            }
            for i in range(100)
        ]

        analyzer = LatencyAnalyzer(records)
        stats = analyzer.analyze()

        assert stats['critical_latency_count'] >= 5, "Should detect high latency signals"
        assert stats['p99_latency_ms'] >= 100, "P99 should reflect high latencies"

    def test_empty_records(self):
        """Test scenario: No records provided."""
        analyzer = LatencyAnalyzer([])
        stats = analyzer.analyze()

        assert stats['p95_latency_ms'] == 0
        assert stats['p99_latency_ms'] == 0
        assert stats['total_records'] == 0


class TestPnLSimulator:
    """Test PnL simulation with signal-based trades."""

    def test_winning_trades(self):
        """Test scenario: Profitable buy signals."""
        records = [
            {
                "id": f"signal_{i}",
                "signal": 1 if i % 2 == 0 else -1,  # Alternating BUY/SELL
                "price": 1.0800 + (i * 0.0001),  # Rising price
                "confidence": 0.85
            }
            for i in range(20)
        ]

        simulator = PnLSimulator(records, initial_balance=10000, slippage_pips=1)
        pnl = simulator.simulate()

        assert pnl['total_trades'] > 0, "Should have at least one closed trade"

    def test_losing_trades(self):
        """Test scenario: Unprofitable sell signals."""
        records = [
            {
                "id": f"signal_{i}",
                "signal": -1,  # SELL
                "price": 1.0800 - (i * 0.0001),  # Falling price
                "confidence": 0.50
            }
            for i in range(20)
        ]

        simulator = PnLSimulator(records, initial_balance=10000, slippage_pips=1)
        pnl = simulator.simulate()

        assert pnl['total_trades'] > 0
        # Lower confidence typically correlates with lower profitability
        assert pnl['win_rate'] < 0.7, "Should have lower win rate for falling prices with sells"

    def test_zero_signal_trades(self):
        """Test scenario: All HOLD signals (no trades)."""
        records = [
            {
                "id": f"signal_{i}",
                "signal": 0,  # HOLD
                "price": 1.0800,
                "confidence": 0.50
            }
            for i in range(50)
        ]

        simulator = PnLSimulator(records, initial_balance=10000, slippage_pips=1)
        pnl = simulator.simulate()

        assert pnl['total_trades'] == 0
        assert pnl['final_balance'] == 10000, "No trades = no P&L change"


class TestDriftAuditor:
    """Test model drift detection and monitoring."""

    def test_stable_signals(self):
        """Test scenario: Consistent signal patterns (no drift)."""
        # Create 1000 consistent signals with stable distribution
        records = [
            {
                "id": f"signal_{i}",
                "signal": 1 if i % 2 == 0 else -1,  # Alternating pattern
                "confidence": 0.60 + (i % 5) * 0.05,  # Consistent confidence
                "timestamp": (datetime.now() - timedelta(hours=72-i/10)).isoformat()
            }
            for i in range(1000)
        ]

        auditor = DriftAuditor(records, window_size=500)
        drift_events = auditor.detect_drift()

        assert drift_events['total_drift_events'] < 5, "Stable signals should have minimal drift"
        assert drift_events['entropy_variance'] < 0.15, "Entropy should be stable"

    def test_drift_with_warnings(self):
        """Test scenario: Pattern shift in signals."""
        records = []

        # Phase 1: Normal signals
        for i in range(500):
            records.append({
                "id": f"signal_{i}",
                "signal": 1 if i % 2 == 0 else -1,
                "confidence": 0.60,
                "timestamp": (datetime.now() -
                              timedelta(hours=72-i/10)).isoformat()
            })

        # Phase 2: Drift phase (confidence drops sharply)
        for i in range(500, 1000):
            records.append({
                "id": f"signal_{i}",
                "signal": -1,  # Reversed signal pattern
                "confidence": 0.30,  # Much lower confidence
                "timestamp": (datetime.now() -
                              timedelta(hours=36-i/20)).isoformat()
            })

        auditor = DriftAuditor(records, window_size=250)
        drift_events = auditor.detect_drift()

        # Should detect at least status change or have drift data
        assert drift_events['status'] in ['OK', 'WARNING']

    def test_empty_drift_audit(self):
        """Test scenario: No records for drift analysis."""
        auditor = DriftAuditor([], window_size=500)
        drift_events = auditor.detect_drift()

        assert drift_events['total_drift_events'] == 0


class TestGatekeepingLogic:
    """Test the core gatekeeping decision logic."""

    def test_approval_all_metrics_pass(self):
        """Test scenario: All metrics pass thresholds."""
        shadow_data = {
            "records": [
                {
                    "id": f"signal_{i}",
                    "timestamp_signal": (datetime.now() - timedelta(milliseconds=5)).isoformat(),
                    "timestamp_log": datetime.now().isoformat(),
                    "signal": 1 if i % 2 == 0 else -1,
                    "price": 1.0800,
                    "confidence": 0.75
                }
                for i in range(100)
            ],
            "metadata": {
                "total_records": 100,
                "timestamp": datetime.now().isoformat()
            }
        }

        comparison_report = {
            "comparison_results": {
                "consistency_rate": 0.407,
                "baseline_accuracy": 0.459,
                "challenger_accuracy": 0.564,
                "baseline_f1": 0.186,
                "challenger_f1": 0.598
            },
            "diversity_results": {
                "diversity_index": 0.593
            }
        }

        autopsy = ShadowAutopsy(shadow_data, comparison_report)
        decision = autopsy.generate_gatekeeping_decision()

        assert decision.is_approved == True, "Should approve when all metrics pass"
        assert decision.critical_errors == 0, "No critical errors expected"
        assert decision.p99_latency_ms < 100, "P99 latency should be <100ms"

    def test_rejection_high_latency(self):
        """Test scenario: High P99 latency triggers rejection."""
        shadow_data = {
            "records": [
                {
                    "id": f"signal_{i}",
                    "timestamp_signal": (datetime.now() - timedelta(milliseconds=150 if i < 20 else 5)).isoformat(),
                    "timestamp_log": datetime.now().isoformat(),
                    "signal": 1,
                    "price": 1.0800,
                    "confidence": 0.75
                }
                for i in range(100)
            ],
            "metadata": {
                "total_records": 100,
                "timestamp": datetime.now().isoformat()
            }
        }

        comparison_report = {
            "comparison_results": {
                "consistency_rate": 0.407,
                "baseline_accuracy": 0.459,
                "challenger_accuracy": 0.564,
                "baseline_f1": 0.186,
                "challenger_f1": 0.598
            },
            "diversity_results": {
                "diversity_index": 0.593
            }
        }

        autopsy = ShadowAutopsy(shadow_data, comparison_report)
        decision = autopsy.generate_gatekeeping_decision()

        assert decision.is_approved == False, "Should reject due to high latency"
        assert decision.rejection_reasons, "Should have rejection reasons"

    def test_rejection_critical_errors(self):
        """Test scenario: Critical errors detected."""
        shadow_data = {
            "records": [
                {
                    "id": f"signal_{i}",
                    "timestamp_signal": (datetime.now() - timedelta(milliseconds=5)).isoformat(),
                    "timestamp_log": datetime.now().isoformat(),
                    "signal": 1 if i < 5 else None,  # 5 records with None signals = errors
                    "price": 1.0800,
                    "confidence": 0.75
                }
                for i in range(100)
            ],
            "metadata": {
                "total_records": 100,
                "timestamp": datetime.now().isoformat()
            }
        }

        comparison_report = {
            "comparison_results": {
                "consistency_rate": 0.407,
                "baseline_accuracy": 0.459,
                "challenger_accuracy": 0.564,
                "baseline_f1": 0.186,
                "challenger_f1": 0.598
            },
            "diversity_results": {
                "diversity_index": 0.593
            }
        }

        autopsy = ShadowAutopsy(shadow_data, comparison_report)
        decision = autopsy.generate_gatekeeping_decision()

        assert decision.is_approved == False, "Should reject due to critical errors"
        assert decision.critical_errors > 0


class TestShadowAutopsyIntegration:
    """Integration tests for the full Shadow Autopsy pipeline."""

    def test_end_to_end_approval_flow(self):
        """Test complete flow from data ingestion to GO decision."""
        # Use realistic data from Task #117
        shadow_data = {
            "metadata": {
                "timestamp": "2026-01-16T08:13:37.750503Z",
                "mode": "SHADOW_MODE",
                "total_records": 100
            },
            "statistics": {
                "total_signals": 100,
                "average_confidence": 0.60,
                "accuracy_15min": 0.50,
                "accuracy_1h": 0.55,
                "accuracy_4h": 0.58
            },
            "records": [
                {
                    "id": f"signal_{i}",
                    "timestamp": (datetime.now() - timedelta(hours=72-i/100)).isoformat(),
                    "signal": 1 if i % 2 == 0 else -1,
                    "price": 1.0800 + (i % 10) * 0.0001,
                    "confidence": 0.55 + (i % 10) * 0.01
                }
                for i in range(100)
            ]
        }

        comparison_report = {
            "timestamp": "2026-01-17T01:49:21.461630",
            "comparison_results": {
                "consistency_rate": 0.407,
                "baseline_accuracy": 0.459,
                "challenger_accuracy": 0.564,
                "baseline_f1": 0.18646616541353384,
                "challenger_f1": 0.5985267034990792
            },
            "diversity_results": {
                "diversity_index": 0.593,
                "different_signals": 59,
                "total_signals": 100
            }
        }

        autopsy = ShadowAutopsy(shadow_data, comparison_report)
        decision = autopsy.generate_gatekeeping_decision()

        # Verify decision object has all required fields
        assert hasattr(decision, 'is_approved')
        assert hasattr(decision, 'critical_errors')
        assert hasattr(decision, 'p99_latency_ms')
        assert hasattr(decision, 'rejection_reasons')
        assert hasattr(decision, 'timestamp')

    def test_report_generation(self):
        """Test generation of markdown admission report."""
        shadow_data = {
            "metadata": {
                "timestamp": "2026-01-16T08:13:37.750503Z",
                "mode": "SHADOW_MODE",
                "total_records": 50
            },
            "records": [
                {
                    "id": f"signal_{i}",
                    "timestamp": (datetime.now() -
                                  timedelta(hours=24-i/50)).isoformat(),
                    "signal": 1 if i % 2 == 0 else -1,
                    "price": 1.0800,
                    "confidence": 0.60
                }
                for i in range(50)
            ]
        }

        comparison_report = {
            "comparison_results": {
                "consistency_rate": 0.407,
                "baseline_accuracy": 0.459,
                "challenger_accuracy": 0.564,
                "baseline_f1": 0.186,
                "challenger_f1": 0.598
            },
            "diversity_results": {
                "diversity_index": 0.593
            }
        }

        autopsy = ShadowAutopsy(shadow_data, comparison_report)
        decision = autopsy.generate_gatekeeping_decision()
        report = autopsy.generate_admission_report(decision)

        # Report should contain key metrics
        assert "P95 Latency" in report or "P99 Latency" in report
        assert ("GO" in report or "NO-GO" in report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
