#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite: Broad Exception Handling Prevention (P0 Issue #5)
=============================================================

验证安全异常处理。

Issue: CWE-1024 (Comparison Using Wrong Factors)
     宽泛的异常捕获可能导致：
     1. 隐藏安全问题
     2. 掩盖真实错误
     3. 难以调试
     4. 信息泄露

Fix: 实现 ExceptionHandler 来：
     1. 定义特定异常类型
     2. 分类异常处理
     3. 防止信息泄露
     4. 安全日志记录

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ai_governance.exception_handler import (
    BaseSecurityError,
    DataProcessingError,
    ModelTrainingError,
    FileOperationError,
    ValidationError,
    ConfigurationError,
    DataShapeError,
    DataTypeError,
    DataIntegrityError,
    MissingDataError,
    TrialError,
    ParameterError,
    ModelFittingError,
    EvaluationError,
    FileNotFoundError,
    FileAccessError,
    FileReadError,
    FileWriteError,
    ExceptionHandler,
    secure_handler,
)


class ExceptionHandlingTestHelper:
    """异常处理防护测试助手"""

    @staticmethod
    def test_exception_hierarchy():
        """测试异常类层次结构"""
        # 验证继承关系
        assert issubclass(DataShapeError, DataProcessingError)
        assert issubclass(DataTypeError, DataProcessingError)
        assert issubclass(DataIntegrityError, DataProcessingError)
        assert issubclass(MissingDataError, DataProcessingError)

        assert issubclass(TrialError, ModelTrainingError)
        assert issubclass(ParameterError, ModelTrainingError)
        assert issubclass(ModelFittingError, ModelTrainingError)
        assert issubclass(EvaluationError, ModelTrainingError)

        assert issubclass(FileNotFoundError, FileOperationError)
        assert issubclass(FileAccessError, FileOperationError)
        assert issubclass(FileReadError, FileOperationError)
        assert issubclass(FileWriteError, FileOperationError)

        assert issubclass(DataProcessingError, BaseSecurityError)
        assert issubclass(ModelTrainingError, BaseSecurityError)
        assert issubclass(FileOperationError, BaseSecurityError)

        return True

    @staticmethod
    def test_exception_raising():
        """测试异常抛出"""
        # 测试数据处理异常
        try:
            raise DataShapeError("Test shape error")
        except DataProcessingError:
            pass  # Expected

        # 测试模型异常
        try:
            raise TrialError("Test trial error")
        except ModelTrainingError:
            pass  # Expected

        # 测试文件异常
        try:
            raise FileNotFoundError("Test file not found")
        except FileOperationError:
            pass  # Expected

        return True

    @staticmethod
    def test_exception_handler_data_error():
        """测试 ExceptionHandler 处理数据错误"""
        error = DataShapeError("Shape mismatch: 10 != 20")
        # 应该记录错误但不抛出异常
        try:
            ExceptionHandler.handle_data_error(error, "test_context")
        except Exception:
            assert False, "Handler should not raise exception"

        return True

    @staticmethod
    def test_exception_handler_model_error():
        """测试 ExceptionHandler 处理模型错误"""
        error = ModelFittingError("Failed to fit model")
        try:
            ExceptionHandler.handle_model_error(error, "test_context")
        except Exception:
            assert False, "Handler should not raise exception"

        return True

    @staticmethod
    def test_exception_handler_file_error():
        """测试 ExceptionHandler 处理文件错误"""
        error = FileNotFoundError("File not found")
        try:
            ExceptionHandler.handle_file_error(error, "test_context")
        except Exception:
            assert False, "Handler should not raise exception"

        return True

    @staticmethod
    def test_safe_execute_success():
        """测试 safe_execute 成功执行"""
        def successful_func(x, y):
            return x + y

        result = ExceptionHandler.safe_execute(
            successful_func, 5, 3, context="test"
        )
        assert result == 8, "Should return correct result"

        return True

    @staticmethod
    def test_safe_execute_with_exception():
        """测试 safe_execute 异常处理"""
        def failing_func():
            raise ValueError("Test error")

        result = ExceptionHandler.safe_execute(
            failing_func, context="test", default_return=None
        )
        assert result is None, "Should return default value on error"

        return True

    @staticmethod
    def test_safe_execute_with_security_error():
        """测试 safe_execute 安全异常处理"""
        def security_error_func():
            raise DataShapeError("Shape mismatch")

        result = ExceptionHandler.safe_execute(
            security_error_func,
            context="test",
            default_return=-1,
            error_handler=ExceptionHandler.handle_data_error
        )
        assert result == -1, "Should return default on security error"

        return True

    @staticmethod
    def test_secure_handler_decorator():
        """测试 secure_handler 装饰器"""
        @secure_handler(
            error_types=(ValueError, TypeError),
            context="test_decorator",
            default_return=0
        )
        def decorated_func(x, y):
            if not isinstance(x, (int, float)):
                raise TypeError("x must be numeric")
            return x + y

        # 正常执行
        result = decorated_func(5, 3)
        assert result == 8

        # 异常执行应返回默认值
        result = decorated_func("invalid", 3)
        assert result == 0

        return True

    @staticmethod
    def test_import_error_handling():
        """测试导入错误处理"""
        def import_failing_func():
            import nonexistent_module  # noqa: F401

        result = ExceptionHandler.safe_execute(
            import_failing_func, context="test", default_return=None
        )
        assert result is None, "Should handle import errors gracefully"

        return True

    @staticmethod
    def test_multiple_exception_types():
        """测试多个异常类型"""
        exceptions_to_test = [
            DataShapeError("shape"),
            DataTypeError("type"),
            DataIntegrityError("integrity"),
            MissingDataError("missing"),
            TrialError("trial"),
            ParameterError("param"),
            ModelFittingError("fitting"),
            EvaluationError("eval"),
        ]

        for exc in exceptions_to_test:
            assert isinstance(exc, BaseSecurityError)

        return True

    @staticmethod
    def test_specific_vs_broad_exception():
        """测试特定异常 vs 宽泛异常的区别"""
        # 特定异常：可以被特定处理
        specific_error = DataShapeError("Test")
        assert isinstance(specific_error, DataProcessingError)
        assert isinstance(specific_error, BaseSecurityError)

        # 这在宽泛 except Exception 中会被掩盖
        def would_be_masked():
            raise DataShapeError("Masked by broad exception")

        # 但现在可以具体处理
        try:
            would_be_masked()
        except DataProcessingError:
            pass  # Specifically caught

        return True


def test_001_exception_hierarchy():
    """Test 001: 异常类层次结构"""
    print("\n" + "=" * 80)
    print("Test 001: 异常类层次结构")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_exception_hierarchy()
    assert result, "Exception hierarchy test failed"
    print("✅ Test 001 PASSED: 异常类层次结构正确")


def test_002_exception_raising():
    """Test 002: 异常抛出"""
    print("\n" + "=" * 80)
    print("Test 002: 异常抛出")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_exception_raising()
    assert result, "Exception raising test failed"
    print("✅ Test 002 PASSED: 异常抛出正确")


def test_003_data_error_handler():
    """Test 003: 数据错误处理"""
    print("\n" + "=" * 80)
    print("Test 003: 数据错误处理")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_exception_handler_data_error()
    assert result, "Data error handler test failed"
    print("✅ Test 003 PASSED: 数据错误处理正确")


def test_004_model_error_handler():
    """Test 004: 模型错误处理"""
    print("\n" + "=" * 80)
    print("Test 004: 模型错误处理")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_exception_handler_model_error()
    assert result, "Model error handler test failed"
    print("✅ Test 004 PASSED: 模型错误处理正确")


def test_005_file_error_handler():
    """Test 005: 文件错误处理"""
    print("\n" + "=" * 80)
    print("Test 005: 文件错误处理")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_exception_handler_file_error()
    assert result, "File error handler test failed"
    print("✅ Test 005 PASSED: 文件错误处理正确")


def test_006_safe_execute_success():
    """Test 006: safe_execute 成功执行"""
    print("\n" + "=" * 80)
    print("Test 006: safe_execute 成功执行")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_safe_execute_success()
    assert result, "Safe execute success test failed"
    print("✅ Test 006 PASSED: safe_execute 成功执行正确")


def test_007_safe_execute_with_exception():
    """Test 007: safe_execute 异常处理"""
    print("\n" + "=" * 80)
    print("Test 007: safe_execute 异常处理")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_safe_execute_with_exception()
    assert result, "Safe execute exception test failed"
    print("✅ Test 007 PASSED: safe_execute 异常处理正确")


def test_008_safe_execute_security_error():
    """Test 008: safe_execute 安全异常"""
    print("\n" + "=" * 80)
    print("Test 008: safe_execute 安全异常")
    print("=" * 80)

    result = (
        ExceptionHandlingTestHelper.test_safe_execute_with_security_error()
    )
    assert result, "Safe execute security error test failed"
    print("✅ Test 008 PASSED: safe_execute 安全异常正确")


def test_009_secure_handler_decorator():
    """Test 009: secure_handler 装饰器"""
    print("\n" + "=" * 80)
    print("Test 009: secure_handler 装饰器")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_secure_handler_decorator()
    assert result, "Secure handler decorator test failed"
    print("✅ Test 009 PASSED: secure_handler 装饰器正确")


def test_010_import_error_handling():
    """Test 010: 导入错误处理"""
    print("\n" + "=" * 80)
    print("Test 010: 导入错误处理")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_import_error_handling()
    assert result, "Import error handling test failed"
    print("✅ Test 010 PASSED: 导入错误处理正确")


def test_011_multiple_exception_types():
    """Test 011: 多个异常类型"""
    print("\n" + "=" * 80)
    print("Test 011: 多个异常类型")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_multiple_exception_types()
    assert result, "Multiple exception types test failed"
    print("✅ Test 011 PASSED: 多个异常类型正确")


def test_012_specific_vs_broad_exception():
    """Test 012: 特定 vs 宽泛异常"""
    print("\n" + "=" * 80)
    print("Test 012: 特定 vs 宽泛异常")
    print("=" * 80)

    result = ExceptionHandlingTestHelper.test_specific_vs_broad_exception()
    assert result, "Specific vs broad exception test failed"
    print("✅ Test 012 PASSED: 特定 vs 宽泛异常正确")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("异常处理防护测试套件 (P0 Issue #5)")
    print("=" * 80)

    tests = [
        test_001_exception_hierarchy,
        test_002_exception_raising,
        test_003_data_error_handler,
        test_004_model_error_handler,
        test_005_file_error_handler,
        test_006_safe_execute_success,
        test_007_safe_execute_with_exception,
        test_008_safe_execute_security_error,
        test_009_secure_handler_decorator,
        test_010_import_error_handling,
        test_011_multiple_exception_types,
        test_012_specific_vs_broad_exception,
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
        print("\n✅ 所有异常处理防护测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
