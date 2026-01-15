#!/usr/bin/env python3
"""
Market Data Ingestion Layer - ZMQ Subscriber Implementation
===========================================================

此模块实现 Linux 端的 ZMQ Subscriber，对接 Windows Gateway (GTW) 的行情广播 (Port 5556)。

核心职能：
1. 接收 GTW 发送的 JSON Tick 数据
2. 清洗和验证数据格式（处理时间戳差异）
3. 提供非阻塞的 get_latest_tick() 接口
4. 实现数据饥饿检测（10 秒无数据触发告警）

设计模式：
- 单例模式：全局只有一个 MarketDataReceiver 实例
- 异步架构：后台线程接收数据，主线程非阻塞轮询
- 韧性设计：网络故障不导致系统崩溃

Protocol v4.3 适配：
- 零信任：所有接收的数据都通过验证和日志记录
- 物理证据：所有关键事件都有时间戳和日志
"""

import zmq
import json
import logging
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================================
# 常量定义
# ============================================================================

# ZMQ 连接参数
ZMQ_INTERNAL_IP = "172.19.141.255"  # Windows Gateway 内网 IP
ZMQ_DATA_PORT = 5556  # 行情推送端口

# 数据饥饿检测
DATA_STARVATION_THRESHOLD = 10  # 10 秒无数据触发告警
HEARTBEAT_INTERVAL = 2  # 心跳检测间隔（秒）

# 缓冲区配置
TICK_BUFFER_SIZE = 1000  # 最多保留最近 1000 条 tick


# ============================================================================
# Market Data Receiver 类
# ============================================================================

class MarketDataReceiver:
    """
    ZMQ 市场数据接收器 - 单例模式

    此类管理与 Windows Gateway 的 ZMQ 连接，并在后台线程中接收 Tick 数据。

    Attributes:
        _instance: 单例实例（类级别）
        context: ZMQ Context
        socket: ZMQ SUB Socket
        running: 运行标志
        latest_tick: 最新的 tick 数据
        tick_buffer: Tick 数据缓冲队列
        last_tick_time: 最后接收到数据的时间戳
        tick_count: 累计接收的 tick 数量
        receiver_thread: 接收线程
    """

    _instance: Optional['MarketDataReceiver'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """确保单例模式（线程安全）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MarketDataReceiver, cls).__new__(cls)
        return cls._instance

    def __init__(self, host: str = ZMQ_INTERNAL_IP, port: int = ZMQ_DATA_PORT):
        """
        初始化市场数据接收器

        Args:
            host: ZMQ 服务器地址（内网 IP）
            port: ZMQ 服务器端口
        """
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.host = host
        self.port = port
        self.context = None
        self.socket = None
        self.running = False
        self.receiver_thread = None

        # 数据存储
        self.latest_tick: Optional[Dict[str, Any]] = None
        self.tick_buffer: deque = deque(maxlen=TICK_BUFFER_SIZE)
        self.last_tick_time = time.time()
        self.tick_count = 0

        # 线程安全锁
        self._data_lock = threading.Lock()

        logger.info("[Ingestion] MarketDataReceiver 初始化完成")

    # ========================================================================
    # 生命周期管理
    # ========================================================================

    def start(self) -> bool:
        """
        启动数据接收器

        1. 创建 ZMQ Context 和 SUB Socket
        2. 连接到 GTW 的 ZMQ PUB 端口
        3. 启动后台接收线程

        Returns:
            True 如果启动成功，False 否则
        """
        if self.running:
            logger.warning("[Ingestion] 接收器已运行")
            return False

        try:
            logger.info(f"[Ingestion] 正在启动数据接收器 ({self.host}:{self.port})...")

            # 创建 ZMQ Context
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)

            # 订阅所有消息（空过滤器）
            # 注意：可以改为订阅特定货币对，如 setsockopt_string(zmq.SUBSCRIBE, "EURUSD")
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

            # 设置接收超时（用于响应关闭请求）
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 秒超时

            # 连接到 GTW
            zmq_addr = f"tcp://{self.host}:{self.port}"
            self.socket.connect(zmq_addr)

            # 等待连接建立
            time.sleep(0.5)

            # 启动接收线程
            self.running = True
            self.receiver_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True,
                name="ZMQ-Receiver-Thread"
            )
            self.receiver_thread.start()

            logger.info(f"[Ingestion] ✅ 数据接收器已启动")
            return True

        except Exception as e:
            logger.error(f"[Ingestion] ❌ 启动失败: {e}")
            self.running = False
            return False

    def stop(self):
        """
        停止数据接收器

        1. 设置运行标志为 False
        2. 等待接收线程结束
        3. 关闭 ZMQ Socket 和 Context
        """
        if not self.running:
            logger.warning("[Ingestion] 接收器未运行")
            return

        logger.info("[Ingestion] 正在停止数据接收器...")
        self.running = False

        # 等待线程结束
        if self.receiver_thread:
            self.receiver_thread.join(timeout=3.0)

        # 关闭 ZMQ
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()

        logger.info("[Ingestion] ✅ 数据接收器已停止")

    # ========================================================================
    # 数据接收循环
    # ========================================================================

    def _receive_loop(self):
        """
        后台接收循环（运行在独立线程中）

        持续接收 ZMQ 消息，解析 JSON，更新 latest_tick 和缓冲区。
        处理错误和网络故障，实现韧性设计。
        """
        logger.info("[Ingestion] 接收循环已启动")

        while self.running:
            try:
                # 接收原始数据
                raw_data = self.socket.recv()

                # 解析 JSON
                try:
                    tick_data = json.loads(raw_data.decode('utf-8'))

                    # 数据清洗和验证
                    cleaned_tick = self._clean_tick(tick_data)

                    # 更新最新 tick 和缓冲区
                    with self._data_lock:
                        self.latest_tick = cleaned_tick
                        self.tick_buffer.append(cleaned_tick)
                        self.last_tick_time = time.time()
                        self.tick_count += 1

                    # 日志记录（物理证据）
                    symbol = cleaned_tick.get('symbol', 'UNKNOWN')
                    bid = cleaned_tick.get('bid', 'N/A')
                    ask = cleaned_tick.get('ask', 'N/A')
                    logger.debug(
                        f"[LIVE_TICK] {symbol}: bid={bid}, ask={ask}, "
                        f"count={self.tick_count}"
                    )

                except json.JSONDecodeError as e:
                    logger.warning(f"[Ingestion] JSON 解析失败: {e}")

            except zmq.Again:
                # 接收超时 - 检查数据饥饿
                self._check_data_starvation()
                continue

            except Exception as e:
                logger.error(f"[Ingestion] 接收错误: {e}")
                time.sleep(0.1)

        logger.info("[Ingestion] 接收循环已停止")

    # ========================================================================
    # 数据清洗
    # ========================================================================

    def _clean_tick(self, raw_tick: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗原始 Tick 数据

        处理关键问题：
        1. 时间戳格式统一（Unix Timestamp -> 保留原值）
        2. 字段名称大小写标准化（bid/Bid -> bid）
        3. 数据类型验证

        Args:
            raw_tick: 原始 JSON 数据

        Returns:
            清洗后的标准格式 Tick 数据
        """
        cleaned = {}

        # 处理 symbol
        if 'symbol' in raw_tick:
            cleaned['symbol'] = str(raw_tick['symbol']).strip()

        # 处理 bid 价格（支持 bid/Bid）
        bid = raw_tick.get('bid') or raw_tick.get('Bid')
        if bid is not None:
            try:
                cleaned['bid'] = float(bid)
            except (ValueError, TypeError):
                logger.warning(f"[Ingestion] 无法转换 bid: {bid}")
                cleaned['bid'] = 0.0

        # 处理 ask 价格（支持 ask/Ask）
        ask = raw_tick.get('ask') or raw_tick.get('Ask')
        if ask is not None:
            try:
                cleaned['ask'] = float(ask)
            except (ValueError, TypeError):
                logger.warning(f"[Ingestion] 无法转换 ask: {ask}")
                cleaned['ask'] = 0.0

        # 处理时间戳
        ts = raw_tick.get('timestamp') or raw_tick.get('time')
        if ts is not None:
            try:
                # 如果是字符串，尝试转为浮点数
                if isinstance(ts, str):
                    cleaned['timestamp'] = float(ts)
                else:
                    cleaned['timestamp'] = float(ts)
            except (ValueError, TypeError):
                cleaned['timestamp'] = time.time()
        else:
            cleaned['timestamp'] = time.time()

        # 其他字段直接传递
        for key in ['volume', 'bid_volume', 'ask_volume']:
            if key in raw_tick:
                try:
                    cleaned[key] = float(raw_tick[key])
                except (ValueError, TypeError):
                    pass

        return cleaned

    # ========================================================================
    # 数据查询接口
    # ========================================================================

    def get_latest_tick(self, timeout_ms: int = 100) -> Optional[Dict[str, Any]]:
        """
        获取最新的 Tick 数据（非阻塞）

        此方法由主线程调用，用于驱动策略引擎。

        Args:
            timeout_ms: 轮询超时时间（毫秒，无实际效果，保留接口兼容性）

        Returns:
            最新的 tick 数据字典，或 None 如果无新数据
        """
        with self._data_lock:
            return self.latest_tick

    def get_tick_history(self, limit: int = 10) -> list:
        """
        获取最近的 Tick 历史

        Args:
            limit: 返回最多多少条数据

        Returns:
            Tick 数据列表（最新的在最后）
        """
        with self._data_lock:
            return list(self.tick_buffer)[-limit:]

    # ========================================================================
    # 监控和诊断
    # ========================================================================

    def _check_data_starvation(self):
        """
        检查数据饥饿状态

        如果 10 秒内未收到数据，记录警告日志。
        """
        now = time.time()
        time_since_last = now - self.last_tick_time

        if time_since_last > DATA_STARVATION_THRESHOLD:
            logger.warning(
                f"[Ingestion] ⚠️  数据饥饿告警: "
                f"{time_since_last:.1f}s 未收到数据 "
                f"(状态: DATA_STARVED)"
            )

    def get_status(self) -> Dict[str, Any]:
        """
        获取接收器状态（用于诊断和监控）

        Returns:
            状态字典，包含连接、数据统计等信息
        """
        now = time.time()
        time_since_last = now - self.last_tick_time

        with self._data_lock:
            status = {
                'running': self.running,
                'host': self.host,
                'port': self.port,
                'tick_count': self.tick_count,
                'latest_tick': self.latest_tick,
                'buffer_size': len(self.tick_buffer),
                'time_since_last_tick': time_since_last,
                'data_starved': time_since_last > DATA_STARVATION_THRESHOLD,
            }

        return status

    def log_status(self):
        """打印当前状态（用于调试）"""
        status = self.get_status()
        logger.info(f"[Ingestion] 状态: {status}")


# ============================================================================
# 全局单例工厂函数
# ============================================================================

_receiver_instance: Optional[MarketDataReceiver] = None


def get_market_data_receiver(
    host: str = ZMQ_INTERNAL_IP,
    port: int = ZMQ_DATA_PORT
) -> MarketDataReceiver:
    """
    获取全局的 MarketDataReceiver 单例实例

    Args:
        host: ZMQ 服务器地址
        port: ZMQ 服务器端口

    Returns:
        MarketDataReceiver 单例实例
    """
    global _receiver_instance
    if _receiver_instance is None:
        _receiver_instance = MarketDataReceiver(host, port)
    return _receiver_instance
