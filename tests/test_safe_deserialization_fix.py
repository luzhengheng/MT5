#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite: Safe Deserialization Prevention (P0 Issue #3)
===========================================================

验证不安全反序列化防护措施。

Issue: CWE-502 (Deserialization of Untrusted Data)
     直接加载文件而不验证可能导致：
     1. 文件被篡改
     2. 数据完整性丧失
     3. 代码执行（某些情况）
     4. DoS 攻击（超大文件）

Fix: 实现 SafeDataLoader 类来：
     1. 验证文件大小（防止 DoS）
     2. 验证校验和（防止篡改）
     3. 验证文件格式
     4. 验证权限

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import json
import tempfile
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ai_governance.safe_data_loader import (
    SafeDataLoader,
    SafeDataLoadError,
    FileTooLargeError,
    ChecksumMismatchError,
    InvalidDataFormatError,
)


class SafeDeserializationTestHelper:
    """安全反序列化防护测试助手"""

    @staticmethod
    def test_file_size_validation():
        """测试文件大小验证"""
        loader = SafeDataLoader()

        # 测试有效大小
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建有效大小的文件
            valid_file = Path(tmpdir) / "valid.json"
            valid_file.write_text('{"data": "test"}')

            file_size = loader.validate_file_size(valid_file)
            assert file_size > 0, "File size should be positive"

        # 测试空文件
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_file = Path(tmpdir) / "empty.json"
            empty_file.write_text("")

            try:
                loader.validate_file_size(empty_file)
                assert False, "Should have raised SafeDataLoadError"
            except SafeDataLoadError:
                pass  # Expected

        return True

    @staticmethod
    def test_file_format_validation():
        """测试文件格式验证"""
        loader = SafeDataLoader()

        # 测试有效格式
        json_file = Path("/tmp/test.json")
        assert loader.validate_file_format(json_file) == "json"

        parquet_file = Path("/tmp/test.parquet")
        assert loader.validate_file_format(parquet_file) == "parquet"

        csv_file = Path("/tmp/test.csv")
        assert loader.validate_file_format(csv_file) == "csv"

        # 测试无效格式
        invalid_file = Path("/tmp/test.xyz")
        try:
            loader.validate_file_format(invalid_file)
            assert False, "Should have raised InvalidDataFormatError"
        except InvalidDataFormatError:
            pass  # Expected

        return True

    @staticmethod
    def test_checksum_calculation():
        """测试校验和计算"""
        loader = SafeDataLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_data = '{"key": "value"}'
            test_file.write_text(test_data)

            # 计算校验和
            checksum1 = loader.validate_checksum(test_file)
            assert len(checksum1) == 64, "SHA256 should be 64 hex chars"

            # 再次计算应该相同
            checksum2 = loader.validate_checksum(test_file)
            assert checksum1 == checksum2, "Checksums should match"

            # 修改文件后校验和应该不同
            test_file.write_text('{"key": "different"}')
            checksum3 = loader.validate_checksum(test_file)
            assert checksum1 != checksum3, "Checksums should differ"

        return True

    @staticmethod
    def test_checksum_mismatch_detection():
        """测试校验和不匹配检测"""
        loader = SafeDataLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_file.write_text('{"data": "test"}')

            # 验证正确的校验和
            correct_checksum = loader.validate_checksum(test_file)

            # 验证错误的校验和应该抛出异常
            wrong_checksum = "0" * 64

            try:
                loader.validate_checksum(test_file, wrong_checksum)
                assert False, "Should have raised ChecksumMismatchError"
            except ChecksumMismatchError:
                pass  # Expected

        return True

    @staticmethod
    def test_json_structure_validation():
        """测试 JSON 结构验证"""
        loader = SafeDataLoader()

        # 测试有效的 JSON 对象
        valid_dict = {"key": "value", "nested": {"data": 123}}
        assert loader.validate_json_structure(valid_dict)

        # 测试有效的 JSON 数组
        valid_list = [1, 2, 3, {"nested": "value"}]
        assert loader.validate_json_structure(valid_list)

        # 测试必需键检查
        data = {"key1": "value1", "key2": "value2"}
        required_keys = {"key1", "key2"}
        assert loader.validate_json_structure(data, required_keys)

        # 测试缺少必需键
        try:
            required_keys = {"key1", "missing_key"}
            loader.validate_json_structure(data, required_keys)
            assert False, "Should have raised InvalidDataFormatError"
        except InvalidDataFormatError:
            pass  # Expected

        return True

    @staticmethod
    def test_json_safe_loading():
        """测试安全 JSON 加载"""
        loader = SafeDataLoader(strict_mode=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_data = {"key": "value", "number": 42}
            test_file.write_text(json.dumps(test_data))

            # 安全加载
            loaded_data = loader.load_json_safe(test_file)
            assert loaded_data == test_data, "Loaded data should match"

        return True

    @staticmethod
    def test_permissions_validation():
        """测试权限验证"""
        loader = SafeDataLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            readable_file = Path(tmpdir) / "readable.json"
            readable_file.write_text('{}')

            # 验证读权限
            assert loader.validate_permissions(readable_file)

            # 测试无权限的文件 (如果可能)
            # 注意：这在某些系统上可能不可行

        return True

    @staticmethod
    def test_integration_safe_loading():
        """测试完整的安全加载集成"""
        loader = SafeDataLoader(strict_mode=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 JSON 文件
            test_file = Path(tmpdir) / "data.json"
            test_data = {
                "features": [1.0, 2.0, 3.0],
                "labels": [0, 1, 0],
                "metadata": {"version": "1.0"}
            }
            test_file.write_text(json.dumps(test_data))

            # 安全加载
            loaded_data = loader.load_json_safe(test_file)
            assert loaded_data["features"] == test_data["features"]
            assert loaded_data["metadata"]["version"] == "1.0"

            # 验证报告
            report = loader.get_validation_report()
            assert isinstance(report, str)
            assert len(report) > 0

        return True

    @staticmethod
    def test_loader_metadata_tracking():
        """测试加载器元数据跟踪"""
        loader = SafeDataLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_file.write_text('{"data": "test"}')

            loaded_data = loader.load_json_safe(test_file)
            assert str(test_file) in loader.loaded_files
            assert "metadata" in loader.loaded_files[str(test_file)]
            assert "data" in loader.loaded_files[str(test_file)]

        return True


def test_001_file_size_validation():
    """Test 001: 文件大小验证"""
    print("\n" + "=" * 80)
    print("Test 001: 文件大小验证")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_file_size_validation()
    assert result, "File size validation test failed"
    print("✅ Test 001 PASSED: 文件大小验证正确")


def test_002_file_format_validation():
    """Test 002: 文件格式验证"""
    print("\n" + "=" * 80)
    print("Test 002: 文件格式验证")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_file_format_validation()
    assert result, "File format validation test failed"
    print("✅ Test 002 PASSED: 文件格式验证正确")


def test_003_checksum_calculation():
    """Test 003: 校验和计算"""
    print("\n" + "=" * 80)
    print("Test 003: 校验和计算")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_checksum_calculation()
    assert result, "Checksum calculation test failed"
    print("✅ Test 003 PASSED: 校验和计算正确")


def test_004_checksum_mismatch():
    """Test 004: 校验和不匹配检测"""
    print("\n" + "=" * 80)
    print("Test 004: 校验和不匹配检测")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_checksum_mismatch_detection()
    assert result, "Checksum mismatch detection test failed"
    print("✅ Test 004 PASSED: 校验和不匹配检测正确")


def test_005_json_structure_validation():
    """Test 005: JSON 结构验证"""
    print("\n" + "=" * 80)
    print("Test 005: JSON 结构验证")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_json_structure_validation()
    assert result, "JSON structure validation test failed"
    print("✅ Test 005 PASSED: JSON 结构验证正确")


def test_006_json_safe_loading():
    """Test 006: 安全 JSON 加载"""
    print("\n" + "=" * 80)
    print("Test 006: 安全 JSON 加载")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_json_safe_loading()
    assert result, "Safe JSON loading test failed"
    print("✅ Test 006 PASSED: 安全 JSON 加载正确")


def test_007_permissions_validation():
    """Test 007: 权限验证"""
    print("\n" + "=" * 80)
    print("Test 007: 权限验证")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_permissions_validation()
    assert result, "Permissions validation test failed"
    print("✅ Test 007 PASSED: 权限验证正确")


def test_008_integration_safe_loading():
    """Test 008: 完整集成测试"""
    print("\n" + "=" * 80)
    print("Test 008: 完整集成测试")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_integration_safe_loading()
    assert result, "Integration safe loading test failed"
    print("✅ Test 008 PASSED: 完整集成测试通过")


def test_009_metadata_tracking():
    """Test 009: 元数据跟踪"""
    print("\n" + "=" * 80)
    print("Test 009: 元数据跟踪")
    print("=" * 80)

    result = SafeDeserializationTestHelper.test_loader_metadata_tracking()
    assert result, "Metadata tracking test failed"
    print("✅ Test 009 PASSED: 元数据跟踪正确")


def test_010_validation_report():
    """Test 010: 验证报告生成"""
    print("\n" + "=" * 80)
    print("Test 010: 验证报告生成")
    print("=" * 80)

    loader = SafeDataLoader()
    report = loader.get_validation_report()

    assert isinstance(report, str), "Report should be a string"
    assert len(report) > 0, "Report should not be empty"

    print("✅ Test 010 PASSED: 验证报告生成正确")


def test_011_loader_instantiation():
    """Test 011: 加载器实例化"""
    print("\n" + "=" * 80)
    print("Test 011: 加载器实例化")
    print("=" * 80)

    # 严格模式
    strict_loader = SafeDataLoader(strict_mode=True)
    assert strict_loader.strict_mode is True

    # 非严格模式
    lenient_loader = SafeDataLoader(strict_mode=False)
    assert lenient_loader.strict_mode is False

    print("✅ Test 011 PASSED: 加载器实例化正确")


def test_012_error_handling():
    """Test 012: 错误处理"""
    print("\n" + "=" * 80)
    print("Test 012: 错误处理")
    print("=" * 80)

    loader = SafeDataLoader(strict_mode=False)

    # 测试不存在的文件
    try:
        loader.validate_file_size(Path("/nonexistent/file.json"))
        assert False, "Should raise SafeDataLoadError"
    except SafeDataLoadError:
        pass  # Expected

    print("✅ Test 012 PASSED: 错误处理正确")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("安全反序列化防护测试套件 (P0 Issue #3)")
    print("=" * 80)

    tests = [
        test_001_file_size_validation,
        test_002_file_format_validation,
        test_003_checksum_calculation,
        test_004_checksum_mismatch,
        test_005_json_structure_validation,
        test_006_json_safe_loading,
        test_007_permissions_validation,
        test_008_integration_safe_loading,
        test_009_metadata_tracking,
        test_010_validation_report,
        test_011_loader_instantiation,
        test_012_error_handling,
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
        print("\n✅ 所有安全反序列化防护测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
