#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #072: Ensemble Evaluation Script

Evaluate and compare LightGBM, LSTM, and Ensemble predictions

Protocol v4.3 (Zero-Trust Edition)
"""

import os
import sys
import pickle
import logging
import numpy as np
import torch
import mlflow
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model.ensemble.loader import ModelLoader
from src.model.ensemble.predictors import LGBPredictor, LSTMPredictor
from src.model.ensemble.alignment import DataAlignmentHandler
from src.model.ensemble.ensemble import EnsemblePredictor


def load_dataset():
    """Load training dataset from Task #069"""
    dataset_path = Path("outputs/datasets/task_069_dataset.pkl")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with open(dataset_path, 'rb') as f:
        dataset = pickle.load(f)

    logger.info(f"Loaded dataset: {dataset.keys()}")
    return dataset


def create_sliding_window_dataset(X, y, sequence_length=60, stride=1):
    """Create sliding window sequences for LSTM"""
    num_windows = (len(X) - sequence_length) // stride + 1
    X_windows = np.array([
        X[i*stride:i*stride + sequence_length]
        for i in range(num_windows)
    ])
    # Labels correspond to the last element of each window
    y_windows = y[sequence_length - 1::stride][:num_windows]
    return X_windows, y_windows


def compute_metrics(y_true, y_pred, y_proba):
    """Compute classification metrics"""
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'f1_weighted': f1_score(y_true, y_pred, average='weighted', zero_division=0),
        'auc_roc': roc_auc_score(y_true, y_proba, multi_class='ovr', zero_division=0),
    }


def evaluate_ensemble():
    """Main evaluation pipeline"""
    logger.info("=" * 70)
    logger.info("Task #072: Ensemble Inference Engine Evaluation")
    logger.info("=" * 70)

    try:
        # Load dataset
        logger.info("\n1. Loading dataset...")
        dataset = load_dataset()
        X_train = dataset['X_train']
        y_train = dataset['y_train']
        X_val = dataset['X_val']
        y_val = dataset['y_val']
        feature_names = dataset['feature_names']

        logger.info(f"   Train: {X_train.shape}, Val: {X_val.shape}")

        # Create sliding windows for LSTM
        logger.info("\n2. Creating sliding window sequences...")
        X_val_windows, y_val_windows = create_sliding_window_dataset(X_val, y_val, sequence_length=60)
        logger.info(f"   LSTM windows: {X_val_windows.shape}")

        # Load models from MLflow
        logger.info("\n3. Loading models from MLflow...")
        models = ModelLoader.load_both_models(feature_names=feature_names)
        logger.info(f"   ✓ LightGBM run: {models['lgb_run_id']}")
        logger.info(f"   ✓ LSTM run: {models['lstm_run_id']}")

        # Create predictors
        logger.info("\n4. Creating prediction wrappers...")
        lgb_pred = LGBPredictor(models['lgb_model'], feature_names=feature_names)
        lstm_pred = LSTMPredictor(models['lstm_model'], device='cpu')
        alignment = DataAlignmentHandler(sequence_length=60, stride=1)
        ensemble = EnsemblePredictor(
            lgb_pred, lstm_pred, alignment,
            weights=(0.5, 0.5),
            use_stacking=False
        )

        # Generate predictions
        logger.info("\n5. Generating predictions...")
        lgb_proba = lgb_pred.predict_proba(X_val)
        lstm_proba = lstm_pred.predict_proba(torch.FloatTensor(X_val_windows))
        ensemble_proba = ensemble.predict_proba(X_val, torch.FloatTensor(X_val_windows))

        logger.info(f"   LGB shape: {lgb_proba.shape}")
        logger.info(f"   LSTM shape: {lstm_proba.shape}")
        logger.info(f"   Ensemble shape: {ensemble_proba.shape}")

        # Get aligned labels
        valid_idx = alignment.get_valid_indices(len(y_val))
        y_val_aligned = y_val[valid_idx]

        # Compute metrics
        logger.info("\n6. Computing metrics...")
        metrics_lgb = compute_metrics(
            y_val_aligned,
            np.argmax(lgb_proba[valid_idx], axis=1),
            lgb_proba[valid_idx]
        )
        metrics_lstm = compute_metrics(
            y_val_aligned,
            np.argmax(lstm_proba, axis=1),
            lstm_proba
        )
        metrics_ensemble = compute_metrics(
            y_val_aligned,
            np.argmax(ensemble_proba, axis=1),
            ensemble_proba
        )

        # Log to MLflow
        logger.info("\n7. Logging results to MLflow...")
        mlflow.set_experiment("task_072_ensemble")

        with mlflow.start_run(run_name=f"ensemble_{datetime.now().isoformat()}") as run:
            # Log parameters
            mlflow.log_params({
                'strategy': 'weighted_average',
                'lgb_weight': 0.5,
                'lstm_weight': 0.5,
                'sequence_length': 60,
                'lgb_run_id': models['lgb_run_id'],
                'lstm_run_id': models['lstm_run_id'],
            })

            # Log metrics
            for model_name, metrics in [
                ('lgb', metrics_lgb),
                ('lstm', metrics_lstm),
                ('ensemble', metrics_ensemble)
            ]:
                for metric_name, metric_value in metrics.items():
                    mlflow.log_metric(f'{model_name}_{metric_name}', metric_value)

            # Log comparison report
            report = generate_report(metrics_lgb, metrics_lstm, metrics_ensemble)
            mlflow.log_text(report, artifact_file='comparison_report.txt')

            logger.info(f"   ✓ Results logged to MLflow run: {run.info.run_id}")

        # Display results
        logger.info("\n" + "=" * 70)
        logger.info("EVALUATION RESULTS")
        logger.info("=" * 70)
        logger.info(report)

        return metrics_lgb, metrics_lstm, metrics_ensemble

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise


def generate_report(metrics_lgb, metrics_lstm, metrics_ensemble):
    """Generate formatted comparison report"""
    best_acc = max(metrics_lgb['accuracy'], metrics_lstm['accuracy'])
    ensemble_acc = metrics_ensemble['accuracy']
    improvement = (ensemble_acc - best_acc) * 100

    report = f"""
╔═══════════════════════════════════════════════════════════════════╗
║              Model Performance Comparison                        ║
╚═══════════════════════════════════════════════════════════════════╝

LightGBM Baseline:
  Accuracy:      {metrics_lgb['accuracy']:.4f}
  F1-Score:      {metrics_lgb['f1_weighted']:.4f}
  AUC-ROC:       {metrics_lgb['auc_roc']:.4f}

LSTM (Optimized):
  Accuracy:      {metrics_lstm['accuracy']:.4f}
  F1-Score:      {metrics_lstm['f1_weighted']:.4f}
  AUC-ROC:       {metrics_lstm['auc_roc']:.4f}

Ensemble (50/50 Weighted Average):
  Accuracy:      {metrics_ensemble['accuracy']:.4f}
  F1-Score:      {metrics_ensemble['f1_weighted']:.4f}
  AUC-ROC:       {metrics_ensemble['auc_roc']:.4f}

Ensemble Performance:
  Best Individual Accuracy: {best_acc:.4f}
  Ensemble Accuracy:        {ensemble_acc:.4f}
  Improvement:              {improvement:+.2f}%

╚═══════════════════════════════════════════════════════════════════╝
"""
    return report


if __name__ == '__main__':
    try:
        metrics_lgb, metrics_lstm, metrics_ensemble = evaluate_ensemble()
        logger.info("\n✓ Ensemble evaluation complete!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
