"""EODHD Financial News API 新闻获取器"""
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from requests.exceptions import RequestException

# 添加父目录到路径以便导入 event_bus
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from event_bus.base_producer import BaseEventProducer
from event_bus.config import redis_config

logger = logging.getLogger(__name__)


class NewsFetcher:
    """EODHD News API 新闻获取器

    功能：
    1. 从 EODHD Financial News API 获取新闻
    2. 发布原始新闻到 Redis Stream (mt5:events:news_raw)
    3. 支持按日期范围、ticker 筛选
    4. 自动提取 API 返回的 ticker 信息
    5. 错误处理与重试
    """

    BASE_URL = "https://eodhd.com/api/news"

    def __init__(
        self,
        api_key: Optional[str] = None,
        event_producer: Optional[BaseEventProducer] = None,
    ):
        """初始化新闻获取器

        Args:
            api_key: EODHD API Key，默认从环境变量 EODHD_API_KEY 读取
            event_producer: 事件生产者，默认创建新的
        """
        self.api_key = api_key or os.getenv('EODHD_API_KEY')
        if not self.api_key:
            logger.warning("EODHD_API_KEY 未设置，将使用演示模式")

        # 初始化事件生产者
        if event_producer:
            self.producer = event_producer
        else:
            self.producer = BaseEventProducer(
                stream_key=redis_config.STREAM_NEWS_RAW
            )

        # 请求配置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MT5-CRS-NewsBot/1.0'
        })

        self.fetch_count = 0
        self.publish_count = 0

        logger.info(f"NewsFetcher 已初始化，API Key: {'已设置' if self.api_key else '未设置'}")

    def fetch_latest_news(
        self,
        limit: int = 50,
        offset: int = 0,
        symbols: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取最新新闻

        Args:
            limit: 返回数量限制，默认50，最大1000
            offset: 偏移量，用于分页
            symbols: 逗号分隔的股票代码，如 "AAPL.US,TSLA.US"
            from_date: 开始日期，格式 YYYY-MM-DD
            to_date: 结束日期，格式 YYYY-MM-DD

        Returns:
            新闻列表
        """
        params = {
            'api_token': self.api_key,
            'limit': limit,
            'offset': offset,
            'fmt': 'json',
        }

        if symbols:
            params['s'] = symbols
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        try:
            logger.info(f"正在获取新闻: limit={limit}, offset={offset}, symbols={symbols}")

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            news_list = response.json()

            if not isinstance(news_list, list):
                logger.error(f"API 返回格式错误: {type(news_list)}")
                return []

            self.fetch_count += len(news_list)
            logger.info(f"✓ 获取到 {len(news_list)} 条新闻")

            return news_list

        except RequestException as e:
            logger.error(f"获取新闻失败: {e}")
            return []
        except ValueError as e:
            logger.error(f"解析 JSON 失败: {e}")
            return []

    def fetch_and_publish(
        self,
        limit: int = 50,
        symbols: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> int:
        """获取新闻并发布到事件总线

        Args:
            limit: 返回数量限制
            symbols: 股票代码筛选
            from_date: 开始日期
            to_date: 结束日期

        Returns:
            成功发布的新闻数量
        """
        news_list = self.fetch_latest_news(
            limit=limit,
            symbols=symbols,
            from_date=from_date,
            to_date=to_date
        )

        if not news_list:
            logger.warning("没有获取到新闻")
            return 0

        success_count = 0

        for news_item in news_list:
            # 标准化新闻数据
            event_data = self._normalize_news(news_item)

            # 发布到事件总线
            message_id = self.producer.produce(
                event_data,
                event_type='news_raw'
            )

            if message_id:
                success_count += 1
            else:
                logger.warning(f"发布新闻失败: {news_item.get('title', 'Unknown')}")

        self.publish_count += success_count

        logger.info(
            f"✓ 发布新闻完成: {success_count}/{len(news_list)} 成功, "
            f"累计: {self.publish_count} 条"
        )

        return success_count

    def _normalize_news(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """标准化新闻数据格式

        EODHD API 返回的新闻格式：
        {
            "date": "2023-10-01T12:34:56Z",
            "title": "...",
            "content": "...",
            "link": "https://...",
            "symbols": "AAPL.US,TSLA.US",  # 可能为空
            "tags": "Technology,Electric Vehicles",
            "sentiment": {
                "polarity": 0.5,
                "neg": 0.1,
                "neu": 0.4,
                "pos": 0.5
            }
        }

        Args:
            news_item: EODHD API 返回的新闻项

        Returns:
            标准化后的新闻数据
        """
        # 提取 tickers（API 自带）
        symbols_str = news_item.get('symbols', '')
        tickers = []
        if symbols_str:
            # 格式: "AAPL.US,TSLA.US" -> ["AAPL", "TSLA"]
            tickers = [
                symbol.split('.')[0]
                for symbol in symbols_str.split(',')
                if symbol.strip()
            ]

        # 标准化后的数据
        normalized = {
            "news_id": news_item.get('link', '').split('/')[-1] or str(hash(news_item.get('title', ''))),
            "title": news_item.get('title', ''),
            "content": news_item.get('content', ''),
            "link": news_item.get('link', ''),
            "published_at": news_item.get('date', ''),
            "source": "EODHD",

            # Ticker 信息（API 自带）
            "symbols_raw": symbols_str,
            "tickers": tickers,

            # 标签
            "tags": news_item.get('tags', '').split(',') if news_item.get('tags') else [],

            # API 自带的情感（如果有）
            "sentiment_api": news_item.get('sentiment'),

            # 元数据
            "fetched_at": datetime.utcnow().isoformat() + 'Z',
        }

        return normalized

    def fetch_periodic(
        self,
        interval_seconds: int = 300,
        limit: int = 50,
        symbols: Optional[str] = None,
    ):
        """定期获取新闻（阻塞运行）

        Args:
            interval_seconds: 获取间隔（秒），默认5分钟
            limit: 每次获取的数量
            symbols: 股票代码筛选
        """
        logger.info(
            f"开始定期获取新闻: 间隔={interval_seconds}秒, "
            f"limit={limit}, symbols={symbols}"
        )

        try:
            while True:
                try:
                    self.fetch_and_publish(limit=limit, symbols=symbols)
                except Exception as e:
                    logger.error(f"获取新闻出错: {e}", exc_info=True)

                logger.info(f"等待 {interval_seconds} 秒后继续...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("收到停止信号，结束定期获取")

    def close(self):
        """关闭资源"""
        self.session.close()
        if self.producer:
            self.producer.close()
        logger.info(
            f"NewsFetcher 已关闭, "
            f"累计获取: {self.fetch_count} 条, "
            f"累计发布: {self.publish_count} 条"
        )


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    fetcher = NewsFetcher()

    # 获取最近7天的新闻
    from_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    to_date = datetime.utcnow().strftime('%Y-%m-%d')

    count = fetcher.fetch_and_publish(
        limit=10,
        from_date=from_date,
        to_date=to_date
    )

    print(f"\n成功发布 {count} 条新闻到事件总线")

    fetcher.close()
