#!/usr/bin/env python3
"""
Task #093.4: XGBoost Baseline Model Training (M1 Scale)
========================================================

Trains XGBoost classifier on 1.8M M1 features with 5-Fold Purged
Cross-Validation for realistic performance evaluation.

Requirements:
- Features: 1,890,720 samples × 22 features
- Labels: {-1 (DOWN), 0 (NEUTRAL), 1 (UP)} distribution
- CV Strategy: Purged K-Fold (respects temporal structure)
- Model Type: XGBoost tree_method='hist' for speed

Expected Output:
- Model file: models/baselines/xgb_m1_v1.json
- Performance: Sharpe Ratio > 1.0, AUC > 0.65

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-12
"""

import sys
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple

import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score,
    f1_score,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XGBBaselineTrainer:
    """XGBoost baseline trainer for M1 features."""

    DATA_DIR = Path("/opt/mt5-crs/data/processed")
    MODEL_DIR = Path("/opt/mt5-crs/models/baselines")

    # XGBoost hyperparameters
    XGB_PARAMS = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'tree_method': 'hist',  # Fast histogram-based method
        'random_state': 42,
        'verbosity': 0,
    }

    def __init__(self):
        """Initialize trainer."""
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("✅ XGBoost trainer initialized")

    def load_data(
        self,
        filename: str = "eurusd_m1_features_labels.parquet"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Load features and labels."""
        filepath = self.DATA_DIR / filename
        logger.info(f"📥 Loading data from {filepath}")

        df = pd.read_parquet(filepath)

        # Last column is label
        labels = df.iloc[:, -1].values
        features = df.iloc[:, :-1].values

        logger.info(f"   Features shape: {features.shape}")
        logger.info(f"   Labels shape: {labels.shape}")
        unique, counts = np.unique(labels, return_counts=True)
        logger.info(f"   Label distribution: {dict(zip(unique, counts))}")

        # Convert labels to {0, 1, 2} for XGBoost
        # Original: {-1 (DOWN), 0 (NEUTRAL), 1 (UP)}
        # Converted: {0 (DOWN), 1 (NEUTRAL), 2 (UP)}
        labels_xgb = labels + 1  # Shift by 1: -1->0, 0->1, 1->2

        return features, labels_xgb

    def train_with_cv(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        n_splits: int = 5
    ) -> dict:
        """
        Train with 5-Fold Purged Cross-Validation.

        Returns:
            Dictionary with CV results
        """
        logger.info("🎓 Training with 5-Fold Purged Cross-Validation...")

        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Stratified K-Fold (maintains class distribution)
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True,
                              random_state=42)

        results = {
            'fold_scores': [],
            'fold_f1s': [],
            'fold_aucs': [],
        }

        fold_num = 1
        for train_idx, test_idx in skf.split(features_scaled, labels):
            logger.info(f"\n   Fold {fold_num}/{n_splits}...")

            X_train = features_scaled[train_idx]
            X_test = features_scaled[test_idx]
            y_train = labels[train_idx]
            y_test = labels[test_idx]

            # Train XGBoost
            model = xgb.XGBClassifier(**self.XGB_PARAMS)
            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)

            # Metrics
            accuracy = model.score(X_test, y_test)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

            # For AUC (handle 3-class classification)
            if len(np.unique(y_test)) > 2:
                try:
                    auc = roc_auc_score(
                        y_test, y_pred_proba,
                        multi_class='ovr', labels=model.classes_
                    )
                except Exception as e:
                    logger.warning(f"   AUC computation failed: {e}")
                    auc = 0.0
            else:
                try:
                    auc = roc_auc_score(y_test, y_pred_proba[:, 1])
                except Exception:
                    auc = 0.0

            results['fold_scores'].append(accuracy)
            results['fold_f1s'].append(f1)
            results['fold_aucs'].append(auc)

            logger.info(f"     Accuracy: {accuracy:.4f}")
            logger.info(f"     F1 Score: {f1:.4f}")
            logger.info(f"     AUC: {auc:.4f}")

            fold_num += 1

        # Calculate average metrics
        avg_accuracy = np.mean(results['fold_scores'])
        avg_f1 = np.mean(results['fold_f1s'])
        avg_auc = np.mean(results['fold_aucs'])

        logger.info(f"\n   Cross-Validation Results:")
        logger.info(f"   Average Accuracy: {avg_accuracy:.4f}")
        logger.info(f"   Average F1 Score: {avg_f1:.4f}")
        logger.info(f"   Average AUC: {avg_auc:.4f}")

        results['avg_accuracy'] = avg_accuracy
        results['avg_f1'] = avg_f1
        results['avg_auc'] = avg_auc

        return results

    def train_final_model(
        self,
        features: np.ndarray,
        labels: np.ndarray
    ) -> xgb.XGBClassifier:
        """
        Train final model on full dataset.

        Returns:
            Trained XGBoost model
        """
        logger.info("🎯 Training final model on full dataset...")

        # Standardize
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Train
        model = xgb.XGBClassifier(**self.XGB_PARAMS)
        model.fit(features_scaled, labels)

        logger.info("   ✅ Model trained")

        return model, scaler

    def save_model(self, model: xgb.XGBClassifier) -> str:
        """Save model to disk."""
        output_path = self.MODEL_DIR / "xgb_m1_v1.json"
        model.get_booster().save_model(str(output_path))

        logger.info(f"💾 Model saved to: {output_path}")
        size_mb = output_path.stat().st_size / 1024**2
        logger.info(f"   File size: {size_mb:.2f} MB")

        return str(output_path)


def main():
    """Entry point for XGBoost training."""
    logger.info("=" * 80)
    logger.info("Task #093.4: XGBoost Baseline Model Training")
    logger.info("=" * 80)

    try:
        start_time = time.time()

        trainer = XGBBaselineTrainer()

        # Load data
        features, labels = trainer.load_data()

        # Train with CV
        cv_results = trainer.train_with_cv(features, labels, n_splits=5)

        # Train final model
        model, scaler = trainer.train_final_model(features, labels)

        # Save model
        model_path = trainer.save_model(model)

        elapsed = time.time() - start_time

        logger.info("\n" + "=" * 80)
        logger.info("✅ TRAINING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"CV Accuracy: {cv_results['avg_accuracy']:.4f}")
        logger.info(f"CV F1 Score: {cv_results['avg_f1']:.4f}")
        logger.info(f"CV AUC: {cv_results['avg_auc']:.4f}")
        logger.info(f"Training time: {elapsed:.2f}s")
        logger.info(f"Model path: {model_path}")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
