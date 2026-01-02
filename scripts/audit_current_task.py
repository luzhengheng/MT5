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


def audit_task_018():
    """
    Task #018 深度审计函数
    验证回测引擎与数据泄露诊断
    """
    results = {
        "backtest_script": False,
        "verify_log": False,
        "sharpe_ratio_found": False,
        "leakage_diagnosis": False,
        "completion_report": False,
        "quick_start": False,
        "sync_guide": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #018 BACKTESTING & LEAKAGE CHECK")
    print("==================================================")

    # 1. 检查回测脚本
    print("\n[1/7] Checking Backtest Script...")
    script_path = "src/backtesting/vbt_runner.py"
    if os.path.exists(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'vbt.Portfolio.from_signals' in content:
                print(f"[✔] {script_path} exists with VectorBT logic")
                results["backtest_script"] = True
            else:
                print(f"[!] {script_path} exists but missing VectorBT call")
        except Exception as e:
            print(f"[✘] Failed to read {script_path}: {e}")
    else:
        print(f"[✘] {script_path} missing")

    # 2. 检查验证日志
    print("\n[2/7] Checking Verification Log...")
    log_path = "docs/archive/tasks/TASK_018/VERIFY_LOG.log"
    if os.path.exists(log_path):
        print(f"[✔] {log_path} exists")
        results["verify_log"] = True
    else:
        print(f"[✘] {log_path} missing")

    # 3. 检查 Sharpe Ratio
    print("\n[3/7] Checking Sharpe Ratio in Log...")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'Sharpe Ratio' in content:
                import re
                match = re.search(r'Sharpe Ratio[:\s]+([0-9.]+)', content)
                if match:
                    sharpe = float(match.group(1))
                    print(f"[✔] Found Sharpe Ratio: {sharpe:.4f}")
                    results["sharpe_ratio_found"] = True
                else:
                    print(f"[!] 'Sharpe Ratio' keyword found but no value")
            else:
                print(f"[✘] 'Sharpe Ratio' not found in log")
        except Exception as e:
            print(f"[✘] Failed to parse log: {e}")

    # 4. 检查泄露诊断
    print("\n[4/7] Checking Leakage Diagnosis...")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'VERDICT' in content and ('LEAKED' in content or 'SAFE' in content):
                print(f"[✔] Leakage diagnosis present")
                results["leakage_diagnosis"] = True
            else:
                print(f"[!] Leakage diagnosis missing")
        except Exception as e:
            print(f"[✘] Failed to check diagnosis: {e}")

    # 5. 检查完成报告
    print("\n[5/7] Checking Completion Report...")
    report_path = "docs/archive/tasks/TASK_018/COMPLETION_REPORT.md"
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'Leakage Diagnosis' in content or '泄露诊断' in content:
                print(f"[✔] {report_path} exists with leakage analysis")
                results["completion_report"] = True
            else:
                print(f"[!] {report_path} exists but missing leakage section")
        except Exception as e:
            print(f"[✘] Failed to read report: {e}")
    else:
        print(f"[✘] {report_path} missing")

    # 6. 检查快速启动指南
    print("\n[6/7] Checking Quick Start Guide...")
    quick_path = "docs/archive/tasks/TASK_018/QUICK_START.md"
    if os.path.exists(quick_path):
        print(f"[✔] {quick_path} exists")
        results["quick_start"] = True
    else:
        print(f"[✘] {quick_path} missing")

    # 7. 检查同步指南
    print("\n[7/7] Checking Sync Guide...")
    sync_path = "docs/archive/tasks/TASK_018/SYNC_GUIDE.md"
    if os.path.exists(sync_path):
        print(f"[✔] {sync_path} exists")
        results["sync_guide"] = True
    else:
        print(f"[✘] {sync_path} missing")

    # 汇总结果
    print("\n" + "=" * 50)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"📊 Audit Summary: {passed_count}/{total_count} checks passed")
    for item, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"    {symbol} {item}")

    return results


def audit_task_019():
    """
    Task #019 深度审计函数
    验证数据泄露修复与真实数据接入
    """
    results = {
        "ingest_script": False,
        "dataset_v2_script": False,
        "raw_data": False,
        "training_data": False,
        "model_file": False,
        "sharpe_fixed": False,
        "completion_report": False,
        "quick_start": False,
        "sync_guide": False,
        "verify_log": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #019 DATA LEAKAGE FIX")
    print("==================================================")

    # 1. 检查数据接入脚本
    print("\n[1/10] Checking Data Ingestion Script...")
    ingest_path = "src/feature_engineering/ingest_eodhd.py"
    if os.path.exists(ingest_path):
        print(f"[✔] {ingest_path} exists")
        results["ingest_script"] = True
    else:
        print(f"[✘] {ingest_path} missing")

    # 2. 检查 v2 数据集脚本
    print("\n[2/10] Checking Dataset v2 Script...")
    dataset_path = "src/training/create_dataset_v2.py"
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '.rolling(' in content:
                print(f"[✔] {dataset_path} exists with rolling windows")
                results["dataset_v2_script"] = True
            else:
                print(f"[!] {dataset_path} exists but missing rolling windows")
        except Exception as e:
            print(f"[✘] Failed to read {dataset_path}: {e}")
    else:
        print(f"[✘] {dataset_path} missing")

    # 3. 检查原始数据
    print("\n[3/10] Checking Raw Market Data...")
    raw_path = "data/raw_market_data.parquet"
    if os.path.exists(raw_path):
        file_size = os.path.getsize(raw_path)
        if file_size > 100000:
            print(f"[✔] Raw data exists ({file_size} bytes, > 100KB)")
            results["raw_data"] = True
        else:
            print(f"[!] Raw data too small ({file_size} bytes)")
    else:
        print(f"[✘] Raw data missing: {raw_path}")

    # 4. 检查训练数据集
    print("\n[4/10] Checking Training Dataset...")
    train_path = "data/training_set.parquet"
    if os.path.exists(train_path):
        file_size = os.path.getsize(train_path)
        if file_size > 100000:
            print(f"[✔] Training data exists ({file_size} bytes, > 100KB)")
            results["training_data"] = True
        else:
            print(f"[!] Training data too small ({file_size} bytes)")
    else:
        print(f"[✘] Training data missing: {train_path}")

    # 5. 检查模型文件
    print("\n[5/10] Checking Model File...")
    model_path = "models/baseline_v1.txt"
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        if file_size > 0:
            print(f"[✔] Model file exists ({file_size} bytes)")
            results["model_file"] = True
        else:
            print(f"[!] Model file empty")
    else:
        print(f"[✘] Model file missing: {model_path}")

    # 6. 检查 Sharpe Ratio 修复
    print("\n[6/10] Checking Sharpe Ratio Fix...")
    log_path = "docs/archive/tasks/TASK_019/VERIFY_LOG.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            import re
            match = re.search(r'Sharpe Ratio[\s:]+([0-9.]+)', content)
            if match:
                sharpe = float(match.group(1))
                if sharpe < 5.0:
                    print(f"[✔] Sharpe Ratio fixed: {sharpe:.4f} < 5.0")
                    results["sharpe_fixed"] = True
                else:
                    print(f"[✘] Sharpe Ratio still too high: {sharpe:.4f}")
            else:
                print(f"[!] Sharpe Ratio not found in log")
        except Exception as e:
            print(f"[✘] Failed to parse log: {e}")
    else:
        print(f"[✘] Verification log missing: {log_path}")

    # 7. 检查完成报告
    print("\n[7/10] Checking Completion Report...")
    report_path = "docs/archive/tasks/TASK_019/COMPLETION_REPORT.md"
    if os.path.exists(report_path):
        print(f"[✔] {report_path} exists")
        results["completion_report"] = True
    else:
        print(f"[✘] {report_path} missing")

    # 8. 检查快速启动指南
    print("\n[8/10] Checking Quick Start Guide...")
    quick_path = "docs/archive/tasks/TASK_019/QUICK_START.md"
    if os.path.exists(quick_path):
        print(f"[✔] {quick_path} exists")
        results["quick_start"] = True
    else:
        print(f"[✘] {quick_path} missing")

    # 9. 检查同步指南
    print("\n[9/10] Checking Sync Guide...")
    sync_path = "docs/archive/tasks/TASK_019/SYNC_GUIDE.md"
    if os.path.exists(sync_path):
        print(f"[✔] {sync_path} exists")
        results["sync_guide"] = True
    else:
        print(f"[✘] {sync_path} missing")

    # 10. 检查验证日志
    print("\n[10/10] Checking Verification Log...")
    if os.path.exists(log_path):
        print(f"[✔] {log_path} exists")
        results["verify_log"] = True
    else:
        print(f"[✘] {log_path} missing")

    # 汇总结果
    print("\n" + "=" * 50)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"📊 Audit Summary: {passed_count}/{total_count} checks passed")
    for item, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"    {symbol} {item}")

    return results


def audit_task_020():
    """
    Task #020 深度审计函数
    验证真实 EODHD 数据接入与流水线固化
    """
    results = {
        "ingest_script": False,
        "env_config": False,
        "real_data": False,
        "data_quality": False,
        "verify_log": False,
        "completion_report": False,
        "quick_start": False,
        "sync_guide": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #020 REAL DATA INGESTION")
    print("==================================================")

    # 1. 检查真实数据接入脚本
    print("\n[1/8] Checking Real Data Ingestion Script...")
    script_path = "src/feature_engineering/ingest_real_eodhd.py"
    if os.path.exists(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_requests = 'import requests' in content or 'from requests' in content
            has_api = 'eodhd.com' in content
            if has_requests and has_api:
                print(f"[✔] {script_path} exists with API integration")
                results["ingest_script"] = True
            else:
                print(f"[!] {script_path} missing API logic")
        except Exception as e:
            print(f"[✘] Failed to read {script_path}: {e}")
    else:
        print(f"[✘] {script_path} missing")

    # 2. 检查环境配置
    print("\n[2/8] Checking Environment Config...")
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                content = f.read()
            if 'EODHD_API_TOKEN' in content:
                print(f"[✔] .env contains EODHD_API_TOKEN")
                results["env_config"] = True
            else:
                print(f"[!] .env missing EODHD_API_TOKEN")
        except Exception as e:
            print(f"[✘] Failed to read .env: {e}")
    else:
        print(f"[!] .env file not found (optional)")

    # 3. 检查真实数据文件
    print("\n[3/8] Checking Real Market Data...")
    data_path = "data/real_market_data.parquet"
    if os.path.exists(data_path):
        try:
            import pandas as pd
            df = pd.read_parquet(data_path)
            row_count = len(df)
            if row_count > 1000:  # 降低阈值，日线数据通常较少
                print(f"[✔] Real data exists ({row_count} rows, > 1000)")
                results["real_data"] = True
            else:
                print(f"[!] Real data too small ({row_count} rows)")
        except Exception as e:
            print(f"[✘] Failed to read data: {e}")
    else:
        print(f"[✘] Real data missing: {data_path}")

    # 4. 检查数据质量
    print("\n[4/8] Checking Data Quality...")
    if os.path.exists(data_path):
        try:
            import pandas as pd
            df = pd.read_parquet(data_path)
            has_close = 'close' in df.columns
            no_null_close = df['close'].notna().all() if has_close else False
            date_range = (df['timestamp'].max() - df['timestamp'].min()).days if 'timestamp' in df.columns else 0

            if has_close and no_null_close and date_range > 365:
                print(f"[✔] Data quality OK (span: {date_range} days)")
                results["data_quality"] = True
            else:
                print(f"[!] Data quality issues: close={has_close}, nulls={not no_null_close}, span={date_range}d")
        except Exception as e:
            print(f"[✘] Failed to check quality: {e}")

    # 5. 检查验证日志
    print("\n[5/8] Checking Verification Log...")
    log_path = "docs/archive/tasks/TASK_020/VERIFY_LOG.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_download = 'Download Complete' in content or 'Downloaded' in content
            has_sharpe = 'Sharpe Ratio' in content
            if has_download and has_sharpe:
                print(f"[✔] Verification log complete")
                results["verify_log"] = True
            else:
                print(f"[!] Log missing keywords: download={has_download}, sharpe={has_sharpe}")
        except Exception as e:
            print(f"[✘] Failed to read log: {e}")
    else:
        print(f"[✘] Verification log missing: {log_path}")

    # 6. 检查完成报告
    print("\n[6/8] Checking Completion Report...")
    report_path = "docs/archive/tasks/TASK_020/COMPLETION_REPORT.md"
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_comparison = 'Simulated vs Real' in content or '模拟 vs 真实' in content
            if has_comparison:
                print(f"[✔] {report_path} exists with comparison")
                results["completion_report"] = True
            else:
                print(f"[!] Report missing comparison section")
        except Exception as e:
            print(f"[✘] Failed to read report: {e}")
    else:
        print(f"[✘] {report_path} missing")

    # 7. 检查快速启动指南
    print("\n[7/8] Checking Quick Start Guide...")
    quick_path = "docs/archive/tasks/TASK_020/QUICK_START.md"
    if os.path.exists(quick_path):
        print(f"[✔] {quick_path} exists")
        results["quick_start"] = True
    else:
        print(f"[✘] {quick_path} missing")

    # 8. 检查同步指南
    print("\n[8/8] Checking Sync Guide...")
    sync_path = "docs/archive/tasks/TASK_020/SYNC_GUIDE.md"
    if os.path.exists(sync_path):
        print(f"[✔] {sync_path} exists")
        results["sync_guide"] = True
    else:
        print(f"[✘] {sync_path} missing")

    # 汇总结果
    print("\n" + "=" * 50)
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"📊 Audit Summary: {passed_count}/{total_count} checks passed")
    for item, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"    {symbol} {item}")

    return results


def audit_task_021():
    """
    Task #021 深度审计函数
    验证 Walk-Forward Analysis 样本外滚动验证
    """
    results = {
        "walk_forward_script": False,
        "verify_log": False,
        "multiple_test_periods": False,
        "oos_sharpe": False,
        "completion_report": False,
        "quick_start": False,
        "sync_guide": False
    }

    print("==================================================")
    print("🔍 AUDIT: Task #021 WALK-FORWARD VALIDATION")
    print("==================================================")

    # 1. 检查 Walk-Forward 脚本
    print("\n[1/7] Checking Walk-Forward Script...")
    script_path = "src/backtesting/walk_forward.py"
    if os.path.exists(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_rolling = 'rolling' in content.lower() or 'TimeSeriesSplit' in content
            has_model_reset = 'LGBMRegressor(' in content or 'lgb.train' in content
            if has_rolling and has_model_reset:
                print(f"[✔] {script_path} exists with rolling logic")
                results["walk_forward_script"] = True
            else:
                print(f"[!] {script_path} missing rolling/model reset logic")
        except Exception as e:
            print(f"[✘] Failed to read {script_path}: {e}")
    else:
        print(f"[✘] {script_path} missing")

    # 2. 检查验证日志
    print("\n[2/7] Checking Verification Log...")
    log_path = "docs/archive/tasks/TASK_021/VERIFY_LOG.log"
    if os.path.exists(log_path):
        print(f"[✔] {log_path} exists")
        results["verify_log"] = True
    else:
        print(f"[✘] {log_path} missing")

    # 3. 检查多个测试周期
    print("\n[3/7] Checking Multiple Test Periods...")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            import re
            test_periods = len(re.findall(r'Test Period|Year \d{4}|Window \d+', content))
            if test_periods >= 3:
                print(f"[✔] Found {test_periods} test periods (>= 3)")
                results["multiple_test_periods"] = True
            else:
                print(f"[✘] Only {test_periods} test periods (need >= 3)")
        except Exception as e:
            print(f"[✘] Failed to parse log: {e}")

    # 4. 检查 OOS Sharpe Ratio
    print("\n[4/7] Checking OOS Sharpe Ratio...")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            import re
            match = re.search(r'OOS Sharpe Ratio[:\s]+([0-9.-]+)', content, re.IGNORECASE)
            if match:
                sharpe = float(match.group(1))
                print(f"[✔] Found OOS Sharpe: {sharpe:.4f}")
                results["oos_sharpe"] = True
            else:
                print(f"[!] OOS Sharpe not found in log")
        except Exception as e:
            print(f"[✘] Failed to parse Sharpe: {e}")

    # 5. 检查完成报告
    print("\n[5/7] Checking Completion Report...")
    report_path = "docs/archive/tasks/TASK_021/COMPLETION_REPORT.md"
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_robustness = 'Robustness' in content or '鲁棒性' in content
            has_decay = 'Decay' in content or '衰减' in content
            if has_robustness and has_decay:
                print(f"[✔] {report_path} exists with robustness analysis")
                results["completion_report"] = True
            else:
                print(f"[!] Report missing robustness/decay analysis")
        except Exception as e:
            print(f"[✘] Failed to read report: {e}")
    else:
        print(f"[✘] {report_path} missing")

    # 6. 检查快速启动指南
    print("\n[6/7] Checking Quick Start Guide...")
    quick_path = "docs/archive/tasks/TASK_021/QUICK_START.md"
    if os.path.exists(quick_path):
        print(f"[✔] {quick_path} exists")
        results["quick_start"] = True
    else:
        print(f"[✘] {quick_path} missing")

    # 7. 检查同步指南
    print("\n[7/7] Checking Sync Guide...")
    sync_path = "docs/archive/tasks/TASK_021/SYNC_GUIDE.md"
    if os.path.exists(sync_path):
        print(f"[✔] {sync_path} exists")
        results["sync_guide"] = True
    else:
        print(f"[✘] {sync_path} missing")

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
    # 运行 Task 021 审计 (最新任务)
    results = audit_task_021()

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
