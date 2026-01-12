#!/usr/bin/env python3
"""
Task #093.1: 高级特征工程框架 - 简化执行版本
不使用 Numba，使用纯 Python 实现以确保兼容性
"""

import sys
sys.path.insert(0, '/opt/mt5-crs')

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
import json
import os

from src.database.timescale_client import TimescaleClient
from src.feature_engineering.advanced_features import AdvancedFeatures


class SimpleFeatureBuilder:
    """简化的特征构建器 - 不使用 Numba"""

    @staticmethod
    def fractional_diff_simple(
        series: pd.Series,
        d: float = 0.5,
        threshold: float = 1e-5
    ) -> pd.Series:
        """
        分数差分（纯 Python 实现）

        Args:
            series: 输入序列
            d: 差分阶数
            threshold: 权重截断阈值

        Returns:
            分数差分后的序列
        """
        # 计算权重
        weights = [1.0]
        k = 1

        while True:
            weight = -weights[-1] * (d - k + 1) / k
            if abs(weight) < threshold:
                break
            weights.append(weight)
            k += 1
            if k > 100:  # 防止无限循环
                break

        weights = np.array(weights[::-1])  # 反转权重

        # 应用卷积
        result = pd.Series(index=series.index, dtype=float)
        for i in range(len(weights) - 1, len(series)):
            result.iloc[i] = np.dot(
                weights,
                series.iloc[i - len(weights) + 1:i + 1]
            )

        return result

    @staticmethod
    def adf_test(series: pd.Series, significance_level: float = 0.05) -> dict:
        """执行 ADF 平稳性测试"""
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
        d_range: np.ndarray = None,
        significance_level: float = 0.05,
        verbose: bool = True
    ) -> dict:
        """寻找最优的分数差分阶数 d"""
        if d_range is None:
            d_range = np.arange(0.0, 1.1, 0.1)

        results = []

        for d in d_range:
            # 应用分数差分
            diff_series = cls.fractional_diff_simple(series, d=d)

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


def main():
    """主函数"""
    print("=" * 60)
    print("Task #093.1: 高级特征工程框架")
    print("=" * 60)

    # 初始化数据库客户端
    client = TimescaleClient()

    if not client.check_connection():
        print("❌ 无法连接到数据库")
        return 1

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

    # 转换数值列为 float64
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    print(f"✅ 载入 {len(df)} 行数据")

    if len(df) == 0:
        print("❌ 数据为空，无法继续")
        return 1

    # 搜索最优 d 值
    print("\n🔍 搜索最优 d 值...")
    opt_result = SimpleFeatureBuilder.find_optimal_d(
        df['close'],
        d_range=np.arange(0.0, 1.1, 0.05),
        significance_level=0.05,
        verbose=True
    )

    print(f"\n{'=' * 60}")
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
    print(f"{'=' * 60}")

    # 使用最优 d 生成特征
    print("\n🔧 生成分数差分特征...")
    df['frac_diff_close_optimal'] = SimpleFeatureBuilder.fractional_diff_simple(
        df['close'],
        d=opt_result['optimal_d']
    )

    # 保存结果
    output_dir = '/opt/mt5-crs/docs/archive/tasks/TASK_093_1'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'aapl_features_simple.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ 特征数据已保存: {output_path}")

    # 保存最优 d 值结果
    result_file = os.path.join(output_dir, 'optimal_d_result.json')
    with open(result_file, 'w') as f:
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
            ),
            'data_rows': len(df)
        }, f, indent=2)
    print(f"✅ 最优 d 值结果已保存: {result_file}")

    print("\n" + "=" * 60)
    print("🎉 Task #093.1 特征工程完成!")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
