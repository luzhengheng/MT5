#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台路径工具 - 动态、健壮的项目根目录获取

提供一致的路径管理，支持多种部署环境：
- Linux: /opt/mt5-crs, /home/user/projects/mt5-crs 等
- Windows: C:\\projects\\mt5-crs 等
- macOS: ~/projects/mt5-crs 等

核心原理：
1. 优先检查环境变量 PROJECT_ROOT
2. 向上查找 .git 目录（git 仓库根）
3. 备选：当前工作目录
"""

import os
from pathlib import Path


def get_project_root() -> Path:
    """
    动态获取项目根目录，支持多种环境和部署路径

    优先级：
    1. 环境变量 PROJECT_ROOT（最高优先级，用于 CI/CD 环境）
    2. 基于脚本位置的相对路径查找 .git 目录
    3. 当前工作目录（备选方案）

    Returns:
        Path: 项目根目录的绝对路径

    Examples:
        >>> root = get_project_root()
        >>> config_file = root / "config" / "settings.yaml"
        >>> data_dir = root / "data"
    """
    # 方案 1: 检查环境变量 PROJECT_ROOT
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        root_path = Path(env_root).resolve()
        if root_path.exists():
            return root_path

    # 方案 2: 向上查找 .git 目录（最可靠的方式）
    # 从当前脚本位置开始向上查找
    current = Path(__file__).resolve().parent

    # 最多向上查找 5 级目录
    # 假设脚本在 src/utils/ 目录，需要向上查找 2 级才能到达项目根
    for _ in range(5):
        if (current / ".git").exists():
            return current
        current = current.parent

    # 方案 3: 检查当前工作目录
    cwd = Path.cwd()
    if (cwd / ".git").exists():
        return cwd

    # 如果仍未找到 .git，返回当前目录但发出警告
    # 这允许脚本在非 git 环境中继续运行（例如容器化环境）
    return cwd


def get_config_dir() -> Path:
    """获取配置文件目录

    Returns:
        Path: <project_root>/config
    """
    return get_project_root() / "config"


def get_scripts_dir() -> Path:
    """获取脚本目录

    Returns:
        Path: <project_root>/scripts
    """
    return get_project_root() / "scripts"


def get_src_dir() -> Path:
    """获取源代码目录

    Returns:
        Path: <project_root>/src
    """
    return get_project_root() / "src"


def get_docs_dir() -> Path:
    """获取文档目录

    Returns:
        Path: <project_root>/docs
    """
    return get_project_root() / "docs"


def get_bin_dir() -> Path:
    """获取可执行文件目录

    Returns:
        Path: <project_root>/bin
    """
    return get_project_root() / "bin"


def get_tests_dir() -> Path:
    """获取测试目录

    Returns:
        Path: <project_root>/tests
    """
    return get_project_root() / "tests"


def ensure_dir_exists(path: Path) -> Path:
    """创建目录（如果不存在）

    Args:
        path: 要创建的目录路径

    Returns:
        Path: 已存在或新创建的目录路径
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


# 测试用例
if __name__ == "__main__":
    print("🔍 项目路径工具测试")
    print(f"✅ 项目根目录: {get_project_root()}")
    print(f"✅ 配置目录: {get_config_dir()}")
    print(f"✅ 脚本目录: {get_scripts_dir()}")
    print(f"✅ 源代码目录: {get_src_dir()}")
    print(f"✅ 文档目录: {get_docs_dir()}")
    print(f"✅ 可执行文件目录: {get_bin_dir()}")
    print(f"✅ 测试目录: {get_tests_dir()}")
