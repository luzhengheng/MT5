"""
机器学习训练器 - LightGBM + Optuna 超参数优化

核心功能:
1. LightGBM 模型训练 (支持样本权重)
2. Optuna 贝叶斯超参数优化
3. Early Stopping 防止过拟合
4. 模型持久化

来源: "Advances in Financial Machine Learning" by Marcos Lopez de Prado
"""

import logging
import numpy as np
import pandas as pd
import pickle
import json
import lightgbm as lgb
import optuna
from typing import Dict, Optional, Tuple, Any, List
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    logger.warning("CatBoost 未安装，将跳过 CatBoost 模型")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LightGBMTrainer:
    """
    LightGBM 训练器 - 支持样本权重和 Early Stopping

    关键特性:
    1. 支持 sample_weight (来自 Triple Barrier)
    2. Early Stopping (防止过拟合)
    3. 类别不平衡处理 (scale_pos_weight)
    4. 验证集评估
    """

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        early_stopping_rounds: int = 50,
        verbose: int = 50
    ):
        """
        Args:
            params: LightGBM 参数字典
            early_stopping_rounds: Early Stopping 轮数
            verbose: 日志输出频率
        """
        self.params = params or self._get_default_params()
        self.early_stopping_rounds = early_stopping_rounds
        self.verbose = verbose
        self.model = None
        self.best_iteration = None
        self.feature_names = None

    @staticmethod
    def _get_default_params() -> Dict[str, Any]:
        """获取默认参数"""
        return {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'lambda_l1': 0.1,
            'lambda_l2': 0.1,
            'min_child_samples': 20,
            'max_depth': -1,
            'verbose': -1,
            'n_jobs': -1
        }

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        sample_weight_train: Optional[pd.Series] = None,
        sample_weight_val: Optional[pd.Series] = None,
        num_boost_round: int = 1000
    ) -> 'LightGBMTrainer':
        """
        训练 LightGBM 模型

        Args:
            X_train: 训练集特征
            y_train: 训练集标签
            X_val: 验证集特征
            y_val: 验证集标签
            sample_weight_train: 训练集样本权重
            sample_weight_val: 验证集样本权重
            num_boost_round: 最大迭代轮数

        Returns:
            self
        """
        logger.info(
            f"开始训练 LightGBM: "
            f"训练集 {X_train.shape[0]} 样本, "
            f"验证集 {X_val.shape[0]} 样本, "
            f"特征数 {X_train.shape[1]}"
        )

        # 保存特征名
        self.feature_names = X_train.columns.tolist()

        # 创建 LightGBM Dataset
        train_data = lgb.Dataset(
            X_train,
            label=y_train,
            weight=sample_weight_train,
            feature_name=self.feature_names
        )

        val_data = lgb.Dataset(
            X_val,
            label=y_val,
            weight=sample_weight_val,
            feature_name=self.feature_names,
            reference=train_data
        )

        # 训练模型
        evals_result = {}
        self.model = lgb.train(
            self.params,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'valid'],
            callbacks=[
                lgb.early_stopping(self.early_stopping_rounds),
                lgb.log_evaluation(self.verbose),
                lgb.record_evaluation(evals_result)
            ]
        )

        self.best_iteration = self.model.best_iteration
        logger.info(f"训练完成! 最佳迭代: {self.best_iteration}")

        # 评估性能
        self._evaluate(X_val, y_val)

        return self

    def _evaluate(self, X_val: pd.DataFrame, y_val: pd.Series):
        """评估模型性能"""
        y_pred = self.predict(X_val)
        y_pred_proba = self.predict_proba(X_val)[:, 1]

        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average='weighted')
        try:
            auc = roc_auc_score(y_val, y_pred_proba)
        except:
            auc = 0.0
        logloss = log_loss(y_val, y_pred_proba)

        logger.info(f"验证集性能:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  F1-Score: {f1:.4f}")
        logger.info(f"  AUC-ROC: {auc:.4f}")
        logger.info(f"  Log Loss: {logloss:.4f}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测类别"""
        if self.model is None:
            raise ValueError("模型未训练,请先调用 train()")

        y_pred_proba = self.model.predict(X, num_iteration=self.best_iteration)
        return (y_pred_proba > 0.5).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if self.model is None:
            raise ValueError("模型未训练,请先调用 train()")

        y_pred_proba = self.model.predict(X, num_iteration=self.best_iteration)
        # 返回 [prob_class_0, prob_class_1] 格式 (sklearn 兼容)
        return np.vstack([1 - y_pred_proba, y_pred_proba]).T

    def get_feature_importance(self, importance_type: str = 'gain') -> pd.Series:
        """
        获取特征重要性

        Args:
            importance_type: 'split' (分裂次数) 或 'gain' (增益)

        Returns:
            特征重要性 Series
        """
        if self.model is None:
            raise ValueError("模型未训练")

        importance = self.model.feature_importance(importance_type=importance_type)
        return pd.Series(importance, index=self.feature_names).sort_values(ascending=False)

    def save(self, model_path: str, metadata: Optional[Dict] = None):
        """
        保存模型

        Args:
            model_path: 模型保存路径 (.pkl)
            metadata: 额外的元数据 (如特征名称、训练日期等)
        """
        model_dir = Path(model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)

        # 保存模型
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'params': self.params,
                'feature_names': self.feature_names,
                'best_iteration': self.best_iteration,
                'metadata': metadata or {}
            }, f)

        logger.info(f"模型已保存至: {model_path}")

        # 保存 LightGBM 原生格式 (用于部署)
        lgb_model_path = model_path.replace('.pkl', '.txt')
        self.model.save_model(lgb_model_path, num_iteration=self.best_iteration)
        logger.info(f"LightGBM 原生模型已保存至: {lgb_model_path}")

    @classmethod
    def load(cls, model_path: str) -> 'LightGBMTrainer':
        """
        加载模型

        Args:
            model_path: 模型路径

        Returns:
            训练器实例
        """
        with open(model_path, 'rb') as f:
            data = pickle.load(f)

        trainer = cls(params=data['params'])
        trainer.model = data['model']
        trainer.feature_names = data['feature_names']
        trainer.best_iteration = data['best_iteration']

        logger.info(f"模型已加载: {model_path}")
        return trainer


class OptunaOptimizer:
    """
    Optuna 超参数优化器

    使用 TPE (Tree-structured Parzen Estimator) 采样器
    进行贝叶斯优化,比 GridSearch 高效 10-100 倍
    """

    def __init__(
        self,
        n_trials: int = 100,
        timeout: Optional[int] = None,
        direction: str = 'maximize'
    ):
        """
        Args:
            n_trials: 优化试验次数
            timeout: 超时时间 (秒)
            direction: 优化方向 ('maximize' 或 'minimize')
        """
        self.n_trials = n_trials
        self.timeout = timeout
        self.direction = direction
        self.study = None
        self.best_params = None

    def optimize(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        sample_weight_train: Optional[pd.Series] = None,
        sample_weight_val: Optional[pd.Series] = None,
        metric: str = 'f1'
    ) -> Dict[str, Any]:
        """
        执行超参数优化

        Args:
            X_train: 训练集特征
            y_train: 训练集标签
            X_val: 验证集特征
            y_val: 验证集标签
            sample_weight_train: 训练集样本权重
            sample_weight_val: 验证集样本权重
            metric: 优化指标 ('f1', 'accuracy', 'auc', 'logloss')

        Returns:
            最佳参数字典
        """
        logger.info(f"开始 Optuna 超参数优化: {self.n_trials} 次试验, 优化指标: {metric}")

        def objective(trial):
            # 定义搜索空间
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': trial.suggest_int('num_leaves', 20, 150),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
                'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
                'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
                'lambda_l1': trial.suggest_float('lambda_l1', 1e-8, 10.0, log=True),
                'lambda_l2': trial.suggest_float('lambda_l2', 1e-8, 10.0, log=True),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'verbose': -1,
                'n_jobs': -1
            }

            # 训练模型
            trainer = LightGBMTrainer(params=params, early_stopping_rounds=30, verbose=-1)
            trainer.train(
                X_train, y_train, X_val, y_val,
                sample_weight_train, sample_weight_val,
                num_boost_round=500
            )

            # 计算指标
            y_pred = trainer.predict(X_val)
            y_pred_proba = trainer.predict_proba(X_val)[:, 1]

            if metric == 'f1':
                score = f1_score(y_val, y_pred, average='weighted')
            elif metric == 'accuracy':
                score = accuracy_score(y_val, y_pred)
            elif metric == 'auc':
                try:
                    score = roc_auc_score(y_val, y_pred_proba)
                except:
                    score = 0.5
            elif metric == 'logloss':
                score = -log_loss(y_val, y_pred_proba)  # 负号,因为要最大化
            else:
                raise ValueError(f"不支持的指标: {metric}")

            return score

        # 创建 study 并优化
        self.study = optuna.create_study(direction=self.direction)
        self.study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            show_progress_bar=True
        )

        self.best_params = self.study.best_params
        logger.info(f"优化完成! 最佳 {metric}: {self.study.best_value:.4f}")
        logger.info(f"最佳参数: {self.best_params}")

        return self.best_params

    def save_study(self, output_path: str):
        """保存优化历史"""
        if self.study is None:
            raise ValueError("未运行优化")

        study_df = self.study.trials_dataframe()
        study_df.to_csv(output_path, index=False)
        logger.info(f"优化历史已保存至: {output_path}")


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("测试训练器模块")
    print("=" * 80)

    # 创建模拟数据
    np.random.seed(42)
    n_samples = 2000

    X = pd.DataFrame({
        f'feature_{i}': np.random.randn(n_samples)
        for i in range(10)
    })
    y = pd.Series((X.sum(axis=1) + np.random.randn(n_samples) > 0).astype(int))

    # 分割数据
    split_idx = int(n_samples * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    # 测试 LightGBM 训练器
    print("\n1. 测试 LightGBM 训练器:")
    trainer = LightGBMTrainer(early_stopping_rounds=20, verbose=-1)
    trainer.train(X_train, y_train, X_val, y_val, num_boost_round=100)

    # 特征重要性
    importance = trainer.get_feature_importance()
    print(f"\nTop 5 重要特征:")
    print(importance.head(5))

    # 保存和加载
    model_path = '/opt/mt5-crs/outputs/models/test_model.pkl'
    trainer.save(model_path)
    loaded_trainer = LightGBMTrainer.load(model_path)
    print(f"\n模型保存和加载测试: {'✅' if loaded_trainer.model is not None else '❌'}")

    print("\n✅ 训练器测试完成!")


class CatBoostTrainer:
    """
    CatBoost 训练器

    优势:
    - 自动处理类别特征
    - 内置防过拟合机制 (Ordered Boosting)
    - 训练速度快
    - 对超参数不敏感
    """

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        early_stopping_rounds: int = 50,
        verbose: int = 50
    ):
        """
        Args:
            params: CatBoost 参数字典
            early_stopping_rounds: Early Stopping 轮数
            verbose: 日志输出频率
        """
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost 未安装，请运行: pip install catboost")

        self.params = params or self._get_default_params()
        self.early_stopping_rounds = early_stopping_rounds
        self.verbose = verbose
        self.model = None
        self.feature_names = None

    @staticmethod
    def _get_default_params() -> Dict[str, Any]:
        """获取默认参数"""
        return {
            'loss_function': 'Logloss',
            'eval_metric': 'Logloss',
            'iterations': 1000,
            'learning_rate': 0.05,
            'depth': 6,
            'l2_leaf_reg': 3.0,
            'random_strength': 1.0,
            'bagging_temperature': 1.0,
            'border_count': 128,
            'verbose': False,
            'thread_count': -1
        }

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        sample_weight_train: Optional[pd.Series] = None,
        sample_weight_val: Optional[pd.Series] = None,
        cat_features: Optional[List[str]] = None
    ) -> 'CatBoostTrainer':
        """
        训练 CatBoost 模型

        Args:
            X_train: 训练集特征
            y_train: 训练集标签
            X_val: 验证集特征
            y_val: 验证集标签
            sample_weight_train: 训练集样本权重
            sample_weight_val: 验证集样本权重
            cat_features: 类别特征列名列表

        Returns:
            self
        """
        logger.info(
            f"开始训练 CatBoost: "
            f"训练集 {X_train.shape[0]} 样本, "
            f"验证集 {X_val.shape[0]} 样本, "
            f"特征数 {X_train.shape[1]}"
        )

        self.feature_names = X_train.columns.tolist()

        # 创建 CatBoost Pool
        train_pool = cb.Pool(
            X_train,
            label=y_train,
            weight=sample_weight_train,
            cat_features=cat_features
        )

        val_pool = cb.Pool(
            X_val,
            label=y_val,
            weight=sample_weight_val,
            cat_features=cat_features
        )

        # 训练模型
        self.model = cb.CatBoostClassifier(**self.params)
        self.model.fit(
            train_pool,
            eval_set=val_pool,
            early_stopping_rounds=self.early_stopping_rounds,
            verbose=self.verbose
        )

        logger.info(f"训练完成! 最佳迭代: {self.model.best_iteration_}")

        # 评估性能
        self._evaluate(X_val, y_val)

        return self

    def _evaluate(self, X_val: pd.DataFrame, y_val: pd.Series):
        """评估模型性能"""
        y_pred = self.predict(X_val)
        y_pred_proba = self.predict_proba(X_val)[:, 1]

        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average='weighted')
        try:
            auc = roc_auc_score(y_val, y_pred_proba)
        except:
            auc = 0.0
        logloss = log_loss(y_val, y_pred_proba)

        logger.info(f"验证集性能:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  F1-Score: {f1:.4f}")
        logger.info(f"  AUC-ROC: {auc:.4f}")
        logger.info(f"  Log Loss: {logloss:.4f}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测类别"""
        if self.model is None:
            raise ValueError("模型未训练,请先调用 train()")
        return self.model.predict(X).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if self.model is None:
            raise ValueError("模型未训练,请先调用 train()")
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> pd.Series:
        """获取特征重要性"""
        if self.model is None:
            raise ValueError("模型未训练")
        importance = self.model.get_feature_importance()
        return pd.Series(importance, index=self.feature_names).sort_values(ascending=False)

    def save(self, model_path: str):
        """保存模型"""
        model_dir = Path(model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)

        self.model.save_model(model_path)
        logger.info(f"CatBoost 模型已保存至: {model_path}")

    @classmethod
    def load(cls, model_path: str) -> 'CatBoostTrainer':
        """加载模型"""
        trainer = cls()
        trainer.model = cb.CatBoostClassifier()
        trainer.model.load_model(model_path)
        logger.info(f"CatBoost 模型已加载: {model_path}")
        return trainer


class EnsembleStacker:
    """
    Ensemble Stacking 模型融合器

    架构:
    - 第一层 (Base Learners): LightGBM + CatBoost
    - 第二层 (Meta Learner): Logistic Regression

    优势:
    - 融合多个模型的预测，提升泛化能力
    - Meta Learner 学习如何组合基模型的输出
    - 降低单一模型的过拟合风险

    流程:
    1. 使用 Purged K-Fold 训练多个基模型
    2. 收集基模型的 Out-of-Fold 预测
    3. 使用 OOF 预测训练 Meta Learner
    4. 最终预测 = Meta Learner(Base Model Predictions)
    """

    def __init__(
        self,
        use_catboost: bool = True,
        lgb_params: Optional[Dict] = None,
        cb_params: Optional[Dict] = None
    ):
        """
        Args:
            use_catboost: 是否使用 CatBoost (如果未安装则自动跳过)
            lgb_params: LightGBM 参数
            cb_params: CatBoost 参数
        """
        self.use_catboost = use_catboost and CATBOOST_AVAILABLE
        self.lgb_params = lgb_params
        self.cb_params = cb_params

        self.lgb_models = []
        self.cb_models = []
        self.meta_model = None
        self.feature_names = None

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        sample_weight_train: Optional[pd.Series] = None,
        cv_splitter = None,
        pred_times: Optional[pd.Series] = None
    ) -> 'EnsembleStacker':
        """
        训练 Stacking 模型

        Args:
            X_train: 训练集特征
            y_train: 训练集标签
            X_val: 验证集特征
            y_val: 验证集标签
            sample_weight_train: 训练集样本权重
            cv_splitter: 交叉验证分割器 (如 PurgedKFold)
            pred_times: 标签结束时间 (用于 Purging)

        Returns:
            self
        """
        logger.info("=" * 80)
        logger.info("开始训练 Ensemble Stacking 模型")
        logger.info("=" * 80)

        self.feature_names = X_train.columns.tolist()

        # 步骤 1: 训练基模型并生成 Out-of-Fold 预测
        logger.info("\n[步骤 1/3] 训练基模型...")

        oof_predictions = {}

        # LightGBM 基模型
        logger.info("\n训练 LightGBM 基模型...")
        lgb_oof = self._train_base_model(
            'lightgbm',
            X_train, y_train, sample_weight_train,
            cv_splitter, pred_times
        )
        oof_predictions['lgb'] = lgb_oof

        # CatBoost 基模型
        if self.use_catboost:
            logger.info("\n训练 CatBoost 基模型...")
            cb_oof = self._train_base_model(
                'catboost',
                X_train, y_train, sample_weight_train,
                cv_splitter, pred_times
            )
            oof_predictions['cb'] = cb_oof

        # 步骤 2: 训练 Meta Learner
        logger.info("\n[步骤 2/3] 训练 Meta Learner...")

        # 构建 Meta 特征 (基模型的 OOF 预测)
        meta_features_train = pd.DataFrame(oof_predictions)

        # 简单的 Logistic Regression 作为 Meta Learner
        self.meta_model = LogisticRegression(
            penalty='l2',
            C=1.0,
            max_iter=1000,
            random_state=42
        )
        self.meta_model.fit(meta_features_train, y_train)

        logger.info("Meta Learner 训练完成!")
        logger.info(f"Meta 特征权重: {dict(zip(meta_features_train.columns, self.meta_model.coef_[0]))}")

        # 步骤 3: 在验证集上评估
        logger.info("\n[步骤 3/3] 验证集评估...")
        self._evaluate(X_val, y_val)

        logger.info("\n✅ Ensemble Stacking 训练完成!")

        return self

    def _train_base_model(
        self,
        model_type: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        sample_weight: Optional[pd.Series],
        cv_splitter,
        pred_times: Optional[pd.Series]
    ) -> np.ndarray:
        """
        训练单个基模型并生成 Out-of-Fold 预测

        Args:
            model_type: 'lightgbm' 或 'catboost'
            X_train: 训练集特征
            y_train: 训练集标签
            sample_weight: 样本权重
            cv_splitter: 交叉验证分割器
            pred_times: 标签结束时间

        Returns:
            Out-of-Fold 预测概率 (shape: [n_samples])
        """
        oof_predictions = np.zeros(len(X_train))

        # 如果没有提供 cv_splitter，使用简单的 train/val 分割
        if cv_splitter is None:
            split_idx = int(len(X_train) * 0.8)
            folds = [(np.arange(split_idx), np.arange(split_idx, len(X_train)))]
        else:
            folds = list(cv_splitter.split(X_train, y_train, event_ends=pred_times))

        for fold_num, (train_idx, val_idx) in enumerate(folds, 1):
            logger.info(f"  Fold {fold_num}/{len(folds)}: 训练 {model_type}...")

            X_fold_train = X_train.iloc[train_idx]
            y_fold_train = y_train.iloc[train_idx]
            X_fold_val = X_train.iloc[val_idx]
            y_fold_val = y_train.iloc[val_idx]

            weight_fold_train = sample_weight.iloc[train_idx] if sample_weight is not None else None
            weight_fold_val = sample_weight.iloc[val_idx] if sample_weight is not None else None

            # 训练模型
            if model_type == 'lightgbm':
                trainer = LightGBMTrainer(
                    params=self.lgb_params,
                    early_stopping_rounds=30,
                    verbose=-1
                )
                trainer.train(
                    X_fold_train, y_fold_train,
                    X_fold_val, y_fold_val,
                    weight_fold_train, weight_fold_val,
                    num_boost_round=500
                )
                self.lgb_models.append(trainer)

            elif model_type == 'catboost':
                trainer = CatBoostTrainer(
                    params=self.cb_params,
                    early_stopping_rounds=30,
                    verbose=0
                )
                trainer.train(
                    X_fold_train, y_fold_train,
                    X_fold_val, y_fold_val,
                    weight_fold_train, weight_fold_val
                )
                self.cb_models.append(trainer)

            # 生成 OOF 预测
            oof_predictions[val_idx] = trainer.predict_proba(X_fold_val)[:, 1]

        logger.info(f"  {model_type} OOF 预测生成完成!")

        return oof_predictions

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测类别"""
        proba = self.predict_proba(X)
        return (proba[:, 1] > 0.5).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if self.meta_model is None:
            raise ValueError("模型未训练,请先调用 train()")

        # 收集基模型预测
        base_predictions = {}

        # LightGBM 预测 (取多个 fold 的平均)
        lgb_preds = np.mean([
            model.predict_proba(X)[:, 1]
            for model in self.lgb_models
        ], axis=0)
        base_predictions['lgb'] = lgb_preds

        # CatBoost 预测
        if self.use_catboost and len(self.cb_models) > 0:
            cb_preds = np.mean([
                model.predict_proba(X)[:, 1]
                for model in self.cb_models
            ], axis=0)
            base_predictions['cb'] = cb_preds

        # 构建 Meta 特征
        meta_features = pd.DataFrame(base_predictions)

        # Meta Learner 预测
        return self.meta_model.predict_proba(meta_features)

    def _evaluate(self, X_val: pd.DataFrame, y_val: pd.Series):
        """评估模型性能"""
        y_pred = self.predict(X_val)
        y_pred_proba = self.predict_proba(X_val)[:, 1]

        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average='weighted')
        try:
            auc = roc_auc_score(y_val, y_pred_proba)
        except:
            auc = 0.0
        logloss = log_loss(y_val, y_pred_proba)

        logger.info(f"\n🎯 Ensemble 验证集性能:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  F1-Score: {f1:.4f}")
        logger.info(f"  AUC-ROC: {auc:.4f}")
        logger.info(f"  Log Loss: {logloss:.4f}")

    def save(self, output_dir: str):
        """保存 Ensemble 模型"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存 LightGBM 模型
        for i, model in enumerate(self.lgb_models):
            model.save(str(output_path / f'lgb_fold_{i}.pkl'))

        # 保存 CatBoost 模型
        if self.use_catboost:
            for i, model in enumerate(self.cb_models):
                model.save(str(output_path / f'cb_fold_{i}.cbm'))

        # 保存 Meta Learner
        with open(output_path / 'meta_model.pkl', 'wb') as f:
            pickle.dump(self.meta_model, f)

        logger.info(f"Ensemble 模型已保存至: {output_dir}")

    @classmethod
    def load(cls, input_dir: str) -> 'EnsembleStacker':
        """加载 Ensemble 模型"""
        input_path = Path(input_dir)

        stacker = cls()

        # 加载 LightGBM 模型
        lgb_files = sorted(input_path.glob('lgb_fold_*.pkl'))
        for lgb_file in lgb_files:
            model = LightGBMTrainer.load(str(lgb_file))
            stacker.lgb_models.append(model)

        # 加载 CatBoost 模型
        if CATBOOST_AVAILABLE:
            cb_files = sorted(input_path.glob('cb_fold_*.cbm'))
            for cb_file in cb_files:
                model = CatBoostTrainer.load(str(cb_file))
                stacker.cb_models.append(model)
            stacker.use_catboost = len(stacker.cb_models) > 0

        # 加载 Meta Learner
        with open(input_path / 'meta_model.pkl', 'rb') as f:
            stacker.meta_model = pickle.load(f)

        logger.info(f"Ensemble 模型已加载: {input_dir}")
        return stacker
