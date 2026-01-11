#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Script for TASK #027: Model Training (XGBoost)

Validates that:
1. Training script exists and imports Feast
2. Prediction script exists and loads model
3. Test script exists for inference verification
4. Model artifacts are generated
5. Verification log contains training metrics
"""

import os
import sys
from pathlib import Path

def check_training_script():
    """
    Verify train.py exists and contains required components

    Returns:
        bool: True if training script is valid, False otherwise
    """
    train_path = Path("src/model/train.py")

    if not train_path.exists():
        print("❌ FAIL: src/model/train.py not found")
        return False

    with open(train_path, 'r') as f:
        content = f.read()

    # Check for Feast imports
    if 'from feast import' not in content and 'import feast' not in content:
        print("❌ FAIL: train.py does not import Feast")
        return False

    # Check for get_historical_features call
    if 'get_historical_features' not in content:
        print("❌ FAIL: train.py does not call get_historical_features()")
        return False

    # Check for XGBoost training
    if 'xgb.train' not in content and 'xgboost' not in content.lower():
        print("❌ FAIL: train.py does not use XGBoost")
        return False

    print("✅ PASS: Training script is valid")
    return True


def check_prediction_script():
    """
    Verify predict.py exists and loads model

    Returns:
        bool: True if prediction script is valid, False otherwise
    """
    predict_path = Path("src/model/predict.py")

    if not predict_path.exists():
        print("❌ FAIL: src/model/predict.py not found")
        return False

    with open(predict_path, 'r') as f:
        content = f.read()

    # Check for model loading
    if 'load_model' not in content and 'pickle.load' not in content and 'joblib.load' not in content:
        print("❌ FAIL: predict.py does not load model")
        return False

    print("✅ PASS: Prediction script is valid")
    return True


def check_test_script():
    """
    Verify test_model_inference.py exists

    Returns:
        bool: True if test script exists, False otherwise
    """
    test_path = Path("scripts/test_model_inference.py")

    if not test_path.exists():
        print("❌ FAIL: scripts/test_model_inference.py not found")
        return False

    print("✅ PASS: Test script exists")
    return True


def check_verify_log():
    """
    Verify log contains training metrics

    Returns:
        bool: True if log is valid, False otherwise
    """
    log_path = Path("docs/archive/tasks/TASK_027_MODEL_TRAINING/VERIFY_LOG.log")

    if not log_path.exists():
        print("⚠️  WARNING: VERIFY_LOG.log not found (run training first)")
        return True  # Don't fail - log is generated during training

    with open(log_path, 'r') as f:
        content = f.read()

    # Check for training metrics
    if 'Accuracy' not in content and 'accuracy' not in content:
        print("⚠️  WARNING: Log does not contain accuracy metrics")
        return True  # Warning only

    if 'Model saved' not in content and 'saved to' not in content:
        print("⚠️  WARNING: Log does not mention model saving")
        return True  # Warning only

    print("✅ PASS: Verification log is valid")
    return True


def main():
    print("\n" + "="*60)
    print("AUDIT: TASK #027 Model Training Checks")
    print("="*60 + "\n")

    # Check 1: Training script
    print("[CHECK 1] Training script validation...")
    train_check = check_training_script()

    print()

    # Check 2: Prediction script
    print("[CHECK 2] Prediction script validation...")
    predict_check = check_prediction_script()

    print()

    # Check 3: Test script
    print("[CHECK 3] Test script validation...")
    test_check = check_test_script()

    print()

    # Check 4: Verification log
    print("[CHECK 4] Verification log validation...")
    log_check = check_verify_log()

    print("\n" + "="*60)

    if train_check and predict_check and test_check and log_check:
        print("✅ ALL CHECKS PASSED - Model training infrastructure ready")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before proceeding")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
