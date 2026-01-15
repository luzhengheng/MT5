#!/usr/bin/env python3
"""
Task #114: ML Predictor (Model Inference Engine)

Loads trained XGBoost model and performs real-time inference.

Protocol: v4.3 (Zero-Trust Edition)
"""

import os
import hashlib
import pickle
import time
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

import numpy as np

logger = logging.getLogger(__name__)

# Model integrity check (Task #114 model matching 21-feature schema)
EXPECTED_MODEL_MD5 = "2310ff8b54c1edfb5e2a2528bfc3a468"
DEFAULT_MODEL_PATH = "/opt/mt5-crs/data/models/xgboost_task_114.pkl"


class MLPredictor:
    """
    ML inference engine for real-time trading signal generation

    Features:
    - Model integrity verification (MD5 check)
    - Graceful degradation on errors
    - Confidence-based signal filtering
    - Latency tracking
    """

    def __init__(self,
                 model_path: str = DEFAULT_MODEL_PATH,
                 confidence_threshold: float = 0.55,
                 verify_md5: bool = True):
        """
        Initialize ML predictor

        Args:
            model_path: Path to pickled XGBoost model
            confidence_threshold: Minimum confidence for BUY/SELL signals
            verify_md5: Whether to verify model file integrity
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.is_loaded = False
        self.load_time_ms = 0.0

        # Load model
        try:
            self._load_model(verify_md5=verify_md5)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Predictor will operate in degraded mode (always HOLD)

        logger.info(f"MLPredictor initialized (threshold={confidence_threshold})")

    def _calculate_md5(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _load_model(self, verify_md5: bool = True):
        """
        Load XGBoost model from disk with integrity check

        Args:
            verify_md5: Whether to verify MD5 hash

        Raises:
            FileNotFoundError: Model file not found
            ValueError: MD5 mismatch (model corruption)
            Exception: Model loading error
        """
        start_time = time.time()

        # Check file exists
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        # Verify MD5 integrity
        if verify_md5:
            actual_md5 = self._calculate_md5(self.model_path)
            if actual_md5 != EXPECTED_MODEL_MD5:
                raise ValueError(
                    f"Model integrity check FAILED!\n"
                    f"Expected MD5: {EXPECTED_MODEL_MD5}\n"
                    f"Actual MD5:   {actual_md5}\n"
                    f"Model file may be corrupted or tampered."
                )
            logger.info(f"Model integrity verified: {actual_md5}")

        # Load pickled model
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)

        self.is_loaded = True
        self.load_time_ms = (time.time() - start_time) * 1000

        logger.info(f"Model loaded successfully (took {self.load_time_ms:.2f}ms)")

    def predict(self,
                feature_vector: np.ndarray) -> Tuple[int, float, float]:
        """
        Perform inference on feature vector

        Args:
            feature_vector: (21,) numpy array of features

        Returns:
            Tuple of (signal, confidence, latency_ms)
            - signal: 0 (HOLD), 1 (BUY), -1 (SELL)
            - confidence: Probability [0, 1]
            - latency_ms: Inference latency in milliseconds
        """
        start_time = time.time()

        # Degraded mode: model not loaded
        if not self.is_loaded or self.model is None:
            logger.warning("Model not loaded, returning HOLD signal")
            latency_ms = (time.time() - start_time) * 1000
            return 0, 0.0, latency_ms

        try:
            # Validate input shape
            if feature_vector.shape != (21,):
                raise ValueError(
                    f"Invalid feature vector shape: {feature_vector.shape}, "
                    f"expected (21,)"
                )

            # Check for NaN or Inf
            if np.any(np.isnan(feature_vector)) or np.any(np.isinf(feature_vector)):
                logger.warning("Feature vector contains NaN or Inf, returning HOLD")
                latency_ms = (time.time() - start_time) * 1000
                return 0, 0.0, latency_ms

            # Reshape for model input: (1, 21)
            X = feature_vector.reshape(1, -1)

            # Get probability predictions
            proba = self.model.predict_proba(X)[0]  # [prob_class_0, prob_class_1]

            # Class 1 = BUY, Class 0 = SELL/HOLD
            confidence = proba[1]  # Probability of BUY

            # Generate signal based on confidence threshold
            if confidence >= self.confidence_threshold:
                signal = 1  # BUY
            elif confidence <= (1 - self.confidence_threshold):
                signal = -1  # SELL
            else:
                signal = 0  # HOLD (low confidence)

            latency_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"Prediction: signal={signal}, confidence={confidence:.4f}, "
                f"latency={latency_ms:.2f}ms"
            )

            return signal, confidence, latency_ms

        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            latency_ms = (time.time() - start_time) * 1000
            return 0, 0.0, latency_ms  # Fail-safe: HOLD

    def get_model_info(self) -> Dict[str, any]:
        """
        Get model metadata

        Returns:
            Dictionary with model information
        """
        return {
            'model_path': self.model_path,
            'is_loaded': self.is_loaded,
            'expected_md5': EXPECTED_MODEL_MD5,
            'load_time_ms': self.load_time_ms,
            'confidence_threshold': self.confidence_threshold,
            'model_type': type(self.model).__name__ if self.model else None
        }

    def set_confidence_threshold(self, threshold: float):
        """
        Update confidence threshold

        Args:
            threshold: New threshold value [0, 1]
        """
        if not 0 <= threshold <= 1:
            raise ValueError(f"Threshold must be in [0, 1], got {threshold}")

        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold updated to {threshold}")


def main():
    """Test harness"""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Initialize predictor
    predictor = MLPredictor(confidence_threshold=0.55)

    # Print model info
    info = predictor.get_model_info()
    print("\n" + "="*60)
    print("ML Predictor Model Info")
    print("="*60)
    for key, value in info.items():
        print(f"{key:25s}: {value}")

    # Test prediction with random features
    print("\n" + "="*60)
    print("Testing prediction with random feature vector")
    print("="*60)

    # Generate random feature vector (simulating real features)
    np.random.seed(42)
    random_features = np.random.randn(21)

    signal, confidence, latency = predictor.predict(random_features)

    print(f"Feature vector (first 5): {random_features[:5]}")
    print(f"Signal:     {signal} ({'BUY' if signal == 1 else 'SELL' if signal == -1 else 'HOLD'})")
    print(f"Confidence: {confidence:.4f}")
    print(f"Latency:    {latency:.2f} ms")

    # Test multiple predictions for latency benchmark
    print("\n" + "="*60)
    print("Latency benchmark (100 predictions)")
    print("="*60)

    latencies = []
    for i in range(100):
        features = np.random.randn(21)
        _, _, lat = predictor.predict(features)
        latencies.append(lat)

    print(f"Mean latency:   {np.mean(latencies):.3f} ms")
    print(f"Median latency: {np.median(latencies):.3f} ms")
    print(f"P95 latency:    {np.percentile(latencies, 95):.3f} ms")
    print(f"P99 latency:    {np.percentile(latencies, 99):.3f} ms")

    # Check if latency meets target (<10ms)
    if np.percentile(latencies, 95) < 10:
        print("\n✅ Latency target met (<10ms P95)")
    else:
        print(f"\n❌ Latency target NOT met (P95 = {np.percentile(latencies, 95):.2f}ms)")


if __name__ == '__main__':
    main()
