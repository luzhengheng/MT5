#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Mapping Module for HUB Model Serving

Maps Sentinel's 23-dimensional feature vector to XGBoost model's 15-dimensional input.

Protocol: v4.3 (Zero-Trust Edition)
"""

import numpy as np
import pandas as pd
from typing import Union, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureMapper:
    """
    Maps Sentinel's feature format to model's expected input format.

    Sentinel sends 23 generic features from FeatureBuilder.
    XGBoost model expects 15 specific features as defined in model_metadata.json.

    This class handles:
    1. Feature extraction from Sentinel's 23 features
    2. NaN handling and defensive programming
    3. Feature ordering consistency with training
    """

    def __init__(self, model_features: Optional[List[str]] = None):
        """
        Initialize feature mapper.

        Args:
            model_features: List of feature names expected by model.
                           If None, uses defaults from model metadata.
        """
        # Default feature names from XGBoost model metadata
        self.model_features = model_features or [
            "price_range",
            "price_change",
            "price_change_pct",
            "sma_5",
            "sma_10",
            "sma_20",
            "ema_5",
            "ema_10",
            "momentum_5",
            "momentum_10",
            "volatility_5",
            "volatility_10",
            "rsi_14",
            "volume_sma_5",
            "volume_change"
        ]

        # Sentinel feature indices (0-22)
        # These map semantic meanings to positions in Sentinel's 23-dimensional vector
        self.sentinel_feature_map = {
            "price_range": 0,           # Feature 0: price range
            "price_change": 1,          # Feature 1: price change
            "price_change_pct": 2,      # Feature 2: price change percentage
            "sma_5": 3,                 # Feature 3: SMA 5
            "sma_10": 4,                # Feature 4: SMA 10
            "sma_20": 5,                # Feature 5: SMA 20
            "ema_5": 6,                 # Feature 6: EMA 5
            "ema_10": 7,                # Feature 7: EMA 10
            "momentum_5": 8,            # Feature 8: Momentum 5
            "momentum_10": 9,           # Feature 9: Momentum 10
            "volatility_5": 10,         # Feature 10: Volatility 5
            "volatility_10": 11,        # Feature 11: Volatility 10
            "rsi_14": 12,               # Feature 12: RSI 14
            "volume_sma_5": 13,         # Feature 13: Volume SMA 5
            "volume_change": 14,        # Feature 14: Volume change
            # Features 15-22 are reserved for future expansion or time-based features
        }

        logger.info(f"FeatureMapper initialized with {len(self.model_features)} model features")

    def map_from_sentinel(
        self,
        sentinel_features: Union[np.ndarray, List, Dict]
    ) -> pd.DataFrame:
        """
        Map Sentinel's 23 features to model's 15 features.

        Args:
            sentinel_features: Sentinel's feature vector. Can be:
                - np.ndarray of shape (1, 23) or (23,)
                - List of 23 values
                - Dict with feature names as keys

        Returns:
            pd.DataFrame with 15 columns (model_features), NaN-safe

        Raises:
            ValueError: If input dimension is invalid
        """
        # Convert to numpy array
        if isinstance(sentinel_features, dict):
            # If dict, assume values are in sentinel order
            features_array = np.array(list(sentinel_features.values()))
        elif isinstance(sentinel_features, list):
            features_array = np.array(sentinel_features)
        elif isinstance(sentinel_features, np.ndarray):
            features_array = sentinel_features.flatten()
        else:
            raise ValueError(f"Unsupported input type: {type(sentinel_features)}")

        # Validate dimension
        if features_array.shape[0] != 23:
            raise ValueError(
                f"Expected 23 features from Sentinel, got {features_array.shape[0]}. "
                f"Shape: {features_array.shape}"
            )

        # Extract model features from sentinel features
        model_feature_values = []
        for model_feat in self.model_features:
            sentinel_idx = self.sentinel_feature_map.get(model_feat)

            if sentinel_idx is None:
                # Feature not mapped - use NaN (will be handled downstream)
                logger.warning(f"Feature '{model_feat}' not found in Sentinel feature map, using NaN")
                model_feature_values.append(np.nan)
            else:
                # Extract feature value
                value = features_array[sentinel_idx]
                # Defensive: ensure not NaN or inf
                if not np.isfinite(value):
                    logger.warning(
                        f"Non-finite value for '{model_feat}' (index {sentinel_idx}): {value}, "
                        f"replacing with NaN"
                    )
                    model_feature_values.append(np.nan)
                else:
                    model_feature_values.append(value)

        # Create DataFrame with proper column names
        mapped_df = pd.DataFrame(
            [model_feature_values],  # Wrap in list for single row
            columns=self.model_features
        )

        # Log NaN status
        nan_count = mapped_df.isna().sum().sum()
        if nan_count > 0:
            logger.warning(f"Mapped features contain {nan_count} NaN values")

        return mapped_df

    def handle_nans(
        self,
        features_df: pd.DataFrame,
        strategy: str = "drop"
    ) -> Optional[pd.DataFrame]:
        """
        Handle NaN values in mapped features.

        Args:
            features_df: DataFrame with features
            strategy: How to handle NaN:
                - "drop": Remove rows with NaN (strict)
                - "forward_fill": Forward fill NaN values (default)
                - "zero": Replace NaN with 0

        Returns:
            Processed DataFrame, or None if all rows dropped
        """
        if strategy == "drop":
            original_len = len(features_df)
            result = features_df.dropna()
            if len(result) == 0:
                logger.error("All rows contain NaN - cannot proceed")
                return None
            if len(result) < original_len:
                logger.warning(f"Dropped {original_len - len(result)} rows with NaN")
            return result

        elif strategy == "forward_fill":
            # Forward fill, then backward fill for leading NaNs
            result = features_df.fillna(method='ffill').fillna(method='bfill')
            if result.isna().any().any():
                logger.warning("Forward fill did not eliminate all NaNs, using zero fill")
                result = result.fillna(0)
            return result

        elif strategy == "zero":
            result = features_df.fillna(0)
            return result

        else:
            raise ValueError(f"Unknown NaN handling strategy: {strategy}")

    def validate_dimensions(
        self,
        features_df: pd.DataFrame
    ) -> bool:
        """
        Validate that features DataFrame has correct shape.

        Args:
            features_df: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        if len(features_df.columns) != len(self.model_features):
            logger.error(
                f"Column count mismatch: expected {len(self.model_features)}, "
                f"got {len(features_df.columns)}"
            )
            return False

        if list(features_df.columns) != self.model_features:
            logger.error(f"Column order mismatch")
            logger.error(f"  Expected: {self.model_features}")
            logger.error(f"  Got: {list(features_df.columns)}")
            return False

        return True


def map_sentinel_to_model(
    sentinel_features: Union[np.ndarray, List],
    model_features: Optional[List[str]] = None
) -> Optional[pd.DataFrame]:
    """
    Utility function to map Sentinel features to model input.

    Args:
        sentinel_features: Sentinel's 23-dimensional feature vector
        model_features: Expected model features (optional)

    Returns:
        Mapped DataFrame ready for model inference, or None on error
    """
    try:
        mapper = FeatureMapper(model_features)
        mapped = mapper.map_from_sentinel(sentinel_features)

        # Handle NaNs defensively
        mapped = mapper.handle_nans(mapped, strategy="forward_fill")
        if mapped is None:
            return None

        # Validate
        if not mapper.validate_dimensions(mapped):
            return None

        return mapped

    except Exception as e:
        logger.error(f"Feature mapping failed: {e}")
        return None
