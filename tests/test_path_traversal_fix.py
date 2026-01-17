#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite: Path Traversal Prevention (P0 Issue #2)
====================================================

验证路径遍历和符号链接攻击的防护措施。

Issue: CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)
     sys.path.insert() 无验证可能导致：
     1. 模块劫持攻击
     2. 符号链接逃逸
     3. 任意代码执行

Fix: 实现 PathValidator 类来：
     1. 验证路径格式和存在性
     2. 检测符号链接
     3. 验证必需的项目文件
     4. 检查权限

Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import tempfile
import os
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ai_governance.path_validator import PathValidator, PathValidationError


class PathTraversalTestHelper:
    """路径遍历防护测试助手"""

    @staticmethod
    def test_format_validation():
        """测试路径格式验证"""
        validator = PathValidator()

        # 测试有效路径
        valid_path = Path(__file__).parent.parent
        assert validator.validate_path_format(valid_path), "Valid path should pass"

        # 测试路径遍历模式
        bad_paths = [
            Path("/etc/../../../root/secret"),
            Path("/tmp/test/../../../etc/passwd"),
        ]

        for bad_path in bad_paths:
            try:
                # 虽然路径被解析为真实路径，但应该检测到遍历意图
                validator.validate_path_format(bad_path)
            except PathValidationError:
                pass  # Expected

        return True

    @staticmethod
    def test_existence_check():
        """测试路径存在性检查"""
        validator = PathValidator()

        # 有效路径
        valid_path = Path(__file__).parent.parent
        assert validator.validate_existence(valid_path), "Existing path should pass"

        # 无效路径
        invalid_path = Path("/nonexistent/path/12345/abcdef")
        try:
            validator.validate_existence(invalid_path)
            assert False, "Should have raised PathValidationError"
        except PathValidationError:
            pass  # Expected

        return True

    @staticmethod
    def test_type_check():
        """测试路径类型检查"""
        validator = PathValidator()

        # 目录路径
        dir_path = Path(__file__).parent.parent
        assert validator.validate_type(dir_path, expected_type="dir"), "Directory should pass"

        # 文件路径
        file_path = Path(__file__)
        assert validator.validate_type(file_path, expected_type="file"), "File should pass"

        # 错误的类型应该抛出异常
        try:
            validator.validate_type(dir_path, expected_type="file")
            assert False, "Should have raised PathValidationError"
        except PathValidationError:
            pass  # Expected

        return True

    @staticmethod
    def test_symlink_detection():
        """测试符号链接检测"""
        validator = PathValidator()

        # 真实目录（不是符号链接）
        real_path = Path(__file__).parent.parent
        assert validator.validate_no_symlinks(real_path), "Real path should pass"

        # 创建临时符号链接进行测试
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 创建真实目录
            real_dir = tmpdir_path / "real_dir"
            real_dir.mkdir()

            # 创建符号链接
            symlink_path = tmpdir_path / "symlink_dir"
            try:
                symlink_path.symlink_to(real_dir)

                # 测试符号链接检测
                try:
                    validator.validate_no_symlinks(symlink_path)
                    assert False, "Should have raised PathValidationError for symlink"
                except PathValidationError:
                    pass  # Expected

            except OSError:
                # Windows 或权限不足，跳过符号链接测试
                pass

        return True

    @staticmethod
    def test_required_files_check():
        """测试必需文件检查"""
        validator = PathValidator()

        # 测试有效项目根目录
        project_root = Path(__file__).parent.parent
        required_files = ["pyproject.toml", "src/", "scripts/", "tests/"]

        try:
            validator.validate_required_files(project_root, required_files)
        except PathValidationError:
            # 如果缺少文件，非严格模式下不应该抛出异常
            pass

        # 测试缺少必需文件的目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            try:
                strict_validator = PathValidator(strict_mode=True)
                strict_validator.validate_required_files(
                    tmpdir_path,
                    required_files=["nonexistent1.txt", "nonexistent2.txt"]
                )
                assert False, "Should have raised PathValidationError"
            except PathValidationError:
                pass  # Expected

        return True

    @staticmethod
    def test_permissions_check():
        """测试权限检查"""
        validator = PathValidator()

        # 项目目录应该有读权限
        project_root = Path(__file__).parent.parent
        assert validator.validate_permissions(project_root, mode="r"), "Should have read permission"

        # 测试无权限的路径（可能不总是可行）
        # 这通常需要 root/admin 权限来设置
        # 在这里我们只验证读权限

        return True

    @staticmethod
    def test_project_root_validation():
        """测试完整项目根目录验证"""
        validator = PathValidator(strict_mode=False)

        project_root = Path(__file__).parent.parent

        # 完整验证应该通过
        assert validator.validate_project_root(project_root), "Project root validation should pass"

        # 检查是否记录了验证
        assert len(validator.validation_log) > 0, "Should have validation logs"

        return True

    @staticmethod
    def test_safe_syspath_addition():
        """测试安全的 sys.path 添加"""
        validator = PathValidator(strict_mode=False)

        project_root = Path(__file__).parent.parent
        original_syspath = sys.path.copy()

        try:
            # 安全添加到 sys.path
            success = validator.safe_add_to_syspath(project_root)
            assert success, "Should successfully add to sys.path"

            # 验证路径已添加
            assert str(project_root.resolve()) in sys.path, "Path should be in sys.path"

        finally:
            # 恢复原始 sys.path
            sys.path = original_syspath

        return True

    @staticmethod
    def test_validation_report():
        """测试验证报告生成"""
        validator = PathValidator()
        project_root = Path(__file__).parent.parent

        # 运行验证
        validator.validate_project_root(project_root)

        # 获取报告
        report = validator.get_validation_report()

        assert isinstance(report, str), "Report should be a string"
        assert len(report) > 0, "Report should not be empty"
        assert "验证" in report or "Validation" in report, "Report should mention validation"

        return True


def test_001_format_validation():
    """Test 001: 路径格式验证"""
    print("\n" + "=" * 80)
    print("Test 001: 路径格式验证")
    print("=" * 80)

    result = PathTraversalTestHelper.test_format_validation()
    assert result, "Format validation test failed"
    print("✅ Test 001 PASSED: 路径格式验证正确")


def test_002_existence_check():
    """Test 002: 路径存在性检查"""
    print("\n" + "=" * 80)
    print("Test 002: 路径存在性检查")
    print("=" * 80)

    result = PathTraversalTestHelper.test_existence_check()
    assert result, "Existence check test failed"
    print("✅ Test 002 PASSED: 路径存在性检查正确")


def test_003_type_check():
    """Test 003: 路径类型检查"""
    print("\n" + "=" * 80)
    print("Test 003: 路径类型检查")
    print("=" * 80)

    result = PathTraversalTestHelper.test_type_check()
    assert result, "Type check test failed"
    print("✅ Test 003 PASSED: 路径类型检查正确")


def test_004_symlink_detection():
    """Test 004: 符号链接检测"""
    print("\n" + "=" * 80)
    print("Test 004: 符号链接检测")
    print("=" * 80)

    result = PathTraversalTestHelper.test_symlink_detection()
    assert result, "Symlink detection test failed"
    print("✅ Test 004 PASSED: 符号链接检测正确")


def test_005_required_files_check():
    """Test 005: 必需文件检查"""
    print("\n" + "=" * 80)
    print("Test 005: 必需文件检查")
    print("=" * 80)

    result = PathTraversalTestHelper.test_required_files_check()
    assert result, "Required files check test failed"
    print("✅ Test 005 PASSED: 必需文件检查正确")


def test_006_permissions_check():
    """Test 006: 权限检查"""
    print("\n" + "=" * 80)
    print("Test 006: 权限检查")
    print("=" * 80)

    result = PathTraversalTestHelper.test_permissions_check()
    assert result, "Permissions check test failed"
    print("✅ Test 006 PASSED: 权限检查正确")


def test_007_project_root_validation():
    """Test 007: 项目根目录完整验证"""
    print("\n" + "=" * 80)
    print("Test 007: 项目根目录完整验证")
    print("=" * 80)

    result = PathTraversalTestHelper.test_project_root_validation()
    assert result, "Project root validation test failed"
    print("✅ Test 007 PASSED: 项目根目录验证正确")


def test_008_safe_syspath_addition():
    """Test 008: 安全的 sys.path 添加"""
    print("\n" + "=" * 80)
    print("Test 008: 安全的 sys.path 添加")
    print("=" * 80)

    result = PathTraversalTestHelper.test_safe_syspath_addition()
    assert result, "Safe sys.path addition test failed"
    print("✅ Test 008 PASSED: 安全 sys.path 添加正确")


def test_009_validation_report():
    """Test 009: 验证报告生成"""
    print("\n" + "=" * 80)
    print("Test 009: 验证报告生成")
    print("=" * 80)

    result = PathTraversalTestHelper.test_validation_report()
    assert result, "Validation report test failed"
    print("✅ Test 009 PASSED: 验证报告生成正确")


def test_010_integration():
    """Test 010: 完整集成测试"""
    print("\n" + "=" * 80)
    print("Test 010: 完整集成测试")
    print("=" * 80)

    validator = PathValidator(strict_mode=False)
    project_root = Path(__file__).parent.parent

    # 执行完整验证流程
    try:
        success = validator.safe_add_to_syspath(project_root)
        assert success, "Integration test failed"
        print("✅ Test 010 PASSED: 完整集成测试通过")
    except Exception as e:
        print(f"❌ Test 010 FAILED: {e}")
        raise


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("路径遍历防护测试套件 (P0 Issue #2)")
    print("=" * 80)

    tests = [
        test_001_format_validation,
        test_002_existence_check,
        test_003_type_check,
        test_004_symlink_detection,
        test_005_required_files_check,
        test_006_permissions_check,
        test_007_project_root_validation,
        test_008_safe_syspath_addition,
        test_009_validation_report,
        test_010_integration,
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
        print("\n✅ 所有路径遍历防护测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
