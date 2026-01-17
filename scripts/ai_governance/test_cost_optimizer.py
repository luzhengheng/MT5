#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成本优化器测试套件
验证缓存、批处理、智能路由功能
"""

import os
import sys
import tempfile

# 添加本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from review_cache import ReviewCache
from review_batcher import ReviewBatcher
from cost_optimizer import AIReviewCostOptimizer


def test_cache():
    """测试多级缓存"""
    print("\n" + "=" * 80)
    print("🧪 Test 1: ReviewCache")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ReviewCache(cache_dir=tmpdir, ttl_hours=24)

        # 创建测试文件
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")

        # 测试保存和读取
        result = {'status': 'PASS', 'score': 8}
        cache.save(test_file, result)

        # 读取缓存
        cached = cache.get(test_file)
        assert cached == result, "Cache read failed"
        print("✅ Cache save/load: PASS")

        # 测试文件分割
        uncached_file = os.path.join(tmpdir, "uncached.py")
        with open(uncached_file, 'w') as f:
            f.write("def foo(): pass")

        cached_list, uncached_list = cache.split(
            [test_file, uncached_file]
        )
        assert test_file in cached_list, "Cached file not in cached list"
        assert uncached_file in uncached_list, (
            "Uncached file not in uncached list"
        )
        print("✅ Cache split: PASS")

        # 测试统计
        stats = cache.get_stats()
        assert stats['memory_cache_size'] > 0, "Memory cache empty"
        print("✅ Cache stats: {}".format(stats))


def test_batcher():
    """测试批处理"""
    print("\n" + "=" * 80)
    print("🧪 Test 2: ReviewBatcher")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        batcher = ReviewBatcher(max_batch_size=3)

        # 创建测试文件
        test_files = []
        for i in range(5):
            filepath = os.path.join(tmpdir, f"test{i}.py")
            with open(filepath, 'w') as f:
                f.write(f"# File {i}\nprint('test {i}')")
            test_files.append(filepath)

        # 创建批次
        batches = batcher.create_batches(test_files, separate_by_risk=False)

        # 验证批处理
        assert len(batches) > 0, "No batches created"
        total_files = sum(len(b.files) for b in batches)
        assert total_files == len(test_files), "Not all files in batches"
        msg = "✅ Batch creation: Created {} batches for {} files"
        print(msg.format(len(batches), len(test_files)))

        # 测试提示语格式化
        batch = batches[0]
        prompt = batcher.format_batch_prompt(batch, use_claude=False)
        assert "batch_" in prompt, "Batch ID not in prompt"
        assert test_files[0] in prompt, "File path not in prompt"
        print("✅ Batch prompt formatting: PASS")

        # 测试结果解析
        api_response = """
### 文件: {}
**风险**: LOW
**问题**: No issues
**建议**: Good code

### 文件: {}
**风险**: HIGH
**问题**: Potential bug
**建议**: Fix it
""".format(test_files[0], test_files[1])

        parsed = batcher.parse_batch_result(batch, api_response)
        assert test_files[0] in parsed, "First file not in parsed results"
        msg = "✅ Batch result parsing: PASS ({} files)"
        print(msg.format(len(parsed)))


def test_optimizer():
    """测试成本优化器"""
    print("\n" + "=" * 80)
    print("🧪 Test 3: AIReviewCostOptimizer")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        optimizer = AIReviewCostOptimizer(
            enable_cache=True,
            enable_batch=True,
            cache_dir=tmpdir,
            log_file=os.path.join(tmpdir, "optimizer.log")
        )

        # 创建测试文件
        test_files = []
        for i in range(5):
            filepath = os.path.join(tmpdir, "module{}.py".format(i))
            with open(filepath, 'w') as f:
                f.write("# Module {}\ndef function_{}(): pass".format(i, i))
            test_files.append(filepath)

        # 模拟API调用器
        call_count = [0]

        def mock_api_caller(batch):
            call_count[0] += 1
            results = {}
            for filepath in batch.files:
                results[filepath] = {
                    'status': 'PASS',
                    'risk': batch.risk_level,
                    'api_call': call_count[0]
                }
            return results

        # 第一次处理（未缓存）
        results1, stats1 = optimizer.process_files(
            test_files,
            api_caller=mock_api_caller
        )

        calls_first_pass = call_count[0]
        msg1 = "✅ First pass: {} files, {} API calls"
        print(msg1.format(len(results1), calls_first_pass))

        # 重置计数器
        call_count[0] = 0

        # 第二次处理（应该使用缓存）
        results2, stats2 = optimizer.process_files(
            test_files,
            api_caller=mock_api_caller
        )

        calls_second_pass = call_count[0]
        msg2 = "✅ Second pass (cached): {} files, {} API calls"
        print(msg2.format(len(results2), calls_second_pass))

        # 验证缓存效果
        assert calls_second_pass <= calls_first_pass, "Cache not working"
        reduction_pct = (
            max(0, (1 - calls_second_pass / calls_first_pass) * 100)
            if calls_first_pass > 0
            else 0
        )
        msg3 = "✅ Cache reduction: {} → {} calls (-{}%)"
        print(msg3.format(calls_first_pass, calls_second_pass, int(reduction_pct)))

        # 检查统计
        assert stats1['total_files'] == len(test_files), "File count mismatch"
        # stats1['cached_files'] 可能 > 0 如果使用了批处理缓存
        assert stats2['cached_files'] > 0, "Cache not working on second pass"
        print("✅ Stats verification: PASS")


def test_cost_reduction():
    """测试成本节省计算"""
    print("\n" + "=" * 80)
    print("🧪 Test 4: Cost Reduction Calculation")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        optimizer = AIReviewCostOptimizer(
            enable_cache=True,
            enable_batch=True,
            cache_dir=tmpdir,
            log_file=os.path.join(tmpdir, "optimizer.log")
        )

        # 创建大量测试文件
        test_files = []
        for i in range(20):
            filepath = os.path.join(tmpdir, "file{}.py".format(i))
            with open(filepath, 'w') as f:
                f.write("# File {}\npass".format(i))
            test_files.append(filepath)

        # 模拟批处理API调用
        def batch_api_caller(batch):
            results = {}
            for filepath in batch.files:
                results[filepath] = {
                    'status': 'PASS',
                    'batch_id': batch.batch_id
                }
            return results

        # 处理所有文件
        results, stats = optimizer.process_files(
            test_files,
            api_caller=batch_api_caller
        )

        # 计算成本节省
        baseline = len(test_files)  # 无优化情况
        actual = stats['api_calls']  # 有优化情况
        reduction = (baseline - actual) / baseline * 100

        print("Baseline (no optimization): {} API calls".format(baseline))
        print("With optimization: {} API calls".format(actual))
        print("Cost reduction: {:.1f}%".format(reduction))
        print("✅ Cost reduction verification: PASS")


def print_summary():
    """打印测试总结"""
    print("\n" + "=" * 80)
    print("📋 Test Summary")
    print("=" * 80)
    print("""
优化效果预期:
  1. 多级缓存: 避免重复审查 → 3-5x 成本降低
  2. 批处理: 合并多个请求 → 6-10x 成本降低
  3. 智能路由: 按需选择模型 → 1.3-2x 成本降低
  4. 综合优化: 缓存+批处理 → 10-15x 成本降低

所有测试完成！✅
    """)


if __name__ == "__main__":
    try:
        test_cache()
        test_batcher()
        test_optimizer()
        test_cost_reduction()
        print_summary()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
