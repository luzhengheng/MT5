#!/usr/bin/env python3
"""
TASK #017 Archive Refactoring Script
将 Task #001-015 的历史资产按 Protocol v3.8 标准迁移至 docs/archive/tasks/TASK_[ID]/
"""
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# 配置
DOCS_ROOT = Path("docs")
ARCHIVE_ROOT = DOCS_ROOT / "archive" / "tasks"
TASK_RANGE = range(1, 16)  # Task 001-015

# 统计
stats = {"moved": 0, "created": 0, "missing": 0}

def create_task_dir(task_id):
    """创建任务归档目录"""
    task_dir = ARCHIVE_ROOT / f"TASK_{task_id:03d}"
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir

def find_and_move_files(task_id, task_dir):
    """查找并移动相关文件"""
    patterns = [
        f"TASK_{task_id:03d}_*.md",
        f"TASK_{task_id}_*.md",
        f"TASK_0{task_id}_*.md" if task_id < 10 else None,
    ]

    moved_files = []
    for pattern in patterns:
        if pattern:
            for file in DOCS_ROOT.rglob(pattern):
                if "archive/tasks" not in str(file):
                    dest = task_dir / file.name
                    print(f"Moved: {file} -> {dest}")
                    shutil.move(str(file), str(dest))
                    moved_files.append(file.name)
                    stats["moved"] += 1

    return moved_files

def create_placeholder_report(task_dir, task_id, moved_files):
    """为缺失文档创建占位符"""
    report_path = task_dir / "COMPLETION_REPORT.md"
    if not report_path.exists():
        content = f"""# TASK #{task_id:03d} - Completion Report

**Status**: Migrated from Legacy System
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Protocol**: v3.8 (Retroactive Archive)

## Migration Summary
此任务的原始文档已从旧系统迁移至当前归档结构。

## Migrated Assets
"""
        if moved_files:
            for f in moved_files:
                content += f"- `{f}`\n"
        else:
            content += "- ⚠️ No original files found in legacy system\n"

        content += "\n## Notes\n- Log files may have been lost during legacy migration\n- This report was auto-generated during TASK #017 archive refactoring\n"

        report_path.write_text(content, encoding="utf-8")
        print(f"Created: {report_path}")
        stats["created"] += 1

def create_missing_assets_note(task_dir):
    """创建缺失资产说明"""
    note_path = task_dir / "MISSING_ASSETS.md"
    content = """# Missing Assets Notice

部分 Quad-Artifact 文件在历史迁移中丢失：
- VERIFY_LOG.log - 原始执行日志未找到
- QUICK_START.md - 使用说明未归档
- SYNC_GUIDE.md - 部署指南未归档

**Reason**: Legacy system did not enforce Protocol v3.8 standards.
"""
    note_path.write_text(content, encoding="utf-8")
    stats["missing"] += 1

def main():
    print("=" * 60)
    print("TASK #017: Historical Archive Standardization")
    print("Protocol v3.8 - Quad-Artifact Migration")
    print("=" * 60)
    print()

    for task_id in TASK_RANGE:
        print(f"\n[Task #{task_id:03d}]")
        task_dir = create_task_dir(task_id)
        moved_files = find_and_move_files(task_id, task_dir)
        create_placeholder_report(task_dir, task_id, moved_files)

        # 检查是否有完整的 Quad-Artifact
        required = ["COMPLETION_REPORT.md", "VERIFY_LOG.log", "QUICK_START.md", "SYNC_GUIDE.md"]
        existing = [f for f in required if (task_dir / f).exists()]

        if len(existing) < 4:
            create_missing_assets_note(task_dir)
            print(f"  ⚠️  Incomplete: {len(existing)}/4 artifacts")
        else:
            print(f"  ✓ Complete: 4/4 artifacts")

    print("\n" + "=" * 60)
    print("Migration Statistics:")
    print(f"  Files Moved: {stats['moved']}")
    print(f"  Reports Created: {stats['created']}")
    print(f"  Tasks with Missing Assets: {stats['missing']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
