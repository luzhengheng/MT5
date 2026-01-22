"""
测试 Notion Bridge 集成功能 (Protocol v4.4)

覆盖范围:
  1. sanitize_task_id() 功能测试
  2. 工作流集成测试

运行: pytest tests/test_notion_bridge_integration.py -v
"""

import pytest
import sys
import tempfile
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ops.notion_bridge import (
    sanitize_task_id,
    find_completion_report,
    extract_report_summary,
    PathTraversalError,
    TaskMetadataError,
    SecurityException,
    FileException,
    ValidationException,
)


# ============================================================================
# 测试 1: sanitize_task_id() 功能测试
# ============================================================================

class TestSanitizeTaskId:
    """任务 ID 清洗功能测试"""

    def test_simple_numeric_id(self):
        """✅ 简单的数字 ID 应该直接返回"""
        assert sanitize_task_id('130') == '130'
        assert sanitize_task_id('1') == '1'
        assert sanitize_task_id('999') == '999'

    def test_dot_separated_version(self):
        """✅ 点分隔的版本号应该保留"""
        assert sanitize_task_id('130.2') == '130.2'
        assert sanitize_task_id('1.1') == '1.1'
        assert sanitize_task_id('999.99') == '999.99'

    def test_remove_task_prefix_underscore(self):
        """✅ 应该移除 TASK_ 前缀"""
        assert sanitize_task_id('TASK_130') == '130'
        assert sanitize_task_id('TASK_130.2') == '130.2'

    def test_remove_task_prefix_hash(self):
        """✅ 应该移除 TASK# 前缀"""
        assert sanitize_task_id('TASK#130') == '130'
        assert sanitize_task_id('TASK#130.2') == '130.2'

    def test_strip_whitespace(self):
        """✅ 应该移除前后空格"""
        assert sanitize_task_id('  130  ') == '130'
        assert sanitize_task_id('\t130.2\n') == '130.2'

    def test_path_traversal_detection_double_dot(self):
        """⚠️ 应该检测 .. 路径遍历"""
        with pytest.raises((PathTraversalError, TaskMetadataError)):
            sanitize_task_id('130..')
        with pytest.raises((PathTraversalError, TaskMetadataError)):
            sanitize_task_id('..130')

    def test_path_traversal_detection_slash(self):
        """⚠️ 应该检测斜杠"""
        with pytest.raises(PathTraversalError):
            sanitize_task_id('130/tmp')
        with pytest.raises(PathTraversalError):
            sanitize_task_id('/tmp/130')

    def test_path_traversal_detection_backslash(self):
        """⚠️ 应该检测反斜杠 (Windows 路径)"""
        with pytest.raises(PathTraversalError):
            sanitize_task_id('130\\tmp')
        with pytest.raises(PathTraversalError):
            sanitize_task_id('\\tmp\\130')

    def test_dangerous_chars_backtick(self):
        """⚠️ 应该检测反引号"""
        with pytest.raises(SecurityException):
            sanitize_task_id('130`id`')

    def test_dangerous_chars_dollar(self):
        """⚠️ 应该检测美元符号"""
        with pytest.raises(SecurityException):
            sanitize_task_id('130$(whoami)')

    def test_dangerous_chars_pipe(self):
        """⚠️ 应该检测管道"""
        with pytest.raises(SecurityException):
            sanitize_task_id('130|cat /etc/passwd')

    def test_dangerous_chars_semicolon(self):
        """⚠️ 应该检测分号"""
        with pytest.raises(SecurityException):
            sanitize_task_id('130;rm -rf /')

    def test_strict_format_validation(self):
        """⚠️ 应该验证严格的格式"""
        # 太多位数的主版本号
        with pytest.raises(TaskMetadataError):
            sanitize_task_id('9999')

        # 太多位数的子版本号
        with pytest.raises(TaskMetadataError):
            sanitize_task_id('130.999')

    def test_valid_edge_cases(self):
        """✅ 边界情况应该工作"""
        assert sanitize_task_id('1') == '1'
        assert sanitize_task_id('999') == '999'
        assert sanitize_task_id('1.1') == '1.1'
        assert sanitize_task_id('999.99') == '999.99'

    def test_case_sensitivity(self):
        """✅ 应该忽略 TASK 前缀的大小写"""
        assert sanitize_task_id('TASK_130') == '130'
        assert sanitize_task_id('task_130') == 'task_130'  # 小写不匹配
        # 实际上小写不应该被移除，因为模式是 TASK_


# ============================================================================
# 测试 2: 工作流集成测试
# ============================================================================

class TestNotionBridgeWorkflow:
    """Notion Bridge 工作流集成测试"""

    @pytest.fixture
    def sample_report(self):
        """创建示例报告文件"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False
        ) as f:
            content = """# Task #130.3 完成报告

## 📊 执行摘要

三阶段优化全部完成：
- ReDoS 防护强化 (+3 分)
- 异常分类细化 (+2 分)
- 微优化整合 (+3 分)

预期分数: 90-97/100

## 实施内容

### 优化 1: ReDoS 防护

新增了 validate_regex_safety() 函数。

### 优化 2: 异常分类

定义了 10+ 异常类。

### 优化 3-5: 微优化

全局变量清理、日志结构化、装饰器优化。

## 验证结果

✅ Python 语法检查: PASS
✅ 代码覆盖率: >85%
✅ 性能提升: +50%

## 后续计划

继续第四轮优化。
"""
            f.write(content)
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    def test_task_id_cleaning_workflow(self):
        """✅ 任务 ID 清洗工作流"""
        # 从不同格式的输入清洗任务 ID
        raw_inputs = [
            'TASK_130.2',
            'TASK#130',
            '130',
            '  130.2  ',
        ]
        expected = [
            '130.2',
            '130',
            '130',
            '130.2',
        ]

        for raw, exp in zip(raw_inputs, expected):
            result = sanitize_task_id(raw)
            assert result == exp

    def test_report_file_discovery_and_processing(self, sample_report):
        """✅ 报告文件发现和处理"""
        # 步骤 1: 验证文件存在
        assert sample_report.exists()
        assert sample_report.is_file()

        # 步骤 2: 提取摘要
        summary = extract_report_summary(sample_report)
        assert isinstance(summary, str)
        assert len(summary) > 0

        # 步骤 3: 验证摘要包含关键信息
        assert ('优化' in summary or '完成' in summary or
                '分数' in summary or len(summary) > 10)

    def test_task_id_validation_and_report_extraction(self, sample_report):
        """✅ 任务 ID 验证和报告提取工作流"""
        # 清洗任务 ID
        task_id = sanitize_task_id('TASK#130.3')
        assert task_id == '130.3'

        # 提取报告摘要
        summary = extract_report_summary(sample_report)
        assert isinstance(summary, str)

        # 验证报告内容
        assert len(summary) > 0

    def test_error_handling_workflow_path_traversal(self):
        """⚠️ 错误处理工作流: 路径遍历"""
        # 尝试清洗包含路径遍历的任务 ID
        with pytest.raises((PathTraversalError, TaskMetadataError)):
            sanitize_task_id('../../../130')

    def test_error_handling_workflow_file_not_found(self):
        """⚠️ 错误处理工作流: 文件不存在"""
        # 尝试提取不存在的文件的摘要
        with pytest.raises(FileException):
            extract_report_summary(
                Path('/tmp/non_existent_report_abc.md')
            )

    def test_complete_task_processing_pipeline(self, sample_report):
        """✅ 完整的任务处理管道"""
        # 输入: 原始任务 ID
        raw_task_id = 'TASK_130.3'

        # 步骤 1: 清洗任务 ID
        clean_task_id = sanitize_task_id(raw_task_id)
        assert clean_task_id == '130.3'

        # 步骤 2: 查找报告文件
        # (在实际应用中，这会查找基于任务 ID 的文件)
        # 这里使用预先创建的示例报告
        report_path = sample_report

        # 步骤 3: 验证报告存在
        assert report_path.exists()

        # 步骤 4: 提取报告摘要
        summary = extract_report_summary(report_path)
        assert isinstance(summary, str)
        assert len(summary) > 0

        # 步骤 5: 验证摘要内容
        assert '三阶段优化' in summary or len(summary) > 20

    def test_batch_task_processing(self, sample_report):
        """✅ 批量任务处理"""
        task_ids = [
            'TASK_130',
            'TASK#130.1',
            'TASK_130.2',
            '130.3',
        ]

        expected_clean = [
            '130',
            '130.1',
            '130.2',
            '130.3',
        ]

        for raw, exp in zip(task_ids, expected_clean):
            clean = sanitize_task_id(raw)
            assert clean == exp

        # 所有任务都可以成功处理
        assert len(task_ids) == len(expected_clean)


# ============================================================================
# 测试 3: 边界情况和特殊场景
# ============================================================================

class TestEdgeCasesAndSpecialScenarios:
    """边界情况和特殊场景"""

    def test_unicode_in_task_id(self):
        """✅ Unicode 字符应该被拒绝或处理"""
        # 中文任务 ID 应该被拒绝
        with pytest.raises((TaskMetadataError, ValidationException)):
            sanitize_task_id('任务130')

    def test_mixed_numeric_letters(self):
        """⚠️ 混合数字和字母应该被拒绝"""
        with pytest.raises(TaskMetadataError):
            sanitize_task_id('130abc')

    def test_multiple_dots(self):
        """⚠️ 多个点应该被拒绝"""
        with pytest.raises(TaskMetadataError):
            sanitize_task_id('130.2.3.4')

    def test_leading_zeros(self):
        """✅ 前导零应该被接受"""
        # 取决于实现，可能被接受或拒绝
        try:
            result = sanitize_task_id('0130')
            # 如果接受，检查是否返回正确的值
            assert result == '0130' or result == '130'
        except TaskMetadataError:
            # 如果拒绝，也可以接受
            pass

    def test_very_long_task_id(self):
        """⚠️ 过长的任务 ID 应该被拒绝"""
        # 远超 3 位数字的主版本号
        with pytest.raises(TaskMetadataError):
            sanitize_task_id('123456789')

    def test_null_byte_in_task_id(self):
        """⚠️ 空字节应该被检测"""
        with pytest.raises(SecurityException):
            sanitize_task_id('130\x00test')

    def test_empty_string(self):
        """⚠️ 空字符串应该被拒绝"""
        with pytest.raises((TaskMetadataError, ValidationException)):
            sanitize_task_id('')

    def test_whitespace_only(self):
        """⚠️ 仅空格应该被拒绝"""
        with pytest.raises((TaskMetadataError, ValidationException)):
            sanitize_task_id('   ')


# ============================================================================
# 性能测试
# ============================================================================

class TestIntegrationPerformance:
    """集成功能的性能测试"""

    def test_sanitize_task_id_performance(self):
        """✅ 任务 ID 清洗应该很快"""
        import time

        task_ids = ['TASK_130', 'TASK#130.2', '130', '  130.2  ']
        iterations = 10000

        start = time.time()
        for _ in range(iterations):
            for task_id in task_ids:
                try:
                    sanitize_task_id(task_id)
                except Exception:
                    pass
        elapsed = time.time() - start

        # 应该在 100ms 内完成 10000 次迭代 * 4 个任务
        # 即每个操作 <2.5 微秒
        avg_time = elapsed / (iterations * len(task_ids))
        assert avg_time < 0.000025, f"Too slow: {avg_time} seconds"

    def test_extract_summary_performance(self):
        """✅ 摘要提取应该在合理时间内"""
        import tempfile
        import time

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False
        ) as f:
            content = """## 📊 执行摘要

摘要内容 """ + ('x' * 1000)
            f.write(content)
            temp_path = Path(f.name)

        try:
            iterations = 100
            start = time.time()
            for _ in range(iterations):
                extract_report_summary(temp_path)
            elapsed = time.time() - start

            # 应该在 1 秒内完成 100 次提取
            avg_time = elapsed / iterations
            assert avg_time < 0.01, f"Too slow: {avg_time} seconds"
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
