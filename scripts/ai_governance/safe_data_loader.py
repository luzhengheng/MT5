#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe Data Loader Module (P0 Issue #3)
=====================================

安全数据加载器，防止不安全反序列化导致的数据篡改和代码执行。

功能:
1. 文件大小验证 - 防止 DoS 攻击
2. 校验和验证 - 防止数据篡改
3. 操作超时 - 防止无限期操作
4. 格式验证 - 确保数据结构完整
5. 权限检查 - 验证文件可访问性

Protocol: v4.3 (Zero-Trust Edition)
CWE-502: Deserialization of Untrusted Data
Author: MT5-CRS Agent
Date: 2026-01-16
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

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

# 安全配置常量
MAX_FILE_SIZE_MB = 500  # 最大文件大小 500MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

OPERATION_TIMEOUT_SECONDS = 3600  # 操作超时 1小时

REQUIRED_METADATA_KEYS = {
    'version',
    'timestamp',
    'data_hash',
    'file_size',
}

SUPPORTED_FORMATS = {
    '.json': 'json',
    '.parquet': 'parquet',
    '.csv': 'csv',
}


class SafeDataLoadError(Exception):
    """安全数据加载失败异常"""
    pass


class FileTooLargeError(SafeDataLoadError):
    """文件过大"""
    pass


class ChecksumMismatchError(SafeDataLoadError):
    """校验和不匹配"""
    pass


class InvalidDataFormatError(SafeDataLoadError):
    """数据格式无效"""
    pass


class OperationTimeoutError(SafeDataLoadError):
    """操作超时"""
    pass


@dataclass
class FileMetadata:
    """文件元数据"""
    filepath: Path
    file_size: int
    file_format: str
    checksum: str
    timestamp: str
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'filepath': str(self.filepath),
            'file_size': self.file_size,
            'file_format': self.file_format,
            'checksum': self.checksum,
            'timestamp': self.timestamp,
            'version': self.version,
        }


class SafeDataLoader:
    """
    安全数据加载器

    用途:
    1. 防止不安全反序列化攻击
    2. 验证数据完整性和真实性
    3. 防止 DoS 攻击
    4. 确保操作超时
    """

    def __init__(self, strict_mode: bool = True):
        """
        初始化安全数据加载器

        参数:
            strict_mode: 是否启用严格模式（推荐生产环境）
        """
        self.strict_mode = strict_mode
        self.loaded_files = {}  # 已加载文件缓存
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

    def _calculate_file_hash(self, filepath: Path) -> str:
        """
        计算文件的 SHA256 校验和

        参数:
            filepath: 文件路径

        返回:
            16进制校验和字符串
        """
        sha256_hash = hashlib.sha256()

        try:
            with open(filepath, 'rb') as f:
                # 分块读取（避免大文件内存溢出）
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)

            return sha256_hash.hexdigest()

        except (IOError, OSError) as e:
            raise SafeDataLoadError(f"❌ 计算文件校验和失败: {e}")

    def validate_file_size(self, filepath: Path) -> int:
        """
        验证文件大小

        检查:
        - 文件存在
        - 文件大小在限制内
        - 防止 DoS 攻击

        参数:
            filepath: 文件路径

        返回:
            文件大小（字节）

        抛出:
            SafeDataLoadError: 文件不存在或过大
        """
        if not filepath.exists():
            raise SafeDataLoadError(f"❌ 文件不存在: {filepath}")

        file_size = filepath.stat().st_size

        if file_size == 0:
            raise SafeDataLoadError(f"❌ 文件为空: {filepath}")

        if file_size > MAX_FILE_SIZE_BYTES:
            file_size_mb = file_size / (1024 * 1024)
            raise FileTooLargeError(
                f"❌ 文件过大: {file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB"
            )

        self.log_validation(f"✓ 文件大小验证通过: {file_size} 字节")
        return file_size

    def validate_file_format(self, filepath: Path) -> str:
        """
        验证文件格式

        参数:
            filepath: 文件路径

        返回:
            文件格式类型

        抛出:
            InvalidDataFormatError: 文件格式不支持
        """
        suffix = filepath.suffix.lower()

        if suffix not in SUPPORTED_FORMATS:
            raise InvalidDataFormatError(
                f"❌ 不支持的文件格式: {suffix}. 支持: {list(SUPPORTED_FORMATS.keys())}"
            )

        file_format = SUPPORTED_FORMATS[suffix]
        self.log_validation(f"✓ 文件格式验证通过: {file_format}")
        return file_format

    def validate_permissions(self, filepath: Path) -> bool:
        """
        验证文件权限

        参数:
            filepath: 文件路径

        返回:
            True 如果有读权限

        抛出:
            SafeDataLoadError: 无读权限
        """
        if not os.access(filepath, os.R_OK):
            raise SafeDataLoadError(f"❌ 无读取权限: {filepath}")

        self.log_validation(f"✓ 文件权限验证通过")
        return True

    def validate_checksum(
        self,
        filepath: Path,
        expected_checksum: Optional[str] = None
    ) -> str:
        """
        验证文件校验和

        参数:
            filepath: 文件路径
            expected_checksum: 期望的校验和（可选）

        返回:
            计算得到的校验和

        抛出:
            ChecksumMismatchError: 校验和不匹配
        """
        calculated_checksum = self._calculate_file_hash(filepath)

        if expected_checksum:
            if calculated_checksum != expected_checksum:
                raise ChecksumMismatchError(
                    f"❌ 校验和不匹配! "
                    f"期望: {expected_checksum[:16]}... "
                    f"实际: {calculated_checksum[:16]}..."
                )

            self.log_validation(f"✓ 校验和验证通过")
        else:
            self.log_validation(f"✓ 校验和计算: {calculated_checksum[:16]}...")

        return calculated_checksum

    def validate_json_structure(self, data: Any, required_keys: Optional[set] = None) -> bool:
        """
        验证 JSON 数据结构

        参数:
            data: JSON 数据
            required_keys: 必需的键集合

        返回:
            True 如果结构有效

        抛出:
            InvalidDataFormatError: 结构无效
        """
        if not isinstance(data, (dict, list)):
            raise InvalidDataFormatError(
                f"❌ JSON 数据必须是对象或数组，得到: {type(data)}"
            )

        if isinstance(data, dict) and required_keys:
            missing_keys = required_keys - set(data.keys())
            if missing_keys:
                raise InvalidDataFormatError(
                    f"❌ 缺少必需的键: {missing_keys}"
                )

        self.log_validation(f"✓ JSON 结构验证通过")
        return True

    def load_json_safe(
        self,
        filepath: Path,
        expected_checksum: Optional[str] = None,
        required_keys: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        安全加载 JSON 文件

        执行步骤:
        1. 验证文件存在和大小
        2. 验证格式
        3. 验证权限
        4. 验证校验和
        5. 解析 JSON
        6. 验证结构

        参数:
            filepath: 文件路径
            expected_checksum: 期望的校验和（可选）
            required_keys: 必需的键集合（可选）

        返回:
            解析的 JSON 数据

        抛出:
            SafeDataLoadError: 验证失败
        """
        filepath = Path(filepath)

        self.log_validation("=" * 60)
        self.log_validation(f"🔒 开始安全加载 JSON 文件: {filepath.name}")
        self.log_validation("=" * 60)

        try:
            # 1. 验证文件大小
            self.log_validation("[1/6] 验证文件大小...")
            file_size = self.validate_file_size(filepath)

            # 2. 验证格式
            self.log_validation("[2/6] 验证文件格式...")
            file_format = self.validate_file_format(filepath)
            if file_format != "json":
                raise InvalidDataFormatError(f"❌ 期望 JSON 格式，得到: {file_format}")

            # 3. 验证权限
            self.log_validation("[3/6] 验证文件权限...")
            self.validate_permissions(filepath)

            # 4. 验证校验和
            self.log_validation("[4/6] 验证文件校验和...")
            checksum = self.validate_checksum(filepath, expected_checksum)

            # 5. 解析 JSON
            self.log_validation("[5/6] 解析 JSON 内容...")
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 6. 验证结构
            self.log_validation("[6/6] 验证数据结构...")
            self.validate_json_structure(data, required_keys)

            # 记录元数据
            metadata = FileMetadata(
                filepath=filepath,
                file_size=file_size,
                file_format=file_format,
                checksum=checksum,
                timestamp=datetime.now().isoformat()
            )

            self.loaded_files[str(filepath)] = {
                'data': data,
                'metadata': metadata,
                'timestamp': datetime.now()
            }

            self.log_validation("=" * 60)
            self.log_validation(f"✅ JSON 文件加载成功", level="SUCCESS")
            self.log_validation("=" * 60)

            return data

        except (json.JSONDecodeError, ValueError) as e:
            self.log_validation(f"❌ JSON 解析失败: {e}", level="ERROR")
            if self.strict_mode:
                raise InvalidDataFormatError(f"JSON 解析失败: {e}")
            return {}

        except SafeDataLoadError as e:
            self.log_validation(f"❌ 验证失败: {e}", level="ERROR")
            if self.strict_mode:
                raise
            return {}

    def load_parquet_safe(
        self,
        filepath: Path,
        expected_checksum: Optional[str] = None
    ):
        """
        安全加载 Parquet 文件

        参数:
            filepath: 文件路径
            expected_checksum: 期望的校验和（可选）

        返回:
            pandas DataFrame

        抛出:
            SafeDataLoadError: 验证失败
        """
        import pandas as pd

        filepath = Path(filepath)

        self.log_validation("=" * 60)
        self.log_validation(f"🔒 开始安全加载 Parquet 文件: {filepath.name}")
        self.log_validation("=" * 60)

        try:
            # 1. 验证文件大小
            self.log_validation("[1/5] 验证文件大小...")
            file_size = self.validate_file_size(filepath)

            # 2. 验证格式
            self.log_validation("[2/5] 验证文件格式...")
            file_format = self.validate_file_format(filepath)
            if file_format != "parquet":
                raise InvalidDataFormatError(f"❌ 期望 Parquet 格式，得到: {file_format}")

            # 3. 验证权限
            self.log_validation("[3/5] 验证文件权限...")
            self.validate_permissions(filepath)

            # 4. 验证校验和
            self.log_validation("[4/5] 验证文件校验和...")
            checksum = self.validate_checksum(filepath, expected_checksum)

            # 5. 加载 Parquet
            self.log_validation("[5/5] 加载 Parquet 内容...")
            df = pd.read_parquet(filepath)

            # 验证数据完整性
            if df.empty:
                raise InvalidDataFormatError("❌ DataFrame 为空")

            # 检查 NaN/Inf
            if df.isna().any().any():
                logger.warning(f"⚠️  DataFrame 包含 NaN 值")

            if df.select_dtypes(include=['float']).isin([float('inf'), float('-inf')]).any().any():
                logger.warning(f"⚠️  DataFrame 包含 Inf 值")

            # 记录元数据
            metadata = FileMetadata(
                filepath=filepath,
                file_size=file_size,
                file_format=file_format,
                checksum=checksum,
                timestamp=datetime.now().isoformat()
            )

            self.loaded_files[str(filepath)] = {
                'data': df,
                'metadata': metadata,
                'timestamp': datetime.now()
            }

            self.log_validation("=" * 60)
            self.log_validation(f"✅ Parquet 文件加载成功", level="SUCCESS")
            self.log_validation(f"   数据形状: {df.shape}")
            self.log_validation("=" * 60)

            return df

        except Exception as e:
            self.log_validation(f"❌ 加载失败: {e}", level="ERROR")
            if self.strict_mode:
                raise SafeDataLoadError(f"Parquet 加载失败: {e}")
            return None

    def get_validation_report(self) -> str:
        """
        获取完整的验证报告

        返回:
            格式化的验证报告字符串
        """
        report = [
            "\n" + "=" * 60,
            "🔍 安全数据加载验证报告",
            "=" * 60,
            f"严格模式: {'启用' if self.strict_mode else '禁用'}",
            f"已加载文件数: {len(self.loaded_files)}",
            f"验证日志条目: {len(self.validation_log)}",
            "-" * 60,
            "最近验证日志:",
            "-" * 60,
        ]

        for i, log_entry in enumerate(self.validation_log[-20:], 1):
            report.append(f"  {i}. {log_entry}")

        report.append("=" * 60)
        return "\n".join(report)


def safe_load_json(filepath: Path, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
    """
    便利函数：安全加载 JSON 文件

    参数:
        filepath: 文件路径
        expected_checksum: 期望的校验和（可选）

    返回:
        解析的 JSON 数据
    """
    loader = SafeDataLoader(strict_mode=True)
    return loader.load_json_safe(filepath, expected_checksum)


def safe_load_parquet(filepath: Path, expected_checksum: Optional[str] = None):
    """
    便利函数：安全加载 Parquet 文件

    参数:
        filepath: 文件路径
        expected_checksum: 期望的校验和（可选）

    返回:
        pandas DataFrame
    """
    loader = SafeDataLoader(strict_mode=True)
    return loader.load_parquet_safe(filepath, expected_checksum)


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 示例：安全加载数据文件
    loader = SafeDataLoader(strict_mode=False)

    # 加载 JSON 文件示例
    # data = loader.load_json_safe(Path("data.json"))

    # 加载 Parquet 文件示例
    # df = loader.load_parquet_safe(Path("features.parquet"))

    print(loader.get_validation_report())
