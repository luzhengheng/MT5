"""事件生产者测试工具"""
import logging
import time
from datetime import datetime

from base_producer import BaseEventProducer
from config import redis_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_produce_single_event():
    """测试发布单个事件"""
    logger.info("=== 测试发布单个事件 ===")

    producer = BaseEventProducer(stream_key=redis_config.STREAM_NEWS_RAW)

    # 模拟一条新闻事件
    event_data = {
        "title": "Tesla股价大涨10%",
        "content": "特斯拉今日股价大涨10%，市值突破8000亿美元...",
        "source": "Bloomberg",
        "published_at": datetime.utcnow().isoformat() + "Z",
        "symbols": ["TSLA"],
        "url": "https://example.com/news/123",
    }

    message_id = producer.produce(event_data, event_type="news_raw")

    if message_id:
        logger.info(f"✓ 事件发布成功，message_id = {message_id}")

        # 查看 Stream 信息
        info = producer.get_stream_info()
        if info:
            logger.info(f"Stream 长度: {info['length']}")
            logger.info(f"第一条消息ID: {info['first-entry'][0] if info.get('first-entry') else 'N/A'}")
            logger.info(f"最后一条消息ID: {info['last-entry'][0] if info.get('last-entry') else 'N/A'}")
    else:
        logger.error("✗ 事件发布失败")

    producer.close()


def test_produce_batch_events():
    """测试批量发布事件"""
    logger.info("\n=== 测试批量发布事件 ===")

    producer = BaseEventProducer(stream_key=redis_config.STREAM_NEWS_RAW)

    # 模拟多条新闻
    events = [
        {
            "title": f"新闻标题 {i}",
            "content": f"新闻内容 {i}",
            "source": "Reuters",
            "published_at": datetime.utcnow().isoformat() + "Z",
            "symbols": ["AAPL", "GOOGL"],
        }
        for i in range(5)
    ]

    message_ids = producer.produce_batch(events, event_type="news_raw")

    success_count = sum(1 for mid in message_ids if mid is not None)
    logger.info(f"✓ 批量发布完成: {success_count}/{len(events)} 成功")

    for i, mid in enumerate(message_ids):
        if mid:
            logger.info(f"  事件 {i}: {mid}")

    producer.close()


def test_maxlen_trim():
    """测试 MAXLEN 自动裁剪"""
    logger.info("\n=== 测试 MAXLEN 自动裁剪 ===")

    producer = BaseEventProducer(stream_key="mt5:events:test_trim")

    # 发布 15 条消息，设置 maxlen=10
    for i in range(15):
        event_data = {"index": i, "timestamp": time.time()}
        producer.produce(event_data, event_type="test", maxlen=10, approximate=True)

    info = producer.get_stream_info()
    if info:
        logger.info(f"✓ 发布15条消息后，Stream长度: {info['length']} (应该约为10)")

    producer.close()


if __name__ == "__main__":
    try:
        test_produce_single_event()
        test_produce_batch_events()
        test_maxlen_trim()

        logger.info("\n=== 所有测试完成 ===")

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
