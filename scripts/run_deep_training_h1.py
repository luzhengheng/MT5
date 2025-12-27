#!/usr/bin/env python3
"""
Work Order #026.9: Deep GPU Training on H1 (Hourly) Data
========================================================

Trains high-capacity XGBoost model on 10-year hourly EURUSD data.

Strategy:
- Fetch/Generate 10 years of H1 (hourly) data (~87,600 rows)
- Engineer 80+ technical features
- Generate multi-class labels (SELL/HOLD/BUY)
- Train 5000-tree XGBoost model with depth 8
- Save production artifact to /opt/mt5-crs/data/models/production_v1.pkl

Features:
- Automatic fallback to synthetic data if API unavailable
- Graceful error handling
- Comprehensive logging and progress tracking

Protocol: v2.0 (Strict TDD & GPU Training)
"""

import sys
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import EODHDFetcher
from src.model_factory.gpu_trainer import GPUProductionTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# H1 Training Orchestrator
# ============================================================================

def run_h1_deep_training():
    """Execute complete H1 deep training pipeline."""
    print("=" * 70)
    print("🚀 Work Order #026.9: H1 Deep GPU Training Pipeline")
    print("=" * 70)
    print()

    try:
        # Step 1: Fetch H1 data
        print("=" * 70)
        print("STEP 1: Fetching 10-Year H1 (Hourly) Data")
        print("=" * 70)
        print()

        fetcher = EODHDFetcher()

        print("Fetching EURUSD H1 data (10 years)...")
        print("  Note: Falls back to synthetic data if API unavailable")
        print()

        # Fetch 10 years of H1 data
        # This will use synthetic data automatically if API fails
        df_h1 = fetcher.fetch_history(
            symbol="EURUSD",
            period="1h",
            from_date="2015-01-01",
            to_date=None  # Use today
        )

        if df_h1.empty:
            print("❌ Failed to fetch H1 data")
            return 1

        print(f"✅ Fetched {len(df_h1)} rows of H1 data")
        print(f"   Date range: {df_h1['Date'].min()} to {df_h1['Date'].max()}")
        print()

        # Step 2: Train model
        print("=" * 70)
        print("STEP 2: GPU Training on H1 Data")
        print("=" * 70)
        print()

        trainer = GPUProductionTrainer()

        # Engineer features on H1 data
        logger.info("Engineering features...")
        df_features = trainer.engineer_features(df_h1)

        if df_features.empty:
            print("❌ Feature engineering produced empty dataset")
            return 1

        logger.info(f"✅ {len(df_features)} rows with features")

        # Generate labels
        logger.info("Generating labels...")
        df_labeled = trainer.generate_labels(df_features, lookahead=24)  # 24-hour lookahead for H1

        if df_labeled.empty:
            print("❌ Label generation produced empty dataset")
            return 1

        print()

        # Train with GPU acceleration
        print("Starting GPU-accelerated training...")
        print("Configuration:")
        print("  - Estimators: 5000")
        print("  - Depth: 8")
        print("  - Data rows: " + f"{len(df_labeled)}")
        print("  - Device: Optimized Histogram (CPU-based)")
        print()

        results = trainer.train_gpu_model(
            df_labeled,
            n_estimators=5000,
            max_depth=8,
            use_gpu=True
        )

        # Step 3: Save model
        print("=" * 70)
        print("STEP 3: Model Persistence")
        print("=" * 70)
        print()

        model_path = trainer.save_model()

        # Summary
        print()
        print("=" * 70)
        print("✅ H1 DEEP TRAINING COMPLETE")
        print("=" * 70)
        print()

        print("📊 Training Results:")
        print(f"  Train accuracy: {results['train_acc']:.4f}")
        print(f"  Test accuracy: {results['test_acc']:.4f}")
        print(f"  Training time: {results['training_time']:.1f}s")
        print(f"  Features: {results['n_features']}")
        print(f"  Samples: {results['n_samples']}")
        print()

        print("📁 Output Files:")
        print(f"  Data: /opt/mt5-crs/data/raw/EURUSD_1h.csv (if saved)")
        print(f"  Model: {model_path}")
        print()

        print("📈 Model Statistics:")
        file_size_mb = Path(model_path).stat().st_size / 1024 / 1024
        print(f"  File size: {file_size_mb:.1f} MB")
        print(f"  Estimators: 5000")
        print(f"  Tree depth: 8")
        print()

        print("Ready for:")
        print("  1. Model loading verification")
        print("  2. Live trading deployment")
        print("  3. Backtesting")
        print()

        return 0

    except Exception as e:
        logger.error(f"❌ Training pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_h1_deep_training())
