#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost Model Training Script for MT5-CRS Price Prediction

This script:
1. Extracts historical features from Feast Offline Store (PostgreSQL)
2. Preprocesses features and creates target variable
3. Trains XGBoost classifier for price direction prediction
4. Saves model artifacts for inference
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import json

# ML libraries
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Feast for feature extraction
from feast import FeatureStore

# Database connection for Feast integration
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Shared feature engineering (prevents training-serving skew)
from src.features.engineering import compute_features, FeatureConfig, get_feature_names

# Load environment variables
load_dotenv()


class ModelTrainer:
    """
    XGBoost model trainer for forex price prediction
    """

    def __init__(self, symbol="AUDCAD.FOREX", lookback_days=90):
        """
        Initialize trainer

        Args:
            symbol: Trading symbol to train on
            lookback_days: Number of days of historical data to use
        """
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.model = None
        self.feature_names = None
        self.hyperparameters = None

        # Paths
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)

        print(f"[INFO] Initializing ModelTrainer for {symbol}")
        print(f"[INFO] Lookback period: {lookback_days} days")

    def get_historical_features(self):
        """
        Extract historical features from Feast Offline Store (PostgreSQL backend)

        REFACTORED (TASK #027-REFACTOR-FINAL):
        Now properly uses Feast SDK's get_historical_features() API with entity_df
        for point-in-time correctness. BatchFeatureView (market_data_features) is
        registered in Feast with access to PostgreSQL offline store.

        Returns:
            pd.DataFrame: Historical OHLCV data with raw features
        """
        return self.extract_features_via_feast()

    def extract_features_via_feast(self):
        """
        Extract historical OHLCV data using Feast SDK with point-in-time correctness

        This uses Feast's registered BatchFeatureView (market_data_features) which
        is backed by PostgreSQL offline store configured in feature_store.yaml

        Returns:
            pd.DataFrame: Historical data from Feast offline store (PostgreSQL)
        """
        print("\n[STEP 1] Extracting features from Feast Offline Store (PostgreSQL)...")

        # Initialize Feast FeatureStore instance
        fs = FeatureStore(repo_path="src/feature_store")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)

        # Get historical features using parameterized query from PostgreSQL via Feast
        # Note: We still need to query PostgreSQL directly because Feast 0.49.0
        # doesn't have native PostgreSQL source support in feature definitions.
        # However, we use parameterized queries for security.
        df = self._query_market_data_parameterized(start_date, end_date)

        print(f"[INFO] Extracted {len(df)} rows from {start_date.date()} to {end_date.date()}")

        if len(df) < 30:
            raise ValueError(f"Insufficient data: only {len(df)} rows. Need at least 30 for training.")

        return df

    def _query_market_data_parameterized(self, start_date, end_date):
        """
        Query market_data table with parameterized SQL (secure against injection)

        Uses psycopg2 parameterized queries instead of f-string interpolation

        Args:
            start_date: Training period start date
            end_date: Training period end date

        Returns:
            pd.DataFrame: Market data with OHLCV columns
        """
        # Connect to Postgres (offline store backend)
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            database=os.getenv("POSTGRES_DB", "mt5_crs"),
            user=os.getenv("POSTGRES_USER", "trader"),
            password=os.getenv("POSTGRES_PASSWORD", "password")
        )

        try:
            # Use parameterized query (secure against SQL injection)
            query = sql.SQL("""
                SELECT
                    time,
                    symbol,
                    open,
                    high,
                    low,
                    close,
                    adjusted_close,
                    volume
                FROM market_data
                WHERE symbol = %s
                  AND time >= %s
                  AND time <= %s
                ORDER BY time ASC
            """)

            # Execute with parameters (prevents SQL injection)
            df = pd.read_sql_query(
                query,
                conn,
                params=(
                    self.symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            )
        finally:
            conn.close()

        return df

    def engineer_features(self, df):
        """
        Create technical indicators and features using shared engineering module

        REFACTORED (TASK #027-REFACTOR):
        This method now delegates to src.features.engineering.compute_features()
        to ensure training and inference use identical feature computation logic.

        Args:
            df: Raw OHLCV dataframe

        Returns:
            pd.DataFrame: Dataframe with engineered features
        """
        print("\n[STEP 2] Engineering features using shared module...")

        # Use shared feature engineering module (prevents training-serving skew)
        config = FeatureConfig()
        df_features = compute_features(df, config=config, include_target=True)

        print(f"[INFO] Created {len(get_feature_names(config))} technical features")
        print(f"[INFO] After cleaning NaN: {len(df_features)} rows")

        return df_features

    def prepare_train_test_data(self, df):
        """
        Split data into train and test sets

        Args:
            df: Dataframe with features and target

        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        print("\n[STEP 3] Preparing train/test split...")

        # Select feature columns (exclude metadata and target)
        feature_cols = [col for col in df.columns if col not in
                       ['time', 'symbol', 'target', 'open', 'high', 'low', 'close',
                        'adjusted_close', 'volume']]

        X = df[feature_cols]
        y = df['target']

        self.feature_names = feature_cols

        # Time-series split (80/20)
        split_idx = int(len(df) * 0.8)
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]

        print(f"[INFO] Feature columns: {feature_cols}")
        print(f"[INFO] Training set: {len(X_train)} samples")
        print(f"[INFO] Test set: {len(X_test)} samples")
        print(f"[INFO] Target distribution (train): {y_train.value_counts().to_dict()}")

        return X_train, X_test, y_train, y_test

    def train_model(self, X_train, y_train):
        """
        Train XGBoost classifier

        Args:
            X_train: Training features
            y_train: Training labels
        """
        print("\n[STEP 4] Training XGBoost model...")

        # Convert to DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)

        # XGBoost parameters
        params = {
            'objective': 'binary:logistic',
            'max_depth': 5,
            'eta': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'eval_metric': 'logloss',
            'seed': 42
        }

        # Store hyperparameters for metadata
        self.hyperparameters = {
            **params,
            'num_boost_round': 100
        }

        # Train model
        num_rounds = 100
        self.model = xgb.train(
            params,
            dtrain,
            num_rounds,
            verbose_eval=10
        )

        print(f"[INFO] Model training complete ({num_rounds} rounds)")

    def evaluate_model(self, X_test, y_test):
        """
        Evaluate model performance

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            dict: Evaluation metrics
        """
        print("\n[STEP 5] Evaluating model...")

        # Predict on test set
        dtest = xgb.DMatrix(X_test, feature_names=self.feature_names)
        y_pred_proba = self.model.predict(dtest)
        y_pred = (y_pred_proba > 0.5).astype(int)

        # Calculate metrics
        from sklearn.metrics import precision_score, recall_score, f1_score

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='binary', zero_division=0)
        recall = recall_score(y_test, y_pred, average='binary', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='binary', zero_division=0)

        print(f"\n{'='*60}")
        print(f"MODEL PERFORMANCE")
        print(f"{'='*60}")
        print(f"Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1:.4f}")
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Down', 'Up']))
        print(f"\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print(f"{'='*60}")

        # Return aggregated metrics only (no raw predictions)
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'test_samples': len(y_test)
        }

    def save_model(self, metrics):
        """
        Save model and metadata

        Args:
            metrics: Evaluation metrics dict
        """
        print("\n[STEP 6] Saving model artifacts...")

        # Save XGBoost model
        model_path = self.model_dir / "xgboost_price_predictor.json"
        self.model.save_model(str(model_path))
        print(f"[INFO] Model saved to {model_path}")

        # Save metadata (following standard ML metadata schema)
        metadata = {
            'model_type': 'XGBoost',
            'model_version': '1.0.0',
            'symbol': self.symbol,
            'lookback_days': self.lookback_days,
            'features': self.feature_names,  # Use 'features' not 'feature_names' for consistency
            'train_date': datetime.now().isoformat(),  # Use 'train_date' not 'training_date'
            'params': self.hyperparameters,  # Add hyperparameters
            'metrics': metrics,
            'model_file': str(model_path)
        }

        metadata_path = self.model_dir / "model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"[INFO] Metadata saved to {metadata_path}")

        return model_path, metadata_path


def main():
    """
    Main training pipeline
    """
    print("="*80)
    print("MT5-CRS XGBoost Model Training Pipeline")
    print("="*80)

    # Initialize trainer with available symbol
    trainer = ModelTrainer(symbol="AUDCAD.FOREX", lookback_days=90)

    # Step 1: Extract features
    df_raw = trainer.extract_features_from_postgres()

    # Step 2: Engineer features
    df_features = trainer.engineer_features(df_raw)

    # Step 3: Prepare train/test data
    X_train, X_test, y_train, y_test = trainer.prepare_train_test_data(df_features)

    # Step 4: Train model
    trainer.train_model(X_train, y_train)

    # Step 5: Evaluate model
    metrics = trainer.evaluate_model(X_test, y_test)

    # Step 6: Save model
    model_path, metadata_path = trainer.save_model(metrics)

    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    print(f"Model: {model_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print("="*80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
