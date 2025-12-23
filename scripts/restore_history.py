#!/usr/bin/env python3
"""
MT5-CRS Project History Restoration Script
Purpose: Populate Notion database with complete project history (#001-#013)
Created: 2025-12-23
Author: Claude Sonnet 4.5 (Lead Architect)
"""

import subprocess
import sys
from pathlib import Path

# Project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CREATE_SCRIPT = SCRIPT_DIR / "quick_create_issue.py"

# Historical tasks with proper categorization
TASKS = [
    # Phase 1: Infrastructure Foundation
    ("#001 阿里云 CentOS 环境初始化 (Python 3.9 + Git + 基础依赖)", "Infra", "P0"),
    ("#006 驱动管理器与 MT5 终端服务部署 (Wine + Xvfb + VNC)", "Infra", "P0"),
    ("#011 Notion API 集成与 DevOps 工具链建设 (多阶段任务)", "Infra", "P1"),

    # Phase 2: Data Pipeline
    ("#002 MT5 数据采集模块原型 (历史数据 + 实时行情)", "Core", "P0"),
    ("#003 TimescaleDB 架构设计与部署 (时序数据库)", "Infra", "P0"),
    ("#007 数据质量监控系统 (DQ Score + Prometheus + Grafana)", "Feature", "P1"),
    ("#008 知识库与文档架构建设 (完整特征工程文档)", "Feature", "P2"),

    # Phase 3: Strategy & Analysis
    ("#004 基础特征工程 (35维技术指标 + TA-Lib 集成)", "Core", "P0"),
    ("#005 高级特征工程 (40维分数差分 + 三重障碍标签法)", "Core", "P1"),
    ("#009 机器学习训练管线 (XGBoost + LightGBM + Optuna 调优)", "Core", "P1"),
    ("#010 回测系统建设 (Backtrader + 风险管理 + 完整报告)", "Core", "P1"),

    # Phase 4: Architecture & Gateway (Current)
    ("#012 MT5 交易网关研究 (ZeroMQ 跨平台通信方案)", "Core", "P0"),
    ("#013 Notion 工作区重构 (中文标准化 + Schema 对齐)", "Infra", "P1"),
]


def print_header():
    """Print the script header"""
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║       MT5-CRS 项目历史恢复工具 (Tasks #001-#013)                          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()


def print_statistics():
    """Print completion statistics"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ History Restoration Complete!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("📊 Statistics:")
    print(f"   - Total Tasks Created: {len(TASKS)}")
    print("   - Phase 1 (Infrastructure): 3 tasks")
    print("   - Phase 2 (Data Pipeline): 4 tasks")
    print("   - Phase 3 (Strategy & Analysis): 4 tasks")
    print("   - Phase 4 (Architecture & Gateway): 2 tasks")
    print()
    print("🔗 Next Steps:")
    print("   1. Verify all tasks in Notion Database")
    print("   2. Add detailed descriptions and documentation links")
    print("   3. Begin Task #014 (new development phase)")
    print()
    print("🎯 Knowledge Base Established - Ready for Next Phase!")


def create_task(idx: int, title: str, task_type: str, priority: str) -> bool:
    """
    Create a single task using quick_create_issue.py

    Args:
        idx: Task index (1-based)
        title: Task title
        task_type: Task type (Core, Infra, Feature, Bug)
        priority: Priority (P0, P1, P2, P3)

    Returns:
        True if successful, False otherwise
    """
    # Display shortened title for readability
    short_title = title[:50] + "..." if len(title) > 50 else title
    print(f"[{idx}/{len(TASKS)}] Creating {short_title}")

    # Build command
    cmd = [
        "python3", str(CREATE_SCRIPT),
        title,
        "--type", task_type,
        "--prio", priority,
        "--status", "DONE"
    ]

    # Execute
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        # Extract and display success message
        for line in result.stdout.split('\n'):
            if 'SUCCESS' in line:
                print(f"  ✅ {line.strip()}")
            elif 'URL' in line:
                print(f"  🔗 {line.strip()}")

        print()
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ Error: Command timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def main():
    """Main execution function"""
    # Check if create script exists
    if not CREATE_SCRIPT.exists():
        print(f"❌ Error: quick_create_issue.py not found at {CREATE_SCRIPT}")
        sys.exit(1)

    # Print header
    print_header()

    # Create all tasks
    success_count = 0
    for idx, (title, task_type, priority) in enumerate(TASKS, 1):
        if create_task(idx, title, task_type, priority):
            success_count += 1
        else:
            print(f"\n⚠️  Warning: Failed to create task {idx}/{len(TASKS)}")
            user_input = input("Continue with remaining tasks? (y/n): ")
            if user_input.lower() != 'y':
                print("\n❌ Restoration aborted by user")
                sys.exit(1)

    # Print statistics
    print_statistics()

    # Exit with appropriate status
    if success_count == len(TASKS):
        print(f"\n✅ All {len(TASKS)} tasks created successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {success_count}/{len(TASKS)} tasks created successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()
