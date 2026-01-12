#!/usr/bin/env python3
"""
三重障碍标签工厂 (Triple Barrier Factory) - Task #093.3

核心功能：
1. 动态波动率驱动的障碍设置
2. Numba JIT 加速的标签扫描
3. 元标签生成（Meta-labels）
4. 样本权重计算

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Team
Date: 2026-01-12

参考文献:
- "Advances in Financial Machine Learning" by Marcos Lopez de Prado
"""

import numpy as np
import pandas as pd
from numba import njit, float64, int64
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@njit(cache=True)
def scan_barriers_jit(
    prices: np.ndarray,
    volatility: np.ndarray,
    lookback_window: int,
    num_std: float,
    max_holding_period: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    JIT 加速的三重障碍标签扫描

    算法逻辑：
    1. 对每个时间点 t，使用 t-lookback_window 到 t 的波动率
    2. 计算动态障碍: TP/SL = num_std * volatility[t]
    3. 向前扫描未来价格，检测哪个障碍先触碰
    4. 返回标签、障碍类型、持有期、实际收益

    Args:
        prices: 价格序列 (float64 数组)
        volatility: 波动率序列 (float64 数组)
        lookback_window: 波动率回看窗口
        num_std: 障碍宽度（倍数）
        max_holding_period: 最大持有期

    Returns:
        labels: 标签数组 (1=上涨, -1=下跌, 0=超时, NaN=无效)
        barrier_touched: 障碍类型 (1=上, -1=下, 0=超时)
        holding_periods: 实际持有期
        returns: 实际收益率
    """
    n = len(prices)
    labels = np.full(n, np.nan, dtype=np.float64)
    barrier_touched = np.full(n, np.nan, dtype=np.float64)
    holding_periods = np.full(n, np.nan, dtype=np.float64)
    returns = np.full(n, np.nan, dtype=np.float64)

    # 从 lookback_window 开始扫描（确保有足够历史数据）
    for i in range(lookback_window, n - max_holding_period):
        entry_price = prices[i]

        # 使用当前时间点的波动率（已经是历史计算的）
        vol = volatility[i]

        # 跳过无效波动率
        if np.isnan(vol) or vol <= 0:
            continue

        # 计算动态障碍
        upper_barrier = num_std * vol
        lower_barrier = -num_std * vol

        # 扫描未来价格
        label = 0.0
        barrier_type = 0.0  # 0=超时, 1=上障碍, -1=下障碍
        holding_period = float(max_holding_period)
        actual_return = 0.0

        for t in range(1, max_holding_period + 1):
            if i + t >= n:
                break

            future_price = prices[i + t]
            ret = (future_price - entry_price) / entry_price

            # 检查上障碍
            if ret >= upper_barrier:
                label = 1.0
                barrier_type = 1.0
                holding_period = float(t)
                actual_return = ret
                break

            # 检查下障碍
            if ret <= lower_barrier:
                label = -1.0
                barrier_type = -1.0
                holding_period = float(t)
                actual_return = ret
                break

            # 最后一天：超时退出
            if t == max_holding_period:
                actual_return = ret
                # 根据收益方向设置标签
                if ret > 0:
                    label = 1.0
                elif ret < 0:
                    label = -1.0
                else:
                    label = 0.0
                barrier_type = 0.0
                holding_period = float(max_holding_period)

        # 记录结果
        labels[i] = label
        barrier_touched[i] = barrier_type
        holding_periods[i] = holding_period
        returns[i] = actual_return

    return labels, barrier_touched, holding_periods, returns


class TripleBarrierFactory:
    """
    三重障碍标签工厂

    功能：
    1. 基于动态波动率的障碍设置
    2. JIT 加速的标签生成
    3. 元标签生成（用于过滤虚假信号）
    4. 样本权重计算（处理类别不平衡）

    使用示例：
    >>> factory = TripleBarrierFactory()
    >>> labels = factory.generate_labels(
    ...     prices=df['close'],
    ...     volatility=df['volatility_20d'],
    ...     lookback_window=20,
    ...     num_std=2.0,
    ...     max_holding_period=10
    ... )
    """

    def __init__(self):
        """初始化工厂"""
        self.logger = logging.getLogger(__name__)

    def generate_labels(
        self,
        prices: pd.Series,
        volatility: pd.Series,
        lookback_window: int = 20,
        num_std: float = 2.0,
        max_holding_period: int = 10,
        generate_meta_labels: bool = False
    ) -> pd.DataFrame:
        """
        生成三重障碍标签

        Args:
            prices: 价格序列 (带时间索引的 Series)
            volatility: 波动率序列 (带时间索引的 Series)
            lookback_window: 波动率回看窗口
            num_std: 障碍宽度（波动率倍数）
            max_holding_period: 最大持有期
            generate_meta_labels: 是否生成元标签

        Returns:
            DataFrame 包含:
                - label: 标签 (1=上涨, -1=下跌, 0=超时)
                - barrier_touched: 障碍类型 ('upper', 'lower', 'vertical')
                - holding_period: 实际持有期
                - return: 实际收益率
                - meta_label: 元标签 (可选, 1=参与交易, 0=不参与)
                - sample_weight: 样本权重 (可选)
        """
        self.logger.info(f"生成三重障碍标签 (窗口={lookback_window}, 倍数={num_std}, 持有期={max_holding_period})")

        # 转换为 numpy 数组
        prices_arr = prices.values.astype(np.float64)
        volatility_arr = volatility.values.astype(np.float64)

        # 调用 JIT 加速函数
        labels, barrier_types, holding_periods, returns = scan_barriers_jit(
            prices=prices_arr,
            volatility=volatility_arr,
            lookback_window=lookback_window,
            num_std=num_std,
            max_holding_period=max_holding_period
        )

        # 构建结果 DataFrame
        result = pd.DataFrame({
            'label': labels,
            'barrier_touched': barrier_types,
            'holding_period': holding_periods,
            'return': returns
        }, index=prices.index)

        # 映射障碍类型
        barrier_map = {1.0: 'upper', -1.0: 'lower', 0.0: 'vertical'}
        result['barrier_touched'] = result['barrier_touched'].map(barrier_map)

        # 生成元标签
        if generate_meta_labels:
            result['meta_label'] = self._generate_meta_labels(result)

        # 计算样本权重
        result['sample_weight'] = self._calculate_sample_weights(result)

        # 统计信息
        self._log_statistics(result)

        return result

    def _generate_meta_labels(self, labels_df: pd.DataFrame) -> pd.Series:
        """
        生成元标签（Meta-labels）

        元标签用于回答："如果主模型预测买入，是否应该执行？"
        - meta_label = 1: 应该参与交易（收益为正）
        - meta_label = 0: 不应该参与（收益为负或零）

        Args:
            labels_df: 包含 'return' 列的 DataFrame

        Returns:
            元标签 Series (0 或 1)
        """
        # 简单策略：如果最终收益为正，则元标签=1
        meta = (labels_df['return'] > 0).astype(int)
        return meta

    def _calculate_sample_weights(self, labels_df: pd.DataFrame) -> pd.Series:
        """
        计算样本权重（处理类别不平衡）

        使用 sklearn 的 class_weight='balanced' 策略：
        weight[i] = n_samples / (n_classes * n_samples_in_class[i])

        Args:
            labels_df: 包含 'label' 列的 DataFrame

        Returns:
            样本权重 Series
        """
        valid_labels = labels_df['label'].dropna()

        if len(valid_labels) == 0:
            return pd.Series(1.0, index=labels_df.index)

        # 统计各类别数量
        label_counts = valid_labels.value_counts()
        n_samples = len(valid_labels)
        n_classes = len(label_counts)

        # 计算权重
        weights = {}
        for label, count in label_counts.items():
            weights[label] = n_samples / (n_classes * count)

        # 映射到所有样本
        sample_weights = labels_df['label'].map(weights)
        sample_weights = sample_weights.fillna(1.0)  # 无效样本权重为 1

        return sample_weights

    def _log_statistics(self, labels_df: pd.DataFrame):
        """
        记录标签统计信息

        Args:
            labels_df: 标签 DataFrame
        """
        valid = labels_df.dropna()
        if len(valid) == 0:
            self.logger.warning("⚠️  没有生成任何有效标签")
            return

        total = len(labels_df)
        valid_count = len(valid)

        self.logger.info(f"📊 标签统计:")
        self.logger.info(f"   总样本数: {total}")
        self.logger.info(f"   有效标签: {valid_count} ({valid_count/total*100:.1f}%)")

        # 类别分布
        label_dist = valid['label'].value_counts().sort_index()
        self.logger.info(f"   类别分布:")
        for label, count in label_dist.items():
            pct = count / valid_count * 100
            self.logger.info(f"      标签 {int(label):+2d}: {count:5d} ({pct:5.1f}%)")

        # 障碍触碰分布
        barrier_dist = valid['barrier_touched'].value_counts()
        self.logger.info(f"   障碍触碰:")
        for barrier, count in barrier_dist.items():
            pct = count / valid_count * 100
            self.logger.info(f"      {barrier:8s}: {count:5d} ({pct:5.1f}%)")

        # 平均持有期
        avg_holding = valid['holding_period'].mean()
        self.logger.info(f"   平均持有期: {avg_holding:.2f} 天")

        # 平均收益
        avg_return = valid['return'].mean()
        self.logger.info(f"   平均收益率: {avg_return*100:.4f}%")


def main():
    """主函数 - 示例用法"""
    print("="*60)
    print("Task #093.3: 三重障碍标签工厂测试")
    print("="*60)

    # 生成模拟数据
    np.random.seed(42)
    n = 1000
    dates = pd.date_range('2020-01-01', periods=n, freq='D')

    # 随机游走价格
    returns = np.random.randn(n) * 0.01 + 0.0001
    prices = pd.Series(1.1000 + np.cumsum(returns), index=dates, name='close')

    # 模拟波动率
    volatility = pd.Series(np.abs(np.random.randn(n) * 0.005 + 0.01), index=dates, name='volatility')

    # 创建工厂
    factory = TripleBarrierFactory()

    # 生成标签
    labels = factory.generate_labels(
        prices=prices,
        volatility=volatility,
        lookback_window=20,
        num_std=2.0,
        max_holding_period=10,
        generate_meta_labels=True
    )

    print(f"\n📊 标签结果:")
    print(labels.head(30))

    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
