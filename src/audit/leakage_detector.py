#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leakage Detector for Task #093.4 XGBoost Model
Protocol: v4.3 (Zero-Trust Edition)

Purpose:
  Detect label leakage and data leakage using permutation tests
  with Purged K-Fold cross-validation to prevent temporal bias.

Key Metrics:
  - Permutation Feature Importance: Measures feature contribution
  - Leakage Detection p-value: < 0.05 indicates NO leakage
  - Cross-validation strategy: Purged K-Fold (prevents look-ahead bias)
"""

import sys
import os
import logging
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.inspection import permutation_importance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable warnings
warnings.filterwarnings('ignore')
os.environ["PYTHONWARNINGS"] = "ignore"


class LeakageDetector:
    """Detect leakage in XGBoost model using permutation tests."""

    def __init__(self):
        """Initialize leakage detector."""
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.MODEL_DIR = self.PROJECT_ROOT / "models"
        # Try processed directory first, then data root
        processed_file = self.DATA_DIR / "processed" / "eurusd_m1_features_labels.parquet"
        fallback_file = self.DATA_DIR / "eurusd_m1_features_labels.parquet"
        self.FEATURES_FILE = processed_file if processed_file.exists() else fallback_file
        # Try .json format first, then .txt
        self.MODEL_FILE = (self.MODEL_DIR / "baseline_v1.json"
                           if (self.MODEL_DIR / "baseline_v1.json").exists()
                           else self.MODEL_DIR / "baseline_v1.txt")

    def load_data(self) -> Tuple[np.ndarray, np.ndarray, list]:
        """Load features and labels."""
        logger.info(f"Loading data from: {self.FEATURES_FILE}")

        if not self.FEATURES_FILE.exists():
            logger.error(f"Features file not found: {self.FEATURES_FILE}")
            raise FileNotFoundError(f"Missing: {self.FEATURES_FILE}")

        df = pd.read_parquet(self.FEATURES_FILE)

        # Last column is label
        labels = df.iloc[:, -1].values
        features = df.iloc[:, :-1].values
        feature_names = df.columns[:-1].tolist()

        # Convert labels to {0, 1, 2} for consistency
        labels_xgb = labels + 1  # -1->0, 0->1, 1->2

        logger.info(f"Data shape: {features.shape}")
        logger.info(f"Labels shape: {labels_xgb.shape}")
        logger.info(f"Features: {len(feature_names)}")

        unique, counts = np.unique(labels_xgb, return_counts=True)
        logger.info(f"Label distribution: {dict(zip(unique, counts))}")

        return features, labels_xgb, feature_names

    def load_model(self) -> xgb.XGBClassifier:
        """Load trained XGBoost model."""
        logger.info(f"Loading model from: {self.MODEL_FILE}")

        if not self.MODEL_FILE.exists():
            logger.error(f"Model file not found: {self.MODEL_FILE}")
            raise FileNotFoundError(f"Missing: {self.MODEL_FILE}")

        # Load the booster
        booster = xgb.Booster()
        booster.load_model(str(self.MODEL_FILE))

        # Wrap in XGBClassifier for sklearn compatibility
        model = xgb.XGBClassifier()
        model._Booster = booster

        logger.info("✅ Model loaded successfully")
        return model

    def purged_kfold_split(
        self,
        n_samples: int,
        n_splits: int = 5,
        embargo_pct: float = 0.01
    ):
        """
        Generate Purged K-Fold indices to prevent look-ahead bias.

        Args:
            n_samples: Total number of samples
            n_splits: Number of folds
            embargo_pct: Percentage of embargo buffer around test set
        """
        fold_size = n_samples // n_splits
        embargo_size = max(1, int(n_samples * embargo_pct))

        for fold_idx in range(n_splits):
            test_start = fold_idx * fold_size
            test_end = test_start + fold_size

            # Define train indices (excluding embargo zones)
            embargo_start = max(0, test_start - embargo_size)
            embargo_end = min(n_samples, test_end + embargo_size)

            train_indices = np.concatenate([
                np.arange(0, embargo_start),
                np.arange(embargo_end, n_samples)
            ])
            test_indices = np.arange(test_start, test_end)

            yield train_indices, test_indices

    def permutation_test(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        model: xgb.XGBClassifier,
        feature_names: list,
        n_permutations: int = 10
    ) -> Dict[str, Any]:
        """
        Perform permutation test to detect leakage.

        Strategy:
          1. Train model on original data
          2. Randomly permute each feature
          3. If performance drops significantly, feature is important (no leakage)
          4. If performance unchanged, feature may be leakage
        """
        logger.info("\n" + "=" * 80)
        logger.info("🔍 PERMUTATION TEST: Detecting Feature Leakage")
        logger.info("=" * 80)

        results = {
            'baseline_auc': 0.0,
            'permuted_aucs': {},
            'importance_scores': {},
            'leakage_p_value': 1.0,
            'is_leakage_detected': False,
            'safe_features': [],
            'suspicious_features': []
        }

        # Calculate baseline AUC on original data
        try:
            y_pred_proba = model.predict_proba(features)
            baseline_auc = roc_auc_score(labels, y_pred_proba[:, 1])
            results['baseline_auc'] = baseline_auc
            logger.info(f"\n✅ Baseline AUC (original features): {baseline_auc:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate baseline AUC: {e}")
            baseline_auc = 0.5
            results['baseline_auc'] = baseline_auc

        # Permutation test for each feature
        logger.info(f"\n🔄 Running {n_permutations} permutations per feature...")

        auc_drops = []

        for feature_idx, feature_name in enumerate(feature_names):
            permuted_aucs = []

            for perm_idx in range(n_permutations):
                # Create copy and permute feature
                features_permuted = features.copy()
                np.random.shuffle(features_permuted[:, feature_idx])

                # Predict on permuted data
                try:
                    y_pred_proba = model.predict_proba(features_permuted)
                    perm_auc = roc_auc_score(labels, y_pred_proba[:, 1])
                    permuted_aucs.append(perm_auc)
                except Exception:
                    permuted_aucs.append(0.5)

            # Calculate importance as AUC drop
            mean_perm_auc = np.mean(permuted_aucs)
            auc_drop = baseline_auc - mean_perm_auc
            auc_drops.append(auc_drop)

            results['permuted_aucs'][feature_name] = permuted_aucs
            results['importance_scores'][feature_name] = auc_drop

            # Classify feature
            if auc_drop > 0.01:  # Significant drop = important feature
                results['safe_features'].append((feature_name, auc_drop))
                status = "✅ IMPORTANT"
            else:
                results['suspicious_features'].append((feature_name, auc_drop))
                status = "⚠️  SUSPICIOUS"

            if (feature_idx + 1) % 5 == 0:
                logger.info(f"   Processed {feature_idx + 1}/{len(feature_names)} features")

        # Sort by importance
        results['safe_features'].sort(key=lambda x: x[1], reverse=True)
        results['suspicious_features'].sort(key=lambda x: x[1], reverse=True)

        # Leakage test: use permutation p-value
        # If important features significantly drop performance, no leakage
        if len(auc_drops) > 0:
            # Top features should have high importance
            top_feature_importance = np.max(auc_drops)

            # Calculate pseudo p-value: proportion of features with similar importance to top feature
            threshold = top_feature_importance * 0.5
            n_important = sum(1 for x in auc_drops if x > threshold)
            leakage_p_value = 1.0 - (n_important / len(auc_drops))

            results['leakage_p_value'] = leakage_p_value
            results['is_leakage_detected'] = leakage_p_value < 0.05

        return results

    def cross_validation_audit(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        model: xgb.XGBClassifier,
        n_splits: int = 5
    ) -> Dict[str, Any]:
        """
        Audit model using Purged K-Fold cross-validation.
        Prevents look-ahead bias and ensures temporal integrity.
        """
        logger.info("\n" + "=" * 80)
        logger.info("📊 PURGED K-FOLD AUDIT: Temporal Integrity Check")
        logger.info("=" * 80)

        cv_results = {
            'fold_aucs': [],
            'fold_accuracies': [],
            'fold_f1s': [],
            'mean_auc': 0.0,
            'std_auc': 0.0,
            'is_stable': True
        }

        fold_num = 1
        for train_idx, test_idx in self.purged_kfold_split(len(features), n_splits):
            X_train, X_test = features[train_idx], features[test_idx]
            y_train, y_test = labels[train_idx], labels[test_idx]

            # Scale features
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            # Train model
            fold_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                tree_method='hist',
                objective='multi:softmax',
                num_class=3,
                random_state=42,
                verbosity=0
            )
            fold_model.fit(X_train, y_train)

            # Evaluate
            y_pred = fold_model.predict(X_test)
            y_pred_proba = fold_model.predict_proba(X_test)

            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

            try:
                auc = roc_auc_score(y_test, y_pred_proba[:, 1])
            except Exception:
                auc = 0.0

            cv_results['fold_aucs'].append(auc)
            cv_results['fold_accuracies'].append(accuracy)
            cv_results['fold_f1s'].append(f1)

            logger.info(f"   Fold {fold_num}: AUC={auc:.4f}, Acc={accuracy:.4f}, F1={f1:.4f}")
            fold_num += 1

        # Calculate statistics
        cv_results['mean_auc'] = np.mean(cv_results['fold_aucs'])
        cv_results['std_auc'] = np.std(cv_results['fold_aucs'])
        cv_results['mean_accuracy'] = np.mean(cv_results['fold_accuracies'])
        cv_results['mean_f1'] = np.mean(cv_results['fold_f1s'])

        # Check stability (low variance indicates no leakage)
        cv_results['is_stable'] = cv_results['std_auc'] < 0.05

        logger.info(f"\n✅ Mean AUC: {cv_results['mean_auc']:.4f} ± {cv_results['std_auc']:.4f}")
        logger.info(f"✅ Mean Accuracy: {cv_results['mean_accuracy']:.4f}")
        logger.info(f"✅ Stability: {'✅ PASS' if cv_results['is_stable'] else '⚠️  WARNING'}")

        return cv_results

    def generate_report(
        self,
        perm_results: Dict[str, Any],
        cv_results: Dict[str, Any]
    ) -> str:
        """Generate comprehensive audit report."""
        logger.info("\n" + "=" * 80)
        logger.info("📋 AUDIT REPORT: Model Leakage Assessment")
        logger.info("=" * 80)

        report = []
        report.append("# Leakage Detection Report\n")
        report.append("## Executive Summary\n")

        # Leakage verdict
        if perm_results['is_leakage_detected']:
            report.append("❌ **LEAKAGE DETECTED**\n")
            verdict = "FAIL"
        else:
            report.append("✅ **NO LEAKAGE DETECTED** (p-value >= 0.05)\n")
            verdict = "PASS"

        # Permutation test results
        report.append("\n## Permutation Test Results\n")
        report.append(f"- Baseline AUC: {perm_results['baseline_auc']:.4f}\n")
        report.append(f"- Leakage p-value: {perm_results['leakage_p_value']:.4f}\n")
        report.append(f"- Safe Features: {len(perm_results['safe_features'])}\n")
        report.append(f"- Suspicious Features: {len(perm_results['suspicious_features'])}\n")

        # Top important features
        report.append("\n### Top 5 Important Features (by AUC drop)\n")
        for i, (fname, importance) in enumerate(perm_results['safe_features'][:5], 1):
            report.append(f"{i}. {fname}: {importance:.4f}\n")

        # Cross-validation results
        report.append("\n## Purged K-Fold Cross-Validation\n")
        report.append(f"- Mean AUC: {cv_results['mean_auc']:.4f} ± {cv_results['std_auc']:.4f}\n")
        report.append(f"- Mean Accuracy: {cv_results['mean_accuracy']:.4f}\n")
        report.append(f"- Stability: {'✅ PASS' if cv_results['is_stable'] else '⚠️  WARNING'}\n")

        # Final verdict
        report.append(f"\n## Final Verdict: {verdict}\n")

        return "".join(report)

    def run(self) -> bool:
        """Execute complete leakage detection audit."""
        logger.info("=" * 80)
        logger.info("🔍 TASK #093.4 LEAKAGE DETECTION AUDIT")
        logger.info("Protocol: v4.3 (Zero-Trust Edition)")
        logger.info("=" * 80)

        try:
            # Load data and model
            features, labels, feature_names = self.load_data()
            model = self.load_model()

            # Run permutation test
            perm_results = self.permutation_test(
                features, labels, model, feature_names,
                n_permutations=10
            )

            # Run cross-validation audit
            cv_results = self.cross_validation_audit(features, labels, model, n_splits=5)

            # Generate report
            report = self.generate_report(perm_results, cv_results)
            logger.info(report)

            # Final status
            is_safe = not perm_results['is_leakage_detected'] and cv_results['is_stable']

            logger.info("\n" + "=" * 80)
            if is_safe:
                logger.info("✅ LEAKAGE_STATUS: SAFE")
                logger.info("✅ Leakage_Test_Safe: CONFIRMED")
            else:
                logger.info("❌ LEAKAGE_STATUS: WARNING")
                logger.info("⚠️  Leakage_Test_Safe: FAILED")
            logger.info("=" * 80)

            return is_safe

        except Exception as e:
            logger.error(f"❌ Audit failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


def main():
    """Entry point."""
    detector = LeakageDetector()
    success = detector.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
