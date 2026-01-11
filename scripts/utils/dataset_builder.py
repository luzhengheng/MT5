#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #069: Feature Dataset Builder with Look-Ahead Bias Prevention
Protocol: v4.3 (Zero-Trust Edition)

This script builds a leakage-free training dataset from Feast features and
generates labels using Triple Barrier methodology. Ensures no look-ahead bias
by removing samples that use future information.

Features:
1. Fetches 23 technical indicators from Feast PostgreSQL offline store
2. Generates labels via Triple Barrier methodology (López de Prado)
3. **CRITICAL**: Prevents look-ahead bias by removing contaminated samples
4. Implements time-aware train/val split (70%/30%, no random shuffle)
5. Applies RobustScaler for feature scaling (outlier-resistant)

Usage:
    python3 scripts/dataset_builder.py --symbol AAPL.US --start-date 2023-01-01 --end-date 2024-01-01
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sklearn.preprocessing import RobustScaler, StandardScaler
import pickle

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feature_engineering.labeling import TripleBarrierLabeling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432')),),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'mt5_crs')),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'trader')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'changeme_timescale'))
}


class FeatureDatasetBuilder:
    """
    Build leakage-free training datasets from Feast features with Triple Barrier labels.

    Implements strict look-ahead bias prevention:
    - Removes initial N rows (warmup period for indicators + label lookahead)
    - Time-aware train/val split (no random shuffle)
    - Feature scaling fit on train, applied to val
    """

    def __init__(self,
                 symbol: str,
                 feature_lookback_days: int = 26,  # EMA(26) requires 26 bars warmup
                 label_lookahead_days: int = 5,     # Triple Barrier lookahead
                 scaling_method: str = 'robust'):
        """
        Initialize dataset builder.

        Args:
            symbol: Trading symbol (e.g., 'AAPL.US')
            feature_lookback_days: Indicator warmup period (default: 26)
            label_lookahead_days: Label generation lookahead (default: 5)
            scaling_method: 'robust' or 'standard' (robust less sensitive to outliers)
        """
        self.symbol = symbol
        self.feature_lookback_days = feature_lookback_days
        self.label_lookahead_days = label_lookahead_days
        self.scaling_method = scaling_method
        self.pg_conn = None
        self.scaler = None

    def connect_postgres(self, max_retries: int = 3) -> bool:
        """Connect to PostgreSQL database."""
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[{attempt}/{max_retries}] Connecting to PostgreSQL...")
                self.pg_conn = psycopg2.connect(**DB_CONFIG)
                self.pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                logger.info("✅ PostgreSQL connection successful")
                return True
            except psycopg2.OperationalError as e:
                logger.warning(f"⚠️  Connection failed: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(2)

        logger.error("❌ Failed to connect to PostgreSQL")
        return False

    def fetch_ohlcv(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch OHLCV data from market_data.ohlcv_daily.

        Args:
            start_date: Start date for OHLCV data
            end_date: End date for OHLCV data

        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        if not self.pg_conn:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT time, open, high, low, close, volume
                    FROM market_data.ohlcv_daily
                    WHERE symbol = %s
                      AND time >= %s
                      AND time <= %s
                    ORDER BY time ASC;
                """, (self.symbol, start_date, end_date))

                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                if not rows:
                    logger.warning(f"No OHLCV data found for {self.symbol}")
                    return pd.DataFrame()

                df = pd.DataFrame(rows, columns=columns)
                logger.info(f"Fetched {len(df)} OHLCV rows for {self.symbol}")
                return df

        except psycopg2.Error as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return pd.DataFrame()

    def fetch_features_from_postgres(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch computed technical indicators from features.technical_indicators table.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with columns: time, symbol, sma_5, sma_10, ..., volume_change (23 indicators)
        """
        if not self.pg_conn:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT time, symbol,
                           sma_5, sma_10, sma_20, ema_12, ema_26,
                           rsi_14, roc_1, roc_5, roc_10, macd, macd_signal, macd_hist,
                           atr_14, bb_upper_20, bb_middle_20, bb_lower_20,
                           high_low_ratio, close_open_ratio,
                           volume_sma_5, volume_sma_20, volume_change
                    FROM features.technical_indicators
                    WHERE symbol = %s
                      AND time >= %s
                      AND time <= %s
                    ORDER BY time ASC;
                """, (self.symbol, start_date, end_date))

                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                if not rows:
                    logger.warning(f"No features found for {self.symbol}")
                    return pd.DataFrame()

                df = pd.DataFrame(rows, columns=columns)
                logger.info(f"Fetched {len(df)} feature rows for {self.symbol}")
                return df

        except psycopg2.Error as e:
            logger.error(f"Error fetching features: {e}")
            return pd.DataFrame()

    def generate_labels(self, ohlcv_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate labels using Triple Barrier methodology.

        Args:
            ohlcv_df: DataFrame with OHLCV data

        Returns:
            Tuple of (labels, sample_weights, label_end_indices)
                - labels: [-1, 0, 1] class labels
                - sample_weights: importance weights for each sample
                - label_end_indices: index where label window ends
        """
        logger.info("Generating labels using Triple Barrier methodology...")

        # Ensure proper index
        ohlcv_df = ohlcv_df.set_index('time')
        close_prices = ohlcv_df['close']

        # Apply Triple Barrier
        labels_result = TripleBarrierLabeling.apply_triple_barrier(
            close_prices,
            upper_barrier=0.02,      # 2% upside
            lower_barrier=-0.02,     # 2% downside
            max_holding_period=self.label_lookahead_days,
            stop_loss=None
        )

        logger.info(f"Generated labels: {labels_result['label'].value_counts().to_dict()}")

        # Extract labels and compute sample weights
        labels = labels_result['label'].values
        sample_weights = TripleBarrierLabeling.compute_sample_weights(
            labels_result['label'],
            labels_result['return']
        ).values

        # For each label, track the index where the label window ends
        # This is used to prevent look-ahead bias
        label_end_indices = np.full(len(labels), self.label_lookahead_days, dtype=int)

        return labels, sample_weights, label_end_indices

    def prevent_look_ahead_bias(self,
                                X: pd.DataFrame,
                                y: np.ndarray,
                                label_end_indices: np.ndarray) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        **CRITICAL**: Remove samples that use future information.

        Strategy:
        1. Remove first N rows where N = feature_lookback_days + label_lookahead_days
        2. This ensures:
           - Features have fully computed (warmup period complete)
           - Labels don't look beyond available data (no future info)

        Args:
            X: Feature matrix
            y: Labels
            label_end_indices: Index where each label window ends

        Returns:
            Tuple of (X_decontaminated, y_decontaminated)
        """
        logger.info("Preventing look-ahead bias by removing contaminated samples...")

        # Minimum rows to remove = feature warmup + label lookahead
        min_rows_to_skip = self.feature_lookback_days + self.label_lookahead_days

        logger.info(f"Removing first {min_rows_to_skip} rows:")
        logger.info(f"  - Feature lookback (warmup): {self.feature_lookback_days} days")
        logger.info(f"  - Label lookahead: {self.label_lookahead_days} days")

        # Remove contaminated rows
        X_clean = X[min_rows_to_skip:].reset_index(drop=True)
        y_clean = y[min_rows_to_skip:]

        logger.info(f"✅ Removed {min_rows_to_skip} rows")
        logger.info(f"Remaining samples: {len(X_clean)} (from {len(X)})")

        return X_clean, y_clean

    def scale_features(self,
                       X_train: pd.DataFrame,
                       X_val: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Scale features using RobustScaler or StandardScaler.

        **CRITICAL**: Fit scaler on training data ONLY, then transform validation.
        This prevents information leakage from validation set into training.

        Args:
            X_train: Training features
            X_val: Validation features

        Returns:
            Tuple of (X_train_scaled, X_val_scaled)
        """
        logger.info(f"Scaling features using {self.scaling_method.upper()}Scaler...")

        if self.scaling_method == 'robust':
            self.scaler = RobustScaler()
        else:
            self.scaler = StandardScaler()

        # Fit on train only, transform both
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        logger.info(f"✅ Scaler fit on {len(X_train)} training samples")
        logger.info(f"Scaling parameters: center={self.scaler.center_}, scale={self.scaler.scale_[:5]}...")

        return X_train_scaled, X_val_scaled

    def build(self,
              start_date: str,
              end_date: str,
              train_split: float = 0.7) -> Dict[str, Any]:
        """
        End-to-end pipeline: fetch → label → decontaminate → scale → split.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            train_split: Train/val split ratio (default: 70%/30%)

        Returns:
            Dictionary with keys:
                - X_train: Training features (scaled, numpy array)
                - y_train: Training labels
                - X_val: Validation features (scaled, numpy array)
                - y_val: Validation labels
                - feature_names: List of feature column names
                - scaler: Fitted scaler object
                - metadata: Dataset metadata
        """
        logger.info("=" * 80)
        logger.info("TASK #069: Feature Dataset Builder")
        logger.info("=" * 80)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Train/Val split: {train_split:.0%}/{1-train_split:.0%}")
        logger.info("")

        # Connect to database
        if not self.connect_postgres():
            return {}

        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            self.close()
            return {}

        # Step 1: Fetch features
        logger.info("Step 1: Fetching features from PostgreSQL...")
        X = self.fetch_features_from_postgres(start_dt, end_dt)
        if X.empty:
            logger.error("No features found. Ensure Task #068 completed (feature computation)")
            self.close()
            return {}

        feature_names = [col for col in X.columns if col not in ['time', 'symbol']]
        logger.info(f"✅ Retrieved {len(feature_names)} features: {feature_names[:5]}...")
        logger.info("")

        # Step 2: Fetch OHLCV for labeling
        logger.info("Step 2: Fetching OHLCV data for label generation...")
        ohlcv = self.fetch_ohlcv(start_dt, end_dt)
        if ohlcv.empty:
            logger.error("No OHLCV data found")
            self.close()
            return {}

        # Ensure same row count
        if len(X) != len(ohlcv):
            logger.warning(f"Feature and OHLCV row count mismatch: {len(X)} vs {len(ohlcv)}")
            min_len = min(len(X), len(ohlcv))
            X = X[:min_len]
            ohlcv = ohlcv[:min_len]
            logger.info(f"Trimmed to {min_len} rows")

        logger.info("")

        # Step 3: Generate labels
        logger.info("Step 3: Generating Triple Barrier labels...")
        y, sample_weights, label_end_indices = self.generate_labels(ohlcv)
        logger.info(f"✅ Label distribution: {np.bincount(y + 1)}")  # Shift [-1,0,1] → [0,1,2]
        logger.info("")

        # Step 4: **CRITICAL** Prevent look-ahead bias
        logger.info("Step 4: Preventing look-ahead bias (CRITICAL)...")
        X_clean, y_clean = self.prevent_look_ahead_bias(X[feature_names], y, label_end_indices)
        logger.info("")

        # Step 5: Time-aware train/val split (NO RANDOM SHUFFLE)
        logger.info("Step 5: Creating time-aware train/validation split...")
        split_idx = int(len(X_clean) * train_split)

        X_train = X_clean[:split_idx]
        X_val = X_clean[split_idx:]
        y_train = y_clean[:split_idx]
        y_val = y_clean[split_idx:]

        logger.info(f"Train set: {len(X_train)} samples ({train_split:.0%})")
        logger.info(f"Val set: {len(X_val)} samples ({1-train_split:.0%})")
        logger.info(f"Train label distribution: {np.bincount(y_train + 1)}")
        logger.info(f"Val label distribution: {np.bincount(y_val + 1)}")
        logger.info("")

        # Step 6: Scale features
        logger.info("Step 6: Scaling features...")
        X_train_scaled, X_val_scaled = self.scale_features(X_train, X_val)
        logger.info("")

        # Close connection
        self.close()

        # Build metadata
        metadata = {
            'symbol': self.symbol,
            'start_date': start_date,
            'end_date': end_date,
            'train_size': len(X_train),
            'val_size': len(X_val),
            'n_features': len(feature_names),
            'feature_names': feature_names,
            'train_label_dist': dict(zip([-1, 0, 1], np.bincount(y_train + 1))),
            'val_label_dist': dict(zip([-1, 0, 1], np.bincount(y_val + 1))),
            'scaling_method': self.scaling_method,
            'scaler_params': {
                'center': self.scaler.center_,
                'scale': self.scaler.scale_
            }
        }

        logger.info("=" * 80)
        logger.info("✅ Dataset building complete")
        logger.info("=" * 80)

        return {
            'X_train': X_train_scaled,
            'y_train': y_train,
            'X_val': X_val_scaled,
            'y_val': y_val,
            'feature_names': feature_names,
            'scaler': self.scaler,
            'metadata': metadata
        }

    def close(self):
        """Close database connection."""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Database connection closed")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Build leakage-free training dataset from Feast features'
    )
    parser.add_argument('--symbol', type=str, default='AAPL.US',
                        help='Trading symbol (default: AAPL.US)')
    parser.add_argument('--start-date', type=str, default=None,
                        help='Start date (YYYY-MM-DD), default: 1 year ago')
    parser.add_argument('--end-date', type=str, default=None,
                        help='End date (YYYY-MM-DD), default: today')
    parser.add_argument('--train-split', type=float, default=0.7,
                        help='Train/val split (default: 0.7)')
    parser.add_argument('--output', type=str, default='outputs/datasets/task_069_dataset.pkl',
                        help='Output pickle file')

    args = parser.parse_args()

    # Default dates (1 year of data)
    if args.end_date is None:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    if args.start_date is None:
        start_dt = datetime.strptime(args.end_date, '%Y-%m-%d') - timedelta(days=365)
        args.start_date = start_dt.strftime('%Y-%m-%d')

    # Build dataset
    builder = FeatureDatasetBuilder(symbol=args.symbol)
    dataset = builder.build(args.start_date, args.end_date, train_split=args.train_split)

    if not dataset:
        logger.error("Dataset building failed")
        return 1

    # Save dataset
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'wb') as f:
        pickle.dump(dataset, f)
    logger.info(f"✅ Dataset saved to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
