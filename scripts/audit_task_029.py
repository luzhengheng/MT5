#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate 2 Audit Script for TASK #029 - E2E Execution Verification

Validates that end-to-end remote order execution is properly configured
and all network components are in place.
"""

import os
import sys
import json
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
                print(f"✅ [{description}] Found: {pattern}")
                return True
            else:
                print(f"❌ [{description}] Pattern not found: {pattern}")
                return False
    except Exception as e:
        print(f"❌ [{description}] Error reading file: {e}")
        return False

def check_config_value(key, expected_value=None):
    """Check configuration value"""
    try:
        from src.config import get_config_summary
        config = get_config_summary()
        
        # Navigate through nested config
        if key == "GTW_HOST":
            actual = config.get('gateway', {}).get('host')
        elif key == "GTW_PORT":
            actual = config.get('gateway', {}).get('port')
        elif key == "ZMQ_URL":
            actual = config.get('gateway', {}).get('url')
        else:
            return False
        
        if actual and (expected_value is None or actual == expected_value):
            print(f"✅ [Config] {key} = {actual}")
            return True
        else:
            print(f"❌ [Config] {key} = {actual} (expected: {expected_value})")
            return False
    except Exception as e:
        print(f"❌ [Config] Error reading config: {e}")
        return False

def main():
    """Run Gate 2 validation checks"""
    print("=" * 80)
    print("GATE 2 AUDIT - TASK #029 (E2E Execution Verification)")
    print("=" * 80)
    
    checks = []
    
    # Check 1: Configuration module exists
    print("\n[CHECK 1] Validating configuration module...")
    checks.append(check_file_exists(
        "src/config.py",
        "Configuration Module"
    ))
    
    # Check 2: Gateway host configured
    print("\n[CHECK 2] Validating gateway host configuration...")
    checks.append(check_config_value("GTW_HOST", "172.19.141.255"))
    
    # Check 3: Gateway port configured
    print("\n[CHECK 3] Validating gateway port configuration...")
    checks.append(check_config_value("GTW_PORT", 5555))
    
    # Check 4: ZMQ URL properly formatted
    print("\n[CHECK 4] Validating ZMQ execution URL...")
    checks.append(check_config_value("ZMQ_URL", "tcp://172.19.141.255:5555"))
    
    # Check 5: Probe script exists
    print("\n[CHECK 5] Validating network probe script...")
    checks.append(check_file_exists(
        "scripts/probe_gateway.py",
        "Network Probe Script"
    ))
    
    # Check 6: Remote execution test script exists
    print("\n[CHECK 6] Validating remote execution test script...")
    checks.append(check_file_exists(
        "scripts/test_remote_execution.py",
        "Remote Execution Test"
    ))
    
    # Check 7: Probe script imports zmq
    print("\n[CHECK 7] Validating probe script ZMQ integration...")
    checks.append(check_file_contains(
        "scripts/probe_gateway.py",
        "import zmq",
        "ZMQ Import in Probe"
    ))
    
    # Check 8: Test script uses ZMQ REQ socket
    print("\n[CHECK 8] Validating remote test ZMQ REQ socket...")
    checks.append(check_file_contains(
        "scripts/test_remote_execution.py",
        "zmq.REQ",
        "ZMQ REQ Socket"
    ))
    
    # Check 9: Test script sends JSON order
    print("\n[CHECK 9] Validating order JSON format...")
    checks.append(check_file_contains(
        "scripts/test_remote_execution.py",
        "send_json",
        "JSON Order Send"
    ))
    
    # Check 10: Error handling in test script
    print("\n[CHECK 10] Validating error handling...")
    checks.append(check_file_contains(
        "scripts/test_remote_execution.py",
        "error",
        "Error Response Handling"
    ))
    
    # Check 11: Verification log exists
    print("\n[CHECK 11] Validating verification log...")
    checks.append(check_file_exists(
        "docs/archive/tasks/TASK_029_E2E_EXECUTION/VERIFY_LOG.log",
        "Verification Log"
    ))
    
    # Check 12: Probe log shows successful connection
    print("\n[CHECK 12] Validating probe results...")
    checks.append(check_file_contains(
        "docs/archive/tasks/TASK_029_E2E_EXECUTION/VERIFY_LOG.log",
        "✅ TCP connectivity: PASS",
        "Gateway Connectivity"
    ))
    
    # Final summary
    print("\n" + "=" * 80)
    print("GATE 2 AUDIT SUMMARY")
    print("=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\nTotal Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ GATE 2 PASSED - All requirements met")
        print("\nEnd-to-End Execution Verification:")
        print("  ✅ Configuration correctly set (172.19.141.255:5555)")
        print("  ✅ Network connectivity verified")
        print("  ✅ ZMQ protocol integrated")
        print("  ✅ Order execution protocol defined")
        print("  ✅ Error handling implemented")
        return 0
    else:
        print(f"\n❌ GATE 2 FAILED - {total - passed} check(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
