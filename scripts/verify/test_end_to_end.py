import sys
import os
import yaml
import xgboost as xgb
import numpy as np
from pathlib import Path

def get_project_root():
    """Get absolute path to project root."""
    return Path(__file__).parent.parent

def load_config(config_path):
    """Load and validate YAML configuration."""
    if not config_path.exists():
        raise FileNotFoundError(f"❌ Config missing: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if not config or 'strategies' not in config or not config['strategies']:
        raise ValueError("❌ Invalid config structure: missing or empty strategies")

    return config

def validate_model_file(model_path):
    """Validate model file exists and is readable."""
    if not model_path.exists():
        raise FileNotFoundError(f"❌ Model file not found at {model_path}")

    # Check file size is reasonable (not empty, not suspiciously small)
    file_size = model_path.stat().st_size
    if file_size < 10_000:  # At least 10KB for a valid model
        raise ValueError(f"❌ Model file suspiciously small ({file_size} bytes). Likely corrupted or invalid.")

    return file_size

def load_and_inspect_model(model_path):
    """Load model using XGBoost API and inspect its properties."""
    try:
        bst = xgb.Booster()
        bst.load_model(str(model_path))
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load model with XGBoost: {e}") from e

    # Get actual feature count from model
    num_features = bst.num_features()

    # Get model complexity
    dump = bst.get_dump()
    num_trees = len(dump)

    return {
        'booster': bst,
        'num_features': num_features,
        'num_trees': num_trees,
    }

def test_model_inference(bst, num_features):
    """Test that model can perform inference with correct feature dimensions."""
    if num_features <= 0:
        raise ValueError(f"❌ Invalid feature count: {num_features}")

    try:
        # Create dummy data with correct number of features
        dummy_data = xgb.DMatrix(np.random.rand(1, num_features))
        predictions = bst.predict(dummy_data)

        if predictions is None or len(predictions) == 0:
            raise ValueError("❌ Model prediction returned empty result")

        return predictions[0]
    except Exception as e:
        raise RuntimeError(f"❌ Model inference failed: {e}") from e

def main():
    """Main end-to-end test execution."""
    print("🚀 Starting End-to-End Logic & Model Verification...")
    print()

    try:
        # Step 1: Load configuration
        print("📋 Step 1: Loading configuration...")
        project_root = get_project_root()
        config_path = project_root / 'config' / 'live_strategies.yaml'
        config = load_config(config_path)

        model_path_str = config['strategies'][0]['model_path']
        model_path = project_root / model_path_str
        print(f"   Configuration points to: {model_path_str}")
        print()

        # Step 2: Validate model file
        print("📦 Step 2: Validating model file...")
        file_size = validate_model_file(model_path)
        file_size_kb = file_size / 1024
        print(f"   File Size: {file_size_kb:.2f} KB")
        print()

        # Step 3: Load and inspect model
        print("🔧 Step 3: Loading and inspecting model...")
        model_info = load_and_inspect_model(model_path)
        bst = model_info['booster']
        num_features = model_info['num_features']
        num_trees = model_info['num_trees']

        print(f"   ✅ XGBoost Engine loaded the model successfully.")
        print(f"   🌲 Model Complexity: {num_trees} trees")
        print(f"   📊 Feature Requirements: {num_features} features")
        print()

        # Step 4: Test model inference
        print("⚙️  Step 4: Testing model inference...")
        prediction = test_model_inference(bst, num_features)
        print(f"   ✅ Model inference successful. Sample prediction: {prediction:.6f}")
        print()

        # Summary
        print("=" * 70)
        print("✅ E2E Test Successful: System is correctly configured")
        print("=" * 70)
        print(f"Model: {model_path_str}")
        print(f"Trees: {num_trees}")
        print(f"Features: {num_features}")
        print(f"File Size: {file_size_kb:.2f} KB")
        print("System ready for live trading.")
        print()

        return 0

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"\n❌ ERROR: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
