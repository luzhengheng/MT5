#!/usr/bin/env python3
"""
Work Order #025: Baseline Model Pipeline & Deployment
=======================================================

Baseline Model Trainer - Reproducible Training Pipeline

This module creates a synthetic baseline model to verify the LiveStrategyAdapter
loading logic. It generates synthetic OHLCV data, computes features, trains a
simple XGBoost classifier, and saves it to a .pkl file.

Architecture:
    1. Generate synthetic OHLCV data (1000 rows)
    2. Compute features using BasicFeatures
    3. Generate synthetic labels (BUY/SELL)
    4. Train XGBClassifier with small parameters
    5. Save to data/models/baseline_v1.pkl

Protocol: v2.0 (Strict TDD & Reproducible ML)
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional
import pickle
from datetime import datetime, timedelta

# ML dependencies
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

# Feature engineering
from src.feature_engineering.basic_features import BasicFeatures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Synthetic Data Generation
# ============================================================================

def generate_synthetic_ohlcv(n_rows: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for model training.

    Args:
        n_rows: Number of rows to generate (default: 1000)
        seed: Random seed for reproducibility (default: 42)

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume

    Logic:
        - Start price: 1.0850 (EURUSD typical level)
        - Random walk with small increments
        - High/Low derived from open/close with noise
        - Volume generated with normal distribution
    """
    np.random.seed(seed)
    logger.info(f"Generating {n_rows} rows of synthetic OHLCV data...")

    # Generate timestamps (1-minute intervals)
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(n_rows)]

    # Generate price data (random walk)
    start_price = 1.0850
    price_changes = np.random.normal(0, 0.0002, n_rows)  # Small increments
    close_prices = start_price + np.cumsum(price_changes)

    # Generate open prices (slight offset from close)
    open_prices = close_prices + np.random.normal(0, 0.0001, n_rows)

    # Generate high/low (must contain open and close)
    highs = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.0001, n_rows))
    lows = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.0001, n_rows))

    # Generate volume (normal distribution around 1000)
    volumes = np.random.normal(1000, 200, n_rows).astype(int)
    volumes = np.maximum(volumes, 100)  # Minimum volume

    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': open_prices,
        'high': highs,
        'low': lows,
        'close': close_prices,
        'volume': volumes
    })

    logger.info(f"✅ Generated {len(df)} rows")
    logger.info(f"   Price range: {df['close'].min():.5f} - {df['close'].max():.5f}")
    logger.info(f"   Volume range: {df['volume'].min()} - {df['volume'].max()}")

    return df


# ============================================================================
# Feature Engineering
# ============================================================================

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute basic features from OHLCV data.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with computed features

    Features:
        - SMA (5, 10, 20 periods)
        - EMA (5, 10, 20 periods)
        - Returns (1, 5, 10 periods)
        - Volatility (rolling std)
        - Volume changes
    """
    logger.info("Computing features...")

    # Use BasicFeatures for feature computation
    basic_features = BasicFeatures()
    df_with_features = basic_features.compute_all_basic_features(df.copy())

    # Drop any NaN rows (due to rolling windows)
    df_with_features = df_with_features.dropna()

    logger.info(f"✅ Features computed: {len(df_with_features)} rows, {len(df_with_features.columns)} columns")

    return df_with_features


# ============================================================================
# Label Generation
# ============================================================================

def generate_labels(df: pd.DataFrame, lookahead: int = 5) -> pd.DataFrame:
    """
    Generate synthetic labels (BUY/SELL) based on future price movement.

    Args:
        df: DataFrame with features
        lookahead: Number of periods to look ahead (default: 5)

    Returns:
        DataFrame with 'label' column added

    Logic:
        - BUY (1): If price increases by > 0.0005 in next N periods
        - SELL (0): Otherwise
    """
    logger.info(f"Generating labels (lookahead={lookahead})...")

    df = df.copy()

    # Calculate future return
    df['future_close'] = df['close'].shift(-lookahead)
    df['future_return'] = (df['future_close'] - df['close']) / df['close']

    # Generate labels
    threshold = 0.0005  # 50 pips for EURUSD
    df['label'] = (df['future_return'] > threshold).astype(int)

    # Drop lookahead rows (no labels available)
    df = df[:-lookahead]

    # Drop temporary columns
    df = df.drop(columns=['future_close', 'future_return'])

    logger.info(f"✅ Labels generated")
    logger.info(f"   BUY signals: {(df['label'] == 1).sum()} ({(df['label'] == 1).mean() * 100:.1f}%)")
    logger.info(f"   SELL signals: {(df['label'] == 0).sum()} ({(df['label'] == 0).mean() * 100:.1f}%)")

    return df


# ============================================================================
# Model Training
# ============================================================================

def train_baseline_model(output_path: Optional[str] = None) -> str:
    """
    Train a baseline XGBoost model on synthetic data.

    Args:
        output_path: Path to save model (default: data/models/baseline_v1.pkl)

    Returns:
        Path to saved model file

    Workflow:
        1. Generate synthetic OHLCV data
        2. Compute features
        3. Generate labels
        4. Train/test split
        5. Train XGBoost classifier
        6. Evaluate performance
        7. Save model to .pkl file

    Model Parameters:
        - max_depth: 3 (small trees for quick training)
        - n_estimators: 50 (few trees for baseline)
        - learning_rate: 0.1
        - objective: binary:logistic
    """
    logger.info("=" * 70)
    logger.info("🏗️  Baseline Model Training Pipeline")
    logger.info("=" * 70)
    print()

    # Determine output path
    if output_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        output_path = project_root / "data" / "models" / "baseline_v1.pkl"
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Generate synthetic OHLCV data
        logger.info("Step 1/6: Generating synthetic OHLCV data...")
        df_ohlcv = generate_synthetic_ohlcv(n_rows=1000, seed=42)
        print()

        # Step 2: Compute features
        logger.info("Step 2/6: Computing features...")
        df_features = compute_features(df_ohlcv)
        print()

        # Step 3: Generate labels
        logger.info("Step 3/6: Generating labels...")
        df_labeled = generate_labels(df_features, lookahead=5)
        print()

        # Step 4: Prepare training data
        logger.info("Step 4/6: Preparing training data...")

        # Select numeric features only (drop timestamp, label)
        feature_cols = [col for col in df_labeled.columns
                       if col not in ['timestamp', 'label', 'open', 'high', 'low', 'close', 'volume']]

        X = df_labeled[feature_cols]
        y = df_labeled['label']

        logger.info(f"   Features: {len(feature_cols)} columns")
        logger.info(f"   Samples: {len(X)} rows")
        logger.info(f"   Class distribution: BUY={y.sum()}, SELL={(~y.astype(bool)).sum()}")

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        logger.info(f"   Train size: {len(X_train)}")
        logger.info(f"   Test size: {len(X_test)}")
        print()

        # Step 5: Train model
        logger.info("Step 5/6: Training XGBoost classifier...")

        model = xgb.XGBClassifier(
            max_depth=3,
            n_estimators=50,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )

        model.fit(X_train, y_train, verbose=False)
        logger.info("✅ Model trained")
        print()

        # Step 6: Evaluate
        logger.info("Step 6/6: Evaluating model...")

        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)

        logger.info(f"   Train accuracy: {train_acc:.3f}")
        logger.info(f"   Test accuracy: {test_acc:.3f}")
        print()

        logger.info("Classification Report (Test Set):")
        print(classification_report(y_test, y_pred_test, target_names=['SELL', 'BUY']))
        print()

        # Step 7: Save model
        logger.info(f"Saving model to: {output_path}")

        with open(output_path, 'wb') as f:
            pickle.dump(model, f)

        logger.info(f"✅ Model saved ({output_path.stat().st_size / 1024:.1f} KB)")
        print()

        # Final summary
        print("=" * 70)
        print("✅ BASELINE MODEL TRAINING COMPLETE")
        print("=" * 70)
        print()
        print(f"Model file: {output_path}")
        print(f"Train accuracy: {train_acc:.3f}")
        print(f"Test accuracy: {test_acc:.3f}")
        print(f"Features: {len(feature_cols)}")
        print()

        return str(output_path)

    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        raise


# ============================================================================
# Direct Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🏗️  Baseline Model Trainer - Direct Execution")
    print("=" * 70)
    print()

    try:
        model_path = train_baseline_model()
        print(f"✅ Success! Model saved to: {model_path}")
        print()

    except Exception as e:
        print(f"❌ Training failed: {e}")
        import sys
        sys.exit(1)
