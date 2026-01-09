#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #073: Stacking Meta-Learner

Train a meta-learner (Logistic Regression) on stacked Out-of-Fold predictions
from LightGBM and LSTM base models.

The meta-learner learns optimal weights and combinations of base model predictions
to improve ensemble performance.

Protocol v4.3 (Zero-Trust Edition)
"""

import numpy as np
import logging
from typing import Optional
from sklearn.linear_model import LogisticRegression

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StackingMetaLearner:
    """
    Train and use a meta-learner for stacking ensemble

    Architecture:
    - Input: Stacked OOF predictions from base models (N_samples, 6)
      - 3 features from LightGBM probabilities [class_0, class_1, class_2]
      - 3 features from LSTM probabilities [class_0, class_1, class_2]
    - Output: Meta-learner predictions (N_samples, 3)
      - Logistic Regression learns optimal combination of base predictions

    Key Properties:
    - Meta-learner trained on OOF predictions (no data leakage)
    - Input shape: (N_samples, 6) - 3 from LGB + 3 from LSTM
    - Output shape: (N_samples, 3) - 3 classes
    - Handles index alignment automatically
    """

    def __init__(self, alignment_handler=None, meta_model=None):
        """
        Initialize meta-learner

        Args:
            alignment_handler: DataAlignmentHandler for index mapping
            meta_model: Pre-trained meta-learner. If None, creates new LogisticRegression
        """
        if alignment_handler is None:
            from src.model.ensemble.alignment import DataAlignmentHandler
            self.alignment = DataAlignmentHandler()
        else:
            self.alignment = alignment_handler

        if meta_model is None:
            # Create new Logistic Regression meta-learner
            self.meta_model = LogisticRegression(
                penalty='l2',
                C=1.0,
                max_iter=1000,
                solver='lbfgs',
                random_state=42,
                multi_class='multinomial',
                verbose=0
            )
        else:
            self.meta_model = meta_model

        logger.info("StackingMetaLearner initialized")

    def train(
        self,
        lgb_oof: np.ndarray,
        lstm_oof: np.ndarray,
        y_train: np.ndarray,
        valid_indices: np.ndarray
    ) -> LogisticRegression:
        """
        Train meta-learner on stacked OOF predictions

        Args:
            lgb_oof: (N_samples, 3) LightGBM OOF probabilities
            lstm_oof: (N_windows, 3) LSTM OOF probabilities
            y_train: (N_samples,) training labels (before windowing)
            valid_indices: Array of indices [59...N-1] where both models predict

        Returns:
            Trained LogisticRegression meta-learner
        """
        logger.info("Training meta-learner on stacked OOF predictions...")

        # Validate input shapes
        assert lgb_oof.shape[1] == 3, f"LGB OOF should have 3 classes, got {lgb_oof.shape[1]}"
        assert lstm_oof.shape[1] == 3, f"LSTM OOF should have 3 classes, got {lstm_oof.shape[1]}"
        assert y_train.shape[0] == lgb_oof.shape[0], \
            f"y_train ({y_train.shape[0]}) must match LGB OOF ({lgb_oof.shape[0]})"

        # Align OOF predictions to same index space
        # LGB OOF is (N_samples, 3), slice to valid indices
        lgb_aligned = lgb_oof[valid_indices]  # (N_windows, 3)
        lstm_aligned = lstm_oof  # Already (N_windows, 3)

        logger.info(f"LGB OOF shape after alignment: {lgb_aligned.shape}")
        logger.info(f"LSTM OOF shape: {lstm_aligned.shape}")

        # Verify shapes match
        assert lgb_aligned.shape[0] == lstm_aligned.shape[0], \
            f"Shape mismatch after alignment: LGB {lgb_aligned.shape[0]} vs LSTM {lstm_aligned.shape[0]}"

        # Stack OOF predictions as meta-features
        X_meta = np.hstack([lgb_aligned, lstm_aligned])  # (N_windows, 6)
        logger.info(f"Meta-features shape: {X_meta.shape}")

        # Verify probabilities sum to 1
        lgb_sums = lgb_aligned.sum(axis=1)
        lstm_sums = lstm_aligned.sum(axis=1)

        if not np.allclose(lgb_sums, 1.0, atol=1e-5):
            logger.warning(f"LGB OOF probabilities don't sum to 1.0:")
            logger.warning(f"  Min sum: {lgb_sums.min():.6f}, Max sum: {lgb_sums.max():.6f}")

        if not np.allclose(lstm_sums, 1.0, atol=1e-5):
            logger.warning(f"LSTM OOF probabilities don't sum to 1.0:")
            logger.warning(f"  Min sum: {lstm_sums.min():.6f}, Max sum: {lstm_sums.max():.6f}")

        # Align labels to valid indices
        y_meta = y_train[valid_indices]
        logger.info(f"Meta-targets shape: {y_meta.shape}")
        logger.info(f"Class distribution: {np.bincount(y_meta + 1)}")  # Shift [-1,0,1] -> [0,1,2]

        # Train meta-learner
        logger.info("Training Logistic Regression meta-learner...")
        self.meta_model.fit(X_meta, y_meta)

        logger.info(f"✓ Meta-learner trained on {X_meta.shape[0]} samples")
        logger.info(f"  Meta-learner coefficients shape: {self.meta_model.coef_.shape}")
        logger.info(f"  Meta-learner intercept shape: {self.meta_model.intercept_.shape}")

        # Log learned weights
        logger.info("Learned feature weights:")
        feature_names = [
            'LGB_class0', 'LGB_class1', 'LGB_class2',
            'LSTM_class0', 'LSTM_class1', 'LSTM_class2'
        ]
        for i, (coef, name) in enumerate(zip(self.meta_model.coef_[0], feature_names)):
            logger.info(f"  {name}: {coef:.4f}")

        return self.meta_model

    def predict_proba(
        self,
        lgb_proba: np.ndarray,
        lstm_proba: np.ndarray
    ) -> np.ndarray:
        """
        Generate ensemble predictions using trained meta-learner

        Args:
            lgb_proba: (N_windows, 3) LightGBM probabilities
            lstm_proba: (N_windows, 3) LSTM probabilities

        Returns:
            (N_windows, 3) ensemble probabilities from meta-learner
        """
        # Verify shapes match
        assert lgb_proba.shape == lstm_proba.shape, \
            f"Shape mismatch: LGB {lgb_proba.shape} vs LSTM {lstm_proba.shape}"

        assert lgb_proba.shape[1] == 3, f"Expected 3 classes, got {lgb_proba.shape[1]}"

        # Stack base predictions
        X_meta = np.hstack([lgb_proba, lstm_proba])  # (N_windows, 6)

        # Predict with meta-learner
        ensemble_proba = self.meta_model.predict_proba(X_meta)  # (N_windows, 3)

        # Validate output
        assert ensemble_proba.shape[1] == 3, f"Expected 3 classes in output, got {ensemble_proba.shape[1]}"
        assert np.allclose(
            ensemble_proba.sum(axis=1), 1.0, atol=1e-5
        ), "Output probabilities don't sum to 1.0"

        return ensemble_proba

    def predict(
        self,
        lgb_proba: np.ndarray,
        lstm_proba: np.ndarray
    ) -> np.ndarray:
        """
        Generate class predictions using trained meta-learner

        Args:
            lgb_proba: (N_windows, 3) LightGBM probabilities
            lstm_proba: (N_windows, 3) LSTM probabilities

        Returns:
            (N_windows,) predicted class labels
        """
        proba = self.predict_proba(lgb_proba, lstm_proba)
        return np.argmax(proba, axis=1)

    def get_weights(self) -> dict:
        """
        Get learned meta-learner weights

        Returns:
            Dictionary with:
            - coef: (n_classes, n_features) weight matrix
            - intercept: (n_classes,) intercept terms
            - feature_names: Names of input features
        """
        feature_names = [
            'LGB_class0', 'LGB_class1', 'LGB_class2',
            'LSTM_class0', 'LSTM_class1', 'LSTM_class2'
        ]

        return {
            'coef': self.meta_model.coef_,
            'intercept': self.meta_model.intercept_,
            'feature_names': feature_names,
            'classes': self.meta_model.classes_
        }

    def save(self, filepath: str):
        """
        Save meta-learner to file

        Args:
            filepath: Path to save meta-learner (pickle format)
        """
        import pickle

        with open(filepath, 'wb') as f:
            pickle.dump(self.meta_model, f)

        logger.info(f"Meta-learner saved to {filepath}")

    @classmethod
    def load(cls, filepath: str, alignment_handler=None) -> 'StackingMetaLearner':
        """
        Load meta-learner from file

        Args:
            filepath: Path to saved meta-learner
            alignment_handler: Optional DataAlignmentHandler

        Returns:
            StackingMetaLearner instance with loaded model
        """
        import pickle

        with open(filepath, 'rb') as f:
            meta_model = pickle.load(f)

        logger.info(f"Meta-learner loaded from {filepath}")

        return cls(alignment_handler=alignment_handler, meta_model=meta_model)


if __name__ == "__main__":
    logger.info("Testing StackingMetaLearner...")
    logger.info("(Full test requires OOF predictions from base models)")
