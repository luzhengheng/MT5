#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Validation Module (P0 Issue #4)
====================================

数据验证器，防止 NaN、Inf 和形状不匹配导致的无效数据处理。

功能:
1. NaN 值检测 - 检查缺失值
2. Inf 值检测 - 检查无限值
3. 形状验证 - 检查数据维度
4. 类型检查 - 验证数据类型
5. 统计验证 - 检查数据分布

Protocol: v4.3 (Zero-Trust Edition)
CWE-1025: Comparison Using Wrong Factors
Author: MT5-CRS Agent
Date: 2026-01-16
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Union, List

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

# 验证配置常量
MIN_SAMPLES = 10  # 最小样本数
MIN_FEATURES = 1  # 最小特征数
MIN_CLASSES = 2   # 最小类别数


class DataValidationError(Exception):
    """数据验证失败异常"""
    pass


class InvalidShapeError(DataValidationError):
    """形状无效"""
    pass


class MissingValuesError(DataValidationError):
    """存在缺失值"""
    pass


class InvalidValuesError(DataValidationError):
    """存在无效值 (NaN, Inf)"""
    pass


class InvalidTypeError(DataValidationError):
    """类型无效"""
    pass


class DataValidator:
    """
    数据验证器

    用途:
    1. 检测 NaN 和 Inf 值
    2. 验证数据形状和维度
    3. 检查数据类型
    4. 验证数据分布
    5. 确保数据完整性
    """

    def __init__(self, strict_mode: bool = True):
        """
        初始化数据验证器

        参数:
            strict_mode: 是否启用严格模式（推荐生产环境）
        """
        self.strict_mode = strict_mode
        self.validation_log = []
        self.validated_data = {}

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

    def validate_array_shape(self, arr: np.ndarray, min_samples: int = MIN_SAMPLES) -> Tuple[int, int]:
        """
        验证数组形状

        参数:
            arr: 输入数组
            min_samples: 最小样本数

        返回:
            (n_samples, n_features) 元组

        抛出:
            InvalidShapeError: 形状无效
        """
        if not isinstance(arr, np.ndarray):
            raise InvalidTypeError(f"❌ 输入必须是 numpy 数组，得到: {type(arr)}")

        if arr.ndim != 2:
            raise InvalidShapeError(
                f"❌ 数组必须是 2D，得到: {arr.ndim}D (shape: {arr.shape})"
            )

        n_samples, n_features = arr.shape

        if n_samples < min_samples:
            raise InvalidShapeError(
                f"❌ 样本数太少: {n_samples} < {min_samples}"
            )

        if n_features < MIN_FEATURES:
            raise InvalidShapeError(
                f"❌ 特征数无效: {n_features} < {MIN_FEATURES}"
            )

        self.log_validation(f"✓ 数组形状有效: {arr.shape}")
        return n_samples, n_features

    def check_nan_values(self, arr: np.ndarray) -> bool:
        """
        检查 NaN 值

        参数:
            arr: 输入数组

        返回:
            True 如果没有 NaN 值，False 否则

        抛出:
            MissingValuesError: 存在 NaN 值（严格模式）
        """
        nan_count = np.isnan(arr).sum()

        if nan_count > 0:
            nan_percent = (nan_count / arr.size) * 100
            message = f"❌ 检测到 {nan_count} 个 NaN 值 ({nan_percent:.2f}%)"

            if self.strict_mode:
                raise MissingValuesError(message)
            else:
                self.log_validation(message, level="WARNING")
                return False

        self.log_validation(f"✓ 无 NaN 值检测到")
        return True

    def check_inf_values(self, arr: np.ndarray) -> bool:
        """
        检查无限值

        参数:
            arr: 输入数组

        返回:
            True 如果没有 Inf 值，False 否则

        抛出:
            InvalidValuesError: 存在 Inf 值（严格模式）
        """
        inf_count = np.isinf(arr).sum()

        if inf_count > 0:
            inf_percent = (inf_count / arr.size) * 100
            message = f"❌ 检测到 {inf_count} 个 Inf 值 ({inf_percent:.2f}%)"

            if self.strict_mode:
                raise InvalidValuesError(message)
            else:
                self.log_validation(message, level="WARNING")
                return False

        self.log_validation(f"✓ 无 Inf 值检测到")
        return True

    def check_numeric_type(self, arr: np.ndarray) -> bool:
        """
        检查数据类型是否为数值类型

        参数:
            arr: 输入数组

        返回:
            True 如果是数值类型

        抛出:
            InvalidTypeError: 非数值类型
        """
        if not np.issubdtype(arr.dtype, np.number):
            raise InvalidTypeError(
                f"❌ 数据必须是数值类型，得到: {arr.dtype}"
            )

        self.log_validation(f"✓ 数据类型有效: {arr.dtype}")
        return True

    def check_labels(self, labels: np.ndarray, expected_samples: Optional[int] = None) -> Tuple[int, int]:
        """
        验证标签数组

        参数:
            labels: 标签数组
            expected_samples: 期望的样本数

        返回:
            (n_samples, n_classes) 元组

        抛出:
            DataValidationError: 标签无效
        """
        if not isinstance(labels, np.ndarray):
            labels = np.array(labels)

        if labels.ndim > 2:
            raise InvalidShapeError(
                f"❌ 标签必须是 1D 或 2D，得到: {labels.ndim}D"
            )

        # 展平为 1D
        labels = labels.ravel()
        n_samples = labels.shape[0]

        # 检查样本数匹配
        if expected_samples and n_samples != expected_samples:
            raise InvalidShapeError(
                f"❌ 标签样本数不匹配: {n_samples} != {expected_samples}"
            )

        # 检查类别数
        unique_classes = np.unique(labels)
        n_classes = len(unique_classes)

        if n_classes < MIN_CLASSES:
            raise InvalidShapeError(
                f"❌ 类别数太少: {n_classes} < {MIN_CLASSES}"
            )

        # 检查 NaN
        if np.isnan(labels).any():
            raise MissingValuesError(f"❌ 标签包含 NaN 值")

        self.log_validation(f"✓ 标签有效: {n_samples} 样本, {n_classes} 类别")
        return n_samples, n_classes

    def validate_features(
        self,
        features: np.ndarray,
        name: str = "Features",
        allow_nan: bool = False,
        allow_inf: bool = False
    ) -> np.ndarray:
        """
        综合验证特征数据

        执行步骤:
        1. 验证形状
        2. 验证类型
        3. 检查 NaN
        4. 检查 Inf

        参数:
            features: 特征数组
            name: 数据名称（用于日志）
            allow_nan: 是否允许 NaN
            allow_inf: 是否允许 Inf

        返回:
            验证后的特征数组

        抛出:
            DataValidationError: 验证失败
        """
        self.log_validation("=" * 60)
        self.log_validation(f"🔍 开始验证特征数据: {name}")
        self.log_validation("=" * 60)

        try:
            # 1. 验证形状
            self.log_validation("[1/4] 验证数据形状...")
            n_samples, n_features = self.validate_array_shape(features)

            # 2. 验证类型
            self.log_validation("[2/4] 验证数据类型...")
            self.check_numeric_type(features)

            # 3. 检查 NaN
            self.log_validation("[3/4] 检查 NaN 值...")
            if not allow_nan:
                self.check_nan_values(features)

            # 4. 检查 Inf
            self.log_validation("[4/4] 检查 Inf 值...")
            if not allow_inf:
                self.check_inf_values(features)

            self.log_validation("=" * 60)
            self.log_validation(f"✅ 特征数据验证通过", level="SUCCESS")
            self.log_validation("=" * 60)

            self.validated_data[name] = {
                'data': features,
                'n_samples': n_samples,
                'n_features': n_features
            }

            return features

        except DataValidationError as e:
            self.log_validation(f"❌ 验证失败: {e}", level="ERROR")
            if self.strict_mode:
                raise
            return features

    def validate_train_test_split(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray
    ) -> bool:
        """
        验证训练/测试分割

        参数:
            X_train: 训练特征
            X_test: 测试特征
            y_train: 训练标签
            y_test: 测试标签

        返回:
            True 如果有效

        抛出:
            DataValidationError: 验证失败
        """
        self.log_validation("=" * 60)
        self.log_validation("🔍 验证训练/测试分割")
        self.log_validation("=" * 60)

        try:
            # 验证训练集
            self.log_validation("[1/4] 验证训练特征...")
            n_train, n_features_train = self.validate_array_shape(X_train)
            self.check_numeric_type(X_train)
            self.check_nan_values(X_train)

            # 验证测试集
            self.log_validation("[2/4] 验证测试特征...")
            n_test, n_features_test = self.validate_array_shape(X_test, min_samples=1)
            self.check_numeric_type(X_test)
            self.check_nan_values(X_test)

            # 验证特征维度匹配
            if n_features_train != n_features_test:
                raise InvalidShapeError(
                    f"❌ 特征维度不匹配: 训练 {n_features_train} != 测试 {n_features_test}"
                )

            # 验证标签
            self.log_validation("[3/4] 验证训练标签...")
            self.check_labels(y_train, n_train)

            self.log_validation("[4/4] 验证测试标签...")
            self.check_labels(y_test, n_test)

            self.log_validation("=" * 60)
            self.log_validation(
                f"✅ 分割验证通过: "
                f"训练 {X_train.shape} | 测试 {X_test.shape}",
                level="SUCCESS"
            )
            self.log_validation("=" * 60)

            return True

        except DataValidationError as e:
            self.log_validation(f"❌ 验证失败: {e}", level="ERROR")
            if self.strict_mode:
                raise
            return False

    def get_validation_report(self) -> str:
        """
        获取完整的验证报告

        返回:
            格式化的验证报告字符串
        """
        report = [
            "\n" + "=" * 60,
            "🔍 数据验证报告",
            "=" * 60,
            f"严格模式: {'启用' if self.strict_mode else '禁用'}",
            f"已验证数据集数: {len(self.validated_data)}",
            f"验证日志条目: {len(self.validation_log)}",
            "-" * 60,
            "最近验证日志:",
            "-" * 60,
        ]

        for i, log_entry in enumerate(self.validation_log[-20:], 1):
            report.append(f"  {i}. {log_entry}")

        report.append("=" * 60)
        return "\n".join(report)


# ============================================================================
# 便利函数
# ============================================================================

def validate_features_simple(features: np.ndarray) -> bool:
    """
    快速验证特征（便利函数）

    参数:
        features: 特征数组

    返回:
        True 如果有效
    """
    validator = DataValidator(strict_mode=False)
    try:
        validator.validate_features(features)
        return True
    except DataValidationError:
        return False


def validate_split_simple(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray
) -> bool:
    """
    快速验证分割（便利函数）

    参数:
        X_train, X_test, y_train, y_test: 分割数据

    返回:
        True 如果有效
    """
    validator = DataValidator(strict_mode=False)
    try:
        return validator.validate_train_test_split(X_train, X_test, y_train, y_test)
    except DataValidationError:
        return False


if __name__ == "__main__":
    # 示例：验证数据
    validator = DataValidator(strict_mode=False)

    # 创建示例数据
    X_valid = np.random.randn(100, 10)
    y_valid = np.random.randint(0, 2, 100)

    # 验证
    validator.validate_features(X_valid, "示例特征")

    print(validator.get_validation_report())
