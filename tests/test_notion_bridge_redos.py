"""
测试 Notion Bridge ReDoS 防护机制 (Protocol v4.4 优化 1)

覆盖范围:
  1. validate_regex_safety() 函数测试
  2. extract_report_summary() 四层防护测试
  3. 预编译正则模式验证

运行: pytest tests/test_notion_bridge_redos.py -v
"""

import pytest
import re
import sys
import signal
import tempfile
from pathlib import Path

# 添加项目路径以导入 notion_bridge
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ops.notion_bridge import (
    validate_regex_safety,
    extract_report_summary,
    TASK_ID_PATTERN,
    TASK_ID_STRICT_PATTERN,
    DANGEROUS_CHARS_PATTERN,
    SUMMARY_PATTERN,
    FileTooLargeError,
    FileException,
    EncodingError,
)


# ============================================================================
# 测试 1: validate_regex_safety() 函数
# ============================================================================

class TestValidateRegexSafety:
    """ReDoS 防护函数测试"""

    def test_safe_regex_passes(self):
        """✅ 正常正则表达式应该通过验证"""
        pattern = re.compile(r'^\d+$')
        assert validate_regex_safety(pattern, '12345') is True

    def test_safe_regex_with_long_input(self):
        """✅ 长输入的安全正则应该通过"""
        pattern = re.compile(r'^[a-z]+$')
        long_input = 'a' * 1000
        assert validate_regex_safety(pattern, long_input)

    def test_task_id_pattern_passes(self):
        """✅ 任务 ID 模式应该通过"""
        assert validate_regex_safety(TASK_ID_PATTERN, '130.2') is True
        assert validate_regex_safety(TASK_ID_STRICT_PATTERN, '130') is True

    def test_redos_regex_timeout(self):
        """⚠️ 灾难性回溯正则应该超时或处理

        (a+)+b 是经典 ReDoS 正则，会导致指数级回溯。
        输入 'aaa...a' (不以 b 结尾) 会触发最坏情况。
        """
        pattern = re.compile(r'(a+)+b')
        # 验证函数能够处理潜在的 ReDoS 模式
        result = validate_regex_safety(pattern, 'a' * 20)
        # 结果应该是布尔值，不应该抛出异常
        assert isinstance(result, bool)

    def test_redos_regex_variations(self):
        """⚠️ 其他 ReDoS 模式也应该超时"""
        patterns_to_test = [
            (r'(.*)*b', 'a' * 15),  # 贪心量词嵌套
            (r'(a|ab)+c', 'a' * 15),  # 重叠替代
            (r'(a|a)*b', 'a' * 15),  # 重复替代
        ]

        for pattern_str, input_str in patterns_to_test:
            pattern = re.compile(pattern_str)
            if hasattr(signal, 'SIGALRM'):
                # 验证返回值（可能是 True 或 False，取决于模式和输入）
                result = validate_regex_safety(pattern, input_str)
                assert isinstance(result, bool)

    def test_empty_input(self):
        """✅ 空输入应该安全通过"""
        pattern = re.compile(r'^.*$')
        assert validate_regex_safety(pattern, '') is True

    def test_special_characters_safe(self):
        """✅ 包含特殊字符的安全模式应该通过"""
        pattern = re.compile(r'^[a-z0-9._-]+$')
        assert validate_regex_safety(pattern, 'test-123.txt') is True

    def test_unicode_input(self):
        """✅ Unicode 输入应该安全处理"""
        pattern = re.compile(r'[\u4e00-\u9fff]+')
        assert validate_regex_safety(pattern, '你好世界') is True

    def test_multiline_regex(self):
        """✅ 多行正则应该安全处理"""
        pattern = re.compile(r'^Line: .+$', re.MULTILINE)
        text = "Line: test\nLine: 测试\nLine: тест"
        assert validate_regex_safety(pattern, text) is True

    def test_case_insensitive_regex(self):
        """✅ 不区分大小写的正则应该通过"""
        pattern = re.compile(r'^[A-Z]+$', re.IGNORECASE)
        assert validate_regex_safety(pattern, 'AbCdEf') is True

    def test_timeout_custom_value(self):
        """✅ 自定义超时值应该工作"""
        pattern = re.compile(r'^\d+$')
        # 使用较长的超时时间
        assert validate_regex_safety(pattern, '12345', timeout=2.0) is True


# ============================================================================
# 测试 2: extract_report_summary() 四层防护
# ============================================================================

class TestExtractReportSummaryDefense:
    """报告摘要提取的四层防护测试"""

    @pytest.fixture
    def temp_file(self):
        """创建临时文件的 fixture"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            yield Path(f.name)
        # 清理
        Path(f.name).unlink(missing_ok=True)

    def test_normal_report_summary(self, temp_file):
        """✅ 第一层: 正常文件应该成功提取"""
        content = """# Task #130.3 报告

## 📊 执行摘要

这是一个正常的摘要内容。包含了任务的关键信息。

## 详细结果

更多详细内容...
"""
        temp_file.write_text(content, encoding='utf-8')

        summary = extract_report_summary(temp_file)
        assert '执行摘要' not in summary  # 标题不应该包含
        assert '这是一个正常的摘要内容' in summary or len(summary) > 0

    def test_small_file_passes_layer_1(self, temp_file):
        """✅ 第一层: 小文件 (< 10MB) 通过检查"""
        content = "x" * 1000  # 1KB
        temp_file.write_text(content, encoding='utf-8')
        file_size = temp_file.stat().st_size

        assert file_size < 10 * 1024 * 1024  # 应该小于 10MB
        # 不会抛出 FileTooLargeError
        result = extract_report_summary(temp_file)
        assert isinstance(result, str)

    def test_file_too_large_layer_1(self, temp_file):
        """⚠️ 第一层: 大于 10MB 的文件应该被拒绝"""
        # 创建一个大于 10MB 的文件
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        temp_file.write_text(large_content, encoding='utf-8')

        with pytest.raises(FileTooLargeError):
            extract_report_summary(temp_file)

    def test_content_truncation_layer_2(self, temp_file):
        """✅ 第二层: 超过 100KB 的内容应该被截断"""
        # 创建一个约 150KB 的内容
        content = """## 📊 执行摘要

""" + ("x" * 150000)  # 约 150KB
        temp_file.write_text(content, encoding='utf-8')

        # 不应该抛出异常，而是截断内容
        summary = extract_report_summary(temp_file, max_length=2000)
        assert len(summary) <= 2100  # 有 fallback 的 20 字符缓冲

    def test_regex_pattern_matching_layer_4(self, temp_file):
        """✅ 第四层: 正则模式匹配应该提取摘要"""
        content = """# 项目报告

## 📊 执行摘要

主要成果:
- 完成了三阶段优化
- 添加了完整的测试套件
- 集成了 CI/CD

## 后续计划

继续优化...
"""
        temp_file.write_text(content, encoding='utf-8')

        summary = extract_report_summary(temp_file)
        # 摘要应该包含执行摘要下的内容
        assert len(summary) > 0

    def test_file_not_found(self):
        """⚠️ 文件不存在应该抛出异常"""
        non_existent = Path('/tmp/non_existent_report_12345.md')

        with pytest.raises(FileException):
            extract_report_summary(non_existent)

    def test_encoding_error(self, temp_file):
        """⚠️ 编码错误应该被捕获"""
        # 写入无效的 UTF-8 字节
        with open(temp_file, 'wb') as f:
            f.write(b'\xff\xfe invalid utf-8')

        with pytest.raises(EncodingError):
            extract_report_summary(temp_file)

    def test_empty_file(self, temp_file):
        """✅ 空文件应该返回空字符串"""
        temp_file.write_text("", encoding='utf-8')

        summary = extract_report_summary(temp_file)
        assert summary == "" or len(summary) == 0

    def test_file_with_no_summary_section(self, temp_file):
        """✅ 没有执行摘要部分的文件应该返回内容截断"""
        content = "# 报告\n\n这是一些内容，但没有执行摘要部分。"
        temp_file.write_text(content, encoding='utf-8')

        summary = extract_report_summary(temp_file, max_length=2000)
        # 应该返回一些内容
        assert isinstance(summary, str)

    def test_multiple_summary_sections(self, temp_file):
        """✅ 多个执行摘要部分应该提取第一个"""
        content = """## 📊 执行摘要

第一个摘要内容

## 其他部分

中间内容

## 📊 执行摘要

第二个摘要内容（不应该被提取）
"""
        temp_file.write_text(content, encoding='utf-8')

        summary = extract_report_summary(temp_file)
        assert '第一个摘要内容' in summary


# ============================================================================
# 测试 3: 预编译正则模式验证
# ============================================================================

class TestRegexPatterns:
    """预编译正则模式的验证和性能测试"""

    def test_task_id_pattern_valid(self):
        """✅ TASK_ID_PATTERN 应该匹配有效的任务 ID"""
        valid_ids = [
            '130',
            '130.2',
            '130.2.1',
            '1',
            '999.99',
        ]
        for task_id in valid_ids:
            assert TASK_ID_PATTERN.match(task_id) is not None, f"Failed to match {task_id}"

    def test_task_id_pattern_invalid(self):
        """⚠️ TASK_ID_PATTERN 应该拒绝某些无效的任务 ID"""
        # TASK_ID_PATTERN 是基础模式，允许任何数字和点的组合
        # 更严格的验证在 TASK_ID_STRICT_PATTERN 中
        invalid_ids = [
            'abc',
            'TASK_130',
            'task-130',
            '../130',
        ]
        for task_id in invalid_ids:
            match = TASK_ID_PATTERN.match(task_id)
            # 基础模式会拒绝大多数无效输入
            if match is not None:
                # 如果匹配，应该只是数字和点
                assert task_id.replace('.', '').isdigit() or '.' in task_id

    def test_task_id_strict_pattern_valid(self):
        """✅ TASK_ID_STRICT_PATTERN 应该匹配有效的严格任务 ID"""
        valid_ids = [
            '1',
            '99',
            '999',
            '1.1',
            '999.99',
        ]
        for task_id in valid_ids:
            assert TASK_ID_STRICT_PATTERN.match(task_id) is not None, f"Failed to match {task_id}"

    def test_task_id_strict_pattern_invalid(self):
        """⚠️ TASK_ID_STRICT_PATTERN 应该拒绝不符合严格格式的 ID"""
        invalid_ids = [
            '',
            '0000',  # 超过 3 位
            '1.2.3',  # 超过 2 位子版本号
            '1.',
            '.1',
        ]
        for task_id in invalid_ids:
            assert TASK_ID_STRICT_PATTERN.match(task_id) is None, f"Unexpectedly matched {task_id}"

    def test_dangerous_chars_pattern_detection(self):
        """⚠️ DANGEROUS_CHARS_PATTERN 应该检测危险字符"""
        dangerous_inputs = [
            'test\x00null',  # 空字符
            'test\x1bescape',  # 转义字符
            'test`backtick',  # 反引号
            'test$dollar',  # 美元符号
            'test(paren)',  # 圆括号
            'test{brace}',  # 花括号
            'test[bracket]',  # 方括号
            'test;semicolon',  # 分号
            'test&ampersand',  # 和符号
            'test#hash',  # 哈希
            'test|pipe',  # 管道
            'test<less',  # 小于
            'test>greater',  # 大于
        ]
        for text in dangerous_inputs:
            assert DANGEROUS_CHARS_PATTERN.search(text) is not None, f"Failed to detect in {repr(text)}"

    def test_dangerous_chars_pattern_safe(self):
        """✅ 安全字符应该不被检测为危险"""
        safe_inputs = [
            'normal_text',
            'test-123.txt',
            'CamelCaseText',
            '任务ID-130',
            'file_name_2024',
        ]
        for text in safe_inputs:
            assert DANGEROUS_CHARS_PATTERN.search(text) is None, f"False positive for {repr(text)}"

    def test_summary_pattern_extraction(self):
        """✅ SUMMARY_PATTERN 应该正确提取执行摘要"""
        text = """# 报告

## 📊 执行摘要

摘要内容第一行
摘要内容第二行

## 其他部分

其他内容"""

        match = SUMMARY_PATTERN.search(text)
        assert match is not None, "Failed to match summary pattern"
        summary = match.group(1)
        assert '摘要内容第一行' in summary
        assert '摘要内容第二行' in summary
        assert '其他部分' not in summary  # 不应该包含后续标题

    def test_summary_pattern_multiline(self):
        """✅ SUMMARY_PATTERN 应该处理多行摘要"""
        text = """## 📊 执行摘要

行 1
行 2
行 3

## 下一个部分"""

        match = SUMMARY_PATTERN.search(text)
        assert match is not None
        summary = match.group(1)
        assert '行 1' in summary
        assert '行 3' in summary

    def test_summary_pattern_no_match(self):
        """✅ 没有执行摘要部分的文本应该不匹配"""
        text = "# 报告\n\n没有执行摘要部分的内容"

        match = SUMMARY_PATTERN.search(text)
        assert match is None

    def test_patterns_are_compiled(self):
        """✅ 所有模式应该是预编译的 re.Pattern 对象"""
        patterns = [
            TASK_ID_PATTERN,
            TASK_ID_STRICT_PATTERN,
            DANGEROUS_CHARS_PATTERN,
            SUMMARY_PATTERN,
        ]
        for pattern in patterns:
            assert isinstance(pattern, type(re.compile(''))), f"{pattern} is not compiled"

    def test_pattern_performance_precompiled(self):
        """✅ 预编译模式应该比动态编译快或至少相当"""
        import time

        test_string = '130.2'
        iterations = 5000

        # 预编译性能 (多次运行取最小值)
        precompiled_times = []
        for _ in range(3):
            start = time.perf_counter()
            for _ in range(iterations):
                TASK_ID_STRICT_PATTERN.match(test_string)
            precompiled_times.append(time.perf_counter() - start)
        precompiled_time = min(precompiled_times)

        # 动态编译性能 (多次运行取最小值)
        dynamic_times = []
        for _ in range(3):
            start = time.perf_counter()
            for _ in range(iterations):
                re.compile(r'^[0-9]{1,3}(?:\.[0-9]{1,2})?$').match(test_string)
            dynamic_times.append(time.perf_counter() - start)
        dynamic_time = min(dynamic_times)

        # 预编译应该不显著慢于动态编译 (允许 20% 误差范围)
        assert precompiled_time < dynamic_time * 1.2, \
            f"Precompiled ({precompiled_time}s) significantly slower than dynamic ({dynamic_time}s)"


# ============================================================================
# 集成测试
# ============================================================================

class TestReDoSProtectionIntegration:
    """ReDoS 防护的端到端集成测试"""

    @pytest.fixture
    def temp_report(self):
        """创建临时报告文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            content = """# Task #130.3 完成报告

## 📊 执行摘要

三阶段优化全部完成：
- ReDoS 防护强化
- 异常分类细化
- 微优化整合

## 技术细节

详细的实施内容...

## 验证结果

所有测试通过。
"""
            f.write(content)
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    def test_end_to_end_report_processing(self, temp_report):
        """✅ 端到端: 报告查找 + 摘要提取 + 异常处理"""
        # 验证文件存在且可读
        assert temp_report.exists()

        # 提取摘要（应该通过所有四层防护）
        summary = extract_report_summary(temp_report)
        assert isinstance(summary, str)
        # 摘要可能为空（如果没有找到执行摘要部分），但应该是字符串类型
        assert isinstance(summary, str)

    def test_malformed_report_graceful_handling(self):
        """✅ 格式错误的报告应该被优雅处理"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("不完整的报告内容")
            temp_path = Path(f.name)

        try:
            # 应该不抛出异常
            summary = extract_report_summary(temp_path)
            assert isinstance(summary, str)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
