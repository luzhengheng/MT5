#!/usr/bin/env python3
"""测试真实的 FinBERT 情感分析功能"""
import os
import sys
import logging

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from sentiment_service.finbert_analyzer import FinBERTAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_real_sentiment():
    """测试真实的情感分析功能"""
    logger.info("=" * 60)
    logger.info("FinBERT 真实情感分析测试")
    logger.info("=" * 60)

    try:
        # 初始化分析器
        logger.info("初始化 FinBERT 分析器...")
        analyzer = FinBERTAnalyzer(model_name='finbert', device='cpu')
        logger.info("")

        # 测试样本
        test_samples = [
            {
                'text': "Apple Inc. announced record-breaking quarterly earnings, with iPhone sales exceeding all expectations.",
                'ticker': 'AAPL',
                'expected': 'positive'
            },
            {
                'text': "Tesla's stock plummeted after disappointing delivery numbers and quality concerns.",
                'ticker': 'TSLA',
                'expected': 'negative'
            },
            {
                'text': "Microsoft reported steady growth in cloud services, meeting analyst forecasts.",
                'ticker': 'MSFT',
                'expected': 'neutral/positive'
            },
            {
                'text': "The Federal Reserve raised interest rates by 25 basis points, signaling continued economic strength.",
                'ticker': 'SPX',
                'expected': 'neutral/negative'
            },
        ]

        logger.info(f"运行 {len(test_samples)} 个测试样本...")
        logger.info("")

        for i, sample in enumerate(test_samples, 1):
            logger.info(f"样本 {i}/{len(test_samples)}:")
            logger.info(f"  文本: {sample['text']}")
            logger.info(f"  Ticker: {sample['ticker']}")
            logger.info(f"  预期情感: {sample['expected']}")

            # 分析情感
            result = analyzer.analyze(sample['text'], return_all_scores=True)

            logger.info(f"  实际情感: {result['sentiment']} (score: {result['score']:.4f}, confidence: {result['confidence']:.4f})")
            if 'all_scores' in result:
                logger.info(f"  所有分数:")
                for label, score in result['all_scores'].items():
                    logger.info(f"    - {label}: {score:.4f}")
            logger.info("")

        # 测试ticker级别的情感分析 (工单#007的创新功能)
        logger.info("=" * 60)
        logger.info("测试目标级情感分析 (工单#007 创新)")
        logger.info("=" * 60)
        logger.info("")

        mixed_news = {
            'text': "Apple stock surged 5% on strong earnings while Tesla dropped 8% on delivery concerns. Microsoft remained flat.",
            'tickers': ['AAPL', 'TSLA', 'MSFT']
        }

        logger.info(f"混合情感新闻: {mixed_news['text']}")
        logger.info(f"涉及 Tickers: {mixed_news['tickers']}")
        logger.info("")

        for ticker in mixed_news['tickers']:
            result = analyzer.analyze_with_ticker_context(mixed_news['text'], ticker)
            logger.info(f"{ticker}: {result['sentiment']} (score: {result['score']:.4f}, confidence: {result['confidence']:.4f})")

        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ 所有测试通过!")
        logger.info("=" * 60)
        logger.info("")
        logger.info(f"分析统计:")
        logger.info(f"  - 总分析次数: {analyzer.analysis_count}")
        logger.info(f"  - 设备: {analyzer.device}")
        logger.info(f"  - 模型: {analyzer.model_name}")

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_real_sentiment()
    sys.exit(0 if success else 1)
