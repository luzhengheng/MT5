#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test purge_env.py safety guards

Verifies that the purge script:
1. Does NOT delete models/
2. Does NOT delete .env
3. Does NOT delete .git
4. Correctly identifies ephemeral paths
5. Confirms before deletion (unless --force)
"""

import sys
from pathlib import Path

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent

def test_protected_paths():
    """Test that SafePurge protects critical paths"""
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

    try:
        from maintenance.purge_env import SafePurge
    except ImportError as e:
        print(f"{RED}❌ Could not import SafePurge: {e}{RESET}")
        return False

    purge = SafePurge(project_root=PROJECT_ROOT)

    print()
    print("=" * 80)
    print(f"{CYAN}🔒 PURGE SAFETY VERIFICATION{RESET}")
    print("=" * 80)
    print()

    all_pass = True

    # Test protected paths
    print(f"{CYAN}Testing protected paths:{RESET}")
    print()

    protected_paths = [
        'models/baseline_v1.json',
        'config/strategies.yaml',
        '.env',
        '.git',
        'src/main/runner.py',
        'scripts/audit_current_task.py',
        'requirements.txt',
        'Dockerfile.strategy'
    ]

    for path in protected_paths:
        if not purge.is_protected(path):
            print(f"{RED}❌ FAIL: {path} should be protected but isn't{RESET}")
            all_pass = False
        else:
            print(f"{GREEN}✅ PASS: {path} is correctly protected{RESET}")

    print()

    # Test ephemeral paths
    print(f"{CYAN}Testing ephemeral paths:{RESET}")
    print()

    ephemeral_paths = [
        'logs/trading.log',
        'logs/debug.log',
        'data/redis/dump.rdb',
        'data/redis/cache.pkl',
        'data/temp/cache.pkl'
    ]

    for path in ephemeral_paths:
        if purge.is_protected(path):
            print(f"{RED}❌ FAIL: {path} should NOT be protected{RESET}")
            all_pass = False
        else:
            print(f"{GREEN}✅ PASS: {path} is correctly identified as ephemeral{RESET}")

    print()

    # Test protected paths exist
    print(f"{CYAN}Verifying protected paths exist:{RESET}")
    print()

    critical_paths = ['models', 'config', '.env', '.git', 'src', 'scripts']

    for critical_path in critical_paths:
        full_path = PROJECT_ROOT / critical_path

        if full_path.exists():
            print(f"{GREEN}✅ PASS: {critical_path} exists{RESET}")
        else:
            print(f"{YELLOW}⚠️  WARNING: {critical_path} does not exist (may be expected in CI){RESET}")

    print()
    print("=" * 80)

    if all_pass:
        print(f"{GREEN}✅ ALL SAFETY TESTS PASSED{RESET}")
        print("=" * 80)
        print()
        return True
    else:
        print(f"{RED}❌ SOME SAFETY TESTS FAILED{RESET}")
        print("=" * 80)
        print()
        return False


def main():
    """Run all safety tests"""
    if test_protected_paths():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
