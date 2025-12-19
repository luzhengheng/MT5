#!/usr/bin/env python3
"""
迭代 1: MVP 数据管道
功能：
1. 采集历史价格数据（Yahoo Finance）
2. 采集历史新闻数据（模拟版本，因为需要 API Key）
3. 运行 FinBERT 情感分析
4. 生成数据质量报告
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/opt/mt5-crs')

import yaml
import pandas as pd

from src.market_data.price_fetcher import PriceDataFetcher
from src.sentiment_service.sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def step1_fetch_price_data(config: dict):
    """步骤 1: 获取价格数据"""
    logger.info("=" * 60)
    logger.info("步骤 1: 获取历史价格数据")
    logger.info("=" * 60)

    # 创建采集器
    fetcher = PriceDataFetcher()

    # 获取资产列表（简化版：只获取部分资产进行测试）
    test_symbols = [
        'AAPL.US', 'MSFT.US', 'NVDA.US', 'TSLA.US', 'GOOGL.US',  # 5 只股票
        'BTC-USD', 'ETH-USD',  # 2 个加密货币
        'EURUSD',  # 1 个外汇
        'GSPC.INDX',  # 1 个指数
    ]

    logger.info(f"测试符号（共 {len(test_symbols)} 个）: {test_symbols}")

    # 获取数据
    start_date = config['data_collection']['start_date']
    data = fetcher.fetch_multiple_symbols(test_symbols, start_date)

    # 保存数据
    fetcher.save_to_parquet(data)

    # 生成质量报告
    report = fetcher.generate_data_quality_report(data)

    logger.info(f"\n步骤 1 完成: 成功获取 {len(data)}/{len(test_symbols)} 个资产的数据")
    logger.info(f"总记录数: {sum(len(df) for df in data.values())}")

    return data, report


def step2_create_sample_news(config: dict):
    """步骤 2: 创建示例新闻数据（模拟）

    注意：实际环境需要 EODHD API Key
    """
    logger.info("=" * 60)
    logger.info("步骤 2: 创建示例新闻数据（模拟）")
    logger.info("=" * 60)

    # 创建示例新闻
    sample_news = [
        {
            'news_id': 'news_001',
            'timestamp': pd.Timestamp('2024-01-15 10:30:00'),
            'ticker_list': ['AAPL.US'],
            'title': 'Apple announces new iPhone with revolutionary AI features',
            'content': 'Apple Inc. unveiled its latest iPhone model featuring advanced AI capabilities...',
            'source': 'Reuters',
        },
        {
            'news_id': 'news_002',
            'timestamp': pd.Timestamp('2024-01-15 14:20:00'),
            'ticker_list': ['TSLA.US'],
            'title': 'Tesla reports disappointing Q4 delivery numbers',
            'content': 'Tesla delivered fewer vehicles than expected in Q4, missing analyst estimates...',
            'source': 'Bloomberg',
        },
        {
            'news_id': 'news_003',
            'timestamp': pd.Timestamp('2024-01-16 09:00:00'),
            'ticker_list': ['MSFT.US', 'GOOGL.US'],
            'title': 'Big Tech companies invest heavily in cloud infrastructure',
            'content': 'Microsoft and Google announced major investments in expanding their cloud services...',
            'source': 'CNBC',
        },
        {
            'news_id': 'news_004',
            'timestamp': pd.Timestamp('2024-01-16 16:45:00'),
            'ticker_list': ['BTC-USD'],
            'title': 'Bitcoin surges to new yearly high on ETF approval hopes',
            'content': 'Bitcoin price jumped 10% today as investors anticipate SEC approval of spot ETFs...',
            'source': 'CoinDesk',
        },
        {
            'news_id': 'news_005',
            'timestamp': pd.Timestamp('2024-01-17 11:30:00'),
            'ticker_list': ['NVDA.US'],
            'title': 'NVIDIA stock hits record high on AI chip demand',
            'content': 'NVIDIA shares reached an all-time high driven by strong demand for AI processors...',
            'source': 'MarketWatch',
        },
    ]

    news_df = pd.DataFrame(sample_news)

    # 保存原始新闻
    output_path = Path('/opt/mt5-crs/data_lake/news_raw')
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / 'sample_news.parquet'
    news_df.to_parquet(output_file, engine='pyarrow', compression='gzip', index=False)

    logger.info(f"创建 {len(news_df)} 条示例新闻")
    logger.info(f"保存到: {output_file}")

    return news_df


def step3_sentiment_analysis(news_df: pd.DataFrame):
    """步骤 3: 运行情感分析"""
    logger.info("=" * 60)
    logger.info("步骤 3: 运行 FinBERT 情感分析")
    logger.info("=" * 60)

    # 创建情感分析器
    model_path = "/opt/mt5-crs/var/cache/models/finbert"
    analyzer = SentimentAnalyzer(model_path=model_path, device='cpu', batch_size=8)

    # 分析情感
    news_df = analyzer.analyze_news_dataframe(news_df, text_column='title')

    # 添加 ticker 级别情感
    news_df = analyzer.analyze_ticker_level_sentiment(news_df)

    # 保存处理后的新闻
    output_path = Path('/opt/mt5-crs/data_lake/news_processed')
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / 'sample_news_processed.parquet'
    news_df.to_parquet(output_file, engine='pyarrow', compression='gzip', index=False)

    logger.info(f"情感分析完成，保存到: {output_file}")

    # 打印结果
    logger.info("\n情感分析结果:")
    for _, row in news_df.iterrows():
        logger.info(f"  {row['ticker_list']}: {row['sentiment_label']} ({row['sentiment_score']:.3f})")
        logger.info(f"    {row['title'][:60]}...")

    return news_df


def step4_generate_summary_report(price_data: dict, news_df: pd.DataFrame, price_report: pd.DataFrame):
    """步骤 4: 生成汇总报告"""
    logger.info("=" * 60)
    logger.info("步骤 4: 生成迭代 1 汇总报告")
    logger.info("=" * 60)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("迭代 1: MVP 数据管道 - 执行报告")
    report_lines.append("=" * 80)
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 价格数据统计
    report_lines.append("## 1. 价格数据采集")
    report_lines.append(f"  - 目标资产数: {len(price_report)}")
    report_lines.append(f"  - 成功获取: {len(price_data)} 个")
    report_lines.append(f"  - 总记录数: {sum(len(df) for df in price_data.values())}")
    report_lines.append(f"  - 日期范围: {price_report['start_date'].min()} 到 {price_report['end_date'].max()}")
    report_lines.append(f"  - 数据质量: {(price_report['quality_original'].sum() / price_report['total_records'].sum() * 100):.1f}% 原始数据")
    report_lines.append("")

    # 新闻数据统计
    report_lines.append("## 2. 新闻数据采集")
    report_lines.append(f"  - 总新闻数: {len(news_df)}")
    report_lines.append(f"  - 含 ticker 新闻: {len(news_df[news_df['ticker_list'].str.len() > 0])}")
    report_lines.append(f"  - 日期范围: {news_df['timestamp'].min()} 到 {news_df['timestamp'].max()}")
    report_lines.append(f"  - 唯一来源: {news_df['source'].nunique()}")
    report_lines.append("")

    # 情感分析统计
    report_lines.append("## 3. 情感分析")
    sentiment_counts = news_df['sentiment_label'].value_counts()
    report_lines.append(f"  - 分析成功率: {(news_df['sentiment_confidence'] > 0).mean():.1%}")
    report_lines.append(f"  - 情感分布:")
    for label, count in sentiment_counts.items():
        report_lines.append(f"      {label}: {count} ({count/len(news_df)*100:.1f}%)")
    report_lines.append(f"  - 平均置信度: {news_df['sentiment_confidence'].mean():.3f}")
    report_lines.append("")

    # 数据输出
    report_lines.append("## 4. 数据输出")
    report_lines.append(f"  - 价格数据: /opt/mt5-crs/data_lake/price_daily/")
    report_lines.append(f"  - 新闻数据: /opt/mt5-crs/data_lake/news_processed/")
    report_lines.append(f"  - 质量报告: /opt/mt5-crs/data_lake/price_daily/data_quality_report.csv")
    report_lines.append("")

    # 下一步
    report_lines.append("## 5. 下一步 (迭代 2)")
    report_lines.append("  - 实现基础特征工程（30 维技术指标）")
    report_lines.append("  - 整合价格数据与新闻情感")
    report_lines.append("  - 生成特征向量")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("迭代 1 完成！✅")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)

    # 保存报告
    report_file = Path('/opt/mt5-crs/var/reports/iteration1_report.txt')
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_text)

    # 打印报告
    print("\n" + report_text)

    logger.info(f"汇总报告已保存到: {report_file}")


def main():
    """主函数"""
    logger.info("开始执行迭代 1: MVP 数据管道")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 加载配置
    with open('/opt/mt5-crs/config/assets.yaml', 'r') as f:
        config = yaml.safe_load(f)

    try:
        # 步骤 1: 获取价格数据
        price_data, price_report = step1_fetch_price_data(config)

        # 步骤 2: 创建示例新闻
        news_df = step2_create_sample_news(config)

        # 步骤 3: 情感分析
        news_df = step3_sentiment_analysis(news_df)

        # 步骤 4: 生成报告
        step4_generate_summary_report(price_data, news_df, price_report)

        logger.info(f"迭代 1 成功完成！结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.error(f"迭代 1 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
