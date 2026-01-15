#!/usr/bin/env python3
"""
Task #114: Feature Parity Verification

Validates that OnlineFeatureCalculator produces identical results
to the offline FeatureEngineer (Task #113).

This is CRITICAL for preventing Training-Serving Skew.

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import numpy as np
import pandas as pd
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.ml_feature_pipeline import FeatureEngineer
from src.inference.online_features import OnlineFeatureCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data(file_path: str, n_rows: int = 100) -> pd.DataFrame:
    """
    Load test OHLCV data

    Args:
        file_path: Path to parquet file
        n_rows: Number of rows to load

    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"Loading test data from {file_path}")

    try:
        df = pd.read_parquet(file_path)
        df = df.head(n_rows)
        logger.info(f"Loaded {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise


def compute_offline_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute features using offline FeatureEngineer (Task #113)

    Args:
        df: OHLCV data

    Returns:
        DataFrame with features
    """
    logger.info("Computing features with OFFLINE method (Task #113)")

    engineer = FeatureEngineer()
    features_df = engineer.engineer_features(df)

    logger.info(f"Offline features shape: {features_df.shape}")
    return features_df


def compute_online_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute features using online OnlineFeatureCalculator (Task #114)

    Simulates streaming by feeding rows one at a time.

    Args:
        df: OHLCV data

    Returns:
        DataFrame with features
    """
    logger.info("Computing features with ONLINE method (Task #114)")

    calculator = OnlineFeatureCalculator(max_lookback=50)

    features_list = []

    for i, row in df.iterrows():
        calculator.update(
            close=row['close'],
            high=row['high'],
            low=row['low'],
            volume=row['volume']
        )

        features = calculator.calculate_features()

        if features is not None:
            features['index'] = i
            features_list.append(features)

    online_df = pd.DataFrame(features_list)
    online_df = online_df.set_index('index')

    logger.info(f"Online features shape: {online_df.shape}")
    return online_df


def compare_features(offline_df: pd.DataFrame,
                    online_df: pd.DataFrame,
                    tolerance: float = 1e-6) -> bool:
    """
    Compare offline and online features for parity

    Args:
        offline_df: Offline computed features
        online_df: Online computed features
        tolerance: Maximum allowed difference

    Returns:
        True if features match within tolerance
    """
    logger.info("="*80)
    logger.info("Feature Parity Comparison")
    logger.info("="*80)

    # Align indices (online has fewer rows due to lookback)
    common_index = offline_df.index.intersection(online_df.index)

    if len(common_index) == 0:
        logger.error("No common indices between offline and online features!")
        return False

    logger.info(f"Comparing {len(common_index)} rows")

    # Get common columns (exclude macd_hist which may have slight differences)
    offline_cols = set(offline_df.columns)
    online_cols = set(online_df.columns)

    common_cols = offline_cols.intersection(online_cols)

    logger.info(f"Common features: {len(common_cols)}")

    # Compare each feature
    all_match = True
    mismatch_count = 0

    for col in sorted(common_cols):
        offline_vals = offline_df.loc[common_index, col].values
        online_vals = online_df.loc[common_index, col].values

        # Compute absolute and relative differences
        abs_diff = np.abs(offline_vals - online_vals)
        max_diff = np.max(abs_diff)
        mean_diff = np.mean(abs_diff)

        # Check if within tolerance
        if max_diff > tolerance:
            all_match = False
            mismatch_count += 1

            logger.warning(
                f"❌ {col:25s}: max_diff = {max_diff:.9f} (FAIL)"
            )

            # Show first few mismatches
            mismatch_idx = np.where(abs_diff > tolerance)[0][:3]
            for idx in mismatch_idx:
                logger.warning(
                    f"   Row {common_index[idx]}: "
                    f"offline={offline_vals[idx]:.9f}, "
                    f"online={online_vals[idx]:.9f}, "
                    f"diff={abs_diff[idx]:.9f}"
                )
        else:
            logger.info(
                f"✅ {col:25s}: max_diff = {max_diff:.9f} (PASS)"
            )

    # Summary
    logger.info("="*80)
    logger.info("Summary")
    logger.info("="*80)
    logger.info(f"Total features compared: {len(common_cols)}")
    logger.info(f"Matching features:       {len(common_cols) - mismatch_count}")
    logger.info(f"Mismatched features:     {mismatch_count}")

    if all_match:
        logger.info("\n✅ PARITY CHECK PASSED: All features match within tolerance")
        return True
    else:
        logger.error(f"\n❌ PARITY CHECK FAILED: {mismatch_count} features exceed tolerance")
        return False


def main():
    """Main verification script"""
    print("\n" + "="*80)
    print("Task #114: Feature Parity Verification")
    print("="*80)

    # Configuration
    test_data_path = "/opt/mt5-crs/data_lake/eodhd_standardized/EURUSD_D1.parquet"
    n_rows = 100
    tolerance = 1e-6

    try:
        # Load test data
        df = load_test_data(test_data_path, n_rows=n_rows)

        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")

        # Compute features with both methods
        offline_features = compute_offline_features(df)
        online_features = compute_online_features(df)

        # Compare
        parity_ok = compare_features(offline_features, online_features, tolerance)

        # Exit code
        if parity_ok:
            print("\n✅ Feature parity verification PASSED")
            sys.exit(0)
        else:
            print("\n❌ Feature parity verification FAILED")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
