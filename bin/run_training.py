#!/usr/bin/env python3
"""
机器学习训练主脚本

整合 #009 工单的所有组件:
1. 数据加载与特征工程
2. 特征聚类与选择
3. PurgedKFold 验证
4. Optuna 超参数优化
5. 模型训练与评估
6. SHAP 分析

用法:
    python bin/run_training.py --mode train --use-optuna --n-trials 50
    python bin/run_training.py --mode eval --model-path outputs/models/best_model.pkl
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from src.models.validation import PurgedKFold, WalkForwardValidator
from src.models.feature_selection import FeatureClusterer, MDFeatureImportance
from src.models.trainer import LightGBMTrainer, OptunaOptimizer
from src.models.evaluator import ModelEvaluator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLPipeline:
    """
    机器学习训练管道

    整合所有组件,提供端到端的训练流程
    """

    def __init__(
        self,
        data_path: str,
        output_dir: str = '/opt/mt5-crs/outputs',
        use_purged_kfold: bool = True,
        use_feature_clustering: bool = True
    ):
        """
        Args:
            data_path: 特征数据路径 (Parquet 格式)
            output_dir: 输出目录
            use_purged_kfold: 是否使用 PurgedKFold
            use_feature_clustering: 是否使用特征聚类
        """
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.use_purged_kfold = use_purged_kfold
        self.use_feature_clustering = use_feature_clustering

        self.model_dir = self.output_dir / 'models'
        self.plot_dir = self.output_dir / 'plots'
        self.model_dir.mkdir(exist_ok=True)
        self.plot_dir.mkdir(exist_ok=True)

        self.data = None
        self.features = None
        self.selected_features = None

    def load_data(self):
        """加载特征数据"""
        logger.info(f"加载数据: {self.data_path}")

        if not Path(self.data_path).exists():
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")

        self.data = pd.read_parquet(self.data_path)
        logger.info(f"数据加载完成: {self.data.shape}")

        # 检查必要的列
        required_cols = ['label', 'sample_weight']
        for col in required_cols:
            if col not in self.data.columns:
                raise ValueError(f"缺少必要的列: {col}")

        # 确保索引是日期类型
        if not isinstance(self.data.index, pd.DatetimeIndex):
            if 'date' in self.data.columns:
                self.data['date'] = pd.to_datetime(self.data['date'])
                self.data.set_index('date', inplace=True)
            else:
                raise ValueError("数据必须有日期索引或 'date' 列")

        logger.info(f"数据时间范围: {self.data.index.min()} 至 {self.data.index.max()}")

        # 排除非特征列
        exclude_cols = [
            'label', 'sample_weight', 'symbol',
            'barrier_touched', 'holding_period', 'event_end_time',
            'close', 'open', 'high', 'low', 'volume'  # 排除原始价格
        ]

        self.features = [
            col for col in self.data.columns
            if col not in exclude_cols and self.data[col].dtype in ['float64', 'int64']
        ]

        logger.info(f"特征数量: {len(self.features)}")
        logger.info(f"标签分布: \n{self.data['label'].value_counts()}")

    def select_features(self):
        """特征聚类与选择"""
        if not self.use_feature_clustering:
            self.selected_features = self.features
            return

        logger.info("=" * 80)
        logger.info("特征聚类与选择")
        logger.info("=" * 80)

        X = self.data[self.features].fillna(0)

        # 特征聚类
        clusterer = FeatureClusterer(correlation_threshold=0.7)
        clusterer.fit(X)

        # 绘制树状图
        clusterer.plot_dendrogram(
            self.features,
            output_path=str(self.plot_dir / 'feature_dendrogram.png')
        )

        # 简单选择: 每组取第一个特征 (后续可用 MDA 优化)
        self.selected_features = []
        for cluster_id, features in clusterer.clusters.items():
            self.selected_features.append(features[0])

        logger.info(f"特征选择完成: {len(self.features)} -> {len(self.selected_features)}")

    def train_with_optuna(
        self,
        n_trials: int = 50,
        metric: str = 'f1'
    ) -> LightGBMTrainer:
        """使用 Optuna 优化超参数"""
        logger.info("=" * 80)
        logger.info(f"Optuna 超参数优化 ({n_trials} 次试验)")
        logger.info("=" * 80)

        # 准备数据
        X = self.data[self.selected_features].fillna(0)
        y = self.data['label']
        sample_weight = self.data['sample_weight']

        # 简单时间分割 (80% 训练, 20% 验证)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        sw_train, sw_val = sample_weight.iloc[:split_idx], sample_weight.iloc[split_idx:]

        # Optuna 优化
        optimizer = OptunaOptimizer(n_trials=n_trials, direction='maximize')
        best_params = optimizer.optimize(
            X_train, y_train, X_val, y_val,
            sw_train, sw_val, metric=metric
        )

        # 保存优化历史
        optimizer.save_study(str(self.output_dir / 'optuna_study.csv'))

        # 使用最佳参数训练最终模型
        logger.info("使用最佳参数训练最终模型...")
        trainer = LightGBMTrainer(params=best_params, early_stopping_rounds=50)
        trainer.train(
            X_train, y_train, X_val, y_val,
            sw_train, sw_val, num_boost_round=1000
        )

        return trainer

    def train_with_purged_kfold(
        self,
        params: dict = None,
        n_splits: int = 5
    ) -> LightGBMTrainer:
        """使用 PurgedKFold 训练"""
        logger.info("=" * 80)
        logger.info(f"PurgedKFold 训练 ({n_splits} 折)")
        logger.info("=" * 80)

        # 准备数据
        X = self.data[self.selected_features].fillna(0)
        y = self.data['label']
        sample_weight = self.data['sample_weight']

        # 获取事件结束时间
        if 'event_end_time' in self.data.columns:
            event_ends = pd.to_datetime(self.data['event_end_time'])
        else:
            logger.warning("未找到 'event_end_time',假设每个样本独立")
            event_ends = None

        # PurgedKFold
        pkf = PurgedKFold(n_splits=n_splits, embargo_pct=0.01, purge_overlap=True)

        # K-Fold 训练
        fold_metrics = []
        best_model = None
        best_f1 = 0

        for fold, (train_idx, val_idx) in enumerate(pkf.split(X, y, event_ends), 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Fold {fold}/{n_splits}")
            logger.info(f"{'='*80}")

            X_train = X.iloc[train_idx]
            X_val = X.iloc[val_idx]
            y_train = y.iloc[train_idx]
            y_val = y.iloc[val_idx]
            sw_train = sample_weight.iloc[train_idx]
            sw_val = sample_weight.iloc[val_idx]

            # 训练模型
            trainer = LightGBMTrainer(params=params, early_stopping_rounds=30, verbose=-1)
            trainer.train(
                X_train, y_train, X_val, y_val,
                sw_train, sw_val, num_boost_round=500
            )

            # 评估
            y_pred = trainer.predict(X_val)
            y_pred_proba = trainer.predict_proba(X_val)[:, 1]

            from sklearn.metrics import f1_score
            fold_f1 = f1_score(y_val, y_pred, average='weighted')
            fold_metrics.append(fold_f1)

            logger.info(f"Fold {fold} F1-Score: {fold_f1:.4f}")

            # 保存最佳模型
            if fold_f1 > best_f1:
                best_f1 = fold_f1
                best_model = trainer

        logger.info(f"\n平均 F1-Score: {np.mean(fold_metrics):.4f} ± {np.std(fold_metrics):.4f}")

        return best_model

    def evaluate_model(
        self,
        trainer: LightGBMTrainer,
        prefix: str = 'final'
    ):
        """评估模型"""
        logger.info("=" * 80)
        logger.info("模型评估")
        logger.info("=" * 80)

        # 准备测试集 (最后 20% 数据)
        X = self.data[self.selected_features].fillna(0)
        y = self.data['label']

        split_idx = int(len(X) * 0.8)
        X_test = X.iloc[split_idx:]
        y_test = y.iloc[split_idx:]

        # 预测
        y_pred = trainer.predict(X_test)
        y_pred_proba = trainer.predict_proba(X_test)[:, 1]

        # 评估
        evaluator = ModelEvaluator(output_dir=str(self.plot_dir))
        metrics = evaluator.evaluate(y_test, y_pred, y_pred_proba, prefix=prefix)

        # SHAP 分析 (可选,耗时较长)
        logger.info("\n计算 SHAP 值...")
        try:
            evaluator.plot_shap_summary(
                trainer.model,
                X_test.sample(min(1000, len(X_test))),  # 最多 1000 样本
                prefix=prefix
            )
        except Exception as e:
            logger.warning(f"SHAP 分析失败: {e}")

        # 特征重要性
        importance = trainer.get_feature_importance()
        importance_df = pd.DataFrame({
            'feature': importance.index,
            'importance': importance.values
        })
        importance_df.to_csv(self.output_dir / 'feature_importance.csv', index=False)
        logger.info(f"\n特征重要性已保存: {self.output_dir / 'feature_importance.csv'}")

        return metrics

    def save_model(self, trainer: LightGBMTrainer, model_name: str = 'best_model'):
        """保存模型"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = self.model_dir / f'{model_name}_{timestamp}.pkl'

        metadata = {
            'features': self.selected_features,
            'n_features': len(self.selected_features),
            'training_date': timestamp,
            'data_shape': self.data.shape
        }

        trainer.save(str(model_path), metadata=metadata)
        logger.info(f"模型已保存: {model_path}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MT5-CRS 机器学习训练脚本')

    parser.add_argument(
        '--mode', type=str, default='train',
        choices=['train', 'optuna', 'eval'],
        help='运行模式: train (PurgedKFold训练), optuna (超参数优化), eval (仅评估)'
    )
    parser.add_argument(
        '--data-path', type=str,
        default='/opt/mt5-crs/data/features/combined_features.parquet',
        help='特征数据路径'
    )
    parser.add_argument(
        '--output-dir', type=str,
        default='/opt/mt5-crs/outputs',
        help='输出目录'
    )
    parser.add_argument(
        '--n-trials', type=int, default=50,
        help='Optuna 试验次数'
    )
    parser.add_argument(
        '--n-splits', type=int, default=5,
        help='PurgedKFold 分割数'
    )
    parser.add_argument(
        '--no-feature-clustering', action='store_true',
        help='禁用特征聚类'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    logger.info("=" * 80)
    logger.info("MT5-CRS 机器学习训练管道")
    logger.info("工单 #009: 机器学习预测引擎与高级验证体系")
    logger.info("=" * 80)

    # 创建管道
    pipeline = MLPipeline(
        data_path=args.data_path,
        output_dir=args.output_dir,
        use_purged_kfold=True,
        use_feature_clustering=not args.no_feature_clustering
    )

    # 加载数据
    pipeline.load_data()

    # 特征选择
    pipeline.select_features()

    # 训练模式
    if args.mode == 'optuna':
        trainer = pipeline.train_with_optuna(n_trials=args.n_trials)
    elif args.mode == 'train':
        trainer = pipeline.train_with_purged_kfold(n_splits=args.n_splits)
    else:
        raise ValueError(f"不支持的模式: {args.mode}")

    # 评估模型
    metrics = pipeline.evaluate_model(trainer)

    # 保存模型
    pipeline.save_model(trainer)

    logger.info("=" * 80)
    logger.info("训练完成! 🎉")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as e:
        logger.error(f"数据文件不存在: {e}")
        logger.info("\n提示: 请先运行特征工程生成数据:")
        logger.info("  python -m src.feature_engineering.feature_engineer")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"训练失败: {e}")
        sys.exit(1)
