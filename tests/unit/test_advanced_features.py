"""
测试高级特征工程模块
"""

import pytest
import pandas as pd
import numpy as np

from feature_engineering.advanced_features import AdvancedFeatures


@pytest.mark.unit
class TestAdvancedFeatures:
    """高级特征类测试"""

    def test_initialization(self):
        """测试初始化"""
        af = AdvancedFeatures()
        assert af is not None
        assert hasattr(af, 'calculate_fractional_diff')

    def test_fractional_diff(self, sample_price_data):
        """测试分数差分计算"""
        af = AdvancedFeatures()
        df = sample_price_data.copy()

        series = df['close']
        result = af.fractional_diff(series, d=0.5, threshold=0.01)

        assert len(result) == len(series)

        # 前 N 个值应该是 NaN
        assert result.iloc[:10].isna().sum() > 0

        # 后面的值应该不是 NaN
        assert result.iloc[50:].notna().sum() > 0

        # 分数差分应该减少自相关
        # (这里只检查结果存在,不验证统计性质)
        assert result.std() > 0

    def test_fractional_diff_d_values(self, sample_price_data):
        """测试不同 d 值的分数差分"""
        af = AdvancedFeatures()
        series = sample_price_data['close']

        # d=0 应该接近原始序列
        result_d0 = af.fractional_diff(series, d=0.0, threshold=0.01)
        # 注意: d=0 时前几个值可能是 NaN
        pd.testing.assert_series_equal(
            result_d0.iloc[10:],
            series.iloc[10:],
            check_names=False,
            atol=0.1
        )

        # d=1 应该接近一阶差分
        result_d1 = af.fractional_diff(series, d=1.0, threshold=0.01)
        first_diff = series.diff()

        # 检查趋势相似
        corr = result_d1.iloc[20:].corr(first_diff.iloc[20:])
        assert corr > 0.9  # 应该高度相关

    def test_calculate_rolling_statistics(self, sample_features_data):
        """测试滚动统计特征计算"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()

        result = af.calculate_rolling_statistics(df, windows=[20, 60])

        # 检查基本统计特征
        assert 'roll_skew_20' in result.columns
        assert 'roll_kurt_20' in result.columns
        assert 'roll_skew_60' in result.columns
        assert 'roll_kurt_60' in result.columns

        # 检查自相关
        assert 'roll_autocorr_1' in result.columns
        assert 'roll_autocorr_5' in result.columns

        # 检查前 N 个值为 NaN
        assert result['roll_skew_20'].iloc[:19].isna().all()
        assert result['roll_skew_60'].iloc[:59].isna().all()

        # 检查自相关在 -1 到 1 之间
        autocorr_1 = result['roll_autocorr_1'].dropna()
        assert autocorr_1.min() >= -1.0
        assert autocorr_1.max() <= 1.0

    def test_calculate_sentiment_momentum(self, sample_features_data, sample_news_data):
        """测试情感动量特征计算"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()
        news_df = sample_news_data.copy()

        # 合并情感数据
        df = df.merge(
            news_df.groupby('published_date')['sentiment_score'].mean().reset_index(),
            left_on='time',
            right_on='published_date',
            how='left'
        )
        df = df.drop(columns=['published_date'])

        result = af.calculate_sentiment_momentum(df, periods=[5, 20])

        # 检查情感动量特征
        assert 'sentiment_momentum_5d' in result.columns
        assert 'sentiment_momentum_20d' in result.columns
        assert 'sentiment_acceleration' in result.columns

        # 情感背离应该是 -1, 0, 1
        if 'sentiment_divergence' in result.columns:
            divergence = result['sentiment_divergence'].dropna()
            assert set(divergence.unique()).issubset({-1.0, 0.0, 1.0})

    def test_calculate_adaptive_window_features(self, sample_features_data):
        """测试自适应窗口特征计算"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()

        result = af.calculate_adaptive_window_features(
            df, base_window=20, min_window=10, max_window=50
        )

        assert 'adaptive_ma' in result.columns
        assert 'adaptive_momentum' in result.columns
        assert 'adaptive_volatility_ratio' in result.columns

        # 波动率比率应该为正
        vol_ratio = result['adaptive_volatility_ratio'].dropna()
        assert (vol_ratio > 0).all()

        # 波动率比率应该在合理范围
        assert vol_ratio.min() > 0.1
        assert vol_ratio.max() < 5.0

    def test_calculate_cross_sectional_rank(self):
        """测试横截面排名特征计算"""
        af = AdvancedFeatures()

        # 创建多资产数据
        assets_data = {}
        for symbol in ['AAPL', 'MSFT', 'GOOGL']:
            df = pd.DataFrame({
                'time': pd.date_range('2024-01-01', periods=100),
                'close': 100 + np.random.randn(100).cumsum(),
                'volume': np.random.randint(1000000, 10000000, 100),
            })
            assets_data[symbol] = df

        # 测试单个资产
        result = af.calculate_cross_sectional_rank(
            assets_data['AAPL'],
            'AAPL',
            assets_data,
            features=['close', 'volume']
        )

        assert 'rank_close' in result.columns
        assert 'rank_volume' in result.columns

        # 排名应该在 0-1 之间
        rank_close = result['rank_close'].dropna()
        assert rank_close.min() >= 0.0
        assert rank_close.max() <= 1.0

    def test_calculate_cross_asset_features(self, sample_features_data):
        """测试跨资产特征计算"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()

        # 创建基准数据
        benchmark_df = sample_features_data.copy()
        benchmark_df['return'] = benchmark_df['return'] * 0.5  # 不同的收益

        result = af.calculate_cross_asset_features(
            df, benchmark_df, window=60
        )

        assert 'beta_to_market' in result.columns or 'beta' in result.columns
        assert 'alpha' in result.columns or 'correlation' in result.columns

        # Beta 应该在合理范围
        if 'beta_to_market' in result.columns:
            beta = result['beta_to_market'].dropna()
            assert beta.min() > -5.0
            assert beta.max() < 5.0

    def test_calculate_regime_features(self, sample_features_data):
        """测试市场状态特征计算"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()

        result = af.calculate_regime_features(df, window=60)

        # 检查状态相关特征
        assert 'volatility_regime' in result.columns or 'regime' in result.columns

        # 状态应该是离散值
        if 'volatility_regime' in result.columns:
            regime = result['volatility_regime'].dropna()
            assert set(regime.unique()).issubset({0, 1, 2})

    def test_fractional_diff_edge_cases(self):
        """测试分数差分边界情况"""
        af = AdvancedFeatures()

        # 测试常数序列
        const_series = pd.Series([100] * 50)
        result = af.fractional_diff(const_series, d=0.5)
        # 常数序列的差分应该接近 0
        assert result.dropna().abs().max() < 1e-6

        # 测试线性序列
        linear_series = pd.Series(range(50))
        result = af.fractional_diff(linear_series, d=0.5)
        assert result.dropna().notna().all()

    def test_rolling_stats_edge_cases(self):
        """测试滚动统计边界情况"""
        af = AdvancedFeatures()

        # 测试所有相同值
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100),
            'close': [100] * 100,
            'return': [0] * 100,
        })

        result = af.calculate_rolling_statistics(df, windows=[20])

        # 偏度和峰度应该是 NaN 或 0
        skew = result['roll_skew_20'].dropna()
        assert len(skew) == 0 or skew.abs().max() < 1e-6

    def test_calculate_all_advanced_features(self, sample_features_data):
        """测试计算所有高级特征"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()

        result = af.calculate_all_advanced_features(df)

        # 检查包含主要高级特征类别
        expected_features = [
            'frac_diff_close_05',  # 分数差分
            'roll_skew_20',         # 滚动统计
            'adaptive_ma',          # 自适应窗口
        ]

        for feature in expected_features:
            assert feature in result.columns, f"Missing feature: {feature}"

    def test_empty_dataframe(self):
        """测试空 DataFrame"""
        af = AdvancedFeatures()
        df = pd.DataFrame()

        with pytest.raises(Exception):
            af.calculate_all_advanced_features(df)

    def test_insufficient_data(self):
        """测试数据不足的情况"""
        af = AdvancedFeatures()

        # 只有 10 行数据
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=10),
            'close': np.random.randn(10),
            'return': np.random.randn(10),
        })

        result = af.calculate_rolling_statistics(df, windows=[20, 60])

        # 所有 20 天和 60 天特征都应该是 NaN
        assert result['roll_skew_20'].isna().all()
        assert result['roll_skew_60'].isna().all()

    def test_feature_consistency(self, sample_features_data):
        """测试特征计算的一致性"""
        af = AdvancedFeatures()
        df = sample_features_data.copy()

        result1 = af.calculate_rolling_statistics(df, windows=[20])
        result2 = af.calculate_rolling_statistics(df, windows=[20])

        # 检查两次计算结果相同
        pd.testing.assert_frame_equal(result1, result2)
