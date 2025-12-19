"""
测试 DQ Score 计算模块
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from monitoring.dq_score import DQScoreCalculator


@pytest.mark.unit
class TestDQScoreCalculator:
    """DQ Score 计算器测试"""

    def test_initialization(self):
        """测试初始化"""
        calculator = DQScoreCalculator()
        assert calculator is not None
        assert hasattr(calculator, 'weights')
        assert hasattr(calculator, 'calculate_dq_score')

        # 检查默认权重
        assert calculator.weights['completeness'] == 0.30
        assert calculator.weights['accuracy'] == 0.25
        assert calculator.weights['consistency'] == 0.20
        assert calculator.weights['timeliness'] == 0.15
        assert calculator.weights['validity'] == 0.10

    def test_custom_weights(self):
        """测试自定义权重"""
        custom_weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.10,
        }
        calculator = DQScoreCalculator(config={'weights': custom_weights})

        assert calculator.weights['completeness'] == 0.25
        assert calculator.weights['accuracy'] == 0.30

    def test_calculate_completeness_score(self, sample_features_data):
        """测试完整性得分计算"""
        calculator = DQScoreCalculator()
        df = sample_features_data.copy()

        score = calculator.calculate_completeness_score(df)

        # 完整性得分应该在 0-100 之间
        assert 0 <= score <= 100

        # 没有缺失值的数据应该得高分
        assert score > 80

    def test_completeness_with_missing_values(self):
        """测试包含缺失值的完整性计算"""
        calculator = DQScoreCalculator()

        df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4, 5],
            'col2': [1, np.nan, 3, np.nan, 5],
            'col3': [1, 2, 3, 4, 5],
        })

        score = calculator.calculate_completeness_score(df)

        # 有缺失值应该降低得分
        assert score < 100
        assert score > 0

    def test_calculate_accuracy_score(self, sample_features_data):
        """测试准确性得分计算"""
        calculator = DQScoreCalculator()
        df = sample_features_data.copy()

        score = calculator.calculate_accuracy_score(df)

        # 准确性得分应该在 0-100 之间
        assert 0 <= score <= 100

        # 正常数据应该得高分
        assert score > 70

    def test_accuracy_with_inf_values(self):
        """测试包含无穷值的准确性计算"""
        calculator = DQScoreCalculator()

        df = pd.DataFrame({
            'col1': [1, 2, 3, np.inf, 5],
            'col2': [1, 2, -np.inf, 4, 5],
            'col3': [1, 2, 3, 4, 5],
        })

        score = calculator.calculate_accuracy_score(df)

        # 有无穷值应该降低得分
        assert score < 100

    def test_accuracy_with_duplicates(self):
        """测试包含重复记录的准确性计算"""
        calculator = DQScoreCalculator()

        df = pd.DataFrame({
            'col1': [1, 2, 2, 2, 5],  # 有重复
            'col2': [1, 2, 2, 2, 5],
        })

        score = calculator.calculate_accuracy_score(df)

        # 有重复应该降低得分
        assert score < 100

    def test_calculate_consistency_score(self, sample_features_data):
        """测试一致性得分计算"""
        calculator = DQScoreCalculator()
        df = sample_features_data.copy()

        score = calculator.calculate_consistency_score(df)

        # 一致性得分应该在 0-100 之间
        assert 0 <= score <= 100

    def test_consistency_with_time_series(self):
        """测试时间序列一致性"""
        calculator = DQScoreCalculator()

        # 单调递增的时间
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100),
            'value': range(100),
        })

        score = calculator.calculate_consistency_score(df)

        # 单调时间序列应该得高分
        assert score > 70

    def test_consistency_with_non_monotonic_time(self):
        """测试非单调时间序列"""
        calculator = DQScoreCalculator()

        # 非单调时间
        times = pd.date_range('2024-01-01', periods=100)
        shuffled_times = times.to_list()
        np.random.shuffle(shuffled_times)

        df = pd.DataFrame({
            'time': shuffled_times,
            'value': range(100),
        })

        score = calculator.calculate_consistency_score(df)

        # 非单调时间应该降低得分
        assert score < 90

    def test_calculate_timeliness_score(self):
        """测试及时性得分计算"""
        calculator = DQScoreCalculator()

        # 最新数据 (今天)
        df_fresh = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=100),
            'value': range(100),
        })

        score_fresh = calculator.calculate_timeliness_score(df_fresh)

        # 新鲜数据应该得高分
        assert score_fresh >= 90

        # 旧数据 (10天前)
        df_old = pd.DataFrame({
            'time': pd.date_range(end=datetime.now() - timedelta(days=10), periods=100),
            'value': range(100),
        })

        score_old = calculator.calculate_timeliness_score(df_old)

        # 旧数据得分应该更低
        assert score_old < score_fresh

    def test_calculate_validity_score(self, sample_features_data):
        """测试有效性得分计算"""
        calculator = DQScoreCalculator()
        df = sample_features_data.copy()

        score = calculator.calculate_validity_score(df)

        # 有效性得分应该在 0-100 之间
        assert 0 <= score <= 100

    def test_calculate_dq_score(self, sample_features_data):
        """测试综合 DQ Score 计算"""
        calculator = DQScoreCalculator()
        df = sample_features_data.copy()

        result = calculator.calculate_dq_score(df)

        # 检查返回的键
        assert 'total_score' in result
        assert 'grade' in result
        assert 'completeness' in result
        assert 'accuracy' in result
        assert 'consistency' in result
        assert 'timeliness' in result
        assert 'validity' in result

        # 综合得分应该在 0-100 之间
        assert 0 <= result['total_score'] <= 100

        # 等级应该是 A-F
        assert result['grade'] in ['A', 'B', 'C', 'D', 'F']

        # 各维度得分也应该在 0-100 之间
        for key in ['completeness', 'accuracy', 'consistency', 'timeliness', 'validity']:
            assert 0 <= result[key] <= 100

    def test_get_grade(self):
        """测试等级评定"""
        calculator = DQScoreCalculator()

        assert calculator._get_grade(95) == 'A'
        assert calculator._get_grade(85) == 'A'
        assert calculator._get_grade(80) == 'B'
        assert calculator._get_grade(70) == 'B'
        assert calculator._get_grade(65) == 'C'
        assert calculator._get_grade(60) == 'C'
        assert calculator._get_grade(55) == 'D'
        assert calculator._get_grade(50) == 'D'
        assert calculator._get_grade(40) == 'F'
        assert calculator._get_grade(0) == 'F'

    def test_perfect_data_score(self):
        """测试完美数据的得分"""
        calculator = DQScoreCalculator()

        # 创建完美数据
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=100, freq='D'),
            'close': 100 + np.arange(100),
            'volume': np.random.randint(1000000, 10000000, 100),
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
        })

        result = calculator.calculate_dq_score(df)

        # 完美数据应该得高分
        assert result['total_score'] >= 80
        assert result['grade'] in ['A', 'B']

    def test_poor_data_score(self):
        """测试低质量数据的得分"""
        calculator = DQScoreCalculator()

        # 创建低质量数据
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now() - timedelta(days=30), periods=100),
            'close': [np.nan] * 50 + [100] * 50,  # 50% 缺失
            'volume': [np.inf] * 20 + list(range(80)),  # 有无穷值
            'feature1': [1] * 100,  # 全部重复
        })

        result = calculator.calculate_dq_score(df)

        # 低质量数据应该得低分
        assert result['total_score'] < 70

    def test_weighted_score_calculation(self):
        """测试加权得分计算"""
        # 自定义权重,完整性权重最高
        calculator = DQScoreCalculator(config={
            'weights': {
                'completeness': 0.50,  # 完整性 50%
                'accuracy': 0.20,
                'consistency': 0.15,
                'timeliness': 0.10,
                'validity': 0.05,
            }
        })

        # 完整性很差,其他都好
        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=100),
            'col1': [np.nan] * 50 + list(range(50)),  # 50% 缺失
            'col2': range(100),
        })

        result = calculator.calculate_dq_score(df)

        # 由于完整性权重高,总分应该受完整性影响大
        # 完整性差,总分也应该不高
        assert result['total_score'] < 80

    def test_empty_dataframe(self):
        """测试空 DataFrame"""
        calculator = DQScoreCalculator()
        df = pd.DataFrame()

        with pytest.raises(Exception):
            calculator.calculate_dq_score(df)

    def test_single_row(self):
        """测试单行数据"""
        calculator = DQScoreCalculator()

        df = pd.DataFrame({
            'time': [datetime.now()],
            'value': [100],
        })

        result = calculator.calculate_dq_score(df)

        # 单行数据应该能计算,虽然某些维度可能不理想
        assert 0 <= result['total_score'] <= 100

    def test_single_column(self):
        """测试单列数据"""
        calculator = DQScoreCalculator()

        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=100),
        })

        result = calculator.calculate_dq_score(df)

        # 单列数据应该能计算
        assert 0 <= result['total_score'] <= 100

    def test_all_nan_column(self):
        """测试全 NaN 列"""
        calculator = DQScoreCalculator()

        df = pd.DataFrame({
            'time': pd.date_range(end=datetime.now(), periods=100),
            'col1': [np.nan] * 100,
            'col2': range(100),
        })

        result = calculator.calculate_dq_score(df)

        # 有全 NaN 列应该降低完整性得分
        assert result['completeness'] < 90

    def test_score_consistency(self, sample_features_data):
        """测试得分计算的一致性"""
        calculator = DQScoreCalculator()
        df = sample_features_data.copy()

        result1 = calculator.calculate_dq_score(df)
        result2 = calculator.calculate_dq_score(df)

        # 两次计算应该完全相同
        assert result1['total_score'] == result2['total_score']
        assert result1['grade'] == result2['grade']
        for key in ['completeness', 'accuracy', 'consistency', 'timeliness', 'validity']:
            assert result1[key] == result2[key]

    def test_calculate_feature_dq_scores(self, temp_data_lake, sample_features_data):
        """测试批量计算多个资产的 DQ Score"""
        calculator = DQScoreCalculator()

        # 保存测试数据
        features_dir = temp_data_lake / 'processed' / 'features'
        for symbol in ['AAPL', 'MSFT', 'GOOGL']:
            df = sample_features_data.copy()
            df.to_parquet(features_dir / f'{symbol}_features.parquet')

        # 计算所有资产的 DQ Score
        result_df = calculator.calculate_feature_dq_scores(str(features_dir))

        # 检查结果
        assert len(result_df) == 3
        assert 'symbol' in result_df.columns
        assert 'total_score' in result_df.columns
        assert 'grade' in result_df.columns

        # 所有得分应该在合理范围
        assert result_df['total_score'].min() >= 0
        assert result_df['total_score'].max() <= 100
