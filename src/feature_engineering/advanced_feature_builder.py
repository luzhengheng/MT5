"""
高级特征构建器 (Task #093.1)

集成 Numba 加速的分数差分计算，支持:
1. 快速分数差分计算
2. ADF 平稳性测试
3. 最优 d 值自动搜索
4. 完整特征集构建

作者: MT5-CRS Team
日期: 2026-01-12
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from statsmodels.tsa.stattools import adfuller
from numba import jit

from src.feature_engineering.advanced_features import AdvancedFeatures


class AdvancedFeatureBuilder:
    """
    高级特征构建器

    集成:
    1. Numba 加速的分数差分计算
    2. ADF 平稳性测试
    3. 最优 d 值搜索
    4. 特征平稳性验证
    """

    @staticmethod
    @jit(nopython=True)
    def compute_frac_diff_weights(
        d: float,
        threshold: float = 1e-5,
        max_k: int = 100
    ) -> np.ndarray:
        """
        使用 Numba 加速计算分数差分权重

        Args:
            d: 差分阶数
            threshold: 权重截断阈值
            max_k: 最大迭代次数

        Returns:
            权重数组
        """
        weights = np.zeros(max_k)
        weights[0] = 1.0
        k = 1

        for i in range(1, max_k):
            weight = -weights[i-1] * (d - k + 1) / k
            if abs(weight) < threshold:
                break
            weights[i] = weight
            k += 1

        # 返回非零权重
        return weights[:k]

    @staticmethod
    @jit(nopython=True)
    def apply_frac_diff(
        series: np.ndarray,
        weights: np.ndarray
    ) -> np.ndarray:
        """
        使用 Numba 加速应用分数差分

        Args:
            series: 输入序列
            weights: 差分权重

        Returns:
            差分后的序列
        """
        n = len(series)
        w_len = len(weights)
        result = np.full(n, np.nan)

        for i in range(w_len - 1, n):
            result[i] = np.dot(weights[::-1], series[i - w_len + 1:i + 1])

        return result

    @classmethod
    def fractional_diff_fast(
        cls,
        series: pd.Series,
        d: float = 0.5,
        threshold: float = 1e-5
    ) -> pd.Series:
        """
        快速分数差分（使用 Numba 加速）

        Args:
            series: 输入序列
            d: 差分阶数
            threshold: 权重截断阈值

        Returns:
            分数差分后的序列
        """
        weights = cls.compute_frac_diff_weights(d, threshold)
        values = series.values
        result = cls.apply_frac_diff(values, weights)

        return pd.Series(result, index=series.index)

    @staticmethod
    def adf_test(
        series: pd.Series,
        significance_level: float = 0.05
    ) -> Dict:
        """
        执行 ADF 平稳性测试

        Args:
            series: 输入序列
            significance_level: 显著性水平

        Returns:
            测试结果字典
        """
        # 去除 NaN
        series_clean = series.dropna()

        if len(series_clean) < 10:
            return {
                'statistic': np.nan,
                'pvalue': np.nan,
                'is_stationary': False,
                'reason': 'insufficient_data'
            }

        try:
            result = adfuller(series_clean, autolag='AIC')

            return {
                'statistic': result[0],
                'pvalue': result[1],
                'is_stationary': result[1] < significance_level,
                'critical_values': result[4],
                'reason': (
                    'pass' if result[1] < significance_level
                    else 'non_stationary'
                )
            }
        except Exception as e:
            return {
                'statistic': np.nan,
                'pvalue': np.nan,
                'is_stationary': False,
                'reason': f'error: {str(e)}'
            }

    @classmethod
    def find_optimal_d(
        cls,
        series: pd.Series,
        d_range: Optional[np.ndarray] = None,
        significance_level: float = 0.05,
        verbose: bool = True
    ) -> Dict:
        """
        寻找最优的分数差分阶数 d

        目标: 找到最小的 d 值，使得序列平稳（ADF p-value < 0.05）

        Args:
            series: 输入序列
            d_range: d 值搜索范围
            significance_level: 显著性水平
            verbose: 是否打印详细信息

        Returns:
            包含最优 d 值和所有结果的字典
        """
        if d_range is None:
            d_range = np.arange(0.0, 1.1, 0.1)

        results = []

        for d in d_range:
            # 应用分数差分
            diff_series = cls.fractional_diff_fast(series, d=d)

            # ADF 测试
            adf_result = cls.adf_test(diff_series, significance_level)

            # 计算相关性（衡量记忆性保留）
            correlation = series.corr(diff_series.shift(1))

            results.append({
                'd': d,
                'adf_statistic': adf_result['statistic'],
                'adf_pvalue': adf_result['pvalue'],
                'is_stationary': adf_result['is_stationary'],
                'correlation': correlation
            })

            if verbose:
                status = "✅" if adf_result['is_stationary'] else "❌"
                print(
                    f"{status} d={d:.2f}: "
                    f"p-value={adf_result['pvalue']:.4f}, "
                    f"corr={correlation:.4f}"
                )

        results_df = pd.DataFrame(results)

        # 找到第一个平稳的 d 值（最小 d）
        stationary_results = results_df[results_df['is_stationary']]

        if len(stationary_results) > 0:
            optimal_d = stationary_results.iloc[0]['d']
            optimal_result = stationary_results.iloc[0].to_dict()
        else:
            # 如果没有平稳的，选择 p-value 最小的
            optimal_idx = results_df['adf_pvalue'].idxmin()
            optimal_d = results_df.loc[optimal_idx, 'd']
            optimal_result = results_df.loc[optimal_idx].to_dict()

        return {
            'optimal_d': optimal_d,
            'optimal_result': optimal_result,
            'all_results': results_df
        }

    @classmethod
    def build_features(
        cls,
        df: pd.DataFrame,
        optimal_d: Optional[float] = None
    ) -> pd.DataFrame:
        """
        构建完整的特征集

        如果提供 optimal_d，使用该值；否则自动搜索最优 d

        Args:
            df: 输入数据框
            optimal_d: 可选的最优 d 值

        Returns:
            包含所有特征的数据框
        """
        print("🔧 开始构建高级特征...")

        # 1. 如果没有提供 optimal_d，自动搜索
        if optimal_d is None:
            print("\n🔍 搜索最优分数差分阶数 d...")
            opt_result = cls.find_optimal_d(df['close'], verbose=True)
            optimal_d = opt_result['optimal_d']
            print(f"\n✅ 最优 d 值: {optimal_d:.2f}")

        # 2. 使用 AdvancedFeatures 计算所有特征
        df = AdvancedFeatures.compute_all_advanced_features(df)

        # 3. 添加使用最优 d 的分数差分特征
        df['frac_diff_close_optimal'] = cls.fractional_diff_fast(
            df['close'],
            d=optimal_d
        )

        print(f"\n✅ 特征构建完成，共 {len(df.columns)} 个特征")

        return df


def main():
    """主函数 - 用于测试"""
    from src.database.timescale_client import TimescaleClient

    print("="*60)
    print("Task #093.1: 高级特征工程框架")
    print("="*60)

    # 初始化数据库客户端
    client = TimescaleClient()

    if not client.check_connection():
        print("❌ 无法连接到数据库")
        return

    # 载入 AAPL 数据
    query = """
    SELECT
        time as date,
        symbol,
        open,
        high,
        low,
        close,
        volume
    FROM market_candles
    WHERE symbol = 'AAPL.US' AND period = 'd'
    ORDER BY time ASC;
    """

    print("\n📊 载入 AAPL 数据...")
    df = pd.read_sql(query, client.engine)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✅ 载入 {len(df)} 行数据")

    # 搜索最优 d 值
    print("\n🔍 搜索最优 d 值...")
    opt_result = AdvancedFeatureBuilder.find_optimal_d(
        df['close'],
        d_range=np.arange(0.0, 1.1, 0.05),
        significance_level=0.05,
        verbose=True
    )

    print(f"\n{'='*60}")
    print("最优结果:")
    print(f"  d 值: {opt_result['optimal_d']:.2f}")
    print(
        f"  ADF p-value: "
        f"{opt_result['optimal_result']['adf_pvalue']:.6f}"
    )
    print(
        f"  平稳性: "
        f"{'✅ 是' if opt_result['optimal_result']['is_stationary'] else '❌ 否'}"
    )
    print(
        f"  相关性: {opt_result['optimal_result']['correlation']:.4f}"
    )
    print(f"{'='*60}")

    # 构建特征
    print("\n🔧 构建完整特征集...")
    features_df = AdvancedFeatureBuilder.build_features(
        df.copy(),
        optimal_d=opt_result['optimal_d']
    )

    # 保存结果
    output_dir = '/opt/mt5-crs/docs/archive/tasks/TASK_093_1'
    import os
    os.makedirs(output_dir, exist_ok=True)

    output_path = f'{output_dir}/aapl_features.csv'  # noqa: F541
    features_df.to_csv(output_path, index=False)
    print(f"\n✅ 特征数据已保存: {output_path}")

    # 保存最优 d 值结果
    import json
    with open(f'{output_dir}/optimal_d_result.json', 'w') as f:
        json.dump({
            'symbol': 'AAPL.US',
            'optimal_d': float(opt_result['optimal_d']),
            'adf_pvalue': float(
                opt_result['optimal_result']['adf_pvalue']
            ),
            'is_stationary': bool(
                opt_result['optimal_result']['is_stationary']
            ),
            'correlation': float(
                opt_result['optimal_result']['correlation']
            )
        }, f, indent=2)
    print(f"✅ 最优 d 值结果已保存")

    print("\n" + "="*60)
    print("🎉 Task #093.1 特征工程完成!")
    print("="*60)


if __name__ == '__main__':
    main()
