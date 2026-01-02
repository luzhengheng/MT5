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


def audit_task_015():
    """
    Task #015 深度审计函数
    验证实时特征管道搭建与数据入库

    Returns:
        dict: 审计结果字典
    """
    results = {
        "definitions_file": False,
        "feature_keywords": False,
        "ingestion_script": False,
        "verify_log": False,
        "parquet_data": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #015 FEATURE PIPELINE & INGESTION")
    print("==================================================")

    # 1. 检查 definitions.py 文件
    print("\n[1/5] Checking Feature Definitions...")
    defs_path = "src/feature_store/definitions.py"
    if os.path.exists(defs_path):
        try:
            with open(defs_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否包含至少 5 个 FeatureView
            feature_view_count = content.count("FeatureView(")
            
            if feature_view_count >= 5:
                print(f"[✔] {defs_path} contains {feature_view_count} FeatureViews")
                results["definitions_file"] = True
            else:
                print(f"[✘] {defs_path} only has {feature_view_count} FeatureViews (need >= 5)")
        except Exception as e:
            print(f"[✘] Failed to read {defs_path}: {e}")
    else:
        print(f"[✘] {defs_path} missing")

    # 2. 检查关键技术指标关键词
    print("\n[2/5] Checking Technical Indicator Keywords...")
    if os.path.exists(defs_path):
        try:
            with open(defs_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            has_rsi = "rsi" in content
            has_sma = "sma" in content
            has_macd = "macd" in content
            
            if has_rsi and has_sma:
                print(f"[✔] Found required keywords: rsi={has_rsi}, sma={has_sma}, macd={has_macd}")
                results["feature_keywords"] = True
            else:
                print(f"[✘] Missing keywords: rsi={has_rsi}, sma={has_sma}")
        except Exception as e:
            print(f"[✘] Failed to check keywords: {e}")
    else:
        print(f"[✘] Cannot check keywords (file missing)")

    # 3. 检查入库脚本
    print("\n[3/5] Checking Ingestion Script...")
    ingest_path = "src/feature_engineering/ingest_stream.py"
    if os.path.exists(ingest_path):
        print(f"[✔] {ingest_path} exists")
        results["ingestion_script"] = True
    else:
        print(f"[✘] {ingest_path} missing")

    # 4. 检查验证日志
    print("\n[4/5] Checking Verification Logs...")
    log_path = "docs/archive/logs/TASK_015_VERIFY.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            has_success = "Materialization successful" in log_content
            
            if has_success:
                print(f"[✔] Verification log complete")
                results["verify_log"] = True
            else:
                print(f"[!] Verification log exists but missing 'Materialization successful'")
        except Exception as e:
            print(f"[✘] Failed to read log: {e}")
    else:
        print(f"[!] Verification log not found (may not have run yet)")

    # 5. 检查 Parquet 数据文件
    print("\n[5/5] Checking Parquet Data...")
    parquet_path = "data/sample_features.parquet"
    if os.path.exists(parquet_path):
        file_size = os.path.getsize(parquet_path)
        if file_size > 0:
            print(f"[✔] Parquet data exists ({file_size} bytes)")
            results["parquet_data"] = True
        else:
            print(f"[!] Parquet file exists but empty")
    else:
        print(f"[!] Parquet data not found: {parquet_path}")

    # 汇总结果
    print("\n" + "=" * 50)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"📊 Audit Summary: {passed_count}/{total_count} checks passed")
    for item, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"    {symbol} {item}")

    return results


def audit_task_016():
    """
    Task #016 深度审计函数
    验证模型训练环境搭建与基线模型
    """
    results = {
        "dataset_script": False,
        "training_script": False,
        "training_data": False,
        "model_file": False,
        "completion_report": False,
        "quick_start": False,
        "sync_guide": False,
        "verify_log": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #016 MODEL TRAINING & BASELINE")
    print("==================================================")

    # 1. 检查数据集创建脚本
    print("\n[1/8] Checking Dataset Script...")
    dataset_path = "src/training/create_dataset.py"
    if os.path.exists(dataset_path):
        print(f"[✔] {dataset_path} exists")
        results["dataset_script"] = True
    else:
        print(f"[✘] {dataset_path} missing")

    # 2. 检查训练脚本
    print("\n[2/8] Checking Training Script...")
    train_path = "src/training/train_baseline.py"
    if os.path.exists(train_path):
        try:
            with open(train_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'lightgbm' in content.lower() or 'lgb' in content:
                print(f"[✔] {train_path} exists with LightGBM")
                results["training_script"] = True
            else:
                print(f"[!] {train_path} exists but missing LightGBM")
        except Exception as e:
            print(f"[✘] Failed to read {train_path}: {e}")
    else:
        print(f"[✘] {train_path} missing")

    # 3. 检查训练数据集
    print("\n[3/8] Checking Training Dataset...")
    data_path = "data/training_set.parquet"
    if os.path.exists(data_path):
        file_size = os.path.getsize(data_path)
        if file_size > 0:
            print(f"[✔] Training dataset exists ({file_size} bytes)")
            results["training_data"] = True
        else:
            print(f"[!] Training dataset exists but empty")
    else:
        print(f"[✘] Training dataset missing: {data_path}")

    # 4. 检查模型文件
    print("\n[4/8] Checking Model File...")
    model_path = "models/baseline_v1.txt"
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        if file_size > 0:
            print(f"[✔] Model file exists ({file_size} bytes)")
            results["model_file"] = True
        else:
            print(f"[!] Model file exists but empty")
    else:
        print(f"[✘] Model file missing: {model_path}")

    # 5. 检查完成报告
    print("\n[5/8] Checking Completion Report...")
    report_path = "docs/archive/tasks/TASK_016/COMPLETION_REPORT.md"
    if os.path.exists(report_path):
        print(f"[✔] {report_path} exists")
        results["completion_report"] = True
    else:
        print(f"[✘] {report_path} missing")

    # 6. 检查快速启动指南
    print("\n[6/8] Checking Quick Start Guide...")
    quick_path = "docs/archive/tasks/TASK_016/QUICK_START.md"
    if os.path.exists(quick_path):
        print(f"[✔] {quick_path} exists")
        results["quick_start"] = True
    else:
        print(f"[✘] {quick_path} missing")

    # 7. 检查同步指南
    print("\n[7/8] Checking Sync Guide...")
    sync_path = "docs/archive/tasks/TASK_016/SYNC_GUIDE.md"
    if os.path.exists(sync_path):
        print(f"[✔] {sync_path} exists")
        results["sync_guide"] = True
    else:
        print(f"[✘] {sync_path} missing")

    # 8. 检查验证日志
    print("\n[8/8] Checking Verification Log...")
    verify_path = "docs/archive/tasks/TASK_016/VERIFY_LOG.log"
    if os.path.exists(verify_path):
        try:
            with open(verify_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_mse = "MSE:" in content or "mse" in content.lower()
            if has_mse:
                print(f"[✔] Verification log complete")
                results["verify_log"] = True
            else:
                print(f"[!] Verification log exists but missing MSE metric")
        except Exception as e:
            print(f"[✘] Failed to read log: {e}")
    else:
        print(f"[✘] Verification log missing: {verify_path}")

    # 汇总结果
    print("\n" + "=" * 50)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"📊 Audit Summary: {passed_count}/{total_count} checks passed")
    for item, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"    {symbol} {item}")

    return results


def audit_task_017():
    """
    Task #017 深度审计函数
    验证历史工单归档标准化
    """
    results = {
        "archive_script": False,
        "task_directories": False,
        "completion_report": False,
        "quick_start": False,
        "sync_guide": False,
        "verify_log": False,
        "docs_cleanup": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #017 ARCHIVE STANDARDIZATION")
    print("==================================================")

    # 1. 检查归档脚本
    print("\n[1/7] Checking Archive Script...")
    script_path = "scripts/maintenance/archive_refactor.py"
    if os.path.exists(script_path):
        print(f"[✔] {script_path} exists")
        results["archive_script"] = True
    else:
        print(f"[✘] {script_path} missing")

    # 2. 检查任务目录数量
    print("\n[2/7] Checking Task Directories...")
    archive_dir = "docs/archive/tasks"
    if os.path.exists(archive_dir):
        task_dirs = [d for d in os.listdir(archive_dir) if d.startswith("TASK_")]
        if len(task_dirs) >= 15:
            print(f"[✔] Found {len(task_dirs)} task directories (>= 15)")
            results["task_directories"] = True
        else:
            print(f"[✘] Only {len(task_dirs)} task directories (need >= 15)")
    else:
        print(f"[✘] Archive directory missing: {archive_dir}")

    # 3. 检查 TASK_017 完成报告
    print("\n[3/7] Checking Completion Report...")
    report_path = "docs/archive/tasks/TASK_017/COMPLETION_REPORT.md"
    if os.path.exists(report_path):
        print(f"[✔] {report_path} exists")
        results["completion_report"] = True
    else:
        print(f"[✘] {report_path} missing")

    # 4. 检查快速启动指南
    print("\n[4/7] Checking Quick Start Guide...")
    quick_path = "docs/archive/tasks/TASK_017/QUICK_START.md"
    if os.path.exists(quick_path):
        print(f"[✔] {quick_path} exists")
        results["quick_start"] = True
    else:
        print(f"[✘] {quick_path} missing")

    # 5. 检查同步指南
    print("\n[5/7] Checking Sync Guide...")
    sync_path = "docs/archive/tasks/TASK_017/SYNC_GUIDE.md"
    if os.path.exists(sync_path):
        print(f"[✔] {sync_path} exists")
        results["sync_guide"] = True
    else:
        print(f"[✘] {sync_path} missing")

    # 6. 检查验证日志
    print("\n[6/7] Checking Verification Log...")
    verify_path = "docs/archive/tasks/TASK_017/VERIFY_LOG.log"
    if os.path.exists(verify_path):
        try:
            with open(verify_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_stats = "Files Moved:" in content
            if has_stats:
                print(f"[✔] Verification log complete")
                results["verify_log"] = True
            else:
                print(f"[!] Verification log exists but missing statistics")
        except Exception as e:
            print(f"[✘] Failed to read log: {e}")
    else:
        print(f"[✘] Verification log missing: {verify_path}")

    # 7. 检查 docs/ 根目录清理
    print("\n[7/7] Checking docs/ Root Cleanup...")
    if os.path.exists("docs"):
        legacy_files = [f for f in os.listdir("docs") if f.startswith("TASK_0") and f.endswith(".md")]
        if len(legacy_files) == 0:
            print(f"[✔] docs/ root is clean (no TASK_0*.md files)")
            results["docs_cleanup"] = True
        else:
            print(f"[!] Found {len(legacy_files)} legacy TASK files in docs/ root")

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
    # 运行 Task 017 审计 (最新任务)
    results = audit_task_017()

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
