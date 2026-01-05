#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Inference Script for MT5-CRS Price Prediction

This script loads the trained XGBoost model and performs inference
on new feature vectors.
"""

import os
import json
from pathlib import Path
import numpy as np
import pandas as pd

import xgboost as xgb

# Shared feature engineering (prevents training-serving skew)
from src.features.engineering import compute_features, FeatureConfig


class PricePredictor:
    """
    Wrapper for XGBoost model inference
    """

    def __init__(self, model_path=None, metadata_path=None):
        """
        Initialize predictor

        Args:
            model_path: Path to saved model file
            metadata_path: Path to model metadata JSON
        """
        # Default paths
        if model_path is None:
            model_path = Path("models/xgboost_price_predictor.json")
        if metadata_path is None:
            metadata_path = Path("models/model_metadata.json")

        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)

        # Load model and metadata
        self.model = None
        self.metadata = None
        self.feature_names = None

        self._load_model()
        self._load_metadata()

    def _load_model(self):
        """Load XGBoost model from disk"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        self.model = xgb.Booster()
        self.model.load_model(str(self.model_path))
        print(f"[INFO] Loaded model from {self.model_path}")

    def _load_metadata(self):
        """Load model metadata"""
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {self.metadata_path}")

        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)

        # Support both old and new field names for backwards compatibility
        self.feature_names = self.metadata.get('features') or self.metadata.get('feature_names', [])
        train_date = self.metadata.get('train_date') or self.metadata.get('training_date', 'Unknown')

        print(f"[INFO] Loaded metadata from {self.metadata_path}")
        print(f"[INFO] Model trained on: {train_date}")
        print(f"[INFO] Test accuracy: {self.metadata.get('metrics', {}).get('accuracy', 'N/A')}")

    def compute_features_from_ohlcv(self, ohlcv_df):
        """
        Compute features from raw OHLCV data using shared engineering module

        REFACTORED (TASK #027-REFACTOR):
        This method ensures inference uses the exact same feature computation
        logic as training, preventing training-serving skew.

        Args:
            ohlcv_df: DataFrame with OHLCV columns (open, high, low, close, volume)

        Returns:
            DataFrame: Features computed using shared module
        """
        config = FeatureConfig()
        features_df = compute_features(ohlcv_df, config=config, include_target=False)
        return features_df

    def predict_from_ohlcv(self, ohlcv_df):
        """
        Predict on raw OHLCV data (most common use case)

        This is the recommended inference method as it ensures features are
        computed consistently with training.

        Args:
            ohlcv_df: DataFrame with OHLCV columns

        Returns:
            dict: Prediction result (single-row input) or list (multi-row input)
        """
        # Compute features using shared module
        features_df = self.compute_features_from_ohlcv(ohlcv_df)

        if len(features_df) == 0:
            raise ValueError("No valid data after feature engineering (all NaN)")

        if len(features_df) == 1:
            # Single row - return dict
            return self.predict(features_df.iloc[-1:])
        else:
            # Multiple rows - return batch results
            return self.predict_batch(features_df)

    def predict(self, features):
        """
        Predict price direction

        Args:
            features: Dict or DataFrame with feature values

        Returns:
            dict: Prediction result with probability
        """
        # Convert dict to DataFrame if needed
        if isinstance(features, dict):
            features = pd.DataFrame([features])

        # Ensure feature order matches training
        if self.feature_names:
            # Reorder columns to match training
            features = features[self.feature_names]

        # Convert to DMatrix
        dmatrix = xgb.DMatrix(features, feature_names=self.feature_names)

        # Predict
        probability = self.model.predict(dmatrix)[0]
        prediction = int(probability > 0.5)

        result = {
            'prediction': prediction,
            'probability': float(probability),
            'direction': 'UP' if prediction == 1 else 'DOWN',
            'confidence': float(abs(probability - 0.5) * 2)  # Scale 0.5-1.0 to 0-1.0
        }

        return result

    def predict_batch(self, features_df):
        """
        Predict on batch of feature vectors

        Args:
            features_df: DataFrame with multiple rows

        Returns:
            list: List of prediction dicts
        """
        # Ensure feature order
        if self.feature_names:
            features_df = features_df[self.feature_names]

        # Convert to DMatrix
        dmatrix = xgb.DMatrix(features_df, feature_names=self.feature_names)

        # Predict
        probabilities = self.model.predict(dmatrix)
        predictions = (probabilities > 0.5).astype(int)

        results = []
        for pred, prob in zip(predictions, probabilities):
            results.append({
                'prediction': int(pred),
                'probability': float(prob),
                'direction': 'UP' if pred == 1 else 'DOWN',
                'confidence': float(abs(prob - 0.5) * 2)
            })

        return results


def main():
    """
    Demo inference script
    """
    print("="*60)
    print("XGBoost Price Predictor - Demo Inference")
    print("="*60)

    # Load predictor
    predictor = PricePredictor()

    # Create sample feature vector (using feature names from metadata)
    sample_features = {}
    for feature_name in predictor.feature_names:
        # Generate random values for demo
        if 'pct' in feature_name or 'rsi' in feature_name:
            sample_features[feature_name] = np.random.uniform(-0.05, 0.05)
        elif 'volume' in feature_name:
            sample_features[feature_name] = np.random.uniform(0, 1000)
        else:
            sample_features[feature_name] = np.random.uniform(1.0, 1.2)

    print("\n[INFO] Sample features (first 5):")
    for i, (key, val) in enumerate(list(sample_features.items())[:5]):
        print(f"  {key}: {val:.6f}")
    print("  ...")

    # Predict
    result = predictor.predict(sample_features)

    print("\n" + "="*60)
    print("PREDICTION RESULT")
    print("="*60)
    print(f"Direction: {result['direction']}")
    print(f"Probability: {result['probability']:.4f}")
    print(f"Confidence: {result['confidence']:.4f}")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
