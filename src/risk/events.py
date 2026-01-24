"""
Risk Events System
RFC-135: Dynamic Risk Management System

提供风险事件的发送、处理和监听机制
Protocol v4.4 compliant
"""

import threading
import logging
from datetime import datetime
from typing import Callable, List, Dict, Any
from queue import Queue, Empty
from decimal import Decimal

from .models import RiskEvent
from .enums import RiskLevel

logger = logging.getLogger(__name__)


class RiskEventBus:
    """
    风险事件总线

    提供事件发送、注册监听器、事件历史记录等功能
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化事件总线

        Args:
            max_history: 保留的最大事件历史记录数
        """
        self.max_history = max_history
        self._listeners: List[Callable[[RiskEvent], None]] = []
        self._history: Queue = Queue(maxsize=max_history)
        self._lock = threading.RLock()
        logger.info("RiskEventBus initialized with max_history=%d", max_history)

    def subscribe(self, listener: Callable[[RiskEvent], None]) -> None:
        """
        订阅风险事件

        Args:
            listener: 事件监听器回调函数
        """
        with self._lock:
            self._listeners.append(listener)
            logger.info("Listener subscribed: %s", listener.__name__)

    def unsubscribe(self, listener: Callable[[RiskEvent], None]) -> None:
        """
        取消订阅风险事件

        Args:
            listener: 要移除的事件监听器
        """
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
                logger.info("Listener unsubscribed: %s", listener.__name__)

    def publish(self, event: RiskEvent) -> None:
        """
        发布风险事件

        Args:
            event: 风险事件
        """
        with self._lock:
            # 添加到历史记录
            try:
                self._history.put_nowait(event)
            except Exception:
                # 队列满，移除最早的事件
                try:
                    self._history.get_nowait()
                    self._history.put_nowait(event)
                except Exception as e:
                    logger.error("Error adding event to history: %s", e)

            # 通知所有监听器
            for listener in self._listeners:
                try:
                    listener(event)
                except Exception as e:
                    logger.error("Error in listener %s: %s", listener.__name__, e)

    def get_history(self, limit: int = 100) -> List[RiskEvent]:
        """
        获取事件历史记录

        Args:
            limit: 返回的最大事件数

        Returns:
            事件列表
        """
        with self._lock:
            events = []
            try:
                while len(events) < limit:
                    events.append(self._history.get_nowait())
            except Empty:
                pass
            # 恢复队列
            for event in events:
                self._history.put_nowait(event)
            return list(reversed(events))  # 按时间顺序返回

    def get_events_by_severity(self, severity: RiskLevel, limit: int = 100) -> List[RiskEvent]:
        """
        获取特定严重程度的事件

        Args:
            severity: 风险级别
            limit: 返回的最大事件数

        Returns:
            事件列表
        """
        events = self.get_history(limit * 3)  # 获取更多以筛选
        return [e for e in events if e.severity == severity][:limit]


class RiskAlertHandler:
    """
    风险告警处理器

    根据风险事件的严重程度生成告警
    """

    def __init__(self, alert_thresholds: Dict[RiskLevel, Callable[[RiskEvent], bool]] = None):
        """
        初始化告警处理器

        Args:
            alert_thresholds: 告警阈值字典 (风险级别 -> 告警条件)
        """
        self.alert_thresholds = alert_thresholds or self._default_thresholds()
        self._lock = threading.RLock()
        self.active_alerts: List[Dict[str, Any]] = []
        logger.info("RiskAlertHandler initialized")

    @staticmethod
    def _default_thresholds() -> Dict[RiskLevel, Callable]:
        """返回默认的告警阈值"""
        return {
            RiskLevel.CRITICAL: lambda e: True,  # 临界状态总是告警
            RiskLevel.HALT: lambda e: True,      # 停止状态总是告警
        }

    def handle_event(self, event: RiskEvent) -> bool:
        """
        处理风险事件并判断是否触发告警

        Args:
            event: 风险事件

        Returns:
            是否触发告警
        """
        with self._lock:
            # 检查是否应该触发告警
            condition = self.alert_thresholds.get(event.severity)
            if condition and condition(event):
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": event.event_type,
                    "severity": event.severity.name,
                    "message": event.message,
                    "data": event.data,
                    "status": "active"
                }
                self.active_alerts.append(alert)
                logger.warning("ALERT TRIGGERED: %s - %s", event.event_type, event.message)
                return True
            return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃的告警

        Returns:
            活跃告警列表
        """
        with self._lock:
            return [a for a in self.active_alerts if a["status"] == "active"]

    def clear_alert(self, alert_index: int) -> bool:
        """
        清除指定的告警

        Args:
            alert_index: 告警索引

        Returns:
            是否成功清除
        """
        with self._lock:
            if 0 <= alert_index < len(self.active_alerts):
                self.active_alerts[alert_index]["status"] = "resolved"
                return True
            return False

    def clear_all_alerts(self) -> int:
        """
        清除所有告警

        Returns:
            清除的告警数量
        """
        with self._lock:
            count = len([a for a in self.active_alerts if a["status"] == "active"])
            for alert in self.active_alerts:
                alert["status"] = "resolved"
            return count


class RiskEventLogger:
    """
    风险事件日志记录器

    提供结构化的风险事件日志记录
    """

    def __init__(self, log_file: str = None):
        """
        初始化事件日志记录器

        Args:
            log_file: 日志文件路径，如果为 None 则仅输出到标准日志
        """
        self.log_file = log_file
        self._lock = threading.RLock()
        if log_file:
            logger.info("Event logger initialized with file: %s", log_file)
        else:
            logger.info("Event logger initialized (console only)")

    def log_event(self, event: RiskEvent) -> None:
        """
        记录风险事件

        Args:
            event: 风险事件
        """
        with self._lock:
            log_entry = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "severity": event.severity.name,
                "message": event.message,
                "data": event.data
            }

            # 输出到标准日志
            log_message = f"[{event.severity.name}] {event.event_type}: {event.message}"
            if event.severity == RiskLevel.HALT:
                logger.critical(log_message)
            elif event.severity == RiskLevel.CRITICAL:
                logger.error(log_message)
            elif event.severity == RiskLevel.WARNING:
                logger.warning(log_message)
            else:
                logger.info(log_message)

            # 输出到文件
            if self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        import json
                        f.write(json.dumps(log_entry) + '\n')
                except Exception as e:
                    logger.error("Error writing to log file: %s", e)

    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的事件日志

        Args:
            count: 返回的最大事件数

        Returns:
            事件日志列表
        """
        if not self.log_file:
            return []

        with self._lock:
            try:
                events = []
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 返回最后的 count 行
                    for line in lines[-count:]:
                        if line.strip():
                            import json
                            events.append(json.loads(line))
                return events
            except Exception as e:
                logger.error("Error reading log file: %s", e)
                return []


# 全局事件总线实例
_global_event_bus: RiskEventBus = None
_global_alert_handler: RiskAlertHandler = None
_global_event_logger: RiskEventLogger = None


def initialize_global_event_system(log_file: str = None) -> RiskEventBus:
    """
    初始化全局事件系统

    Args:
        log_file: 日志文件路径

    Returns:
        全局事件总线实例
    """
    global _global_event_bus, _global_alert_handler, _global_event_logger

    _global_event_bus = RiskEventBus()
    _global_alert_handler = RiskAlertHandler()
    _global_event_logger = RiskEventLogger(log_file)

    # 连接处理器
    _global_event_bus.subscribe(_global_alert_handler.handle_event)
    _global_event_bus.subscribe(_global_event_logger.log_event)

    logger.info("Global event system initialized")
    return _global_event_bus


def get_event_bus() -> RiskEventBus:
    """获取全局事件总线"""
    global _global_event_bus
    if _global_event_bus is None:
        initialize_global_event_system()
    return _global_event_bus


def get_alert_handler() -> RiskAlertHandler:
    """获取全局告警处理器"""
    global _global_alert_handler
    if _global_alert_handler is None:
        initialize_global_event_system()
    return _global_alert_handler


def get_event_logger() -> RiskEventLogger:
    """获取全局事件日志记录器"""
    global _global_event_logger
    if _global_event_logger is None:
        initialize_global_event_system()
    return _global_event_logger
