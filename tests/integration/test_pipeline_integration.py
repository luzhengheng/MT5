"""
测试完整数据管道集成
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from feature_engineering.basic_features import BasicFeatures
from feature_engineering.advanced_features import AdvancedFeatures
from feature_engineering.labeling import TripleBarrierLabeling
from monitoring.dq_score import DQScoreCalculator


@pytest.mark.integration
class TestPipelineIntegration:
    """完整数据管道集成测试"""

    def test_basic_to_advanced_features(self, sample_price_data):
        """测试从基础特征到高级特征的流程"""
        # Step 1: 计算基础特征
        bf = BasicFeatures()
        df_basic = bf.calculate_all_features(sample_price_data)

        assert df_basic is not None
        assert len(df_basic) == len(sample_price_data)
        assert 'return' in df_basic.columns
        assert 'ema_5' in df_basic.columns

        # Step 2: 计算高级特征
        af = AdvancedFeatures()
        df_advanced = af.calculate_all_advanced_features(df_basic)

        assert df_advanced is not None
        assert len(df_advanced) == len(df_basic)
        assert 'frac_diff_close_05' in df_advanced.columns
        assert 'roll_skew_20' in df_advanced.columns

        # 确保原始列仍然存在
        assert 'close' in df_advanced.columns
        assert 'return' in df_advanced.columns

    def test_features_to_labels(self, sample_price_data):
        """测试从特征到标签的流程"""
        # Step 1: 计算特征
        bf = BasicFeatures()
        df_features = bf.calculate_all_features(sample_price_data)

        # Step 2: 生成标签
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )
        df_labels = tbl.apply_triple_barrier(df_features)

        assert df_labels is not None
        assert 'label' in df_labels.columns
        assert 'return' in df_labels.columns  # 注意: 可能被覆盖

        # 标签应该是 -1, 0, 1
        labels = df_labels['label'].dropna()
        assert set(labels.unique()).issubset({-1, 0, 1})

    def test_end_to_end_pipeline(self, sample_price_data):
        """测试端到端管道: 价格数据 -> 特征 -> 标签 -> DQ Score"""
        # Step 1: 基础特征
        bf = BasicFeatures()
        df = bf.calculate_all_features(sample_price_data)
        assert 'return' in df.columns

        # Step 2: 高级特征
        af = AdvancedFeatures()
        df = af.calculate_all_advanced_features(df)
        assert 'frac_diff_close_05' in df.columns

        # Step 3: 标签
        tbl = TripleBarrierLabeling(
            upper_barrier=0.02,
            lower_barrier=-0.02,
            max_holding_period=5
        )
        df = tbl.apply_triple_barrier(df)
        assert 'label' in df.columns

        # Step 4: DQ Score
        calculator = DQScoreCalculator()
        dq_result = calculator.calculate_dq_score(df)

        assert dq_result is not None
        assert 0 <= dq_result['total_score'] <= 100
        assert dq_result['grade'] in ['A', 'B', 'C', 'D', 'F']

    def test_multi_asset_pipeline(self, sample_price_data, temp_data_lake):
        """测试多资产管道处理"""
        symbols = ['AAPL', 'MSFT', 'GOOGL']

        # 保存原始价格数据
        raw_dir = temp_data_lake / 'raw' / 'market_data'
        for symbol in symbols:
            df = sample_price_data.copy()
            df.to_parquet(raw_dir / f'{symbol}.parquet')

        # 处理每个资产
        features_dir = temp_data_lake / 'processed' / 'features'
        labels_dir = temp_data_lake / 'processed' / 'labels'

        bf = BasicFeatures()
        af = AdvancedFeatures()
        tbl = TripleBarrierLabeling()

        for symbol in symbols:
            # 读取原始数据
            df = pd.read_parquet(raw_dir / f'{symbol}.parquet')

            # 计算特征
            df = bf.calculate_all_features(df)
            df = af.calculate_all_advanced_features(df)

            # 保存特征
            df.to_parquet(features_dir / f'{symbol}_features.parquet')

            # 生成标签
            df_labels = tbl.apply_triple_barrier(df)

            # 保存标签
            df_labels.to_parquet(labels_dir / f'{symbol}_labels.parquet')

        # 验证所有文件都已创建
        assert len(list(features_dir.glob('*.parquet'))) == 3
        assert len(list(labels_dir.glob('*.parquet'))) == 3

        # 计算所有资产的 DQ Score
        calculator = DQScoreCalculator()
        dq_scores = calculator.calculate_feature_dq_scores(str(features_dir))

        assert len(dq_scores) == 3
        assert (dq_scores['total_score'] >= 0).all()
        assert (dq_scores['total_score'] <= 100).all()

    def test_incremental_processing(self, sample_price_data):
        """测试增量处理"""
        # 初始数据
        initial_data = sample_price_data.iloc[:200].copy()

        # 新数据
        new_data = sample_price_data.iloc[200:].copy()

        # 处理初始数据
        bf = BasicFeatures()
        df_initial = bf.calculate_all_features(initial_data)

        # 处理新数据
        df_new = bf.calculate_all_features(new_data)

        # 合并
        df_combined = pd.concat([df_initial, df_new], ignore_index=True)

        assert len(df_combined) == len(sample_price_data)

    def test_feature_persistence(self, sample_price_data, temp_data_lake):
        """测试特征持久化和加载"""
        # 计算特征
        bf = BasicFeatures()
        af = AdvancedFeatures()

        df = bf.calculate_all_features(sample_price_data)
        df = af.calculate_all_advanced_features(df)

        # 保存
        features_path = temp_data_lake / 'processed' / 'features' / 'TEST_features.parquet'
        df.to_parquet(features_path)

        # 加载
        df_loaded = pd.read_parquet(features_path)

        # 验证
        pd.testing.assert_frame_equal(df, df_loaded)

    def test_error_handling_in_pipeline(self):
        """测试管道中的错误处理"""
        # 创建有问题的数据
        bad_data = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=10),
            'close': [100, 101, np.nan, 103, np.inf, 105, 106, 107, 108, 109],
            'open': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107],
            'volume': [1000000] * 10,
            'tick_volume': [10000] * 10,
        })

        # 基础特征应该能处理 NaN
        bf = BasicFeatures()
        df = bf.calculate_all_features(bad_data)
        assert df is not None

        # DQ Score 应该能检测到问题
        calculator = DQScoreCalculator()
        dq_result = calculator.calculate_dq_score(df)

        # 数据质量得分应该较低
        assert dq_result['total_score'] < 90  # 因为有 NaN 和 inf

    def test_data_quality_feedback_loop(self, sample_price_data):
        """测试数据质量反馈循环"""
        bf = BasicFeatures()
        calculator = DQScoreCalculator()

        # 计算特征
        df = bf.calculate_all_features(sample_price_data)

        # 评估质量
        dq_result = calculator.calculate_dq_score(df)

        # 如果质量不好,进行数据清洗
        if dq_result['total_score'] < 70:
            # 移除 NaN
            df = df.dropna()

            # 重新评估
            dq_result_after = calculator.calculate_dq_score(df)

            # 质量应该有所提升
            assert dq_result_after['total_score'] >= dq_result['total_score']

    def test_concurrent_asset_processing(self, sample_price_data):
        """测试并发处理多个资产 (顺序模拟)"""
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

        bf = BasicFeatures()
        results = {}

        for symbol in symbols:
            # 为每个资产生成略有不同的数据
            df = sample_price_data.copy()
            df['close'] = df['close'] * (1 + np.random.randn() * 0.1)

            # 处理
            df_features = bf.calculate_all_features(df)
            results[symbol] = df_features

        # 验证所有资产都已处理
        assert len(results) == 5
        for symbol in symbols:
            assert 'return' in results[symbol].columns

    def test_feature_versioning(self, sample_price_data, temp_data_lake):
        """测试特征版本控制"""
        bf = BasicFeatures()

        # Version 1: 只有基础特征
        df_v1 = bf.calculate_all_features(sample_price_data)
        v1_path = temp_data_lake / 'processed' / 'features' / 'TEST_features_v1.parquet'
        df_v1.to_parquet(v1_path)

        # Version 2: 基础 + 高级特征
        af = AdvancedFeatures()
        df_v2 = af.calculate_all_advanced_features(df_v1)
        v2_path = temp_data_lake / 'processed' / 'features' / 'TEST_features_v2.parquet'
        df_v2.to_parquet(v2_path)

        # 验证两个版本都存在
        assert v1_path.exists()
        assert v2_path.exists()

        # V2 应该有更多列
        df_v1_loaded = pd.read_parquet(v1_path)
        df_v2_loaded = pd.read_parquet(v2_path)
        assert df_v2_loaded.shape[1] > df_v1_loaded.shape[1]

    def test_label_features_alignment(self, sample_price_data):
        """测试标签和特征的对齐"""
        bf = BasicFeatures()
        tbl = TripleBarrierLabeling()

        # 计算特征
        df_features = bf.calculate_all_features(sample_price_data)

        # 生成标签
        df_labels = tbl.apply_triple_barrier(df_features)

        # 由于标签生成需要 forward data,标签数应该少于特征数
        assert len(df_labels.dropna(subset=['label'])) <= len(df_features)

        # 时间应该对齐
        if 'time' in df_labels.columns:
            assert df_labels['time'].iloc[0] == df_features['time'].iloc[0]

    def test_data_lake_structure(self, temp_data_lake):
        """测试数据湖目录结构"""
        # 验证目录存在
        assert (temp_data_lake / 'raw' / 'market_data').exists()
        assert (temp_data_lake / 'raw' / 'news').exists()
        assert (temp_data_lake / 'processed' / 'features').exists()
        assert (temp_data_lake / 'processed' / 'labels').exists()

    def test_memory_efficiency(self, sample_price_data):
        """测试内存效率 (大数据集)"""
        # 创建大数据集 (重复 10 次)
        large_data = pd.concat([sample_price_data] * 10, ignore_index=True)

        bf = BasicFeatures()

        # 应该能处理大数据集不崩溃
        df = bf.calculate_all_features(large_data)

        assert len(df) == len(large_data)
        assert df is not None


@pytest.mark.integration
@pytest.mark.slow
class TestLongRunningIntegration:
    """长时间运行的集成测试"""

    def test_full_year_processing(self):
        """测试完整一年数据处理"""
        # 生成一年的数据
        dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
        np.random.seed(42)

        df = pd.DataFrame({
            'time': dates,
            'open': 100 + np.random.randn(len(dates)).cumsum(),
            'high': 102 + np.random.randn(len(dates)).cumsum(),
            'low': 98 + np.random.randn(len(dates)).cumsum(),
            'close': 100 + np.random.randn(len(dates)).cumsum(),
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'tick_volume': np.random.randint(10000, 100000, len(dates)),
        })

        # 确保价格合理
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

        # 完整流程
        bf = BasicFeatures()
        af = AdvancedFeatures()
        tbl = TripleBarrierLabeling()

        df = bf.calculate_all_features(df)
        df = af.calculate_all_advanced_features(df)
        df_labels = tbl.apply_triple_barrier(df)

        # 验证
        assert len(df) == 366  # 2024 是闰年
        assert 'label' in df_labels.columns
