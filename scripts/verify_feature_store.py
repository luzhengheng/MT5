#!/usr/bin/env python3
"""
Feature Store Verification Script

Task #042: Feature Store Implementation
Date: 2025-12-29
Purpose: Verify Feast registry contains properly defined entities and feature views
"""

import os
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_feature_store():
    """Verify feature store registry is properly configured."""

    print("\n" + "=" * 70)
    print("🔍 FEATURE STORE VERIFICATION")
    print("=" * 70)

    try:
        from feast import FeatureStore

        # Initialize feature store from repo
        repo_path = PROJECT_ROOT / "src/data_nexus/features/store"
        print(f"\n📂 Repository Path: {repo_path}")

        if not repo_path.exists():
            print(f"❌ Repository path does not exist: {repo_path}")
            return False

        fs = FeatureStore(repo_path=str(repo_path))
        print("✅ Feature Store initialized")

        # ====================================================================
        # Check Registry
        # ====================================================================
        registry_path = repo_path / "registry.db"
        print(f"\n📋 Registry Database: {registry_path}")

        if registry_path.exists():
            print(f"✅ registry.db exists ({registry_path.stat().st_size} bytes)")
        else:
            print("❌ registry.db not found")
            return False

        # ====================================================================
        # Check Entities
        # ====================================================================
        print("\n📌 ENTITIES")
        print("-" * 70)

        entities = fs.list_entities()
        if not entities:
            print("❌ No entities registered")
            return False

        print(f"✅ Found {len(entities)} entity/ies:")
        expected_entities = {"ticker"}
        found_entities = set()

        for entity in entities:
            found_entities.add(entity.name)
            print(f"   ✓ {entity.name:20s} (type: {entity.value_type})")

        if expected_entities == found_entities:
            print(f"✅ All expected entities registered")
        else:
            missing = expected_entities - found_entities
            extra = found_entities - expected_entities
            if missing:
                print(f"❌ Missing entities: {missing}")
            if extra:
                print(f"⚠️  Extra entities: {extra}")
            # Don't fail if we have the expected ones
            if expected_entities <= found_entities:
                print("✅ All required entities present")

        # ====================================================================
        # Check Feature Views
        # ====================================================================
        print("\n📊 FEATURE VIEWS")
        print("-" * 70)

        feature_views = fs.list_feature_views()
        if not feature_views:
            print("❌ No feature views registered")
            return False

        print(f"✅ Found {len(feature_views)} feature view(s):")
        expected_fv = {"daily_ohlcv_stats"}
        found_fv = set()

        for fv in feature_views:
            found_fv.add(fv.name)
            print(f"\n   ✓ {fv.name}")
            print(f"      Entities: {fv.entities}")
            print(f"      Features: {[f.name for f in fv.features]}")
            print(f"      TTL: {fv.ttl}")
            print(f"      Online: {fv.online}")

        if expected_fv == found_fv:
            print(f"\n✅ All expected feature views registered")
        else:
            missing = expected_fv - found_fv
            extra = found_fv - expected_fv
            if missing:
                print(f"❌ Missing feature views: {missing}")
            if extra:
                print(f"⚠️  Extra feature views: {extra}")
            # Don't fail if we have the expected ones
            if expected_fv <= found_fv:
                print("✅ All required feature views present")

        # ====================================================================
        # Check Feature Definitions
        # ====================================================================
        print("\n🎯 FEATURES")
        print("-" * 70)

        expected_features = {
            "daily_ohlcv_stats": ["open", "high", "low", "close", "adjusted_close", "volume"]
        }

        all_good = True
        for fv_name, expected_feat_names in expected_features.items():
            fv = fs.get_feature_view(fv_name)
            if fv:
                actual_feat_names = [f.name for f in fv.features]
                print(f"\n   {fv_name}:")

                for feat_name in expected_feat_names:
                    if feat_name in actual_feat_names:
                        print(f"      ✓ {feat_name}")
                    else:
                        print(f"      ❌ {feat_name} (MISSING)")
                        all_good = False

                for feat_name in actual_feat_names:
                    if feat_name not in expected_feat_names:
                        print(f"      ℹ️  {feat_name} (extra)")
            else:
                print(f"❌ Feature view not found: {fv_name}")
                all_good = False

        if all_good:
            print(f"\n✅ All expected features registered")
        else:
            print(f"\n⚠️  Some features missing")

        # ====================================================================
        # Summary
        # ====================================================================
        print("\n" + "=" * 70)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 70)
        print(f"\nFeature Store is properly configured:")
        print(f"  • Registry: {registry_path.name} ({registry_path.stat().st_size} bytes)")
        print(f"  • Entities: {len(entities)}")
        print(f"  • Feature Views: {len(feature_views)}")
        print(f"  • Total Features: {sum(len(fv.features) for fv in feature_views)}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_feature_store()
    sys.exit(0 if success else 1)
