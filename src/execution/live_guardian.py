"""
Live Guardian Module (Task #119)
Runtime monitoring and safety guardrails for Phase 6 live trading.
Integrates DriftAuditor, LatencyAnalyzer, and real-time risk monitoring.
"""

import logging
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import deque
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.shadow_autopsy import DriftAuditor, LatencyAnalyzer
from risk.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


@dataclass
class RuntimeGuardMetrics:
    """Metrics collected by Live Guardian during runtime"""
    timestamp: str
    latency_spike_count: int = 0
    drift_events: int = 0
    critical_errors: int = 0
    p99_latency_ms: float = 0.0
    should_halt: bool = False
    halt_reason: Optional[str] = None
    system_health: str = "HEALTHY"  # HEALTHY, WARNING, CRITICAL


class LatencySpikeDetector:
    """Detects and tracks latency spikes >100ms"""

    CRITICAL_THRESHOLD_MS = 100
    WARNING_THRESHOLD_MS = 50
    WINDOW_SIZE = 100

    def __init__(self):
        self.latency_history = deque(maxlen=self.WINDOW_SIZE)
        self.spike_count = 0
        self.warning_count = 0

    def record_latency(self, latency_ms: float) -> bool:
        """
        Record a latency sample and detect spikes.
        Returns True if spike detected.
        """
        self.latency_history.append(latency_ms)

        if latency_ms > self.CRITICAL_THRESHOLD_MS:
            self.spike_count += 1
            logger.warning(
                f"⚠️ LATENCY SPIKE DETECTED: {latency_ms:.2f}ms "
                f"(threshold: {self.CRITICAL_THRESHOLD_MS}ms)"
            )
            return True

        if latency_ms > self.WARNING_THRESHOLD_MS:
            self.warning_count += 1
            logger.debug(
                f"📊 Latency elevated: {latency_ms:.2f}ms "
                f"(warning threshold: {self.WARNING_THRESHOLD_MS}ms)"
            )

        return False

    def get_p99_latency(self) -> float:
        """Calculate P99 latency from history"""
        if not self.latency_history:
            return 0.0

        sorted_latencies = sorted(list(self.latency_history))
        p99_index = int(len(sorted_latencies) * 0.99)
        return float(sorted_latencies[min(p99_index, len(sorted_latencies) - 1)])

    def get_stats(self) -> Dict[str, Any]:
        """Get latency statistics"""
        if not self.latency_history:
            return {
                "total_samples": 0,
                "avg_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "spike_count": 0,
                "warning_count": 0
            }

        latencies = list(self.latency_history)
        return {
            "total_samples": len(latencies),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "p99_latency_ms": self.get_p99_latency(),
            "max_latency_ms": max(latencies),
            "spike_count": self.spike_count,
            "warning_count": self.warning_count
        }


class DriftMonitor:
    """Monitors concept drift every 1 hour using PSI-based detection"""

    CHECK_INTERVAL_SECONDS = 3600  # 1 hour
    PSI_THRESHOLD = 0.25
    MAX_DRIFT_EVENTS_24H = 5

    def __init__(self):
        self.last_check_time = datetime.utcnow()
        self.drift_events_24h = deque(maxlen=24)  # One per hour max
        self.drift_history: List[Dict[str, Any]] = []

    def should_check_drift(self) -> bool:
        """Check if 1 hour has passed since last check"""
        elapsed = (datetime.utcnow() - self.last_check_time).total_seconds()
        return elapsed >= self.CHECK_INTERVAL_SECONDS

    def record_drift_check(self, psi_value: float, drift_detected: bool):
        """Record a drift check result"""
        check_time = datetime.utcnow()
        self.last_check_time = check_time

        if drift_detected:
            self.drift_events_24h.append(check_time)
            self.drift_history.append({
                "timestamp": check_time.isoformat(),
                "psi_value": psi_value,
                "threshold": self.PSI_THRESHOLD,
                "triggered": True
            })
            logger.warning(
                f"🚨 DRIFT DETECTED: PSI={psi_value:.4f} "
                f"(threshold: {self.PSI_THRESHOLD}) | "
                f"Events in 24h: {len(self.drift_events_24h)}/{self.MAX_DRIFT_EVENTS_24H}"
            )
            return True
        else:
            self.drift_history.append({
                "timestamp": check_time.isoformat(),
                "psi_value": psi_value,
                "threshold": self.PSI_THRESHOLD,
                "triggered": False
            })
            logger.debug(f"✅ Drift check passed: PSI={psi_value:.4f}")
            return False

    def is_drift_critical(self) -> bool:
        """Check if drift events exceeded 24h threshold"""
        return len(self.drift_events_24h) >= self.MAX_DRIFT_EVENTS_24H

    def get_drift_status(self) -> Dict[str, Any]:
        """Get current drift monitoring status"""
        return {
            "events_24h": len(self.drift_events_24h),
            "max_threshold": self.MAX_DRIFT_EVENTS_24H,
            "is_critical": self.is_drift_critical(),
            "last_check": self.last_check_time.isoformat(),
            "history": self.drift_history[-5:]  # Last 5 events
        }


class LiveGuardian:
    """Main guardian module for runtime safety enforcement"""

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.latency_detector = LatencySpikeDetector()
        self.drift_monitor = DriftMonitor()
        self.critical_error_count = 0
        self.startup_time = datetime.utcnow()
        self.metrics_history: List[RuntimeGuardMetrics] = []

        logger.info("🛡️ Live Guardian initialized (Task #119)")

    def check_latency_spike(self, latency_ms: float) -> bool:
        """
        Check if latency exceeds 100ms threshold.
        Returns True if spike detected.
        """
        return self.latency_detector.record_latency(latency_ms)

    def check_drift(self, psi_value: Optional[float] = None) -> bool:
        """
        Check for concept drift using PSI metric.
        Returns True if drift detected and critical.
        """
        if not self.drift_monitor.should_check_drift():
            return False

        drift_detected = psi_value is not None and psi_value > self.drift_monitor.PSI_THRESHOLD
        self.drift_monitor.record_drift_check(psi_value or 0.0, drift_detected)

        if self.drift_monitor.is_drift_critical():
            logger.critical(
                "🛑 DRIFT CRITICAL: Exceeded maximum events in 24h. System halt triggered."
            )
            return True

        return False

    def record_error(self, error_type: str, details: str):
        """Record a critical error"""
        self.critical_error_count += 1
        logger.error(f"❌ CRITICAL ERROR [{error_type}]: {details}")

    def should_halt(self) -> bool:
        """
        Determine if system should halt based on all monitored metrics.
        Returns True if halt conditions met.
        """
        # Check circuit breaker status
        if not self.circuit_breaker.is_safe():
            logger.critical(
                "🛑 HALT: Circuit breaker is ENGAGED. System safety compromised."
            )
            return True

        # Check latency spikes (>3 spikes in recent window)
        latency_stats = self.latency_detector.get_stats()
        if latency_stats.get("spike_count", 0) > 3:
            logger.critical(
                f"🛑 HALT: Excessive latency spikes detected "
                f"({latency_stats['spike_count']} spikes)"
            )
            return True

        # Check critical errors
        if self.critical_error_count > 5:
            logger.critical(
                f"🛑 HALT: Too many critical errors ({self.critical_error_count})"
            )
            return True

        # Check drift criticality
        if self.drift_monitor.is_drift_critical():
            logger.critical("🛑 HALT: Concept drift exceeded safe threshold")
            return True

        return False

    def get_system_health(self) -> str:
        """
        Assess overall system health.
        Returns: HEALTHY, WARNING, or CRITICAL
        """
        latency_stats = self.latency_detector.get_stats()
        drift_status = self.drift_monitor.get_drift_status()

        if self.should_halt():
            return "CRITICAL"

        # Check for warning conditions
        if (latency_stats.get("spike_count", 0) > 1 or
            drift_status["events_24h"] > 2 or
            self.critical_error_count > 2):
            return "WARNING"

        return "HEALTHY"

    def get_status(self) -> RuntimeGuardMetrics:
        """Get current guardian status snapshot"""
        latency_stats = self.latency_detector.get_stats()
        drift_status = self.drift_monitor.get_drift_status()

        metrics = RuntimeGuardMetrics(
            timestamp=datetime.utcnow().isoformat(),
            latency_spike_count=latency_stats.get("spike_count", 0),
            drift_events=drift_status["events_24h"],
            critical_errors=self.critical_error_count,
            p99_latency_ms=latency_stats.get("p99_latency_ms", 0.0),
            should_halt=self.should_halt(),
            halt_reason=None,
            system_health=self.get_system_health()
        )

        if metrics.should_halt:
            if not self.circuit_breaker.is_safe():
                metrics.halt_reason = "Circuit breaker engaged"
            elif latency_stats.get("spike_count", 0) > 3:
                metrics.halt_reason = "Excessive latency spikes"
            elif self.critical_error_count > 5:
                metrics.halt_reason = f"Too many errors ({self.critical_error_count})"
            elif self.drift_monitor.is_drift_critical():
                metrics.halt_reason = "Concept drift exceeded threshold"

        self.metrics_history.append(metrics)
        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
            "system_health": self.get_system_health(),
            "should_halt": self.should_halt(),
            "latency_stats": self.latency_detector.get_stats(),
            "drift_status": self.drift_monitor.get_drift_status(),
            "critical_errors": self.critical_error_count,
            "recent_metrics": [asdict(m) for m in self.metrics_history[-10:]]
        }


def initialize_guardian() -> LiveGuardian:
    """Factory function to initialize guardian with circuit breaker"""
    circuit_breaker = CircuitBreaker()
    return LiveGuardian(circuit_breaker=circuit_breaker)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Test the guardian
    guardian = initialize_guardian()

    print("\n✅ Live Guardian initialized successfully")
    print(f"📊 System Health: {guardian.get_system_health()}")
    print(f"🛡️  System Safe: {not guardian.should_halt()}\n")
