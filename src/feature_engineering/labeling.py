"""
标签生成模块 - Triple Barrier Labeling
用于监督学习的标签生成

来源: "Advances in Financial Machine Learning" by Marcos Lopez de Prado
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TripleBarrierLabeling:
    """
    三重壁垒标签法 (Triple Barrier Method)

    为每个样本设置三个退出条件:
    1. 上界 (Upper Barrier): 价格上涨达到目标收益 -> 标签 = 1 (做多)
    2. 下界 (Lower Barrier): 价格下跌达到止损 -> 标签 = -1 (做空/止损)
    3. 时间界 (Vertical Barrier): 持有期到期 -> 标签 = 0 或基于收益方向

    优势:
    - 避免固定持有期的偏差
    - 考虑止损和止盈
    - 更符合实际交易逻辑
    """

    @staticmethod
    def apply_triple_barrier(
        prices: pd.Series,
        upper_barrier: float = 0.02,
        lower_barrier: float = -0.02,
        max_holding_period: int = 5,
        stop_loss: Optional[float] = None
    ) -> pd.DataFrame:
        """
        应用三重壁垒标签法

        Args:
            prices: 价格序列 (Series with datetime index)
            upper_barrier: 上界收益率阈值 (默认 2%)
            lower_barrier: 下界收益率阈值 (默认 -2%)
            max_holding_period: 最大持有期 (天数)
            stop_loss: 止损阈值 (可选,如 -1% 止损)

        Returns:
            DataFrame 包含:
                - label: 标签 (1=上涨, -1=下跌, 0=中性)
                - barrier_touched: 触发的壁垒类型 ('upper', 'lower', 'vertical')
                - holding_period: 实际持有期
                - return: 实际收益率
        """
        logger.info("应用 Triple Barrier Labeling...")

        results = []

        for i in range(len(prices) - max_holding_period):
            entry_price = prices.iloc[i]
            entry_date = prices.index[i]

            # 未来价格序列
            future_prices = prices.iloc[i+1:i+1+max_holding_period]

            if len(future_prices) == 0:
                continue

            # 计算收益率
            returns = (future_prices - entry_price) / entry_price

            # 检查壁垒触发
            label = 0
            barrier_touched = 'vertical'
            holding_period = max_holding_period
            actual_return = returns.iloc[-1] if len(returns) > 0 else 0

            # 1. 检查上界
            upper_touch = returns >= upper_barrier
            if upper_touch.any():
                upper_idx = upper_touch.idxmax()
                upper_day = returns.index.get_loc(upper_idx)

                # 2. 检查下界
                lower_touch = returns <= lower_barrier
                if lower_touch.any():
                    lower_idx = lower_touch.idxmax()
                    lower_day = returns.index.get_loc(lower_idx)

                    # 哪个先触发
                    if upper_day <= lower_day:
                        label = 1
                        barrier_touched = 'upper'
                        holding_period = upper_day + 1
                        actual_return = returns.iloc[upper_day]
                    else:
                        label = -1
                        barrier_touched = 'lower'
                        holding_period = lower_day + 1
                        actual_return = returns.iloc[lower_day]
                else:
                    # 只触发上界
                    label = 1
                    barrier_touched = 'upper'
                    holding_period = upper_day + 1
                    actual_return = returns.iloc[upper_day]

            else:
                # 3. 检查下界
                lower_touch = returns <= lower_barrier
                if lower_touch.any():
                    lower_idx = lower_touch.idxmax()
                    lower_day = returns.index.get_loc(lower_idx)
                    label = -1
                    barrier_touched = 'lower'
                    holding_period = lower_day + 1
                    actual_return = returns.iloc[lower_day]
                else:
                    # 到达时间界
                    # 基于最终收益方向判断标签
                    if actual_return > 0:
                        label = 1
                    elif actual_return < 0:
                        label = -1
                    else:
                        label = 0

            # 4. 检查止损 (可选)
            if stop_loss is not None and stop_loss < 0:
                stop_touch = returns <= stop_loss
                if stop_touch.any():
                    stop_idx = stop_touch.idxmax()
                    stop_day = returns.index.get_loc(stop_idx)

                    # 止损优先
                    if stop_day < holding_period:
                        label = -1
                        barrier_touched = 'stop_loss'
                        holding_period = stop_day + 1
                        actual_return = returns.iloc[stop_day]

            results.append({
                'date': entry_date,
                'label': label,
                'barrier_touched': barrier_touched,
                'holding_period': holding_period,
                'return': actual_return,
                'entry_price': entry_price,
            })

        result_df = pd.DataFrame(results)
        result_df.set_index('date', inplace=True)

        # 统计
        label_counts = result_df['label'].value_counts()
        logger.info(f"标签分布: {label_counts.to_dict()}")
        logger.info(f"平均持有期: {result_df['holding_period'].mean():.2f} 天")
        logger.info(f"触发统计: {result_df['barrier_touched'].value_counts().to_dict()}")

        return result_df

    @staticmethod
    def compute_meta_labels(
        predictions: pd.Series,
        actual_returns: pd.Series,
        threshold: float = 0.0
    ) -> pd.Series:
        """
        计算元标签 (Meta-Labeling)

        元标签用于二级模型,判断主模型的预测是否应该被信任

        Args:
            predictions: 主模型的预测 (1=做多, -1=做空)
            actual_returns: 实际收益率
            threshold: 收益率阈值 (默认 0,即盈利=1,亏损=0)

        Returns:
            元标签序列 (1=应该交易, 0=不应该交易)
        """
        logger.info("计算 Meta-Labels...")

        meta_labels = pd.Series(0, index=predictions.index)

        # 做多信号 -> 检查是否盈利
        long_signals = predictions == 1
        meta_labels[long_signals & (actual_returns > threshold)] = 1

        # 做空信号 -> 检查是否盈利
        short_signals = predictions == -1
        meta_labels[short_signals & (actual_returns < -threshold)] = 1

        positive_rate = meta_labels.mean()
        logger.info(f"元标签正样本比例: {positive_rate:.2%}")

        return meta_labels

    @staticmethod
    def compute_sample_weights(
        labels: pd.Series,
        returns: pd.Series,
        decay: float = 0.95
    ) -> pd.Series:
        """
        计算样本权重 (Sample Weights)

        考虑因素:
        1. 时间衰减: 近期样本权重更高
        2. 收益幅度: 收益越大权重越高
        3. 类别平衡: 少数类样本权重更高

        Args:
            labels: 标签序列
            returns: 收益率序列
            decay: 时间衰减系数 (默认 0.95)

        Returns:
            样本权重序列
        """
        logger.info("计算样本权重...")

        weights = pd.Series(1.0, index=labels.index)

        # 1. 时间衰减权重
        n = len(labels)
        time_weights = np.array([decay ** (n - i - 1) for i in range(n)])
        weights *= time_weights

        # 2. 收益幅度权重 (绝对收益越大权重越高)
        return_weights = 1 + np.abs(returns)
        weights *= return_weights

        # 3. 类别平衡权重
        label_counts = labels.value_counts()
        max_count = label_counts.max()

        for label, count in label_counts.items():
            class_weight = max_count / count
            weights[labels == label] *= class_weight

        # 归一化
        weights = weights / weights.sum() * len(weights)

        logger.info(f"权重统计: mean={weights.mean():.4f}, std={weights.std():.4f}, "
                   f"min={weights.min():.4f}, max={weights.max():.4f}")

        return weights

    @staticmethod
    def add_labels_to_dataframe(
        df: pd.DataFrame,
        price_column: str = 'close',
        upper_barrier: float = 0.02,
        lower_barrier: float = -0.02,
        max_holding_period: int = 5,
        stop_loss: Optional[float] = None
    ) -> pd.DataFrame:
        """
        将 Triple Barrier 标签添加到 DataFrame

        Args:
            df: 包含价格数据的 DataFrame
            price_column: 价格列名
            upper_barrier: 上界阈值
            lower_barrier: 下界阈值
            max_holding_period: 最大持有期
            stop_loss: 止损阈值

        Returns:
            添加了标签列的 DataFrame
        """
        logger.info(f"为 DataFrame 添加 Triple Barrier 标签...")

        # 应用三重壁垒
        prices = df.set_index('date')[price_column] if 'date' in df.columns else df[price_column]
        labels_df = TripleBarrierLabeling.apply_triple_barrier(
            prices,
            upper_barrier=upper_barrier,
            lower_barrier=lower_barrier,
            max_holding_period=max_holding_period,
            stop_loss=stop_loss
        )

        # 合并标签
        df = df.set_index('date') if 'date' in df.columns else df
        df = df.join(labels_df[['label', 'barrier_touched', 'holding_period', 'return']], how='left')

        # 填充未标注的行
        df['label'] = df['label'].fillna(0).astype(int)
        df['barrier_touched'] = df['barrier_touched'].fillna('none')
        df['holding_period'] = df['holding_period'].fillna(0).astype(int)
        df['return'] = df['return'].fillna(0)

        # 计算样本权重
        df['sample_weight'] = TripleBarrierLabeling.compute_sample_weights(
            df['label'],
            df['return']
        )

        df = df.reset_index()

        logger.info("标签添加完成 ✓")
        return df


# 测试代码
if __name__ == '__main__':
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')

    # 模拟价格序列 (带趋势和噪音)
    trend = np.linspace(100, 120, len(dates))
    noise = np.random.randn(len(dates)) * 2
    prices = pd.Series(trend + noise, index=dates)

    print("测试 Triple Barrier Labeling...")
    print("=" * 60)

    # 应用三重壁垒
    labels_df = TripleBarrierLabeling.apply_triple_barrier(
        prices,
        upper_barrier=0.03,
        lower_barrier=-0.02,
        max_holding_period=5,
        stop_loss=-0.01
    )

    print("\n标签结果:")
    print(labels_df.head(10))

    print("\n标签统计:")
    print(labels_df['label'].value_counts())
    print(f"\n平均持有期: {labels_df['holding_period'].mean():.2f} 天")

    print("\n触发类型统计:")
    print(labels_df['barrier_touched'].value_counts())

    print("\n收益率统计:")
    print(labels_df['return'].describe())

    # 测试添加到 DataFrame
    test_df = pd.DataFrame({
        'date': dates,
        'close': prices.values,
        'volume': np.random.randint(1000000, 10000000, len(dates)),
    })

    test_df = TripleBarrierLabeling.add_labels_to_dataframe(
        test_df,
        upper_barrier=0.03,
        lower_barrier=-0.02,
        max_holding_period=5
    )

    print("\n添加标签后的 DataFrame:")
    print(test_df[['date', 'close', 'label', 'barrier_touched', 'holding_period', 'sample_weight']].head(10))

    print("\n" + "=" * 60)
    print("Triple Barrier Labeling 测试完成!")
