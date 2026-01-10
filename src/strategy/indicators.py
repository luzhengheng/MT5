#!/usr/bin/env python3
"""
Technical Indicators Library - The Brain
==========================================

提供 TechnicalIndicators 类，将原始 OHLCV 数据转换为可操作的交易信号。

核心原则：
- **严格向量化**: 所有计算使用 pandas/numpy，禁止使用 for 循环
- **链式调用**: 方法返回 DataFrame，支持连续调用
- **输入验证**: 确保输入 DataFrame 包含必需列
- **NaN 处理**: 前 N 个数据点因预热周期存在 NaN（符合预期）

功能：
- calculate_sma(df, period, price_col) - 简单移动平均线
- calculate_ema(df, period, price_col) - 指数移动平均线
- calculate_rsi(df, period, price_col) - 相对强弱指标（0-100）
- calculate_atr(df, period) - 平均真实波幅（动态止损）
- calculate_bollinger_bands(df, period, std_dev) - 布林带（上轨、中轨、下轨）
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    技术指标计算引擎

    所有方法遵循向量化原则，不使用 Python for 循环。
    输入: pandas DataFrame（必须包含 OHLCV 列）
    输出: DataFrame with 新增指标列
    """

    @staticmethod
    def calculate_sma(
        df: pd.DataFrame,
        period: int = 14,
        price_col: str = 'close'
    ) -> pd.DataFrame:
        """
        计算简单移动平均线 (Simple Moving Average)

        参数：
            df (DataFrame): OHLCV 数据，必须包含 price_col 列
            period (int): 周期（默认 14）
            price_col (str): 价格列名（默认 'close'）

        返回：
            DataFrame: 原 DataFrame + 新列 f'sma_{period}'

        算法：
            SMA = (P1 + P2 + ... + Pn) / n
            使用 pandas.rolling().mean() 实现向量化计算

        注意：
            前 period-1 个值为 NaN（预热周期）
        """
        if price_col not in df.columns:
            logger.error(f"列 '{price_col}' 不存在于 DataFrame")
            return df

        col_name = f'sma_{period}'
        df[col_name] = df[price_col].rolling(window=period, min_periods=period).mean()

        logger.info(f"计算 SMA({period}) 完成 - 列名: {col_name}")
        return df

    @staticmethod
    def calculate_ema(
        df: pd.DataFrame,
        period: int = 14,
        price_col: str = 'close'
    ) -> pd.DataFrame:
        """
        计算指数移动平均线 (Exponential Moving Average)

        参数：
            df (DataFrame): OHLCV 数据，必须包含 price_col 列
            period (int): 周期（默认 14）
            price_col (str): 价格列名（默认 'close'）

        返回：
            DataFrame: 原 DataFrame + 新列 f'ema_{period}'

        算法：
            EMA = Price(t) * k + EMA(t-1) * (1-k)
            其中 k = 2 / (period + 1)
            使用 pandas.ewm().mean() 实现向量化计算

        注意：
            EMA 没有严格的预热周期，但初始值使用 SMA 作为种子
        """
        if price_col not in df.columns:
            logger.error(f"列 '{price_col}' 不存在于 DataFrame")
            return df

        col_name = f'ema_{period}'
        df[col_name] = df[price_col].ewm(span=period, adjust=False).mean()

        logger.info(f"计算 EMA({period}) 完成 - 列名: {col_name}")
        return df

    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame,
        period: int = 14,
        price_col: str = 'close'
    ) -> pd.DataFrame:
        """
        计算相对强弱指标 (Relative Strength Index)

        参数：
            df (DataFrame): OHLCV 数据，必须包含 price_col 列
            period (int): 周期（默认 14）
            price_col (str): 价格列名（默认 'close'）

        返回：
            DataFrame: 原 DataFrame + 新列 f'rsi_{period}'

        算法：
            1. 计算价格变化 delta = price(t) - price(t-1)
            2. 分离上涨 (gain) 和下跌 (loss)
            3. 计算平均上涨和平均下跌（使用 EMA）
            4. RS = avg_gain / avg_loss
            5. RSI = 100 - (100 / (1 + RS))

        输出范围：
            0-100（超买 > 70，超卖 < 30）

        注意：
            前 period 个值为 NaN
        """
        if price_col not in df.columns:
            logger.error(f"列 '{price_col}' 不存在于 DataFrame")
            return df

        # 计算价格变化（向量化）
        delta = df[price_col].diff()

        # 分离上涨和下跌（向量化）
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # 计算平均上涨和平均下跌（使用 EMA，向量化）
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        # 计算 RS 和 RSI（向量化，避免除零）
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        col_name = f'rsi_{period}'
        df[col_name] = rsi

        logger.info(f"计算 RSI({period}) 完成 - 列名: {col_name}")
        return df

    @staticmethod
    def calculate_atr(
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """
        计算平均真实波幅 (Average True Range)

        参数：
            df (DataFrame): OHLCV 数据，必须包含 'high', 'low', 'close' 列
            period (int): 周期（默认 14）

        返回：
            DataFrame: 原 DataFrame + 新列 f'atr_{period}'

        算法：
            1. TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
            2. ATR = EMA(TR, period)

        用途：
            动态止损、仓位管理、波动率过滤

        注意：
            前 1 个值（TR）为 NaN，前 period 个值（ATR）为 NaN
        """
        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"列 '{col}' 不存在于 DataFrame")
                return df

        # 计算 True Range（向量化）
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()

        # TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 计算 ATR（使用 EMA，向量化）
        atr = tr.ewm(span=period, adjust=False).mean()

        col_name = f'atr_{period}'
        df[col_name] = atr

        logger.info(f"计算 ATR({period}) 完成 - 列名: {col_name}")
        return df

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        price_col: str = 'close'
    ) -> pd.DataFrame:
        """
        计算布林带 (Bollinger Bands)

        参数：
            df (DataFrame): OHLCV 数据，必须包含 price_col 列
            period (int): 周期（默认 20）
            std_dev (float): 标准差倍数（默认 2.0）
            price_col (str): 价格列名（默认 'close'）

        返回：
            DataFrame: 原 DataFrame + 3 个新列：
                - f'bb_upper_{period}': 上轨
                - f'bb_middle_{period}': 中轨（SMA）
                - f'bb_lower_{period}': 下轨

        算法：
            1. Middle Band = SMA(close, period)
            2. Upper Band = Middle Band + (std_dev * std(close, period))
            3. Lower Band = Middle Band - (std_dev * std(close, period))

        用途：
            超买超卖、波动率突破、均值回归

        注意：
            前 period-1 个值为 NaN
        """
        if price_col not in df.columns:
            logger.error(f"列 '{price_col}' 不存在于 DataFrame")
            return df

        # 计算中轨（SMA，向量化）
        middle = df[price_col].rolling(window=period, min_periods=period).mean()

        # 计算标准差（向量化）
        std = df[price_col].rolling(window=period, min_periods=period).std()

        # 计算上轨和下轨（向量化）
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        # 添加列
        df[f'bb_upper_{period}'] = upper
        df[f'bb_middle_{period}'] = middle
        df[f'bb_lower_{period}'] = lower

        logger.info(
            f"计算 Bollinger Bands({period}, {std_dev}σ) 完成 - "
            f"列名: bb_upper/middle/lower_{period}"
        )
        return df


# 便利函数：获取技术指标实例（虽然是静态方法，但提供统一接口）
def get_technical_indicators() -> TechnicalIndicators:
    """获取 TechnicalIndicators 实例（无状态，纯静态）"""
    return TechnicalIndicators()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建示例数据
    test_data = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=100, freq='1h'),
        'open': np.random.uniform(1.08, 1.10, 100),
        'high': np.random.uniform(1.09, 1.11, 100),
        'low': np.random.uniform(1.07, 1.09, 100),
        'close': np.random.uniform(1.08, 1.10, 100),
        'volume': np.random.randint(100, 1000, 100)
    })

    # 测试所有指标
    indicators = TechnicalIndicators()
    test_data = indicators.calculate_sma(test_data, period=14)
    test_data = indicators.calculate_ema(test_data, period=14)
    test_data = indicators.calculate_rsi(test_data, period=14)
    test_data = indicators.calculate_atr(test_data, period=14)
    test_data = indicators.calculate_bollinger_bands(test_data, period=20)

    print("技术指标测试完成")
    print(f"列: {test_data.columns.tolist()}")
    print(f"\n最后 5 行:\n{test_data.tail()}")
