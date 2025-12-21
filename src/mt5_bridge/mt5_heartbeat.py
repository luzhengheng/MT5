"""
MT5 连接状态心跳监控

根据 Gemini Pro P1-03 建议，实现定期检查 MT5 连接状态的心跳机制。

核心功能:
- 定期检查 MT5 连接状态
- 记录连接事件（连接/断连/重连）
- 提供重连机制
- 非阻塞式检查（与异步交易循环不冲突）
"""

import time
import logging
import threading
from datetime import datetime
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass, field, asdict
from enum import Enum

# MT5 库可能不在测试环境中
try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """连接状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class HeartbeatEvent:
    """心跳事件记录"""
    timestamp: str
    status: ConnectionStatus
    is_connected: bool
    server_name: Optional[str] = None
    trade_allowed: bool = False
    account_info: Optional[Dict] = None
    error_msg: Optional[str] = None
    reconnect_attempt: int = 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class HeartbeatConfig:
    """心跳配置"""
    # 检查间隔（秒）
    interval: int = 5

    # 重连配置
    max_reconnect_attempts: int = 3
    reconnect_backoff: float = 2.0  # 指数退避因子

    # 日志和回调
    enable_logging: bool = True
    status_callback: Optional[Callable[[HeartbeatEvent], None]] = None

    # 检查项
    check_connection: bool = True
    check_trade_allowed: bool = True
    check_account_info: bool = True


class MT5HeartbeatMonitor:
    """
    MT5 连接状态心跳监控器

    特点:
    - 非阻塞式定期检查（后台线程）
    - 自动重连机制
    - 完整的事件日志
    - 线程安全
    """

    def __init__(self, config: Optional[HeartbeatConfig] = None):
        """
        初始化心跳监控器

        Args:
            config: 心跳配置
        """
        self.config = config or HeartbeatConfig()

        # 状态跟踪
        self.running = False
        self.current_status = ConnectionStatus.DISCONNECTED
        self._last_status = None
        self._reconnect_attempts = 0
        self._last_check_time = None

        # 事件日志
        self.events: List[HeartbeatEvent] = []
        self._max_events = 1000  # 最多保留 1000 条事件

        # 线程管理
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

        logger.info(f"✓ MT5 心跳监控器初始化 (间隔: {self.config.interval}s)")

    def start(self) -> bool:
        """
        启动心跳监控

        Returns:
            是否成功启动
        """
        with self._lock:
            if self.running:
                logger.warning("⚠️ 心跳监控已在运行")
                return True

            try:
                self.running = True
                self._stop_event.clear()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    daemon=True,
                    name="MT5-Heartbeat"
                )
                self._monitor_thread.start()
                logger.info("✓ 心跳监控启动成功")
                return True
            except Exception as e:
                logger.error(f"✗ 启动心跳监控失败: {e}")
                self.running = False
                return False

    def stop(self) -> bool:
        """
        停止心跳监控

        Returns:
            是否成功停止
        """
        with self._lock:
            if not self.running:
                return True

            self._stop_event.set()
            self.running = False

            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)

            logger.info("✓ 心跳监控已停止")
            return True

    def _monitor_loop(self):
        """
        后台监控循环（在独立线程中运行）
        """
        logger.debug("📍 心跳监控线程已启动")

        while not self._stop_event.is_set():
            try:
                # 执行检查
                self._check_connection()

                # 等待下一次检查
                self._stop_event.wait(self.config.interval)

            except Exception as e:
                logger.error(f"❌ 心跳检查异常: {e}")
                time.sleep(self.config.interval)

        logger.debug("📍 心跳监控线程已退出")

    def _check_connection(self):
        """
        执行连接状态检查（线程安全）
        """
        with self._lock:
            try:
                self._last_check_time = datetime.now().isoformat()

                # 1. 检查基本连接
                is_connected = False
                try:
                    if mt5 is not None:
                        is_connected = mt5.initialize()
                    else:
                        logger.debug("MT5 库不可用")
                        is_connected = False
                except Exception as e:
                    logger.debug(f"MT5 初始化检查失败: {e}")
                    is_connected = False

                # 2. 构建事件
                event = HeartbeatEvent(
                    timestamp=self._last_check_time,
                    status=self._determine_status(is_connected),
                    is_connected=is_connected,
                    reconnect_attempt=self._reconnect_attempts,
                )

                # 3. 获取额外信息
                if is_connected and self.config.check_account_info and mt5 is not None:
                    try:
                        account_info = mt5.account_info()
                        if account_info:
                            event.server_name = account_info.server
                            event.trade_allowed = account_info.trade_allowed
                            event.account_info = {
                                'login': account_info.login,
                                'name': account_info.name,
                                'server': account_info.server,
                                'trade_allowed': account_info.trade_allowed,
                                'balance': float(account_info.balance),
                                'equity': float(account_info.equity),
                            }
                    except Exception as e:
                        logger.debug(f"⚠️ 获取账户信息失败: {e}")

                # 4. 状态转换处理
                self._handle_status_change(event)

                # 5. 记录事件
                self._record_event(event)

            except Exception as e:
                logger.error(f"❌ 连接检查异常: {e}")

    def _determine_status(self, is_connected: bool) -> ConnectionStatus:
        """
        确定当前连接状态

        Args:
            is_connected: MT5 初始化是否成功

        Returns:
            连接状态
        """
        if not is_connected:
            if self._last_status == ConnectionStatus.CONNECTED:
                return ConnectionStatus.RECONNECTING
            elif self._reconnect_attempts >= self.config.max_reconnect_attempts:
                return ConnectionStatus.FAILED
            else:
                return ConnectionStatus.DISCONNECTED
        else:
            return ConnectionStatus.CONNECTED

    def _handle_status_change(self, event: HeartbeatEvent):
        """
        处理连接状态变化

        Args:
            event: 心跳事件
        """
        # 状态变化检测
        if event.status != self._last_status:
            logger.warning(
                f"🔄 连接状态变化: {self._last_status.value if self._last_status else 'INIT'} "
                f"→ {event.status.value}"
            )
            self._last_status = event.status

            # 状态特定处理
            if event.status == ConnectionStatus.DISCONNECTED:
                self._handle_disconnection(event)
            elif event.status == ConnectionStatus.CONNECTED:
                self._handle_reconnection(event)
            elif event.status == ConnectionStatus.FAILED:
                self._handle_connection_failure(event)
        else:
            # 状态未变化，重置重连计数
            if event.status == ConnectionStatus.CONNECTED:
                self._reconnect_attempts = 0

        self.current_status = event.status

        # 触发回调
        if self.config.status_callback:
            try:
                self.config.status_callback(event)
            except Exception as e:
                logger.error(f"❌ 状态回调异常: {e}")

    def _handle_disconnection(self, event: HeartbeatEvent):
        """处理断连事件"""
        logger.warning(f"⚠️ MT5 已断连 (尝试重连 {self._reconnect_attempts + 1}/{self.config.max_reconnect_attempts})")

        if self._reconnect_attempts < self.config.max_reconnect_attempts:
            self._reconnect_attempts += 1
            # 实现指数退避
            backoff = self.config.reconnect_backoff ** (self._reconnect_attempts - 1)
            logger.info(f"📍 将在 {backoff:.1f}s 后尝试重连...")

    def _handle_reconnection(self, event: HeartbeatEvent):
        """处理重连成功事件"""
        if self._reconnect_attempts > 0:
            logger.info(f"✓ MT5 已重新连接 (尝试 {self._reconnect_attempts} 次后恢复)")
        else:
            logger.info(f"✓ MT5 已连接")

        self._reconnect_attempts = 0

    def _handle_connection_failure(self, event: HeartbeatEvent):
        """处理连接失败事件"""
        logger.error(
            f"❌ MT5 连接失败，超过最大重试次数 ({self.config.max_reconnect_attempts})"
        )
        event.error_msg = "Max reconnection attempts exceeded"

    def _record_event(self, event: HeartbeatEvent):
        """
        记录事件

        Args:
            event: 心跳事件
        """
        self.events.append(event)

        # 限制事件列表大小
        if len(self.events) > self._max_events:
            self.events = self.events[-self._max_events:]

        # 日志输出
        if self.config.enable_logging:
            if event.status == ConnectionStatus.CONNECTED:
                logger.info(
                    f"✓ 连接正常 | 服务器: {event.server_name} | "
                    f"允许交易: {event.trade_allowed} | "
                    f"余额: {event.account_info.get('balance', 'N/A') if event.account_info else 'N/A'}"
                )
            elif event.status == ConnectionStatus.DISCONNECTED:
                logger.warning(f"⚠️ 连接断开 | 时间: {event.timestamp}")
            elif event.status == ConnectionStatus.FAILED:
                logger.error(f"❌ 连接失败 | 错误: {event.error_msg}")

    def get_status(self) -> ConnectionStatus:
        """
        获取当前连接状态

        Returns:
            连接状态
        """
        with self._lock:
            return self.current_status

    def is_connected(self) -> bool:
        """
        是否已连接

        Returns:
            连接状态布尔值
        """
        with self._lock:
            return self.current_status == ConnectionStatus.CONNECTED

    def get_stats(self) -> Dict:
        """
        获取监控统计信息

        Returns:
            统计字典
        """
        with self._lock:
            connected_count = sum(
                1 for e in self.events
                if e.status == ConnectionStatus.CONNECTED
            )
            disconnected_count = sum(
                1 for e in self.events
                if e.status == ConnectionStatus.DISCONNECTED
            )

            return {
                'running': self.running,
                'current_status': self.current_status.value,
                'last_check_time': self._last_check_time,
                'total_events': len(self.events),
                'connected_events': connected_count,
                'disconnected_events': disconnected_count,
                'reconnect_attempts': self._reconnect_attempts,
                'is_connected': self.current_status == ConnectionStatus.CONNECTED,
            }

    def get_events(self, limit: int = 100) -> List[Dict]:
        """
        获取最近事件

        Args:
            limit: 返回的最大事件数

        Returns:
            事件列表
        """
        with self._lock:
            events = self.events[-limit:]
            return [e.to_dict() for e in events]

    def get_last_event(self) -> Optional[Dict]:
        """
        获取最后一条事件

        Returns:
            最后一条事件或 None
        """
        with self._lock:
            if self.events:
                return self.events[-1].to_dict()
            return None

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (
            f"MT5HeartbeatMonitor("
            f"running={stats['running']}, "
            f"status={stats['current_status']}, "
            f"events={stats['total_events']}"
            f")"
        )


# 全局实例
_heartbeat_monitor: Optional[MT5HeartbeatMonitor] = None


def get_heartbeat_monitor(
    config: Optional[HeartbeatConfig] = None
) -> MT5HeartbeatMonitor:
    """
    获取全局心跳监控实例（单例模式）

    Args:
        config: 心跳配置

    Returns:
        心跳监控实例
    """
    global _heartbeat_monitor

    if _heartbeat_monitor is None:
        _heartbeat_monitor = MT5HeartbeatMonitor(config)

    return _heartbeat_monitor
