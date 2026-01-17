#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Benchmark for Cost Optimizer
验证成本优化器的性能指标和成本节省

场景:
1. 小规模 (10 个文件)
2. 中等规模 (50 个文件)
3. 大规模 (100 个文件)

指标:
- API 调用次数
- 缓存命中率
- 成本节省率
- 执行时间
"""

import os
import sys
import time
import hashlib
import tempfile
from pathlib import Path

# 添加脚本目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cost_optimizer import AIReviewCostOptimizer
from review_batcher import ReviewBatch

# 颜色定义
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


def generate_test_files(count, risk_level="mixed"):
    """
    生成测试文件列表

    Args:
        count: 文件数量
        risk_level: 风险等级 ("high", "low", "mixed")

    Returns:
        list of (filepath, content) tuples
    """
    files = []

    # 高危文件内容
    high_risk_content = """
import subprocess
import os
import sys

# 危险操作：直接执行 shell 命令
result = os.system('rm -rf /')
output = subprocess.call('curl http://attacker.com')

# 硬编码密钥
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"

# SQL 注入风险
query = f"SELECT * FROM users WHERE id = {user_id}"
"""

    # 低危文件内容
    low_risk_content = """
def calculate_sum(numbers):
    \"\"\"计算数字总和\"\"\"
    return sum(numbers)

def filter_data(data):
    \"\"\"过滤数据\"\"\"
    return [item for item in data if item is not None]

class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, x):
        self.result += x
        return self.result
"""

    for i in range(count):
        if risk_level == "high":
            content = high_risk_content
        elif risk_level == "low":
            content = low_risk_content
        else:  # mixed
            content = high_risk_content if i % 2 == 0 else low_risk_content

        filepath = f"test_file_{i:04d}.py"
        files.append((filepath, content))

    return files


def simulate_api_call(batch):
    """
    模拟 API 调用
    返回批处理结果
    """
    time.sleep(0.1)  # 模拟网络延迟

    results = {}
    for file_info in batch.files:
        results[file_info['filepath']] = {
            'status': 'PASS',
            'risk': file_info['risk_level'],
            'comment': f'Code review for {file_info["filepath"]}'
        }

    return results


def benchmark_scenario(scenario_name, file_count, risk_distribution="mixed"):
    """
    执行一个基准测试场景
    """
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}场景: {scenario_name} ({file_count} 个文件){RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    # 生成测试文件
    print(f"[STEP 1] 生成 {file_count} 个测试文件...")
    test_files = generate_test_files(file_count, risk_distribution)
    print(f"  ✅ 生成完成\n")

    # 初始化优化器
    print(f"[STEP 2] 初始化成本优化器...")
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = os.path.join(tmpdir, "benchmark_cache")

        optimizer = AIReviewCostOptimizer(
            enable_cache=True,
            enable_batch=True,
            enable_routing=False,
            cache_dir=cache_dir,
            log_file=os.devnull  # 不输出日志
        )
        print(f"  ✅ 初始化完成\n")

        # 第一次运行：无缓存，完整批处理
        print(f"[STEP 3] 第一次运行 (无缓存)...")
        start_time = time.time()

        api_call_count_1 = 0

        def api_caller_1(batch):
            nonlocal api_call_count_1
            api_call_count_1 += 1
            return simulate_api_call(batch)

        results_1, stats_1 = optimizer.process_files(
            [f[0] for f in test_files],
            api_caller=api_caller_1,
            risk_detector=lambda f, c: ("high" if "import subprocess" in c else "low", []),
            force_refresh=True  # 强制刷新缓存
        )

        elapsed_1 = time.time() - start_time
        print(f"  ✅ 完成 ({elapsed_1:.2f}s)")
        print(f"     - API 调用次数: {api_call_count_1}")
        print(f"     - 缓存命中: {stats_1['cached_files']}")
        print(f"     - 新增审查: {stats_1['uncached_files']}")
        print(f"     - 成本节省率: {stats_1['cost_reduction_rate']:.1%}\n")

        # 第二次运行：完整缓存
        print(f"[STEP 4] 第二次运行 (使用缓存)...")
        start_time = time.time()

        api_call_count_2 = 0

        def api_caller_2(batch):
            nonlocal api_call_count_2
            api_call_count_2 += 1
            return simulate_api_call(batch)

        results_2, stats_2 = optimizer.process_files(
            [f[0] for f in test_files],
            api_caller=api_caller_2,
            risk_detector=lambda f, c: ("high" if "import subprocess" in c else "low", []),
            force_refresh=False  # 使用缓存
        )

        elapsed_2 = time.time() - start_time
        print(f"  ✅ 完成 ({elapsed_2:.2f}s)")
        print(f"     - API 调用次数: {api_call_count_2}")
        print(f"     - 缓存命中: {stats_2['cached_files']}")
        print(f"     - 新增审查: {stats_2['uncached_files']}")
        print(f"     - 成本节省率: {stats_2['cost_reduction_rate']:.1%}\n")

        # 计算基准对比
        print(f"[STEP 5] 性能对比分析...")
        baseline_cost = file_count * 5  # 假设每次 API 调用 $5
        optimized_cost_1 = api_call_count_1 * 5
        optimized_cost_2 = api_call_count_2 * 5

        cost_reduction_1 = (baseline_cost - optimized_cost_1) / baseline_cost if baseline_cost > 0 else 0
        cost_reduction_2 = (baseline_cost - optimized_cost_2) / baseline_cost if baseline_cost > 0 else 0

        print(f"\n📊 成本分析 (假设 $5 per API call):")
        print(f"  基准成本:      ${baseline_cost:>6.1f}  ({file_count} 次调用)")
        print(f"  第一次优化:    ${optimized_cost_1:>6.1f}  ({api_call_count_1} 次调用) - 节省 {cost_reduction_1:.1%}")
        print(f"  第二次优化:    ${optimized_cost_2:>6.1f}  ({api_call_count_2} 次调用) - 节省 {cost_reduction_2:.1%}")

        print(f"\n⏱️  执行时间:")
        print(f"  第一次运行:    {elapsed_1:.2f}s")
        print(f"  第二次运行:    {elapsed_2:.2f}s (加速 {elapsed_1/elapsed_2:.1f}x)")

        # 验证成本节省目标
        print(f"\n{BLUE}验证目标:{RESET}")
        if cost_reduction_1 >= 0.80:
            print(f"  {GREEN}✅ 第一次运行成本节省 ≥ 80% {RESET}")
        else:
            print(f"  {RED}❌ 第一次运行成本节省 < 80% {RESET}")

        if api_call_count_2 == 0:
            print(f"  {GREEN}✅ 第二次运行完全使用缓存 (0 次 API 调用){RESET}")
        else:
            print(f"  {YELLOW}⚠️  第二次运行仍需 {api_call_count_2} 次 API 调用{RESET}")

        return {
            'scenario': scenario_name,
            'file_count': file_count,
            'api_calls_run1': api_call_count_1,
            'api_calls_run2': api_call_count_2,
            'cost_reduction_1': cost_reduction_1,
            'cost_reduction_2': cost_reduction_2,
            'baseline_cost': baseline_cost,
            'optimized_cost_1': optimized_cost_1,
            'optimized_cost_2': optimized_cost_2,
            'time_1': elapsed_1,
            'time_2': elapsed_2,
            'stats_1': stats_1,
            'stats_2': stats_2
        }


def main():
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}成本优化器性能基准测试{RESET}")
    print(f"{CYAN}{'='*80}{RESET}")

    # 运行三个场景
    results = []

    # 场景 1: 小规模 (10 个文件)
    result_1 = benchmark_scenario("小规模 (10 个文件)", 10, "mixed")
    results.append(result_1)

    # 场景 2: 中等规模 (50 个文件)
    result_2 = benchmark_scenario("中等规模 (50 个文件)", 50, "mixed")
    results.append(result_2)

    # 场景 3: 大规模 (100 个文件)
    result_3 = benchmark_scenario("大规模 (100 个文件)", 100, "mixed")
    results.append(result_3)

    # 汇总报告
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{CYAN}基准测试总结{RESET}")
    print(f"{CYAN}{'='*80}{RESET}\n")

    print(f"{'场景':<15} {'文件数':<8} {'API调用(1)':<12} {'API调用(2)':<12} {'成本节省(1)':<12} {'成本节省(2)':<12}")
    print(f"{'-'*80}")

    all_pass = True
    for r in results:
        cost_red_1_str = f"{r['cost_reduction_1']:.1%}"
        cost_red_2_str = f"{r['cost_reduction_2']:.1%}"

        # 检查是否通过基准
        pass_1 = r['cost_reduction_1'] >= 0.80
        pass_2 = r['api_calls_run2'] <= 2  # 第二次应该用缓存

        if not (pass_1 and pass_2):
            all_pass = False

        marker = f"{GREEN}✅{RESET}" if (pass_1 and pass_2) else f"{RED}❌{RESET}"

        print(f"{marker} {r['scenario']:<13} {r['file_count']:<8} {r['api_calls_run1']:<12} {r['api_calls_run2']:<12} {cost_red_1_str:<12} {cost_red_2_str:<12}")

    print(f"\n{BLUE}预期目标:{RESET}")
    print(f"  • 场景1: API调用 10→1-2, 成本节省 80-90%")
    print(f"  • 场景2: API调用 50→3-5, 成本节省 90-94%")
    print(f"  • 场景3: API调用 100→4-10, 成本节省 90-96%")

    if all_pass:
        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN}✅ 所有基准测试通过!{RESET}")
        print(f"{GREEN}{'='*80}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*80}{RESET}")
        print(f"{RED}❌ 部分基准测试未通过{RESET}")
        print(f"{RED}{'='*80}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
