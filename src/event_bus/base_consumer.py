"""Redis Streams 事件消费者基类"""
import json
import logging
import time
import signal
import sys
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod
import redis
from redis.exceptions import RedisError
from prometheus_client import Counter, Histogram, Gauge

from .config import redis_config

logger = logging.getLogger(__name__)

# Prometheus 指标
events_consumed_total = Counter(
    'mt5_events_consumed_total',
    'Total number of events consumed',
    ['stream', 'consumer_group', 'status']
)

event_consume_duration = Histogram(
    'mt5_event_consume_duration_seconds',
    'Time spent consuming and processing events',
    ['stream', 'consumer_group']
)

event_process_errors = Counter(
    'mt5_event_process_errors_total',
    'Total number of event processing errors',
    ['stream', 'consumer_group', 'error_type']
)

pending_events_count = Gauge(
    'mt5_pending_events_count',
    'Number of pending events in consumer group',
    ['stream', 'consumer_group']
)


class BaseEventConsumer(ABC):
    """事件消费者基类

    功能：
    1. 从 Redis Streams 消费事件
    2. 支持消费者组（Consumer Group）
    3. 自动 ACK 或手动 ACK
    4. 处理 PEL（Pending Entry List）中的超时消息
    5. 错误处理与死信队列
    6. 优雅关闭
    7. Prometheus 监控集成

    子类需要实现 process_event() 方法
    """

    def __init__(
        self,
        stream_key: str,
        consumer_group: str,
        consumer_name: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: Optional[int] = None,
        redis_password: Optional[str] = None,
        auto_ack: bool = True,
        block_ms: Optional[int] = None,
        batch_size: Optional[int] = None,
    ):
        """初始化消费者

        Args:
            stream_key: Redis Stream 的 key
            consumer_group: 消费者组名称
            consumer_name: 消费者名称，默认为类名+时间戳
            redis_host: Redis 主机地址
            redis_port: Redis 端口
            redis_db: Redis 数据库编号
            redis_password: Redis 密码
            auto_ack: 是否自动 ACK，True 则处理成功后自动确认
            block_ms: 阻塞读取超时（毫秒），None 则使用配置默认值
            batch_size: 批量读取大小，None 则使用配置默认值
        """
        self.stream_key = stream_key
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"{self.__class__.__name__}_{int(time.time())}"
        self.auto_ack = auto_ack

        # Redis 连接配置
        self.redis_host = redis_host or redis_config.host
        self.redis_port = redis_port or redis_config.port
        self.redis_db = redis_db or redis_config.db
        self.redis_password = redis_password or redis_config.password

        # 消费配置
        self.block_ms = block_ms if block_ms is not None else redis_config.block_ms
        self.batch_size = batch_size if batch_size is not None else redis_config.batch_size

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

        # 初始化消费者组
        self._ensure_consumer_group()

        # 运行状态
        self.running = False

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(
            f"EventConsumer '{self.consumer_name}' initialized for "
            f"stream '{stream_key}', group '{consumer_group}' "
            f"at {self.redis_host}:{self.redis_port}/{self.redis_db}"
        )

    def _connect(self):
        """建立 Redis 连接"""
        try:
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _ensure_connection(self):
        """确保 Redis 连接正常"""
        try:
            if self.redis_client is None:
                self._connect()
            else:
                self.redis_client.ping()
        except RedisError:
            logger.warning("Redis connection lost, reconnecting...")
            self._connect()

    def _ensure_consumer_group(self):
        """确保消费者组存在，不存在则创建"""
        try:
            self._ensure_connection()

            # 尝试创建消费者组
            self.redis_client.xgroup_create(
                name=self.stream_key,
                groupname=self.consumer_group,
                id='0',  # 从头开始消费
                mkstream=True  # 如果 stream 不存在则创建
            )
            logger.info(
                f"Consumer group '{self.consumer_group}' created for "
                f"stream '{self.stream_key}'"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(
                    f"Consumer group '{self.consumer_group}' already exists "
                    f"for stream '{self.stream_key}'"
                )
            else:
                logger.error(f"Failed to create consumer group: {e}")
                raise

    @abstractmethod
    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """处理事件（子类必须实现）

        Args:
            event_id: 事件ID
            event_data: 事件数据字典

        Returns:
            bool: 处理是否成功，True 表示成功，False 表示失败
        """
        pass

    def start(self):
        """启动消费者，开始消费事件"""
        self.running = True
        logger.info(
            f"Consumer '{self.consumer_name}' starting to consume from "
            f"stream '{self.stream_key}', group '{self.consumer_group}'"
        )

        while self.running:
            try:
                # 1. 先处理 PEL 中的超时消息
                self._process_pending_messages()

                # 2. 读取新消息
                self._consume_new_messages()

            except RedisError as e:
                logger.error(f"Redis error in consumer loop: {e}", exc_info=True)
                time.sleep(5)  # 等待后重试
            except Exception as e:
                logger.error(f"Unexpected error in consumer loop: {e}", exc_info=True)
                time.sleep(5)

        logger.info(f"Consumer '{self.consumer_name}' stopped")

    def _consume_new_messages(self):
        """消费新消息"""
        self._ensure_connection()

        # 从 '>' 读取新消息（未被消费的）
        messages = self.redis_client.xreadgroup(
            groupname=self.consumer_group,
            consumername=self.consumer_name,
            streams={self.stream_key: '>'},
            count=self.batch_size,
            block=self.block_ms,
        )

        if not messages:
            return

        for stream_name, stream_messages in messages:
            for message_id, message_data in stream_messages:
                self._handle_message(message_id, message_data)

    def _process_pending_messages(self):
        """处理 PEL（Pending Entry List）中的超时消息"""
        try:
            self._ensure_connection()

            # 获取当前消费者的 PEL
            pending = self.redis_client.xpending_range(
                name=self.stream_key,
                groupname=self.consumer_group,
                min='-',
                max='+',
                count=self.batch_size,
                consumername=self.consumer_name,
            )

            if not pending:
                return

            # 处理超时的消息
            min_idle_time = redis_config.min_idle_time_ms
            for entry in pending:
                message_id = entry['message_id']
                idle_time = entry['time_since_delivered']
                times_delivered = entry['times_delivered']

                # 如果空闲时间超过阈值且未超过最大重试次数
                if idle_time >= min_idle_time and times_delivered <= redis_config.max_retries:
                    logger.warning(
                        f"Reprocessing pending message {message_id}, "
                        f"idle_time={idle_time}ms, delivered={times_delivered} times"
                    )

                    # 重新认领消息
                    claimed = self.redis_client.xclaim(
                        name=self.stream_key,
                        groupname=self.consumer_group,
                        consumername=self.consumer_name,
                        min_idle_time=min_idle_time,
                        message_ids=[message_id],
                    )

                    for msg_id, msg_data in claimed:
                        self._handle_message(msg_id, msg_data)

                elif times_delivered > redis_config.max_retries:
                    # 超过最大重试次数，移到死信队列
                    logger.error(
                        f"Message {message_id} exceeded max retries, "
                        f"moving to dead letter queue"
                    )
                    self._move_to_deadletter(message_id, entry)
                    # ACK 掉原消息
                    self.redis_client.xack(self.stream_key, self.consumer_group, message_id)

        except RedisError as e:
            logger.error(f"Error processing pending messages: {e}")

    def _handle_message(self, message_id: str, message_data: Dict[str, Any]):
        """处理单条消息"""
        start_time = time.time()

        try:
            # 解析 JSON 数据
            parsed_data = {}
            for key, value in message_data.items():
                try:
                    parsed_data[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[key] = value

            # 调用子类实现的处理方法
            success = self.process_event(message_id, parsed_data)

            duration = time.time() - start_time

            if success:
                # 处理成功
                if self.auto_ack:
                    self.redis_client.xack(self.stream_key, self.consumer_group, message_id)

                events_consumed_total.labels(
                    stream=self.stream_key,
                    consumer_group=self.consumer_group,
                    status='success'
                ).inc()

                logger.debug(
                    f"Event processed successfully: id={message_id}, "
                    f"duration={duration:.3f}s"
                )
            else:
                # 处理失败但不抛异常，记录错误
                events_consumed_total.labels(
                    stream=self.stream_key,
                    consumer_group=self.consumer_group,
                    status='failed'
                ).inc()

                logger.warning(
                    f"Event processing returned False: id={message_id}, "
                    f"will retry later"
                )

            event_consume_duration.labels(
                stream=self.stream_key,
                consumer_group=self.consumer_group
            ).observe(duration)

        except Exception as e:
            event_process_errors.labels(
                stream=self.stream_key,
                consumer_group=self.consumer_group,
                error_type=type(e).__name__
            ).inc()

            logger.error(
                f"Error processing event {message_id}: {e}",
                exc_info=True
            )

    def _move_to_deadletter(self, message_id: str, pending_info: Dict[str, Any]):
        """将消息移到死信队列"""
        try:
            deadletter_data = {
                'original_stream': self.stream_key,
                'original_message_id': message_id,
                'consumer_group': self.consumer_group,
                'consumer_name': self.consumer_name,
                'times_delivered': pending_info.get('times_delivered', 0),
                'moved_at': datetime.utcnow().isoformat() + 'Z',
            }

            self.redis_client.xadd(
                name=redis_config.STREAM_DEADLETTER,
                fields={k: json.dumps(v) for k, v in deadletter_data.items()},
            )

            logger.info(f"Message {message_id} moved to dead letter queue")

        except RedisError as e:
            logger.error(f"Failed to move message to deadletter: {e}")

    def _signal_handler(self, signum, frame):
        """信号处理器，优雅关闭"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def stop(self):
        """停止消费者"""
        self.running = False
        logger.info(f"Consumer '{self.consumer_name}' stopping...")

    def close(self):
        """关闭连接"""
        self.stop()
        if self.redis_client:
            self.redis_client.close()
            logger.info(f"Consumer '{self.consumer_name}' closed")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
