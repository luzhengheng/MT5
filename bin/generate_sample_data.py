#!/usr/bin/env python3
"""
生成示例数据用于测试机器学习训练管道

创建模拟的特征、标签、样本权重和预测时间数据
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import logging

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_data():
    """生成示例数据"""
    logger.info("开始生成示例数据...")

    # 配置
    n_samples = 10000
    n_features = 30
    start_date = '2022-01-01'

    # 生成时间索引
    dates = pd.date_range(start_date, periods=n_samples, freq='H')

    # 生成特征 (模拟金融特征)
    np.random.seed(42)

    features = {}

    # 基础特征
    for i in range(10):
        features[f'feature_basic_{i}'] = np.random.randn(n_samples)

    # 技术指标特征
    for i in range(5):
        features[f'rsi_{i}'] = np.random.uniform(0, 100, n_samples)
        features[f'macd_{i}'] = np.random.randn(n_samples) * 0.5

    # 分数差分特征
    for i in range(3):
        features[f'frac_diff_close_{i}'] = np.random.randn(n_samples) * 0.01

    # 滚动统计特征
    for i in range(5):
        features[f'rolling_mean_{i}'] = np.random.randn(n_samples) * 0.5

    # 横截面特征
    for i in range(3):
        features[f'cross_section_rank_{i}'] = np.random.uniform(0, 1, n_samples)

    # 情绪特征
    for i in range(4):
        features[f'sentiment_score_{i}'] = np.random.uniform(-1, 1, n_samples)

    # 创建 DataFrame
    features_df = pd.DataFrame(features, index=dates)

    # 生成标签 (三分类: 0=下跌, 1=横盘, 2=上涨)
    # 使用特征的线性组合 + 噪声
    signal = (
        features_df['feature_basic_0'] * 0.3 +
        features_df['rsi_0'] / 100 * 0.2 +
        features_df['frac_diff_close_0'] * 10 +
        np.random.randn(n_samples) * 0.5
    )

    labels = pd.Series(
        pd.cut(signal, bins=3, labels=[0, 1, 2]).astype(int),
        index=dates,
        name='label'
    )

    # 生成样本权重 (根据收益率的绝对值)
    returns = np.abs(signal) + 0.1
    weights = returns / returns.sum()
    weights_df = pd.DataFrame({'weight': weights}, index=dates)

    # 生成预测时间 (标签结束时间 = 当前时间 + 5 天)
    pred_times = pd.DataFrame({
        'pred_time': dates + pd.Timedelta(days=5)
    }, index=dates)

    # 保存数据
    output_dir = Path('/opt/mt5-crs/outputs/features')
    output_dir.mkdir(parents=True, exist_ok=True)

    features_df.to_parquet(output_dir / 'features.parquet')
    labels.to_frame().to_parquet(output_dir / 'labels.parquet')
    weights_df.to_parquet(output_dir / 'sample_weights.parquet')
    pred_times.to_parquet(output_dir / 'pred_times.parquet')

    logger.info(f"示例数据已保存至: {output_dir}")
    logger.info(f"  特征: {features_df.shape}")
    logger.info(f"  标签分布: {labels.value_counts().to_dict()}")
    logger.info(f"  样本权重: {weights_df.shape}")
    logger.info(f"  预测时间: {pred_times.shape}")

    logger.info("\n✅ 示例数据生成完成!")
    logger.info("现在可以运行: python bin/train_ml_model.py")


if __name__ == "__main__":
    generate_sample_data()
