#!/usr/bin/env python3
"""
Quarantine Corrupted Files Script
根据 Task #110 审计报告，将损坏或不完整的文件隔离到 data/quarantine
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# 根据审计报告中的错误列表，这些文件需要被隔离
CORRUPTED_FILES = [
    "data/processed/eurusd_m1_features_labels.parquet",
    "data/processed/forex_training_set_v1.parquet",
    "data/chroma/chroma-collections.parquet",
    "data/chroma/chroma-embeddings.parquet",
    "data/eurusd_m1_features_labels.parquet",
    "data/raw/m1_fetch_manifest.json",
    "data/fused_AAPL.parquet",
    "data/meta/trial_registry.json",
    "data/sample_features.parquet",
    "data_lake/samples/user_profile_mock.json",
    "data_lake/samples/fundamental_sample.json",
    "data_lake/samples/user_profile.json",
    "_archive_20251222/logs/iteration3_feature_quality_report.csv",
    "_archive_20251222/logs/iteration2_feature_quality_report.csv",
]

def quarantine_file(file_path):
    """隔离一个文件"""
    full_path = Path(file_path)

    if not full_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False

    try:
        # 保持原始目录结构
        relative_path = full_path.relative_to(full_path.parts[0])  # 移除可能的 root 前缀
        quarantine_path = Path("data/quarantine") / relative_path

        # 创建必要的目录
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)

        # 移动文件
        shutil.move(str(full_path), str(quarantine_path))
        print(f"✅ Quarantined: {file_path} -> {quarantine_path}")
        return True
    except Exception as e:
        print(f"❌ Error quarantining {file_path}: {e}")
        return False

def main():
    print(f"[{datetime.now().isoformat()}] Starting quarantine process...")
    print(f"Total files to quarantine: {len(CORRUPTED_FILES)}")

    success_count = 0
    failed_count = 0
    not_found_count = 0

    for file_path in CORRUPTED_FILES:
        if not Path(file_path).exists():
            print(f"⚠️  Not found: {file_path}")
            not_found_count += 1
        else:
            if quarantine_file(file_path):
                success_count += 1
            else:
                failed_count += 1

    # 生成隔离报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_targeted": len(CORRUPTED_FILES),
        "successfully_quarantined": success_count,
        "failed": failed_count,
        "not_found": not_found_count,
        "quarantine_location": "data/quarantine/",
        "source_task": "Task #110 Data Audit"
    }

    print(f"\n{'='*60}")
    print(f"Quarantine Summary:")
    print(f"  Successfully quarantined: {success_count}/{len(CORRUPTED_FILES)}")
    print(f"  Failed: {failed_count}")
    print(f"  Not found: {not_found_count}")
    print(f"{'='*60}\n")

    # 保存报告
    with open("QUARANTINE_REPORT.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Quarantine report saved to: QUARANTINE_REPORT.json")

if __name__ == "__main__":
    main()
