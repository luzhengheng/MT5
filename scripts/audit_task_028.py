#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate 1 Audit Script for TASK #028 - Strategy Engine

Validates that all deliverables meet minimum requirements before AI review.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ [{description}] File exists: {filepath}")
        return True
    else:
        print(f"❌ [{description}] File missing: {filepath}")
        return False

def check_file_contains(filepath, pattern, description):
    """Check if a file contains a specific pattern"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if pattern in content:
                print(f"✅ [{description}] Found pattern: {pattern}")
                return True
            else:
                print(f"❌ [{description}] Pattern not found: {pattern}")
                return False
    except Exception as e:
        print(f"❌ [{description}] Error reading file: {e}")
        return False

def main():
    """Run Gate 1 validation checks"""
    print("="*80)
    print("GATE 1 AUDIT - TASK #028 (Strategy Engine)")
    print("="*80)
    
    checks = []
    
    # Check 1: Strategy engine exists
    print("\n[CHECK 1] Validating strategy engine file...")
    checks.append(check_file_exists(
        "src/strategy/engine.py",
        "Strategy Engine"
    ))
    
    # Check 2: Imports shared feature engineering
    print("\n[CHECK 2] Validating feature engineering import...")
    checks.append(check_file_contains(
        "src/strategy/engine.py",
        "from src.features.engineering import",
        "Feature Engineering Import"
    ))
    
    # Check 3: ZMQ SUB socket
    print("\n[CHECK 3] Validating ZMQ SUB (market data)...")
    checks.append(check_file_contains(
        "src/strategy/engine.py",
        "zmq.SUB",
        "ZMQ SUB Socket"
    ))
    
    # Check 4: ZMQ REQ socket
    print("\n[CHECK 4] Validating ZMQ REQ (execution)...")
    checks.append(check_file_contains(
        "src/strategy/engine.py",
        "zmq.REQ",
        "ZMQ REQ Socket"
    ))
    
    # Check 5: Test script exists
    print("\n[CHECK 5] Validating test script...")
    checks.append(check_file_exists(
        "scripts/test_live_inference.py",
        "Live Inference Test"
    ))
    
    # Check 6: Model loading
    print("\n[CHECK 6] Validating model loading...")
    checks.append(check_file_contains(
        "src/strategy/engine.py",
        "PricePredictor",
        "Model Loading"
    ))
    
    # Check 7: compute_features usage
    print("\n[CHECK 7] Validating compute_features() call...")
    checks.append(check_file_contains(
        "src/strategy/engine.py",
        "compute_features",
        "Feature Computation"
    ))
    
    # Check 8: Latency logging
    print("\n[CHECK 8] Validating latency metrics...")
    checks.append(check_file_contains(
        "src/strategy/engine.py",
        "latency",
        "Latency Metrics"
    ))
    
    # Final summary
    print("\n" + "="*80)
    print("GATE 1 AUDIT SUMMARY")
    print("="*80)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\nTotal Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ GATE 1 PASSED - All requirements met")
        return 0
    else:
        print(f"\n❌ GATE 1 FAILED - {total - passed} check(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
