"""
性能基准测试 - Notion Bridge (Protocol v4.4 优化 2)

覆盖范围:
  1. 正则表达式性能基准
  2. 异常处理性能基准
  3. 系统级性能基准

运行: pytest tests/test_notion_bridge_performance.py -v -m performance
"""

import pytest
import sys
import time
import tempfile
import re
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ops.notion_bridge import (
    validate_regex_safety,
    extract_report_summary,
    sanitize_task_id,
    TASK_ID_STRICT_PATTERN,
    DANGEROUS_CHARS_PATTERN,
    SUMMARY_PATTERN,
)


# ============================================================================
# 性能基准配置
# ============================================================================

@pytest.mark.performance
class TestRegexPerformance:
    """正则表达式性能基准测试"""

    def test_precompiled_vs_dynamic_task_id(self):
        """✅ 预编译 vs 动态编译性能对比 (目标: 预编译快 50%+)"""
        test_string = '130.2'
        iterations = 10000

        # 预编译性能
        start = time.perf_counter()
        for _ in range(iterations):
            TASK_ID_STRICT_PATTERN.match(test_string)
        precompiled_time = time.perf_counter() - start

        # 动态编译性能
        start = time.perf_counter()
        for _ in range(iterations):
            pattern = re.compile(r'^[0-9]{1,3}(?:\.[0-9]{1,2})?$')
            pattern.match(test_string)
        dynamic_time = time.perf_counter() - start

        # 预编译应该快 50%+
        speedup = dynamic_time / precompiled_time
        print(f"\nPrecompiled: {precompiled_time:.4f}s")
        print(f"Dynamic:     {dynamic_time:.4f}s")
        print(f"Speedup:     {speedup:.2f}x")

        assert precompiled_time < dynamic_time, \
            f"Precompiled ({precompiled_time}s) should be faster than dynamic ({dynamic_time}s)"
        assert speedup >= 1.5, f"Speedup only {speedup}x, expected >1.5x"

    def test_dangerous_chars_detection_performance(self):
        """✅ 危险字符检测性能"""
        safe_input = 'normal_task_id_130'
        unsafe_input = 'malicious$(whoami)'
        iterations = 5000

        # 安全输入性能
        start = time.perf_counter()
        for _ in range(iterations):
            DANGEROUS_CHARS_PATTERN.search(safe_input)
        safe_time = time.perf_counter() - start

        # 不安全输入性能
        start = time.perf_counter()
        for _ in range(iterations):
            DANGEROUS_CHARS_PATTERN.search(unsafe_input)
        unsafe_time = time.perf_counter() - start

        # 两者都应该很快 (<1ms 总时间)
        assert safe_time < 0.1, f"Safe detection too slow: {safe_time}s"
        assert unsafe_time < 0.1, f"Unsafe detection too slow: {unsafe_time}s"

        print(f"\nSafe input:   {safe_time:.4f}s ({iterations} iterations)")
        print(f"Unsafe input: {unsafe_time:.4f}s ({iterations} iterations)")

    def test_summary_pattern_performance(self):
        """✅ 摘要模式匹配性能"""
        text = """# 报告

## 📊 执行摘要

这是摘要内容。

## 其他部分

其他内容。
"""
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            SUMMARY_PATTERN.search(text)
        elapsed = time.perf_counter() - start

        # 应该很快 (<0.1s for 1000 iterations = <0.1ms per iteration)
        assert elapsed < 0.1, f"Pattern matching too slow: {elapsed}s for {iterations} iterations"

        print(f"\nSummary pattern: {elapsed:.4f}s ({iterations} iterations)")
        print(f"Per iteration:   {elapsed / iterations * 1000:.2f}ms")


# ============================================================================
# 异常处理性能
# ============================================================================

@pytest.mark.performance
class TestExceptionPerformance:
    """异常处理的性能基准"""

    def test_exception_creation_performance(self):
        """✅ 异常创建性能"""
        from scripts.ops.notion_bridge import (
            PathTraversalError,
            FileTooLargeError,
            TaskMetadataError,
        )

        exception_classes = [
            PathTraversalError,
            FileTooLargeError,
            TaskMetadataError,
        ]
        iterations = 10000

        for exc_class in exception_classes:
            start = time.perf_counter()
            for _ in range(iterations):
                exc = exc_class("test message")
            elapsed = time.perf_counter() - start

            # 异常创建应该很快 (<0.1ms 每个)
            per_op = elapsed / iterations * 1000
            assert per_op < 0.1, \
                f"{exc_class.__name__} creation too slow: {per_op:.4f}ms"

            print(f"\n{exc_class.__name__}: {per_op:.4f}ms per creation")

    def test_exception_catching_performance(self):
        """✅ 异常捕获性能"""
        from scripts.ops.notion_bridge import NotionBridgeException

        iterations = 5000

        start = time.perf_counter()
        for _ in range(iterations):
            try:
                raise NotionBridgeException("test")
            except NotionBridgeException:
                pass
        elapsed = time.perf_counter() - start

        per_op = elapsed / iterations * 1000
        # 异常捕获应该相对快速
        assert per_op < 1.0, f"Exception catching too slow: {per_op:.4f}ms"

        print(f"\nException catching: {per_op:.4f}ms per operation")


# ============================================================================
# 系统级性能
# ============================================================================

@pytest.mark.performance
class TestSystemLevelPerformance:
    """系统级性能基准"""

    def test_sanitize_task_id_throughput(self):
        """✅ 任务 ID 清洗吞吐量"""
        task_ids = [
            '130',
            'TASK_130',
            'TASK_130.2',
            '130.2',
        ]
        iterations = 1000

        start = time.perf_counter()
        processed = 0
        for _ in range(iterations):
            for task_id in task_ids:
                try:
                    sanitize_task_id(task_id)
                    processed += 1
                except Exception:
                    # 某些测试可能会抛出异常，这是正常的
                    pass
        elapsed = time.perf_counter() - start

        throughput = processed / elapsed
        per_op = elapsed / processed * 1000

        assert throughput > 1000, f"Too slow: {throughput:.0f} ops/sec"
        assert per_op < 1.0, f"Per operation: {per_op:.4f}ms"

        print(f"\nTask ID sanitization:")
        print(f"  Throughput: {throughput:.0f} ops/sec")
        print(f"  Per op:     {per_op:.4f}ms")

    def test_extract_summary_performance(self):
        """✅ 摘要提取性能"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            content = """# 报告

## 📊 执行摘要

这是摘要内容，包含了任务的关键信息。

## 详细结果

更多详细内容...
"""
            f.write(content)
            temp_path = Path(f.name)

        try:
            iterations = 100

            start = time.perf_counter()
            for _ in range(iterations):
                extract_report_summary(temp_path)
            elapsed = time.perf_counter() - start

            per_op = elapsed / iterations * 1000

            assert per_op < 10.0, f"Too slow: {per_op:.2f}ms per extraction"

            print(f"\nReport summary extraction:")
            print(f"  Per op: {per_op:.2f}ms")
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_regex_safety_performance(self):
        """✅ ReDoS 防护性能开销"""
        pattern = re.compile(r'^\d+$')
        test_input = '12345'
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            validate_regex_safety(pattern, test_input)
        elapsed = time.perf_counter() - start

        per_op = elapsed / iterations * 1000

        # 超时检测应该有最小的开销
        assert per_op < 1.0, f"ReDoS check too slow: {per_op:.4f}ms"

        print(f"\nRegex safety validation:")
        print(f"  Per op: {per_op:.4f}ms")


# ============================================================================
# 并发性能测试
# ============================================================================

@pytest.mark.performance
class TestConcurrentPerformance:
    """并发场景性能"""

    def test_concurrent_task_id_processing(self):
        """✅ 并发任务 ID 处理性能"""
        import concurrent.futures

        task_ids = ['TASK_130', '130.2', 'TASK#130.1'] * 20  # 60 个任务

        def process_task_id(task_id):
            try:
                return sanitize_task_id(task_id)
            except Exception:
                return None

        # 单线程性能
        start = time.perf_counter()
        results = [process_task_id(tid) for tid in task_ids]
        single_thread_time = time.perf_counter() - start

        # 多线程性能
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_task_id, task_ids))
        multi_thread_time = time.perf_counter() - start

        print(f"\nConcurrent task ID processing:")
        print(f"  Single thread: {single_thread_time:.4f}s")
        print(f"  Multi thread:  {multi_thread_time:.4f}s")

        # 多线程应该相对快速（虽然 GIL 的影响可能使其不明显快）
        assert len(results) == len(task_ids)


# ============================================================================
# 性能基线测试
# ============================================================================

@pytest.mark.performance
class TestPerformanceBaselines:
    """性能基线建立"""

    def test_establish_baseline_regex_operations(self):
        """建立正则操作的性能基线"""
        baselines = {
            '预编译模式匹配': None,
            '动态模式编译': None,
            '危险字符检测': None,
        }

        # 预编译模式匹配
        start = time.perf_counter()
        for _ in range(10000):
            TASK_ID_STRICT_PATTERN.match('130.2')
        baselines['预编译模式匹配'] = time.perf_counter() - start

        # 动态模式编译
        start = time.perf_counter()
        for _ in range(10000):
            re.compile(r'^[0-9]{1,3}(?:\.[0-9]{1,2})?$').match('130.2')
        baselines['动态模式编译'] = time.perf_counter() - start

        # 危险字符检测
        start = time.perf_counter()
        for _ in range(10000):
            DANGEROUS_CHARS_PATTERN.search('normal_text')
        baselines['危险字符检测'] = time.perf_counter() - start

        print("\n性能基线:")
        for name, time_taken in baselines.items():
            print(f"  {name}: {time_taken:.4f}s")

        # 验证所有操作都在合理时间内
        for time_taken in baselines.values():
            assert time_taken < 1.0, "Operation took too long"

    def test_establish_baseline_exception_operations(self):
        """建立异常操作的性能基线"""
        from scripts.ops.notion_bridge import TaskMetadataError

        baselines = {
            '异常创建': None,
            '异常捕获': None,
        }

        # 异常创建
        start = time.perf_counter()
        for _ in range(5000):
            exc = TaskMetadataError("test")
        baselines['异常创建'] = time.perf_counter() - start

        # 异常捕获
        start = time.perf_counter()
        for _ in range(1000):
            try:
                raise TaskMetadataError("test")
            except TaskMetadataError:
                pass
        baselines['异常捕获'] = time.perf_counter() - start

        print("\n异常操作基线:")
        for name, time_taken in baselines.items():
            print(f"  {name}: {time_taken:.4f}s")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'performance'])
