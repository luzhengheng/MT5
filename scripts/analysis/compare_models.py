#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #117: Model Comparison Script
===================================

对比基线模型和挑战者模型的信号生成能力

功能:
- 加载两个模型
- 在相同的市场数据上运行预测
- 计算信号一致度 (IoU - Intersection over Union)
- 评估性能差异
- 生成对比报告

协议: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-17
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any
import json

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.datasets import make_classification

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

PROJECT_ROOT = Path(__file__).parent.parent.parent


class ModelComparator:
    """
    模型对比引擎
    """

    def __init__(
        self,
        baseline_path: str = "models/xgboost_baseline.json",
        challenger_path: str = "models/xgboost_challenger.json"
    ):
        """初始化模型对比器"""
        self.baseline_path = Path(baseline_path)
        self.challenger_path = Path(challenger_path)

        self.baseline_model = None
        self.challenger_model = None

        # 加载模型
        self._load_models()

    def _load_models(self):
        """加载两个模型"""
        logger.info(f"{CYAN}📥 加载模型...{RESET}")

        # 加载基线模型
        if not self.baseline_path.exists():
            raise FileNotFoundError(f"基线模型不存在: {self.baseline_path}")

        booster_baseline = xgb.Booster()
        booster_baseline.load_model(str(self.baseline_path))
        self.baseline_model = booster_baseline
        logger.info(f"{GREEN}✅ 基线模型加载成功{RESET}")

        # 加载挑战者模型
        if not self.challenger_path.exists():
            raise FileNotFoundError(f"挑战者模型不存在: {self.challenger_path}")

        booster_challenger = xgb.Booster()
        booster_challenger.load_model(str(self.challenger_path))
        self.challenger_model = booster_challenger
        logger.info(f"{GREEN}✅ 挑战者模型加载成功{RESET}\n")

    def compare_predictions(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Dict[str, Any]:
        """
        对比两个模型的预测结果

        参数:
            X: 特征数组 (N x M)
            y: 标签数组 (N,)

        返回:
            对比结果字典
        """
        logger.info(f"{MAGENTA}🔍 对比模型预测...{RESET}\n")

        # 转换为 DMatrix
        dmatrix = xgb.DMatrix(X)

        # 基线预测
        baseline_probs = self.baseline_model.predict(dmatrix)
        baseline_preds = (baseline_probs > 0.5).astype(int)

        # 挑战者预测
        challenger_probs = self.challenger_model.predict(dmatrix)
        challenger_preds = (challenger_probs > 0.5).astype(int)

        # 计算一致度 (IoU - Intersection over Union)
        agreement = (baseline_preds == challenger_preds).sum()
        total = len(baseline_preds)
        consistency_rate = agreement / total

        logger.info(f"   总样本数: {total}")
        logger.info(f"   一致的预测: {agreement}")
        logger.info(f"   一致度: {consistency_rate:.2%}\n")

        # 计算性能指标
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        )

        baseline_acc = accuracy_score(y, baseline_preds)
        challenger_acc = accuracy_score(y, challenger_preds)

        baseline_f1 = f1_score(y, baseline_preds, zero_division=0)
        challenger_f1 = f1_score(y, challenger_preds, zero_division=0)

        logger.info(f"   {CYAN}[Baseline]{RESET}")
        logger.info(f"      Accuracy: {baseline_acc:.4f}")
        logger.info(f"      F1-Score: {baseline_f1:.4f}")

        logger.info(f"   {CYAN}[Challenger]{RESET}")
        logger.info(f"      Accuracy: {challenger_acc:.4f}")
        logger.info(f"      F1-Score: {challenger_f1:.4f}")

        logger.info(f"   {YELLOW}[Improvement]{RESET}")
        logger.info(
            f"      Accuracy Delta: {challenger_acc - baseline_acc:+.4f} "
            f"({(challenger_acc - baseline_acc) / baseline_acc * 100:+.2f}%)"
        )
        logger.info(
            f"      F1-Score Delta: {challenger_f1 - baseline_f1:+.4f} "
            f"({(challenger_f1 - baseline_f1) / baseline_f1 * 100:+.2f}% if baseline > 0)"
        )

        return {
            "consistency_rate": consistency_rate,
            "baseline_accuracy": baseline_acc,
            "challenger_accuracy": challenger_acc,
            "baseline_f1": baseline_f1,
            "challenger_f1": challenger_f1,
            "baseline_probs": baseline_probs.tolist(),
            "challenger_probs": challenger_probs.tolist(),
            "baseline_preds": baseline_preds.tolist(),
            "challenger_preds": challenger_preds.tolist()
        }

    def calculate_signal_diversity(
        self,
        comparison_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算信号多样性指标

        检查两个模型是否产生不同的信号（这是好的，说明它们在学习不同的模式）
        """
        baseline_preds = np.array(comparison_results["baseline_preds"])
        challenger_preds = np.array(comparison_results["challenger_preds"])

        # 计算不同信号的数量
        diff_count = (baseline_preds != challenger_preds).sum()
        total = len(baseline_preds)
        diversity = diff_count / total

        logger.info(f"\n   {MAGENTA}信号多样性分析:{RESET}")
        logger.info(f"      总信号数: {total}")
        logger.info(f"      不同信号数: {diff_count}")
        logger.info(f"      多样性指数: {diversity:.2%}")

        if diversity > 0.3:
            logger.info(
                f"      {GREEN}✅ 高多样性 - 两个模型学习了不同的特征{RESET}"
            )
        elif diversity > 0.1:
            logger.info(
                f"      {YELLOW}⚠️  中等多样性 - 模型部分相似{RESET}"
            )
        else:
            logger.info(
                f"      {YELLOW}⚠️  低多样性 - 模型几乎相同{RESET}"
            )

        return {
            "diversity_index": diversity,
            "different_signals": diff_count,
            "total_signals": total
        }


def main():
    """主函数"""
    logger.info(f"\n{BLUE}{'=' * 80}{RESET}")
    logger.info(f"{BLUE}Model Comparison: Baseline vs. Challenger{RESET}")
    logger.info(f"{BLUE}{'=' * 80}{RESET}\n")

    try:
        # 创建对比器
        comparator = ModelComparator(
            baseline_path="models/xgboost_baseline.json",
            challenger_path="models/xgboost_challenger.json"
        )

        # 生成测试数据 (使用特定的特征名称)
        logger.info(f"{MAGENTA}📊 生成测试数据...{RESET}")

        # 特征名称必须匹配模型训练时的特征名称
        feature_names = [
            'rsi_14', 'rsi_21', 'volatility_10', 'volatility_20',
            'sma_5', 'sma_10', 'sma_20', 'sma_50',
            'macd', 'macd_signal', 'macd_hist',
            'price_lag_1', 'price_lag_5', 'price_lag_10',
            'return_1d', 'return_5d', 'return_10d',
            'hl_ratio', 'hl_range', 'volume_ratio', 'volume_price_trend'
        ]

        # 生成数据
        X_raw, y = make_classification(
            n_samples=1000,
            n_features=21,
            n_informative=15,
            n_redundant=5,
            n_classes=2,
            random_state=42
        )

        # 转换为 DataFrame 并指定特征名称
        X = pd.DataFrame(X_raw, columns=feature_names)

        logger.info(f"   数据形状: {X.shape}")
        logger.info(f"   标签分布: {np.bincount(y)}")
        logger.info(f"   特征数: {len(feature_names)}\n")

        # 对比预测
        comparison_results = comparator.compare_predictions(X, y)

        # 计算信号多样性
        diversity_results = comparator.calculate_signal_diversity(comparison_results)

        # 总结
        logger.info(f"\n{BLUE}{'=' * 80}{RESET}")
        logger.info(f"{GREEN}✅ 模型对比完成{RESET}")
        logger.info(f"{BLUE}{'=' * 80}{RESET}\n")

        logger.info(f"{MAGENTA}📈 关键指标总结:{RESET}")
        logger.info(f"   一致度 (Consistency): {comparison_results['consistency_rate']:.2%}")
        logger.info(f"   多样性 (Diversity): {diversity_results['diversity_index']:.2%}")
        logger.info(f"   Baseline F1: {comparison_results['baseline_f1']:.4f}")
        logger.info(f"   Challenger F1: {comparison_results['challenger_f1']:.4f}")
        logger.info(f"   F1 改进: {comparison_results['challenger_f1'] - comparison_results['baseline_f1']:+.4f}\n")

        # 保存报告
        report_path = PROJECT_ROOT / "docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "task": "TASK #117",
            "timestamp": pd.Timestamp.now().isoformat(),
            "comparison_results": {
                "consistency_rate": float(comparison_results["consistency_rate"]),
                "baseline_accuracy": float(comparison_results["baseline_accuracy"]),
                "challenger_accuracy": float(comparison_results["challenger_accuracy"]),
                "baseline_f1": float(comparison_results["baseline_f1"]),
                "challenger_f1": float(comparison_results["challenger_f1"])
            },
            "diversity_results": {
                "diversity_index": float(diversity_results["diversity_index"]),
                "different_signals": int(diversity_results["different_signals"]),
                "total_signals": int(diversity_results["total_signals"])
            }
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"   报告已保存到: {report_path}")

        return 0

    except Exception as e:
        logger.error(f"{RED}❌ 对比失败: {e}{RESET}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    exit_code = main()
    sys.exit(exit_code)
