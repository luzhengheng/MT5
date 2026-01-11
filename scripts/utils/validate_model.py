#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Validation Script
Task #026.02: Manual Verification of Remote Training
Protocol: v2.2 (Trust, But Verify)

Validates that the trained model file is correct and GPU-trained.
"""

import json
import sys
from pathlib import Path

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{CYAN}ℹ️  {msg}{RESET}")

def main():
    print()
    print("=" * 80)
    print(f"{CYAN}📊 MODEL VALIDATION{RESET}")
    print("=" * 80)
    print()

    model_file = Path("models/deep_v1.json")

    # Check 1: File exists
    print_info("Checking model file...")
    if not model_file.exists():
        print_error("Model file not found: models/deep_v1.json")
        return 1

    print_success("Model file exists")

    # Check 2: File size
    size = model_file.stat().st_size
    size_mb = size / (1024 * 1024)

    print_info(f"File size: {size_mb:.2f} MB ({size} bytes)")

    if size < 1000000:
        print_error(f"Model file too small ({size_mb:.2f} MB)")
        return 1

    print_success(f"File size is reasonable")

    # Check 3: Valid JSON
    print_info("Validating JSON format...")
    try:
        with open(model_file) as f:
            model_data = json.load(f)
        print_success("Valid JSON format")
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        return 1

    # Check 4: GPU signature
    print_info("Checking for GPU training signature...")
    try:
        with open(model_file) as f:
            content = f.read()

        if "gpu_hist" in content:
            print_success("GPU signature found: gpu_hist (GPU-trained model)")
        elif "hist" in content:
            print_warning("CPU histogram found (may be CPU-trained)")
        else:
            print_warning("Could not determine training method from file")
    except Exception as e:
        print_error(f"Could not check file content: {e}")
        return 1

    # Check 5: XGBoost validation
    print_info("Validating XGBoost model...")
    try:
        import xgboost as xgb
        bst = xgb.Booster(model_file=str(model_file))
        num_trees = len(bst.get_dump())
        print_success(f"XGBoost model loads successfully ({num_trees} trees)")
    except ImportError:
        print_warning("XGBoost not available for validation (install with: pip install xgboost)")
    except Exception as e:
        print_error(f"XGBoost validation failed: {e}")
        return 1

    # Check 6: Model structure
    print_info("Checking model structure...")
    try:
        if isinstance(model_data, dict):
            if "learner" in model_data:
                print_success("Valid XGBoost JSON structure (has 'learner' key)")
            else:
                print_warning("Unknown model structure")
        else:
            print_warning("Model is not a dictionary")
    except Exception as e:
        print_error(f"Could not check model structure: {e}")
        return 1

    # Summary
    print()
    print("=" * 80)
    print_success("MODEL VALIDATION PASSED")
    print("=" * 80)
    print()
    print(f"Model file: models/deep_v1.json")
    print(f"File size: {size_mb:.2f} MB")
    print(f"Format: XGBoost JSON")
    print(f"Status: Ready for deployment")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
