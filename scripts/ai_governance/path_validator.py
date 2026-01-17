#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path Traversal Prevention Module (P0 Issue #2)
===============================================

安全路径验证器，防止 sys.path 中的路径遍历攻击和模块劫持。

功能:
1. 验证项目根目录有效性
2. 检测符号链接（安全风险）
3. 验证必需文件存在
4. 防止路径外逃逸 (Path traversal)
5. 安全的 sys.path 管理

Protocol: v4.3 (Zero-Trust Edition)
CWE-22: Improper Limitation of a Pathname to a Restricted Directory
Author: MT5-CRS Agent
Date: 2026-01-16
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Set
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# 项目安全配置
REQUIRED_PROJECT_FILES = [
    'pyproject.toml',  # 项目配置
    'src/',            # 源代码目录
    'scripts/',        # 脚本目录
    'tests/',          # 测试目录
]

FORBIDDEN_PATTERNS = [
    '..',              # 路径逃逸
    '~',               # 用户主目录
    '/etc',            # 系统目录
    '/sys',            # 系统目录
    '/proc',           # 系统目录
]

MAX_PATH_DEPTH = 10  # 防止超深路径


class PathValidationError(Exception):
    """路径验证失败异常"""
    pass


class PathValidator:
    """
    安全路径验证器

    用途:
    1. 验证项目根目录安全性
    2. 防止 sys.path 中的安全问题
    3. 检测恶意或危险的路径配置
    """

    def __init__(self, strict_mode: bool = True):
        """
        初始化路径验证器

        参数:
            strict_mode: 是否启用严格模式（推荐生产环境）
        """
        self.strict_mode = strict_mode
        self.validated_paths: Set[Path] = set()
        self.validation_log = []

    def log_validation(self, message: str, level: str = "INFO"):
        """记录验证操作"""
        self.validation_log.append(message)
        if level == "INFO":
            logger.info(f"{CYAN}{message}{RESET}")
        elif level == "WARNING":
            logger.warning(f"{YELLOW}{message}{RESET}")
        elif level == "ERROR":
            logger.error(f"{RED}{message}{RESET}")
        elif level == "SUCCESS":
            logger.info(f"{GREEN}{message}{RESET}")

    def validate_path_format(self, path: Path) -> bool:
        """
        验证路径格式是否安全

        检查:
        - 无路径遍历模式 (..)
        - 无禁止的模式 (~, /etc, /sys, /proc)
        - 路径深度不超过限制

        参数:
            path: 要验证的路径

        返回:
            True 如果路径安全，否则抛出异常
        """
        path_str = str(path.resolve())

        # 检查禁止的模式
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in path_str:
                raise PathValidationError(
                    f"❌ 路径包含禁止模式 '{pattern}': {path_str}"
                )

        # 检查路径深度
        depth = len(Path(path_str).parts)
        if depth > MAX_PATH_DEPTH:
            raise PathValidationError(
                f"❌ 路径深度过深 ({depth} > {MAX_PATH_DEPTH}): {path_str}"
            )

        self.log_validation(f"✓ 路径格式安全: {path_str[:60]}...")
        return True

    def validate_existence(self, path: Path) -> bool:
        """
        验证路径存在

        参数:
            path: 要验证的路径

        返回:
            True 如果路径存在，否则抛出异常
        """
        if not path.exists():
            raise PathValidationError(
                f"❌ 路径不存在: {path}"
            )

        self.log_validation(f"✓ 路径存在: {path}")
        return True

    def validate_type(self, path: Path, expected_type: str = "dir") -> bool:
        """
        验证路径类型（目录或文件）

        参数:
            path: 要验证的路径
            expected_type: 期望的类型 ("dir" 或 "file")

        返回:
            True 如果类型匹配，否则抛出异常
        """
        is_dir = path.is_dir()
        is_file = path.is_file()

        if expected_type == "dir" and not is_dir:
            raise PathValidationError(
                f"❌ 路径不是目录: {path} (is_dir={is_dir})"
            )

        if expected_type == "file" and not is_file:
            raise PathValidationError(
                f"❌ 路径不是文件: {path} (is_file={is_file})"
            )

        self.log_validation(f"✓ 路径类型正确 ({expected_type}): {path}")
        return True

    def validate_no_symlinks(self, path: Path) -> bool:
        """
        检测符号链接（安全风险）

        符号链接可能被攻击者利用来：
        - 绕过目录限制
        - 指向系统敏感目录
        - 进行目录遍历攻击

        参数:
            path: 要验证的路径

        返回:
            True 如果不是符号链接，否则抛出异常
        """
        if path.is_symlink():
            resolved = path.resolve()
            raise PathValidationError(
                f"❌ 路径是符号链接（安全风险）: {path} -> {resolved}"
            )

        self.log_validation(f"✓ 不是符号链接: {path}")
        return True

    def validate_required_files(self, root_path: Path, required_files: Optional[List[str]] = None) -> bool:
        """
        验证必需文件/目录存在（用于验证项目结构）

        参数:
            root_path: 项目根目录
            required_files: 必需的文件/目录列表

        返回:
            True 如果所有必需文件存在，否则抛出异常
        """
        required_files = required_files or REQUIRED_PROJECT_FILES

        missing_files = []
        for req_file in required_files:
            file_path = root_path / req_file
            if not file_path.exists():
                missing_files.append(req_file)
                self.log_validation(f"✗ 必需文件缺失: {req_file}", level="WARNING")
            else:
                self.log_validation(f"✓ 必需文件存在: {req_file}", level="SUCCESS")

        if missing_files:
            if self.strict_mode:
                raise PathValidationError(
                    f"❌ 缺少必需文件: {', '.join(missing_files)}"
                )
            else:
                logger.warning(f"⚠️  缺少必需文件（非严格模式，继续）: {missing_files}")

        return True

    def validate_permissions(self, path: Path, mode: str = "r") -> bool:
        """
        验证目录/文件权限

        参数:
            path: 要验证的路径
            mode: 权限模式 ("r" 读, "w" 写, "x" 执行)

        返回:
            True 如果有相应权限，否则抛出异常
        """
        if mode == "r" and not os.access(path, os.R_OK):
            raise PathValidationError(f"❌ 无读取权限: {path}")

        if mode == "w" and not os.access(path, os.W_OK):
            raise PathValidationError(f"❌ 无写入权限: {path}")

        if mode == "x" and not os.access(path, os.X_OK):
            raise PathValidationError(f"❌ 无执行权限: {path}")

        self.log_validation(f"✓ 权限验证通过 ({mode}): {path}")
        return True

    def validate_project_root(self, root_path: Path) -> bool:
        """
        综合验证项目根目录

        执行所有安全检查:
        1. 路径格式验证
        2. 存在性检查
        3. 类型检查 (必须是目录)
        4. 符号链接检查
        5. 必需文件检查
        6. 权限检查

        参数:
            root_path: 项目根目录路径

        返回:
            True 如果所有检查通过，否则抛出异常
        """
        self.log_validation("=" * 60)
        self.log_validation("🔒 开始项目根目录安全验证...", level="INFO")
        self.log_validation("=" * 60)

        try:
            # 1. 路径格式验证
            self.log_validation("[1/6] 验证路径格式...")
            self.validate_path_format(root_path)

            # 2. 存在性检查
            self.log_validation("[2/6] 检查路径存在...")
            self.validate_existence(root_path)

            # 3. 类型检查
            self.log_validation("[3/6] 检查路径类型...")
            self.validate_type(root_path, expected_type="dir")

            # 4. 符号链接检查
            self.log_validation("[4/6] 检查符号链接...")
            self.validate_no_symlinks(root_path)

            # 5. 必需文件检查
            self.log_validation("[5/6] 验证项目结构...")
            self.validate_required_files(root_path)

            # 6. 权限检查
            self.log_validation("[6/6] 验证读取权限...")
            self.validate_permissions(root_path, mode="r")

            self.log_validation("=" * 60)
            self.log_validation("✅ 项目根目录验证通过 - 安全", level="SUCCESS")
            self.log_validation("=" * 60)

            # 记录为已验证
            self.validated_paths.add(root_path.resolve())

            return True

        except PathValidationError as e:
            self.log_validation(f"❌ 验证失败: {e}", level="ERROR")
            if self.strict_mode:
                raise
            return False

    def safe_add_to_syspath(self, path: Path) -> bool:
        """
        安全地将路径添加到 sys.path

        参数:
            path: 要添加的路径

        返回:
            True 如果成功添加，False 如果验证失败
        """
        try:
            # 验证路径安全性
            self.log_validation(f"🔒 验证 sys.path 条目: {path}")
            self.validate_project_root(path)

            path_str = str(path.resolve())

            # 检查是否已在 sys.path 中
            if path_str in sys.path:
                self.log_validation(f"⚠️  路径已在 sys.path 中: {path_str}")
                return True

            # 在最前面插入（优先级最高）
            sys.path.insert(0, path_str)
            self.log_validation(f"✅ 安全添加到 sys.path: {path_str}", level="SUCCESS")

            return True

        except PathValidationError as e:
            self.log_validation(f"❌ 添加失败: {e}", level="ERROR")
            return False

    def get_validation_report(self) -> str:
        """
        获取完整的验证报告

        返回:
            格式化的验证报告字符串
        """
        report = [
            "\n" + "=" * 60,
            "🔍 路径验证报告",
            "=" * 60,
            f"严格模式: {'启用' if self.strict_mode else '禁用'}",
            f"已验证路径数: {len(self.validated_paths)}",
            f"验证日志条目: {len(self.validation_log)}",
            "-" * 60,
            "验证日志:",
            "-" * 60,
        ]

        for i, log_entry in enumerate(self.validation_log[-20:], 1):  # 显示最后20条
            report.append(f"  {i}. {log_entry}")

        report.append("=" * 60)
        return "\n".join(report)


def validate_and_setup_project(project_root: Optional[Path] = None) -> bool:
    """
    验证项目配置并设置 sys.path

    便利函数，用于在脚本启动时调用

    参数:
        project_root: 项目根目录（如果为 None，自动推导）

    返回:
        True 如果设置成功，False 否则
    """
    # 自动推导项目根目录
    if project_root is None:
        # 假设此脚本在 scripts/ai_governance/ 目录中
        project_root = Path(__file__).parent.parent.parent

    # 创建验证器（生产环境使用严格模式）
    validator = PathValidator(strict_mode=True)

    # 验证并添加到 sys.path
    try:
        success = validator.safe_add_to_syspath(project_root)

        if success:
            print(validator.get_validation_report())
            return True
        else:
            logger.error("❌ 项目配置验证失败")
            return False

    except Exception as e:
        logger.error(f"❌ 异常错误: {e}", exc_info=True)
        return False


# ============================================================================
# 使用示例和测试
# ============================================================================

if __name__ == "__main__":
    # 示例：在脚本启动时验证项目
    success = validate_and_setup_project()
    sys.exit(0 if success else 1)
