#!/usr/bin/env python3
"""
Signal Generation Engine - The Decision Maker
===============================================

提供 SignalEngine 类，将技术指标转换为交易信号（1: 买入, -1: 卖出, 0: 持有）。

核心原则：
- **严格向量化**: 使用 pandas 布尔运算，禁止行迭代
- **信号值约束**: 仅返回 1 (Buy), -1 (Sell), 0 (Hold)
- **策略可扩展**: 支持多种策略选择

功能：
- apply_strategy(df, strategy_name) - 应用指定策略生成信号
- 策略 A (MA Crossover) - 均线交叉策略
- 策略 B (RSI Reversion) - RSI 超买超卖反转策略
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)


class SignalEngine:
    """
    信号生成引擎

    将技术指标转换为可操作的交易信号。
    所有信号生成逻辑必须是向量化的。

    信号值：
        1: 买入 (Long)
        -1: 卖出 (Short)
        0: 持有 (Neutral)
    """

    @staticmethod
    def apply_strategy(
        df: pd.DataFrame,
        strategy_name: str = 'ma_crossover'
    ) -> pd.DataFrame:
        """
        应用指定策略生成交易信号

        参数：
            df (DataFrame): 包含技术指标的 OHLCV 数据
            strategy_name (str): 策略名称，可选：
                - 'ma_crossover': 均线交叉策略
                - 'rsi_reversion': RSI 超买超卖反转策略

        返回：
            DataFrame: 原 DataFrame + 新列 'signal' (int: 1, -1, 0)

        注意：
            信号生成需要预先计算的技术指标列
        """
        if strategy_name == 'ma_crossover':
            return SignalEngine._ma_crossover_strategy(df)
        elif strategy_name == 'rsi_reversion':
            return SignalEngine._rsi_reversion_strategy(df)
        else:
            logger.error(f"未知策略: {strategy_name}")
            logger.error("支持的策略: 'ma_crossover', 'rsi_reversion'")
            return df

    @staticmethod
    def _ma_crossover_strategy(df: pd.DataFrame) -> pd.DataFrame:
        """
        均线交叉策略 (MA Crossover)

        参数：
            df (DataFrame): 必须包含 'sma_10' 和 'sma_20' 列
                           (或任意快线/慢线组合)

        返回：
            DataFrame: 原 DataFrame + 'signal' 列

        策略逻辑（向量化）：
            1. 买入信号 (1): 快线从下向上穿越慢线 (Golden Cross)
                - sma_fast(t-1) <= sma_slow(t-1)
                - sma_fast(t) > sma_slow(t)

            2. 卖出信号 (-1): 快线从上向下穿越慢线 (Death Cross)
                - sma_fast(t-1) >= sma_slow(t-1)
                - sma_fast(t) < sma_slow(t)

            3. 持有信号 (0): 其他情况

        算法实现：
            使用 .shift() 获取前一周期值，然后用布尔运算检测交叉
        """
        # 检查必需列（尝试多种命名）
        fast_col = None
        slow_col = None

        # 查找快线（期间较短的 SMA）
        for period in [5, 10, 12, 14, 20]:
            col_name = f'sma_{period}'
            if col_name in df.columns:
                if fast_col is None:
                    fast_col = col_name
                elif slow_col is None:
                    slow_col = col_name
                    break

        # 如果没找到两条 SMA，尝试使用默认
        if fast_col is None or slow_col is None:
            logger.warning("未找到 sma_fast 和 sma_slow 列，尝试使用默认 sma_10 和 sma_20")
            fast_col = 'sma_10'
            slow_col = 'sma_20'

        # 验证列存在
        if fast_col not in df.columns or slow_col not in df.columns:
            logger.error(
                f"MA Crossover 策略需要 {fast_col} 和 {slow_col} 列。"
                "请先调用 TechnicalIndicators.calculate_sma(df, period=10) 和 period=20"
            )
            df['signal'] = 0
            return df

        logger.info(f"使用均线: 快线 = {fast_col}, 慢线 = {slow_col}")

        # 获取当前和前一周期的均线值（向量化）
        fast_current = df[fast_col]
        slow_current = df[slow_col]
        fast_prev = df[fast_col].shift(1)
        slow_prev = df[slow_col].shift(1)

        # 检测金叉 (Golden Cross) - 向量化布尔运算
        golden_cross = (fast_prev <= slow_prev) & (fast_current > slow_current)

        # 检测死叉 (Death Cross) - 向量化布尔运算
        death_cross = (fast_prev >= slow_prev) & (fast_current < slow_current)

        # 生成信号（向量化）
        df['signal'] = 0  # 默认持有
        df.loc[golden_cross, 'signal'] = 1   # 金叉买入
        df.loc[death_cross, 'signal'] = -1   # 死叉卖出

        signal_count = (df['signal'] != 0).sum()
        logger.info(f"MA Crossover 策略生成 {signal_count} 个信号")

        return df

    @staticmethod
    def _rsi_reversion_strategy(df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 超买超卖反转策略 (RSI Reversion)

        参数：
            df (DataFrame): 必须包含 'rsi_14' 列

        返回：
            DataFrame: 原 DataFrame + 'signal' 列

        策略逻辑（向量化）：
            1. 卖出信号 (-1): RSI > 70 (超买区域，预期回落)
            2. 买入信号 (1): RSI < 30 (超卖区域，预期反弹)
            3. 持有信号 (0): 30 <= RSI <= 70 (中性区域)

        算法实现：
            使用 pandas 布尔索引直接赋值信号
        """
        # 检查必需列
        rsi_col = None

        # 查找 RSI 列（尝试多种周期）
        for period in [14, 9, 21]:
            col_name = f'rsi_{period}'
            if col_name in df.columns:
                rsi_col = col_name
                break

        # 如果没找到，使用默认
        if rsi_col is None:
            logger.warning("未找到 rsi 列，尝试使用默认 rsi_14")
            rsi_col = 'rsi_14'

        # 验证列存在
        if rsi_col not in df.columns:
            logger.error(
                f"RSI Reversion 策略需要 {rsi_col} 列。"
                "请先调用 TechnicalIndicators.calculate_rsi(df, period=14)"
            )
            df['signal'] = 0
            return df

        logger.info(f"使用 RSI 指标: {rsi_col}")

        # 定义超买超卖阈值
        OVERBOUGHT = 70
        OVERSOLD = 30

        # 生成信号（向量化）
        df['signal'] = 0  # 默认持有

        # 超买信号：RSI > 70 -> 卖出 (-1)
        df.loc[df[rsi_col] > OVERBOUGHT, 'signal'] = -1

        # 超卖信号：RSI < 30 -> 买入 (1)
        df.loc[df[rsi_col] < OVERSOLD, 'signal'] = 1

        signal_count = (df['signal'] != 0).sum()
        logger.info(f"RSI Reversion 策略生成 {signal_count} 个信号")

        return df


# 便利函数：获取信号引擎实例（无状态，纯静态）
def get_signal_engine() -> SignalEngine:
    """获取 SignalEngine 实例（无状态，纯静态）"""
    return SignalEngine()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建示例数据（模拟已计算指标的 DataFrame）
    test_data = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=100, freq='1h'),
        'close': np.random.uniform(1.08, 1.10, 100),
        'sma_10': np.random.uniform(1.08, 1.10, 100),
        'sma_20': np.random.uniform(1.08, 1.10, 100),
        'rsi_14': np.random.uniform(20, 80, 100)
    })

    # 测试 MA Crossover 策略
    engine = SignalEngine()
    test_data_ma = engine.apply_strategy(test_data.copy(), strategy_name='ma_crossover')
    print("MA Crossover 信号:")
    print(test_data_ma[test_data_ma['signal'] != 0][['time', 'sma_10', 'sma_20', 'signal']].tail())

    # 测试 RSI Reversion 策略
    test_data_rsi = engine.apply_strategy(test_data.copy(), strategy_name='rsi_reversion')
    print("\nRSI Reversion 信号:")
    print(test_data_rsi[test_data_rsi['signal'] != 0][['time', 'rsi_14', 'signal']].tail())
