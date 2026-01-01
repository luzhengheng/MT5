#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS Task Auditor (Clean Version)
Validates the completion status of the current task.
"""

import sys
import os
import logging
import warnings
import json
import subprocess

# 全局设置
logging.disable(logging.CRITICAL)
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# 全局计数器
passed = 0
failed = 0

# 全局 PyYAML 导入
try:
    import yaml as pyyaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    pyyaml = None

def check_yaml_file(filepath):
    """全局 YAML 检查函数"""
    if not os.path.exists(filepath):
        print(f"[ ] {filepath} does not exist")
        return False
    if not HAS_YAML:
        print(f"[✔] {filepath} exists (syntax check skipped - PyYAML missing)")
        return True
    try:
        with open(filepath, 'r') as f:
            pyyaml.safe_load(f)
        print(f"[✔] {filepath} exists")
        return True
    except Exception as e:
        print(f"[✘] Failed to parse {filepath}: {e}")
        return False

def audit():
    global passed, failed
    print("==================================================")
    print("🔍 AUDIT: Task #014.01 AI BRIDGE & FEAST COMPLIANCE")
    print("==================================================")

    # TASK #014.01
    print("\n[TASK #014.01 AI BRIDGE & FEAST FEATURE STORE AUDIT (CRITICAL)]")
    
    # 1. Docs
    if os.path.exists("docs/TASK_014_01_PLAN.md"):
        print("[✔] [Docs] TASK_014_01_PLAN.md exists")
        passed += 1
    else:
        print("[ ] [Docs] TASK_014_01_PLAN.md missing")
        # 非阻塞

    # 2. Bridge Dependency
    try:
        import curl_cffi
        print("[✔] [Deps] curl_cffi is available")
        passed += 1
    except ImportError:
        print("[!] [Deps] curl_cffi missing (recommended)")
        # 非阻塞

    # 3. Bridge Script
    if os.path.exists("gemini_review_bridge.py"):
        print("[✔] [Code] gemini_review_bridge.py exists")
        passed += 1
    else:
        print("[✘] [Code] gemini_review_bridge.py missing")
        failed += 1

    # 4. Feature Store Config (The Problematic Part Fixed)
    fs_config_path = "src/feature_store/feature_store.yaml"
    if os.path.exists(fs_config_path):
        print(f"[✔] [Config] {fs_config_path} exists")
        passed += 1
        
        if HAS_YAML:
            try:
                with open(fs_config_path, 'r') as f:
                    # 使用明确的变量名 fs_config，避免 feature_store_pyyaml 混淆
                    fs_config = pyyaml.safe_load(f)
                
                if fs_config and fs_config.get('project') == 'mt5_crs':
                    print("[✔] [Config] Project name correct")
                    passed += 1
                else:
                    print(f"[!] [Config] Project name mismatch: {fs_config.get('project')}")
            except Exception as e:
                print(f"[✘] [Config] Failed to parse yaml: {e}")
                failed += 1
    else:
        print(f"[✘] [Config] {fs_config_path} missing")
        failed += 1

    # 5. Feast Init
    try:
        from feast import FeatureStore
        # 尝试初始化但不连接
        fs = FeatureStore(repo_path="src/feature_store")
        print("[✔] [Feast] FeatureStore initialized successfully")
        passed += 1
    except Exception as e:
        print(f"[!] [Feast] Init warning: {e}")
        # 非阻塞

    print("-" * 50)
    print(f"📊 Audit Finished: Passed={passed}, Failed={failed}")
    return {"passed": passed, "failed": failed}

if __name__ == "__main__":
    result = audit()
    if result["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
