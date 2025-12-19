#!/usr/bin/env python3
"""
迭代 2: 基础特征工程
功能：
1. 加载价格数据
2. 加载新闻情感数据
3. 整合价格 + 情感
4. 计算基础特征（32 维）
5. 生成特征质量报告
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/opt/mt5-crs')

import yaml
import pandas as pd
import numpy as np

from src.feature_engineering.feature_engineer import FeatureEngineer

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_feature_quality_report(results: dict) -> pd.DataFrame:
    """生成特征质量报告

    Args:
        results: {symbol: DataFrame} 字典

    Returns:
        质量报告 DataFrame
    """
    logger.info("生成特征质量报告...")

    reports = []

    for symbol, df in results.items():
        # 识别特征列
        base_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                       'adjusted_close', 'quality']
        feature_columns = [col for col in df.columns if col not in base_columns]

        # 统计信息
        report = {
            'symbol': symbol,
            'total_records': len(df),
            'total_features': len(feature_columns),
            'date_start': df['date'].min(),
            'date_end': df['date'].max(),
            'completeness_rate': (1 - df[feature_columns].isnull().sum().sum() / (len(df) * len(feature_columns))),
            'has_sentiment': (df['sentiment_mean'] != 0).any(),
            'news_days': (df['news_count'] > 0).sum(),
        }

        # 特征统计
        numeric_features = df[feature_columns].select_dtypes(include=[np.number])
        report['avg_feature_mean'] = numeric_features.mean().mean()
        report['avg_feature_std'] = numeric_features.std().mean()

        reports.append(report)

    report_df = pd.DataFrame(reports)

    # 保存报告
    report_path = Path('/opt/mt5-crs/var/reports')
    report_path.mkdir(parents=True, exist_ok=True)

    report_file = report_path / 'iteration2_feature_quality_report.csv'
    report_df.to_csv(report_file, index=False)

    logger.info(f"特征质量报告已保存到: {report_file}")

    return report_df


def compute_feature_statistics(results: dict) -> dict:
    """计算特征统计信息

    Args:
        results: {symbol: DataFrame} 字典

    Returns:
        统计信息字典
    """
    logger.info("计算特征统计信息...")

    # 合并所有资产的特征
    all_features = []
    for symbol, df in results.items():
        all_features.append(df)

    combined_df = pd.concat(all_features, ignore_index=True)

    # 识别特征列
    base_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                   'adjusted_close', 'quality']
    feature_columns = [col for col in combined_df.columns if col not in base_columns]

    stats = {
        'total_symbols': len(results),
        'total_records': len(combined_df),
        'total_features': len(feature_columns),
        'feature_list': feature_columns,
        'date_range': f"{combined_df['date'].min()} to {combined_df['date'].max()}",
        'completeness_rate': (1 - combined_df[feature_columns].isnull().sum().sum() /
                             (len(combined_df) * len(feature_columns))),
        'symbols_with_sentiment': (combined_df.groupby('symbol')['sentiment_mean'].apply(
            lambda x: (x != 0).any()
        )).sum(),
    }

    return stats


def generate_summary_report(results: dict, quality_report: pd.DataFrame, stats: dict):
    """生成汇总报告

    Args:
        results: 结果字典
        quality_report: 质量报告
        stats: 统计信息
    """
    logger.info("=" * 60)
    logger.info("生成迭代 2 汇总报告")
    logger.info("=" * 60)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("迭代 2: 基础特征工程 - 执行报告")
    report_lines.append("=" * 80)
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 数据处理统计
    report_lines.append("## 1. 数据处理")
    report_lines.append(f"  - 处理资产数: {stats['total_symbols']}")
    report_lines.append(f"  - 总记录数: {stats['total_records']}")
    report_lines.append(f"  - 日期范围: {stats['date_range']}")
    report_lines.append("")

    # 特征统计
    report_lines.append("## 2. 特征工程")
    report_lines.append(f"  - 总特征数: {stats['total_features']}")
    report_lines.append(f"  - 特征完整率: {stats['completeness_rate']:.2%}")
    report_lines.append(f"  - 包含情感数据的资产: {stats['symbols_with_sentiment']}/{stats['total_symbols']}")
    report_lines.append("")

    # 特征类别
    report_lines.append("  - 特征类别:")
    report_lines.append("    * 趋势类: 10 个 (EMA, SMA, 交叉信号等)")
    report_lines.append("    * 动量类: 8 个 (RSI, MACD, ROC, Stochastic, Williams %R)")
    report_lines.append("    * 波动类: 6 个 (ATR, Bollinger Bands, 已实现波动率)")
    report_lines.append("    * 成交量类: 3 个 (Volume SMA, Volume Ratio, OBV)")
    report_lines.append("    * 回报类: 5 个 (1/3/5/10/20 日回报)")
    report_lines.append("    * 情感类: 3 个 (情感均值、动量、移动平均)")
    report_lines.append("")

    # 数据质量
    report_lines.append("## 3. 数据质量")
    report_lines.append(f"  - 平均完整率: {quality_report['completeness_rate'].mean():.2%}")
    report_lines.append(f"  - 最高完整率: {quality_report['completeness_rate'].max():.2%} "
                       f"({quality_report.loc[quality_report['completeness_rate'].idxmax(), 'symbol']})")
    report_lines.append(f"  - 最低完整率: {quality_report['completeness_rate'].min():.2%} "
                       f"({quality_report.loc[quality_report['completeness_rate'].idxmin(), 'symbol']})")
    report_lines.append("")

    # 情感数据覆盖
    report_lines.append("## 4. 情感数据覆盖")
    report_lines.append(f"  - 有情感数据的资产: {quality_report['has_sentiment'].sum()}/{len(quality_report)}")
    report_lines.append(f"  - 平均新闻天数: {quality_report['news_days'].mean():.1f} 天")
    report_lines.append("")

    # 输出文件
    report_lines.append("## 5. 输出文件")
    report_lines.append("  - 特征数据: /opt/mt5-crs/data_lake/features_daily/")
    report_lines.append("  - 质量报告: /opt/mt5-crs/var/reports/iteration2_feature_quality_report.csv")
    report_lines.append("")

    # 示例特征列表
    report_lines.append("## 6. 特征列表示例（前 20 个）")
    for i, feat in enumerate(stats['feature_list'][:20], 1):
        report_lines.append(f"  {i:2d}. {feat}")
    if len(stats['feature_list']) > 20:
        report_lines.append(f"  ... 还有 {len(stats['feature_list']) - 20} 个特征")
    report_lines.append("")

    # 下一步
    report_lines.append("## 7. 下一步 (迭代 3)")
    report_lines.append("  - 实现 Fractional Differentiation（6 维）")
    report_lines.append("  - 实现 Rolling Statistics（12 维）")
    report_lines.append("  - 实现 Cross-Sectional Rank（6 维）")
    report_lines.append("  - 实现 Sentiment Momentum（8 维）")
    report_lines.append("  - 实现 Triple Barrier Labeling")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("迭代 2 完成！✅")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)

    # 保存报告
    report_file = Path('/opt/mt5-crs/var/reports/iteration2_report.txt')
    report_file.write_text(report_text)

    # 打印报告
    print("\n" + report_text)

    logger.info(f"汇总报告已保存到: {report_file}")


def main():
    """主函数"""
    logger.info("开始执行迭代 2: 基础特征工程")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 加载配置
    with open('/opt/mt5-crs/config/features.yaml', 'r') as f:
        features_config = yaml.safe_load(f)

    with open('/opt/mt5-crs/config/assets.yaml', 'r') as f:
        assets_config = yaml.safe_load(f)

    try:
        # 创建特征工程器
        engineer = FeatureEngineer(features_config)

        # 定义要处理的资产（简化版：使用已有价格数据的资产）
        # 实际环境：处理所有 55 个资产
        test_symbols = [
            'AAPL.US', 'MSFT.US', 'NVDA.US', 'TSLA.US', 'GOOGL.US',
            'BTC-USD', 'ETH-USD',
            'EURUSD',
            'GSPC.INDX'
        ]

        logger.info(f"准备处理 {len(test_symbols)} 个资产")

        # 批量处理
        results = engineer.process_multiple_symbols(test_symbols)

        if not results:
            logger.error("没有成功处理任何资产")
            sys.exit(1)

        # 生成特征质量报告
        quality_report = generate_feature_quality_report(results)

        # 计算统计信息
        stats = compute_feature_statistics(results)

        # 生成汇总报告
        generate_summary_report(results, quality_report, stats)

        logger.info(f"迭代 2 成功完成！结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.error(f"迭代 2 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
