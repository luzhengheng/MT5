"""事件消费者测试工具"""
import logging
from typing import Dict, Any

from base_consumer import BaseEventConsumer
from config import redis_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestNewsConsumer(BaseEventConsumer):
    """测试用的新闻消费者"""

    def __init__(self):
        super().__init__(
            stream_key=redis_config.STREAM_NEWS_RAW,
            consumer_group=redis_config.CONSUMER_GROUP_NEWS_FILTER,
            consumer_name="test_consumer",
            auto_ack=True,
            block_ms=5000,
            batch_size=10,
        )
        self.processed_count = 0

    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """处理事件"""
        try:
            logger.info(f"\n处理事件: {event_id}")
            logger.info(f"  事件类型: {event_data.get('event_type')}")
            logger.info(f"  标题: {event_data.get('title')}")
            logger.info(f"  来源: {event_data.get('source')}")
            logger.info(f"  符号: {event_data.get('symbols')}")

            self.processed_count += 1

            # 模拟处理成功
            return True

        except Exception as e:
            logger.error(f"处理事件失败: {e}", exc_info=True)
            return False


def test_consumer():
    """测试消费者"""
    logger.info("=== 启动测试消费者 ===")
    logger.info("提示：先运行 test_producer.py 发布一些事件")
    logger.info("按 Ctrl+C 停止消费者\n")

    consumer = TestNewsConsumer()

    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info(f"\n收到停止信号")
    finally:
        logger.info(f"共处理 {consumer.processed_count} 条事件")
        consumer.close()


if __name__ == "__main__":
    test_consumer()
