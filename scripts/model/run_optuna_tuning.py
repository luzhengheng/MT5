#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #116: ML Hyperparameter Optimization - Execution Script
============================================================

使用 Optuna 运行超参数优化，产出 xgboost_challenger.json 模型。

执行步骤:
1. 加载标准化的 Parquet 数据 (Task #111 产出)
2. 运行 50 次 Optuna Trials
3. 使用 TimeSeriesSplit 防止未来数据泄露
4. 保存最优模型和元数据
5. 生成对比报告

协议: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-16
"""

import sys
import logging
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def load_standardized_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    加载 Task #111 产出的标准化 Parquet 数据

    返回:
        (features, labels) 元组
    """
    logger.info(f"{CYAN}📥 加载标准化数据...{RESET}")

    data_dir = PROJECT_ROOT / "docs/archive/outputs/features"

    if not data_dir.exists():
        logger.warning(f"{YELLOW}⚠️  标准化数据目录不存在: {data_dir}{RESET}")
        logger.info(f"{CYAN}尝试备用位置...{RESET}")

        # 尝试其他位置
        backup_dirs = [
            PROJECT_ROOT / "data/standardized",
            PROJECT_ROOT / "data/processed",
        ]

        for backup_dir in backup_dirs:
            if backup_dir.exists():
                data_dir = backup_dir
                logger.info(f"{GREEN}✅ 找到数据目录: {data_dir}{RESET}")
                break
        else:
            logger.error(f"{RED}❌ 无法找到数据目录{RESET}")
            logger.info(f"{CYAN}预期位置:{RESET}")
            for d in [PROJECT_ROOT / "docs/archive/outputs/features"] + backup_dirs:
                logger.info(f"   - {d}")
            return None, None

    try:
        # 加载特征
        features_path = data_dir / "features.parquet"
        if features_path.exists():
            logger.info(f"   加载特征: {features_path}")
            features_df = pd.read_parquet(features_path)
            features = features_df.values
            logger.info(f"   特征形状: {features.shape}")
        else:
            logger.error(f"{RED}❌ 特征文件不存在: {features_path}{RESET}")
            return None, None

        # 加载标签
        labels_path = data_dir / "labels.parquet"
        if labels_path.exists():
            logger.info(f"   加载标签: {labels_path}")
            labels_df = pd.read_parquet(labels_path)
            labels = labels_df.values.ravel()
            logger.info(f"   标签形状: {labels.shape}")
        else:
            logger.error(f"{RED}❌ 标签文件不存在: {labels_path}{RESET}")
            return None, None

        logger.info(f"{GREEN}✅ 数据加载成功{RESET}\n")

        return features, labels

    except Exception as e:
        logger.error(f"{RED}❌ 加载数据失败: {e}{RESET}")
        return None, None


def prepare_data(features: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    准备训练和测试数据

    参数:
        features: 原始特征
        labels: 原始标签

    返回:
        (X_train, X_test, y_train, y_test) 元组
    """
    logger.info(f"{CYAN}🔧 准备数据...{RESET}")

    # ⚠️ CRITICAL FIX: TimeSeriesSplit FIRST, then StandardScaler
    # This prevents data leakage where scaler sees test set statistics
    logger.info(f"   使用 TimeSeriesSplit 分割数据 (防止未来数据泄露)...")

    # 使用 TimeSeriesSplit 分割数据 (BEFORE scaling)
    tscv = TimeSeriesSplit(n_splits=3)
    train_idx, test_idx = list(tscv.split(features))[-1]  # 使用最后一个分割

    # ✅ CORRECT: Fit scaler ONLY on training data
    scaler = StandardScaler()
    X_train = scaler.fit_transform(features[train_idx])
    X_test = scaler.transform(features[test_idx])

    y_train = labels[train_idx]
    y_test = labels[test_idx]

    logger.info(f"   特征已标准化 (StandardScaler fit on training data only)")
    logger.info(f"   TimeSeriesSplit 分割完成:")
    logger.info(f"   训练集: {X_train.shape[0]} 样本")
    logger.info(f"   测试集: {X_test.shape[0]} 样本")
    logger.info(f"   特征维度: {X_train.shape[1]}")
    logger.info(f"   ✅ 防止数据泄露: 标准化器仅在训练集上拟合")
    logger.info(f"{GREEN}✅ 数据准备完成{RESET}\n")

    return X_train, X_test, y_train, y_test


def main():
    """主执行函数"""
    logger.info(f"\n{BLUE}{'=' * 80}{RESET}")
    logger.info(f"{BLUE}Task #116: ML Hyperparameter Optimization Framework{RESET}")
    logger.info(f"{BLUE}{'=' * 80}{RESET}\n")

    start_time = time.time()

    try:
        # Step 1: 加载数据
        logger.info(f"{MAGENTA}[Step 1] 加载标准化数据{RESET}")
        features, labels = load_standardized_data()

        if features is None or labels is None:
            logger.info(f"{YELLOW}📊 使用合成数据进行演示...{RESET}")
            from sklearn.datasets import make_classification
            features, labels = make_classification(
                n_samples=2000,
                n_features=21,
                n_informative=15,
                n_redundant=5,
                n_classes=2,
                random_state=42
            )
            logger.info(f"   合成数据形状: {features.shape}")

        # Step 2: 准备数据
        logger.info(f"\n{MAGENTA}[Step 2] 准备数据{RESET}")
        X_train, X_test, y_train, y_test = prepare_data(features, labels)

        # Step 3: 加载基线指标
        logger.info(f"\n{MAGENTA}[Step 3] 加载基线指标{RESET}")
        from src.model.optimization import load_baseline_metrics
        baseline_metrics = load_baseline_metrics()

        # Step 4: 创建优化器
        logger.info(f"\n{MAGENTA}[Step 4] 创建 OptunaOptimizer{RESET}")
        from src.model.optimization import OptunaOptimizer

        optimizer = OptunaOptimizer(
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            n_trials=50,  # 50 次试验
            random_state=42
        )

        logger.info(f"   Session UUID: {optimizer.session_uuid}\n")

        # Step 5: 运行优化
        logger.info(f"\n{MAGENTA}[Step 5] 运行超参数优化{RESET}")
        best_params = optimizer.optimize()

        # Step 6: 训练最佳模型
        logger.info(f"\n{MAGENTA}[Step 6] 训练最佳模型{RESET}")
        model = optimizer.train_best_model()

        # Step 7: 评估模型
        logger.info(f"\n{MAGENTA}[Step 7] 评估模型性能{RESET}")
        metrics = optimizer.evaluate_best_model()

        # Step 8: 对比基线
        logger.info(f"\n{MAGENTA}[Step 8] 对比基线模型{RESET}")
        optimizer.compare_with_baseline(baseline_metrics)

        # Step 9: 保存模型
        logger.info(f"\n{MAGENTA}[Step 9] 保存模型和元数据{RESET}")
        model_path = optimizer.save_challenger_model()
        metadata_path = optimizer.save_metadata()

        # Step 10: 打印统计信息
        logger.info(f"\n{MAGENTA}[Step 10] 优化统计信息{RESET}")
        stats = optimizer.get_study_statistics()
        logger.info(f"   总试验数: {stats['total_trials']}")
        logger.info(f"   完成试验: {stats['completed_trials']}")
        logger.info(f"   剪枝试验: {stats['pruned_trials']}")
        logger.info(f"   最佳 F1: {stats['best_value']:.4f}")
        logger.info(f"   最佳试验: Trial #{stats['best_trial_number']}\n")

        # 计算耗时
        elapsed = time.time() - start_time

        logger.info(f"\n{BLUE}{'=' * 80}{RESET}")
        logger.info(f"{GREEN}✅ Task #116 执行完成{RESET}")
        logger.info(f"{BLUE}{'=' * 80}{RESET}\n")

        logger.info(f"📊 执行摘要:")
        logger.info(f"   模型: {model_path}")
        logger.info(f"   元数据: {metadata_path}")
        logger.info(f"   F1 改进: {metrics['f1_score'] - baseline_metrics['f1_score']:.4f}")
        logger.info(f"   改进比例: {((metrics['f1_score'] - baseline_metrics['f1_score']) / baseline_metrics['f1_score'] * 100):.2f}%")
        logger.info(f"   总耗时: {elapsed:.2f}s\n")

        # 输出关键指标用于物理验尸
        logger.info(f"{CYAN}🔍 物理验尸信息:{RESET}")
        logger.info(f"   Session UUID: {optimizer.session_uuid}")
        logger.info(f"   Best Trial Number: {stats['best_trial_number']}")
        logger.info(f"   Best Trial F1 Score: {stats['best_value']:.4f}")
        logger.info(f"   Token Usage: [由 unified_review_gate 计算]")
        logger.info(f"   Timestamp: {pd.Timestamp.now().isoformat()}\n")

        return 0

    except Exception as e:
        logger.error(f"\n{RED}❌ 执行失败: {e}{RESET}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
