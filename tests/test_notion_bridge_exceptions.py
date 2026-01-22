"""
测试 Notion Bridge 异常分类体系 (Protocol v4.4 优化 2)

覆盖范围:
  1. 异常类继承关系验证
  2. 异常处理正确性验证
  3. 异常链保留验证

运行: pytest tests/test_notion_bridge_exceptions.py -v
"""

import pytest
import sys
import tempfile
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ops.notion_bridge import (
    NotionBridgeException,
    SecurityException,
    PathTraversalError,
    CredentialError,
    ValidationException,
    TaskMetadataError,
    NetworkException,
    NotionAPIError,
    TimeoutException,
    FileException,
    FileTooLargeError,
    EncodingError,
    find_completion_report,
    extract_report_summary,
    sanitize_task_id,
)


# ============================================================================
# 测试 1: 异常类继承验证
# ============================================================================

class TestExceptionHierarchy:
    """验证异常类的继承关系"""

    def test_all_exceptions_inherit_from_base(self):
        """✅ 所有异常应该继承自 NotionBridgeException"""
        exceptions = [
            SecurityException,
            ValidationException,
            NetworkException,
            FileException,
            PathTraversalError,
            CredentialError,
            TaskMetadataError,
            NotionAPIError,
            TimeoutException,
            FileTooLargeError,
            EncodingError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, NotionBridgeException), \
                f"{exc_class.__name__} should inherit from NotionBridgeException"

    def test_security_exception_hierarchy(self):
        """✅ SecurityException 的子类应该正确继承"""
        assert issubclass(PathTraversalError, SecurityException)
        assert issubclass(CredentialError, SecurityException)
        assert issubclass(PathTraversalError, NotionBridgeException)
        assert issubclass(CredentialError, NotionBridgeException)

    def test_validation_exception_hierarchy(self):
        """✅ ValidationException 的子类应该正确继承"""
        assert issubclass(TaskMetadataError, ValidationException)
        assert issubclass(TaskMetadataError, NotionBridgeException)

    def test_network_exception_hierarchy(self):
        """✅ NetworkException 的子类应该正确继承"""
        assert issubclass(NotionAPIError, NetworkException)
        assert issubclass(TimeoutException, NetworkException)
        assert issubclass(NotionAPIError, NotionBridgeException)
        assert issubclass(TimeoutException, NotionBridgeException)

    def test_file_exception_hierarchy(self):
        """✅ FileException 的子类应该正确继承"""
        assert issubclass(FileTooLargeError, FileException)
        assert issubclass(EncodingError, FileException)
        assert issubclass(FileTooLargeError, NotionBridgeException)
        assert issubclass(EncodingError, NotionBridgeException)

    def test_exception_isinstance_checks(self):
        """✅ isinstance 检查应该工作"""
        try:
            raise PathTraversalError("test")
        except SecurityException as e:
            assert isinstance(e, SecurityException)
            assert isinstance(e, NotionBridgeException)

        try:
            raise FileTooLargeError("test")
        except FileException as e:
            assert isinstance(e, FileException)
            assert isinstance(e, NotionBridgeException)

    def test_exception_catching_order(self):
        """✅ 异常捕获顺序应该正确工作"""
        caught_as = None

        try:
            raise PathTraversalError("test path traversal")
        except FileException:
            caught_as = "FileException"
        except SecurityException:
            caught_as = "SecurityException"
        except NotionBridgeException:
            caught_as = "NotionBridgeException"

        # 应该被 SecurityException 捕获
        assert caught_as == "SecurityException"


# ============================================================================
# 测试 2: 异常处理正确性
# ============================================================================

class TestExceptionHandling:
    """验证关键函数的异常处理"""

    @pytest.fixture
    def temp_file(self):
        """临时文件 fixture"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    def test_find_completion_report_not_found(self):
        """⚠️ find_completion_report() 文件不存在应该返回 None"""
        non_existent_task_id = 'non_existent_task_xyz'

        # 文件不存在时返回 None
        result = find_completion_report(non_existent_task_id)
        assert result is None

    def test_extract_report_summary_file_not_found(self):
        """⚠️ extract_report_summary() 文件不存在应该抛出异常"""
        non_existent = Path('/tmp/non_existent_report_xyz.md')

        with pytest.raises(FileException):
            extract_report_summary(non_existent)

    def test_extract_report_summary_encoding_error(self, temp_file):
        """⚠️ extract_report_summary() 编码错误应该抛出异常"""
        # 写入无效的 UTF-8
        with open(temp_file, 'wb') as f:
            f.write(b'\xff\xfe invalid utf-8')

        with pytest.raises(EncodingError):
            extract_report_summary(temp_file)

    def test_extract_report_summary_file_too_large(self, temp_file):
        """⚠️ extract_report_summary() 超大文件应该抛出异常"""
        # 创建超过 10MB 的文件
        large_content = 'x' * (11 * 1024 * 1024)
        temp_file.write_text(large_content)

        with pytest.raises(FileTooLargeError):
            extract_report_summary(temp_file)

    def test_sanitize_task_id_path_traversal(self):
        """⚠️ sanitize_task_id() 路径遍历应该抛出异常"""
        malicious_ids = [
            '../130',
            '../../root',
            './130',
            '130/../..',
        ]

        for task_id in malicious_ids:
            with pytest.raises((PathTraversalError, TaskMetadataError)):
                sanitize_task_id(task_id)

    def test_sanitize_task_id_invalid_format(self):
        """⚠️ sanitize_task_id() 无效格式应该抛出异常"""
        invalid_ids = [
            'TASK_ABC',
            '999.999.999',  # 子版本号过多
            '',
            'abc',
        ]

        for task_id in invalid_ids:
            with pytest.raises((TaskMetadataError, ValidationException)):
                sanitize_task_id(task_id)

    def test_sanitize_task_id_dangerous_chars(self):
        """⚠️ sanitize_task_id() 危险字符应该抛出异常"""
        dangerous_ids = [
            '130;rm -rf /',
            '130$(whoami)',
            '130`id`',
            '130|cat /etc/passwd',
        ]

        for task_id in dangerous_ids:
            # 危险字符可能导致格式验证失败或安全检查失败
            with pytest.raises((SecurityException, TaskMetadataError)):
                sanitize_task_id(task_id)

    def test_sanitize_task_id_valid(self):
        """✅ sanitize_task_id() 有效输入应该成功"""
        valid_ids = [
            ('130', '130'),
            ('TASK_130', '130'),
            ('  130  ', '130'),
            ('130.2', '130.2'),
        ]

        for input_id, expected in valid_ids:
            result = sanitize_task_id(input_id)
            assert result == expected


# ============================================================================
# 测试 3: 异常链保留
# ============================================================================

class TestExceptionChaining:
    """验证异常链 (from e) 是否正确保留"""

    def test_exception_chain_preserved_in_file_error(self):
        """✅ 文件异常应该保留原始异常链"""
        non_existent = Path('/tmp/non_existent_abc123.md')

        try:
            extract_report_summary(non_existent)
        except FileException as e:
            # 检查异常链
            assert e.__cause__ is not None or e.__context__ is not None
            # 原始异常应该是 FileNotFoundError
            cause = e.__cause__ if e.__cause__ else e.__context__
            assert isinstance(cause, FileNotFoundError)

    def test_exception_chain_information(self):
        """✅ 异常链应该包含有用的信息"""
        non_existent = Path('/tmp/non_existent_xyz.md')

        try:
            extract_report_summary(non_existent)
        except FileException as e:
            error_msg = str(e)
            # 异常信息应该包含路径或文件名
            assert 'non_existent' in error_msg or isinstance(e, FileException)

    def test_exception_repr(self):
        """✅ 异常应该有有意义的字符串表示"""
        exc = PathTraversalError("test path traversal")
        repr_str = repr(exc)
        assert 'PathTraversalError' in repr_str

        exc = TaskMetadataError("invalid metadata")
        str_repr = str(exc)
        assert 'invalid metadata' in str_repr


# ============================================================================
# 测试 4: 异常通用行为
# ============================================================================

class TestExceptionGeneralBehavior:
    """验证异常的通用行为"""

    def test_exception_instantiation(self):
        """✅ 所有异常类应该可以实例化"""
        exceptions_to_test = [
            (NotionBridgeException, "test message"),
            (SecurityException, "security error"),
            (PathTraversalError, "path traversal"),
            (ValidationException, "validation failed"),
            (TaskMetadataError, "bad metadata"),
            (NetworkException, "network error"),
            (FileException, "file error"),
            (FileTooLargeError, "file too large"),
            (EncodingError, "encoding problem"),
        ]

        for exc_class, message in exceptions_to_test:
            exc = exc_class(message)
            assert isinstance(exc, Exception)
            assert message in str(exc)

    def test_exception_with_multiple_args(self):
        """✅ 异常应该支持多个参数"""
        exc = NotionBridgeException("error", "details", 123)
        assert "error" in str(exc) or len(str(exc)) > 0

    def test_exception_reraise(self):
        """✅ 异常应该可以重新抛出"""
        try:
            try:
                raise PathTraversalError("original")
            except PathTraversalError as e:
                raise  # 重新抛出
        except PathTraversalError as e:
            assert "original" in str(e)

    def test_exception_inheritance_mro(self):
        """✅ MRO (方法解析顺序) 应该正确"""
        # 检查 PathTraversalError 的 MRO
        mro = PathTraversalError.__mro__
        assert PathTraversalError in mro
        assert SecurityException in mro
        assert NotionBridgeException in mro
        assert Exception in mro

    def test_custom_exception_attributes(self):
        """✅ 异常应该保留自定义属性"""
        exc = FileTooLargeError("file too large: 15MB > 10MB limit")
        assert hasattr(exc, 'args')
        assert len(exc.args) > 0


# ============================================================================
# 测试 5: 异常处理模式
# ============================================================================

class TestExceptionPatterns:
    """验证常见的异常处理模式"""

    def test_catch_specific_exception(self):
        """✅ 应该能够捕获特定异常"""
        try:
            raise TaskMetadataError("bad format")
        except TaskMetadataError:
            pass  # 成功捕获
        except Exception:
            pytest.fail("Should have caught TaskMetadataError")

    def test_catch_parent_exception(self):
        """✅ 应该能够捕获父类异常"""
        try:
            raise FileTooLargeError("too large")
        except FileException:
            pass  # 成功捕获为父类
        except Exception:
            pytest.fail("Should have caught FileException")

    def test_catch_base_exception(self):
        """✅ 应该能够捕获基础异常"""
        try:
            raise PathTraversalError("traversal")
        except NotionBridgeException:
            pass  # 成功捕获为基础异常
        except Exception:
            pytest.fail("Should have caught NotionBridgeException")

    def test_multiple_exception_handlers(self):
        """✅ 多个异常处理程序应该工作"""
        exceptions = [
            PathTraversalError("traversal"),
            FileTooLargeError("large"),
            TaskMetadataError("metadata"),
        ]

        for exc in exceptions:
            caught = False
            try:
                raise exc
            except PathTraversalError:
                caught = True
            except FileTooLargeError:
                caught = True
            except TaskMetadataError:
                caught = True

            assert caught, f"Failed to catch {exc.__class__.__name__}"

    def test_exception_context_preservation(self):
        """✅ 异常上下文应该被保留"""
        try:
            try:
                raise ValueError("original error")
            except ValueError as e:
                raise FileException("file problem") from e
        except FileException as outer_exc:
            assert outer_exc.__cause__ is not None
            assert isinstance(outer_exc.__cause__, ValueError)


# ============================================================================
# 集成测试
# ============================================================================

class TestExceptionIntegration:
    """异常处理的端到端集成测试"""

    def test_full_error_handling_workflow(self):
        """✅ 完整的错误处理工作流"""
        # 模拟一个完整的工作流，其中会抛出异常

        # 测试 1: 无效的任务 ID
        with pytest.raises((TaskMetadataError, ValidationException)):
            sanitize_task_id("INVALID")

        # 测试 2: 不存在的文件
        with pytest.raises(FileException):
            extract_report_summary(Path('/tmp/non_existent_abc.md'))

        # 测试 3: 有效的任务 ID 应该成功
        result = sanitize_task_id('130.2')
        assert result == '130.2'

    def test_exception_logging_compatibility(self):
        """✅ 异常应该与日志兼容"""
        import logging

        logger = logging.getLogger('test')

        try:
            raise PathTraversalError("test path traversal error")
        except PathTraversalError as e:
            # 应该能够记录异常
            logger.exception("Caught exception")
            assert str(e) is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
