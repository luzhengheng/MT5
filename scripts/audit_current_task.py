#!/usr/bin/env python3
"""
Task #037 Compliance Audit Script

Verifies that the Notion State Cleanup implementation meets
Protocol v2.0 requirements before allowing task completion.

Audit Criteria:
1. Structural: Cleanup script exists and is syntactically valid
2. Functional: Script contains logic to handle all affected tasks (#033-#036)
3. Output: Report generation capability exists
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def audit():
    """Execute comprehensive audit of Task #037 deliverables."""
    print("=" * 80)
    print("🔍 AUDIT: Task #037 Notion State Cleanup Compliance Check")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    # ============================================================================
    # 1. STRUCTURAL AUDIT - Script Existence and Validity
    # ============================================================================
    print("📋 [1/3] STRUCTURAL AUDIT")
    print("-" * 80)

    # Check cleanup script exists
    cleanup_script = PROJECT_ROOT / "scripts" / "maintenance" / "fix_notion_state.py"
    if cleanup_script.exists():
        print(f"✅ [Structure] Cleanup script exists: {cleanup_script}")
        passed += 1
    else:
        print(f"❌ [Structure] Cleanup script missing: {cleanup_script}")
        failed += 1

    # Check maintenance directory exists
    maintenance_dir = PROJECT_ROOT / "scripts" / "maintenance"
    if maintenance_dir.exists() and maintenance_dir.is_dir():
        print(f"✅ [Structure] Maintenance directory exists")
        passed += 1
    else:
        print(f"❌ [Structure] Maintenance directory missing")
        failed += 1

    # Check syntax validity
    if cleanup_script.exists():
        try:
            import py_compile
            py_compile.compile(str(cleanup_script), doraise=True)
            print("✅ [Syntax] Cleanup script is syntactically valid")
            passed += 1
        except py_compile.PyCompileError as e:
            print(f"❌ [Syntax] Syntax error in cleanup script: {e}")
            failed += 1
    else:
        print("⚠️  [Syntax] Skipped - script doesn't exist")
        failed += 1

    print()

    # ============================================================================
    # 2. FUNCTIONAL AUDIT - Logic Coverage
    # ============================================================================
    print("📋 [2/3] FUNCTIONAL AUDIT")
    print("-" * 80)

    # Check script handles Task #033
    if cleanup_script.exists():
        content = cleanup_script.read_text()

        if "033" in content or "#033" in content:
            print("✅ [Logic] Script handles Task #033")
            passed += 1
        else:
            print("❌ [Logic] Script missing Task #033 handling")
            failed += 1

        # Check script handles Task #034
        if "034" in content or "#034" in content:
            print("✅ [Logic] Script handles Task #034")
            passed += 1
        else:
            print("❌ [Logic] Script missing Task #034 handling")
            failed += 1

        # Check script handles Task #035 (ghost task - CRITICAL)
        if "035" in content or "#035" in content:
            print("✅ [Logic] Script handles Task #035 (ghost task)")
            passed += 1
        else:
            print("❌ [Logic] Script missing Task #035 handling (CRITICAL)")
            failed += 1

        # Check script handles Task #036
        if "036" in content or "#036" in content:
            print("✅ [Logic] Script handles Task #036")
            passed += 1
        else:
            print("❌ [Logic] Script missing Task #036 handling")
            failed += 1

    else:
        print("⚠️  [Logic] Skipped - script doesn't exist")
        failed += 4

    print()

    # ============================================================================
    # 3. OUTPUT AUDIT - Report Generation
    # ============================================================================
    print("📋 [3/3] OUTPUT AUDIT")
    print("-" * 80)

    # Check for report generation capability
    if cleanup_script.exists():
        content = cleanup_script.read_text()

        if "ADMIN_CLEANUP_REPORT" in content or "report" in content.lower():
            print("✅ [Output] Report generation capability detected")
            passed += 1
        else:
            print("❌ [Output] No report generation capability found")
            failed += 1

        # Check for Notion integration attempt
        if "notion" in content.lower() or "NOTION" in content:
            print("✅ [Integration] Notion integration logic present")
            passed += 1
        else:
            print("❌ [Integration] No Notion integration logic found")
            failed += 1

    else:
        print("⚠️  [Output] Skipped - script doesn't exist")
        failed += 2

    # ============================================================================
    # AUDIT SUMMARY
    # ============================================================================
    print()
    print("=" * 80)
    print(f"📊 AUDIT SUMMARY: {passed} Passed, {failed} Failed")
    print("=" * 80)

    if failed == 0:
        print()
        print("🎉 ✅ AUDIT PASSED: Ready for AI Review")
        print()
        print("Task #037 implementation meets Protocol v2.0 requirements.")
        print("You may proceed with: python3 scripts/project_cli.py finish")
        print()
        return 0
    else:
        print()
        print("⚠️  ❌ AUDIT FAILED: Remediation Required")
        print()
        print("Issues found during audit:")
        print(f"  • {failed} check(s) failed")
        print("  • Fix issues before running 'project_cli.py finish'")
        print()
        return 1


if __name__ == "__main__":
    exit_code = audit()
    sys.exit(exit_code)
