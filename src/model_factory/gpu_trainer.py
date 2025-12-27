#!/usr/bin/env python3
"""
Work Order #026: GPU-Accelerated Production Trainer
====================================================

Trains high-capacity XGBoost models on deep historical data using GPU acceleration.

Architecture:
1. Load largest available dataset (EURUSD daily + hourly)
2. Advanced feature engineering (80+ technical indicators)
3. Multi-timeframe label generation
4. GPU-accelerated training with heavy trees (5000 estimators, depth 8)
5. Save production model to /opt/mt5-crs/data/models/production_v1.pkl

Protocol: v2.0 (Strict TDD & GPU Training)
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

# ML dependencies
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
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
# GPU Production Trainer
# ============================================================================

class GPUProductionTrainer:
    """
    Production-grade GPU-accelerated XGBoost trainer.

    Features:
    - GPU acceleration with NVIDIA A10
    - Heavy trees (5000 estimators, depth 8)
    - Time series cross-validation
    - Multi-class labels (BUY/HOLD/SELL)
    - Advanced feature engineering
    """

    def __init__(
        self,
        data_dir: str = "/opt/mt5-crs/data/raw",
        model_dir: str = "/opt/mt5-crs/data/models"
    ):
        """
        Initialize GPU trainer.

        Args:
            data_dir: Directory containing raw CSV data
            model_dir: Directory to save trained models
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.feature_engineer = BasicFeatures()
        self.model = None

        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Model directory: {self.model_dir}")

    # ========================================================================
    # Data Loading
    # ========================================================================

    def load_data(self, symbol: str = "EURUSD", period: str = "d") -> pd.DataFrame:
        """
        Load historical data from CSV.

        Args:
            symbol: Symbol name (EURUSD, XAUUSD)
            period: Period ('d' for daily, '1h' for hourly)

        Returns:
            DataFrame with OHLCV data
        """
        csv_file = self.data_dir / f"{symbol}_{period}.csv"

        if not csv_file.exists():
            raise FileNotFoundError(f"Data file not found: {csv_file}")

        logger.info(f"Loading data from: {csv_file}")
        df = pd.read_csv(csv_file)

        # Ensure Date column is datetime
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)

        logger.info(f"✅ Loaded {len(df)} rows")
        logger.info(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")

        return df

    # ========================================================================
    # Feature Engineering
    # ========================================================================

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute advanced features using BasicFeatures.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with computed features
        """
        logger.info("Engineering features...")

        # Rename columns to match BasicFeatures expected format
        df_renamed = df.copy()

        # Map EODHD columns to expected format
        column_mapping = {
            'Date': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        }

        for old_col, new_col in column_mapping.items():
            if old_col in df_renamed.columns:
                df_renamed = df_renamed.rename(columns={old_col: new_col})

        # Compute all basic features
        df_features = self.feature_engineer.compute_all_basic_features(df_renamed)

        # Drop NaN rows
        df_features = df_features.dropna()

        logger.info(f"✅ Features computed: {len(df_features)} rows, {len(df_features.columns)} columns")

        return df_features

    # ========================================================================
    # Label Generation
    # ========================================================================

    def generate_labels(
        self,
        df: pd.DataFrame,
        lookahead: int = 5,
        buy_threshold: float = 0.001,
        sell_threshold: float = -0.001
    ) -> pd.DataFrame:
        """
        Generate multi-class labels (BUY/HOLD/SELL).

        Args:
            df: DataFrame with features
            lookahead: Number of periods to look ahead
            buy_threshold: Threshold for BUY signal (e.g., +0.1%)
            sell_threshold: Threshold for SELL signal (e.g., -0.1%)

        Returns:
            DataFrame with 'label' column (0=SELL, 1=HOLD, 2=BUY)
        """
        logger.info(f"Generating labels (lookahead={lookahead})...")

        df = df.copy()

        # Calculate future return
        df['future_close'] = df['close'].shift(-lookahead)
        df['future_return'] = (df['future_close'] - df['close']) / df['close']

        # Generate multi-class labels
        # BUY (2): Strong positive return
        # HOLD (1): Neutral return
        # SELL (0): Strong negative return
        df['label'] = 1  # Default: HOLD

        df.loc[df['future_return'] > buy_threshold, 'label'] = 2  # BUY
        df.loc[df['future_return'] < sell_threshold, 'label'] = 0  # SELL

        # Drop lookahead rows
        df = df[:-lookahead]

        # Drop temporary columns
        df = df.drop(columns=['future_close', 'future_return'])

        # Class distribution
        class_counts = df['label'].value_counts().sort_index()
        logger.info("✅ Labels generated")
        logger.info(f"   SELL (0): {class_counts.get(0, 0)} ({class_counts.get(0, 0) / len(df) * 100:.1f}%)")
        logger.info(f"   HOLD (1): {class_counts.get(1, 0)} ({class_counts.get(1, 0) / len(df) * 100:.1f}%)")
        logger.info(f"   BUY  (2): {class_counts.get(2, 0)} ({class_counts.get(2, 0) / len(df) * 100:.1f}%)")

        return df

    # ========================================================================
    # GPU Training
    # ========================================================================

    def train_gpu_model(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        n_estimators: int = 5000,
        max_depth: int = 8,
        use_gpu: bool = True
    ) -> dict:
        """
        Train high-capacity XGBoost model with GPU acceleration.

        Args:
            df: DataFrame with features and labels
            test_size: Test set size (default: 0.2)
            n_estimators: Number of trees (default: 5000)
            max_depth: Tree depth (default: 8)
            use_gpu: Use GPU acceleration (default: True)

        Returns:
            Dict with training results and metrics
        """
        logger.info("=" * 70)
        logger.info("🚀 GPU Training Pipeline")
        logger.info("=" * 70)
        print()

        # Prepare data
        logger.info("Preparing training data...")

        # Select numeric features only (exclude timestamp, label, OHLCV)
        feature_cols = [
            col for col in df.columns
            if col not in ['timestamp', 'label', 'open', 'high', 'low', 'close', 'volume', 'Date']
            and df[col].dtype in [np.float64, np.float32, np.int64, np.int32]
        ]

        X = df[feature_cols]
        y = df['label']

        logger.info(f"   Features: {len(feature_cols)} columns")
        logger.info(f"   Samples: {len(X)} rows")
        logger.info(f"   Classes: {y.nunique()} (0=SELL, 1=HOLD, 2=BUY)")

        # Time series split
        logger.info(f"\nSplitting data (test_size={test_size})...")

        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        logger.info(f"   Train size: {len(X_train)} ({len(X_train) / len(X) * 100:.1f}%)")
        logger.info(f"   Test size: {len(X_test)} ({len(X_test) / len(X) * 100:.1f}%)")
        print()

        # Configure GPU training
        logger.info("Configuring XGBoost GPU training...")

        params = {
            'objective': 'multi:softprob',  # Multi-class
            'num_class': 3,  # SELL, HOLD, BUY
            'tree_method': 'gpu_hist' if use_gpu else 'hist',
            'device': 'cuda' if use_gpu else 'cpu',
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'eval_metric': 'mlogloss',
        }

        logger.info(f"   Device: {'GPU (CUDA)' if use_gpu else 'CPU'}")
        logger.info(f"   Trees: {n_estimators}")
        logger.info(f"   Depth: {max_depth}")
        logger.info(f"   Learning rate: {params['learning_rate']}")
        print()

        # Train model
        logger.info("🏋️  Training model...")
        logger.info("   This may take several minutes on GPU...")
        print()

        start_time = datetime.now()

        self.model = xgb.XGBClassifier(**params)
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            verbose=100  # Log every 100 iterations
        )

        end_time = datetime.now()
        training_time = (end_time - start_time).total_seconds()

        logger.info(f"\n✅ Training complete ({training_time:.1f}s)")
        print()

        # Evaluate
        logger.info("Evaluating model...")

        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)

        logger.info(f"   Train accuracy: {train_acc:.4f}")
        logger.info(f"   Test accuracy: {test_acc:.4f}")
        print()

        logger.info("Classification Report (Test Set):")
        print(classification_report(
            y_test,
            y_pred_test,
            target_names=['SELL', 'HOLD', 'BUY'],
            digits=4
        ))
        print()

        # Save results
        results = {
            'model': self.model,
            'feature_cols': feature_cols,
            'train_acc': train_acc,
            'test_acc': test_acc,
            'training_time': training_time,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'n_features': len(feature_cols),
            'n_samples': len(X),
        }

        return results

    # ========================================================================
    # Model Persistence
    # ========================================================================

    def save_model(self, output_path: Optional[str] = None) -> str:
        """
        Save trained model to disk.

        Args:
            output_path: Path to save model (default: data/models/production_v1.pkl)

        Returns:
            Path to saved model file
        """
        if self.model is None:
            raise ValueError("No model trained. Call train_gpu_model() first.")

        if output_path is None:
            output_path = self.model_dir / "production_v1.pkl"
        else:
            output_path = Path(output_path)

        logger.info(f"Saving model to: {output_path}")

        with open(output_path, 'wb') as f:
            pickle.dump(self.model, f)

        file_size = output_path.stat().st_size
        logger.info(f"✅ Model saved ({file_size / 1024 / 1024:.1f} MB)")

        return str(output_path)


# ============================================================================
# Direct Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 GPU Production Trainer - Direct Execution")
    print("=" * 70)
    print()

    try:
        # Initialize trainer
        trainer = GPUProductionTrainer()

        # Load EURUSD daily data
        df = trainer.load_data(symbol="EURUSD", period="d")

        # Engineer features
        df_features = trainer.engineer_features(df)

        # Generate labels
        df_labeled = trainer.generate_labels(df_features)

        # Train model
        results = trainer.train_gpu_model(df_labeled)

        # Save model
        model_path = trainer.save_model()

        print()
        print("=" * 70)
        print("✅ PRODUCTION MODEL TRAINING COMPLETE")
        print("=" * 70)
        print()
        print(f"Model file: {model_path}")
        print(f"Train accuracy: {results['train_acc']:.4f}")
        print(f"Test accuracy: {results['test_acc']:.4f}")
        print(f"Training time: {results['training_time']:.1f}s")
        print(f"Features: {results['n_features']}")
        print(f"Samples: {results['n_samples']}")
        print()

    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
