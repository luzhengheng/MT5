#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Feature Engineering Module

Validates that feature computation is consistent and correct.
"""

import unittest
import pandas as pd
import numpy as np
from src.features.engineering import (
    compute_features,
    compute_price_features,
    compute_moving_averages,
    compute_momentum_features,
    compute_volatility_features,
    compute_rsi,
    compute_technical_indicators,
    compute_volume_features,
    FeatureConfig,
    get_feature_names,
)


class TestFeatureEngineering(unittest.TestCase):
    """Test suite for feature engineering module"""

    def setUp(self):
        """Create sample OHLCV data for testing"""
        # Create 100 rows of synthetic data
        np.random.seed(42)
        dates = pd.date_range('2025-10-01', periods=100, freq='D')

        # Generate realistic price data
        close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

        self.df = pd.DataFrame({
            'time': dates,
            'symbol': 'AUDCAD.FOREX',
            'open': close_prices - 0.5 + np.random.randn(100) * 0.3,
            'high': close_prices + 1 + np.random.randn(100) * 0.3,
            'low': close_prices - 1 + np.random.randn(100) * 0.3,
            'close': close_prices,
            'adjusted_close': close_prices,
            'volume': np.random.randint(1000, 10000, 100)
        })

    def test_compute_price_features(self):
        """Test price feature computation"""
        result = compute_price_features(self.df.copy())

        # Check that new columns exist
        self.assertIn('price_range', result.columns)
        self.assertIn('price_change', result.columns)
        self.assertIn('price_change_pct', result.columns)

        # Check that values are computed correctly
        expected_range = result['high'] - result['low']
        np.testing.assert_array_almost_equal(result['price_range'].values, expected_range.values)

    def test_compute_moving_averages(self):
        """Test moving average computation"""
        config = FeatureConfig(sma_windows=[5, 10], ema_windows=[5])
        result = compute_moving_averages(self.df.copy(), config)

        # Check that MA columns exist
        self.assertIn('sma_5', result.columns)
        self.assertIn('sma_10', result.columns)
        self.assertIn('ema_5', result.columns)

        # Check that SMA is computed correctly
        expected_sma_5 = result['close'].rolling(window=5).mean()
        np.testing.assert_array_almost_equal(
            result['sma_5'].values,
            expected_sma_5.values,
            decimal=5
        )

    def test_compute_momentum_features(self):
        """Test momentum feature computation"""
        config = FeatureConfig(momentum_windows=[5, 10])
        result = compute_momentum_features(self.df.copy(), config)

        # Check that momentum columns exist
        self.assertIn('momentum_5', result.columns)
        self.assertIn('momentum_10', result.columns)

        # Check that momentum is computed correctly
        expected_momentum_5 = result['close'] - result['close'].shift(5)
        np.testing.assert_array_almost_equal(
            result['momentum_5'].values[5:],
            expected_momentum_5.values[5:]
        )

    def test_compute_rsi(self):
        """Test RSI computation"""
        result = compute_rsi(self.df.copy(), window=14)

        # Check that RSI values are in valid range [0, 100]
        valid_rsi = result.dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())

    def test_compute_features_complete(self):
        """Test complete feature engineering pipeline"""
        config = FeatureConfig()
        result = compute_features(self.df.copy(), config=config, include_target=False)

        # Check that all expected columns exist
        feature_names = get_feature_names(config)
        for feature_name in feature_names:
            self.assertIn(feature_name, result.columns,
                         f"Feature {feature_name} not found in result")

        # Check that result has fewer rows (due to NaN drops from rolling windows)
        self.assertLess(len(result), len(self.df))

        # Check that there are no NaN values
        self.assertFalse(result.isna().any().any(), "Result contains NaN values")

    def test_compute_features_with_target(self):
        """Test feature engineering with target variable"""
        config = FeatureConfig()
        result = compute_features(self.df.copy(), config=config, include_target=True)

        # Check that target column exists
        self.assertIn('target', result.columns)

        # Check that target is binary (0 or 1)
        self.assertTrue(result['target'].isin([0, 1]).all())

    def test_feature_config_defaults(self):
        """Test that FeatureConfig defaults are reasonable"""
        config = FeatureConfig()

        # Check that defaults are set
        self.assertIsNotNone(config.sma_windows)
        self.assertIsNotNone(config.ema_windows)
        self.assertIsNotNone(config.momentum_windows)
        self.assertIsNotNone(config.volatility_windows)

        # Check that windows are non-empty
        self.assertGreater(len(config.sma_windows), 0)
        self.assertGreater(len(config.ema_windows), 0)

    def test_get_feature_names(self):
        """Test feature name retrieval"""
        config = FeatureConfig()
        feature_names = get_feature_names(config)

        # Check that feature names list is not empty
        self.assertGreater(len(feature_names), 0)

        # Check that common features are present
        self.assertIn('price_range', feature_names)
        self.assertIn('sma_5', feature_names)
        self.assertIn('momentum_5', feature_names)
        self.assertIn('rsi_14', feature_names)

    def test_feature_consistency_across_calls(self):
        """Test that feature computation is consistent across multiple calls"""
        config = FeatureConfig()

        # Compute features twice
        result1 = compute_features(self.df.copy(), config=config, include_target=False)
        result2 = compute_features(self.df.copy(), config=config, include_target=False)

        # Check that results are identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_nan_handling(self):
        """Test that NaN handling works correctly"""
        # Create data with some NaN values
        df_with_nan = self.df.copy()
        df_with_nan.loc[0:5, 'close'] = np.nan

        config = FeatureConfig()
        result = compute_features(df_with_nan, config=config, include_target=False)

        # Check that result doesn't have NaN values
        self.assertFalse(result.isna().any().any())

        # Check that result is shorter due to NaN rows being dropped
        self.assertLess(len(result), len(self.df))


class TestTrainInferenceConsistency(unittest.TestCase):
    """Test that training and inference use consistent feature engineering"""

    def setUp(self):
        """Create sample OHLCV data"""
        np.random.seed(42)
        dates = pd.date_range('2025-10-01', periods=100, freq='D')
        close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

        self.df = pd.DataFrame({
            'time': dates,
            'symbol': 'AUDCAD.FOREX',
            'open': close_prices - 0.5 + np.random.randn(100) * 0.3,
            'high': close_prices + 1 + np.random.randn(100) * 0.3,
            'low': close_prices - 1 + np.random.randn(100) * 0.3,
            'close': close_prices,
            'adjusted_close': close_prices,
            'volume': np.random.randint(1000, 10000, 100)
        })

    def test_training_inference_features_match(self):
        """
        Test that training and inference produce the same feature columns

        This is critical to prevent training-serving skew.
        """
        config = FeatureConfig()

        # Simulate training feature engineering
        features_train = compute_features(
            self.df.copy(), config=config, include_target=True
        )

        # Simulate inference feature engineering
        features_inference = compute_features(
            self.df.copy(), config=config, include_target=False
        )

        # Get non-target feature columns
        train_features_only = features_train.drop(columns=['target'])

        # Check that both have same columns (except target)
        self.assertEqual(
            set(train_features_only.columns),
            set(features_inference.columns),
            "Training and inference have different feature columns!"
        )

    def test_feature_values_identical(self):
        """
        Test that the same input produces identical feature values in training vs inference
        """
        config = FeatureConfig()

        # Compute features for training
        features_train = compute_features(
            self.df.copy(), config=config, include_target=True
        )

        # Compute features for inference
        features_inference = compute_features(
            self.df.copy(), config=config, include_target=False
        )

        # Compare numeric features (exclude datetime/object columns)
        for col in features_inference.columns:
            if features_inference[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                np.testing.assert_array_almost_equal(
                    features_train[col].values,
                    features_inference[col].values,
                    err_msg=f"Feature '{col}' differs between training and inference!"
                )


if __name__ == '__main__':
    unittest.main()
