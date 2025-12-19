"""
Numba JIT 加速的计算函数
用于加速分数差分、滚动统计等计算密集型操作
"""

import logging
import numpy as np

# 尝试导入 Numba
try:
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    logging.warning("Numba not available. Install with: pip install numba")

    # 提供 fallback decorator
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    prange = range

logger = logging.getLogger(__name__)


# ==================== 分数差分加速 ====================

@jit(nopython=True)
def compute_frac_diff_weights(d: float, size: int, threshold: float = 0.01) -> np.ndarray:
    """
    计算分数差分权重 (Numba 加速)

    Args:
        d: 差分阶数 (0 < d < 1)
        size: 权重数量
        threshold: 权重阈值

    Returns:
        权重数组
    """
    weights = np.zeros(size)
    weights[0] = 1.0

    for k in range(1, size):
        weight = -weights[k-1] * (d - k + 1) / k

        if abs(weight) < threshold:
            break

        weights[k] = weight

    # 归一化
    weights_sum = np.sum(np.abs(weights))
    if weights_sum > 0:
        weights = weights / weights_sum

    return weights


@jit(nopython=True)
def apply_frac_diff_weights(series: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    应用分数差分权重 (Numba 加速)

    Args:
        series: 时间序列
        weights: 差分权重

    Returns:
        差分后的序列
    """
    n = len(series)
    w_len = len(weights)
    result = np.full(n, np.nan)

    for i in range(w_len, n):
        conv_sum = 0.0
        for j in range(w_len):
            if not np.isnan(series[i-j]):
                conv_sum += weights[j] * series[i-j]
        result[i] = conv_sum

    return result


# ==================== 滚动统计加速 ====================

@jit(nopython=True)
def rolling_mean_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动均值 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小

    Returns:
        滚动均值
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        window_sum = 0.0
        count = 0

        for j in range(window):
            val = series[i-j]
            if not np.isnan(val):
                window_sum += val
                count += 1

        if count > 0:
            result[i] = window_sum / count

    return result


@jit(nopython=True)
def rolling_std_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动标准差 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小

    Returns:
        滚动标准差
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        values = []

        for j in range(window):
            val = series[i-j]
            if not np.isnan(val):
                values.append(val)

        if len(values) > 1:
            # 计算标准差
            mean = np.mean(np.array(values))
            var = np.mean((np.array(values) - mean) ** 2)
            result[i] = np.sqrt(var)

    return result


@jit(nopython=True)
def rolling_skew_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动偏度 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小

    Returns:
        滚动偏度
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        values = []

        for j in range(window):
            val = series[i-j]
            if not np.isnan(val):
                values.append(val)

        if len(values) >= 3:
            arr = np.array(values)
            mean = np.mean(arr)
            std = np.std(arr)

            if std > 1e-10:
                # 计算偏度
                skew = np.mean(((arr - mean) / std) ** 3)
                result[i] = skew

    return result


@jit(nopython=True)
def rolling_kurt_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动峰度 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小

    Returns:
        滚动峰度
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        values = []

        for j in range(window):
            val = series[i-j]
            if not np.isnan(val):
                values.append(val)

        if len(values) >= 4:
            arr = np.array(values)
            mean = np.mean(arr)
            std = np.std(arr)

            if std > 1e-10:
                # 计算峰度
                kurt = np.mean(((arr - mean) / std) ** 4) - 3.0
                result[i] = kurt

    return result


@jit(nopython=True)
def rolling_min_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动最小值 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小

    Returns:
        滚动最小值
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        min_val = np.inf
        found = False

        for j in range(window):
            val = series[i-j]
            if not np.isnan(val):
                if val < min_val:
                    min_val = val
                found = True

        if found:
            result[i] = min_val

    return result


@jit(nopython=True)
def rolling_max_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动最大值 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小

    Returns:
        滚动最大值
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        max_val = -np.inf
        found = False

        for j in range(window):
            val = series[i-j]
            if not np.isnan(val):
                if val > max_val:
                    max_val = val
                found = True

        if found:
            result[i] = max_val

    return result


# ==================== 自相关加速 ====================

@jit(nopython=True)
def rolling_autocorr_fast(series: np.ndarray, window: int, lag: int = 1) -> np.ndarray:
    """
    滚动自相关 (Numba 加速)

    Args:
        series: 时间序列
        window: 窗口大小
        lag: 滞后期

    Returns:
        滚动自相关
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1+lag, n):
        x_values = []
        y_values = []

        for j in range(window):
            x_val = series[i-j]
            y_val = series[i-j-lag]

            if not np.isnan(x_val) and not np.isnan(y_val):
                x_values.append(x_val)
                y_values.append(y_val)

        if len(x_values) >= 2:
            x_arr = np.array(x_values)
            y_arr = np.array(y_values)

            x_mean = np.mean(x_arr)
            y_mean = np.mean(y_arr)

            numerator = np.sum((x_arr - x_mean) * (y_arr - y_mean))
            denominator = np.sqrt(np.sum((x_arr - x_mean) ** 2) * np.sum((y_arr - y_mean) ** 2))

            if denominator > 1e-10:
                result[i] = numerator / denominator

    return result


# ==================== 最大回撤加速 ====================

@jit(nopython=True)
def rolling_max_drawdown_fast(series: np.ndarray, window: int) -> np.ndarray:
    """
    滚动最大回撤 (Numba 加速)

    Args:
        series: 时间序列 (累计收益)
        window: 窗口大小

    Returns:
        滚动最大回撤
    """
    n = len(series)
    result = np.full(n, np.nan)

    for i in range(window-1, n):
        max_val = -np.inf
        max_dd = 0.0

        for j in range(window):
            val = series[i-window+1+j]

            if not np.isnan(val):
                if val > max_val:
                    max_val = val

                if max_val > 0:
                    dd = (val - max_val) / max_val
                    if dd < max_dd:
                        max_dd = dd

        result[i] = max_dd

    return result


# ==================== EMA 加速 ====================

@jit(nopython=True)
def ema_fast(series: np.ndarray, span: int) -> np.ndarray:
    """
    指数移动平均 (Numba 加速)

    Args:
        series: 时间序列
        span: 跨度

    Returns:
        EMA 序列
    """
    n = len(series)
    result = np.full(n, np.nan)

    alpha = 2.0 / (span + 1.0)

    # 找到第一个非 NaN 值作为初始值
    for i in range(n):
        if not np.isnan(series[i]):
            result[i] = series[i]
            break

    # 计算 EMA
    for i in range(1, n):
        if not np.isnan(series[i]):
            if not np.isnan(result[i-1]):
                result[i] = alpha * series[i] + (1 - alpha) * result[i-1]
            else:
                result[i] = series[i]

    return result


# ==================== 便捷函数 ====================

def get_acceleration_info() -> dict:
    """
    获取加速信息

    Returns:
        加速信息字典
    """
    return {
        'numba_available': NUMBA_AVAILABLE,
        'jit_enabled': NUMBA_AVAILABLE,
        'parallel_enabled': NUMBA_AVAILABLE,
        'functions': [
            'compute_frac_diff_weights',
            'apply_frac_diff_weights',
            'rolling_mean_fast',
            'rolling_std_fast',
            'rolling_skew_fast',
            'rolling_kurt_fast',
            'rolling_min_fast',
            'rolling_max_fast',
            'rolling_autocorr_fast',
            'rolling_max_drawdown_fast',
            'ema_fast',
        ]
    }


def benchmark_function(func, *args, n_runs: int = 10):
    """
    基准测试函数性能

    Args:
        func: 要测试的函数
        *args: 函数参数
        n_runs: 运行次数

    Returns:
        平均运行时间 (秒)
    """
    import time

    # 预热
    func(*args)

    # 测试
    times = []
    for _ in range(n_runs):
        start = time.time()
        func(*args)
        end = time.time()
        times.append(end - start)

    return np.mean(times)
