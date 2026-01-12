#!/usr/bin/env python3
"""
JIT-Accelerated Feature Engineering Operators (Task #093.2)

Numba-optimized implementations of core feature engineering operators
with explicit type signatures to avoid object mode fallback.

Core operators:
1. Fractional Differentiation (FracDiff)
2. Rolling Volatility
3. Weight calculation utilities

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Team
Date: 2026-01-12
"""

import numpy as np
import pandas as pd
from numba import njit, float64, int64


@njit(float64[:](float64, float64, int64), cache=True)
def compute_frac_diff_weights(
    d: float,
    threshold: float = 1e-5,
    max_k: int = 100
) -> np.ndarray:
    """
    计算分数差分权重 (Numba JIT 加速)

    使用显式类型签名: float64[:](float64, float64, int64)
    - 输入: d (差分阶数), threshold (截断阈值), max_k (最大长度)
    - 输出: float64 数组

    Args:
        d: 差分阶数 (0.0 - 1.0)
        threshold: 权重截断阈值
        max_k: 最大权重数量

    Returns:
        权重数组 (numpy.ndarray)

    Example:
        >>> weights = compute_frac_diff_weights(0.5, 1e-5, 100)
        >>> print(f"Weight count: {len(weights)}")
    """
    weights = np.zeros(max_k, dtype=np.float64)
    weights[0] = 1.0

    for k in range(1, max_k):
        weight = -weights[k-1] * (d - float(k) + 1.0) / float(k)

        if abs(weight) < threshold:
            # 截断，但仍返回完整数组（与基准保持一致）
            break

        weights[k] = weight

    return weights


@njit(float64[:](float64[:], float64[:]), cache=True)
def apply_frac_diff_jit(
    series: np.ndarray,
    weights: np.ndarray
) -> np.ndarray:
    """
    应用分数差分权重到序列 (Numba JIT 加速)

    使用显式类型签名: float64[:](float64[:], float64[:])
    - 输入: series (价格序列), weights (差分权重)
    - 输出: float64 数组

    算法: 对每个位置 i，计算 dot(weights[::-1], series[i-w_len+1:i+1])
    等价于: sum(weights[w_len-1-j] * series[i-w_len+1+j] for j in range(w_len))

    Args:
        series: 输入时间序列
        weights: 差分权重

    Returns:
        分数差分后的序列

    Example:
        >>> series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        >>> weights = compute_frac_diff_weights(0.5)
        >>> result = apply_frac_diff_jit(series, weights)
    """
    n = len(series)
    w_len = len(weights)
    result = np.full(n, np.nan, dtype=np.float64)

    # 使用卷积计算差分
    # 等价于 np.dot(weights[::-1], series[i - w_len + 1:i + 1])
    for i in range(w_len - 1, n):
        conv_sum = 0.0
        for j in range(w_len):
            # weights[::-1][j] = weights[w_len-1-j]
            # series[i-w_len+1:i+1][j] = series[i-w_len+1+j]
            conv_sum += weights[w_len - 1 - j] * series[i - w_len + 1 + j]
        result[i] = conv_sum

    return result


@njit(float64[:](float64[:], int64), cache=True)
def rolling_std_jit(series: np.ndarray, window: int) -> np.ndarray:
    """
    计算滚动标准差 (Numba JIT 加速)

    使用显式类型签名: float64[:](float64[:], int64)
    使用 ddof=1 (样本标准差) 以匹配 Pandas 默认行为

    Args:
        series: 输入序列
        window: 窗口大小

    Returns:
        滚动标准差序列

    Example:
        >>> series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        >>> vol = rolling_std_jit(series, window=3)
    """
    n = len(series)
    result = np.full(n, np.nan, dtype=np.float64)

    for i in range(window - 1, n):
        window_data = series[i - window + 1:i + 1]
        # 手动计算样本标准差 (ddof=1)
        mean = np.mean(window_data)
        variance = np.sum((window_data - mean) ** 2) / (window - 1)
        result[i] = np.sqrt(variance)

    return result


@njit(float64[:](float64[:], int64), cache=True)
def rolling_mean_jit(series: np.ndarray, window: int) -> np.ndarray:
    """
    计算滚动平均 (Numba JIT 加速)

    使用显式类型签名: float64[:](float64[:], int64)

    Args:
        series: 输入序列
        window: 窗口大小

    Returns:
        滚动平均序列
    """
    n = len(series)
    result = np.full(n, np.nan, dtype=np.float64)

    for i in range(window - 1, n):
        window_data = series[i - window + 1:i + 1]
        result[i] = np.mean(window_data)

    return result


@njit(float64(float64[:], float64[:]), cache=True)
def calculate_correlation_jit(x: np.ndarray, y: np.ndarray) -> float:
    """
    计算相关系数 (Numba JIT 加速)

    使用显式类型签名: float64(float64[:], float64[:])

    Args:
        x: 数组 1
        y: 数组 2

    Returns:
        相关系数
    """
    # 确保两个数组长度相同
    if len(x) != len(y):
        return np.nan

    # 移除 NaN 值（只保留两个数组都有效的位置）
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        return np.nan

    # 计算均值
    mean_x = np.mean(x_clean)
    mean_y = np.mean(y_clean)

    # 计算标准差
    std_x = np.std(x_clean)
    std_y = np.std(y_clean)

    if std_x == 0.0 or std_y == 0.0:
        return np.nan

    # 计算协方差
    n = len(x_clean)
    cov = 0.0
    for i in range(n):
        cov += (x_clean[i] - mean_x) * (y_clean[i] - mean_y)
    cov /= n

    # 计算相关系数
    corr = cov / (std_x * std_y)

    return corr


class JITFeatureEngine:
    """
    JIT 加速特征引擎

    封装所有 Numba 加速算子，提供 Pandas 友好的接口
    """

    @staticmethod
    def fractional_diff(
        series: pd.Series,
        d: float = 0.5,
        threshold: float = 1e-5,
        max_k: int = 100
    ) -> pd.Series:
        """
        分数差分 (Pandas 接口)

        Args:
            series: 输入 Pandas Series
            d: 差分阶数
            threshold: 权重截断阈值
            max_k: 最大权重数量

        Returns:
            分数差分后的 Pandas Series

        Example:
            >>> df = pd.DataFrame({'close': [1.0, 2.0, 3.0, 4.0, 5.0]})
            >>> df['frac_diff'] = JITFeatureEngine.fractional_diff(df['close'], d=0.5)
        """
        # 计算权重
        weights = compute_frac_diff_weights(d, threshold, max_k)

        # 转换为 numpy 数组
        values = series.values.astype(np.float64)

        # 应用分数差分
        result = apply_frac_diff_jit(values, weights)

        # 返回 Pandas Series
        return pd.Series(result, index=series.index, name=f'frac_diff_d{d:.2f}')

    @staticmethod
    def rolling_volatility(
        series: pd.Series,
        window: int = 20
    ) -> pd.Series:
        """
        滚动波动率 (Pandas 接口)

        Args:
            series: 输入 Pandas Series
            window: 窗口大小

        Returns:
            滚动波动率 Series

        Example:
            >>> df['volatility'] = JITFeatureEngine.rolling_volatility(df['close'], window=20)
        """
        values = series.values.astype(np.float64)
        result = rolling_std_jit(values, window)

        return pd.Series(result, index=series.index, name=f'rolling_vol_{window}')

    @staticmethod
    def rolling_average(
        series: pd.Series,
        window: int = 20
    ) -> pd.Series:
        """
        滚动平均 (Pandas 接口)

        Args:
            series: 输入 Pandas Series
            window: 窗口大小

        Returns:
            滚动平均 Series
        """
        values = series.values.astype(np.float64)
        result = rolling_mean_jit(values, window)

        return pd.Series(result, index=series.index, name=f'rolling_mean_{window}')


def benchmark_jit_speedup(series: pd.Series, d: float = 0.5, n_iterations: int = 10) -> dict:
    """
    性能基准测试：JIT vs Pure Python

    Args:
        series: 测试序列
        d: 差分阶数
        n_iterations: 迭代次数

    Returns:
        性能对比结果字典

    Example:
        >>> import pandas as pd
        >>> test_series = pd.Series(np.random.randn(1000))
        >>> results = benchmark_jit_speedup(test_series)
        >>> print(f"Speedup: {results['speedup']:.2f}x")
    """
    import time

    # JIT 预热
    _ = JITFeatureEngine.fractional_diff(series[:100], d=d)

    # 测试 JIT 版本
    start_jit = time.time()
    for _ in range(n_iterations):
        _ = JITFeatureEngine.fractional_diff(series, d=d)
    time_jit = time.time() - start_jit

    # 测试纯 Python 版本 (使用 AdvancedFeatureBuilder 作为基准)
    from src.feature_engineering.advanced_feature_builder import AdvancedFeatureBuilder

    start_python = time.time()
    for _ in range(n_iterations):
        _ = AdvancedFeatureBuilder.fractional_diff_fast(series, d=d)
    time_python = time.time() - start_python

    speedup = time_python / time_jit if time_jit > 0 else 0

    return {
        'time_jit': time_jit,
        'time_python': time_python,
        'speedup': speedup,
        'n_iterations': n_iterations,
        'series_length': len(series)
    }


def main():
    """主函数 - 性能测试和验证"""
    print("="*60)
    print("Task #093.2: JIT 算子性能测试")
    print("="*60)

    # 生成测试数据
    np.random.seed(42)
    test_series = pd.Series(np.cumsum(np.random.randn(5000)), name='close')

    print(f"\n📊 测试数据: {len(test_series)} 个数据点")

    # 性能基准测试
    print("\n🚀 运行性能基准测试...")
    results = benchmark_jit_speedup(test_series, d=0.5, n_iterations=50)

    print(f"\n{'='*60}")
    print("性能测试结果:")
    print(f"  JIT 时间: {results['time_jit']:.4f} 秒")
    print(f"  Python 时间: {results['time_python']:.4f} 秒")
    print(f"  加速比: {results['speedup']:.2f}x")
    print(f"  迭代次数: {results['n_iterations']}")
    print(f"{'='*60}")

    # 验证正确性
    print("\n🔍 验证计算正确性...")
    jit_result = JITFeatureEngine.fractional_diff(test_series[:1000], d=0.5)
    python_result = AdvancedFeatureBuilder.fractional_diff_fast(test_series[:1000], d=0.5)

    # 计算差异
    diff = (jit_result - python_result).abs().max()
    print(f"  最大误差: {diff:.10f}")

    if diff < 1e-6:
        print("  ✅ 计算结果一致")
    else:
        print(f"  ⚠️  计算结果存在差异 (最大误差: {diff})")

    print("\n" + "="*60)
    print("🎉 JIT 算子测试完成!")
    print("="*60)


if __name__ == '__main__':
    # Import after function definitions
    from src.feature_engineering.advanced_feature_builder import AdvancedFeatureBuilder
    main()
