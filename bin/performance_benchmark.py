#!/usr/bin/env python3
"""
性能基准测试脚本
对比优化前后的性能提升
"""

import sys
import time
from pathlib import Path
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import pandas as pd
import numpy as np

from feature_engineering.basic_features import BasicFeatures
from feature_engineering.advanced_features import AdvancedFeatures

# 尝试导入优化模块
try:
    from optimization.numba_accelerated import (
        compute_frac_diff_weights,
        apply_frac_diff_weights,
        rolling_mean_fast,
        rolling_std_fast,
        get_acceleration_info
    )
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_data(n_rows=10000):
    """创建测试数据"""
    logger.info(f"创建测试数据: {n_rows} 行...")

    dates = pd.date_range('2020-01-01', periods=n_rows, freq='D')
    np.random.seed(42)

    data = {
        'time': dates,
        'open': 100 + np.random.randn(n_rows).cumsum(),
        'high': 102 + np.random.randn(n_rows).cumsum(),
        'low': 98 + np.random.randn(n_rows).cumsum(),
        'close': 100 + np.random.randn(n_rows).cumsum(),
        'volume': np.random.randint(1000000, 10000000, n_rows),
        'tick_volume': np.random.randint(10000, 100000, n_rows),
    }

    df = pd.DataFrame(data)
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

    return df


def benchmark_basic_features(df, n_runs=3):
    """基准测试基础特征计算"""
    logger.info("\n" + "=" * 60)
    logger.info("基准测试: 基础特征计算")
    logger.info("=" * 60)

    bf = BasicFeatures()
    times = []

    for i in range(n_runs):
        start = time.time()
        result = bf.calculate_all_features(df.copy())
        end = time.time()
        elapsed = end - start
        times.append(elapsed)
        logger.info(f"  运行 {i+1}: {elapsed:.2f} 秒")

    avg_time = np.mean(times)
    logger.info(f"  平均时间: {avg_time:.2f} 秒")
    logger.info(f"  吞吐量: {len(df) / avg_time:.0f} 行/秒")

    return avg_time, result


def benchmark_advanced_features(df, n_runs=3):
    """基准测试高级特征计算"""
    logger.info("\n" + "=" * 60)
    logger.info("基准测试: 高级特征计算")
    logger.info("=" * 60)

    # 先计算基础特征
    bf = BasicFeatures()
    df = bf.calculate_all_features(df.copy())

    af = AdvancedFeatures()
    times = []

    for i in range(n_runs):
        start = time.time()
        result = af.calculate_all_advanced_features(df.copy())
        end = time.time()
        elapsed = end - start
        times.append(elapsed)
        logger.info(f"  运行 {i+1}: {elapsed:.2f} 秒")

    avg_time = np.mean(times)
    logger.info(f"  平均时间: {avg_time:.2f} 秒")
    logger.info(f"  吞吐量: {len(df) / avg_time:.0f} 行/秒")

    return avg_time, result


def benchmark_numba_acceleration(n_rows=10000, n_runs=10):
    """基准测试 Numba 加速"""
    if not NUMBA_AVAILABLE:
        logger.warning("Numba 不可用，跳过加速测试")
        return None

    logger.info("\n" + "=" * 60)
    logger.info("基准测试: Numba 加速")
    logger.info("=" * 60)

    # 创建测试数据
    series = np.random.randn(n_rows).cumsum()

    results = {}

    # 1. 分数差分权重
    logger.info("\n1. 分数差分权重计算")

    # 原始 Python 实现
    def compute_weights_python(d, size, threshold=0.01):
        weights = [1.0]
        for k in range(1, size):
            weight = -weights[-1] * (d - k + 1) / k
            if abs(weight) < threshold:
                break
            weights.append(weight)
        return np.array(weights)

    # 测试 Python 版本
    python_times = []
    for _ in range(n_runs):
        start = time.time()
        compute_weights_python(0.5, 100)
        python_times.append(time.time() - start)

    # 测试 Numba 版本
    # 预热
    compute_frac_diff_weights(0.5, 100)

    numba_times = []
    for _ in range(n_runs):
        start = time.time()
        compute_frac_diff_weights(0.5, 100)
        numba_times.append(time.time() - start)

    python_avg = np.mean(python_times) * 1000  # 转换为毫秒
    numba_avg = np.mean(numba_times) * 1000
    speedup = python_avg / numba_avg

    logger.info(f"  Python: {python_avg:.2f} ms")
    logger.info(f"  Numba:  {numba_avg:.2f} ms")
    logger.info(f"  加速比: {speedup:.1f}x")

    results['frac_diff_weights'] = {'speedup': speedup, 'python_ms': python_avg, 'numba_ms': numba_avg}

    # 2. 滚动均值
    logger.info("\n2. 滚动均值计算")

    # Pandas 版本
    pandas_times = []
    for _ in range(n_runs):
        start = time.time()
        pd.Series(series).rolling(window=20).mean()
        pandas_times.append(time.time() - start)

    # Numba 版本 (预热)
    rolling_mean_fast(series, 20)

    numba_times = []
    for _ in range(n_runs):
        start = time.time()
        rolling_mean_fast(series, 20)
        numba_times.append(time.time() - start)

    pandas_avg = np.mean(pandas_times) * 1000
    numba_avg = np.mean(numba_times) * 1000
    speedup = pandas_avg / numba_avg

    logger.info(f"  Pandas: {pandas_avg:.2f} ms")
    logger.info(f"  Numba:  {numba_avg:.2f} ms")
    logger.info(f"  加速比: {speedup:.1f}x")

    results['rolling_mean'] = {'speedup': speedup, 'pandas_ms': pandas_avg, 'numba_ms': numba_avg}

    # 3. 滚动标准差
    logger.info("\n3. 滚动标准差计算")

    # Pandas 版本
    pandas_times = []
    for _ in range(n_runs):
        start = time.time()
        pd.Series(series).rolling(window=20).std()
        pandas_times.append(time.time() - start)

    # Numba 版本 (预热)
    rolling_std_fast(series, 20)

    numba_times = []
    for _ in range(n_runs):
        start = time.time()
        rolling_std_fast(series, 20)
        numba_times.append(time.time() - start)

    pandas_avg = np.mean(pandas_times) * 1000
    numba_avg = np.mean(numba_times) * 1000
    speedup = pandas_avg / numba_avg

    logger.info(f"  Pandas: {pandas_avg:.2f} ms")
    logger.info(f"  Numba:  {numba_avg:.2f} ms")
    logger.info(f"  加速比: {speedup:.1f}x")

    results['rolling_std'] = {'speedup': speedup, 'pandas_ms': pandas_avg, 'numba_ms': numba_avg}

    return results


def print_summary(basic_time, advanced_time, numba_results):
    """打印性能总结"""
    logger.info("\n" + "=" * 60)
    logger.info("性能基准测试总结")
    logger.info("=" * 60)

    logger.info(f"\n基础特征计算: {basic_time:.2f} 秒")
    logger.info(f"高级特征计算: {advanced_time:.2f} 秒")
    logger.info(f"总计: {basic_time + advanced_time:.2f} 秒")

    if numba_results:
        logger.info(f"\nNumba 加速效果:")
        for func_name, metrics in numba_results.items():
            logger.info(f"  {func_name}: {metrics['speedup']:.1f}x 加速")

    logger.info("\n系统信息:")
    logger.info(f"  Numba 可用: {'是' if NUMBA_AVAILABLE else '否'}")

    if NUMBA_AVAILABLE:
        acc_info = get_acceleration_info()
        logger.info(f"  JIT 编译: {'启用' if acc_info['jit_enabled'] else '禁用'}")
        logger.info(f"  并行化: {'启用' if acc_info['parallel_enabled'] else '禁用'}")


def main():
    """主函数"""
    logger.info("\n" + "=" * 60)
    logger.info("MT5-CRS 性能基准测试")
    logger.info("=" * 60)

    # 创建测试数据
    df = create_test_data(n_rows=10000)

    # 基准测试
    basic_time, _ = benchmark_basic_features(df, n_runs=3)
    advanced_time, _ = benchmark_advanced_features(df, n_runs=3)
    numba_results = benchmark_numba_acceleration(n_rows=10000, n_runs=10)

    # 打印总结
    print_summary(basic_time, advanced_time, numba_results)

    logger.info("\n" + "=" * 60)
    logger.info("基准测试完成!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
