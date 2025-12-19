"""
机器学习模型模块单元测试

测试覆盖:
1. PurgedKFold 验证器
2. WalkForwardValidator
3. FeatureClusterer
4. LightGBM 训练器
5. ModelEvaluator
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.models.validation import PurgedKFold, WalkForwardValidator
from src.models.feature_selection import FeatureClusterer
from src.models.trainer import LightGBMTrainer
from src.models.evaluator import ModelEvaluator


@pytest.fixture
def sample_timeseries_data():
    """创建模拟时序数据"""
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    n_samples = len(dates)

    X = pd.DataFrame({
        f'feature_{i}': np.random.randn(n_samples)
        for i in range(10)
    }, index=dates)

    y = pd.Series(
        (X.sum(axis=1) + np.random.randn(n_samples) > 0).astype(int),
        index=dates
    )

    # 模拟事件结束时间 (标签持续 5 天)
    event_ends = pd.Series(
        [dates[min(i + 5, n_samples - 1)] for i in range(n_samples)],
        index=dates
    )

    return X, y, event_ends


class TestPurgedKFold:
    """测试 PurgedKFold 验证器"""

    def test_basic_split(self, sample_timeseries_data):
        """测试基本分割功能"""
        X, y, event_ends = sample_timeseries_data

        pkf = PurgedKFold(n_splits=5, embargo_pct=0.01, purge_overlap=True)
        splits = list(pkf.split(X, y, event_ends))

        # 检查分割数
        assert len(splits) == 5

        # 检查每个分割 (第一个 fold 的训练集可能为空)
        for fold_idx, (train_idx, test_idx) in enumerate(splits):
            if fold_idx > 0:  # 跳过第一个 fold
                assert len(train_idx) > 0
            assert len(test_idx) > 0
            assert len(np.intersect1d(train_idx, test_idx)) == 0  # 无重叠

    def test_without_purging(self, sample_timeseries_data):
        """测试不使用 purging"""
        X, y, _ = sample_timeseries_data

        pkf = PurgedKFold(n_splits=3, purge_overlap=False)
        splits = list(pkf.split(X, y, event_ends=None))

        assert len(splits) == 3


class TestWalkForwardValidator:
    """测试 WalkForward 验证器"""

    def test_basic_split(self, sample_timeseries_data):
        """测试滚动窗口分割"""
        X, y, _ = sample_timeseries_data

        wfv = WalkForwardValidator(
            train_period_days=365,
            test_period_days=90,
            step_days=90
        )

        splits = list(wfv.split(X, y))

        # 应该有多个分割
        assert len(splits) > 0

        # 检查每个分割的大小
        for train_idx, test_idx in splits:
            assert len(train_idx) > 0
            assert len(test_idx) > 0

    def test_get_n_splits(self, sample_timeseries_data):
        """测试分割数计算"""
        X, _, _ = sample_timeseries_data

        wfv = WalkForwardValidator(
            train_period_days=365,
            test_period_days=90,
            step_days=90
        )

        n_splits = wfv.get_n_splits(X)
        assert n_splits > 0


class TestFeatureClusterer:
    """测试特征聚类器"""

    def test_clustering(self):
        """测试特征聚类"""
        np.random.seed(42)
        n_samples = 500

        # 创建高相关特征
        f1 = np.random.randn(n_samples)
        X = pd.DataFrame({
            'feature_1': f1,
            'feature_2': f1 + np.random.randn(n_samples) * 0.1,  # 高度相关
            'feature_3': np.random.randn(n_samples)  # 独立
        })

        clusterer = FeatureClusterer(correlation_threshold=0.7)
        clusterer.fit(X)

        # 应该有 2 个群组 (feature_1+2 一组, feature_3 一组)
        assert len(clusterer.clusters) >= 2

    def test_dendrogram(self, tmp_path):
        """测试树状图生成"""
        X = pd.DataFrame({
            f'feature_{i}': np.random.randn(100)
            for i in range(5)
        })

        clusterer = FeatureClusterer()
        clusterer.fit(X)

        output_path = tmp_path / 'test_dendrogram.png'
        clusterer.plot_dendrogram(X.columns.tolist(), str(output_path))

        assert output_path.exists()


class TestLightGBMTrainer:
    """测试 LightGBM 训练器"""

    def test_train_and_predict(self, sample_timeseries_data):
        """测试训练和预测"""
        X, y, _ = sample_timeseries_data

        # 分割数据
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # 训练
        trainer = LightGBMTrainer(early_stopping_rounds=10, verbose=-1)
        trainer.train(X_train, y_train, X_val, y_val, num_boost_round=50)

        # 预测
        y_pred = trainer.predict(X_val)
        assert len(y_pred) == len(y_val)
        assert set(y_pred).issubset({0, 1})

        # 预测概率
        y_pred_proba = trainer.predict_proba(X_val)
        assert y_pred_proba.shape == (len(y_val), 2)
        assert np.all((y_pred_proba >= 0) & (y_pred_proba <= 1))

    def test_feature_importance(self, sample_timeseries_data):
        """测试特征重要性"""
        X, y, _ = sample_timeseries_data

        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        trainer = LightGBMTrainer(verbose=-1)
        trainer.train(X_train, y_train, X_val, y_val, num_boost_round=50)

        importance = trainer.get_feature_importance()
        assert len(importance) == X.shape[1]
        assert importance.sum() > 0

    def test_save_and_load(self, sample_timeseries_data, tmp_path):
        """测试模型保存和加载"""
        X, y, _ = sample_timeseries_data

        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # 训练
        trainer = LightGBMTrainer(verbose=-1)
        trainer.train(X_train, y_train, X_val, y_val, num_boost_round=50)

        # 保存
        model_path = tmp_path / 'test_model.pkl'
        trainer.save(str(model_path))
        assert model_path.exists()

        # 加载
        loaded_trainer = LightGBMTrainer.load(str(model_path))
        assert loaded_trainer.model is not None

        # 预测结果应该一致
        y_pred_original = trainer.predict(X_val)
        y_pred_loaded = loaded_trainer.predict(X_val)
        np.testing.assert_array_equal(y_pred_original, y_pred_loaded)


class TestModelEvaluator:
    """测试模型评估器"""

    def test_evaluate(self, tmp_path):
        """测试模型评估"""
        np.random.seed(42)
        n_samples = 500

        y_true = pd.Series(np.random.choice([0, 1], n_samples, p=[0.6, 0.4]))
        y_pred_proba = np.clip(y_true + np.random.randn(n_samples) * 0.3, 0, 1)
        y_pred = (y_pred_proba > 0.5).astype(int)

        evaluator = ModelEvaluator(output_dir=str(tmp_path))
        metrics = evaluator.evaluate(y_true, y_pred, y_pred_proba, prefix='test')

        # 检查指标
        assert 'accuracy' in metrics
        assert 'f1_score' in metrics
        assert 'auc_roc' in metrics

        # 检查图表
        assert (tmp_path / 'test_roc_pr_curves.png').exists()
        assert (tmp_path / 'test_confusion_matrix.png').exists()
        assert (tmp_path / 'test_calibration_curve.png').exists()

    def test_generate_report(self):
        """测试报告生成"""
        y_true = pd.Series([0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 0, 0, 1])

        evaluator = ModelEvaluator()
        report = evaluator.generate_report(y_true, y_pred)

        assert isinstance(report, str)
        assert 'precision' in report.lower()
        assert 'recall' in report.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
