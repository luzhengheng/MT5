#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #072: Unified Prediction Interface for Base Learners

Standardize prediction interfaces for LightGBM and LSTM models:
- LightGBM: Binary classification → 3-class probabilities
- LSTM: Logits → Softmax probabilities

Both return (N, 3) numpy arrays with class probabilities

Protocol v4.3 (Zero-Trust Edition)
"""

import numpy as np
import torch
import torch.nn.functional as F
import logging
from abc import ABC, abstractmethod
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseLearnerPredictor(ABC):
    """
    Abstract base class for unified prediction interface

    All predictors must implement predict_proba() returning (N, 3) probability arrays
    """

    @abstractmethod
    def predict_proba(self, X) -> np.ndarray:
        """
        Return class probabilities

        Returns:
            numpy array of shape (N, 3) with probabilities for classes [0, 1, 2]
            - Class 0: Short signal (-1 in original labels)
            - Class 1: Hold signal (0 in original labels)
            - Class 2: Long signal (1 in original labels)
        """
        pass

    def predict(self, X) -> np.ndarray:
        """Predict class labels from probabilities"""
        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)

    def predict_confidence(self, X) -> np.ndarray:
        """Predict with confidence scores"""
        proba = self.predict_proba(X)
        # Confidence = max probability - 1/num_classes
        confidence = np.max(proba, axis=1) - (1.0 / 3)
        return confidence


class LGBPredictor(BaseLearnerPredictor):
    """
    Wrapper for LightGBM binary predictions

    Converts LightGBM binary probabilities to 3-class format for ensemble compatibility.

    LightGBM trains on binary (0, 1) labels:
    - Class 0: Original label -1 (short)
    - Class 1: Original label 0 or 1 (hold or long)

    This predictor expands to 3-class by:
    - Class 0 (short): 1 - binary_proba
    - Class 1 (hold): 0.0 (not predicted by binary model)
    - Class 2 (long): binary_proba
    """

    def __init__(self, model, feature_names: Optional[list] = None):
        """
        Initialize LGBPredictor

        Args:
            model: LightGBM booster object
            feature_names: Optional list of feature names
        """
        self.model = model
        self.feature_names = feature_names or []
        logger.info(f"LGBPredictor initialized with {len(self.feature_names)} features")

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        LightGBM binary proba [0, 1] → convert to [0, 1, 2] format

        Args:
            X: Input features shape (N, n_features)

        Returns:
            Probabilities shape (N, 3) for classes [short, hold, long]
        """
        try:
            # Get binary probabilities from LightGBM
            y_proba_binary = self.model.predict(X)  # Shape: (N,) or (N, 1)

            # Ensure 1D array
            if y_proba_binary.ndim > 1:
                y_proba_binary = y_proba_binary.ravel()

            # Validate probabilities are in [0, 1]
            if np.any(y_proba_binary < 0) or np.any(y_proba_binary > 1):
                logger.warning(
                    f"LightGBM probabilities out of range: "
                    f"min={np.min(y_proba_binary):.4f}, max={np.max(y_proba_binary):.4f}"
                )

            # Convert binary to 3-class
            # Class 0 (short): probability of NOT predicting class 1
            proba_0 = 1 - y_proba_binary

            # Class 2 (long): probability of predicting class 1
            proba_2 = y_proba_binary

            # Class 1 (hold): 0.0 (not predicted by binary model)
            # This will be redistributed by ensemble weighting
            proba_1 = np.zeros_like(proba_0)

            # Stack into (N, 3) array
            proba_3class = np.column_stack([proba_0, proba_1, proba_2])

            # Validate output shape and values
            assert proba_3class.shape[1] == 3, f"Expected shape (N, 3), got {proba_3class.shape}"
            assert np.allclose(
                proba_3class.sum(axis=1), 1.0, atol=1e-6
            ), "Probabilities don't sum to 1.0"

            return proba_3class

        except Exception as e:
            logger.error(f"Error in LGBPredictor.predict_proba: {e}")
            raise

    def __repr__(self) -> str:
        return f"LGBPredictor(features={len(self.feature_names)})"


class LSTMPredictor(BaseLearnerPredictor):
    """
    Wrapper for LSTM predictions

    LSTM forward pass returns logits (N, 3) for 3-class classification.
    This predictor applies softmax to convert logits to probabilities.
    """

    def __init__(self, model, device: str = "cpu"):
        """
        Initialize LSTMPredictor

        Args:
            model: PyTorch LSTM model
            device: Device to use for inference (cpu or cuda)
        """
        self.model = model
        self.device = device
        logger.info(f"LSTMPredictor initialized on device={device}")

    def predict_proba(self, X: torch.Tensor) -> np.ndarray:
        """
        LSTM forward pass returns logits → apply softmax

        Args:
            X: Input tensor shape (N, seq_len, n_features) or numpy array

        Returns:
            Probabilities shape (N, 3) for classes [short, hold, long]
        """
        try:
            # Convert to tensor if needed
            if isinstance(X, np.ndarray):
                X = torch.FloatTensor(X)

            # Move to device
            X_device = X.to(self.device)

            # Forward pass (no gradients)
            with torch.no_grad():
                logits = self.model(X_device)  # Shape: (N, 3)

                # Apply softmax to get probabilities
                proba = F.softmax(logits, dim=1)  # Shape: (N, 3)

                # Convert to numpy
                proba_np = proba.cpu().numpy()

            # Validate output
            assert proba_np.shape[1] == 3, f"Expected shape (N, 3), got {proba_np.shape}"
            assert np.allclose(
                proba_np.sum(axis=1), 1.0, atol=1e-6
            ), "Probabilities don't sum to 1.0"

            return proba_np

        except Exception as e:
            logger.error(f"Error in LSTMPredictor.predict_proba: {e}")
            raise

    def __repr__(self) -> str:
        return f"LSTMPredictor(device={self.device})"


if __name__ == "__main__":
    # Test prediction interfaces
    logger.info("Testing prediction interfaces...")

    # Test LGBPredictor with dummy data
    try:
        import lightgbm as lgb

        # Create dummy LightGBM model
        X_test = np.random.randn(10, 23)
        dummy_model = lgb.LGBMClassifier(random_state=42)
        dummy_model.fit(np.random.randn(100, 23), np.random.randint(0, 2, 100))

        lgb_pred = LGBPredictor(dummy_model.booster_, feature_names=[f"feat_{i}" for i in range(23)])
        lgb_proba = lgb_pred.predict_proba(X_test)

        logger.info(f"✓ LGBPredictor output shape: {lgb_proba.shape}")
        logger.info(f"  Probabilities sum to 1.0: {np.allclose(lgb_proba.sum(axis=1), 1.0)}")

    except Exception as e:
        logger.error(f"LGBPredictor test failed: {e}")

    # Test LSTMPredictor with dummy data
    try:
        from src.model.dl.models import LSTMModel

        X_test = torch.randn(10, 60, 23)  # (batch, seq_len, features)

        lstm_model = LSTMModel(
            input_size=23, hidden_dim=64, num_layers=2, dropout=0.1, output_size=3
        )

        lstm_pred = LSTMPredictor(lstm_model, device="cpu")
        lstm_proba = lstm_pred.predict_proba(X_test)

        logger.info(f"✓ LSTMPredictor output shape: {lstm_proba.shape}")
        logger.info(f"  Probabilities sum to 1.0: {np.allclose(lstm_proba.sum(axis=1), 1.0)}")

    except Exception as e:
        logger.error(f"LSTMPredictor test failed: {e}")

    logger.info("Prediction interface tests complete!")
