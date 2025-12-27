#!/usr/bin/env python3
"""
Work Order #025: Baseline Model Deployment
============================================

Deployment Script - Generates and deploys baseline model

This script:
1. Calls train_baseline_model() from model_factory
2. Verifies the .pkl file exists
3. Checks file size and integrity
4. Reports success/failure

Protocol: v2.0 (Strict TDD)
"""

import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_factory import train_baseline_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Deployment Functions
# ============================================================================

def deploy_baseline_model(output_path: str = None) -> bool:
    """
    Deploy baseline model by training and saving.

    Args:
        output_path: Path to save model (default: data/models/baseline_v1.pkl)

    Returns:
        True if deployment successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info("📦 Baseline Model Deployment")
    logger.info("=" * 70)
    print()

    try:
        # Train and save model
        logger.info("Training baseline model...")
        model_path = train_baseline_model(output_path=output_path)
        print()

        # Verify file exists
        model_file = Path(model_path)
        if not model_file.exists():
            logger.error(f"❌ Model file not found: {model_path}")
            return False

        logger.info(f"✅ Model file exists: {model_file}")

        # Check file size
        file_size = model_file.stat().st_size
        logger.info(f"✅ File size: {file_size / 1024:.1f} KB")

        if file_size < 1000:
            logger.warning(f"⚠️  File size seems small: {file_size} bytes")

        # Verify file is readable
        try:
            import pickle
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"✅ Model loaded successfully")
            logger.info(f"   Model type: {type(model).__name__}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False

        print()
        print("=" * 70)
        logger.info("✅ DEPLOYMENT SUCCESSFUL")
        print("=" * 70)
        print()
        logger.info(f"Model deployed to: {model_path}")
        logger.info(f"Ready for LiveStrategyAdapter loading")
        print()

        return True

    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run deployment."""
    print("=" * 70)
    print("📦 Work Order #025: Baseline Model Deployment")
    print("=" * 70)
    print()

    success = deploy_baseline_model()

    if success:
        print("🎯 Next steps:")
        print("  1. Run verification: python3 scripts/verify_model_loading.py")
        print("  2. Run audit: python3 scripts/audit_current_task.py")
        print("  3. Test live adapter: python3 src/strategy/live_adapter.py")
        print()
        return 0
    else:
        print("❌ Deployment failed")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
