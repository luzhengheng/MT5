#!/usr/bin/env python3
"""
迭代 3: 高级特征工程
功能:
1. 加载迭代 2 的基础特征数据
2. 计算 Fractional Differentiation (6 维)
3. 计算 Rolling Statistics (12 维)
4. 计算 Cross-Sectional Rank (6 维)
5. 计算 Sentiment Momentum (8 维)
6. 计算 Adaptive Window Features (3 维)
7. 计算 Cross-Asset Features (5 维)
8. 应用 Triple Barrier Labeling
9. 生成完整特征报告 (基础 35 维 + 高级 40 维 = 75 维)
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

from src.feature_engineering.advanced_features import AdvancedFeatures
from src.feature_engineering.labeling import TripleBarrierLabeling

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_basic_features(symbol: str, data_path: str = "/opt/mt5-crs/data_lake/features_daily") -> pd.DataFrame:
    """
    加载迭代 2 生成的基础特征数据

    Args:
        symbol: 资产符号
        data_path: 数据路径

    Returns:
        基础特征 DataFrame
    """
    safe_symbol = symbol.replace('/', '_').replace('=', '_').replace('^', '_')
    file_path = Path(data_path) / f"{safe_symbol}_features.parquet"

    if not file_path.exists():
        logger.warning(f"基础特征文件不存在: {file_path}")
        return None

    try:
        df = pd.read_parquet(file_path)
        logger.info(f"加载 {symbol} 基础特征: {len(df)} 条, {len(df.columns)} 列")
        return df
    except Exception as e:
        logger.error(f"加载 {symbol} 基础特征失败: {e}")
        return None


def load_all_symbols(symbols: list, data_path: str = "/opt/mt5-crs/data_lake/features_daily") -> dict:
    """
    加载所有资产的基础特征

    Args:
        symbols: 资产列表
        data_path: 数据路径

    Returns:
        {symbol: DataFrame} 字典
    """
    logger.info(f"加载 {len(symbols)} 个资产的基础特征...")

    all_dfs = {}
    for symbol in symbols:
        df = load_basic_features(symbol, data_path)
        if df is not None:
            all_dfs[symbol] = df

    logger.info(f"成功加载 {len(all_dfs)}/{len(symbols)} 个资产")
    return all_dfs


def compute_advanced_features_for_symbol(
    symbol: str,
    df: pd.DataFrame,
    all_dfs: dict,
    reference_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    为单个资产计算高级特征

    Args:
        symbol: 资产符号
        df: 基础特征 DataFrame
        all_dfs: 所有资产的 DataFrame 字典
        reference_df: 基准资产 DataFrame (用于跨资产特征)

    Returns:
        添加了高级特征的 DataFrame
    """
    logger.info(f"{'='*60}")
    logger.info(f"计算 {symbol} 的高级特征")
    logger.info(f"{'='*60}")

    # 计算高级特征 (40 维)
    df = AdvancedFeatures.compute_all_advanced_features(
        df,
        all_dfs=all_dfs,
        reference_df=reference_df
    )

    # 应用 Triple Barrier Labeling
    df = TripleBarrierLabeling.add_labels_to_dataframe(
        df,
        price_column='close',
        upper_barrier=0.02,  # 2% 止盈
        lower_barrier=-0.02,  # -2% 止损
        max_holding_period=5,  # 5 天最大持有
        stop_loss=-0.01  # -1% 硬止损
    )

    logger.info(f"{symbol} 高级特征计算完成 ✓")
    return df


def save_advanced_features(df: pd.DataFrame, symbol: str,
                           output_path: str = "/opt/mt5-crs/data_lake/features_advanced"):
    """
    保存高级特征数据

    Args:
        df: 特征数据
        symbol: 资产符号
        output_path: 输出路径
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    safe_symbol = symbol.replace('/', '_').replace('=', '_').replace('^', '_')
    output_file = output_path / f"{safe_symbol}_features_advanced.parquet"

    df.to_parquet(output_file, engine='pyarrow', compression='gzip', index=False)
    logger.info(f"{symbol} 高级特征已保存: {output_file}")


def generate_feature_report(results: dict) -> pd.DataFrame:
    """
    生成特征质量报告

    Args:
        results: {symbol: DataFrame} 字典

    Returns:
        质量报告 DataFrame
    """
    logger.info("生成高级特征质量报告...")

    reports = []

    for symbol, df in results.items():
        # 识别特征列
        base_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                       'adjusted_close', 'quality', 'label', 'barrier_touched',
                       'holding_period', 'return', 'entry_price', 'sample_weight']
        feature_columns = [col for col in df.columns if col not in base_columns]

        # 统计信息
        report = {
            'symbol': symbol,
            'total_records': len(df),
            'total_features': len(feature_columns),
            'date_start': df['date'].min(),
            'date_end': df['date'].max(),
            'completeness_rate': (1 - df[feature_columns].isnull().sum().sum() /
                                 (len(df) * len(feature_columns))),
            'label_distribution': df['label'].value_counts().to_dict(),
            'avg_holding_period': df['holding_period'].mean(),
        }

        reports.append(report)

    report_df = pd.DataFrame(reports)

    # 保存报告
    report_path = Path('/opt/mt5-crs/var/reports')
    report_path.mkdir(parents=True, exist_ok=True)

    report_file = report_path / 'iteration3_feature_quality_report.csv'
    report_df.to_csv(report_file, index=False)

    logger.info(f"特征质量报告已保存: {report_file}")
    return report_df


def compute_statistics(results: dict) -> dict:
    """
    计算统计信息

    Args:
        results: {symbol: DataFrame} 字典

    Returns:
        统计信息字典
    """
    logger.info("计算高级特征统计信息...")

    # 合并所有资产
    all_features = []
    for symbol, df in results.items():
        all_features.append(df)

    combined_df = pd.concat(all_features, ignore_index=True)

    # 识别特征列
    base_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                   'adjusted_close', 'quality', 'label', 'barrier_touched',
                   'holding_period', 'return', 'entry_price', 'sample_weight']
    feature_columns = [col for col in combined_df.columns if col not in base_columns]

    # 按类别分组
    basic_features = [col for col in feature_columns if not any(x in col for x in
                     ['frac_diff', 'roll_', 'cs_rank', 'sentiment_', 'adaptive_', 'beta_', 'correlation_', 'alpha_'])]

    frac_diff_features = [col for col in feature_columns if 'frac_diff' in col]
    rolling_features = [col for col in feature_columns if 'roll_' in col]
    cs_features = [col for col in feature_columns if 'cs_rank' in col]
    sentiment_features = [col for col in feature_columns if 'sentiment_' in col and 'frac_diff' not in col]
    adaptive_features = [col for col in feature_columns if 'adaptive_' in col]
    cross_asset_features = [col for col in feature_columns if any(x in col for x in
                           ['beta_', 'correlation_', 'alpha_', 'relative_', 'tracking_'])]

    stats = {
        'total_symbols': len(results),
        'total_records': len(combined_df),
        'total_features': len(feature_columns),
        'basic_features_count': len(basic_features),
        'frac_diff_features_count': len(frac_diff_features),
        'rolling_features_count': len(rolling_features),
        'cs_features_count': len(cs_features),
        'sentiment_features_count': len(sentiment_features),
        'adaptive_features_count': len(adaptive_features),
        'cross_asset_features_count': len(cross_asset_features),
        'date_range': f"{combined_df['date'].min()} to {combined_df['date'].max()}",
        'completeness_rate': (1 - combined_df[feature_columns].isnull().sum().sum() /
                             (len(combined_df) * len(feature_columns))),
        'label_distribution': combined_df['label'].value_counts().to_dict(),
        'avg_holding_period': combined_df['holding_period'].mean(),
    }

    return stats


def generate_summary_report(results: dict, quality_report: pd.DataFrame, stats: dict):
    """
    生成汇总报告

    Args:
        results: 结果字典
        quality_report: 质量报告
        stats: 统计信息
    """
    logger.info("=" * 60)
    logger.info("生成迭代 3 汇总报告")
    logger.info("=" * 60)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("迭代 3: 高级特征工程 - 执行报告")
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
    report_lines.append(f"    * 基础特征: {stats['basic_features_count']} 维")
    report_lines.append(f"    * Fractional Diff: {stats['frac_diff_features_count']} 维")
    report_lines.append(f"    * Rolling Stats: {stats['rolling_features_count']} 维")
    report_lines.append(f"    * Cross-Sectional: {stats['cs_features_count']} 维")
    report_lines.append(f"    * Sentiment: {stats['sentiment_features_count']} 维")
    report_lines.append(f"    * Adaptive: {stats['adaptive_features_count']} 维")
    report_lines.append(f"    * Cross-Asset: {stats['cross_asset_features_count']} 维")
    report_lines.append(f"  - 特征完整率: {stats['completeness_rate']:.2%}")
    report_lines.append("")

    # 标签统计
    report_lines.append("## 3. Triple Barrier Labeling")
    label_dist = stats['label_distribution']
    report_lines.append(f"  - 标签分布:")
    for label, count in sorted(label_dist.items()):
        label_name = {1: '做多', -1: '做空', 0: '中性'}[label]
        pct = count / stats['total_records'] * 100
        report_lines.append(f"    * {label_name} ({label}): {count} ({pct:.1f}%)")
    report_lines.append(f"  - 平均持有期: {stats['avg_holding_period']:.2f} 天")
    report_lines.append("")

    # 数据质量
    report_lines.append("## 4. 数据质量")
    report_lines.append(f"  - 平均完整率: {quality_report['completeness_rate'].mean():.2%}")
    report_lines.append(f"  - 最高完整率: {quality_report['completeness_rate'].max():.2%} "
                       f"({quality_report.loc[quality_report['completeness_rate'].idxmax(), 'symbol']})")
    report_lines.append(f"  - 最低完整率: {quality_report['completeness_rate'].min():.2%} "
                       f"({quality_report.loc[quality_report['completeness_rate'].idxmin(), 'symbol']})")
    report_lines.append("")

    # 输出文件
    report_lines.append("## 5. 输出文件")
    report_lines.append("  - 高级特征数据: /opt/mt5-crs/data_lake/features_advanced/")
    report_lines.append("  - 质量报告: /opt/mt5-crs/var/reports/iteration3_feature_quality_report.csv")
    report_lines.append("")

    # 功能完成度
    report_lines.append("## 6. 功能完成度")
    report_lines.append("  ✅ 迭代 1: 数据采集 (100%)")
    report_lines.append("  ✅ 迭代 2: 基础特征 (100%)")
    report_lines.append("  ✅ 迭代 3: 高级特征 (100%)")
    report_lines.append("  ⏳ 迭代 4: 数据质量监控 (0%)")
    report_lines.append("  ⏳ 迭代 5: 文档和测试 (0%)")
    report_lines.append("  ⏳ 迭代 6: 性能优化 (0%)")
    report_lines.append("")
    report_lines.append("  **总体进度: 60% (3/6 迭代完成)**")
    report_lines.append("")

    # 下一步
    report_lines.append("## 7. 下一步 (迭代 4)")
    report_lines.append("  - 实现 DQ Score 计算系统")
    report_lines.append("  - 创建 Prometheus 指标导出器")
    report_lines.append("  - 设计 Grafana 仪表盘")
    report_lines.append("  - 配置告警规则")
    report_lines.append("  - 创建健康检查脚本")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("迭代 3 完成！✅")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)

    # 保存报告
    report_file = Path('/opt/mt5-crs/var/reports/iteration3_report.txt')
    report_file.write_text(report_text)

    # 打印报告
    print("\n" + report_text)

    logger.info(f"汇总报告已保存: {report_file}")


def main():
    """主函数"""
    logger.info("开始执行迭代 3: 高级特征工程")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 定义要处理的资产
    test_symbols = [
        'AAPL.US', 'MSFT.US', 'NVDA.US', 'TSLA.US', 'GOOGL.US',
        'BTC-USD', 'ETH-USD',
        'EURUSD',
        'GSPC.INDX'
    ]

    try:
        # 1. 加载所有资产的基础特征
        all_dfs = load_all_symbols(test_symbols)

        if not all_dfs:
            logger.error("没有成功加载任何资产的基础特征")
            sys.exit(1)

        # 2. 加载基准资产 (S&P 500)
        reference_df = all_dfs.get('GSPC.INDX')
        if reference_df is None:
            logger.warning("未找到基准资产 GSPC.INDX，跨资产特征将设为默认值")

        # 3. 为每个资产计算高级特征
        results = {}

        for symbol in all_dfs.keys():
            df = compute_advanced_features_for_symbol(
                symbol,
                all_dfs[symbol].copy(),
                all_dfs,
                reference_df
            )

            if df is not None:
                # 保存高级特征
                save_advanced_features(df, symbol)
                results[symbol] = df

        if not results:
            logger.error("没有成功处理任何资产")
            sys.exit(1)

        # 4. 生成特征质量报告
        quality_report = generate_feature_report(results)

        # 5. 计算统计信息
        stats = compute_statistics(results)

        # 6. 生成汇总报告
        generate_summary_report(results, quality_report, stats)

        logger.info(f"迭代 3 成功完成！结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.error(f"迭代 3 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
