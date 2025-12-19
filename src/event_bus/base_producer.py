"""Redis Streams 事件生产者基类"""
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis
from redis.exceptions import RedisError
from prometheus_client import Counter, Histogram

from .config import redis_config

logger = logging.getLogger(__name__)

# Prometheus 指标
events_produced_total = Counter(
    'mt5_events_produced_total',
    'Total number of events produced',
    ['stream', 'event_type']
)

event_produce_duration = Histogram(
    'mt5_event_produce_duration_seconds',
    'Time spent producing events',
    ['stream']
)

event_produce_errors = Counter(
    'mt5_event_produce_errors_total',
    'Total number of event production errors',
    ['stream', 'error_type']
)


class BaseEventProducer:
    """事件生产者基类

    功能：
    1. 连接 Redis Streams
    2. 发布事件到指定 stream
    3. 自动添加元数据（时间戳、事件ID等）
    4. 支持自动裁剪（MAXLEN ~ 近似裁剪）
    5. 错误处理与重试
    6. Prometheus 监控集成
    """

    def __init__(
        self,
        stream_key: str,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: Optional[int] = None,
        redis_password: Optional[str] = None,
    ):
        """初始化生产者

        Args:
            stream_key: Redis Stream 的 key
            redis_host: Redis 主机地址，默认从配置读取
            redis_port: Redis 端口，默认从配置读取
            redis_db: Redis 数据库编号，默认从配置读取
            redis_password: Redis 密码，默认从配置读取
        """
        self.stream_key = stream_key

        # Redis 连接配置
        self.redis_host = redis_host or redis_config.host
        self.redis_port = redis_port or redis_config.port
        self.redis_db = redis_db or redis_config.db
        self.redis_password = redis_password or redis_config.password

        # 初始化连接池
        self.redis_pool = redis.ConnectionPool(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            decode_responses=redis_config.decode_responses,
            max_connections=redis_config.max_connections,
            socket_timeout=redis_config.socket_timeout,
            socket_connect_timeout=redis_config.socket_connect_timeout,
        )

        self.redis_client: Optional[redis.Redis] = None
        self._connect()

        logger.info(
            f"EventProducer initialized for stream '{stream_key}' "
            f"at {self.redis_host}:{self.redis_port}/{self.redis_db}"
        )

    def _connect(self):
        """建立 Redis 连接"""
        try:
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _ensure_connection(self):
        """确保 Redis 连接正常，如果断开则重连"""
        try:
            if self.redis_client is None:
                self._connect()
            else:
                self.redis_client.ping()
        except RedisError as e:
            logger.warning(f"Redis connection lost, reconnecting: {e}")
            self._connect()

    def produce(
        self,
        event_data: Dict[str, Any],
        event_type: str = "unknown",
        maxlen: Optional[int] = None,
        approximate: bool = True,
    ) -> Optional[str]:
        """发布事件到 Redis Stream

        Args:
            event_data: 事件数据字典
            event_type: 事件类型，用于监控分类
            maxlen: Stream 最大长度，超过后自动裁剪旧消息，None 则使用配置默认值
            approximate: 是否使用近似裁剪（~），更高效

        Returns:
            事件ID（message_id），失败返回 None
        """
        start_time = time.time()

        try:
            self._ensure_connection()

            # 添加元数据
            enriched_data = self._enrich_event(event_data, event_type)

            # 序列化为字符串
            payload = {
                key: json.dumps(value) if not isinstance(value, str) else value
                for key, value in enriched_data.items()
            }

            # 发布到 Stream
            maxlen_value = maxlen if maxlen is not None else redis_config.max_stream_length

            message_id = self.redis_client.xadd(
                name=self.stream_key,
                fields=payload,
                maxlen=maxlen_value,
                approximate=approximate,
            )

            # 记录指标
            duration = time.time() - start_time
            events_produced_total.labels(
                stream=self.stream_key,
                event_type=event_type
            ).inc()
            event_produce_duration.labels(stream=self.stream_key).observe(duration)

            logger.debug(
                f"Event produced to '{self.stream_key}': "
                f"id={message_id}, type={event_type}, duration={duration:.3f}s"
            )

            return message_id

        except RedisError as e:
            event_produce_errors.labels(
                stream=self.stream_key,
                error_type=type(e).__name__
            ).inc()
            logger.error(
                f"Failed to produce event to '{self.stream_key}': {e}",
                exc_info=True
            )
            return None
        except Exception as e:
            event_produce_errors.labels(
                stream=self.stream_key,
                error_type="UnexpectedError"
            ).inc()
            logger.error(
                f"Unexpected error producing event to '{self.stream_key}': {e}",
                exc_info=True
            )
            return None

    def _enrich_event(self, event_data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        """为事件添加元数据

        Args:
            event_data: 原始事件数据
            event_type: 事件类型

        Returns:
            enriched_data: 增强后的事件数据
        """
        enriched = {
            "event_type": event_type,
            "produced_at": datetime.utcnow().isoformat() + "Z",
            "producer": self.__class__.__name__,
        }
        enriched.update(event_data)
        return enriched

    def produce_batch(
        self,
        events: List[Dict[str, Any]],
        event_type: str = "unknown",
        maxlen: Optional[int] = None,
    ) -> List[Optional[str]]:
        """批量发布事件

        Args:
            events: 事件数据列表
            event_type: 事件类型
            maxlen: Stream 最大长度

        Returns:
            message_ids: 事件ID列表，失败的为 None
        """
        message_ids = []
        for event_data in events:
            message_id = self.produce(event_data, event_type, maxlen)
            message_ids.append(message_id)

        success_count = sum(1 for mid in message_ids if mid is not None)
        logger.info(
            f"Batch produced {success_count}/{len(events)} events "
            f"to '{self.stream_key}'"
        )

        return message_ids

    def get_stream_info(self) -> Optional[Dict[str, Any]]:
        """获取 Stream 信息

        Returns:
            Stream 信息字典，包含长度、消费者组等
        """
        try:
            self._ensure_connection()
            info = self.redis_client.xinfo_stream(self.stream_key)
            return info
        except RedisError as e:
            logger.error(f"Failed to get stream info for '{self.stream_key}': {e}")
            return None

    def close(self):
        """关闭连接"""
        if self.redis_client:
            self.redis_client.close()
            logger.info(f"EventProducer for '{self.stream_key}' closed")
