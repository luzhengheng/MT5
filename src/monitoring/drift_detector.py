#!/usr/bin/env python3
"""
Task #115: Drift Detector Module

Implements concept drift detection using PSI (Population Stability Index)
and KL divergence to monitor feature distribution shifts in real-time.

Protocol: v4.3 (Zero-Trust Edition)
"""

import logging
import numpy as np
from collections import deque
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detects concept drift by monitoring feature distribution shifts.

    Uses Population Stability Index (PSI) and KL divergence to compare
    current feature distributions against training data distributions.

    Key thresholds:
    - PSI < 0.10: No significant drift
    - 0.10 <= PSI < 0.25: Small drift detected
    - PSI >= 0.25: Significant drift (trigger alert)
    """

    def __init__(self,
                 reference_features: np.ndarray,
                 n_bins: int = 10,
                 window_size: int = 500,
                 drift_threshold: float = 0.25,
                 alert_threshold: float = 0.20):
        """
        Initialize drift detector.

        Args:
            reference_features: Training data features (N, D) for establishing baseline
            n_bins: Number of bins for histogram (default 10)
            window_size: Sliding window size for real-time calculation
            drift_threshold: PSI threshold to trigger stop_inference alert (0.25)
            alert_threshold: PSI threshold for warning (0.20)
        """
        self.reference_features = reference_features
        self.n_bins = n_bins
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.alert_threshold = alert_threshold

        # Calculate reference (training) distribution statistics
        self.reference_histograms = {}  # Per-feature histograms
        self.reference_means = np.mean(reference_features, axis=0)
        self.reference_stds = np.std(reference_features, axis=0)

        self._compute_reference_histograms()

        # Sliding window buffer for real-time features
        self.feature_window = deque(maxlen=window_size)

        # Statistics tracking
        self.drift_events = 0
        self.max_psi = 0.0
        self.last_psi = 0.0
        self.last_check_time = None

        logger.info(
            f"DriftDetector initialized: "
            f"reference={reference_features.shape}, "
            f"n_bins={n_bins}, "
            f"drift_threshold={drift_threshold}"
        )

    def _compute_reference_histograms(self):
        """Compute histograms for each feature in reference data."""
        n_features = self.reference_features.shape[1]

        for feat_idx in range(n_features):
            feature_data = self.reference_features[:, feat_idx]
            hist, _ = np.histogram(feature_data, bins=self.n_bins, density=True)

            # Normalize to probabilities (add small epsilon to avoid division by zero)
            hist = hist / (np.sum(hist) + 1e-10)
            self.reference_histograms[feat_idx] = hist

        logger.debug(f"Computed {len(self.reference_histograms)} reference histograms")

    def get_histogram(self, features: np.ndarray, feature_idx: int = 0) -> np.ndarray:
        """
        Compute histogram for a feature.

        Args:
            features: Feature data (N,) or (N, D)
            feature_idx: Feature index if 2D input

        Returns:
            Normalized histogram array
        """
        if features.ndim == 1:
            data = features
        else:
            data = features[:, feature_idx]

        # Use reference bins for consistency
        reference_data = self.reference_features[:, feature_idx]
        ref_min, ref_max = np.min(reference_data), np.max(reference_data)

        # Create bins
        bins = np.linspace(ref_min, ref_max, self.n_bins + 1)

        hist, _ = np.histogram(data, bins=bins, density=True)

        # Normalize to probabilities
        hist = hist / (np.sum(hist) + 1e-10)

        return hist

    def calculate_psi(self, current_features: np.ndarray, feature_idx: int = 0) -> float:
        """
        Calculate Population Stability Index (PSI) for a feature.

        PSI = Σ (current_pct - reference_pct) * ln(current_pct / reference_pct)

        Interpretation:
        - PSI < 0.10: No significant drift
        - 0.10 ≤ PSI < 0.25: Small drift
        - PSI ≥ 0.25: Significant drift

        Args:
            current_features: Current feature data (N,) or (N, D)
            feature_idx: Feature index if 2D

        Returns:
            PSI value (float)
        """
        if current_features.ndim == 1 or (current_features.ndim == 2 and current_features.shape[1] == 1):
            if current_features.ndim == 2:
                current_features = current_features[:, 0]
            reference_hist = self.reference_histograms[0]
        else:
            reference_hist = self.reference_histograms.get(
                feature_idx,
                self.reference_histograms[0]
            )

        # Get current histogram
        current_hist = self.get_histogram(current_features, feature_idx)

        # Calculate PSI
        psi = 0.0
        for i in range(len(reference_hist)):
            ref_pct = reference_hist[i] + 1e-10  # Avoid log(0)
            curr_pct = current_hist[i] + 1e-10

            psi += (curr_pct - ref_pct) * np.log(curr_pct / ref_pct)

        return psi

    def calculate_kl_divergence(self, current_features: np.ndarray, feature_idx: int = 0) -> float:
        """
        Calculate Kullback-Leibler (KL) divergence.

        KL(P||Q) = Σ P(x) * ln(P(x) / Q(x))

        Args:
            current_features: Current feature data
            feature_idx: Feature index if multi-dimensional

        Returns:
            KL divergence value
        """
        if current_features.ndim == 1 or (current_features.ndim == 2 and current_features.shape[1] == 1):
            if current_features.ndim == 2:
                current_features = current_features[:, 0]
            reference_hist = self.reference_histograms[0]
        else:
            reference_hist = self.reference_histograms.get(
                feature_idx,
                self.reference_histograms[0]
            )

        current_hist = self.get_histogram(current_features, feature_idx)

        # Calculate KL divergence (reference is P, current is Q)
        kl = 0.0
        for i in range(len(reference_hist)):
            ref_pct = reference_hist[i] + 1e-10
            curr_pct = current_hist[i] + 1e-10

            kl += ref_pct * np.log(ref_pct / curr_pct)

        return kl

    def update_and_calculate_psi(self, new_features: np.ndarray) -> float:
        """
        Update sliding window with new features and calculate PSI.

        Args:
            new_features: New feature batch (N, D) or (N,)

        Returns:
            PSI value for windowed data
        """
        # Add to window
        if new_features.ndim == 1:
            new_features = new_features.reshape(-1, 1)

        for row in new_features:
            self.feature_window.append(row)

        # Calculate PSI on window if enough data
        if len(self.feature_window) > 50:
            window_array = np.array(list(self.feature_window))
            psi = self.calculate_psi(window_array[:, 0])
            self.last_psi = psi
            self.max_psi = max(self.max_psi, psi)

            return psi

        return 0.0

    def is_drifted(self, features: np.ndarray, threshold: Optional[float] = None) -> bool:
        """
        Check if features indicate drift based on threshold.

        Args:
            features: Feature data
            threshold: PSI threshold (use default if None)

        Returns:
            True if drift detected
        """
        if threshold is None:
            threshold = self.drift_threshold

        psi = self.calculate_psi(features)

        if psi >= threshold:
            self.drift_events += 1
            logger.warning(
                f"[DRIFT_ALERT] PSI={psi:.4f} exceeds threshold {threshold}"
            )
            return True

        return False

    def check_alert_conditions(self, features: np.ndarray) -> Dict:
        """
        Check drift status and return alert information.

        Args:
            features: Current feature batch

        Returns:
            Dictionary with drift status and details
        """
        self.last_check_time = datetime.now()

        psi = self.calculate_psi(features)
        kl = self.calculate_kl_divergence(features)

        self.last_psi = psi
        self.max_psi = max(self.max_psi, psi)

        status = {
            'timestamp': self.last_check_time.isoformat(),
            'psi': psi,
            'kl_divergence': kl,
            'drift_detected': False,
            'alert_level': 'GREEN'  # GREEN, YELLOW, RED
        }

        if psi >= self.drift_threshold:
            status['drift_detected'] = True
            status['alert_level'] = 'RED'
            self.drift_events += 1

            logger.error(
                f"[DRIFT_GUARD] CRITICAL: PSI={psi:.4f} >= threshold {self.drift_threshold}"
            )

        elif psi >= self.alert_threshold:
            status['alert_level'] = 'YELLOW'

            logger.warning(
                f"[DRIFT_GUARD] WARNING: PSI={psi:.4f} >= alert threshold {self.alert_threshold}"
            )
        else:
            logger.info(
                f"[DRIFT_GUARD] Feature distribution OK: PSI={psi:.4f}"
            )

        return status

    def get_statistics(self) -> Dict:
        """Get drift detector statistics."""
        return {
            'drift_events': self.drift_events,
            'max_psi': self.max_psi,
            'last_psi': self.last_psi,
            'drift_threshold': self.drift_threshold,
            'alert_threshold': self.alert_threshold,
            'window_size': len(self.feature_window),
            'n_bins': self.n_bins
        }

    def reset(self):
        """Reset detector state."""
        self.feature_window.clear()
        self.drift_events = 0
        self.max_psi = 0.0
        self.last_psi = 0.0
        logger.info("DriftDetector reset")


def main():
    """Test harness for DriftDetector"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\n" + "="*80)
    print("DriftDetector - Test Harness")
    print("="*80)

    # Generate synthetic training data
    np.random.seed(42)
    train_features = np.random.normal(0, 1, (1000, 5))

    # Initialize detector
    detector = DriftDetector(
        reference_features=train_features,
        n_bins=10,
        drift_threshold=0.25,
        alert_threshold=0.20
    )

    print("\n1. Testing normal distribution (no drift)")
    print("-" * 80)
    normal_features = np.random.normal(0, 1, (100, 5))
    alert = detector.check_alert_conditions(normal_features[:, 0])

    print(f"   PSI: {alert['psi']:.4f}")
    print(f"   Alert Level: {alert['alert_level']}")
    print(f"   Drift Detected: {alert['drift_detected']}")

    print("\n2. Testing shifted distribution (drift)")
    print("-" * 80)
    shifted_features = np.random.normal(3, 1, (100, 5))
    alert = detector.check_alert_conditions(shifted_features[:, 0])

    print(f"   PSI: {alert['psi']:.4f}")
    print(f"   Alert Level: {alert['alert_level']}")
    print(f"   Drift Detected: {alert['drift_detected']}")

    print("\n3. Testing KL divergence")
    print("-" * 80)
    kl = detector.calculate_kl_divergence(normal_features[:, 0])
    print(f"   KL divergence (normal): {kl:.4f}")

    kl_shifted = detector.calculate_kl_divergence(shifted_features[:, 0])
    print(f"   KL divergence (shifted): {kl_shifted:.4f}")

    print("\n4. Detector Statistics")
    print("-" * 80)
    stats = detector.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ DriftDetector test harness completed")


if __name__ == '__main__':
    main()
