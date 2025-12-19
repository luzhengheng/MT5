"""事件总线集成测试"""
import logging
import time
import threading
from typing import Dict, Any

from base_producer import BaseEventProducer
from base_consumer import BaseEventConsumer
from config import redis_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class IntegrationTestConsumer(BaseEventConsumer):
    """集成测试消费者"""

    def __init__(self):
        super().__init__(
            stream_key='mt5:events:test_integration',
            consumer_group='test-group',
            consumer_name='test_consumer_1',
            auto_ack=True,
        )
        self.processed_events = []
        self.max_events = 10  # 处理10条后自动停止

    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """处理事件"""
        logger.info(f"处理事件: {event_id}, 数据: {event_data.get('message')}")
        self.processed_events.append(event_id)

        # 处理够数量后停止
        if len(self.processed_events) >= self.max_events:
            self.stop()

        return True


def test_producer_consumer_flow():
    """测试生产者-消费者完整流程"""
    logger.info("=== 事件总线集成测试 ===\n")

    # 1. 创建生产者
    logger.info("步骤 1: 创建生产者")
    producer = BaseEventProducer(stream_key='mt5:events:test_integration')

    # 2. 创建消费者
    logger.info("步骤 2: 创建消费者")
    consumer = IntegrationTestConsumer()

    # 3. 在后台线程启动消费者
    logger.info("步骤 3: 启动消费者线程")
    consumer_thread = threading.Thread(target=consumer.start)
    consumer_thread.daemon = True
    consumer_thread.start()

    # 等待消费者启动
    time.sleep(2)

    # 4. 生产者发布事件
    logger.info("\n步骤 4: 发布10条测试事件")
    for i in range(10):
        event_data = {
            "message": f"测试消息 {i}",
            "index": i,
            "timestamp": time.time()
        }
        message_id = producer.produce(event_data, event_type="test")
        logger.info(f"  发布事件 {i}: {message_id}")
        time.sleep(0.5)

    # 5. 等待消费者处理完成
    logger.info("\n步骤 5: 等待消费者处理完成")
    consumer_thread.join(timeout=30)

    # 6. 验证结果
    logger.info("\n步骤 6: 验证结果")
    logger.info(f"✓ 消费者处理了 {len(consumer.processed_events)} 条事件")

    if len(consumer.processed_events) == 10:
        logger.info("✓ 集成测试通过！")
        success = True
    else:
        logger.error("✗ 集成测试失败：处理的事件数量不正确")
        success = False

    # 7. 清理
    producer.close()
    consumer.close()

    return success


def test_pending_retry():
    """测试 PEL 重试机制"""
    logger.info("\n=== 测试 PEL 重试机制 ===\n")

    class FailingConsumer(BaseEventConsumer):
        """会失败的消费者"""

        def __init__(self):
            super().__init__(
                stream_key='mt5:events:test_retry',
                consumer_group='retry-test-group',
                consumer_name='failing_consumer',
                auto_ack=False,  # 不自动 ACK
            )
            self.attempts = {}

        def process_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
            """模拟处理失败"""
            self.attempts[event_id] = self.attempts.get(event_id, 0) + 1
            logger.info(f"处理事件 {event_id}，第 {self.attempts[event_id]} 次尝试")

            # 前3次失败，第4次成功
            if self.attempts[event_id] < 4:
                logger.warning(f"  模拟失败")
                return False
            else:
                logger.info(f"  处理成功！")
                # 手动 ACK
                self.redis_client.xack(self.stream_key, self.consumer_group, event_id)
                self.stop()
                return True

    # 发布一条测试事件
    producer = BaseEventProducer(stream_key='mt5:events:test_retry')
    event_data = {"message": "测试重试机制"}
    message_id = producer.produce(event_data, event_type="test")
    logger.info(f"发布测试事件: {message_id}")
    producer.close()

    # 启动消费者
    consumer = FailingConsumer()
    consumer.start()

    logger.info(f"\n✓ 重试测试完成，事件被处理了 {consumer.attempts.get(message_id, 0)} 次")
    consumer.close()


if __name__ == "__main__":
    try:
        # 运行集成测试
        success = test_producer_consumer_flow()

        if success:
            logger.info("\n" + "=" * 50)
            logger.info("所有集成测试通过！")
            logger.info("=" * 50)
        else:
            logger.error("\n集成测试失败")

    except Exception as e:
        logger.error(f"测试出错: {e}", exc_info=True)
