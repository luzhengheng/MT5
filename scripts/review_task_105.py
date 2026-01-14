#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #105 专项审查脚本
针对 Live Risk Monitor 的核心文件进行审查
"""

import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_governance'))

from unified_review_gate import UnifiedReviewGate

def main():
    """审查 Task #105 的实际文件"""

    # Task #105 的核心文件
    task_105_files = [
        "config/risk_limits.yaml",
        "src/execution/risk_monitor.py",
        "scripts/verify_risk_trigger.py",
    ]

    # 过滤存在的文件
    existing_files = [f for f in task_105_files if os.path.exists(f)]

    if not existing_files:
        print("❌ 没有找到 Task #105 的文件")
        return 1

    print(f"🎯 准备审查 {len(existing_files)} 个 Task #105 文件:")
    for f in existing_files:
        print(f"  - {f}")
    print()

    # 创建审查网关
    gate = UnifiedReviewGate(enable_optimizer=False)  # 禁用优化器避免 bug

    # 执行审查
    success, report, stats = gate.execute_review(existing_files, use_optimizer=False)

    # 输出报告
    print("\n" + "=" * 80)
    print("📋 Task #105 审查报告")
    print("=" * 80)
    print(report)

    # 保存报告
    report_file = "TASK_105_AI_REVIEW_REPORT_EXTERNAL.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已保存到: {report_file}")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
