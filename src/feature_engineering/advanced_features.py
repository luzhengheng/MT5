"""
高级特征工程模块 - 实现 40 维高级特征
包括:
1. Fractional Differentiation (6 维)
2. Rolling Statistics (12 维)
3. Cross-Sectional Rank (6 维)
4. Sentiment Momentum (8 维)
5. Adaptive Window Features (3 维)
6. Cross-Asset Features (5 维)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedFeatures:
    """高级特征计算类"""

    @staticmethod
    def fractional_diff(series: pd.Series, d: float = 0.5, threshold: float = 1e-5) -> pd.Series:
        """
        分数阶差分 (Fractional Differentiation)
        保留记忆性的同时实现平稳化

        来源: "Advances in Financial Machine Learning" by Marcos Lopez de Prado

        Args:
            series: 时间序列
            d: 差分阶数 (0 < d < 1)，d=1 为完全差分，d=0.5 为半差分
            threshold: 权重截断阈值

        Returns:
            分数阶差分后的序列
        """
        # 计算权重
        weights = [1.0]
        k = 1

        # 迭代计算权重直到小于阈值
        while True:
            weight = -weights[-1] * (d - k + 1) / k
            if abs(weight) < threshold:
                break
            weights.append(weight)
            k += 1

        weights = np.array(weights[::-1])  # 反转权重

        # 应用卷积
        result = pd.Series(index=series.index, dtype=float)
        for i in range(len(weights) - 1, len(series)):
            result.iloc[i] = np.dot(weights, series.iloc[i - len(weights) + 1:i + 1])

        return result

    @staticmethod
    def compute_fractional_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 Fractional Differentiation 特征 (6 维)

        特征列表:
        1. frac_diff_close_05: 收盘价 d=0.5 分数差分
        2. frac_diff_close_07: 收盘价 d=0.7 分数差分
        3. frac_diff_volume_05: 成交量 d=0.5 分数差分
        4. frac_diff_returns_05: 收益率 d=0.5 分数差分
        5. frac_diff_volatility_05: 波动率 d=0.5 分数差分
        6. frac_diff_sentiment_05: 情感 d=0.5 分数差分

        Args:
            df: 包含 OHLCV 和情感数据的 DataFrame

        Returns:
            添加了 Fractional Differentiation 特征的 DataFrame
        """
        logger.info("计算 Fractional Differentiation 特征...")

        # 1. 收盘价 d=0.5
        df['frac_diff_close_05'] = AdvancedFeatures.fractional_diff(
            df['close'], d=0.5
        )

        # 2. 收盘价 d=0.7 (更强的差分)
        df['frac_diff_close_07'] = AdvancedFeatures.fractional_diff(
            df['close'], d=0.7
        )

        # 3. 成交量 d=0.5
        df['frac_diff_volume_05'] = AdvancedFeatures.fractional_diff(
            df['volume'], d=0.5
        )

        # 4. 收益率 d=0.5
        returns = df['close'].pct_change()
        df['frac_diff_returns_05'] = AdvancedFeatures.fractional_diff(
            returns, d=0.5
        )

        # 5. 波动率 d=0.5 (使用 20 日滚动标准差)
        volatility = df['close'].pct_change().rolling(window=20).std()
        df['frac_diff_volatility_05'] = AdvancedFeatures.fractional_diff(
            volatility, d=0.5
        )

        # 6. 情感 d=0.5
        if 'sentiment_mean' in df.columns:
            df['frac_diff_sentiment_05'] = AdvancedFeatures.fractional_diff(
                df['sentiment_mean'], d=0.5
            )
        else:
            df['frac_diff_sentiment_05'] = 0.0

        logger.info("Fractional Differentiation 特征计算完成 (6 维)")
        return df

    @staticmethod
    def compute_rolling_statistics(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算滚动统计特征 (12 维)

        特征列表:
        1. roll_skew_20: 20 日收益率偏度
        2. roll_kurt_20: 20 日收益率峰度
        3. roll_skew_60: 60 日收益率偏度
        4. roll_kurt_60: 60 日收益率峰度
        5. roll_autocorr_1: 收益率自相关(lag=1)
        6. roll_autocorr_5: 收益率自相关(lag=5)
        7. roll_max_drawdown_20: 20 日最大回撤
        8. roll_max_drawdown_60: 60 日最大回撤
        9. roll_sharpe_20: 20 日 Sharpe 比率
        10. roll_sortino_20: 20 日 Sortino 比率
        11. roll_calmar_60: 60 日 Calmar 比率
        12. roll_tail_ratio_20: 20 日尾部比率 (95th/5th percentile)

        Args:
            df: DataFrame

        Returns:
            添加了滚动统计特征的 DataFrame
        """
        logger.info("计算 Rolling Statistics 特征...")

        returns = df['close'].pct_change()

        # 1-2. 20 日偏度和峰度
        df['roll_skew_20'] = returns.rolling(window=20).skew()
        df['roll_kurt_20'] = returns.rolling(window=20).kurt()

        # 3-4. 60 日偏度和峰度
        df['roll_skew_60'] = returns.rolling(window=60).skew()
        df['roll_kurt_60'] = returns.rolling(window=60).kurt()

        # 5-6. 自相关
        df['roll_autocorr_1'] = returns.rolling(window=20).apply(
            lambda x: x.autocorr(lag=1) if len(x) > 1 else np.nan
        )
        df['roll_autocorr_5'] = returns.rolling(window=20).apply(
            lambda x: x.autocorr(lag=5) if len(x) > 5 else np.nan
        )

        # 7-8. 最大回撤
        def max_drawdown(prices):
            cumulative = (1 + prices).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return drawdown.min()

        df['roll_max_drawdown_20'] = returns.rolling(window=20).apply(max_drawdown)
        df['roll_max_drawdown_60'] = returns.rolling(window=60).apply(max_drawdown)

        # 9. Sharpe 比率 (假设无风险利率=0)
        df['roll_sharpe_20'] = (
            returns.rolling(window=20).mean() / returns.rolling(window=20).std()
        ) * np.sqrt(252)  # 年化

        # 10. Sortino 比率 (只考虑下行波动)
        def sortino_ratio(rets):
            downside = rets[rets < 0]
            if len(downside) > 0:
                downside_std = downside.std()
                if downside_std > 0:
                    return (rets.mean() / downside_std) * np.sqrt(252)
            return np.nan

        df['roll_sortino_20'] = returns.rolling(window=20).apply(sortino_ratio)

        # 11. Calmar 比率 (收益率 / 最大回撤)
        df['roll_calmar_60'] = (
            returns.rolling(window=60).mean() * 252 /  # 年化收益
            df['roll_max_drawdown_60'].abs()
        )

        # 12. 尾部比率
        def tail_ratio(rets):
            if len(rets) > 0:
                p95 = np.percentile(rets, 95)
                p05 = np.percentile(rets, 5)
                if p05 != 0:
                    return abs(p95 / p05)
            return np.nan

        df['roll_tail_ratio_20'] = returns.rolling(window=20).apply(tail_ratio)

        logger.info("Rolling Statistics 特征计算完成 (12 维)")
        return df

    @staticmethod
    def compute_cross_sectional_rank(df: pd.DataFrame, all_dfs: Dict[str, pd.DataFrame] = None) -> pd.DataFrame:
        """
        计算横截面排名特征 (6 维)
        相对于所有资产的排名

        特征列表:
        1. cs_rank_return_1d: 1 日收益率横截面排名
        2. cs_rank_return_5d: 5 日收益率横截面排名
        3. cs_rank_volatility: 波动率横截面排名
        4. cs_rank_volume: 成交量横截面排名
        5. cs_rank_rsi: RSI 横截面排名
        6. cs_rank_sentiment: 情感横截面排名

        Args:
            df: 当前资产的 DataFrame
            all_dfs: 所有资产的 DataFrame 字典 {symbol: df}

        Returns:
            添加了横截面排名特征的 DataFrame
        """
        logger.info("计算 Cross-Sectional Rank 特征...")

        if all_dfs is None or len(all_dfs) < 2:
            # 如果没有其他资产数据,设置为中位数 0.5
            logger.warning("没有其他资产数据,横截面排名特征设为 0.5")
            df['cs_rank_return_1d'] = 0.5
            df['cs_rank_return_5d'] = 0.5
            df['cs_rank_volatility'] = 0.5
            df['cs_rank_volume'] = 0.5
            df['cs_rank_rsi'] = 0.5
            df['cs_rank_sentiment'] = 0.5
            return df

        # 为每个日期计算横截面排名
        dates = df['date'].unique()

        for date in dates:
            # 收集所有资产在该日期的数据
            cross_section = []
            for symbol, other_df in all_dfs.items():
                date_data = other_df[other_df['date'] == date]
                if not date_data.empty:
                    cross_section.append({
                        'symbol': symbol,
                        'return_1d': date_data['return_1d'].iloc[0] if 'return_1d' in date_data.columns else np.nan,
                        'return_5d': date_data['return_5d'].iloc[0] if 'return_5d' in date_data.columns else np.nan,
                        'volatility': date_data['volatility_20d'].iloc[0] if 'volatility_20d' in date_data.columns else np.nan,
                        'volume': date_data['volume'].iloc[0],
                        'rsi': date_data['rsi_14'].iloc[0] if 'rsi_14' in date_data.columns else np.nan,
                        'sentiment': date_data['sentiment_mean'].iloc[0] if 'sentiment_mean' in date_data.columns else 0,
                    })

            if len(cross_section) > 1:
                cs_df = pd.DataFrame(cross_section)

                # 计算排名 (百分位数)
                current_symbol = df[df['date'] == date]['symbol'].iloc[0] if 'symbol' in df.columns else None

                if current_symbol:
                    for col, feature in [
                        ('return_1d', 'cs_rank_return_1d'),
                        ('return_5d', 'cs_rank_return_5d'),
                        ('volatility', 'cs_rank_volatility'),
                        ('volume', 'cs_rank_volume'),
                        ('rsi', 'cs_rank_rsi'),
                        ('sentiment', 'cs_rank_sentiment'),
                    ]:
                        if col in cs_df.columns:
                            cs_df[feature] = cs_df[col].rank(pct=True)
                            rank_value = cs_df[cs_df['symbol'] == current_symbol][feature].iloc[0] if not cs_df[cs_df['symbol'] == current_symbol].empty else 0.5
                            df.loc[df['date'] == date, feature] = rank_value

        logger.info("Cross-Sectional Rank 特征计算完成 (6 维)")
        return df

    @staticmethod
    def compute_sentiment_momentum(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算情感动量特征 (8 维)

        特征列表:
        1. sentiment_momentum_5d: 5 日情感动量
        2. sentiment_momentum_20d: 20 日情感动量
        3. sentiment_acceleration: 情感加速度 (动量的变化)
        4. sentiment_divergence: 情感-价格背离 (情感上涨但价格下跌)
        5. sentiment_consistency_5d: 5 日情感一致性 (连续正/负的比例)
        6. sentiment_intensity: 情感强度 (绝对值的均值)
        7. sentiment_volatility_20d: 20 日情感波动率
        8. news_frequency_ma20: 20 日新闻频率移动平均

        Args:
            df: DataFrame

        Returns:
            添加了情感动量特征的 DataFrame
        """
        logger.info("计算 Sentiment Momentum 特征...")

        if 'sentiment_mean' not in df.columns:
            logger.warning("没有情感数据,情感动量特征设为 0")
            for feat in ['sentiment_momentum_5d', 'sentiment_momentum_20d',
                        'sentiment_acceleration', 'sentiment_divergence',
                        'sentiment_consistency_5d', 'sentiment_intensity',
                        'sentiment_volatility_20d', 'news_frequency_ma20']:
                df[feat] = 0.0
            return df

        # 1-2. 情感动量
        df['sentiment_momentum_5d'] = df['sentiment_mean'] - df['sentiment_mean'].shift(5)
        df['sentiment_momentum_20d'] = df['sentiment_mean'] - df['sentiment_mean'].shift(20)

        # 3. 情感加速度
        df['sentiment_acceleration'] = df['sentiment_momentum_5d'] - df['sentiment_momentum_5d'].shift(5)

        # 4. 情感-价格背离
        price_momentum = df['close'].pct_change(5)
        sentiment_momentum = df['sentiment_momentum_5d']
        df['sentiment_divergence'] = (
            ((sentiment_momentum > 0) & (price_momentum < 0)).astype(int) -
            ((sentiment_momentum < 0) & (price_momentum > 0)).astype(int)
        )

        # 5. 情感一致性 (5 日窗口内同向比例)
        def consistency(series):
            if len(series) == 0:
                return 0
            positive = (series > 0).sum()
            negative = (series < 0).sum()
            return max(positive, negative) / len(series)

        df['sentiment_consistency_5d'] = df['sentiment_mean'].rolling(window=5).apply(consistency)

        # 6. 情感强度
        df['sentiment_intensity'] = df['sentiment_mean'].abs().rolling(window=20).mean()

        # 7. 情感波动率
        df['sentiment_volatility_20d'] = df['sentiment_mean'].rolling(window=20).std()

        # 8. 新闻频率移动平均
        if 'news_count' in df.columns:
            df['news_frequency_ma20'] = df['news_count'].rolling(window=20).mean()
        else:
            df['news_frequency_ma20'] = 0.0

        logger.info("Sentiment Momentum 特征计算完成 (8 维)")
        return df

    @staticmethod
    def compute_adaptive_window_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算自适应窗口特征 (3 维)
        根据市场波动率动态调整窗口大小

        特征列表:
        1. adaptive_ma: 自适应移动平均 (基于波动率调整窗口)
        2. adaptive_momentum: 自适应动量
        3. adaptive_volatility_ratio: 自适应波动率比率

        Args:
            df: DataFrame

        Returns:
            添加了自适应窗口特征的 DataFrame
        """
        logger.info("计算 Adaptive Window Features...")

        # 计算基准波动率
        returns = df['close'].pct_change()
        baseline_vol = returns.rolling(window=60).std()
        current_vol = returns.rolling(window=20).std()

        # 波动率比率 (当前/基准)
        vol_ratio = current_vol / baseline_vol
        vol_ratio = vol_ratio.fillna(1.0).clip(0.5, 2.0)  # 限制在 0.5-2 倍

        # 1. 自适应移动平均 (高波动时用短窗口,低波动时用长窗口)
        # 窗口: 10 到 50 天
        adaptive_window = (50 - 40 * (vol_ratio - 0.5) / 1.5).clip(10, 50).astype(int)

        df['adaptive_ma'] = np.nan
        for i in range(len(df)):
            if i >= 50:  # 确保有足够数据
                window = adaptive_window.iloc[i]
                df.loc[df.index[i], 'adaptive_ma'] = df['close'].iloc[i-window:i].mean()

        # 2. 自适应动量
        df['adaptive_momentum'] = df['close'] / df['adaptive_ma'] - 1

        # 3. 自适应波动率比率
        df['adaptive_volatility_ratio'] = vol_ratio

        logger.info("Adaptive Window Features 计算完成 (3 维)")
        return df

    @staticmethod
    def compute_cross_asset_features(df: pd.DataFrame, reference_df: pd.DataFrame = None,
                                    reference_symbol: str = 'GSPC.INDX') -> pd.DataFrame:
        """
        计算跨资产特征 (5 维)
        相对于基准资产(如 S&P 500)的特征

        特征列表:
        1. beta_to_market: 相对市场的 Beta (60日)
        2. correlation_to_market: 与市场的相关性 (60日)
        3. relative_strength: 相对强度 (当前资产收益 / 市场收益)
        4. alpha_to_market: 相对市场的 Alpha
        5. tracking_error: 跟踪误差

        Args:
            df: 当前资产的 DataFrame
            reference_df: 基准资产的 DataFrame
            reference_symbol: 基准资产名称

        Returns:
            添加了跨资产特征的 DataFrame
        """
        logger.info("计算 Cross-Asset Features...")

        if reference_df is None or reference_df.empty:
            logger.warning("没有基准资产数据,跨资产特征设为 0")
            df['beta_to_market'] = 0.0
            df['correlation_to_market'] = 0.0
            df['relative_strength'] = 0.0
            df['alpha_to_market'] = 0.0
            df['tracking_error'] = 0.0
            return df

        # 确保日期对齐
        df['date'] = pd.to_datetime(df['date'])
        reference_df['date'] = pd.to_datetime(reference_df['date'])

        # 合并数据
        merged = pd.merge(
            df[['date', 'close']],
            reference_df[['date', 'close']],
            on='date',
            how='left',
            suffixes=('', '_market')
        )

        # 计算收益率
        merged['return'] = merged['close'].pct_change()
        merged['return_market'] = merged['close_market'].pct_change()

        # 1. Beta (60日滚动)
        def rolling_beta(returns, market_returns):
            """计算 Beta"""
            # 去除 NaN
            mask = ~(np.isnan(returns) | np.isnan(market_returns))
            if mask.sum() < 10:
                return np.nan

            returns_clean = returns[mask]
            market_returns_clean = market_returns[mask]

            # 计算协方差和方差
            if len(returns_clean) < 10:
                return np.nan

            covariance = np.cov(returns_clean, market_returns_clean)[0, 1]
            market_variance = np.var(market_returns_clean)

            if market_variance > 0:
                return covariance / market_variance
            return np.nan

        # 计算滚动 Beta
        beta_values = []
        for i in range(len(merged)):
            if i < 60:
                beta_values.append(np.nan)
            else:
                window_returns = merged['return'].iloc[i-60:i].values
                window_market = merged['return_market'].iloc[i-60:i].values
                beta = rolling_beta(window_returns, window_market)
                beta_values.append(beta)

        merged['beta_to_market'] = beta_values

        # 2. 相关性 (60日)
        merged['correlation_to_market'] = merged['return'].rolling(window=60).corr(merged['return_market'])

        # 3. 相对强度 (20日累计收益比)
        merged['relative_strength'] = (
            (1 + merged['return']).rolling(window=20).apply(lambda x: x.prod()) /
            (1 + merged['return_market']).rolling(window=20).apply(lambda x: x.prod())
        )

        # 4. Alpha (收益率 - Beta * 市场收益率)
        merged['alpha_to_market'] = merged['return'] - merged['beta_to_market'] * merged['return_market']

        # 5. 跟踪误差 (60日)
        merged['tracking_error'] = (merged['return'] - merged['return_market']).rolling(window=60).std() * np.sqrt(252)

        # 合并回原 DataFrame
        df['beta_to_market'] = merged['beta_to_market'].values
        df['correlation_to_market'] = merged['correlation_to_market'].values
        df['relative_strength'] = merged['relative_strength'].values
        df['alpha_to_market'] = merged['alpha_to_market'].values
        df['tracking_error'] = merged['tracking_error'].values

        logger.info("Cross-Asset Features 计算完成 (5 维)")
        return df

    @staticmethod
    def compute_all_advanced_features(df: pd.DataFrame, all_dfs: Dict[str, pd.DataFrame] = None,
                                     reference_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        计算所有高级特征 (40 维)

        Args:
            df: 当前资产的 DataFrame
            all_dfs: 所有资产的 DataFrame 字典 (用于横截面特征)
            reference_df: 基准资产的 DataFrame (用于跨资产特征)

        Returns:
            添加了所有高级特征的 DataFrame
        """
        logger.info("开始计算所有高级特征 (40 维)...")

        # 1. Fractional Differentiation (6 维)
        df = AdvancedFeatures.compute_fractional_features(df)

        # 2. Rolling Statistics (12 维)
        df = AdvancedFeatures.compute_rolling_statistics(df)

        # 3. Cross-Sectional Rank (6 维)
        df = AdvancedFeatures.compute_cross_sectional_rank(df, all_dfs)

        # 4. Sentiment Momentum (8 维)
        df = AdvancedFeatures.compute_sentiment_momentum(df)

        # 5. Adaptive Window Features (3 维)
        df = AdvancedFeatures.compute_adaptive_window_features(df)

        # 6. Cross-Asset Features (5 维)
        df = AdvancedFeatures.compute_cross_asset_features(df, reference_df)

        logger.info("所有高级特征计算完成 (40 维) ✓")
        return df


# 测试代码
if __name__ == '__main__':
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')

    test_df = pd.DataFrame({
        'date': dates,
        'symbol': 'TEST',
        'open': 100 + np.cumsum(np.random.randn(len(dates))),
        'high': 102 + np.cumsum(np.random.randn(len(dates))),
        'low': 98 + np.cumsum(np.random.randn(len(dates))),
        'close': 100 + np.cumsum(np.random.randn(len(dates))),
        'volume': np.random.randint(1000000, 10000000, len(dates)),
        'sentiment_mean': np.random.randn(len(dates)) * 0.5,
        'news_count': np.random.randint(0, 10, len(dates)),
    })

    # 添加基础特征
    test_df['return_1d'] = test_df['close'].pct_change()
    test_df['return_5d'] = test_df['close'].pct_change(5)
    test_df['volatility_20d'] = test_df['return_1d'].rolling(20).std()
    test_df['rsi_14'] = 50.0

    print("测试高级特征计算...")
    print("=" * 60)

    # 测试 Fractional Differentiation
    test_df = AdvancedFeatures.compute_fractional_features(test_df)
    print("\nFractional Differentiation 特征:")
    print(test_df[['date', 'frac_diff_close_05', 'frac_diff_close_07']].tail())

    # 测试 Rolling Statistics
    test_df = AdvancedFeatures.compute_rolling_statistics(test_df)
    print("\nRolling Statistics 特征:")
    print(test_df[['date', 'roll_skew_20', 'roll_sharpe_20']].tail())

    # 测试 Sentiment Momentum
    test_df = AdvancedFeatures.compute_sentiment_momentum(test_df)
    print("\nSentiment Momentum 特征:")
    print(test_df[['date', 'sentiment_momentum_5d', 'sentiment_divergence']].tail())

    # 测试 Adaptive Window Features
    test_df = AdvancedFeatures.compute_adaptive_window_features(test_df)
    print("\nAdaptive Window Features:")
    print(test_df[['date', 'adaptive_ma', 'adaptive_momentum']].tail())

    print("\n" + "=" * 60)
    print("高级特征测试完成!")
    print(f"总特征数: {len(test_df.columns)} 列")
