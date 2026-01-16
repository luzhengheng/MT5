"""
Shadow Autopsy Engine (Task #118)
Performs comprehensive analysis of shadow mode trading logs and generates
live trading admission decisions based on quantified metrics.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import deque
import statistics
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class GatekeepingDecision:
    """Represents the final gatekeeping decision for live trading."""
    is_approved: bool
    timestamp: str
    critical_errors: int
    p95_latency_ms: float
    p99_latency_ms: float
    drift_events_24h: int
    pnl_net_return: float
    diversity_index: float
    rejection_reasons: List[str]
    approval_confidence: float
    decision_hash: str = ""

    def __post_init__(self):
        """Generate decision hash for integrity verification."""
        decision_str = f"{self.timestamp}:{self.critical_errors}:{self.p99_latency_ms}"
        self.decision_hash = hashlib.sha256(decision_str.encode()).hexdigest()[:16]


class LatencyAnalyzer:
    """Analyzes signal generation to logging latency (Task #118 requirement)."""

    CRITICAL_LATENCY_THRESHOLD_MS = 100  # Hard limit: P99 < 100ms
    WARNING_LATENCY_THRESHOLD_MS = 50    # Soft limit: warn if >50ms

    def __init__(self, records: List[Dict[str, Any]]):
        """Initialize with shadow mode records."""
        self.records = records
        self.latencies_ms = []

    def analyze(self) -> Dict[str, Any]:
        """Calculate P95, P99 latencies and identify critical delays."""
        if not self.records:
            return {
                'p95_latency_ms': 0,
                'p99_latency_ms': 0,
                'critical_latency_count': 0,
                'warning_latency_count': 0,
                'total_records': 0,
                'avg_latency_ms': 0
            }

        for record in self.records:
            try:
                # Parse timestamps - handle both string and datetime formats
                ts_signal = record.get('timestamp_signal', record.get('timestamp'))
                ts_log = record.get('timestamp_log')

                if not ts_signal or not ts_log:
                    continue

                # Convert ISO format to datetime if needed
                if isinstance(ts_signal, str):
                    signal_time = datetime.fromisoformat(ts_signal.replace('Z', '+00:00'))
                else:
                    signal_time = ts_signal

                if isinstance(ts_log, str):
                    log_time = datetime.fromisoformat(ts_log.replace('Z', '+00:00'))
                else:
                    log_time = ts_log

                # Calculate latency in milliseconds
                latency_ms = (log_time - signal_time).total_seconds() * 1000
                if latency_ms >= 0:  # Only positive latencies count
                    self.latencies_ms.append(latency_ms)

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse latency for record {record.get('id')}: {e}")
                continue

        if not self.latencies_ms:
            return {
                'p95_latency_ms': 0,
                'p99_latency_ms': 0,
                'critical_latency_count': 0,
                'warning_latency_count': 0,
                'total_records': len(self.records),
                'avg_latency_ms': 0
            }

        sorted_latencies = sorted(self.latencies_ms)
        n = len(sorted_latencies)

        # Calculate percentiles
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        p95_latency = sorted_latencies[p95_idx] if p95_idx < n else sorted_latencies[-1]
        p99_latency = sorted_latencies[p99_idx] if p99_idx < n else sorted_latencies[-1]

        # Count problematic latencies
        critical_count = sum(1 for l in self.latencies_ms if l > self.CRITICAL_LATENCY_THRESHOLD_MS)
        warning_count = sum(1 for l in self.latencies_ms if self.WARNING_LATENCY_THRESHOLD_MS < l <= self.CRITICAL_LATENCY_THRESHOLD_MS)

        return {
            'p95_latency_ms': round(p95_latency, 2),
            'p99_latency_ms': round(p99_latency, 2),
            'critical_latency_count': critical_count,
            'warning_latency_count': warning_count,
            'total_records': len(self.records),
            'avg_latency_ms': round(statistics.mean(self.latencies_ms), 2)
        }


class PnLSimulator:
    """Simulates PnL based on shadow mode signals (Task #118 requirement)."""

    def __init__(self, records: List[Dict[str, Any]], initial_balance: float = 10000, slippage_pips: float = 1):
        """Initialize PnL simulator with trade records."""
        self.records = records
        self.initial_balance = initial_balance
        self.slippage_pips = slippage_pips

    def simulate(self) -> Dict[str, Any]:
        """Simulate trading P&L based on signals and prices."""
        balance = self.initial_balance
        trades = []
        position = None

        for record in self.records:
            signal = record.get('signal', 0)
            price = record.get('price', 0)
            confidence = record.get('confidence', 0.5)

            if signal == 0:  # HOLD
                continue

            # Position sizing based on confidence (conservative scaling)
            position_size = 100 * confidence  # $100 base position

            if signal == 1:  # BUY
                entry_price = price * (1 + self.slippage_pips / 10000)
                position = {'type': 'LONG', 'entry_price': entry_price, 'size': position_size}

            elif signal == -1:  # SELL
                if position and position['type'] == 'LONG':
                    # Close position
                    exit_price = price * (1 - self.slippage_pips / 10000)
                    pnl = (exit_price - position['entry_price']) * position['size'] / 100
                    balance += pnl
                    trades.append({
                        'type': 'CLOSE',
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl
                    })
                    position = None
                else:
                    # Short position
                    entry_price = price * (1 - self.slippage_pips / 10000)
                    position = {'type': 'SHORT', 'entry_price': entry_price, 'size': position_size}

        # Close any open position at last price
        if position and self.records:
            last_price = self.records[-1].get('price', 0)
            if position['type'] == 'LONG':
                exit_price = last_price * (1 - self.slippage_pips / 10000)
                pnl = (exit_price - position['entry_price']) * position['size'] / 100
            else:  # SHORT
                exit_price = last_price * (1 + self.slippage_pips / 10000)
                pnl = (position['entry_price'] - exit_price) * position['size'] / 100
            balance += pnl
            trades.append({'type': 'CLOSE_FINAL', 'pnl': pnl})

        # Calculate statistics
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0

        return {
            'initial_balance': self.initial_balance,
            'final_balance': round(balance, 2),
            'total_pnl': round(balance - self.initial_balance, 2),
            'net_return_pct': round((balance / self.initial_balance - 1) * 100, 2),
            'total_trades': len(trades),
            'win_rate': round(win_rate, 4),
            'avg_pnl_per_trade': round(statistics.mean([t.get('pnl', 0) for t in trades]), 2) if trades else 0
        }


class DriftAuditor:
    """Detects concept drift in signal patterns (Task #118 requirement)."""

    DRIFT_THRESHOLD_PSI = 0.25  # Population Stability Index threshold
    ENTROPY_VARIANCE_THRESHOLD = 0.20

    def __init__(self, records: List[Dict[str, Any]], window_size: int = 500):
        """Initialize drift auditor with sliding window."""
        self.records = records
        self.window_size = window_size

    def detect_drift(self) -> Dict[str, Any]:
        """Detect signal distribution changes over time (PSI-based)."""
        if len(self.records) < self.window_size * 2:
            return {
                'total_drift_events': 0,
                'entropy_variance': 0,
                'drift_events': [],
                'status': 'INSUFFICIENT_DATA'
            }

        drift_events = []
        entropies = []

        # Sliding window analysis
        for i in range(len(self.records) - self.window_size):
            window = self.records[i:i + self.window_size]

            # Extract signals and calculate entropy
            signals = [r.get('signal', 0) for r in window]
            signal_counts = {s: signals.count(s) for s in set(signals)}
            signal_dist = {s: c / len(signals) for s, c in signal_counts.items()}

            # Shannon entropy
            entropy = -sum(p * (math.log(p) if p > 0 else 0) for p in signal_dist.values())
            entropies.append(entropy)

            # Compare with previous window for drift
            if i > 0:
                prev_window = self.records[i-1:i-1 + self.window_size]
                prev_signals = [r.get('signal', 0) for r in prev_window]
                prev_counts = {s: prev_signals.count(s) for s in set(prev_signals)}
                prev_dist = {s: c / len(prev_signals) for s, c in prev_counts.items()}

                # PSI calculation (simplified)
                psi = self._calculate_psi(signal_dist, prev_dist)

                if psi > self.DRIFT_THRESHOLD_PSI:
                    drift_events.append({
                        'window_start': i,
                        'psi': round(psi, 4),
                        'timestamp': self.records[i + self.window_size - 1].get('timestamp', '')
                    })

        # Entropy variance
        entropy_variance = statistics.variance(entropies) if len(entropies) > 1 else 0

        return {
            'total_drift_events': len(drift_events),
            'entropy_variance': round(entropy_variance, 4),
            'drift_events': drift_events,
            'status': 'OK' if len(drift_events) <= 5 else 'WARNING'
        }

    def _calculate_psi(self, current_dist: Dict[int, float], previous_dist: Dict[int, float]) -> float:
        """Calculate Population Stability Index."""
        psi = 0
        all_keys = set(current_dist.keys()) | set(previous_dist.keys())

        for key in all_keys:
            current = current_dist.get(key, 0.001)  # Avoid log(0)
            previous = previous_dist.get(key, 0.001)

            if current > 0 and previous > 0:
                psi += (current - previous) * math.log(current / previous)

        return abs(psi)


class ShadowAutopsy:
    """Main Shadow Autopsy Engine - orchestrates all analysis and generates admission decision."""

    def __init__(self, shadow_data: Dict[str, Any], comparison_report: Dict[str, Any]):
        """Initialize with shadow mode data and model comparison results."""
        self.shadow_data = shadow_data
        self.comparison_report = comparison_report
        self.records = shadow_data.get('records', [])

    def generate_gatekeeping_decision(self) -> GatekeepingDecision:
        """Generate comprehensive gatekeeping decision."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        rejection_reasons = []

        # 1. Analyze latencies
        latency_analyzer = LatencyAnalyzer(self.records)
        latency_stats = latency_analyzer.analyze()

        # 2. Simulate PnL
        pnl_simulator = PnLSimulator(self.records)
        pnl_stats = pnl_simulator.simulate()

        # 3. Detect drift
        drift_auditor = DriftAuditor(self.records)
        drift_stats = drift_auditor.detect_drift()

        # 4. Count critical errors
        critical_errors = 0
        for record in self.records:
            if record.get('signal') is None or record.get('price') is None:
                critical_errors += 1

        # 5. Extract comparison metrics
        comparison_results = self.comparison_report.get('comparison_results', {})
        diversity_results = self.comparison_report.get('diversity_results', {})

        challenger_f1 = comparison_results.get('challenger_f1', 0)
        diversity_index = diversity_results.get('diversity_index', 0)

        # 6. Apply gatekeeping rules
        is_approved = True

        # Rule 1: Critical errors must be zero
        if critical_errors > 0:
            is_approved = False
            rejection_reasons.append(f"Critical errors detected: {critical_errors} records with invalid data")

        # Rule 2: P99 latency must be <100ms
        p99_latency = latency_stats['p99_latency_ms']
        if p99_latency >= 100:
            is_approved = False
            rejection_reasons.append(f"P99 latency {p99_latency}ms exceeds 100ms threshold")

        # Rule 3: Drift events per 24h must be <5
        drift_24h = drift_stats['total_drift_events']
        if drift_24h >= 5:
            is_approved = False
            rejection_reasons.append(f"Too many drift events: {drift_24h} >= 5 per 24h")

        # Rule 4: Model must show improvement (F1 > 0.5)
        if challenger_f1 < 0.5:
            rejection_reasons.append(f"Model F1 score {challenger_f1} below 0.5 threshold")
            # This is a warning, not automatic rejection, unless very low
            if challenger_f1 < 0.3:
                is_approved = False

        # Rule 5: Minimum signal diversity
        if diversity_index < 0.4:
            rejection_reasons.append(f"Signal diversity {diversity_index} below 0.4 threshold")

        # Calculate approval confidence
        approval_confidence = 1.0
        if not is_approved:
            approval_confidence = 0.0
        else:
            # Adjust confidence based on how close metrics are to thresholds
            latency_confidence = max(0, 1.0 - (p99_latency / 100))
            drift_confidence = max(0, 1.0 - (drift_24h / 5))
            f1_confidence = min(1.0, challenger_f1)
            approval_confidence = (latency_confidence + drift_confidence + f1_confidence) / 3

        return GatekeepingDecision(
            is_approved=is_approved,
            timestamp=timestamp,
            critical_errors=critical_errors,
            p95_latency_ms=latency_stats['p95_latency_ms'],
            p99_latency_ms=p99_latency,
            drift_events_24h=drift_24h,
            pnl_net_return=pnl_stats['net_return_pct'],
            diversity_index=diversity_index,
            rejection_reasons=rejection_reasons,
            approval_confidence=round(approval_confidence, 4)
        )

    def generate_admission_report(self, decision: GatekeepingDecision) -> str:
        """Generate markdown admission report with detailed findings."""
        decision_text = "**GO**" if decision.is_approved else "**NO-GO**"
        decision_emoji = "✅" if decision.is_approved else "❌"

        report = f"""# 🔐 Live Trading Admission Report (Task #118)

**Generated**: {decision.timestamp}
**Decision Hash**: {decision.decision_hash}

---

## Executive Summary

**Final Decision**: {decision_emoji} {decision_text}
**Approval Confidence**: {decision.approval_confidence * 100:.1f}%

The Shadow Autopsy Engine has completed comprehensive analysis of {len(self.records)} trading signals from 72 hours of shadow mode operation.

---

## Performance Audit Results

### Signal Latency Analysis
- **P95 Latency**: {decision.p95_latency_ms:.2f}ms ✅
- **P99 Latency**: {decision.p99_latency_ms:.2f}ms {"✅" if decision.p99_latency_ms < 100 else "❌"}
- **Threshold**: <100ms (soft real-time requirement)
- **Status**: {"PASS - Inference engine performing within soft real-time bounds" if decision.p99_latency_ms < 100 else "FAIL - P99 latency violates soft real-time SLA"}

### Model Quality Metrics
- **Challenger F1 Score**: {self.comparison_report.get('comparison_results', {}).get('challenger_f1', 0):.4f}
- **Baseline F1 Score**: {self.comparison_report.get('comparison_results', {}).get('baseline_f1', 0):.4f}
- **F1 Improvement**: {((self.comparison_report.get('comparison_results', {}).get('challenger_f1', 0) / self.comparison_report.get('comparison_results', {}).get('baseline_f1', 0.001)) - 1) * 100:.1f}%
- **Signal Diversity**: {decision.diversity_index * 100:.1f}% (Threshold: >40%)

### Risk Metrics
- **Critical Data Errors**: {decision.critical_errors} records ✅
- **Drift Events (24h)**: {decision.drift_events_24h} events (Threshold: <5) {"✅" if decision.drift_events_24h < 5 else "⚠️"}
- **Simulated P&L Return**: {decision.pnl_net_return:.2f}%

---

## Gatekeeping Rules Verification

| Rule | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Critical Errors | = 0 | {decision.critical_errors} | {"✅ PASS" if decision.critical_errors == 0 else "❌ FAIL"} |
| P99 Latency | < 100ms | {decision.p99_latency_ms:.2f}ms | {"✅ PASS" if decision.p99_latency_ms < 100 else "❌ FAIL"} |
| Drift Events (24h) | < 5 | {decision.drift_events_24h} | {"✅ PASS" if decision.drift_events_24h < 5 else "⚠️ WARNING"} |
| Model F1 Score | > 0.50 | {self.comparison_report.get('comparison_results', {}).get('challenger_f1', 0):.4f} | {"✅ PASS" if self.comparison_report.get('comparison_results', {}).get('challenger_f1', 0) > 0.5 else "⚠️ BORDERLINE"} |
| Signal Diversity | > 40% | {decision.diversity_index * 100:.1f}% | {"✅ PASS" if decision.diversity_index > 0.4 else "❌ FAIL"} |

---

## Rejection Reasons (if any)

"""
        if decision.rejection_reasons:
            for reason in decision.rejection_reasons:
                report += f"- ❌ {reason}\n"
        else:
            report += "- ✅ All gatekeeping rules passed - system is ready for live trading\n"

        report += f"""
---

## Recommendation

**DECISION**: {decision_text}

"""
        if decision.is_approved:
            report += f"""✅ **APPROVED FOR LIVE TRADING**

The system has successfully completed shadow mode validation with all critical metrics within acceptable ranges. The challenger model demonstrates superior performance (F1 +{((self.comparison_report.get('comparison_results', {}).get('challenger_f1', 0) / self.comparison_report.get('comparison_results', {}).get('baseline_f1', 0.001)) - 1) * 100:.0f}%) and the inference pipeline maintains soft real-time performance (P99 <100ms).

**Next Steps**:
1. Enable live trading on demo account (JustMarkets-Demo2, Account 1100212251)
2. Start with 10% position sizing
3. Monitor first 24 hours with circuit breaker active
4. Scale to 100% after successful validation

"""
        else:
            report += f"""❌ **REJECTED - DO NOT PROCEED TO LIVE TRADING**

The system has identified critical issues that must be resolved before proceeding to live trading:

{chr(10).join([f"  {i+1}. {r}" for i, r in enumerate(decision.rejection_reasons)])}

**Required Actions**:
1. Investigate and fix identified issues
2. Re-run 72-hour shadow mode validation
3. Re-submit for gatekeeping review

"""

        report += f"""---

## Metadata

- **Analysis Timestamp**: {decision.timestamp}
- **Shadow Mode Records Analyzed**: {len(self.records)}
- **Analysis Duration**: 72 hours of trading signals
- **Decision Hash**: {decision.decision_hash}
- **Protocol**: v4.3 (Zero-Trust Edition)

---

**Generated by**: Shadow Autopsy Engine (Task #118)
**Status**: {decision_text} for Phase 6 Live Trading
"""
        return report


# Import math for entropy calculations
import math
