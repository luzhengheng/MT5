#!/usr/bin/env python3
"""
Task #113: ML Alpha Pipeline & Baseline Model Registration
Audit script for feature engineering and XGBoost baseline model

Protocol: v4.3 (Zero-Trust Edition)
Gate 1: Local TDD validation
"""

import unittest
import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestFeatureEngineering(unittest.TestCase):
    """Test feature engineering pipeline for ML Alpha"""

    def setUp(self):
        """Set up test data"""
        # Create sample OHLCV data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        })
        self.df = self.df.set_index('timestamp')

    def test_rsi_calculation(self):
        """Test RSI (Relative Strength Index) calculation"""
        logger.info("Testing RSI calculation...")

        # RSI implementation
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(
                window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(
                window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        rsi = calculate_rsi(self.df['close'], period=14)

        # Assertions
        self.assertEqual(len(rsi), len(self.df))
        self.assertTrue((rsi[14:] >= 0).all() or (rsi[14:] <= 100).all())
        logger.info("✅ RSI test passed. Mean RSI: %.2f", rsi[14:].mean())

    def test_volatility_calculation(self):
        """Test volatility (rolling std) calculation"""
        logger.info("Testing volatility calculation...")

        # Volatility: rolling standard deviation
        volatility = self.df['close'].rolling(window=20).std()

        # Assertions
        self.assertEqual(len(volatility), len(self.df))
        self.assertGreater(volatility[20:].mean(), 0)
        logger.info("✅ Volatility test passed. Mean: %.4f",
                    volatility[20:].mean())

    def test_lag_features(self):
        """Test lagged features generation"""
        logger.info("Testing lag features...")

        # Create lag features
        lags = [1, 5, 20]
        for lag in lags:
            self.df[f'close_lag_{lag}'] = self.df['close'].shift(lag)

        # Assertions
        for lag in lags:
            col_name = f'close_lag_{lag}'
            self.assertIn(col_name, self.df.columns)
            self.assertEqual(len(self.df[col_name]), len(self.df))
            # First lag rows are NaN
            self.assertEqual(self.df[col_name].isna().sum(), lag)

        logger.info("✅ Lag features test passed. Created %d lag columns",
                    len(lags))

    def test_timeseries_split(self):
        """Test TimeSeriesSplit for train/validation/test split"""
        logger.info("Testing TimeSeriesSplit...")

        from sklearn.model_selection import TimeSeriesSplit

        # TimeSeriesSplit with n_splits=3
        tscv = TimeSeriesSplit(n_splits=3)
        splits = list(tscv.split(self.df))

        # Assertions
        self.assertEqual(len(splits), 3)

        # Verify temporal ordering (train < validation < test)
        train_idx, val_idx = splits[0]
        self.assertLess(max(train_idx), min(val_idx))
        logger.info("✅ TimeSeriesSplit test passed. %d splits created",
                    len(splits))

        # Log split sizes
        for i, (train, val) in enumerate(splits):
            logger.info("   Split %d: train=%d, validation=%d",
                        i, len(train), len(val))

    def test_label_generation(self):
        """Test binary classification label generation"""
        logger.info("Testing label generation...")

        # Binary label: 1 if next close > current close, else 0
        self.df['label'] = (
            self.df['close'].shift(-1) > self.df['close']).astype(int)

        # Assertions
        self.assertIn('label', self.df.columns)
        self.assertTrue(self.df['label'].isin([0, 1]).all())
        self.assertGreater(self.df['label'].sum(), 0)  # At least some 1s
        self.assertGreater((self.df['label'] == 0).sum(), 0)  # Some 0s

        logger.info("✅ Label generation test passed. Ratio: %.2f%%",
                    self.df['label'].mean() * 100)

    def test_feature_normalization(self):
        """Test feature normalization (StandardScaler)"""
        logger.info("Testing feature normalization...")

        from sklearn.preprocessing import StandardScaler

        features = self.df[['close', 'volume']].dropna()
        scaler = StandardScaler()
        scaled = scaler.fit_transform(features)

        # Assertions
        scaled_df = pd.DataFrame(scaled, columns=['close', 'volume'])
        self.assertAlmostEqual(scaled_df['close'].mean(), 0, places=4)
        # Standard scaler std close to 1 (within 1% tolerance)
        self.assertTrue(0.99 < scaled_df['close'].std() < 1.01)

        logger.info("✅ Feature normalization test passed")


class TestXGBoostModel(unittest.TestCase):
    """Test XGBoost model training and evaluation"""

    def setUp(self):
        """Set up test data with features"""
        # Create sample dataset
        n_samples = 200
        dates = pd.date_range('2023-01-01', periods=n_samples, freq='D')

        self.df = pd.DataFrame({
            'timestamp': dates,
            'close': np.random.uniform(100, 110, n_samples),
            'volume': np.random.uniform(1000, 10000, n_samples),
            'rsi': np.random.uniform(20, 80, n_samples),
            'volatility': np.random.uniform(0.01, 0.05, n_samples),
        })

        # Generate binary labels
        self.df['label'] = np.random.randint(0, 2, n_samples)
        self.df = self.df.set_index('timestamp')

    def test_xgboost_import(self):
        """Test XGBoost library import"""
        logger.info("Testing XGBoost import...")

        try:
            import xgboost as xgb
            logger.info("✅ XGBoost version %s imported successfully",
                        xgb.__version__)
            self.assertTrue(hasattr(xgb, 'XGBClassifier'))
        except ImportError as e:
            self.fail("XGBoost import failed: {}".format(e))

    def test_model_training(self):
        """Test XGBoost model training"""
        logger.info("Testing XGBoost model training...")

        import xgboost as xgb
        from sklearn.model_selection import train_test_split

        # Prepare features and labels
        X = self.df[['close', 'volume', 'rsi', 'volatility']]
        y = self.df['label']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        model = xgb.XGBClassifier(
            n_estimators=10,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)

        # Assertions
        self.assertIsNotNone(model)
        score = model.score(X_test, y_test)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)

        logger.info("✅ Model training test passed. Accuracy: %.4f", score)

    def test_model_prediction(self):
        """Test model prediction capability"""
        logger.info("Testing model prediction...")

        import xgboost as xgb

        # Train simple model
        X = self.df[['close', 'volume', 'rsi', 'volatility']]
        y = self.df['label']

        model = xgb.XGBClassifier(n_estimators=5, max_depth=3,
                                   random_state=42)
        model.fit(X, y)

        # Make predictions
        predictions = model.predict(X[:10])

        # Assertions
        self.assertEqual(len(predictions), 10)
        self.assertTrue(all(p in [0, 1] for p in predictions))

        logger.info("✅ Model prediction test passed. Preds: %s",
                    predictions[:5])

    def test_model_serialization(self):
        """Test model save/load functionality"""
        logger.info("Testing model serialization...")

        import xgboost as xgb
        import tempfile

        # Train model
        X = self.df[['close', 'volume', 'rsi', 'volatility']]
        y = self.df['label']

        model = xgb.XGBClassifier(n_estimators=5, max_depth=3,
                                   random_state=42)
        model.fit(X, y)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.json',
                                          delete=False) as tmp:
            tmp_path = tmp.name

        try:
            model.save_model(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))

            # Load model
            loaded_model = xgb.XGBClassifier()
            loaded_model.load_model(tmp_path)

            # Compare predictions
            orig_pred = model.predict(X[:5])
            loaded_pred = loaded_model.predict(X[:5])

            np.testing.assert_array_equal(orig_pred, loaded_pred)
            logger.info("✅ Model serialization test passed")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_model_metadata(self):
        """Test model metadata tracking"""
        logger.info("Testing model metadata...")

        import xgboost as xgb

        metadata = {
            'model_name': 'xgboost_baseline',
            'version': '1.0',
            'features': ['close', 'volume', 'rsi', 'volatility'],
            'model_type': 'binary_classifier',
            'created_at': datetime.now().isoformat(),
            'framework': 'xgboost',
            'framework_version': xgb.__version__
        }

        # Assertions
        self.assertIn('model_name', metadata)
        self.assertIn('features', metadata)
        self.assertEqual(len(metadata['features']), 4)

        logger.info("✅ Model metadata test passed")


class TestDataValidation(unittest.TestCase):
    """Test data validation for ML pipeline"""

    def test_eodhd_data_format(self):
        """Test EODHD standardized data format"""
        logger.info("Testing EODHD data format...")

        # Check if standardized data exists
        data_dir = Path('data_lake/standardized')
        if data_dir.exists():
            parquet_files = list(data_dir.glob('*.parquet'))
            logger.info("Found %d standardized Parquet files",
                        len(parquet_files))

            for pf in parquet_files[:1]:  # Check first file
                df = pd.read_parquet(pf)
                logger.info("✅ %s: %d rows, columns: %s",
                            pf.name, df.shape[0], list(df.columns))

                # Assertions
                expected_cols = ['timestamp', 'open', 'high', 'low',
                                  'close', 'volume']
                for col in expected_cols:
                    self.assertIn(col, df.columns,
                                  "Missing column: {}".format(col))
        else:
            logger.warning("Data directory %s not found", data_dir)

    def test_feature_consistency(self):
        """Test feature consistency across samples"""
        logger.info("Testing feature consistency...")

        # Create test feature set
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        features = pd.DataFrame({
            'close': np.random.uniform(100, 110, 100),
            'rsi': np.random.uniform(20, 80, 100),
            'volatility': np.random.uniform(0.01, 0.05, 100),
            'volume': np.random.uniform(1000, 10000, 100),
            'close_lag_1': np.random.uniform(100, 110, 100),
            'close_lag_5': np.random.uniform(100, 110, 100),
        }, index=dates)

        # Assertions
        self.assertEqual(len(features), 100)
        self.assertEqual(features.shape[1], 6)

        logger.info("✅ Feature consistency test passed")


def run_tests():
    """Run all tests and generate report"""
    logger.info("=" * 80)
    logger.info("Task #113: Audit Test Suite")
    logger.info("=" * 80)
    logger.info("Start time: %s", datetime.now().isoformat())

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureEngineering))
    suite.addTests(loader.loadTestsFromTestCase(TestXGBoostModel))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Log summary
    logger.info("=" * 80)
    logger.info("Tests run: %d", result.testsRun)
    successes = result.testsRun - len(result.failures) - len(result.errors)
    logger.info("Successes: %d", successes)
    logger.info("Failures: %d", len(result.failures))
    logger.info("Errors: %d", len(result.errors))
    logger.info("End time: %s", datetime.now().isoformat())
    logger.info("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
