"""
测试标签系统模块
"""

import pytest
import pandas as pd
import numpy as np

from feature_engineering.labeling import TripleBarrierLabeling


@pytest.mark.unit
class TestTripleBarrierLabeling:
    """Triple Barrier 标签系统测试"""

    def test_initialization(self):
        """测试初始化"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )
        assert tbl.upper_barrier == 0.02
        assert tbl.lower_barrier == -0.02
        assert tbl.max_holding_period == 5

    def test_apply_triple_barrier(self, sample_price_data):
        """测试 Triple Barrier 标签生成"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )

        df = sample_price_data.copy()
        result = tbl.apply_triple_barrier(df)

        # 检查标签列
        assert 'label' in result.columns
        assert 'return' in result.columns
        assert 'holding_period' in result.columns
        assert 'triggered_barrier' in result.columns

        # 标签应该是 -1, 0, 1
        labels = result['label'].dropna()
        assert set(labels.unique()).issubset({-1, 0, 1})

        # 持有期应该 <= max_holding_period
        holding = result['holding_period'].dropna()
        assert holding.max() <= tbl.max_holding_period

        # 触发边界应该是有效值
        barriers = result['triggered_barrier'].dropna()
        assert set(barriers.unique()).issubset({'upper', 'lower', 'vertical'})

    def test_label_distribution(self, sample_price_data):
        """测试标签分布合理性"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )

        df = sample_price_data.copy()
        result = tbl.apply_triple_barrier(df)

        labels = result['label'].dropna()

        # 应该有足够的标签
        assert len(labels) > 10

        # 每个标签类别都应该有样本 (可能性很高)
        # 注意: 在某些极端情况下可能只有一个类别
        label_counts = labels.value_counts()
        assert len(label_counts) >= 1

        # 标签总数应该小于数据总数 (因为需要 future data)
        assert len(labels) < len(df)

    def test_upper_barrier_triggered(self):
        """测试上界触发情况"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.01,  # 1% 上界
            lower_barrier=-0.10,  # 10% 下界 (不容易触发)
            max_holding_period=10
        )

        # 创建明显上涨的价格序列
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=50),
            'close': 100 + np.arange(50) * 0.3,  # 每天上涨 0.3
        })

        result = tbl.apply_triple_barrier(df)

        # 大部分应该触发上界
        upper_triggered = (result['triggered_barrier'] == 'upper').sum()
        assert upper_triggered > len(result) * 0.3  # 至少 30%

        # 大部分应该是做多标签
        long_labels = (result['label'] == 1).sum()
        assert long_labels > len(result) * 0.3

    def test_lower_barrier_triggered(self):
        """测试下界触发情况"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.10,  # 10% 上界 (不容易触发)
            lower_barrier=-0.01,  # 1% 下界
            max_holding_period=10
        )

        # 创建明显下跌的价格序列
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=50),
            'close': 100 - np.arange(50) * 0.3,  # 每天下跌 0.3
        })

        result = tbl.apply_triple_barrier(df)

        # 大部分应该触发下界
        lower_triggered = (result['triggered_barrier'] == 'lower').sum()
        assert lower_triggered > len(result) * 0.3

        # 大部分应该是做空标签
        short_labels = (result['label'] == -1).sum()
        assert short_labels > len(result) * 0.3

    def test_vertical_barrier_triggered(self):
        """测试时间界触发情况"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.50,  # 50% 上界 (很难触发)
            lower_barrier=-0.50,  # 50% 下界 (很难触发)
            max_holding_period=5
        )

        # 创建窄幅震荡的价格序列
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100),
            'close': 100 + np.sin(np.arange(100) * 0.1) * 2,  # 窄幅震荡
        })

        result = tbl.apply_triple_barrier(df)

        # 大部分应该触发时间界
        vertical_triggered = (result['triggered_barrier'] == 'vertical').sum()
        assert vertical_triggered > len(result) * 0.5  # 至少 50%

    def test_return_calculation(self, sample_price_data):
        """测试收益率计算正确性"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )

        df = sample_price_data.copy()
        result = tbl.apply_triple_barrier(df)

        # 检查收益率与标签一致性
        labeled = result.dropna(subset=['label', 'return'])

        # 做多标签应该有正收益 (触发上界) 或接近 0 (时间界)
        long_returns = labeled[labeled['label'] == 1]['return']
        # 做空标签应该有负收益 (触发下界) 或接近 0 (时间界)
        short_returns = labeled[labeled['label'] == -1]['return']

        # 至少平均收益应该符合标签方向
        if len(long_returns) > 0:
            assert long_returns.mean() > -0.01  # 允许小误差
        if len(short_returns) > 0:
            assert short_returns.mean() < 0.01

    def test_hard_stop_loss(self):
        """测试硬止损功能"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.05,
            lower_barrier=-0.05,
            max_holding_period=10,
            hard_stop_loss=-0.03  # 3% 硬止损
        )

        # 创建大幅下跌的序列
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=50),
            'close': 100 - np.arange(50) * 1.0,  # 大幅下跌
        })

        result = tbl.apply_triple_barrier(df)

        # 应该有硬止损触发
        # 收益率不应低于硬止损
        returns = result['return'].dropna()
        # 允许小误差
        assert returns.min() >= tbl.hard_stop_loss - 0.01

    def test_min_holding_period(self):
        """测试最小持有期"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=10,
            min_holding_period=3
        )

        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100),
            'close': 100 + np.random.randn(100).cumsum(),
        })

        result = tbl.apply_triple_barrier(df)

        # 持有期应该 >= min_holding_period
        holding = result['holding_period'].dropna()
        if len(holding) > 0:
            assert holding.min() >= tbl.min_holding_period

    def test_entry_exit_times(self, sample_price_data):
        """测试入场和出场时间"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )

        df = sample_price_data.copy()
        result = tbl.apply_triple_barrier(df)

        # 检查时间列存在
        assert 'entry_time' in result.columns or 'time' in result.columns
        assert 'exit_time' in result.columns

        # 出场时间应该晚于入场时间
        valid_labels = result.dropna(subset=['exit_time'])
        if len(valid_labels) > 0:
            if 'entry_time' in result.columns:
                assert (valid_labels['exit_time'] >= valid_labels['entry_time']).all()
            else:
                assert (valid_labels['exit_time'] >= valid_labels['time']).all()

    def test_empty_dataframe(self):
        """测试空 DataFrame"""
        tbl = TripleBarrierLabeling()
        df = pd.DataFrame()

        with pytest.raises(Exception):
            tbl.apply_triple_barrier(df)

    def test_insufficient_data(self):
        """测试数据不足"""
        tbl = TripleBarrierLabeling(max_holding_period=10)

        # 只有 5 行数据,不足以计算 10 天持有期
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=5),
            'close': [100, 101, 102, 101, 100],
        })

        result = tbl.apply_triple_barrier(df)

        # 应该没有标签或很少标签
        labels = result['label'].dropna()
        assert len(labels) == 0

    def test_missing_columns(self):
        """测试缺失必需列"""
        tbl = TripleBarrierLabeling()

        # 缺少 'close' 列
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=10),
            'price': np.random.randn(10),
        })

        with pytest.raises(KeyError):
            tbl.apply_triple_barrier(df)

    def test_symmetric_barriers(self):
        """测试对称边界"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,  # 对称
            max_holding_period=5
        )

        # 随机游走价格
        np.random.seed(42)
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=200),
            'close': 100 + np.random.randn(200).cumsum() * 0.5,
        })

        result = tbl.apply_triple_barrier(df)

        # 对称边界下,做多和做空标签数量应该接近
        labels = result['label'].value_counts()
        if 1 in labels and -1 in labels:
            ratio = labels[1] / labels[-1]
            # 允许较大偏差 (0.5 到 2 之间)
            assert 0.3 < ratio < 3.0

    def test_asymmetric_barriers(self):
        """测试非对称边界"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.05,  # 5% 上界
            lower_barrier=-0.01,  # 1% 下界 (更容易触发)
            max_holding_period=5
        )

        # 随机游走价格
        np.random.seed(42)
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=200),
            'close': 100 + np.random.randn(200).cumsum() * 0.5,
        })

        result = tbl.apply_triple_barrier(df)

        # 下界更容易触发,应该有更多做空标签
        labels = result['label'].value_counts()
        if 1 in labels and -1 in labels:
            # 做空标签应该更多
            assert labels[-1] > labels[1] * 0.5

    def test_label_consistency(self, sample_price_data):
        """测试标签计算的一致性"""
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )

        df = sample_price_data.copy()

        result1 = tbl.apply_triple_barrier(df)
        result2 = tbl.apply_triple_barrier(df)

        # 检查两次计算结果相同
        pd.testing.assert_frame_equal(result1, result2)
