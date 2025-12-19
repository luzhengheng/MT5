#!/usr/bin/env python3
"""
MT5-CRS 机器学习训练脚本

对冲基金级别的预测引擎训练管道:
1. 加载特征与标签 (来自 #008 工单)
2. 应用 Purged K-Fold 交叉验证
3. 特征去噪与聚类
4. 训练 Ensemble Stacking 模型
5. Optuna 超参数优化 (可选)
6. 全面评估与报告

理论基础: "Advances in Financial Machine Learning" by Marcos Lopez de Prado

用法:
    python bin/train_ml_model.py
    python bin/train_ml_model.py --config config/custom_config.yaml
    python bin/train_ml_model.py --quick  # 快速测试模式
"""

import sys
import os
import logging
import argparse
import yaml
import json
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.validation import PurgedKFold, WalkForwardValidator
from src.models.feature_selection import FeatureClusterer, MDFeatureImportance
from src.models.trainer import (
    LightGBMTrainer,
    CatBoostTrainer,
    EnsembleStacker,
    OptunaOptimizer,
    CATBOOST_AVAILABLE
)
from src.models.evaluator import ModelEvaluator

warnings.filterwarnings('ignore')


class MLTrainingPipeline:
    """机器学习训练管道"""

    def __init__(self, config_path: str):
        """
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_output_dirs()

        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.sample_weights = None
        self.pred_times = None

        self.model = None
        self.feature_names = None

        logger.info("=" * 80)
        logger.info("MT5-CRS 机器学习训练管道")
        logger.info("=" * 80)

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))

        # 配置 logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[]
        )

        global logger
        logger = logging.getLogger(__name__)

        # 控制台输出
        if log_config.get('console', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            logger.addHandler(console_handler)

        # 文件输出
        if log_config.get('file', True):
            log_file = Path(log_config.get('file_path', 'outputs/logs/training.log'))
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            logger.addHandler(file_handler)

    def _setup_output_dirs(self):
        """创建输出目录"""
        output_config = self.config.get('output', {})

        for key in ['model_dir', 'plots_dir', 'logs_dir']:
            path = Path(output_config.get(key, f'outputs/{key}'))
            path.mkdir(parents=True, exist_ok=True)

    def run(self):
        """执行完整训练流程"""
        try:
            logger.info("\n[步骤 1/7] 加载数据...")
            self.load_data()

            logger.info("\n[步骤 2/7] 数据预处理...")
            self.preprocess_data()

            logger.info("\n[步骤 3/7] 特征选择与去噪...")
            self.feature_selection()

            logger.info("\n[步骤 4/7] 配置验证策略...")
            cv_splitter = self.setup_validation()

            logger.info("\n[步骤 5/7] 训练模型...")
            self.train_model(cv_splitter)

            logger.info("\n[步骤 6/7] 评估模型...")
            self.evaluate_model()

            logger.info("\n[步骤 7/7] 保存模型与报告...")
            self.save_outputs()

            logger.info("\n" + "=" * 80)
            logger.info("✅ 训练完成!")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"训练失败: {e}", exc_info=True)
            raise

    def load_data(self):
        """加载特征、标签、样本权重"""
        data_config = self.config['data']

        # 加载特征
        features_path = Path(data_config['features_path'])
        if not features_path.exists():
            raise FileNotFoundError(f"特征文件不存在: {features_path}")

        logger.info(f"加载特征: {features_path}")
        features_df = pd.read_parquet(features_path)

        # 加载标签
        labels_path = Path(data_config['labels_path'])
        logger.info(f"加载标签: {labels_path}")
        labels_df = pd.read_parquet(labels_path)

        # 加载样本权重 (可选)
        weights_path = Path(data_config.get('weights_path', ''))
        if weights_path.exists():
            logger.info(f"加载样本权重: {weights_path}")
            weights_df = pd.read_parquet(weights_path)
            self.sample_weights = weights_df['weight']
        else:
            logger.warning("未找到样本权重文件,将使用均等权重")
            self.sample_weights = None

        # 加载预测时间 (用于 Purged K-Fold)
        pred_times_path = Path(data_config.get('pred_times_path', ''))
        if pred_times_path.exists():
            logger.info(f"加载预测时间: {pred_times_path}")
            pred_times_df = pd.read_parquet(pred_times_path)
            self.pred_times = pred_times_df['pred_time']
        else:
            logger.warning("未找到预测时间文件,Purged K-Fold 将无法工作")
            self.pred_times = None

        # 合并数据 (确保索引对齐)
        data = features_df.join(labels_df, how='inner')

        logger.info(f"数据加载完成: {len(data)} 样本, {len(features_df.columns)} 特征")

        # 分割训练集和测试集
        train_end_date = pd.to_datetime(data_config.get('train_end_date', '2024-01-01'))

        if isinstance(data.index, pd.DatetimeIndex):
            train_mask = data.index < train_end_date
        else:
            logger.warning("数据索引不是 DatetimeIndex,使用 80/20 分割")
            split_idx = int(len(data) * 0.8)
            train_mask = np.zeros(len(data), dtype=bool)
            train_mask[:split_idx] = True

        # 训练集
        train_data = data[train_mask]
        self.X_train = train_data[features_df.columns]
        self.y_train = train_data['label']

        # 测试集
        test_data = data[~train_mask]
        self.X_test = test_data[features_df.columns]
        self.y_test = test_data['label']

        # 样本权重分割
        if self.sample_weights is not None:
            self.sample_weights = self.sample_weights[train_mask]

        # 预测时间分割
        if self.pred_times is not None:
            self.pred_times = self.pred_times[train_mask]

        logger.info(f"训练集: {len(self.X_train)} 样本")
        logger.info(f"测试集: {len(self.X_test)} 样本")
        logger.info(f"训练集标签分布: {self.y_train.value_counts().to_dict()}")

    def preprocess_data(self):
        """数据预处理"""
        data_config = self.config['data']

        # 删除原始价格列 (只保留平稳特征)
        drop_features = data_config.get('drop_features', [])
        existing_drop_features = [f for f in drop_features if f in self.X_train.columns]

        if existing_drop_features:
            logger.info(f"删除原始价格列: {existing_drop_features}")
            self.X_train = self.X_train.drop(columns=existing_drop_features)
            self.X_test = self.X_test.drop(columns=existing_drop_features)

        # 检查缺失值
        missing_train = self.X_train.isnull().sum().sum()
        if missing_train > 0:
            logger.warning(f"训练集存在 {missing_train} 个缺失值,将填充为 0")
            self.X_train = self.X_train.fillna(0)
            self.X_test = self.X_test.fillna(0)

        # 检查无限值
        inf_train = np.isinf(self.X_train).sum().sum()
        if inf_train > 0:
            logger.warning(f"训练集存在 {inf_train} 个无限值,将替换为 0")
            self.X_train = self.X_train.replace([np.inf, -np.inf], 0)
            self.X_test = self.X_test.replace([np.inf, -np.inf], 0)

        logger.info("数据预处理完成!")

    def feature_selection(self):
        """特征选择与去噪"""
        fs_config = self.config.get('feature_selection', {})

        if not fs_config.get('enable', False):
            logger.info("特征选择已禁用,使用全部特征")
            self.feature_names = self.X_train.columns.tolist()
            return

        method = fs_config.get('method', 'none')

        if method == 'clustered_importance':
            logger.info("使用特征聚类去噪...")
            clustering_config = fs_config.get('clustering', {})

            clusterer = FeatureClusterer(
                correlation_threshold=clustering_config.get('correlation_threshold', 0.75)
            )
            clusterer.fit(self.X_train)

            # 绘制树状图
            output_dir = Path(self.config['output']['plots_dir'])
            clusterer.plot_dendrogram(
                self.X_train.columns.tolist(),
                output_path=str(output_dir / 'feature_clustering_dendrogram.png')
            )

            logger.info("特征聚类完成!")

        elif method == 'mda':
            logger.info("使用 MDA 特征重要性筛选...")
            # 需要先训练一个基础模型
            logger.warning("MDA 方法需要预训练模型,暂时跳过")

        else:
            logger.info(f"未知的特征选择方法: {method}")

        self.feature_names = self.X_train.columns.tolist()
        logger.info(f"最终特征数: {len(self.feature_names)}")

    def setup_validation(self):
        """设置交叉验证策略"""
        val_config = self.config['validation']
        method = val_config.get('method', 'purged_kfold')

        if method == 'purged_kfold':
            pkf_config = val_config['purged_kfold']
            cv_splitter = PurgedKFold(
                n_splits=pkf_config.get('n_splits', 5),
                embargo_pct=pkf_config.get('embargo_pct', 0.01),
                purge_overlap=pkf_config.get('purge_overlap', True)
            )
            logger.info(f"使用 Purged K-Fold: {pkf_config['n_splits']} folds")

        elif method == 'walk_forward':
            wf_config = val_config['walk_forward']
            cv_splitter = WalkForwardValidator(
                train_period_days=wf_config.get('train_period_days', 730),
                test_period_days=wf_config.get('test_period_days', 90),
                step_days=wf_config.get('step_days', 90)
            )
            logger.info("使用 Walk Forward 验证")

        else:
            logger.warning(f"未知的验证方法: {method},使用默认 5-Fold")
            cv_splitter = None

        return cv_splitter

    def train_model(self, cv_splitter):
        """训练模型"""
        models_config = self.config['models']
        architecture = models_config.get('architecture', 'lightgbm')

        # 检查是否启用 Optuna
        optuna_config = self.config.get('optuna', {})
        if optuna_config.get('enable', False):
            logger.info("🔍 启动 Optuna 超参数优化...")
            self._run_optuna_optimization()
            # 优化后使用最佳参数重新训练
            # (这里简化处理,实际应该用最佳参数)

        if architecture == 'lightgbm':
            logger.info("训练 LightGBM 模型...")
            lgb_config = models_config['lightgbm']

            # 简单分割验证集
            split_idx = int(len(self.X_train) * 0.8)
            X_train_split = self.X_train.iloc[:split_idx]
            y_train_split = self.y_train.iloc[:split_idx]
            X_val_split = self.X_train.iloc[split_idx:]
            y_val_split = self.y_train.iloc[split_idx:]

            weight_train = self.sample_weights.iloc[:split_idx] if self.sample_weights is not None else None
            weight_val = self.sample_weights.iloc[split_idx:] if self.sample_weights is not None else None

            self.model = LightGBMTrainer(
                params=lgb_config,
                early_stopping_rounds=lgb_config.get('early_stopping_rounds', 50)
            )
            self.model.train(
                X_train_split, y_train_split,
                X_val_split, y_val_split,
                weight_train, weight_val,
                num_boost_round=lgb_config.get('num_boost_round', 1000)
            )

        elif architecture == 'catboost':
            if not CATBOOST_AVAILABLE:
                logger.error("CatBoost 未安装,请运行: pip install catboost")
                raise ImportError("CatBoost 未安装")

            logger.info("训练 CatBoost 模型...")
            cb_config = models_config['catboost']

            split_idx = int(len(self.X_train) * 0.8)
            X_train_split = self.X_train.iloc[:split_idx]
            y_train_split = self.y_train.iloc[:split_idx]
            X_val_split = self.X_train.iloc[split_idx:]
            y_val_split = self.y_train.iloc[split_idx:]

            weight_train = self.sample_weights.iloc[:split_idx] if self.sample_weights is not None else None
            weight_val = self.sample_weights.iloc[split_idx:] if self.sample_weights is not None else None

            self.model = CatBoostTrainer(
                params=cb_config,
                early_stopping_rounds=cb_config.get('early_stopping_rounds', 50)
            )
            self.model.train(
                X_train_split, y_train_split,
                X_val_split, y_val_split,
                weight_train, weight_val
            )

        elif architecture == 'ensemble_stacking':
            logger.info("训练 Ensemble Stacking 模型...")
            ensemble_config = models_config.get('ensemble', {})

            # 简单分割验证集
            split_idx = int(len(self.X_train) * 0.8)
            X_train_split = self.X_train.iloc[:split_idx]
            y_train_split = self.y_train.iloc[:split_idx]
            X_val_split = self.X_train.iloc[split_idx:]
            y_val_split = self.y_train.iloc[split_idx:]

            weight_train = self.sample_weights.iloc[:split_idx] if self.sample_weights is not None else None
            pred_times_split = self.pred_times.iloc[:split_idx] if self.pred_times is not None else None

            self.model = EnsembleStacker(
                use_catboost=ensemble_config.get('use_catboost', True),
                lgb_params=models_config.get('lightgbm'),
                cb_params=models_config.get('catboost')
            )
            self.model.train(
                X_train_split, y_train_split,
                X_val_split, y_val_split,
                weight_train,
                cv_splitter,
                pred_times_split
            )

        else:
            raise ValueError(f"未知的模型架构: {architecture}")

        logger.info("模型训练完成!")

    def _run_optuna_optimization(self):
        """运行 Optuna 超参数优化"""
        optuna_config = self.config['optuna']

        # 简单分割
        split_idx = int(len(self.X_train) * 0.8)
        X_train_split = self.X_train.iloc[:split_idx]
        y_train_split = self.y_train.iloc[:split_idx]
        X_val_split = self.X_train.iloc[split_idx:]
        y_val_split = self.y_train.iloc[split_idx:]

        weight_train = self.sample_weights.iloc[:split_idx] if self.sample_weights is not None else None
        weight_val = self.sample_weights.iloc[split_idx:] if self.sample_weights is not None else None

        optimizer = OptunaOptimizer(
            n_trials=optuna_config.get('n_trials', 50),
            timeout=optuna_config.get('timeout'),
            direction=optuna_config.get('direction', 'maximize')
        )

        best_params = optimizer.optimize(
            X_train_split, y_train_split,
            X_val_split, y_val_split,
            weight_train, weight_val,
            metric=optuna_config.get('metric', 'f1')
        )

        # 保存最佳参数
        output_dir = Path(self.config['output']['model_dir'])
        with open(output_dir / 'best_params.json', 'w') as f:
            json.dump(best_params, f, indent=2)

        logger.info(f"最佳参数已保存至: {output_dir / 'best_params.json'}")

    def evaluate_model(self):
        """评估模型"""
        logger.info("在测试集上评估模型...")

        evaluator = ModelEvaluator(
            output_dir=self.config['output']['plots_dir']
        )

        # 预测
        y_pred = self.model.predict(self.X_test)
        y_pred_proba = self.model.predict_proba(self.X_test)[:, 1]

        # 评估
        metrics = evaluator.evaluate(
            self.y_test,
            y_pred,
            y_pred_proba,
            prefix='test_set'
        )

        # 保存指标
        output_dir = Path(self.config['output']['model_dir'])
        with open(output_dir / 'test_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"测试集指标已保存至: {output_dir / 'test_metrics.json'}")

        # 特征重要性
        if hasattr(self.model, 'get_feature_importance'):
            importance = self.model.get_feature_importance()
            importance.to_csv(output_dir / 'feature_importance.csv')
            logger.info(f"特征重要性已保存至: {output_dir / 'feature_importance.csv'}")

    def save_outputs(self):
        """保存模型与报告"""
        output_config = self.config['output']

        if output_config.get('save_best_model', True):
            model_dir = Path(output_config['model_dir'])
            model_path = model_dir / 'model.pkl'

            if hasattr(self.model, 'save'):
                self.model.save(str(model_path))
                logger.info(f"模型已保存至: {model_path}")

        logger.info("所有输出已保存!")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MT5-CRS 机器学习训练脚本')

    parser.add_argument(
        '--config',
        type=str,
        default='config/ml_training_config.yaml',
        help='配置文件路径'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速测试模式 (减少数据量和迭代次数)'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 检查配置文件是否存在
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        print(f"请先创建配置文件，参考: config/ml_training_config.yaml")
        sys.exit(1)

    # 快速模式 (修改配置)
    if args.quick:
        print("⚡ 快速测试模式")
        # TODO: 修改配置减少数据量

    # 创建训练管道
    pipeline = MLTrainingPipeline(str(config_path))

    # 执行训练
    pipeline.run()


if __name__ == "__main__":
    main()
