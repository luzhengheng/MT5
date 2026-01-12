#!/usr/bin/env python3
"""
路径配置中心 - Single Source of Truth (SSOT)

Purpose:
  消除项目中的硬编码路径，通过 pathlib 动态计算绝对路径，
  确保文件移动后 CI/CD 流程仍能稳健运行。

Design:
  - PROJECT_ROOT: 项目根目录锚点
  - GOVERNANCE_TOOLS: 治理工具注册表
  - resolve_tool(): 路径解析函数，失败时抛出异常 (Fail-Closed)

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-12
"""

from pathlib import Path
from typing import Dict


# ============================================================================
# 项目根目录锚点定义
# ============================================================================
# 本文件位于 src/config/paths.py
# 相对路径: ../../ (回到项目根)

_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent

# 验证锚点
if not (PROJECT_ROOT / ".git").exists():
    raise RuntimeError(
        f"❌ Project root detection failed: {PROJECT_ROOT}\n"
        f"   Expected to find .git directory at project root."
    )


# ============================================================================
# 核心目录定义
# ============================================================================

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
AI_GOVERNANCE_DIR = SCRIPTS_DIR / "ai_governance"
SRC_DIR = PROJECT_ROOT / "src"
CONFIG_DIR = SRC_DIR / "config"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
DOCS_DIR = PROJECT_ROOT / "docs"
ARCHIVE_DIR = DOCS_DIR / "archive" / "tasks"


# ============================================================================
# 治理工具注册表
# ============================================================================
# 所有 AI 审查和自动化工具的唯一来源

GOVERNANCE_TOOLS: Dict[str, Path] = {
    "AI_BRIDGE": AI_GOVERNANCE_DIR / "gemini_review_bridge.py",
    "NEXUS": AI_GOVERNANCE_DIR / "nexus_with_proxy.py",
}


# ============================================================================
# 路径解析函数 (Fail-Closed)
# ============================================================================

def resolve_tool(name: str) -> Path:
    """
    解析治理工具路径。

    Args:
        name: 工具名称 (e.g., "AI_BRIDGE", "NEXUS")

    Returns:
        Path: 工具的绝对路径

    Raises:
        FileNotFoundError: 如果工具不存在或配置缺失

    Examples:
        >>> path = resolve_tool("AI_BRIDGE")
        >>> print(path)
        /opt/mt5-crs/scripts/ai_governance/gemini_review_bridge.py
    """
    if name not in GOVERNANCE_TOOLS:
        available = ", ".join(GOVERNANCE_TOOLS.keys())
        raise KeyError(
            f"❌ Unknown tool: {name}\n"
            f"   Available tools: {available}"
        )

    path = GOVERNANCE_TOOLS[name]

    if not path.exists():
        raise FileNotFoundError(
            f"🚨 Critical Infrastructure Missing: {name}\n"
            f"   Expected path: {path}\n"
            f"   This file is required for AI audit pipeline."
        )

    return path


def get_project_root() -> Path:
    """Get project root directory."""
    return PROJECT_ROOT


def get_ai_governance_dir() -> Path:
    """Get AI governance scripts directory."""
    return AI_GOVERNANCE_DIR


def verify_infrastructure() -> bool:
    """
    验证基础设施完整性。

    Returns:
        True if all critical tools are present

    Raises:
        FileNotFoundError: 如果任何关键工具缺失
    """
    print("🔍 Verifying infrastructure...")
    print(f"   Project root: {PROJECT_ROOT}")
    print(f"   AI governance dir: {AI_GOVERNANCE_DIR}")

    for name in GOVERNANCE_TOOLS.keys():
        try:
            path = resolve_tool(name)
            print(f"   ✅ {name}: {path}")
        except FileNotFoundError as e:
            print(f"   ❌ {name}: {e}")
            raise

    print("✅ Infrastructure verification passed")
    return True


# ============================================================================
# 初始化检查
# ============================================================================

if __name__ == "__main__":
    # 当直接运行此模块时执行验证
    verify_infrastructure()
