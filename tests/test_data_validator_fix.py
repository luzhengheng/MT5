#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite: Data Validation Prevention (P0 Issue #4)
=====================================================

验证数据验证防护措施。

Issue: CWE-1025 (Comparison Using Wrong Factors)
     NaN/Inf 值未检测可能导致：
     1. 沉默数据损坏（Silent Data Corruption）
     2. 错误的模型训练
     3. 无效的评估指标
     4. 生产错误

Fix: 实现 DataValidator 类来：
     1. 验证数组形状 (防止维度不匹配)
     2. 验证 NaN 值 (防止缺失数据)
     3. 验证 Inf 值 (防止无穷大)
     4. 验证数据类型 (防止类型错误)
     5. 验证标签 (防止标签问题)
     6. 验证训练/测试分割 (防止维度不匹配)

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ai_governance.data_validator import (
    DataValidator,
    MissingValuesError,
    InvalidValuesError,
    InvalidShapeError,
    InvalidTypeError,
)


class DataValidationTestHelper:
    """数据验证防护测试助手"""

    @staticmethod
    def test_nan_detection():
        """测试 NaN 值检测"""
        validator = DataValidator()

        # 测试无 NaN 的数组
        valid_array = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = validator.check_nan_values(valid_array)
        assert result is True, "Should have no NaN (return True)"

        # 测试包含 NaN 的数组
        invalid_array = np.array([[1.0, 2.0], [3.0, np.nan]])
        try:
            # 严格模式会抛出异常
            strict_validator = DataValidator(strict_mode=True)
            strict_validator.check_nan_values(invalid_array)
            assert False, "Should have raised MissingValuesError"
        except MissingValuesError:
            pass  # Expected

        return True

    @staticmethod
    def test_inf_detection():
        """测试 Inf 值检测"""
        validator = DataValidator()

        # 测试无 Inf 的数组
        valid_array = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = validator.check_inf_values(valid_array)
        assert result is True, "Should have no Inf (return True)"

        # 测试包含正 Inf 的数组
        invalid_array = np.array([[1.0, 2.0], [3.0, np.inf]])
        try:
            strict_validator = DataValidator(strict_mode=True)
            strict_validator.check_inf_values(invalid_array)
            assert False, "Should have raised InvalidValuesError"
        except InvalidValuesError:
            pass  # Expected

        # 测试包含负 Inf 的数组
        invalid_array = np.array([[1.0, 2.0], [3.0, -np.inf]])
        try:
            strict_validator = DataValidator(strict_mode=True)
            strict_validator.check_inf_values(invalid_array)
            assert False, "Should have raised InvalidValuesError"
        except InvalidValuesError:
            pass  # Expected

        return True

    @staticmethod
    def test_array_shape_validation():
        """测试数组形状验证"""
        validator = DataValidator()

        # 测试有效形状
        valid_array = np.random.randn(100, 20)
        rows, cols = validator.validate_array_shape(valid_array, min_samples=10)
        assert rows == 100 and cols == 20, "Shape should be (100, 20)"

        # 测试样本过少
        too_small = np.random.randn(5, 20)
        try:
            validator.validate_array_shape(too_small, min_samples=10)
            assert False, "Should have raised InvalidShapeError"
        except InvalidShapeError:
            pass  # Expected

        # 测试 1D 数组（应转为 2D）
        array_1d = np.array([1, 2, 3, 4, 5])
        try:
            validator.validate_array_shape(array_1d)
            assert False, "Should have raised InvalidShapeError for 1D"
        except InvalidShapeError:
            pass  # Expected

        return True

    @staticmethod
    def test_numeric_type_validation():
        """测试数值类型验证"""
        validator = DataValidator()

        # 测试有效的浮点数数组
        valid_float = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        assert validator.check_numeric_type(valid_float) is True

        # 测试有效的整数数组
        valid_int = np.array([[1, 2], [3, 4]], dtype=np.int32)
        assert validator.check_numeric_type(valid_int) is True

        # 测试无效的字符串数组
        invalid_str = np.array([["a", "b"], ["c", "d"]])
        try:
            validator.check_numeric_type(invalid_str)
            assert False, "Should have raised InvalidTypeError"
        except InvalidTypeError:
            pass  # Expected

        return True

    @staticmethod
    def test_labels_validation():
        """测试标签验证"""
        validator = DataValidator()

        # 测试有效的二分类标签
        valid_labels = np.array([0, 1, 0, 1, 0, 1])
        n_samples, n_classes = validator.check_labels(valid_labels)
        assert n_samples == 6 and n_classes == 2, "Should have 6 samples, 2 classes"

        # 测试有效的多分类标签
        valid_multiclass = np.array([0, 1, 2, 3, 0, 1, 2, 3])
        n_samples, n_classes = validator.check_labels(valid_multiclass)
        assert n_samples == 8 and n_classes == 4, "Should have 8 samples, 4 classes"

        # 测试标签中包含 NaN
        invalid_labels = np.array([0.0, 1.0, np.nan, 1.0])
        try:
            strict_validator = DataValidator(strict_mode=True)
            strict_validator.check_labels(invalid_labels)
            assert False, "Should have raised MissingValuesError"
        except MissingValuesError:
            pass  # Expected

        return True

    @staticmethod
    def test_validate_features():
        """测试特征验证"""
        validator = DataValidator(strict_mode=False)

        # 测试有效的特征
        valid_features = np.random.randn(100, 20)
        result = validator.validate_features(valid_features, "TestFeatures")
        assert result is not None, "Should return validated features"

        # 测试包含 NaN 的特征（严格模式）
        strict_validator = DataValidator(strict_mode=True)
        features_with_nan = np.random.randn(100, 20)
        features_with_nan[5, 3] = np.nan

        try:
            strict_validator.validate_features(features_with_nan)
            assert False, "Should have raised MissingValuesError"
        except MissingValuesError:
            pass  # Expected

        return True

    @staticmethod
    def test_train_test_split_validation():
        """测试训练/测试分割验证"""
        validator = DataValidator()

        # 测试有效的分割
        X_train = np.random.randn(80, 20)
        X_test = np.random.randn(20, 20)
        y_train = np.random.randint(0, 2, 80)
        y_test = np.random.randint(0, 2, 20)

        result = validator.validate_train_test_split(
            X_train, X_test, y_train, y_test
        )
        assert result is True, "Should validate correctly"

        # 测试特征维度不匹配
        X_test_wrong_dim = np.random.randn(20, 15)  # 应该是 20 列
        try:
            validator.validate_train_test_split(
                X_train, X_test_wrong_dim, y_train, y_test
            )
            assert False, "Should have raised InvalidShapeError"
        except InvalidShapeError:
            pass  # Expected

        # 测试样本数不匹配
        y_test_wrong_samples = np.random.randint(0, 2, 15)
        try:
            validator.validate_train_test_split(
                X_train, X_test, y_train, y_test_wrong_samples
            )
            assert False, "Should have raised InvalidShapeError"
        except InvalidShapeError:
            pass  # Expected

        return True

    @staticmethod
    def test_validation_report():
        """测试验证报告生成"""
        validator = DataValidator()

        # 进行一些验证
        valid_array = np.random.randn(100, 20)
        validator.validate_features(valid_array)

        report = validator.get_validation_report()
        assert isinstance(report, str), "Report should be string"
        assert len(report) > 0, "Report should not be empty"
        assert "✓" in report or "✅" in report or "SUCCESS" in report

        return True

    @staticmethod
    def test_strict_vs_lenient_mode():
        """测试严格模式和宽松模式"""
        # 严格模式应该抛出异常
        strict_validator = DataValidator(strict_mode=True)
        features_with_nan = np.random.randn(100, 20)
        features_with_nan[5, 3] = np.nan

        try:
            strict_validator.validate_features(features_with_nan)
            assert False, "Strict mode should raise exception"
        except MissingValuesError:
            pass  # Expected

        # 宽松模式应该返回 None 或处理优雅
        lenient_validator = DataValidator(strict_mode=False)
        result = lenient_validator.validate_features(features_with_nan)
        # 应该不抛出异常

        return True

    @staticmethod
    def test_edge_case_empty_array():
        """测试边界情况：空数组"""
        validator = DataValidator()

        empty_array = np.array([]).reshape(0, 10)

        try:
            validator.validate_array_shape(empty_array, min_samples=1)
            assert False, "Should raise InvalidShapeError for empty array"
        except InvalidShapeError:
            pass  # Expected

        return True

    @staticmethod
    def test_edge_case_single_feature():
        """测试边界情况：单个特征"""
        validator = DataValidator()

        single_feature = np.random.randn(100, 1)
        rows, cols = validator.validate_array_shape(single_feature)
        assert rows == 100 and cols == 1

        return True

    @staticmethod
    def test_all_zeros_array():
        """测试全零数组"""
        validator = DataValidator()

        zeros_array = np.zeros((100, 20))
        result = validator.validate_features(zeros_array)
        assert result is not None, "All-zeros array should be valid"

        return True

    @staticmethod
    def test_all_ones_array():
        """测试全一数组"""
        validator = DataValidator()

        ones_array = np.ones((100, 20))
        result = validator.validate_features(ones_array)
        assert result is not None, "All-ones array should be valid"

        return True

    @staticmethod
    def test_mixed_positive_negative():
        """测试混合正负数"""
        validator = DataValidator()

        mixed_array = np.random.randn(100, 20)
        assert (mixed_array > 0).any() and (mixed_array < 0).any()

        result = validator.validate_features(mixed_array)
        assert result is not None

        return True

    @staticmethod
    def test_very_large_values():
        """测试极大值（但不是 Inf）"""
        validator = DataValidator()

        large_array = np.random.randn(100, 20) * 1e10
        result = validator.validate_features(large_array)
        assert result is not None, "Very large values should be valid"

        return True

    @staticmethod
    def test_very_small_values():
        """测试极小值（但不是 Inf）"""
        validator = DataValidator()

        small_array = np.random.randn(100, 20) * 1e-10
        result = validator.validate_features(small_array)
        assert result is not None, "Very small values should be valid"

        return True


def test_001_nan_detection():
    """Test 001: NaN 值检测"""
    print("\n" + "=" * 80)
    print("Test 001: NaN 值检测")
    print("=" * 80)

    result = DataValidationTestHelper.test_nan_detection()
    assert result, "NaN detection test failed"
    print("✅ Test 001 PASSED: NaN 值检测正确")


def test_002_inf_detection():
    """Test 002: Inf 值检测"""
    print("\n" + "=" * 80)
    print("Test 002: Inf 值检测")
    print("=" * 80)

    result = DataValidationTestHelper.test_inf_detection()
    assert result, "Inf detection test failed"
    print("✅ Test 002 PASSED: Inf 值检测正确")


def test_003_array_shape_validation():
    """Test 003: 数组形状验证"""
    print("\n" + "=" * 80)
    print("Test 003: 数组形状验证")
    print("=" * 80)

    result = DataValidationTestHelper.test_array_shape_validation()
    assert result, "Array shape validation test failed"
    print("✅ Test 003 PASSED: 数组形状验证正确")


def test_004_numeric_type_validation():
    """Test 004: 数值类型验证"""
    print("\n" + "=" * 80)
    print("Test 004: 数值类型验证")
    print("=" * 80)

    result = DataValidationTestHelper.test_numeric_type_validation()
    assert result, "Numeric type validation test failed"
    print("✅ Test 004 PASSED: 数值类型验证正确")


def test_005_labels_validation():
    """Test 005: 标签验证"""
    print("\n" + "=" * 80)
    print("Test 005: 标签验证")
    print("=" * 80)

    result = DataValidationTestHelper.test_labels_validation()
    assert result, "Labels validation test failed"
    print("✅ Test 005 PASSED: 标签验证正确")


def test_006_validate_features():
    """Test 006: 特征验证"""
    print("\n" + "=" * 80)
    print("Test 006: 特征验证")
    print("=" * 80)

    result = DataValidationTestHelper.test_validate_features()
    assert result, "Feature validation test failed"
    print("✅ Test 006 PASSED: 特征验证正确")


def test_007_train_test_split_validation():
    """Test 007: 训练/测试分割验证"""
    print("\n" + "=" * 80)
    print("Test 007: 训练/测试分割验证")
    print("=" * 80)

    result = DataValidationTestHelper.test_train_test_split_validation()
    assert result, "Train/test split validation test failed"
    print("✅ Test 007 PASSED: 训练/测试分割验证正确")


def test_008_validation_report():
    """Test 008: 验证报告生成"""
    print("\n" + "=" * 80)
    print("Test 008: 验证报告生成")
    print("=" * 80)

    result = DataValidationTestHelper.test_validation_report()
    assert result, "Validation report test failed"
    print("✅ Test 008 PASSED: 验证报告生成正确")


def test_009_strict_vs_lenient_mode():
    """Test 009: 严格/宽松模式"""
    print("\n" + "=" * 80)
    print("Test 009: 严格/宽松模式")
    print("=" * 80)

    result = DataValidationTestHelper.test_strict_vs_lenient_mode()
    assert result, "Strict vs lenient mode test failed"
    print("✅ Test 009 PASSED: 严格/宽松模式正确")


def test_010_edge_case_empty_array():
    """Test 010: 边界情况 - 空数组"""
    print("\n" + "=" * 80)
    print("Test 010: 边界情况 - 空数组")
    print("=" * 80)

    result = DataValidationTestHelper.test_edge_case_empty_array()
    assert result, "Empty array edge case test failed"
    print("✅ Test 010 PASSED: 空数组边界情况正确")


def test_011_edge_case_single_feature():
    """Test 011: 边界情况 - 单个特征"""
    print("\n" + "=" * 80)
    print("Test 011: 边界情况 - 单个特征")
    print("=" * 80)

    result = DataValidationTestHelper.test_edge_case_single_feature()
    assert result, "Single feature edge case test failed"
    print("✅ Test 011 PASSED: 单个特征边界情况正确")


def test_012_all_zeros_array():
    """Test 012: 全零数组"""
    print("\n" + "=" * 80)
    print("Test 012: 全零数组")
    print("=" * 80)

    result = DataValidationTestHelper.test_all_zeros_array()
    assert result, "All-zeros array test failed"
    print("✅ Test 012 PASSED: 全零数组正确")


def test_013_all_ones_array():
    """Test 013: 全一数组"""
    print("\n" + "=" * 80)
    print("Test 013: 全一数组")
    print("=" * 80)

    result = DataValidationTestHelper.test_all_ones_array()
    assert result, "All-ones array test failed"
    print("✅ Test 013 PASSED: 全一数组正确")


def test_014_mixed_positive_negative():
    """Test 014: 混合正负数"""
    print("\n" + "=" * 80)
    print("Test 014: 混合正负数")
    print("=" * 80)

    result = DataValidationTestHelper.test_mixed_positive_negative()
    assert result, "Mixed positive/negative test failed"
    print("✅ Test 014 PASSED: 混合正负数正确")


def test_015_extreme_values():
    """Test 015: 极值（大和小）"""
    print("\n" + "=" * 80)
    print("Test 015: 极值（大和小）")
    print("=" * 80)

    result1 = DataValidationTestHelper.test_very_large_values()
    result2 = DataValidationTestHelper.test_very_small_values()
    assert result1 and result2, "Extreme values test failed"
    print("✅ Test 015 PASSED: 极值处理正确")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("数据验证防护测试套件 (P0 Issue #4)")
    print("=" * 80)

    tests = [
        test_001_nan_detection,
        test_002_inf_detection,
        test_003_array_shape_validation,
        test_004_numeric_type_validation,
        test_005_labels_validation,
        test_006_validate_features,
        test_007_train_test_split_validation,
        test_008_validation_report,
        test_009_strict_vs_lenient_mode,
        test_010_edge_case_empty_array,
        test_011_edge_case_single_feature,
        test_012_all_zeros_array,
        test_013_all_ones_array,
        test_014_mixed_positive_negative,
        test_015_extreme_values,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)

    if failed == 0:
        print("\n✅ 所有数据验证防护测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
