#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #073: Custom MLflow Model for Stacking Ensemble

Package LightGBM + LSTM + Logistic Regression meta-learner into a single
production-ready MLflow model that can be deployed and served seamlessly.

This custom PythonModel encapsulates:
1. LGB predictor (loads LightGBM model from artifact)
2. LSTM predictor (loads PyTorch LSTM model from artifact)
3. Data alignment handler (handles index mapping)
4. Meta-learner (loads Logistic Regression from artifact)

Inference pipeline:
- Input: X_tabular (N, 23) + X_sequential (N-59, 60, 23)
- Output: (N-59, 3) ensemble probabilities

Protocol v4.3 (Zero-Trust Edition)
"""

import numpy as np
import pandas as pd
import logging
import json
import pickle
from typing import Dict, Any

try:
    import mlflow.pyfunc
except ImportError:
    mlflow = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StackingEnsembleMLflowModel(mlflow.pyfunc.PythonModel if mlflow else object):
    """
    Custom MLflow model for stacking ensemble inference

    This model wraps the complete inference pipeline:
    1. Load base models (LGB, LSTM) from artifacts
    2. Load meta-learner from artifacts
    3. Generate predictions using aligned LGB + LSTM outputs
    4. Return final ensemble predictions

    Can be served via:
    - mlflow.models.serve() for REST API
    - model.predict() for batch inference
    - MLflow Model Registry for production deployments
    """

    def load_context(self, context):
        """
        Load model artifacts from MLflow context

        Called once when model is loaded. Initializes all components needed
        for inference.

        Args:
            context: MLflow context containing artifacts
        """
        logger.info("Loading StackingEnsembleMLflowModel context...")

        try:
            # Import model components
            from src.model.ensemble.predictors import LGBPredictor, LSTMPredictor
            from src.model.ensemble.alignment import DataAlignmentHandler

            # Load LightGBM model
            import lightgbm as lgb
            lgb_model_path = context.artifacts['lgb_model_path']
            self.lgb_model = lgb.Booster(model_file=lgb_model_path)
            logger.info(f"✓ LightGBM model loaded from {lgb_model_path}")

            # Load LSTM model
            import torch
            from src.model.dl.models import LSTMModel

            lstm_model_path = context.artifacts['lstm_model_path']
            checkpoint = torch.load(lstm_model_path, map_location='cpu')

            # Reconstruct LSTM with hyperparameters from metadata
            lstm_config = json.loads(context.artifacts['lstm_config_path'])
            self.lstm_model = LSTMModel(
                input_size=lstm_config['input_size'],
                hidden_dim=lstm_config['hidden_dim'],
                num_layers=lstm_config['num_layers'],
                dropout=lstm_config['dropout'],
                output_size=lstm_config['output_size']
            )
            self.lstm_model.load_state_dict(checkpoint)
            self.lstm_model.eval()
            logger.info(f"✓ LSTM model loaded from {lstm_model_path}")

            # Load feature names
            with open(context.artifacts['feature_names_path'], 'r') as f:
                self.feature_names = json.load(f)
            logger.info(f"✓ Feature names loaded ({len(self.feature_names)} features)")

            # Load meta-learner
            with open(context.artifacts['meta_learner_path'], 'rb') as f:
                meta_learner = pickle.load(f)
            logger.info(f"✓ Meta-learner loaded from {context.artifacts['meta_learner_path']}")

            # Initialize predictors and ensemble components
            self.lgb_predictor = LGBPredictor(self.lgb_model, self.feature_names)
            logger.info("✓ LGBPredictor initialized")

            self.lstm_predictor = LSTMPredictor(self.lstm_model, device='cpu')
            logger.info("✓ LSTMPredictor initialized")

            self.alignment = DataAlignmentHandler(sequence_length=60)
            logger.info("✓ DataAlignmentHandler initialized")

            # Initialize ensemble with meta-learner
            from src.model.ensemble.ensemble import EnsemblePredictor

            self.ensemble = EnsemblePredictor(
                self.lgb_predictor,
                self.lstm_predictor,
                self.alignment,
                weights=(0.5, 0.5),
                use_stacking=True
            )
            self.ensemble.meta_learner = meta_learner
            logger.info("✓ EnsemblePredictor initialized with meta-learner")

            logger.info("✓ StackingEnsembleMLflowModel context loaded successfully")

        except Exception as e:
            logger.error(f"Error loading context: {e}")
            raise

    def predict(self, context, model_input: pd.DataFrame) -> pd.DataFrame:
        """
        Make ensemble predictions

        Args:
            context: MLflow context (ignored, used for consistency)
            model_input: DataFrame with columns:
                - 'X_tabular': (N, 23) tabular features for LightGBM
                - 'X_sequential': (N-59, 60, 23) sequence features for LSTM
                  (Can be serialized as list or numpy array in DataFrame)

        Returns:
            DataFrame with columns ['class_0_prob', 'class_1_prob', 'class_2_prob']
            containing (N-59, 3) ensemble probabilities
        """
        logger.info(f"Making predictions on {len(model_input)} samples")

        try:
            # Extract and validate input
            if 'X_tabular' not in model_input.columns or 'X_sequential' not in model_input.columns:
                raise ValueError(
                    f"Expected columns ['X_tabular', 'X_sequential'], "
                    f"got {list(model_input.columns)}"
                )

            # Convert input to numpy arrays
            X_tabular = np.array(model_input['X_tabular'].tolist())
            X_sequential = np.array(model_input['X_sequential'].tolist())

            logger.info(f"X_tabular shape: {X_tabular.shape}")
            logger.info(f"X_sequential shape: {X_sequential.shape}")

            # Validate shapes
            assert X_tabular.shape[1] == 23, f"Expected 23 features, got {X_tabular.shape[1]}"
            assert X_sequential.shape[1] == 60, f"Expected sequence length 60, got {X_sequential.shape[1]}"
            assert X_sequential.shape[2] == 23, f"Expected 23 features, got {X_sequential.shape[2]}"

            # Convert sequences to tensor if needed
            import torch
            if not isinstance(X_sequential, torch.Tensor):
                X_sequential = torch.FloatTensor(X_sequential)

            # Generate ensemble predictions
            ensemble_proba = self.ensemble.predict_proba(X_tabular, X_sequential)

            logger.info(f"Ensemble predictions shape: {ensemble_proba.shape}")

            # Validate output
            assert ensemble_proba.shape[1] == 3, f"Expected 3 classes, got {ensemble_proba.shape[1]}"
            assert np.allclose(
                ensemble_proba.sum(axis=1), 1.0, atol=1e-5
            ), "Output probabilities don't sum to 1.0"

            # Return as DataFrame
            result_df = pd.DataFrame(
                ensemble_proba,
                columns=['class_0_prob', 'class_1_prob', 'class_2_prob']
            )

            logger.info(f"✓ Predictions generated successfully")

            return result_df

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise


def create_mlflow_model_artifacts(
    lgb_model_path: str,
    lstm_model_path: str,
    lstm_config: dict,
    meta_learner,
    feature_names: list,
    artifact_dir: str
) -> Dict[str, str]:
    """
    Prepare artifacts for MLflow model registration

    Args:
        lgb_model_path: Path to LightGBM model file
        lstm_model_path: Path to LSTM checkpoint file
        lstm_config: Dictionary with LSTM hyperparameters
        meta_learner: Trained meta-learner (sklearn LogisticRegression)
        feature_names: List of feature names
        artifact_dir: Directory to save artifacts

    Returns:
        Dictionary mapping artifact names to paths
    """
    import os

    os.makedirs(artifact_dir, exist_ok=True)

    artifacts = {}

    # Copy LightGBM model
    import shutil
    lgb_dest = os.path.join(artifact_dir, 'lgb_model.txt')
    shutil.copy(lgb_model_path, lgb_dest)
    artifacts['lgb_model_path'] = lgb_dest
    logger.info(f"✓ LGB model artifact: {lgb_dest}")

    # Copy LSTM checkpoint
    lstm_dest = os.path.join(artifact_dir, 'lstm_model.pt')
    shutil.copy(lstm_model_path, lstm_dest)
    artifacts['lstm_model_path'] = lstm_dest
    logger.info(f"✓ LSTM model artifact: {lstm_dest}")

    # Save LSTM config
    lstm_config_path = os.path.join(artifact_dir, 'lstm_config.json')
    with open(lstm_config_path, 'w') as f:
        json.dump(lstm_config, f, indent=2)
    artifacts['lstm_config_path'] = lstm_config_path
    logger.info(f"✓ LSTM config artifact: {lstm_config_path}")

    # Save meta-learner
    meta_learner_path = os.path.join(artifact_dir, 'meta_learner.pkl')
    with open(meta_learner_path, 'wb') as f:
        pickle.dump(meta_learner, f)
    artifacts['meta_learner_path'] = meta_learner_path
    logger.info(f"✓ Meta-learner artifact: {meta_learner_path}")

    # Save feature names
    feature_names_path = os.path.join(artifact_dir, 'feature_names.json')
    with open(feature_names_path, 'w') as f:
        json.dump(feature_names, f, indent=2)
    artifacts['feature_names_path'] = feature_names_path
    logger.info(f"✓ Feature names artifact: {feature_names_path}")

    return artifacts


if __name__ == "__main__":
    logger.info("Testing StackingEnsembleMLflowModel...")
    logger.info("(Full test requires artifact paths and MLflow context)")
