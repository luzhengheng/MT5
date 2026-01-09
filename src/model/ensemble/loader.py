#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #072: Model Loading & Artifact Retrieval from MLflow

Load best trained models from MLflow experiments:
- Task #069 (LightGBM): task_069_baseline experiment
- Task #071 (LSTM Optuna): task_071_lstm_hpo experiment

Protocol v4.3 (Zero-Trust Edition)
"""

import mlflow
import torch
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    """Load trained models from MLflow artifacts and checkpoints"""

    @staticmethod
    def load_best_lgb_model(experiment_name: str = "task_069_baseline") -> Tuple:
        """
        Load best LightGBM model from MLflow

        Searches for best run (highest AUC score) in the specified experiment
        and loads the logged LightGBM artifact.

        Args:
            experiment_name: MLflow experiment name (default: task_069_baseline)

        Returns:
            Tuple of (lgb_model, run_id)
        """
        logger.info(f"Loading best LightGBM model from {experiment_name}...")

        try:
            # Search for best run (highest AUC score)
            runs = mlflow.search_runs(
                experiment_names=[experiment_name],
                order_by=["metrics.auc_roc DESC"],
                max_results=1
            )

            if runs.empty:
                raise ValueError(f"No runs found in experiment: {experiment_name}")

            best_run_id = runs.iloc[0]["run_id"]
            logger.info(f"Found best LightGBM run: {best_run_id}")

            # Load model artifact from MLflow
            try:
                lgb_model = mlflow.lightgbm.load_model(f"runs:/{best_run_id}/model")
                logger.info(f"Successfully loaded LightGBM model from {best_run_id}")
                return lgb_model, best_run_id
            except Exception as e:
                logger.error(f"Failed to load LightGBM model: {e}")
                raise

        except Exception as e:
            logger.error(f"Error loading best LightGBM model: {e}")
            raise

    @staticmethod
    def load_best_lstm_model(
        experiment_name: str = "task_071_lstm_hpo",
        input_size: int = 23,
        sequence_length: int = 60
    ) -> Tuple:
        """
        Load best LSTM model from MLflow

        Searches for best trial (lowest validation loss) in the Optuna
        HPO experiment and loads the trained PyTorch checkpoint.

        Args:
            experiment_name: MLflow experiment name (default: task_071_lstm_hpo)
            input_size: Number of input features (default: 23)
            sequence_length: Sliding window sequence length (default: 60)

        Returns:
            Tuple of (lstm_model, run_id)
        """
        logger.info(f"Loading best LSTM model from {experiment_name}...")

        try:
            # Search for best trial (lowest validation loss)
            runs = mlflow.search_runs(
                experiment_names=[experiment_name],
                order_by=["metrics.best_val_loss ASC"],
                max_results=1
            )

            if runs.empty:
                raise ValueError(f"No runs found in experiment: {experiment_name}")

            best_run_id = runs.iloc[0]["run_id"]
            logger.info(f"Found best LSTM run: {best_run_id}")

            # Extract hyperparameters from run
            run_data = mlflow.get_run(best_run_id)
            params = run_data.data.params

            hidden_dim = int(params.get("hidden_dim", 96))
            num_layers = int(params.get("num_layers", 3))
            dropout = float(params.get("dropout", 0.0))

            logger.info(
                f"Best LSTM hyperparameters: "
                f"hidden_dim={hidden_dim}, num_layers={num_layers}, dropout={dropout}"
            )

            # Load PyTorch model checkpoint
            try:
                # Download artifact path
                checkpoint_path = mlflow.artifacts.download_artifacts(
                    run_id=best_run_id,
                    artifact_path="model"
                )
                logger.info(f"Downloaded LSTM checkpoint from {checkpoint_path}")

                # Import LSTMModel class
                from src.model.dl.models import LSTMModel

                # Create model instance with optimal hyperparameters
                lstm_model = LSTMModel(
                    input_size=input_size,
                    hidden_dim=hidden_dim,
                    num_layers=num_layers,
                    dropout=dropout,
                    output_size=3  # 3 classes: short (-1), hold (0), long (1)
                )

                # Load checkpoint
                checkpoint_file = Path(checkpoint_path) / "best_model.pt"
                if checkpoint_file.exists():
                    checkpoint = torch.load(checkpoint_file, map_location="cpu")
                    lstm_model.load_state_dict(checkpoint)
                    logger.info(f"Successfully loaded LSTM checkpoint from {checkpoint_file}")
                else:
                    # Try alternative naming patterns
                    alt_patterns = [
                        Path(checkpoint_path) / "model.pt",
                        Path(checkpoint_path) / "lstm_model.pt",
                    ]
                    found = False
                    for alt_file in alt_patterns:
                        if alt_file.exists():
                            checkpoint = torch.load(alt_file, map_location="cpu")
                            lstm_model.load_state_dict(checkpoint)
                            logger.info(f"Successfully loaded LSTM checkpoint from {alt_file}")
                            found = True
                            break
                    if not found:
                        raise FileNotFoundError(
                            f"Could not find LSTM checkpoint in {checkpoint_path}"
                        )

                # Set to evaluation mode
                lstm_model.eval()
                logger.info("LSTM model set to evaluation mode")

                return lstm_model, best_run_id

            except Exception as e:
                logger.error(f"Failed to load LSTM model: {e}")
                raise

        except Exception as e:
            logger.error(f"Error loading best LSTM model: {e}")
            raise

    @classmethod
    def load_both_models(
        cls,
        lgb_exp: str = "task_069_baseline",
        lstm_exp: str = "task_071_lstm_hpo",
        input_size: int = 23,
        feature_names: Optional[list] = None
    ) -> Dict:
        """
        Load both LightGBM and LSTM models from their respective MLflow experiments

        Args:
            lgb_exp: LightGBM experiment name
            lstm_exp: LSTM experiment name
            input_size: Number of input features
            feature_names: Optional list of feature names for tracking

        Returns:
            Dictionary containing:
            {
                'lgb_model': LightGBM booster object,
                'lgb_run_id': LightGBM run ID,
                'lstm_model': LSTM PyTorch model,
                'lstm_run_id': LSTM run ID,
                'input_size': Input feature count,
                'feature_names': Feature names list,
                'sequence_length': Sliding window length
            }
        """
        logger.info("Loading both LightGBM and LSTM models...")

        try:
            # Load LightGBM model
            lgb_model, lgb_run_id = cls.load_best_lgb_model(lgb_exp)
            logger.info(f"✓ LightGBM model loaded: {lgb_run_id}")

            # Load LSTM model
            lstm_model, lstm_run_id = cls.load_best_lstm_model(lstm_exp, input_size=input_size)
            logger.info(f"✓ LSTM model loaded: {lstm_run_id}")

            # Default feature names if not provided
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(input_size)]

            result = {
                "lgb_model": lgb_model,
                "lgb_run_id": lgb_run_id,
                "lstm_model": lstm_model,
                "lstm_run_id": lstm_run_id,
                "input_size": input_size,
                "feature_names": feature_names,
                "sequence_length": 60,  # From Task #071
            }

            logger.info("✓ Both models successfully loaded!")
            return result

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise


if __name__ == "__main__":
    # Test model loading
    logger.info("Testing ModelLoader...")

    try:
        models = ModelLoader.load_both_models()
        logger.info("Models loaded successfully!")
        logger.info(f"LightGBM run ID: {models['lgb_run_id']}")
        logger.info(f"LSTM run ID: {models['lstm_run_id']}")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        exit(1)
