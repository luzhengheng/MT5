"""Redis Streams 事件总线配置"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class RedisConfig:
    """Redis 连接配置"""
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    db: int = int(os.getenv('REDIS_DB', '0'))
    password: Optional[str] = os.getenv('REDIS_PASSWORD')
    decode_responses: bool = True
    
    # 连接池配置
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    # Stream 配置
    max_stream_length: int = 30000  # 使用 ~ 近似裁剪
    block_ms: int = 5000  # 阻塞读取超时
    batch_size: int = 100  # 批量处理大小
    
    # 重试配置
    min_idle_time_ms: int = 300000  # 5分钟后重试
    max_retries: int = 3  # 最大重试次数
    
    # Stream Key 定义
    STREAM_NEWS_RAW = 'mt5:events:news_raw'
    STREAM_NEWS_FILTERED = 'mt5:events:news_filtered'
    STREAM_DEADLETTER = 'mt5:events:deadletter'
    
    # 消费者组定义
    CONSUMER_GROUP_NEWS_FILTER = 'news-filter-group'


# 全局配置实例
redis_config = RedisConfig()
