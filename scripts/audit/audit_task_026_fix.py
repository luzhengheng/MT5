#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Script for TASK #026-FIX: Security Hardening

Validates that:
1. No hardcoded passwords in feature_store.yaml
2. Credentials use environment variable syntax
3. registry.db is properly .gitignored
"""

import os
import sys
from pathlib import Path

def check_hardcoded_password():
    """
    Verify feature_store.yaml doesn't contain hardcoded passwords

    Returns:
        bool: True if no hardcoded passwords found, False otherwise
    """
    yaml_path = Path("src/feature_store/feature_store.yaml")

    if not yaml_path.exists():
        print("❌ FAIL: feature_store.yaml not found")
        return False

    with open(yaml_path, 'r') as f:
        content = f.read()

    # Check for hardcoded password patterns (MUST FAIL before fix)
    hardcoded_patterns = [
        'password: password',
        'password: "password"',
        "password: 'password'",
        'password: changeme',
        'password: "changeme"',
        "password: 'changeme'",
    ]

    for pattern in hardcoded_patterns:
        if pattern in content:
            print(f"❌ FAIL: Found hardcoded password pattern: {pattern}")
            return False

    # Check that password uses environment variable syntax
    if 'password: "${POSTGRES_PASSWORD}"' not in content:
        print("❌ FAIL: Password not using environment variable syntax")
        print("   Expected: password: \"${POSTGRES_PASSWORD}\"")
        print("   Got:")
        for line in content.split('\n'):
            if 'password' in line.lower():
                print(f"   {line}")
        return False

    print("✅ PASS: No hardcoded passwords found")
    return True


def check_gitignore():
    """
    Verify registry.db is in .gitignore

    Returns:
        bool: True if properly gitignored, False otherwise
    """
    gitignore_path = Path(".gitignore")

    if not gitignore_path.exists():
        print("⚠️  WARNING: .gitignore not found")
        return False

    with open(gitignore_path, 'r') as f:
        content = f.read()

    if "src/feature_store/registry.db" not in content:
        print("❌ FAIL: registry.db not found in .gitignore")
        return False

    if "src/feature_store/registry.db-wal" not in content:
        print("⚠️  WARNING: registry.db-wal not found in .gitignore")
        # Don't fail on this, it's optional
        return True

    print("✅ PASS: registry.db properly gitignored")
    return True


def main():
    print("\n" + "="*60)
    print("AUDIT: TASK #026-FIX Security Hardening Checks")
    print("="*60 + "\n")

    # Check 1: Hardcoded passwords
    print("[CHECK 1] Hardcoded password detection...")
    password_check = check_hardcoded_password()

    print()

    # Check 2: .gitignore verification
    print("[CHECK 2] .gitignore verification...")
    gitignore_check = check_gitignore()

    print("\n" + "="*60)

    if password_check and gitignore_check:
        print("✅ ALL CHECKS PASSED - Security hardening complete")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Security issues remain")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
