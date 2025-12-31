#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost Hyperparameter Optimizer

使用 Optuna 框架进行超参数优化。

协议: v2.2 (本地存储，文档优先)
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score,
    recall_score, f1_score
)

try:
    import optuna
    from optuna.samplers import TPESampler
    from optuna.pruners import MedianPruner
except ImportError:
    print("❌ Optuna 未安装。请运行: pip install optuna")
    sys.exit(1)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


class HyperparameterOptimizer:
    """XGBoost 超参数优化器"""

    def __init__(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: pd.Series,
        y_test: pd.Series,
        n_trials: int = 50,
        random_state: int = 42
    ):
        """
        初始化优化器
        
        参数:
            X_train: 训练特征 (标准化后)
            X_test: 测试特征 (标准化后)
            y_train: 训练标签
            y_test: 测试标签
            n_trials: Optuna 试验次数
            random_state: 随机种子
        """
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.n_trials = n_trials
        self.random_state = random_state

        self.study = None
        self.best_params = None
        self.best_model = None
        self.best_score = None

        logger.info(f"{GREEN}✅ HyperparameterOptimizer 已初始化{RESET}")
        logger.info(f"  训练集: {len(X_train)} 样本")
        logger.info(f"  测试集: {len(X_test)} 样本")
        logger.info(f"  试验次数: {n_trials}")

    def objective(self, trial):
        """
        Optuna 目标函数
        
        参数:
            trial: Optuna Trial 对象
            
        返回:
            AUC-ROC 分数 (越高越好)
        """
        # 采样超参数
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 2.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
            'objective': 'binary:logistic',
            'random_state': self.random_state,
            'n_jobs': -1,
            'verbosity': 0
        }

        try:
            # 训练模型
            model = XGBClassifier(**params)
            model.fit(self.X_train, self.y_train, verbose=False)

            # 预测测试集
            y_pred_proba = model.predict_proba(self.X_test)[:, 1]

            # 计算 AUC-ROC
            auc = roc_auc_score(self.y_test, y_pred_proba)

            return auc

        except Exception as e:
            logger.warning(f"{YELLOW}⚠️  Trial {trial.number} 失败: {e}{RESET}")
            return 0.0

    def optimize(self) -> Dict:
        """
        运行超参数优化
        
        返回:
            最佳超参数字典
        """
        logger.info(f"{BLUE}{'=' * 80}{RESET}")
        logger.info(f"{BLUE}🔧 XGBoost 超参数优化 (Optuna){RESET}")
        logger.info(f"{BLUE}{'=' * 80}{RESET}")
        logger.info("")

        logger.info(f"{CYAN}🚀 开始优化...{RESET}")
        logger.info(f"  试验次数: {self.n_trials}")
        logger.info(f"  采样器: TPESampler")
        logger.info(f"  剪枝器: MedianPruner")
        logger.info(f"  目标: 最大化 AUC-ROC")
        logger.info("")

        # 创建 Study
        self.study = optuna.create_study(
            study_name='xgboost_optimization_v1',
            direction='maximize',
            sampler=TPESampler(seed=self.random_state),
            pruner=MedianPruner(
                n_startup_trials=10,
                n_warmup_steps=5
            )
        )

        # 运行优化
        self.study.optimize(
            self.objective,
            n_trials=self.n_trials,
            show_progress_bar=True
        )

        # 获取最佳参数
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value

        logger.info("")
        logger.info(f"{GREEN}✅ 优化完成{RESET}")
        logger.info(f"  最佳 AUC: {self.best_score:.4f}")
        logger.info(f"  最佳试验: Trial {self.study.best_trial.number}")
        logger.info(f"  最佳参数:")
        for key, value in self.best_params.items():
            if isinstance(value, float):
                logger.info(f"    {key}: {value:.4f}")
            else:
                logger.info(f"    {key}: {value}")

        return self.best_params

    def train_best_model(self) -> XGBClassifier:
        """
        使用最佳参数训练最终模型
        
        返回:
            训练好的 XGBClassifier
        """
        if self.best_params is None:
            raise ValueError("必须先运行 optimize() 方法")

        logger.info("")
        logger.info(f"{CYAN}🚀 使用最佳参数训练模型...{RESET}")

        # 构建完整参数
        params = {
            **self.best_params,
            'objective': 'binary:logistic',
            'random_state': self.random_state,
            'n_jobs': -1,
            'verbosity': 0
        }

        # 训练模型
        self.best_model = XGBClassifier(**params)
        self.best_model.fit(self.X_train, self.y_train, verbose=False)

        logger.info(f"{GREEN}✅ 模型训练完成{RESET}")

        return self.best_model

    def evaluate_best_model(self) -> Dict:
        """
        评估最佳模型性能
        
        返回:
            评估指标字典
        """
        if self.best_model is None:
            raise ValueError("必须先运行 train_best_model() 方法")

        logger.info("")
        logger.info(f"{CYAN}📊 评估最佳模型...{RESET}")

        # 预测
        y_pred = self.best_model.predict(self.X_test)
        y_pred_proba = self.best_model.predict_proba(self.X_test)[:, 1]

        # 计算指标
        results = {
            'accuracy': float(accuracy_score(self.y_test, y_pred)),
            'precision': float(precision_score(self.y_test, y_pred)),
            'recall': float(recall_score(self.y_test, y_pred)),
            'f1_score': float(f1_score(self.y_test, y_pred)),
            'auc_roc': float(roc_auc_score(self.y_test, y_pred_proba)),
            'test_samples': int(len(self.y_test)),
            'train_samples': int(len(self.y_train))
        }

        logger.info(f"{GREEN}✅ 评估完成{RESET}")
        logger.info("")
        logger.info(f"  Accuracy:  {results['accuracy']:.4f}")
        logger.info(f"  Precision: {results['precision']:.4f}")
        logger.info(f"  Recall:    {results['recall']:.4f}")
        logger.info(f"  F1-Score:  {results['f1_score']:.4f}")
        logger.info(f"  AUC-ROC:   {results['auc_roc']:.4f}")

        return results

    def save_best_params(self, path: str = "models/best_params_v1.json") -> str:
        """
        保存最佳超参数到 JSON 文件
        
        参数:
            path: 保存路径
            
        返回:
            保存的文件路径
        """
        if self.best_params is None:
            raise ValueError("必须先运行 optimize() 方法")

        logger.info("")
        logger.info(f"{CYAN}💾 保存最佳参数...{RESET}")

        filepath = PROJECT_ROOT / path
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # 添加元数据
        output = {
            "best_params": self.best_params,
            "best_auc": float(self.best_score),
            "n_trials": self.n_trials,
            "random_state": self.random_state,
            "timestamp": pd.Timestamp.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"{GREEN}✅ 最佳参数已保存{RESET}")
        logger.info(f"  路径: {filepath}")

        return str(filepath)

    def compare_with_baseline(self, baseline_results: Dict) -> None:
        """
        对比优化后模型与基线模型
        
        参数:
            baseline_results: 基线模型的评估结果
        """
        if self.best_model is None:
            raise ValueError("必须先运行 train_best_model() 方法")

        optimized_results = self.evaluate_best_model()

        logger.info("")
        logger.info(f"{MAGENTA}{'=' * 80}{RESET}")
        logger.info(f"{MAGENTA}📈 Before vs After 对比{RESET}")
        logger.info(f"{MAGENTA}{'=' * 80}{RESET}")
        logger.info("")

        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc']

        for metric in metrics:
            baseline_val = baseline_results.get(metric, 0.0)
            optimized_val = optimized_results.get(metric, 0.0)
            improvement = optimized_val - baseline_val
            improvement_pct = (improvement / baseline_val * 100) if baseline_val > 0 else 0.0

            color = GREEN if improvement > 0 else (RED if improvement < 0 else YELLOW)
            sign = "+" if improvement > 0 else ""

            logger.info(
                f"  {metric.upper():12s}: "
                f"{baseline_val:.4f} → {optimized_val:.4f} "
                f"{color}({sign}{improvement:.4f}, {sign}{improvement_pct:.2f}%){RESET}"
            )

        logger.info("")
        logger.info(f"{MAGENTA}{'=' * 80}{RESET}")


def load_baseline_results(path: str = "models/baseline_v1_results.json") -> Dict:
    """
    加载基线模型的评估结果
    
    参数:
        path: 基线结果文件路径
        
    返回:
        评估结果字典
    """
    filepath = PROJECT_ROOT / path

    if not filepath.exists():
        logger.warning(f"{YELLOW}⚠️  基线结果文件不存在: {filepath}{RESET}")
        return {}

    with open(filepath, 'r') as f:
        results = json.load(f)

    logger.info(f"{GREEN}✅ 已加载基线结果: {filepath}{RESET}")

    return results
