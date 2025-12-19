"""简单的事件总线测试"""
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

import logging
import time
from datetime import datetime

# 修改导入，避免相对导入
import config as cfg
import redis
from prometheus_client import Counter, Histogram

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_redis_connection():
    """测试 Redis 连接"""
    logger.info("=== 测试 Redis 连接 ===")
    
    try:
        client = redis.Redis(
            host=cfg.redis_config.host,
            port=cfg.redis_config.port,
            db=cfg.redis_config.db,
            decode_responses=True
        )
        
        # 测试 ping
        result = client.ping()
        logger.info(f"✓ Redis 连接成功: {result}")
        
        # 测试基本操作
        test_key = "mt5:test:hello"
        client.set(test_key, "world", ex=10)
        value = client.get(test_key)
        logger.info(f"✓ Redis 读写测试: {test_key} = {value}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Redis 连接失败: {e}")
        return False


def test_stream_operations():
    """测试 Stream 基本操作"""
    logger.info("\n=== 测试 Stream 基本操作 ===")
    
    try:
        client = redis.Redis(
            host=cfg.redis_config.host,
            port=cfg.redis_config.port,
            db=cfg.redis_config.db,
            decode_responses=True
        )
        
        stream_key = "mt5:test:stream"
        
        # 1. 发布消息
        message_data = {
            "title": "测试新闻",
            "content": "这是一条测试新闻内容",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        message_id = client.xadd(stream_key, message_data, maxlen=100, approximate=True)
        logger.info(f"✓ 发布消息成功: {message_id}")
        
        # 2. 读取消息
        messages = client.xread({stream_key: '0'}, count=10)
        logger.info(f"✓ 读取到 {len(messages)} 个 stream")
        
        if messages:
            stream_name, stream_messages = messages[0]
            logger.info(f"  Stream: {stream_name}, 消息数: {len(stream_messages)}")
            for msg_id, msg_data in stream_messages:
                logger.info(f"  消息ID: {msg_id}")
                logger.info(f"  标题: {msg_data.get('title')}")
        
        # 3. 创建消费者组
        try:
            client.xgroup_create(stream_key, 'test-group', id='0', mkstream=True)
            logger.info(f"✓ 创建消费者组成功")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"✓ 消费者组已存在")
            else:
                raise
        
        # 4. 从消费者组读取
        group_messages = client.xreadgroup(
            'test-group',
            'consumer-1',
            {stream_key: '>'},
            count=10
        )
        
        if group_messages:
            logger.info(f"✓ 消费者组读取成功，收到 {len(group_messages[0][1])} 条新消息")
            
            # ACK 消息
            for _, msgs in group_messages:
                for msg_id, _ in msgs:
                    client.xack(stream_key, 'test-group', msg_id)
                    logger.info(f"✓ ACK 消息: {msg_id}")
        else:
            logger.info("  没有新消息（可能已被消费）")
        
        # 5. 获取 Stream 信息
        info = client.xinfo_stream(stream_key)
        logger.info(f"✓ Stream 信息:")
        logger.info(f"  长度: {info['length']}")
        logger.info(f"  消费者组数: {info['groups']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Stream 操作失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("开始事件总线基础测试\n")
    
    success_count = 0
    total_count = 2
    
    if test_redis_connection():
        success_count += 1
    
    if test_stream_operations():
        success_count += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"测试完成: {success_count}/{total_count} 通过")
    logger.info(f"{'='*50}")
