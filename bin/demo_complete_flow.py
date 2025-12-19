"""完整流程演示脚本

模拟整个数据流：新闻 → 情感分析 → 信号生成
不需要实际加载 FinBERT 模型，使用模拟的情感分析
"""
import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from event_bus.base_producer import BaseEventProducer
from event_bus.config import redis_config
import redis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockSentimentAnalyzer:
    """模拟情感分析器"""

    def analyze_with_ticker_context(self, text: str, ticker: str) -> Dict[str, Any]:
        """模拟情感分析

        简单规则：
        - 包含 "surge", "record", "high", "gain" → positive
        - 包含 "fall", "delay", "drop", "down" → negative
        - 其他 → neutral
        """
        text_lower = text.lower()

        positive_words = ['surge', 'record', 'high', 'gain', 'up', 'rise', 'beat']
        negative_words = ['fall', 'delay', 'drop', 'down', 'miss', 'decline']

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
            score = 0.80 + (positive_count * 0.05)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = -(0.80 + (negative_count * 0.05))
        else:
            sentiment = 'neutral'
            score = 0.0

        score = max(-1.0, min(1.0, score))  # 限制在 -1 到 1
        confidence = 0.85 if abs(score) > 0.7 else 0.65

        return {
            'ticker': ticker,
            'sentiment': sentiment,
            'score': score,
            'confidence': confidence,
            'context_used': True
        }


def main():
    logger.info("=" * 60)
    logger.info("MT5-CRS 完整流程演示")
    logger.info("=" * 60)
    logger.info("")

    # 连接 Redis
    try:
        r = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            decode_responses=True
        )
        r.ping()
        logger.info("✓ Redis 连接成功")
    except Exception as e:
        logger.error(f"✗ Redis 连接失败: {e}")
        return

    logger.info("")
    logger.info("=" * 60)
    logger.info("阶段1：发布原始新闻")
    logger.info("=" * 60)

    # 测试新闻
    test_news = [
        {
            "news_id": "news_001",
            "title": "Apple reports record-breaking Q4 earnings, stock surges 10%",
            "content": "Apple Inc. announced record quarterly earnings today, beating analyst expectations by 15%. The stock price surged 10% in after-hours trading.",
            "link": "https://example.com/news/1",
            "published_at": datetime.utcnow().isoformat() + 'Z',
            "source": "EODHD",
            "tickers": ["AAPL"]
        },
        {
            "news_id": "news_002",
            "title": "Tesla faces production delays, shares fall 8%",
            "content": "Tesla announced significant production delays at its new factory, causing shares to drop 8% in morning trading.",
            "link": "https://example.com/news/2",
            "published_at": datetime.utcnow().isoformat() + 'Z',
            "source": "EODHD",
            "tickers": ["TSLA"]
        },
        {
            "news_id": "news_003",
            "title": "Microsoft beats revenue expectations, stock rises 5%",
            "content": "Microsoft Corporation reported strong quarterly results, with cloud services revenue beating expectations. Stock price rose 5%.",
            "link": "https://example.com/news/3",
            "published_at": datetime.utcnow().isoformat() + 'Z',
            "source": "EODHD",
            "tickers": ["MSFT"]
        }
    ]

    # 发布原始新闻
    producer_raw = BaseEventProducer(stream_key=redis_config.STREAM_NEWS_RAW)

    for news in test_news:
        msg_id = producer_raw.produce(news, event_type='news_raw')
        logger.info(f"  ✓ 发布新闻: {news['title'][:60]}...")
        logger.info(f"    → {msg_id}")

    producer_raw.close()
    logger.info(f"\n共发布 {len(test_news)} 条原始新闻")

    time.sleep(1)

    logger.info("")
    logger.info("=" * 60)
    logger.info("阶段2：模拟情感分析与过滤")
    logger.info("=" * 60)

    # 模拟情感分析
    analyzer = MockSentimentAnalyzer()
    producer_filtered = BaseEventProducer(stream_key=redis_config.STREAM_NEWS_FILTERED)

    filtered_count = 0

    for news in test_news:
        logger.info(f"\n处理新闻: {news['title'][:60]}...")

        ticker_sentiments = []

        for ticker in news.get('tickers', []):
            result = analyzer.analyze_with_ticker_context(
                news['title'] + ' ' + news['content'],
                ticker
            )

            logger.info(f"  {ticker}: {result['sentiment']} "
                       f"(score={result['score']:.2f}, conf={result['confidence']:.2f})")

            # 过滤条件：|score| >= 0.75 and confidence >= 0.60
            if abs(result['score']) >= 0.75 and result['confidence'] >= 0.60:
                ticker_sentiments.append(result)
                logger.info(f"    ✓ 通过过滤")
            else:
                logger.info(f"    ✗ 未通过过滤（阈值不足）")

        # 如果有 ticker 通过过滤，发布过滤后的新闻
        if ticker_sentiments:
            filtered_news = {
                **news,
                'ticker_sentiment': ticker_sentiments,
                'ticker_count': len(ticker_sentiments)
            }
            msg_id = producer_filtered.produce(filtered_news, event_type='news_filtered')
            logger.info(f"  → 发布过滤后新闻: {msg_id}")
            filtered_count += 1

    producer_filtered.close()
    logger.info(f"\n共有 {filtered_count}/{len(test_news)} 条新闻通过过滤")

    time.sleep(1)

    logger.info("")
    logger.info("=" * 60)
    logger.info("阶段3：模拟信号生成")
    logger.info("=" * 60)

    # 读取过滤后的新闻
    stream_key = redis_config.STREAM_NEWS_FILTERED
    messages = r.xrange(stream_key, count=100)

    if not messages:
        logger.warning("⚠️ 没有找到过滤后的新闻")
        return

    logger.info(f"找到 {len(messages)} 条过滤后的新闻")

    producer_signals = BaseEventProducer(stream_key=redis_config.STREAM_SIGNALS)
    signal_count = 0

    for msg_id, data in messages:
        import json
        event_data = json.loads(data.get('event_data', '{}'))

        logger.info(f"\n处理新闻: {event_data.get('title', 'N/A')[:60]}...")

        for ts in event_data.get('ticker_sentiment', []):
            ticker = ts['ticker']
            sentiment = ts['sentiment']
            score = ts['score']
            confidence = ts['confidence']

            # 生成信号
            direction = 'BUY' if sentiment == 'positive' else 'SELL'

            # 简化的手数计算：基于情感强度和置信度
            lot_size = round(abs(score) * confidence * 0.2, 2)
            lot_size = max(0.01, min(1.0, lot_size))

            # 简化的止损止盈
            if ticker in ['AAPL', 'MSFT', 'TSLA']:  # 股票
                sl = 100
                tp = 300
            else:
                sl = 50
                tp = 150

            signal = {
                'signal_id': f"sig_{ticker}_{int(time.time())}",
                'ticker': ticker,
                'direction': direction,
                'lot_size': lot_size,
                'stop_loss': sl,
                'take_profit': tp,
                'entry_price': 0.0,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'expiry_at': datetime.utcnow().isoformat() + 'Z',  # 简化
                'source': 'news_sentiment',
                'news_id': event_data.get('news_id'),
                'sentiment': sentiment,
                'sentiment_score': score,
                'confidence': confidence,
                'status': 'pending'
            }

            msg_id_sig = producer_signals.produce(signal, event_type='trading_signal')

            logger.info(f"  ✓ 生成信号: {ticker} {direction} {lot_size} lots")
            logger.info(f"    SL={sl}, TP={tp}")
            logger.info(f"    → {msg_id_sig}")

            signal_count += 1

    producer_signals.close()
    logger.info(f"\n共生成 {signal_count} 个交易信号")

    time.sleep(1)

    logger.info("")
    logger.info("=" * 60)
    logger.info("阶段4：验证数据流")
    logger.info("=" * 60)

    # 检查各个 stream
    streams = [
        (redis_config.STREAM_NEWS_RAW, "原始新闻"),
        (redis_config.STREAM_NEWS_FILTERED, "过滤后新闻"),
        (redis_config.STREAM_SIGNALS, "交易信号")
    ]

    for stream_key, name in streams:
        try:
            length = r.xlen(stream_key)
            logger.info(f"\n{name} ({stream_key}):")
            logger.info(f"  消息数量: {length}")

            if length > 0:
                messages = r.xrevrange(stream_key, count=3)
                logger.info(f"  最新消息:")
                for msg_id, data in messages:
                    event_data = json.loads(data.get('event_data', '{}'))
                    if 'title' in event_data:
                        logger.info(f"    {msg_id}: {event_data['title'][:50]}...")
                    elif 'ticker' in event_data:
                        logger.info(f"    {msg_id}: {event_data['ticker']} {event_data.get('direction', 'N/A')}")
        except Exception as e:
            logger.error(f"  ✗ 检查失败: {e}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("演示完成")
    logger.info("=" * 60)
    logger.info("")
    logger.info("✓ 完整的数据流已验证:")
    logger.info("  1. 原始新闻发布 → mt5:events:news_raw")
    logger.info("  2. 情感分析与过滤 → mt5:events:news_filtered")
    logger.info("  3. 交易信号生成 → mt5:events:signals")
    logger.info("")
    logger.info("注：本演示使用模拟情感分析器")
    logger.info("生产环境中将使用真实的 FinBERT 模型")


if __name__ == "__main__":
    main()
