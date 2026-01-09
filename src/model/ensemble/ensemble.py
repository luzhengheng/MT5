#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #072: Ensemble Predictor

Combine LightGBM and LSTM predictions via weighted averaging or stacking

Strategies:
1. Weighted Average (simple): ensemble = w1*lgb + w2*lstm
2. Stacking (complex): meta-learner trained on base predictions

Protocol v4.3 (Zero-Trust Edition)
"""

import numpy as np
import logging
from typing import Tuple, Optional
from sklearn.linear_model import LogisticRegression

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """
    Combine LightGBM and LSTM predictions via weighted averaging or stacking
    """

    def __init__(
        self,
        lgb_predictor,
        lstm_predictor,
        alignment_handler,
        weights: Tuple[float, float] = (0.5, 0.5),
        use_stacking: bool = False,
    ):
        """
        Initialize ensemble predictor

        Args:
            lgb_predictor: LGBPredictor instance
            lstm_predictor: LSTMPredictor instance
            alignment_handler: DataAlignmentHandler instance
            weights: Tuple of (w_lgb, w_lstm) for weighted averaging
            use_stacking: If True, use meta-learner instead of weighted average
        """
        self.lgb_predictor = lgb_predictor
        self.lstm_predictor = lstm_predictor
        self.alignment = alignment_handler
        self.weights = weights
        self.use_stacking = use_stacking
        self.meta_learner = None

        logger.info(f"EnsemblePredictor initialized: " f"weights={weights}, stacking={use_stacking}")

    def predict_proba(self, X_tabular: np.ndarray, X_sequential) -> np.ndarray:
        """
        Generate ensemble predictions

        Args:
            X_tabular: (N, 23) features for LightGBM
            X_sequential: (N-59, 60, 23) sequences for LSTM (or numpy/tensor)

        Returns:
            (N-59, 3) ensemble probability array
        """
        try:
            N_samples = X_tabular.shape[0]

            # Get individual model predictions
            lgb_proba = self.lgb_predictor.predict_proba(X_tabular)  # (N, 3)
            lstm_proba = self.lstm_predictor.predict_proba(X_sequential)  # (N-59, 3)

            # Align to same index space
            lgb_aligned, lstm_aligned, valid_idx = self.alignment.align_predictions(
                lgb_proba, lstm_proba, N_samples
            )

            if self.use_stacking and self.meta_learner is not None:
                # Stack predictions and pass to meta-learner
                stacked = np.hstack([lgb_aligned, lstm_aligned])  # (M, 6)
                ensemble_proba = self.meta_learner.predict_proba(stacked)
            else:
                # Weighted average
                w_lgb, w_lstm = self.weights
                ensemble_proba = w_lgb * lgb_aligned + w_lstm * lstm_aligned

                # Normalize (ensure probabilities sum to 1)
                ensemble_proba = ensemble_proba / ensemble_proba.sum(axis=1, keepdims=True)

            return ensemble_proba

        except Exception as e:
            logger.error(f"Error in ensemble prediction: {e}")
            raise

    def fit_meta_learner(self, X_tabular: np.ndarray, X_sequential, y_true: np.ndarray):
        """
        Train stacking meta-learner (Logistic Regression) on base predictions

        Args:
            X_tabular: (N, 23) training features for LightGBM
            X_sequential: (N-59, 60, 23) training sequences for LSTM
            y_true: (N,) training labels
        """
        if not self.use_stacking:
            logger.info("Stacking disabled, skipping meta-learner training")
            return

        try:
            N_samples = X_tabular.shape[0]

            logger.info("Training meta-learner on base predictions...")

            # Generate base predictions
            lgb_proba = self.lgb_predictor.predict_proba(X_tabular)  # (N, 3)
            lstm_proba = self.lstm_predictor.predict_proba(X_sequential)  # (N-59, 3)

            # Align
            lgb_aligned, lstm_aligned, _ = self.alignment.align_predictions(
                lgb_proba, lstm_proba, N_samples
            )

            # Stack as meta-features: (M, 6)
            X_meta = np.hstack([lgb_aligned, lstm_aligned])

            # Get aligned labels
            valid_idx = self.alignment.get_valid_indices(N_samples)
            y_meta = y_true[valid_idx]

            # Train meta-learner
            self.meta_learner = LogisticRegression(max_iter=1000, random_state=42)
            self.meta_learner.fit(X_meta, y_meta)

            logger.info(f"✓ Meta-learner trained on {X_meta.shape[0]} samples")

        except Exception as e:
            logger.error(f"Error training meta-learner: {e}")
            raise

    def predict(self, X_tabular: np.ndarray, X_sequential) -> np.ndarray:
        """Predict class labels"""
        proba = self.predict_proba(X_tabular, X_sequential)
        return np.argmax(proba, axis=1)

    def predict_confidence(self, X_tabular: np.ndarray, X_sequential) -> np.ndarray:
        """Predict with confidence scores"""
        proba = self.predict_proba(X_tabular, X_sequential)
        # Confidence = max_prob - 1/num_classes
        confidence = np.max(proba, axis=1) - (1.0 / 3)
        return confidence


if __name__ == "__main__":
    logger.info("Testing EnsemblePredictor...")
    logger.info("(Full test requires loading actual models from MLflow)")
