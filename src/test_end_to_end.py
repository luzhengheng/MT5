"""端到端测试脚本

测试完整的新闻到信号生成流程
"""
import sys
import os
import time
import logging
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import redis
from event_bus.config import redis_config
from event_bus.base_producer import BaseEventProducer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_redis_connection():
    """测试 Redis 连接"""
    logger.info("=== 测试1：Redis 连接 ===")

    try:
        client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            decode_responses=True
        )

        client.ping()
        logger.info("✓ Redis 连接成功")
        return True
    except Exception as e:
        logger.error(f"✗ Redis 连接失败: {e}")
        return False


def publish_test_news():
    """发布测试新闻到 news_raw stream"""
    logger.info("\n=== 测试2：发布测试新闻 ===")

    producer = BaseEventProducer(stream_key=redis_config.STREAM_NEWS_RAW)

    # 测试新闻数据
    test_news = [
        {
            "news_id": "test-001",
            "title": "Apple reports record-breaking Q4 earnings, stock surges 10%",
            "content": "Apple Inc. announced impressive fourth-quarter results today, with revenue beating analyst expectations. The iPhone maker's stock jumped 10% in after-hours trading.",
            "link": "https://example.com/news/apple-earnings",
            "published_at": datetime.utcnow().isoformat() + "Z",
            "source": "TEST",
            "tickers": ["AAPL"],
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        },
        {
            "news_id": "test-002",
            "title": "Tesla faces production delays, shares fall 8%",
            "content": "Tesla is experiencing significant production delays at its new factory, causing shares to drop 8% today. Analysts express concerns about delivery targets.",
            "link": "https://example.com/news/tesla-delays",
            "published_at": datetime.utcnow().isoformat() + "Z",
            "source": "TEST",
            "tickers": ["TSLA"],
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        },
        {
            "news_id": "test-003",
            "title": "Mixed earnings from tech giants: Google up, Amazon down",
            "content": "Tech earnings season continues with mixed results. Google parent Alphabet beat estimates and rose 5%, while Amazon missed expectations and fell 3%.",
            "link": "https://example.com/news/tech-earnings",
            "published_at": datetime.utcnow().isoformat() + "Z",
            "source": "TEST",
            "tickers": ["GOOGL", "AMZN"],
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        },
    ]

    published_ids = []
    for news in test_news:
        msg_id = producer.produce(news, event_type='news_raw')
        if msg_id:
            published_ids.append(msg_id)
            logger.info(f"✓ 发布新闻: {news['title'][:60]}... → {msg_id}")
        else:
            logger.error(f"✗ 发布失败: {news['title'][:60]}...")

    producer.close()

    logger.info(f"\n共发布 {len(published_ids)}/{len(test_news)} 条测试新闻")
    return len(published_ids) == len(test_news)


def check_stream_data(stream_key, expected_min=0):
    """检查 stream 中的数据"""
    try:
        client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            decode_responses=True
        )

        # 获取 stream 长度
        info = client.xinfo_stream(stream_key)
        length = info['length']

        logger.info(f"  Stream '{stream_key}': {length} 条消息")

        if length >= expected_min:
            # 读取最新的几条消息
            messages = client.xrevrange(stream_key, count=3)

            logger.info(f"  最新消息预览:")
            for msg_id, msg_data in messages:
                # 解析第一个字段作为预览
                preview = list(msg_data.keys())[0] if msg_data else "空"
                logger.info(f"    {msg_id}: {preview}...")

            return True
        else:
            logger.warning(f"  ⚠️ 消息数量不足: {length} < {expected_min}")
            return False

    except Exception as e:
        logger.error(f"  ✗ 检查失败: {e}")
        return False


def monitor_pipeline():
    """监控完整管道的数据流"""
    logger.info("\n=== 测试3：监控数据流 ===")

    streams = [
        (redis_config.STREAM_NEWS_RAW, "原始新闻"),
        (redis_config.STREAM_NEWS_FILTERED, "过滤后新闻"),
        (redis_config.STREAM_SIGNALS, "交易信号"),
        (redis_config.STREAM_DEADLETTER, "死信队列"),
    ]

    results = {}
    for stream_key, description in streams:
        logger.info(f"\n检查 {description} ({stream_key}):")
        results[stream_key] = check_stream_data(stream_key)

    return all(results.values())


def test_signal_generation():
    """测试信号生成（需要先运行消费者）"""
    logger.info("\n=== 测试4：信号生成验证 ===")
    logger.info("提示：此测试需要 news_filter_consumer 和 signal_generator_consumer 正在运行")
    logger.info("等待10秒让消费者处理...")

    time.sleep(10)

    try:
        client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            decode_responses=True
        )

        # 检查 signals stream
        signals = client.xrevrange(redis_config.STREAM_SIGNALS, count=5)

        if signals:
            logger.info(f"✓ 发现 {len(signals)} 个信号:")

            for msg_id, msg_data in signals:
                # 解析信号数据
                import json

                signal_data = {}
                for key, value in msg_data.items():
                    try:
                        signal_data[key] = json.loads(value)
                    except:
                        signal_data[key] = value

                logger.info(f"\n信号 {msg_id}:")
                logger.info(f"  Ticker: {signal_data.get('ticker', 'N/A')}")
                logger.info(f"  方向: {signal_data.get('direction', 'N/A')}")
                logger.info(f"  手数: {signal_data.get('lot_size', 'N/A')}")
                logger.info(f"  止损: {signal_data.get('stop_loss', 'N/A')}")
                logger.info(f"  止盈: {signal_data.get('take_profit', 'N/A')}")
                logger.info(f"  情感: {signal_data.get('sentiment', 'N/A')} (score={signal_data.get('sentiment_score', 'N/A')})")
                logger.info(f"  资产类别: {signal_data.get('asset_class', 'N/A')}")

            return True
        else:
            logger.warning("⚠️ 未发现信号")
            logger.info("可能原因：")
            logger.info("  1. 消费者未运行")
            logger.info("  2. 新闻未通过情感阈值过滤")
            logger.info("  3. 处理时间较长，请稍后再检查")
            return False

    except Exception as e:
        logger.error(f"✗ 检查信号失败: {e}")
        return False


def cleanup_test_data():
    """清理测试数据（可选）"""
    logger.info("\n=== 清理测试数据 ===")
    logger.info("提示：如需清理，请手动运行: redis-cli FLUSHDB")


def main():
    """主测试流程"""
    logger.info("=" * 60)
    logger.info("MT5-CRS 驱动管家系统 - 端到端测试")
    logger.info("=" * 60)
    logger.info("\n测试流程：")
    logger.info("1. 测试 Redis 连接")
    logger.info("2. 发布测试新闻到 news_raw")
    logger.info("3. 监控各 stream 的数据")
    logger.info("4. 验证信号生成")
    logger.info("\n注意：测试3和4需要消费者进程正在运行！")
    logger.info("=" * 60 + "\n")

    results = {}

    # 测试1：Redis 连接
    results['redis'] = test_redis_connection()
    if not results['redis']:
        logger.error("\n❌ Redis 连接失败，请先启动 Redis")
        return False

    # 测试2：发布测试新闻
    results['publish'] = publish_test_news()
    if not results['publish']:
        logger.error("\n❌ 发布测试新闻失败")
        return False

    # 测试3：监控管道
    results['monitor'] = monitor_pipeline()

    # 测试4：验证信号
    results['signals'] = test_signal_generation()

    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"  {test_name}: {status}")

    logger.info(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        logger.info("\n🎉 所有测试通过！")
        logger.info("\n完整管道工作正常：")
        logger.info("  新闻发布 → 情感分析 → 信号生成 ✅")
    else:
        logger.warning("\n⚠️ 部分测试未通过")
        logger.info("\n建议检查：")
        logger.info("  1. 消费者进程是否在运行")
        logger.info("  2. FinBERT 模型是否已下载")
        logger.info("  3. 查看消费者日志排查问题")

    logger.info("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n测试出错: {e}", exc_info=True)
        sys.exit(1)
