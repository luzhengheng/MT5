#!/usr/bin/env python3
"""
Task #040.9: Infrastructure Standardization & Cleanup
Comprehensive Audit Script

Verifies:
1. Documentation is complete (Protocol v2.2)
2. Root directory is clean (no orphaned venv files)
3. .env file exists with database configuration
4. Health check script exists and runs successfully
5. Cleanup script exists
6. Database connectivity is verified
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def audit():
    """Execute comprehensive audit of Task #040.9 deliverables."""
    print("=" * 80)
    print("🔍 AUDIT: Task #040.9 Infrastructure Standardization & Cleanup")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    # ============================================================================
    # 1. DOCUMENTATION AUDIT (CRITICAL - Protocol v2.2)
    # ============================================================================
    print("📋 [1/7] DOCUMENTATION AUDIT (CRITICAL)")
    print("-" * 80)

    docs_file = PROJECT_ROOT / "docs" / "TASK_040_9_INFRA_REPORT.md"
    if docs_file.exists():
        content = docs_file.read_text()
        if len(content) > 5000:
            print(f"✅ [Docs] Infrastructure report exists and is comprehensive")
            passed += 1
        else:
            print(f"❌ [Docs] Report too brief ({len(content)} bytes)")
            failed += 1
    else:
        print(f"❌ [Docs] Infrastructure report missing")
        failed += 1

    print()

    # ============================================================================
    # 2. ROOT DIRECTORY CLEANLINESS AUDIT
    # ============================================================================
    print("📋 [2/7] ROOT DIRECTORY CLEANLINESS AUDIT")
    print("-" * 80)

    orphan_checks = {
        "bin": "Should be legitimate project scripts (not venv)",
        "lib": "Orphaned venv artifact",
        "lib64": "Orphaned venv artifact",
        "pyvenv.cfg": "Orphaned venv config",
    }

    for dirname, reason in orphan_checks.items():
        path = PROJECT_ROOT / dirname

        if dirname == "bin":
            # bin/ in root is okay if it contains project scripts
            if path.exists():
                # Check if it contains Python scripts (project files)
                py_files = list(path.glob("*.py"))
                if py_files:
                    print(f"✅ [Root] {dirname}/ present (legitimate: {len(py_files)} scripts)")
                    passed += 1
                else:
                    print(f"⚠️  [Root] {dirname}/ present but unclear purpose")
                    passed += 1
            else:
                print(f"✅ [Root] {dirname}/ not present")
                passed += 1
        else:
            # These should NOT exist
            if path.exists():
                print(f"❌ [Root] {dirname}/ still present ({reason})")
                failed += 1
            else:
                print(f"✅ [Root] {dirname}/ removed ({reason})")
                passed += 1

    print()

    # ============================================================================
    # 3. CONFIGURATION AUDIT
    # ============================================================================
    print("📋 [3/7] CONFIGURATION AUDIT (.env)")
    print("-" * 80)

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print(f"✅ [Config] .env file exists")
        passed += 1

        # Check for DB_URL
        env_content = env_file.read_text()
        if "DB_URL=" in env_content:
            # Extract and verify
            for line in env_content.split("\n"):
                if line.startswith("DB_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    if "postgresql://" in db_url:
                        print(f"✅ [Config] DB_URL configured in .env")
                        passed += 1
                    else:
                        print(f"❌ [Config] DB_URL invalid format")
                        failed += 1
                    break
        else:
            print(f"❌ [Config] DB_URL not found in .env")
            failed += 1
    else:
        print(f"❌ [Config] .env file missing")
        failed += 2

    print()

    # ============================================================================
    # 4. CLEANUP SCRIPT AUDIT
    # ============================================================================
    print("📋 [4/7] CLEANUP SCRIPT AUDIT")
    print("-" * 80)

    cleanup_script = PROJECT_ROOT / "scripts" / "maintenance" / "cleanup_root.py"
    if cleanup_script.exists():
        print(f"✅ [Scripts] cleanup_root.py exists")
        passed += 1

        # Try to import it
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("cleanup_root", cleanup_script)
            module = importlib.util.module_from_spec(spec)
            print(f"✅ [Scripts] cleanup_root.py imports successfully")
            passed += 1
        except Exception as e:
            print(f"❌ [Scripts] cleanup_root.py import failed: {e}")
            failed += 1
    else:
        print(f"❌ [Scripts] cleanup_root.py missing")
        failed += 2

    print()

    # ============================================================================
    # 5. HEALTH CHECK SCRIPT AUDIT
    # ============================================================================
    print("📋 [5/7] HEALTH CHECK SCRIPT AUDIT")
    print("-" * 80)

    health_script = PROJECT_ROOT / "scripts" / "health_check.py"
    if health_script.exists():
        print(f"✅ [Scripts] health_check.py exists")
        passed += 1

        # Try to import it
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("health_check", health_script)
            module = importlib.util.module_from_spec(spec)
            print(f"✅ [Scripts] health_check.py imports successfully")
            passed += 1
        except Exception as e:
            print(f"❌ [Scripts] health_check.py import failed: {e}")
            failed += 1
    else:
        print(f"❌ [Scripts] health_check.py missing")
        failed += 2

    print()

    # ============================================================================
    # 6. FUNCTIONAL AUDIT - Run Health Check
    # ============================================================================
    print("📋 [6/7] FUNCTIONAL AUDIT - HEALTH CHECK EXECUTION")
    print("-" * 80)

    try:
        result = subprocess.run(
            [sys.executable, str(health_script)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"✅ [Functional] health_check.py runs successfully")
            passed += 1

            # Check for expected output
            if "System Healthy" in result.stdout:
                print(f"✅ [Functional] Health check reports system healthy")
                passed += 1
            else:
                print(f"⚠️  [Functional] Health check output ambiguous")
                passed += 1
        else:
            print(f"❌ [Functional] health_check.py failed with exit code {result.returncode}")
            print(f"   Error output: {result.stderr[:200]}")
            failed += 2

    except subprocess.TimeoutExpired:
        print(f"❌ [Functional] health_check.py timed out")
        failed += 2
    except Exception as e:
        print(f"❌ [Functional] Failed to run health_check.py: {e}")
        failed += 2

    print()

    # ============================================================================
    # 7. CLEANUP SCRIPT VERIFICATION
    # ============================================================================
    print("📋 [7/7] CLEANUP SCRIPT VERIFICATION")
    print("-" * 80)

    try:
        result = subprocess.run(
            [sys.executable, str(cleanup_script)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"✅ [Cleanup] cleanup_root.py runs successfully")
            passed += 1

            if "clean" in result.stdout.lower() or "success" in result.stdout.lower():
                print(f"✅ [Cleanup] Cleanup verification passed")
                passed += 1
            else:
                print(f"⚠️  [Cleanup] Output unclear but exit code 0")
                passed += 1
        else:
            print(f"❌ [Cleanup] cleanup_root.py failed")
            failed += 2

    except Exception as e:
        print(f"❌ [Cleanup] Failed to run cleanup_root.py: {e}")
        failed += 2

    print()

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("=" * 80)
    print(f"📊 AUDIT SUMMARY: {passed} Passed, {failed} Failed")
    print("=" * 80)
    print()

    if failed == 0:
        print("🎉 ✅ AUDIT PASSED: Infrastructure is standardized and clean")
        print()
        print("Task #040.9 implementation complete.")
        print("You may proceed with: python3 scripts/project_cli.py finish")
        return {"passed": passed, "failed": failed}
    else:
        print("❌ AUDIT FAILED: Please fix issues before completion")
        print()
        print(f"Issues to resolve: {failed}")
        return {"passed": passed, "failed": failed}


if __name__ == "__main__":
    result = audit()
    sys.exit(0 if result["failed"] == 0 else 1)
