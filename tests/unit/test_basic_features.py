"""
测试基础特征工程模块
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from feature_engineering.basic_features import BasicFeatures


@pytest.mark.unit
class TestBasicFeatures:
    """基础特征类测试"""

    def test_initialization(self):
        """测试初始化"""
        bf = BasicFeatures()
        assert bf is not None
        assert hasattr(bf, 'calculate_returns')

    def test_calculate_returns(self, sample_price_data):
        """测试收益率计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_returns(df)

        # 检查返回列
        assert 'return' in result.columns
        assert 'log_return' in result.columns

        # 检查第一个值为 NaN
        assert pd.isna(result['return'].iloc[0])
        assert pd.isna(result['log_return'].iloc[0])

        # 检查非 NaN 值的合理性
        returns = result['return'].dropna()
        assert returns.abs().max() < 1.0  # 单日收益率不应超过 100%

        # 检查 log return 和 return 的关系
        # log(1 + r) ≈ r for small r
        non_nan_mask = ~result['return'].isna()
        returns_diff = (result.loc[non_nan_mask, 'log_return'] -
                        np.log(1 + result.loc[non_nan_mask, 'return'])).abs()
        assert returns_diff.max() < 1e-10

    def test_calculate_moving_averages(self, sample_price_data):
        """测试移动平均线计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        # 测试 SMA
        result = bf.calculate_sma(df, windows=[5, 20])

        assert 'sma_5' in result.columns
        assert 'sma_20' in result.columns

        # 检查前 N 个值为 NaN
        assert result['sma_5'].iloc[:4].isna().all()
        assert result['sma_20'].iloc[:19].isna().all()

        # 检查非 NaN 值
        assert result['sma_5'].iloc[4:].notna().all()

        # 测试 EMA
        result = bf.calculate_ema(df, spans=[5, 20])

        assert 'ema_5' in result.columns
        assert 'ema_20' in result.columns

        # EMA 应该从第二个值开始有值
        assert result['ema_5'].iloc[1:].notna().all()

    def test_calculate_rsi(self, sample_price_data):
        """测试 RSI 指标计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_rsi(df, period=14)

        assert 'rsi_14' in result.columns

        # RSI 应该在 0-100 范围内
        rsi_values = result['rsi_14'].dropna()
        assert rsi_values.min() >= 0
        assert rsi_values.max() <= 100

        # 检查前 N 个值为 NaN
        assert result['rsi_14'].iloc[:14].isna().sum() > 0

    def test_calculate_macd(self, sample_price_data):
        """测试 MACD 指标计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_macd(df, fast=12, slow=26, signal=9)

        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_hist' in result.columns

        # 检查 MACD 直方图 = MACD - Signal
        non_nan_mask = result['macd_hist'].notna()
        hist_diff = (result.loc[non_nan_mask, 'macd_hist'] -
                     (result.loc[non_nan_mask, 'macd'] -
                      result.loc[non_nan_mask, 'macd_signal'])).abs()
        assert hist_diff.max() < 1e-10

    def test_calculate_bollinger_bands(self, sample_price_data):
        """测试布林带计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_bollinger_bands(df, window=20, num_std=2)

        assert 'bb_middle' in result.columns
        assert 'bb_upper' in result.columns
        assert 'bb_lower' in result.columns
        assert 'bb_width' in result.columns
        assert 'bb_pct' in result.columns

        # 检查上轨 >= 中轨 >= 下轨
        non_nan_mask = result['bb_upper'].notna()
        assert (result.loc[non_nan_mask, 'bb_upper'] >=
                result.loc[non_nan_mask, 'bb_middle']).all()
        assert (result.loc[non_nan_mask, 'bb_middle'] >=
                result.loc[non_nan_mask, 'bb_lower']).all()

        # 检查 BB 宽度为正
        assert (result.loc[non_nan_mask, 'bb_width'] >= 0).all()

        # 检查 BB% 在合理范围 (通常 0-1, 但可能超出)
        bb_pct = result['bb_pct'].dropna()
        assert bb_pct.min() >= -1.0
        assert bb_pct.max() <= 2.0

    def test_calculate_atr(self, sample_price_data):
        """测试 ATR 计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_atr(df, period=14)

        assert 'atr_14' in result.columns

        # ATR 应该为正
        atr_values = result['atr_14'].dropna()
        assert (atr_values > 0).all()

    def test_calculate_volume_features(self, sample_price_data):
        """测试成交量特征计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_volume_features(df)

        assert 'volume_ma_20' in result.columns
        assert 'volume_ratio' in result.columns

        # 成交量移动平均应该为正
        vol_ma = result['volume_ma_20'].dropna()
        assert (vol_ma > 0).all()

        # 成交量比率应该为正
        vol_ratio = result['volume_ratio'].dropna()
        assert (vol_ratio > 0).all()

    def test_calculate_price_features(self, sample_price_data):
        """测试价格特征计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_price_features(df)

        assert 'high_low_ratio' in result.columns
        assert 'close_open_ratio' in result.columns

        # 比率应该为正
        hl_ratio = result['high_low_ratio'].dropna()
        assert (hl_ratio > 0).all()

    def test_calculate_momentum(self, sample_price_data):
        """测试动量指标计算"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_momentum(df, periods=[5, 20])

        assert 'momentum_5' in result.columns
        assert 'momentum_20' in result.columns

        # 检查前 N 个值为 NaN
        assert result['momentum_5'].iloc[:5].isna().all()
        assert result['momentum_20'].iloc[:20].isna().all()

    def test_calculate_all_features(self, sample_price_data):
        """测试计算所有特征"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result = bf.calculate_all_features(df)

        # 检查包含主要特征
        expected_features = [
            'return', 'log_return',
            'ema_5', 'ema_20',
            'sma_5', 'sma_20',
            'rsi_14',
            'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower',
            'atr_14',
        ]

        for feature in expected_features:
            assert feature in result.columns, f"Missing feature: {feature}"

        # 检查原始列仍然存在
        assert 'close' in result.columns
        assert 'volume' in result.columns

    def test_empty_dataframe(self):
        """测试空 DataFrame"""
        bf = BasicFeatures()
        df = pd.DataFrame()

        with pytest.raises(Exception):
            bf.calculate_all_features(df)

    def test_missing_columns(self):
        """测试缺失必需列"""
        bf = BasicFeatures()
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=10),
            'close': np.random.randn(10),
        })

        # 缺少 'open', 'high', 'low', 'volume' 等列
        with pytest.raises(KeyError):
            bf.calculate_all_features(df)

    def test_single_row(self):
        """测试单行数据"""
        bf = BasicFeatures()
        df = pd.DataFrame({
            'time': [datetime(2024, 1, 1)],
            'open': [100],
            'high': [101],
            'low': [99],
            'close': [100.5],
            'volume': [1000000],
            'tick_volume': [10000],
        })

        result = bf.calculate_all_features(df)

        # 大部分特征应该是 NaN (需要多行数据)
        assert result['return'].isna().all()
        assert result['sma_20'].isna().all()

    def test_feature_consistency(self, sample_price_data):
        """测试特征计算的一致性 (多次计算结果相同)"""
        bf = BasicFeatures()
        df = sample_price_data.copy()

        result1 = bf.calculate_all_features(df)
        result2 = bf.calculate_all_features(df)

        # 检查两次计算结果相同
        pd.testing.assert_frame_equal(result1, result2)

    def test_feature_with_nan_input(self):
        """测试输入包含 NaN 的情况"""
        bf = BasicFeatures()

        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100),
            'open': np.random.randn(100),
            'high': np.random.randn(100),
            'low': np.random.randn(100),
            'close': np.random.randn(100),
            'volume': np.random.randint(1000, 10000, 100),
            'tick_volume': np.random.randint(100, 1000, 100),
        })

        # 插入一些 NaN
        df.loc[10:15, 'close'] = np.nan

        result = bf.calculate_all_features(df)

        # 应该仍然能计算特征,虽然有些值是 NaN
        assert result is not None
        assert len(result) == len(df)
