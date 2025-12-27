#!/usr/bin/env python3
"""
Work Order #026: Deep Training Orchestrator
============================================

Orchestrates the complete GPU training pipeline:
1. Fetch 10 years of Forex data (EURUSD, XAUUSD)
2. Train GPU-accelerated XGBoost model
3. Save production model artifact

Protocol: v2.0 (Strict TDD & GPU Training)
"""

import sys
import os
import logging
from pathlib import Path

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
# Training Orchestrator
# ============================================================================

def run_deep_training():
    """Execute complete deep training pipeline."""
    print("=" * 70)
    print("🚀 Work Order #026: Deep GPU Training Pipeline")
    print("=" * 70)
    print()

    try:
        # Step 1: Fetch data
        print("=" * 70)
        print("STEP 1: Fetching Historical Data")
        print("=" * 70)
        print()

        fetcher = EODHDFetcher()

        print("Fetching EURUSD & XAUUSD (10 years + 120 days intraday)...")
        print()

        results = fetcher.fetch_deep_history(symbols=['EURUSD', 'XAUUSD'])

        print()
        print("Data fetching complete:")
        for symbol, data in results.items():
            print(f"  {symbol}:")
            print(f"    Daily:  {len(data['daily'])} rows ({data['daily']['Date'].min()} - {data['daily']['Date'].max()})")
            print(f"    Hourly: {len(data['hourly'])} rows ({data['hourly']['Date'].min()} - {data['hourly']['Date'].max()})")

        print()

        # Step 2: Train model on largest dataset
        print("=" * 70)
        print("STEP 2: GPU Training on EURUSD Daily Data")
        print("=" * 70)
        print()

        trainer = GPUProductionTrainer()

        # Load EURUSD daily (largest dataset)
        df = trainer.load_data(symbol="EURUSD", period="d")

        # Engineer features
        df_features = trainer.engineer_features(df)

        # Generate labels
        df_labeled = trainer.generate_labels(df_features)

        # Train with GPU acceleration
        print("Starting GPU-accelerated training...")
        print("This will use NVIDIA A10 GPU for fast training")
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
        print("✅ DEEP TRAINING COMPLETE")
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
        print(f"  Data: /opt/mt5-crs/data/raw/")
        print(f"  Model: {model_path}")
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
    sys.exit(run_deep_training())
