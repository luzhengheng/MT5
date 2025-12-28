"""
ML Training Pipeline - XGBoost Baseline Model

Task #039: ML Training Pipeline

Provides ModelTrainer class for building binary classification models
to predict price direction (up/down) using technical indicators from Task #038.

Data Flow:
    Load OHLCV → Engineer Features → Create Target → Clean Data →
    Split Train/Test → Train XGBoost → Evaluate → Save Model
"""

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from xgboost import XGBClassifier

from src.data_nexus.database.connection import PostgresConnection
from src.data_nexus.features.calculator import FeatureEngineer

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    XGBoost training pipeline for binary price direction classification.

    Workflow:
        1. Load OHLCV history from TimescaleDB
        2. Engineer technical indicator features
        3. Create binary target: Close[t+1] > Close[t]
        4. Clean NaN values
        5. Split into train/test sets
        6. Train XGBoost model
        7. Evaluate metrics
        8. Save trained model

    Attributes:
        symbol: Trading symbol (e.g., "EURUSD.s")
        model: Trained XGBClassifier (None until trained)
        metrics: Dictionary of evaluation metrics
        feature_columns: List of feature column names used for training
    """

    def __init__(self, symbol: str, db_config: Optional[object] = None):
        """
        Initialize ModelTrainer.

        Args:
            symbol: Trading symbol (e.g., "EURUSD.s")
            db_config: Optional database configuration (uses default if None)
        """
        self.symbol = symbol
        self.db_config = db_config
        self.model = None
        self.metrics = {}
        self.feature_columns = []

        logger.info(f"Initialized ModelTrainer for symbol: {symbol}")

    def load_and_prepare(
        self,
        min_samples: int = 100,
        limit_days: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load OHLCV data and engineer features.

        Process:
            1. Query TimescaleDB for OHLCV history
            2. Apply FeatureEngineer to calculate indicators
            3. Create binary target variable
            4. Remove NaN rows
            5. Validate sufficient data

        Args:
            min_samples: Minimum required samples after cleaning
            limit_days: Optional limit on days to load (for testing)

        Returns:
            Tuple of (features DataFrame, target Series)

        Raises:
            ValueError: If insufficient data after cleaning
            RuntimeError: If database connection fails
        """
        logger.info(f"Loading OHLCV data for {self.symbol}...")

        # Connect to database
        try:
            conn = PostgresConnection()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise RuntimeError(f"Database connection failed: {e}")

        # Query OHLCV history (ordered by time)
        try:
            query = f"""
                SELECT time, open, high, low, close, volume
                FROM market_data
                WHERE symbol = '{self.symbol}'
                ORDER BY time ASC
            """
            results = conn.query_all(query)

            if not results:
                logger.error(f"No data found for {self.symbol}")
                raise ValueError(f"No market data found for {self.symbol}")

            # Convert to DataFrame
            df = pd.DataFrame(
                results,
                columns=['time', 'open', 'high', 'low', 'close', 'volume']
            )

            logger.info(f"Loaded {len(df)} rows of OHLCV data")

        except Exception as e:
            logger.error(f"Failed to load OHLCV data: {e}")
            raise

        # Engineer features using Task #038
        logger.info("Engineering technical indicator features...")
        engineer = FeatureEngineer(df)
        df = engineer.add_all_indicators()

        logger.info(f"Created {len(engineer.get_feature_columns())} feature columns")

        # Create binary target: Close[t+1] > Close[t]
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

        # Remove last row (NaN target) and rows with NaN features
        df = df.dropna(subset=['target', 'RSI_14'])

        logger.info(f"After cleaning: {len(df)} rows")

        # Validate sufficient data
        if len(df) < min_samples:
            raise ValueError(
                f"Insufficient data: {len(df)} rows < {min_samples} minimum"
            )

        # Extract features and target
        self.feature_columns = engineer.get_feature_columns()
        X = df[self.feature_columns]
        y = df['target']

        logger.info(f"Prepared dataset: {len(X)} samples, {len(X.columns)} features")

        return X, y

    def split_data(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into train and test sets (time-based).

        Uses time-based split to preserve temporal ordering of time series.
        Test set is the last test_size% of data (most recent).

        Args:
            X: Features DataFrame
            y: Target Series
            test_size: Fraction of data for test set (default: 0.2 = 20%)

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        split_idx = int(len(X) * (1 - test_size))

        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]

        logger.info(
            f"Train/Test split: {len(X_train)} train, {len(X_test)} test "
            f"({len(X_train)/(len(X_train)+len(X_test))*100:.1f}% train)"
        )

        return X_train, X_test, y_train, y_test

    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.1
    ) -> XGBClassifier:
        """
        Train XGBoost classifier.

        Hyperparameters:
            - n_estimators: Number of boosting rounds (trees)
            - max_depth: Maximum depth of decision trees
            - learning_rate: Boosting learning rate (shrinkage)

        Args:
            X_train: Training features
            y_train: Training targets
            n_estimators: Number of boosting rounds
            max_depth: Tree depth limit
            learning_rate: Boosting step size

        Returns:
            Trained XGBClassifier
        """
        logger.info("Training XGBoost model...")

        self.model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            objective='binary:logistic',
            eval_metric='logloss',
            random_state=42,
            verbosity=0
        )

        self.model.fit(X_train, y_train)

        logger.info(f"Model training complete ({n_estimators} estimators)")

        return self.model

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate model on test set.

        Computes:
            - Accuracy: Overall correctness
            - Precision: True positives / (TP + FP)
            - Recall: True positives / (TP + FN)
            - F1-Score: Harmonic mean of precision & recall

        Args:
            X_test: Test features
            y_test: Test targets

        Returns:
            Dictionary of metrics
        """
        if self.model is None:
            raise RuntimeError("Model not trained yet. Call train_model() first.")

        logger.info("Evaluating model on test set...")

        y_pred = self.model.predict(X_test)

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0)
        }

        self.metrics = metrics

        logger.info(
            f"Evaluation metrics - Accuracy: {metrics['accuracy']:.4f}, "
            f"Precision: {metrics['precision']:.4f}, "
            f"Recall: {metrics['recall']:.4f}, "
            f"F1: {metrics['f1']:.4f}"
        )

        return metrics

    def save_checkpoint(self, path: Optional[str] = None) -> str:
        """
        Save trained model to disk.

        Default path: `models/xgboost_baseline_{symbol}_{timestamp}.joblib`

        Args:
            path: Optional custom save path

        Returns:
            Path to saved model file
        """
        if self.model is None:
            raise RuntimeError("No model to save. Train model first.")

        if path is None:
            models_dir = Path(__file__).parent.parent.parent.parent / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = models_dir / f"xgboost_baseline_{self.symbol}_{timestamp}.joblib"

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save model with metadata
        checkpoint = {
            'model': self.model,
            'symbol': self.symbol,
            'feature_columns': self.feature_columns,
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        }

        joblib.dump(checkpoint, path)

        logger.info(f"Model saved to {path}")

        return str(path)

    def run_full_pipeline(
        self,
        test_size: float = 0.2,
        min_samples: int = 100,
        save_model: bool = True
    ) -> Dict:
        """
        Run complete training pipeline end-to-end.

        Steps:
            1. Load and prepare data
            2. Split into train/test
            3. Train model
            4. Evaluate metrics
            5. Save checkpoint

        Args:
            test_size: Fraction of data for test set
            min_samples: Minimum samples required
            save_model: Whether to save trained model

        Returns:
            Dictionary with results and metrics
        """
        logger.info(f"Starting full training pipeline for {self.symbol}...")

        # Load and prepare
        X, y = self.load_and_prepare(min_samples=min_samples)

        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y, test_size=test_size)

        # Train model
        self.train_model(X_train, y_train)

        # Evaluate
        metrics = self.evaluate(X_test, y_test)

        # Save checkpoint
        model_path = None
        if save_model:
            model_path = self.save_checkpoint()

        result = {
            'symbol': self.symbol,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'n_features': len(self.feature_columns),
            'metrics': metrics,
            'model_path': model_path
        }

        logger.info(f"Pipeline complete. Model saved: {model_path}")

        return result


# Example usage
if __name__ == "__main__":
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Train model on EURUSD
    trainer = ModelTrainer(symbol="EURUSD.s")

    try:
        results = trainer.run_full_pipeline(test_size=0.2)

        print("\n" + "=" * 80)
        print("Training Complete")
        print("=" * 80)
        print(f"Symbol: {results['symbol']}")
        print(f"Train samples: {results['train_samples']}")
        print(f"Test samples: {results['test_samples']}")
        print(f"Features: {results['n_features']}")
        print(f"\nMetrics:")
        for metric, value in results['metrics'].items():
            print(f"  {metric.capitalize()}: {value:.4f}")
        print(f"\nModel saved: {results['model_path']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
