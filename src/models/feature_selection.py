"""
特征选择与去噪模块 - Clustered Feature Importance

解决高共线性特征带来的问题:
1. 特征重要性被稀释 (Substitution Effect)
2. 模型解释性降低
3. 训练不稳定

来源: "Advances in Financial Machine Learning" by Marcos Lopez de Prado
Chapter 8: Feature Importance
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.metrics import log_loss, accuracy_score
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureClusterer:
    """
    特征聚类器 - 基于层次聚类的特征分组

    核心思路:
    1. 计算特征之间的相关性矩阵
    2. 使用层次聚类 (Hierarchical Clustering) 将相似特征分组
    3. 每组选择一个代表性特征,或基于 MDA 评估整组重要性

    优势:
    - 降低特征冗余
    - 提升模型解释性
    - 加速训练
    """

    def __init__(self, correlation_threshold: float = 0.7):
        """
        Args:
            correlation_threshold: 相关性阈值,超过此值的特征会被分到同一组
        """
        self.correlation_threshold = correlation_threshold
        self.linkage_matrix = None
        self.clusters = None
        self.cluster_labels = None

    def fit(self, X: pd.DataFrame) -> 'FeatureClusterer':
        """
        拟合特征聚类模型

        Args:
            X: 特征矩阵

        Returns:
            self
        """
        logger.info(f"开始特征聚类: {X.shape[1]} 个特征")

        # 计算相关性矩阵
        corr_matrix = X.corr().abs()

        # 转换为距离矩阵 (1 - |correlation|)
        distance_matrix = 1 - corr_matrix
        distance_condensed = squareform(distance_matrix, checks=False)

        # 层次聚类
        self.linkage_matrix = linkage(distance_condensed, method='ward')

        # 根据阈值切割树
        distance_threshold = 1 - self.correlation_threshold
        self.cluster_labels = fcluster(
            self.linkage_matrix,
            distance_threshold,
            criterion='distance'
        )

        # 构建聚类字典 {cluster_id: [feature_names]}
        self.clusters = {}
        for feature_name, cluster_id in zip(X.columns, self.cluster_labels):
            if cluster_id not in self.clusters:
                self.clusters[cluster_id] = []
            self.clusters[cluster_id].append(feature_name)

        logger.info(f"聚类完成: 发现 {len(self.clusters)} 个特征群组")
        for cluster_id, features in self.clusters.items():
            if len(features) > 1:
                logger.info(f"  群组 {cluster_id}: {len(features)} 个特征 - {features[:3]}...")

        return self

    def get_representative_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model,
        method: str = 'importance'
    ) -> List[str]:
        """
        从每个群组中选择代表性特征

        Args:
            X: 特征矩阵
            y: 标签
            model: 已训练的模型 (用于计算特征重要性)
            method: 选择方法
                - 'importance': 选择特征重要性最高的
                - 'variance': 选择方差最大的
                - 'first': 选择每组的第一个特征

        Returns:
            代表性特征名称列表
        """
        if self.clusters is None:
            raise ValueError("请先调用 fit() 方法")

        representative_features = []

        for cluster_id, features in self.clusters.items():
            if len(features) == 1:
                representative_features.append(features[0])
            else:
                if method == 'importance':
                    # 选择特征重要性最高的
                    if hasattr(model, 'feature_importances_'):
                        importances = model.feature_importances_
                        feature_names = model.feature_name_
                        cluster_importances = {
                            f: importances[feature_names.index(f)]
                            for f in features if f in feature_names
                        }
                        best_feature = max(cluster_importances, key=cluster_importances.get)
                    else:
                        best_feature = features[0]
                elif method == 'variance':
                    # 选择方差最大的
                    variances = X[features].var()
                    best_feature = variances.idxmax()
                else:  # 'first'
                    best_feature = features[0]

                representative_features.append(best_feature)

        logger.info(f"选择了 {len(representative_features)} 个代表性特征")
        return representative_features

    def plot_dendrogram(
        self,
        feature_names: List[str],
        output_path: Optional[str] = None
    ):
        """
        绘制特征聚类树状图

        Args:
            feature_names: 特征名称列表
            output_path: 输出路径 (可选)
        """
        if self.linkage_matrix is None:
            raise ValueError("请先调用 fit() 方法")

        plt.figure(figsize=(20, 10))
        dendrogram(
            self.linkage_matrix,
            labels=feature_names,
            leaf_rotation=90,
            leaf_font_size=8
        )
        plt.title('Feature Hierarchical Clustering Dendrogram', fontsize=16)
        plt.xlabel('Feature Name', fontsize=12)
        plt.ylabel('Distance (1 - |Correlation|)', fontsize=12)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"树状图已保存至: {output_path}")

        plt.close()


class MDFeatureImportance:
    """
    Mean Decrease Accuracy (MDA) 特征重要性

    MDA 通过打乱单个特征的值来测量模型精度的下降程度。
    相比于 split/gain 方法,MDA 更能反映特征的真实重要性。

    流程:
    1. 在验证集上计算基准精度
    2. 逐个打乱每个特征的值
    3. 重新计算精度
    4. 重要性 = 基准精度 - 打乱后精度
    """

    @staticmethod
    def compute_importance(
        model,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        n_repeats: int = 5,
        scoring: str = 'accuracy'
    ) -> pd.Series:
        """
        计算 MDA 特征重要性

        Args:
            model: 已训练的模型
            X_val: 验证集特征
            y_val: 验证集标签
            n_repeats: 打乱重复次数 (取平均)
            scoring: 评分方法 ('accuracy' 或 'log_loss')

        Returns:
            特征重要性 Series (feature_name -> importance)
        """
        logger.info(f"计算 MDA 特征重要性: {X_val.shape[1]} 个特征, {n_repeats} 次重复")

        # 基准得分
        y_pred = model.predict(X_val)
        y_pred_proba = model.predict_proba(X_val) if hasattr(model, 'predict_proba') else None

        if scoring == 'accuracy':
            baseline_score = accuracy_score(y_val, y_pred)
        elif scoring == 'log_loss' and y_pred_proba is not None:
            baseline_score = -log_loss(y_val, y_pred_proba)
        else:
            raise ValueError(f"不支持的评分方法: {scoring}")

        logger.info(f"基准得分 ({scoring}): {baseline_score:.4f}")

        # 计算每个特征的重要性
        importances = {}

        for feature in X_val.columns:
            feature_scores = []

            for _ in range(n_repeats):
                # 复制数据并打乱单个特征
                X_val_shuffled = X_val.copy()
                X_val_shuffled[feature] = np.random.permutation(X_val_shuffled[feature].values)

                # 重新预测
                y_pred = model.predict(X_val_shuffled)

                if scoring == 'accuracy':
                    score = accuracy_score(y_val, y_pred)
                else:  # log_loss
                    y_pred_proba = model.predict_proba(X_val_shuffled)
                    score = -log_loss(y_val, y_pred_proba)

                feature_scores.append(score)

            # 重要性 = 基准得分 - 平均打乱得分
            avg_shuffled_score = np.mean(feature_scores)
            importance = baseline_score - avg_shuffled_score
            importances[feature] = importance

        # 转换为 Series 并排序
        importance_series = pd.Series(importances).sort_values(ascending=False)

        logger.info(f"Top 5 重要特征:")
        for feature, importance in importance_series.head(5).items():
            logger.info(f"  {feature}: {importance:.4f}")

        return importance_series

    @staticmethod
    def plot_importance(
        importance: pd.Series,
        top_n: int = 20,
        output_path: Optional[str] = None
    ):
        """
        绘制特征重要性图

        Args:
            importance: 特征重要性 Series
            top_n: 显示前 N 个特征
            output_path: 输出路径 (可选)
        """
        plt.figure(figsize=(12, 8))
        top_features = importance.head(top_n)

        sns.barplot(x=top_features.values, y=top_features.index, palette='viridis')
        plt.title(f'Top {top_n} Feature Importance (MDA)', fontsize=16)
        plt.xlabel('Importance (Mean Decrease Accuracy)', fontsize=12)
        plt.ylabel('Feature Name', fontsize=12)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"重要性图已保存至: {output_path}")

        plt.close()


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("测试特征选择模块")
    print("=" * 80)

    # 创建模拟数据 (带有共线性)
    np.random.seed(42)
    n_samples = 1000

    # 基础特征
    f1 = np.random.randn(n_samples)
    f2 = np.random.randn(n_samples)
    f3 = np.random.randn(n_samples)

    # 创建高相关特征
    X = pd.DataFrame({
        'feature_1': f1,
        'feature_2': f1 + np.random.randn(n_samples) * 0.1,  # 与 f1 高度相关
        'feature_3': f1 + np.random.randn(n_samples) * 0.2,  # 与 f1 相关
        'feature_4': f2,
        'feature_5': f2 + np.random.randn(n_samples) * 0.15,  # 与 f2 相关
        'feature_6': f3,
        'feature_7': np.random.randn(n_samples),  # 独立特征
        'feature_8': np.random.randn(n_samples)   # 独立特征
    })

    y = pd.Series((f1 + f2 - f3 + np.random.randn(n_samples) * 0.5 > 0).astype(int))

    # 测试特征聚类
    print("\n1. 测试特征聚类:")
    clusterer = FeatureClusterer(correlation_threshold=0.7)
    clusterer.fit(X)

    # 打印聚类结果
    print("\n聚类结果:")
    for cluster_id, features in clusterer.clusters.items():
        print(f"  群组 {cluster_id}: {features}")

    # 绘制树状图
    clusterer.plot_dendrogram(
        X.columns.tolist(),
        output_path='/opt/mt5-crs/outputs/plots/feature_dendrogram_test.png'
    )

    print("\n✅ 特征选择模块测试完成!")
