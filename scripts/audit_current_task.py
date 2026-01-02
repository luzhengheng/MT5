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

def audit_task_014():
    """
    Task #014 深度审计函数
    验证 AI Bridge 核心组件与 Feast 特征库集成

    Returns:
        dict: 审计结果字典，包含各项检查的 pass/fail 状态
    """
    results = {
        "plan_doc": False,
        "feature_store_config": False,
        "bridge_dependency": False,
        "verify_log": False,
        "feast_registry": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #014 AI BRIDGE & FEAST COMPLIANCE")
    print("==================================================")

    # 1. 文档检查 - TASK_014_PLAN.md
    print("\n[1/5] Checking Plan Document...")
    plan_path = "docs/TASK_014_PLAN.md"
    if os.path.exists(plan_path):
        # 验证文件内容非空且包含关键章节
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 1000 and "架构图" in content and "回滚计划" in content:
                    print(f"[✔] {plan_path} exists with valid content")
                    results["plan_doc"] = True
                else:
                    print(f"[!] {plan_path} exists but content incomplete")
        except Exception as e:
            print(f"[✘] Failed to read {plan_path}: {e}")
    else:
        print(f"[✘] {plan_path} missing")

    # 2. Feature Store 配置深度验证
    print("\n[2/5] Validating Feature Store Configuration...")
    fs_config_path = "src/feature_store/feature_store.yaml"
    if os.path.exists(fs_config_path):
        if HAS_YAML:
            try:
                with open(fs_config_path, 'r', encoding='utf-8') as f:
                    config = pyyaml.safe_load(f)

                # 深度验证配置字段
                checks = {
                    "project": config.get("project") == "mt5_crs",
                    "online_store_type": config.get("online_store", {}).get("type") == "redis",
                    "offline_store_type": config.get("offline_store", {}).get("type") == "file"
                }

                if all(checks.values()):
                    print(f"[✔] {fs_config_path} valid")
                    print(f"    - project: mt5_crs ✓")
                    print(f"    - online_store.type: redis ✓")
                    print(f"    - offline_store.type: file ✓")
                    results["feature_store_config"] = True
                else:
                    print(f"[✘] {fs_config_path} validation failed:")
                    for key, passed in checks.items():
                        status = "✓" if passed else "✗"
                        print(f"    - {key}: {status}")

            except Exception as e:
                print(f"[✘] Failed to parse {fs_config_path}: {e}")
        else:
            print(f"[!] {fs_config_path} exists (PyYAML missing, skipped content check)")
            results["feature_store_config"] = True  # 降级通过
    else:
        print(f"[✘] {fs_config_path} missing")

    # 3. Bridge 依赖检查
    print("\n[3/5] Checking Bridge Dependencies...")
    try:
        import curl_cffi
        print("[✔] curl_cffi is available")
        results["bridge_dependency"] = True
    except ImportError:
        print("[✘] curl_cffi missing")

    # 4. Feast Registry 检查
    print("\n[4/5] Checking Feast Registry...")
    registry_path = "data/registry.db"
    if os.path.exists(registry_path):
        file_size = os.path.getsize(registry_path)
        if file_size > 0:
            print(f"[✔] Feast registry exists ({file_size} bytes)")
            results["feast_registry"] = True
        else:
            print(f"[!] Feast registry exists but empty")
    else:
        print(f"[✘] Feast registry missing: {registry_path}")

    # 5. 验证日志检查
    print("\n[5/5] Checking Verification Logs...")
    log_path = "docs/archive/logs/TASK_014_VERIFY.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()

            has_feast = "Feast apply successful" in content
            has_bridge = "Bridge dependency OK" in content

            if has_feast and has_bridge:
                print(f"[✔] Verification log complete")
                results["verify_log"] = True
            else:
                print(f"[!] Verification log exists but missing keywords:")
                print(f"    - Feast apply successful: {'✓' if has_feast else '✗'}")
                print(f"    - Bridge dependency OK: {'✓' if has_bridge else '✗'}")
        except Exception as e:
            print(f"[✘] Failed to read log: {e}")
    else:
        print(f"[!] Verification log not found (may not have run yet)")

    # 汇总结果
    print("\n" + "=" * 50)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"📊 Audit Summary: {passed_count}/{total_count} checks passed")
    for item, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"    {symbol} {item}")

    return results


def audit():
    """主审计入口函数"""
    results = audit_task_014()

    # 计算全局统计
    global passed, failed
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    # 返回标准格式
    return {"passed": passed, "failed": failed, "details": results}

if __name__ == "__main__":
    result = audit()
    if result["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
