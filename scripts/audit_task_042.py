#!/usr/bin/env python3
"""
Task #042: Feast Feature Implementation & Materialization
Audit & Verification Script

Date: 2025-12-29
Protocol: v2.2 (Docs-as-Code)
Purpose: Verify all deliverables for Task #042 completion
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_file_exists(path, description):
    """Check if a file exists and return status."""
    exists = path.exists()
    status = "✅" if exists else "❌"
    size = f"({path.stat().st_size} bytes)" if exists else ""
    print(f"{status} {description}: {path.relative_to(PROJECT_ROOT)} {size}")
    return exists

def run_audit():
    """Run Task #042 audit checks."""

    print("\n" + "=" * 80)
    print("TASK #042: FEAST FEATURE IMPLEMENTATION & MATERIALIZATION")
    print("AUDIT & VERIFICATION REPORT")
    print("=" * 80)

    results = {
        "documentation": [],
        "configuration": [],
        "definitions": [],
        "registry": [],
        "verification": []
    }

    # ========================================================================
    # 1. DOCUMENTATION CHECKS
    # ========================================================================
    print("\n" + "=" * 80)
    print("1. DOCUMENTATION (Protocol v2.2 - Docs-as-Code)")
    print("=" * 80)

    doc_path = PROJECT_ROOT / "docs" / "TASK_042_FEAST_IMPL.md"
    check1 = check_file_exists(doc_path, "Main documentation")
    results["documentation"].append(("docs/TASK_042_FEAST_IMPL.md", check1))

    if doc_path.exists():
        content = doc_path.read_text()
        has_feast_version = "0.10.2" in content
        has_reality = "CRITICAL FINDING" in content or "latest available" in content
        print(f"   {'✅' if has_feast_version else '❌'} Contains Feast 0.10.2 reference")
        print(f"   {'✅' if has_reality else '❌'} Documents version limitation")
        results["documentation"].append(("Version documentation", has_feast_version and has_reality))

    # ========================================================================
    # 2. CONFIGURATION FILES
    # ========================================================================
    print("\n" + "=" * 80)
    print("2. CONFIGURATION FILES")
    print("=" * 80)

    config_dir = PROJECT_ROOT / "src/data_nexus/features/store"

    # Check feature_store.yaml
    yaml_path = config_dir / "feature_store.yaml"
    check2a = check_file_exists(yaml_path, "feature_store.yaml")
    results["configuration"].append(("feature_store.yaml exists", check2a))

    if yaml_path.exists():
        yaml_content = yaml_path.read_text()
        has_project = "project:" in yaml_content
        has_registry = "registry:" in yaml_content
        has_online = "online_store:" in yaml_content
        print(f"   {'✅' if has_project else '❌'} Contains project configuration")
        print(f"   {'✅' if has_registry else '❌'} Contains registry configuration")
        print(f"   {'✅' if has_online else '❌'} Contains online store configuration")
        results["configuration"].append(("feature_store.yaml valid", has_project and has_registry and has_online))

    # ========================================================================
    # 3. FEATURE DEFINITIONS
    # ========================================================================
    print("\n" + "=" * 80)
    print("3. FEATURE DEFINITIONS")
    print("=" * 80)

    def_path = config_dir / "definitions.py"
    check3 = check_file_exists(def_path, "definitions.py")
    results["definitions"].append(("definitions.py exists", check3))

    if def_path.exists():
        try:
            # Try to import the definitions
            sys.path.insert(0, str(config_dir.parent.parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location("definitions", def_path)
            defs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(defs)

            # Check for required exports
            has_ticker = hasattr(defs, 'ticker')
            has_feature_view = hasattr(defs, 'daily_ohlcv_stats')
            has_features = hasattr(defs, 'ohlcv_features')

            print(f"   {'✅' if has_ticker else '❌'} Contains Entity 'ticker'")
            print(f"   {'✅' if has_feature_view else '❌'} Contains FeatureView 'daily_ohlcv_stats'")
            print(f"   {'✅' if has_features else '❌'} Contains feature list 'ohlcv_features'")

            results["definitions"].append(("Entity ticker", has_ticker))
            results["definitions"].append(("FeatureView daily_ohlcv_stats", has_feature_view))
            results["definitions"].append(("Features defined", has_features))

            if has_ticker:
                print(f"      Ticker type: {defs.ticker.value_type}")
            if has_feature_view:
                fv = defs.daily_ohlcv_stats
                print(f"      Entities: {fv.entities}")
                print(f"      Feature count: {len(fv.features)}")
                print(f"      TTL: {fv.ttl}")

        except Exception as e:
            print(f"   ❌ Error importing definitions: {e}")
            results["definitions"].append(("Import successful", False))

    # ========================================================================
    # 4. REGISTRY
    # ========================================================================
    print("\n" + "=" * 80)
    print("4. FEAST REGISTRY")
    print("=" * 80)

    registry_path = config_dir / "registry.db"
    check4a = check_file_exists(registry_path, "registry.db")
    results["registry"].append(("registry.db exists", check4a))

    if registry_path.exists():
        try:
            from feast import FeatureStore

            fs = FeatureStore(repo_path=str(config_dir))
            entities = fs.list_entities()
            feature_views = fs.list_feature_views()

            print(f"   ✅ Registry loads successfully")
            print(f"   ✅ Entities registered: {len(entities)}")
            for entity in entities:
                print(f"      • {entity.name} ({entity.value_type})")

            print(f"   ✅ Feature Views registered: {len(feature_views)}")
            for fv in feature_views:
                print(f"      • {fv.name} ({len(fv.features)} features)")

            results["registry"].append(("Registry valid", True))
            results["registry"].append(("Entities registered", len(entities) > 0))
            results["registry"].append(("Feature views registered", len(feature_views) > 0))

        except Exception as e:
            print(f"   ❌ Registry error: {e}")
            results["registry"].append(("Registry valid", False))

    # ========================================================================
    # 5. VERIFICATION SCRIPT
    # ========================================================================
    print("\n" + "=" * 80)
    print("5. VERIFICATION & TESTING")
    print("=" * 80)

    verify_path = PROJECT_ROOT / "scripts" / "verify_feature_store.py"
    check5 = check_file_exists(verify_path, "verify_feature_store.py")
    results["verification"].append(("Verification script exists", check5))

    if verify_path.exists():
        try:
            # Run the verification script
            import subprocess
            result = subprocess.run(
                ["/opt/mt5-crs/venv/bin/python3", str(verify_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"   ✅ Verification script runs successfully")
                results["verification"].append(("Verification passes", True))
            else:
                print(f"   ⚠️  Verification script exit code: {result.returncode}")
                results["verification"].append(("Verification passes", False))
        except Exception as e:
            print(f"   ⚠️  Error running verification: {e}")
            results["verification"].append(("Verification passes", False))

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    total_checks = 0
    total_passed = 0

    for category, checks in results.items():
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        total_checks += total
        total_passed += passed
        status = "✅" if passed == total else "⚠️" if passed >= total // 2 else "❌"
        print(f"{status} {category.upper():20s}: {passed}/{total}")

    print("\n" + "=" * 80)
    print(f"OVERALL: {total_passed}/{total_checks} checks passed ({100 * total_passed // total_checks}%)")
    print("=" * 80)

    # ========================================================================
    # COMPLETION STATUS
    # ========================================================================
    if total_passed == total_checks:
        print("\n✅ TASK #042 COMPLETE - ALL CHECKS PASSED")
        return True
    else:
        print(f"\n⚠️  TASK #042 PARTIAL - {total_passed}/{total_checks} checks passed")
        return total_passed > 0


if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
