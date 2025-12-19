"""FinBERT 分析器测试脚本"""
import sys
import os
import logging

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sentiment_service.finbert_analyzer import FinBERTAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_basic_analysis():
    """测试基本情感分析功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本情感分析")
    print("=" * 60 + "\n")

    # 初始化分析器
    analyzer = FinBERTAnalyzer(model_name='finbert')

    # 测试用例
    test_cases = [
        {
            'text': "Apple stock surges 15% as iPhone 15 sales exceed all expectations",
            'expected': 'positive'
        },
        {
            'text': "Tesla faces major production delays and quality control issues",
            'expected': 'negative'
        },
        {
            'text': "Microsoft announces quarterly earnings, meeting analyst estimates",
            'expected': 'neutral'
        },
        {
            'text': "Amazon reports record-breaking profits, beating forecasts significantly",
            'expected': 'positive'
        },
        {
            'text': "Google faces regulatory challenges as antitrust investigation deepens",
            'expected': 'negative'
        },
    ]

    success_count = 0

    for i, case in enumerate(test_cases, 1):
        text = case['text']
        expected = case['expected']

        result = analyzer.analyze(text, return_all_scores=True)

        sentiment = result['sentiment']
        score = result['score']
        confidence = result['confidence']

        match = "✓" if sentiment == expected else "✗"
        if sentiment == expected:
            success_count += 1

        print(f"{i}. {match} 文本: {text}")
        print(f"   预期: {expected}, 实际: {sentiment}")
        print(f"   分数: {score:.3f}, 置信度: {confidence:.3f}")
        print(f"   详细: {result.get('all_scores', {})}")
        print()

    print(f"准确率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)\n")


def test_ticker_context():
    """测试目标级情感分析（ticker上下文）"""
    print("\n" + "=" * 60)
    print("测试 2: Ticker 目标级情感分析")
    print("=" * 60 + "\n")

    analyzer = FinBERTAnalyzer(model_name='finbert')

    # 多 ticker 新闻
    news_text = """
    Apple's iPhone 15 sales surge past expectations, driving stock to new highs.
    Meanwhile, Samsung faces challenges in the smartphone market with declining sales.
    Tesla announced new battery technology, but production delays continue to worry investors.
    """

    tickers = ['AAPL', 'SAMSUNG', 'TSLA']

    print("新闻文本:")
    print(news_text.strip())
    print("\n分析结果:\n")

    for ticker in tickers:
        result = analyzer.analyze_with_ticker_context(
            news_text,
            ticker,
            context_window=150
        )

        sentiment = result['sentiment']
        score = result['score']
        confidence = result['confidence']
        context_used = result.get('context_used', False)

        print(f"Ticker: {ticker}")
        print(f"  情感: {sentiment}")
        print(f"  分数: {score:.3f}")
        print(f"  置信度: {confidence:.3f}")
        print(f"  使用上下文: {'是' if context_used else '否'}")
        print()


def test_batch_analysis():
    """测试批量分析"""
    print("\n" + "=" * 60)
    print("测试 3: 批量分析")
    print("=" * 60 + "\n")

    analyzer = FinBERTAnalyzer(model_name='finbert')

    texts = [
        "Strong earnings report boosts investor confidence",
        "Company faces bankruptcy amid mounting debts",
        "Stock price remains stable despite market volatility",
        "Merger deal creates industry giant with massive growth potential",
        "Layoffs announced as company struggles to cut costs",
    ]

    print("批量分析 5 条新闻...\n")

    results = analyzer.analyze_batch(texts, batch_size=3)

    for i, (text, result) in enumerate(zip(texts, results), 1):
        print(f"{i}. {text}")
        print(f"   → {result['sentiment']} (score={result['score']:.3f})")

    print(f"\n共分析 {len(results)} 条")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试 4: 边界情况")
    print("=" * 60 + "\n")

    analyzer = FinBERTAnalyzer(model_name='finbert')

    edge_cases = [
        ("", "空字符串"),
        ("   ", "仅空格"),
        ("a" * 1000, "超长文本"),
        ("$AAPL", "仅 ticker"),
        ("123 456", "纯数字"),
    ]

    for text, description in edge_cases:
        result = analyzer.analyze(text)
        print(f"{description}: sentiment={result['sentiment']}, score={result['score']:.3f}")

    print()


if __name__ == "__main__":
    try:
        print("\n" + "=" * 60)
        print("FinBERT 情感分析器测试套件")
        print("=" * 60)

        test_basic_analysis()
        test_ticker_context()
        test_batch_analysis()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
