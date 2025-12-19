"""新闻过滤消费者

从 mt5:events:news_raw 消费新闻，
进行 FinBERT 情感分析和过滤，
发布到 mt5:events:news_filtered
"""
import logging
import sys
import os
from typing import Dict, Any, List
import json

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from event_bus.base_consumer import BaseEventConsumer
from event_bus.base_producer import BaseEventProducer
from event_bus.config import redis_config
from sentiment_service.finbert_analyzer import FinBERTAnalyzer
from news_service.ticker_extractor import TickerExtractor

logger = logging.getLogger(__name__)


class NewsFilterConsumer(BaseEventConsumer):
    """新闻过滤消费者

    功能：
    1. 从 mt5:events:news_raw 消费原始新闻
    2. 使用 FinBERT 对每个 ticker 进行目标级情感分析
    3. 根据情感强度阈值过滤
    4. 发布过滤后的新闻到 mt5:events:news_filtered
    """

    def __init__(
        self,
        sentiment_threshold: float = 0.75,
        min_confidence: float = 0.60,
        finbert_model: str = 'finbert',
    ):
        """初始化消费者

        Args:
            sentiment_threshold: 情感强度阈值，|score| >= threshold 才保留
            min_confidence: 最小置信度要求
            finbert_model: FinBERT 模型名称
        """
        # 初始化基类
        super().__init__(
            stream_key=redis_config.STREAM_NEWS_RAW,
            consumer_group=redis_config.CONSUMER_GROUP_NEWS_FILTER,
            consumer_name='news_filter_consumer_1',
            auto_ack=True,
            block_ms=5000,
            batch_size=10,
        )

        # 配置
        self.sentiment_threshold = sentiment_threshold
        self.min_confidence = min_confidence

        # 初始化 FinBERT 分析器
        logger.info(f"初始化 FinBERT 分析器: model={finbert_model}")
        self.analyzer = FinBERTAnalyzer(model_name=finbert_model)

        # 初始化 Ticker 提取器（fallback）
        self.ticker_extractor = TickerExtractor()

        # 初始化输出生产者
        self.output_producer = BaseEventProducer(
            stream_key=redis_config.STREAM_NEWS_FILTERED
        )

        # 统计
        self.processed_count = 0
        self.filtered_count = 0
        self.published_count = 0

        logger.info(
            f"NewsFilterConsumer 已初始化: "
            f"sentiment_threshold={sentiment_threshold}, "
            f"min_confidence={min_confidence}"
        )

    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """处理单条新闻事件

        Args:
            event_id: 事件ID
            event_data: 新闻数据

        Returns:
            处理是否成功
        """
        try:
            self.processed_count += 1

            logger.info(f"\n处理新闻: {event_id}")
            logger.info(f"  标题: {event_data.get('title', 'N/A')}")

            # 1. 提取 tickers
            tickers = self._extract_tickers(event_data)

            if not tickers:
                logger.info(f"  跳过：没有提取到 ticker")
                return True  # 成功但不发布

            logger.info(f"  提取到 {len(tickers)} 个 tickers: {tickers}")

            # 2. 对每个 ticker 进行情感分析
            ticker_sentiments = self._analyze_ticker_sentiments(
                event_data,
                tickers
            )

            if not ticker_sentiments:
                logger.info(f"  跳过：没有符合阈值的 ticker")
                self.filtered_count += 1
                return True

            logger.info(f"  过滤后保留 {len(ticker_sentiments)} 个 tickers")

            # 3. 构造过滤后的新闻数据
            filtered_news = self._build_filtered_news(
                event_data,
                ticker_sentiments
            )

            # 4. 发布到输出 stream
            message_id = self.output_producer.produce(
                filtered_news,
                event_type='news_filtered'
            )

            if message_id:
                self.published_count += 1
                logger.info(f"  ✓ 已发布到 filtered stream: {message_id}")
            else:
                logger.warning(f"  ✗ 发布失败")

            # 5. 每处理10条打印统计
            if self.processed_count % 10 == 0:
                self._log_stats()

            return True

        except Exception as e:
            logger.error(f"处理新闻失败: {e}", exc_info=True)
            return False

    def _extract_tickers(self, event_data: Dict[str, Any]) -> List[str]:
        """提取 tickers

        优先使用 API 自带的，如果没有则用 fallback 提取

        Args:
            event_data: 新闻数据

        Returns:
            ticker 列表
        """
        # 优先使用 API 自带的 tickers
        tickers = event_data.get('tickers', [])

        if tickers:
            return tickers

        # Fallback: 从标题和内容提取
        tickers = self.ticker_extractor.extract_from_news(event_data)

        return tickers

    def _analyze_ticker_sentiments(
        self,
        event_data: Dict[str, Any],
        tickers: List[str]
    ) -> List[Dict[str, Any]]:
        """对每个 ticker 进行情感分析

        Args:
            event_data: 新闻数据
            tickers: ticker 列表

        Returns:
            符合阈值的 ticker 情感列表
        """
        title = event_data.get('title', '')
        content = event_data.get('content', '')
        full_text = f"{title}. {content}"

        ticker_sentiments = []

        for ticker in tickers:
            # 分析该 ticker 的情感
            result = self.analyzer.analyze_with_ticker_context(
                full_text,
                ticker,
                context_window=200
            )

            sentiment = result['sentiment']
            score = result['score']
            confidence = result['confidence']

            logger.debug(
                f"    Ticker {ticker}: {sentiment} "
                f"(score={score:.3f}, conf={confidence:.3f})"
            )

            # 应用过滤条件
            if (abs(score) >= self.sentiment_threshold and
                confidence >= self.min_confidence):

                ticker_sentiments.append({
                    'ticker': ticker,
                    'sentiment': sentiment,
                    'score': score,
                    'confidence': confidence,
                    'context_used': result.get('context_used', False)
                })

                logger.info(
                    f"    ✓ {ticker}: {sentiment} "
                    f"(score={score:.3f}, conf={confidence:.3f})"
                )
            else:
                logger.debug(
                    f"    ✗ {ticker}: 不符合阈值 "
                    f"(|{score:.3f}| < {self.sentiment_threshold} or "
                    f"{confidence:.3f} < {self.min_confidence})"
                )

        return ticker_sentiments

    def _build_filtered_news(
        self,
        event_data: Dict[str, Any],
        ticker_sentiments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构造过滤后的新闻数据

        Args:
            event_data: 原始新闻数据
            ticker_sentiments: ticker 情感列表

        Returns:
            过滤后的新闻数据
        """
        filtered_news = {
            # 保留原始字段
            'news_id': event_data.get('news_id'),
            'title': event_data.get('title'),
            'content': event_data.get('content'),
            'link': event_data.get('link'),
            'published_at': event_data.get('published_at'),
            'source': event_data.get('source'),
            'fetched_at': event_data.get('fetched_at'),

            # 新增：ticker 级别的情感分析结果
            'ticker_sentiment': ticker_sentiments,

            # 统计
            'ticker_count': len(ticker_sentiments),
        }

        return filtered_news

    def _log_stats(self):
        """打印统计信息"""
        filter_rate = (self.filtered_count / self.processed_count * 100
                       if self.processed_count > 0 else 0)

        logger.info(
            f"\n=== 统计 ===\n"
            f"  已处理: {self.processed_count}\n"
            f"  已过滤: {self.filtered_count} ({filter_rate:.1f}%)\n"
            f"  已发布: {self.published_count}\n"
            f"  FinBERT 分析次数: {self.analyzer.analysis_count}\n"
        )

    def close(self):
        """关闭资源"""
        self._log_stats()
        self.output_producer.close()
        super().close()


if __name__ == "__main__":
    # 测试运行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=== 启动 NewsFilterConsumer ===")
    logger.info("提示：请先运行 news_fetcher 发布一些新闻到 mt5:events:news_raw")
    logger.info("按 Ctrl+C 停止\n")

    consumer = NewsFilterConsumer(
        sentiment_threshold=0.75,
        min_confidence=0.60
    )

    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("\n收到停止信号")
    finally:
        consumer.close()
