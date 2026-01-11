#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #069: Baseline Model Training with MLflow Experiment Tracking
Protocol: v4.3 (Zero-Trust Edition)

This script trains a LightGBM baseline model with comprehensive MLflow logging:
1. Logs hyperparameters
2. Logs metrics (accuracy, F1, AUC, log loss)
3. Logs model artifacts and feature importance
4. Performs 5-fold Purged K-Fold cross-validation (prevents look-ahead bias)
5. Saves model for later deployment

Usage:
    python3 scripts/train_baseline.py --dataset outputs/datasets/task_069_dataset.pkl
"""

import os
import sys
import logging
import pickle
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mlflow
import mlflow.lightgbm
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, log_loss, confusion_matrix
from src.models.trainer import LightGBMTrainer
from src.models.validation import PurgedKFold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BaselineModelTrainer:
    """
    Train LightGBM baseline with MLflow experiment tracking.

    Key features:
    - Simple hyperparameters (not tuned, baseline)
    - Purged K-Fold cross-validation (5 folds, 1% embargo)
    - MLflow logging of all parameters and metrics
    - Early stopping with validation set
    """

    def __init__(self, mlflow_uri: str = "http://localhost:5000"):
        """Initialize trainer with MLflow configuration."""
        self.mlflow_uri = mlflow_uri
        self.model = None
        self.scaler = None
        self.results = {}

        # Set MLflow tracking URI
        mlflow.set_tracking_uri(mlflow_uri)

    def log_dataset_info(self, metadata: Dict[str, Any]):
        """Log dataset information as MLflow parameters."""
        logger.info("Logging dataset metadata to MLflow...")

        mlflow.set_tag("dataset.symbol", metadata.get('symbol', 'unknown'))
        mlflow.set_tag("dataset.start_date", metadata.get('start_date', 'unknown'))
        mlflow.set_tag("dataset.end_date", metadata.get('end_date', 'unknown'))
        mlflow.log_param("dataset.train_size", metadata.get('train_size', 0))
        mlflow.log_param("dataset.val_size", metadata.get('val_size', 0))
        mlflow.log_param("dataset.n_features", metadata.get('n_features', 0))
        mlflow.log_param("dataset.scaling_method", metadata.get('scaling_method', 'unknown'))

        # Log label distribution
        train_dist = metadata.get('train_label_dist', {})
        val_dist = metadata.get('val_label_dist', {})

        mlflow.log_param("train.label_-1_count", train_dist.get(-1, 0))
        mlflow.log_param("train.label_0_count", train_dist.get(0, 0))
        mlflow.log_param("train.label_1_count", train_dist.get(1, 0))

        mlflow.log_param("val.label_-1_count", val_dist.get(-1, 0))
        mlflow.log_param("val.label_0_count", val_dist.get(0, 0))
        mlflow.log_param("val.label_1_count", val_dist.get(1, 0))

    def train_baseline(self,
                      X_train: np.ndarray,
                      y_train: np.ndarray,
                      X_val: np.ndarray,
                      y_val: np.ndarray,
                      feature_names: list) -> Dict[str, Any]:
        """
        Train LightGBM baseline model with early stopping.

        Args:
            X_train: Training features (scaled)
            y_train: Training labels
            X_val: Validation features (scaled)
            y_val: Validation labels
            feature_names: List of feature names

        Returns:
            Dictionary with model and metrics
        """
        logger.info("Training LightGBM baseline model...")

        # Baseline hyperparameters (simple, not tuned)
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'lambda_l1': 0.0,
            'lambda_l2': 0.0,
            'min_child_samples': 20,
            'max_depth': 5,
            'verbose': -1,
            'random_state': 42,
        }

        # Log hyperparameters to MLflow
        logger.info("Logging hyperparameters to MLflow...")
        for param_name, param_value in params.items():
            mlflow.log_param(param_name, param_value)

        # Create and train model
        trainer = LightGBMTrainer(params=params, feature_names=feature_names)

        # Convert labels from [-1, 0, 1] to [0, 1] for binary classification
        # -1 and 0 → 0 (no action), 1 → 1 (long signal)
        y_train_binary = (y_train == 1).astype(int)
        y_val_binary = (y_val == 1).astype(int)

        logger.info(f"Training samples: {len(X_train)}")
        logger.info(f"Validation samples: {len(X_val)}")
        logger.info(f"Training label distribution: {np.bincount(y_train_binary)}")

        # Train with early stopping
        train_data = trainer.create_lgb_dataset(X_train, y_train_binary)
        val_data = trainer.create_lgb_dataset(X_val, y_val_binary, reference=train_data)

        trained_model = trainer.train(
            train_data, val_data,
            num_boost_round=500,
            early_stopping_rounds=50,
            verbose_eval=False
        )

        self.model = trained_model

        # Evaluate on validation set
        logger.info("Evaluating on validation set...")
        y_pred_proba = trained_model.predict(X_val)
        y_pred = (y_pred_proba > 0.5).astype(int)

        # Compute metrics
        metrics = {
            'accuracy': accuracy_score(y_val_binary, y_pred),
            'f1_score': f1_score(y_val_binary, y_pred, zero_division=0),
            'auc_roc': roc_auc_score(y_val_binary, y_pred_proba),
            'log_loss': log_loss(y_val_binary, y_pred_proba),
            'best_iteration': trained_model.best_iteration,
        }

        logger.info(f"✅ Model trained")
        logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"F1 Score: {metrics['f1_score']:.4f}")
        logger.info(f"AUC-ROC: {metrics['auc_roc']:.4f}")
        logger.info(f"Log Loss: {metrics['log_loss']:.4f}")
        logger.info(f"Best iteration: {metrics['best_iteration']}")

        # Log metrics to MLflow
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)

        # Log confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_val_binary, y_pred).ravel()
        mlflow.log_param("confusion_matrix.tn", tn)
        mlflow.log_param("confusion_matrix.fp", fp)
        mlflow.log_param("confusion_matrix.fn", fn)
        mlflow.log_param("confusion_matrix.tp", tp)

        # Log feature importance
        logger.info("Logging feature importance...")
        importance = trained_model.feature_importance()
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        # Save and log feature importance as artifact
        importance_path = "feature_importance.csv"
        importance_df.to_csv(importance_path, index=False)
        mlflow.log_artifact(importance_path)
        os.remove(importance_path)

        logger.info(f"Top 5 features:")
        for idx, row in importance_df.head(5).iterrows():
            logger.info(f"  {idx+1}. {row['feature']}: {row['importance']:.2f}")

        return {
            'model': trained_model,
            'metrics': metrics,
            'feature_importance': importance_df,
            'y_pred_proba': y_pred_proba,
            'y_val_binary': y_val_binary
        }

    def cross_validate(self,
                      X: np.ndarray,
                      y: np.ndarray,
                      feature_names: list,
                      n_splits: int = 5) -> Dict[str, Any]:
        """
        Perform 5-fold Purged K-Fold cross-validation.

        Uses Purged K-Fold to prevent look-ahead bias in time-series data.

        Args:
            X: All feature data
            y: All labels
            feature_names: Feature names
            n_splits: Number of folds

        Returns:
            Dictionary with CV metrics
        """
        logger.info("")
        logger.info("Performing Purged K-Fold cross-validation (prevents look-ahead bias)...")

        # Convert labels to binary
        y_binary = (y == 1).astype(int)

        # Initialize Purged K-Fold
        cv = PurgedKFold(n_splits=n_splits, embargo_pct=0.01, purge_overlap=True)

        fold_scores = {
            'accuracy': [],
            'f1_score': [],
            'auc_roc': [],
            'log_loss': [],
        }

        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'max_depth': 5,
            'verbose': -1,
            'random_state': 42,
        }

        # Hyperparameters baseline
        baseline_hyperparams = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'lambda_l1': 0.0,
            'lambda_l2': 0.0,
            'min_child_samples': 20,
            'max_depth': 5,
            'verbose': -1,
            'random_state': 42,
        }

        for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y_binary)):
            logger.info(f"Fold {fold_idx + 1}/{n_splits}...")

            X_train_fold = X[train_idx]
            X_test_fold = X[test_idx]
            y_train_fold = y_binary[train_idx]
            y_test_fold = y_binary[test_idx]

            # Train model for this fold
            trainer = LightGBMTrainer(params=baseline_hyperparams, feature_names=feature_names)

            train_data = trainer.create_lgb_dataset(X_train_fold, y_train_fold)
            test_data = trainer.create_lgb_dataset(X_test_fold, y_test_fold, reference=train_data)

            model = trainer.train(
                train_data, test_data,
                num_boost_round=500,
                early_stopping_rounds=50,
                verbose_eval=False
            )

            # Evaluate
            y_pred_proba = model.predict(X_test_fold)
            y_pred = (y_pred_proba > 0.5).astype(int)

            fold_scores['accuracy'].append(accuracy_score(y_test_fold, y_pred))
            fold_scores['f1_score'].append(f1_score(y_test_fold, y_pred, zero_division=0))
            fold_scores['auc_roc'].append(roc_auc_score(y_test_fold, y_pred_proba))
            fold_scores['log_loss'].append(log_loss(y_test_fold, y_pred_proba))

            logger.info(f"  Accuracy: {fold_scores['accuracy'][-1]:.4f}")
            logger.info(f"  F1 Score: {fold_scores['f1_score'][-1]:.4f}")
            logger.info(f"  AUC-ROC: {fold_scores['auc_roc'][-1]:.4f}")

            # Log fold metrics to MLflow
            mlflow.log_metric('cv_fold_accuracy', fold_scores['accuracy'][-1], step=fold_idx)
            mlflow.log_metric('cv_fold_f1_score', fold_scores['f1_score'][-1], step=fold_idx)
            mlflow.log_metric('cv_fold_auc_roc', fold_scores['auc_roc'][-1], step=fold_idx)

        # Compute and log CV mean/std
        logger.info("")
        logger.info("Cross-validation results:")
        cv_results = {}
        for metric_name, metric_values in fold_scores.items():
            mean_val = np.mean(metric_values)
            std_val = np.std(metric_values)
            cv_results[f'cv_mean_{metric_name}'] = mean_val
            cv_results[f'cv_std_{metric_name}'] = std_val

            logger.info(f"  {metric_name}: {mean_val:.4f} ± {std_val:.4f}")
            mlflow.log_metric(f'cv_mean_{metric_name}', mean_val)
            mlflow.log_metric(f'cv_std_{metric_name}', std_val)

        return cv_results

    def run(self, dataset_path: str, enable_cv: bool = True):
        """
        Run complete baseline training pipeline.

        Args:
            dataset_path: Path to pickled dataset from dataset_builder.py
            enable_cv: Whether to run cross-validation (slower but more robust)

        Returns:
            Exit code (0 for success)
        """
        logger.info("=" * 80)
        logger.info("TASK #069: Baseline Model Training with MLflow")
        logger.info("=" * 80)
        logger.info("")

        # Load dataset
        logger.info(f"Loading dataset from {dataset_path}...")
        try:
            with open(dataset_path, 'rb') as f:
                dataset = pickle.load(f)
        except FileNotFoundError:
            logger.error(f"Dataset not found: {dataset_path}")
            logger.error("Run dataset_builder.py first to generate the dataset")
            return 1

        X_train = dataset['X_train']
        y_train = dataset['y_train']
        X_val = dataset['X_val']
        y_val = dataset['y_val']
        feature_names = dataset['feature_names']
        metadata = dataset['metadata']
        self.scaler = dataset['scaler']

        logger.info(f"✅ Dataset loaded: {len(X_train)} train, {len(X_val)} val")
        logger.info("")

        # Create MLflow experiment
        experiment_name = "task_069_baseline"
        mlflow.set_experiment(experiment_name)

        # Start MLflow run
        with mlflow.start_run() as run:
            logger.info(f"MLflow Run ID: {run.info.run_id}")
            logger.info(f"Experiment: {experiment_name}")
            logger.info("")

            # Set tags
            mlflow.set_tag("task", "task_069")
            mlflow.set_tag("model_type", "lightgbm_baseline")
            mlflow.set_tag("validation_method", "purged_kfold")
            mlflow.set_tag("timestamp", datetime.now().isoformat())

            # Log dataset info
            self.log_dataset_info(metadata)

            # Train baseline
            logger.info("=" * 80)
            logger.info("Training baseline model")
            logger.info("=" * 80)
            baseline_result = self.train_baseline(X_train, y_train, X_val, y_val, feature_names)
            logger.info("")

            # Cross-validation (optional)
            if enable_cv:
                logger.info("=" * 80)
                logger.info("Cross-validation on combined train+val set")
                logger.info("=" * 80)
                cv_results = self.cross_validate(
                    np.vstack([X_train, X_val]),
                    np.concatenate([y_train, y_val]),
                    feature_names,
                    n_splits=5
                )
            else:
                cv_results = {}

            # Log model artifact
            logger.info("")
            logger.info("Logging model artifact to MLflow...")
            mlflow.lightgbm.log_model(
                baseline_result['model'].model,
                artifact_path='model',
                registered_model_name='baseline_lightgbm_task_069'
            )

            # Summary
            logger.info("")
            logger.info("=" * 80)
            logger.info("TRAINING COMPLETE")
            logger.info("=" * 80)
            logger.info(f"MLflow Run ID: {run.info.run_id}")
            logger.info(f"Model accuracy: {baseline_result['metrics']['accuracy']:.4f}")
            logger.info(f"Model AUC-ROC: {baseline_result['metrics']['auc_roc']:.4f}")

            if cv_results:
                logger.info(f"CV mean accuracy: {cv_results.get('cv_mean_accuracy', 0):.4f}")
                logger.info(f"CV mean AUC-ROC: {cv_results.get('cv_mean_auc_roc', 0):.4f}")

            logger.info("")

            # Save results summary
            results_summary = {
                'mlflow_run_id': run.info.run_id,
                'mlflow_experiment': experiment_name,
                'baseline_metrics': baseline_result['metrics'],
                'cv_results': cv_results,
                'feature_importance': baseline_result['feature_importance'].to_dict('records')[:10],
                'metadata': metadata,
            }

            results_file = "outputs/results/task_069_results.json"
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(results_summary, f, indent=2, default=str)

            logger.info(f"✅ Results saved to {results_file}")

        return 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Train baseline model with MLflow tracking')
    parser.add_argument('--dataset', type=str, default='outputs/datasets/task_069_dataset.pkl',
                        help='Path to dataset pickle file')
    parser.add_argument('--mlflow-uri', type=str, default='http://localhost:5000',
                        help='MLflow tracking URI')
    parser.add_argument('--skip-cv', action='store_true',
                        help='Skip cross-validation (faster)')

    args = parser.parse_args()

    trainer = BaselineModelTrainer(mlflow_uri=args.mlflow_uri)
    return trainer.run(args.dataset, enable_cv=not args.skip_cv)


if __name__ == "__main__":
    sys.exit(main())
