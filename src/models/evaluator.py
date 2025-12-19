"""
模型评估器 - ROC/PR 曲线、概率校准、SHAP 分析

提供全面的模型评估和可解释性分析
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Optional, List
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, roc_curve, precision_recall_curve,
    confusion_matrix, classification_report, log_loss
)
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SHAP 是可选依赖
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP 未安装,部分功能将不可用。安装: pip install shap")


class ModelEvaluator:
    """
    模型评估器

    提供:
    1. 分类指标计算 (Accuracy, F1, Precision, Recall, AUC)
    2. ROC 曲线 & PR 曲线
    3. 混淆矩阵
    4. 概率校准曲线
    5. SHAP 分析 (可选)
    """

    def __init__(self, output_dir: str = '/opt/mt5-crs/outputs/plots'):
        """
        Args:
            output_dir: 图表输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray,
        prefix: str = 'model'
    ) -> Dict[str, float]:
        """
        全面评估模型

        Args:
            y_true: 真实标签
            y_pred: 预测标签
            y_pred_proba: 预测概率 (0-1)
            prefix: 文件名前缀

        Returns:
            评估指标字典
        """
        logger.info(f"开始模型评估: {len(y_true)} 样本")

        # 计算指标
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'f1_score': f1_score(y_true, y_pred, average='weighted'),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'log_loss': log_loss(y_true, y_pred_proba)
        }

        try:
            metrics['auc_roc'] = roc_auc_score(y_true, y_pred_proba)
        except:
            metrics['auc_roc'] = 0.0

        # 打印指标
        logger.info("评估指标:")
        for metric_name, value in metrics.items():
            logger.info(f"  {metric_name}: {value:.4f}")

        # 生成可视化
        self.plot_roc_pr_curves(y_true, y_pred_proba, prefix)
        self.plot_confusion_matrix(y_true, y_pred, prefix)
        self.plot_calibration_curve(y_true, y_pred_proba, prefix)

        return metrics

    def plot_roc_pr_curves(
        self,
        y_true: pd.Series,
        y_pred_proba: np.ndarray,
        prefix: str = 'model'
    ):
        """
        绘制 ROC 曲线和 PR 曲线

        Args:
            y_true: 真实标签
            y_pred_proba: 预测概率
            prefix: 文件名前缀
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # ROC 曲线
        try:
            fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
            auc = roc_auc_score(y_true, y_pred_proba)

            axes[0].plot(fpr, tpr, label=f'ROC (AUC = {auc:.3f})', linewidth=2)
            axes[0].plot([0, 1], [0, 1], 'k--', label='Random')
            axes[0].set_xlabel('False Positive Rate', fontsize=12)
            axes[0].set_ylabel('True Positive Rate', fontsize=12)
            axes[0].set_title('ROC Curve', fontsize=14)
            axes[0].legend(fontsize=11)
            axes[0].grid(alpha=0.3)
        except Exception as e:
            logger.warning(f"ROC 曲线绘制失败: {e}")

        # PR 曲线
        try:
            precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)

            axes[1].plot(recall, precision, label='PR Curve', linewidth=2)
            axes[1].set_xlabel('Recall', fontsize=12)
            axes[1].set_ylabel('Precision', fontsize=12)
            axes[1].set_title('Precision-Recall Curve', fontsize=14)
            axes[1].legend(fontsize=11)
            axes[1].grid(alpha=0.3)
        except Exception as e:
            logger.warning(f"PR 曲线绘制失败: {e}")

        plt.tight_layout()
        output_path = self.output_dir / f'{prefix}_roc_pr_curves.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"ROC/PR 曲线已保存: {output_path}")

    def plot_confusion_matrix(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray,
        prefix: str = 'model'
    ):
        """
        绘制混淆矩阵

        Args:
            y_true: 真实标签
            y_pred: 预测标签
            prefix: 文件名前缀
        """
        cm = confusion_matrix(y_true, y_pred)

        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Class 0', 'Class 1'],
            yticklabels=['Class 0', 'Class 1'],
            cbar_kws={'label': 'Count'}
        )
        plt.xlabel('Predicted Label', fontsize=12)
        plt.ylabel('True Label', fontsize=12)
        plt.title('Confusion Matrix', fontsize=14)

        output_path = self.output_dir / f'{prefix}_confusion_matrix.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"混淆矩阵已保存: {output_path}")

    def plot_calibration_curve(
        self,
        y_true: pd.Series,
        y_pred_proba: np.ndarray,
        prefix: str = 'model',
        n_bins: int = 10
    ):
        """
        绘制概率校准曲线

        检查模型输出的概率是否可靠:
        - 如果模型说 80%,实际应该有 ~80% 的样本是正类
        - 完美校准: 曲线接近对角线

        Args:
            y_true: 真实标签
            y_pred_proba: 预测概率
            prefix: 文件名前缀
            n_bins: 分箱数
        """
        try:
            fraction_of_positives, mean_predicted_value = calibration_curve(
                y_true, y_pred_proba, n_bins=n_bins, strategy='uniform'
            )

            plt.figure(figsize=(8, 6))
            plt.plot(mean_predicted_value, fraction_of_positives, 's-', label='Model', linewidth=2)
            plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')

            plt.xlabel('Mean Predicted Probability', fontsize=12)
            plt.ylabel('Fraction of Positives', fontsize=12)
            plt.title('Probability Calibration Curve', fontsize=14)
            plt.legend(fontsize=11)
            plt.grid(alpha=0.3)

            output_path = self.output_dir / f'{prefix}_calibration_curve.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"校准曲线已保存: {output_path}")
        except Exception as e:
            logger.warning(f"校准曲线绘制失败: {e}")

    def plot_shap_summary(
        self,
        model,
        X: pd.DataFrame,
        prefix: str = 'model',
        max_display: int = 20
    ):
        """
        SHAP Summary Plot (蜂群图)

        解释每个特征对预测的贡献

        Args:
            model: LightGBM 模型
            X: 特征矩阵
            prefix: 文件名前缀
            max_display: 显示特征数
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP 未安装,跳过 SHAP 分析")
            return

        try:
            logger.info("计算 SHAP 值 (可能需要几分钟)...")

            # 创建 SHAP Explainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)

            # 如果是二分类,取正类的 SHAP 值
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            # Summary Plot
            plt.figure(figsize=(12, 8))
            shap.summary_plot(
                shap_values, X,
                max_display=max_display,
                show=False
            )

            output_path = self.output_dir / f'{prefix}_shap_summary.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"SHAP 汇总图已保存: {output_path}")

            # Bar Plot (特征重要性)
            plt.figure(figsize=(12, 8))
            shap.summary_plot(
                shap_values, X,
                plot_type='bar',
                max_display=max_display,
                show=False
            )

            output_path = self.output_dir / f'{prefix}_shap_importance.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"SHAP 重要性图已保存: {output_path}")

        except Exception as e:
            logger.warning(f"SHAP 分析失败: {e}")

    def generate_report(
        self,
        y_true: pd.Series,
        y_pred: np.ndarray,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成分类报告

        Args:
            y_true: 真实标签
            y_pred: 预测标签
            output_path: 输出路径 (可选)

        Returns:
            报告字符串
        """
        report = classification_report(y_true, y_pred, digits=4)

        logger.info(f"\n分类报告:\n{report}")

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            logger.info(f"报告已保存: {output_path}")

        return report


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("测试评估器模块")
    print("=" * 80)

    # 创建模拟数据
    np.random.seed(42)
    n_samples = 1000

    y_true = pd.Series(np.random.choice([0, 1], n_samples, p=[0.6, 0.4]))
    y_pred_proba = np.clip(y_true + np.random.randn(n_samples) * 0.3, 0, 1)
    y_pred = (y_pred_proba > 0.5).astype(int)

    # 测试评估器
    evaluator = ModelEvaluator(output_dir='/opt/mt5-crs/outputs/plots')

    print("\n1. 评估指标:")
    metrics = evaluator.evaluate(y_true, y_pred, y_pred_proba, prefix='test')

    print("\n2. 生成报告:")
    report = evaluator.generate_report(
        y_true, y_pred,
        output_path='/opt/mt5-crs/outputs/test_classification_report.txt'
    )

    print("\n✅ 评估器测试完成!")
