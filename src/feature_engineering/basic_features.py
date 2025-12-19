"""
基础技术指标特征计算
使用 pandas 和 numpy 实现（避免 ta-lib 依赖）
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BasicFeatures:
    """基础技术指标特征计算器"""

    @staticmethod
    def compute_ema(series: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均（EMA）"""
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def compute_sma(series: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均（SMA）"""
        return series.rolling(window=period).mean()

    @staticmethod
    def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """计算相对强弱指标（RSI）"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算 MACD 指标"""
        ema_fast = BasicFeatures.compute_ema(series, fast)
        ema_slow = BasicFeatures.compute_ema(series, slow)

        macd_line = ema_fast - ema_slow
        signal_line = BasicFeatures.compute_ema(macd_line, signal)
        histogram = macd_line - signal_line

        return pd.DataFrame({
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_hist': histogram
        })

    @staticmethod
    def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算平均真实波幅（ATR）"""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR 是 TR 的移动平均
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def compute_bollinger_bands(series: pd.Series, period: int = 20, std: int = 2) -> pd.DataFrame:
        """计算布林带"""
        sma = BasicFeatures.compute_sma(series, period)
        rolling_std = series.rolling(window=period).std()

        upper = sma + (rolling_std * std)
        lower = sma - (rolling_std * std)

        return pd.DataFrame({
            'bbands_upper': upper,
            'bbands_middle': sma,
            'bbands_lower': lower,
            'bbands_width': (upper - lower) / sma
        })

    @staticmethod
    def compute_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                          k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """计算随机震荡指标（Stochastic）"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()

        return pd.DataFrame({
            'stochastic_k': k,
            'stochastic_d': d
        })

    @staticmethod
    def compute_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算威廉指标（Williams %R）"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r

    @staticmethod
    def compute_roc(series: pd.Series, period: int = 10) -> pd.Series:
        """计算变化率（ROC - Rate of Change）"""
        roc = ((series - series.shift(period)) / series.shift(period)) * 100
        return roc

    @staticmethod
    def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """计算能量潮（OBV - On-Balance Volume）"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    @staticmethod
    def compute_realized_volatility(returns: pd.Series, period: int = 20) -> pd.Series:
        """计算已实现波动率"""
        return returns.rolling(window=period).std() * np.sqrt(252)  # 年化

    @staticmethod
    def compute_returns(close: pd.Series, periods: list = [1, 3, 5, 10, 20]) -> pd.DataFrame:
        """计算多期滞后回报"""
        returns_df = pd.DataFrame()

        for period in periods:
            returns_df[f'return_{period}d'] = close.pct_change(period)

        return returns_df

    @staticmethod
    def compute_all_basic_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有基础特征（30 维）

        Args:
            df: 必须包含 ['open', 'high', 'low', 'close', 'volume'] 列

        Returns:
            添加了基础特征的 DataFrame
        """
        df = df.copy()

        logger.info("计算基础技术指标特征...")

        # 趋势类特征 (10 维)
        df['ema_12'] = BasicFeatures.compute_ema(df['close'], 12)
        df['ema_26'] = BasicFeatures.compute_ema(df['close'], 26)
        df['ema_50'] = BasicFeatures.compute_ema(df['close'], 50)
        df['ema_200'] = BasicFeatures.compute_ema(df['close'], 200)
        df['sma_20'] = BasicFeatures.compute_sma(df['close'], 20)
        df['sma_60'] = BasicFeatures.compute_sma(df['close'], 60)

        df['price_vs_ema200'] = (df['close'] - df['ema_200']) / df['ema_200']
        df['golden_cross'] = (df['ema_50'] > df['ema_200']).astype(int)
        df['death_cross'] = (df['ema_50'] < df['ema_200']).astype(int)
        df['trend_strength'] = (df['ema_12'] - df['ema_200']) / df['ema_200']

        # 动量类特征 (8 维)
        df['rsi_14'] = BasicFeatures.compute_rsi(df['close'], 14)
        macd_df = BasicFeatures.compute_macd(df['close'])
        df = pd.concat([df, macd_df], axis=1)
        df['roc_10'] = BasicFeatures.compute_roc(df['close'], 10)

        stoch_df = BasicFeatures.compute_stochastic(df['high'], df['low'], df['close'])
        df = pd.concat([df, stoch_df], axis=1)

        df['williams_r'] = BasicFeatures.compute_williams_r(df['high'], df['low'], df['close'], 14)

        # 波动类特征 (6 维)
        df['atr_14'] = BasicFeatures.compute_atr(df['high'], df['low'], df['close'], 14)

        bbands_df = BasicFeatures.compute_bollinger_bands(df['close'])
        df = pd.concat([df, bbands_df], axis=1)

        df['return_1d'] = df['close'].pct_change()
        df['realized_volatility_20'] = BasicFeatures.compute_realized_volatility(df['return_1d'], 20)

        # 成交量类特征 (3 维)
        df['volume_sma20'] = BasicFeatures.compute_sma(df['volume'], 20)
        df['volume_ratio'] = df['volume'] / df['volume_sma20']
        df['obv'] = BasicFeatures.compute_obv(df['close'], df['volume'])

        # 滞后回报类特征 (5 维) - return_1d 已计算
        returns_df = BasicFeatures.compute_returns(df['close'], periods=[3, 5, 10, 20])
        df = pd.concat([df, returns_df], axis=1)

        logger.info(f"基础特征计算完成，新增 {len(df.columns) - 6} 个特征")

        return df


def main():
    """测试基础特征计算"""
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    np.random.seed(42)

    test_df = pd.DataFrame({
        'date': dates,
        'open': 100 + np.random.randn(300).cumsum(),
        'high': 101 + np.random.randn(300).cumsum(),
        'low': 99 + np.random.randn(300).cumsum(),
        'close': 100 + np.random.randn(300).cumsum(),
        'volume': np.random.randint(1000000, 10000000, 300)
    })

    print("原始数据:")
    print(test_df.head())
    print(f"\n原始列数: {len(test_df.columns)}")

    # 计算基础特征
    result_df = BasicFeatures.compute_all_basic_features(test_df)

    print(f"\n添加特征后列数: {len(result_df.columns)}")
    print("\n新增特征:")
    new_features = [col for col in result_df.columns if col not in test_df.columns]
    for i, feat in enumerate(new_features, 1):
        print(f"{i:2d}. {feat}")

    print(f"\n特征数据预览:")
    print(result_df[new_features].tail(5))

    # 检查缺失值
    print(f"\n缺失值统计:")
    missing_counts = result_df[new_features].isnull().sum()
    print(missing_counts[missing_counts > 0])

    print(f"\n特征完整率: {(1 - result_df[new_features].isnull().sum().sum() / (len(result_df) * len(new_features))):.2%}")


if __name__ == '__main__':
    main()
