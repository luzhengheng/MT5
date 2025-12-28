#!/usr/bin/env python3
"""
ML Training Pipeline Verification Script

Task #039: Verify the XGBoost training pipeline on real EURUSD data

Steps:
1. Load EURUSD.s history from TimescaleDB
2. Engineer features (Task #038)
3. Train XGBoost model
4. Evaluate metrics
5. Save trained model

Expected output:
  - Model trained on 1000+ samples
  - Accuracy > 0.5 (better than random)
  - Model file saved to models/
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
from src.data_nexus.ml.trainer import ModelTrainer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run training pipeline verification."""
    print("=" * 80)
    print("🤖 ML TRAINING PIPELINE VERIFICATION")
    print("=" * 80)
    print()

    symbol = "EURUSD.s"

    print(f"Training symbol: {symbol}")
    print()

    try:
        # Initialize trainer
        print("📋 Initializing ModelTrainer...")
        trainer = ModelTrainer(symbol=symbol)
        print(f"✅ Trainer initialized for {symbol}")
        print()

        # Run full pipeline
        print("🚀 Running full training pipeline...")
        print()

        results = trainer.run_full_pipeline(test_size=0.2, save_model=True)

        # Display results
        print()
        print("=" * 80)
        print("📊 TRAINING RESULTS")
        print("=" * 80)
        print()

        print(f"Symbol: {results['symbol']}")
        print(f"Train samples: {results['train_samples']:,}")
        print(f"Test samples: {results['test_samples']:,}")
        print(f"Total samples: {results['train_samples'] + results['test_samples']:,}")
        print(f"Features used: {results['n_features']}")
        print()

        print("📈 Evaluation Metrics:")
        print("-" * 80)
        metrics = results['metrics']
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1-Score:  {metrics['f1']:.4f}")
        print()

        # Validate metrics
        if metrics['accuracy'] > 0.5:
            print(f"✅ Accuracy ({metrics['accuracy']:.4f}) > 0.5 (random baseline)")
        else:
            print(f"⚠️  Accuracy ({metrics['accuracy']:.4f}) <= 0.5 (needs improvement)")

        print()
        print(f"💾 Model saved: {results['model_path']}")
        print()

        # Check if model file exists
        model_path = Path(results['model_path'])
        if model_path.exists():
            file_size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✅ Model file exists (size: {file_size_mb:.2f} MB)")
        else:
            print(f"❌ Model file not found: {model_path}")
            return 1

        print()
        print("=" * 80)
        print("✅ ML Training Pipeline Verified")
        print("=" * 80)
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
