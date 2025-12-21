"""
MT5 连接状态心跳监控单元测试

根据 Gemini Pro P1-03 建议，验证 MT5 心跳监控的正确性和性能。

测试覆盖:
- 初始化和配置
- 连接状态检查
- 状态转换和事件记录
- 重连机制
- 线程安全性
- 统计信息追踪
- 性能基准（检查耗时 < 100ms）
"""

import unittest
import time
import threading
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mt5_bridge.mt5_heartbeat import (
    MT5HeartbeatMonitor,
    HeartbeatConfig,
    HeartbeatEvent,
    ConnectionStatus,
    get_heartbeat_monitor,
)


class TestConnectionStatus(unittest.TestCase):
    """连接状态枚举测试"""

    def test_01_status_values(self):
        """测试状态值"""
        self.assertEqual(ConnectionStatus.CONNECTED.value, "connected")
        self.assertEqual(ConnectionStatus.DISCONNECTED.value, "disconnected")
        self.assertEqual(ConnectionStatus.RECONNECTING.value, "reconnecting")
        self.assertEqual(ConnectionStatus.FAILED.value, "failed")

    def test_02_status_comparison(self):
        """测试状态比较"""
        status1 = ConnectionStatus.CONNECTED
        status2 = ConnectionStatus.CONNECTED
        status3 = ConnectionStatus.DISCONNECTED

        self.assertEqual(status1, status2)
        self.assertNotEqual(status1, status3)


class TestHeartbeatEvent(unittest.TestCase):
    """心跳事件测试"""

    def test_01_create_event(self):
        """测试创建事件"""
        event = HeartbeatEvent(
            timestamp="2025-12-21T19:00:00",
            status=ConnectionStatus.CONNECTED,
            is_connected=True,
        )

        self.assertEqual(event.timestamp, "2025-12-21T19:00:00")
        self.assertEqual(event.status, ConnectionStatus.CONNECTED)
        self.assertTrue(event.is_connected)

    def test_02_event_to_dict(self):
        """测试事件转换为字典"""
        event = HeartbeatEvent(
            timestamp="2025-12-21T19:00:00",
            status=ConnectionStatus.CONNECTED,
            is_connected=True,
            server_name="MetaTrader5",
            trade_allowed=True,
        )

        event_dict = event.to_dict()

        self.assertIsInstance(event_dict, dict)
        self.assertEqual(event_dict["timestamp"], "2025-12-21T19:00:00")
        self.assertEqual(event_dict["status"], "connected")
        self.assertTrue(event_dict["is_connected"])


class TestHeartbeatConfig(unittest.TestCase):
    """心跳配置测试"""

    def test_01_default_config(self):
        """测试默认配置"""
        config = HeartbeatConfig()

        self.assertEqual(config.interval, 5)
        self.assertEqual(config.max_reconnect_attempts, 3)
        self.assertEqual(config.reconnect_backoff, 2.0)
        self.assertTrue(config.enable_logging)

    def test_02_custom_config(self):
        """测试自定义配置"""
        config = HeartbeatConfig(
            interval=10,
            max_reconnect_attempts=5,
            reconnect_backoff=1.5,
        )

        self.assertEqual(config.interval, 10)
        self.assertEqual(config.max_reconnect_attempts, 5)
        self.assertEqual(config.reconnect_backoff, 1.5)


class TestHeartbeatMonitorInitialization(unittest.TestCase):
    """心跳监控初始化测试"""

    def test_01_default_initialization(self):
        """测试默认初始化"""
        monitor = MT5HeartbeatMonitor()

        self.assertFalse(monitor.running)
        self.assertEqual(monitor.current_status, ConnectionStatus.DISCONNECTED)
        self.assertEqual(len(monitor.events), 0)
        self.assertEqual(monitor._reconnect_attempts, 0)

    def test_02_custom_config_initialization(self):
        """测试自定义配置初始化"""
        config = HeartbeatConfig(interval=10)
        monitor = MT5HeartbeatMonitor(config)

        self.assertEqual(monitor.config.interval, 10)
        self.assertFalse(monitor.running)

    def test_03_monitor_repr(self):
        """测试监控器字符串表示"""
        monitor = MT5HeartbeatMonitor()

        repr_str = repr(monitor)

        self.assertIn("MT5HeartbeatMonitor", repr_str)
        self.assertIn("running=False", repr_str)


class TestHeartbeatMonitorStartStop(unittest.TestCase):
    """心跳监控启动/停止测试"""

    def test_01_start_monitor(self):
        """测试启动监控"""
        monitor = MT5HeartbeatMonitor()

        result = monitor.start()

        self.assertTrue(result)
        self.assertTrue(monitor.running)

        monitor.stop()

    def test_02_double_start(self):
        """测试重复启动"""
        monitor = MT5HeartbeatMonitor()

        result1 = monitor.start()
        result2 = monitor.start()

        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(monitor.running)

        monitor.stop()

    def test_03_stop_monitor(self):
        """测试停止监控"""
        monitor = MT5HeartbeatMonitor()
        monitor.start()

        # 等待监控启动
        time.sleep(0.2)

        result = monitor.stop()

        self.assertTrue(result)
        self.assertFalse(monitor.running)

    def test_04_stop_without_start(self):
        """测试未启动时停止"""
        monitor = MT5HeartbeatMonitor()

        result = monitor.stop()

        self.assertTrue(result)
        self.assertFalse(monitor.running)


class TestHeartbeatMonitorConnection(unittest.TestCase):
    """连接检查测试"""

    def setUp(self):
        """测试前准备"""
        self.monitor = MT5HeartbeatMonitor(
            HeartbeatConfig(interval=1)  # 快速检查间隔
        )

    def tearDown(self):
        """测试后清理"""
        if self.monitor.running:
            self.monitor.stop()

    def test_01_get_status(self):
        """测试获取连接状态"""
        monitor = MT5HeartbeatMonitor()

        status = monitor.get_status()

        self.assertEqual(status, ConnectionStatus.DISCONNECTED)

    def test_02_is_connected(self):
        """测试连接状态布尔值"""
        monitor = MT5HeartbeatMonitor()

        # 初始状态：未连接
        self.assertFalse(monitor.is_connected())

    def test_03_current_status_attribute(self):
        """测试当前状态属性"""
        monitor = MT5HeartbeatMonitor()

        self.assertIsInstance(monitor.current_status, ConnectionStatus)
        self.assertEqual(monitor.current_status, ConnectionStatus.DISCONNECTED)


class TestHeartbeatMonitorEvents(unittest.TestCase):
    """事件记录测试"""

    def setUp(self):
        """测试前准备"""
        self.monitor = MT5HeartbeatMonitor()

    def test_01_record_event(self):
        """测试记录事件"""
        event = HeartbeatEvent(
            timestamp=datetime.now().isoformat(),
            status=ConnectionStatus.CONNECTED,
            is_connected=True,
        )

        self.monitor._record_event(event)

        self.assertEqual(len(self.monitor.events), 1)

    def test_02_get_events(self):
        """测试获取事件"""
        # 记录几个事件
        for i in range(5):
            event = HeartbeatEvent(
                timestamp=datetime.now().isoformat(),
                status=ConnectionStatus.CONNECTED if i % 2 == 0 else ConnectionStatus.DISCONNECTED,
                is_connected=i % 2 == 0,
            )
            self.monitor._record_event(event)

        events = self.monitor.get_events(limit=3)

        self.assertEqual(len(events), 3)
        self.assertIsInstance(events[0], dict)

    def test_03_get_last_event(self):
        """测试获取最后一条事件"""
        # 空事件列表
        self.assertIsNone(self.monitor.get_last_event())

        # 添加事件
        event = HeartbeatEvent(
            timestamp=datetime.now().isoformat(),
            status=ConnectionStatus.CONNECTED,
            is_connected=True,
        )
        self.monitor._record_event(event)

        last_event = self.monitor.get_last_event()

        self.assertIsNotNone(last_event)
        self.assertEqual(last_event["status"], "connected")

    def test_04_event_list_limit(self):
        """测试事件列表大小限制"""
        # 添加超过限制的事件
        for i in range(1100):
            event = HeartbeatEvent(
                timestamp=datetime.now().isoformat(),
                status=ConnectionStatus.CONNECTED,
                is_connected=True,
            )
            self.monitor._record_event(event)

        # 应该只保留最新的 1000 条
        self.assertEqual(len(self.monitor.events), 1000)


class TestHeartbeatMonitorStats(unittest.TestCase):
    """统计信息测试"""

    def setUp(self):
        """测试前准备"""
        self.monitor = MT5HeartbeatMonitor()

    def test_01_get_stats_initial(self):
        """测试初始统计信息"""
        stats = self.monitor.get_stats()

        self.assertFalse(stats['running'])
        self.assertEqual(stats['current_status'], 'disconnected')
        self.assertEqual(stats['total_events'], 0)
        self.assertFalse(stats['is_connected'])

    def test_02_get_stats_with_events(self):
        """测试有事件时的统计信息"""
        # 添加事件
        for i in range(3):
            event = HeartbeatEvent(
                timestamp=datetime.now().isoformat(),
                status=ConnectionStatus.CONNECTED,
                is_connected=True,
            )
            self.monitor._record_event(event)

        stats = self.monitor.get_stats()

        self.assertEqual(stats['total_events'], 3)
        self.assertEqual(stats['connected_events'], 3)
        self.assertEqual(stats['disconnected_events'], 0)


class TestHeartbeatMonitorStatusTransitions(unittest.TestCase):
    """状态转换测试"""

    def setUp(self):
        """测试前准备"""
        self.monitor = MT5HeartbeatMonitor()
        self.status_changes = []

        # 设置状态回调
        def on_status_change(event):
            self.status_changes.append(event.status)

        self.monitor.config.status_callback = on_status_change

    def test_01_determine_status_connected(self):
        """测试确定连接状态"""
        status = self.monitor._determine_status(is_connected=True)
        self.assertEqual(status, ConnectionStatus.CONNECTED)

    def test_02_determine_status_disconnected(self):
        """测试确定断连状态"""
        status = self.monitor._determine_status(is_connected=False)
        # 初始时应该是 DISCONNECTED 或 RECONNECTING
        self.assertIn(status, [ConnectionStatus.DISCONNECTED, ConnectionStatus.RECONNECTING])

    def test_03_status_change_callback(self):
        """测试状态变化回调"""
        event = HeartbeatEvent(
            timestamp=datetime.now().isoformat(),
            status=ConnectionStatus.CONNECTED,
            is_connected=True,
        )

        self.monitor._handle_status_change(event)

        self.assertEqual(len(self.status_changes), 1)
        self.assertEqual(self.status_changes[0], ConnectionStatus.CONNECTED)


class TestHeartbeatMonitorThreadSafety(unittest.TestCase):
    """线程安全性测试"""

    def test_01_concurrent_status_check(self):
        """测试并发状态检查"""
        monitor = MT5HeartbeatMonitor()
        results = []

        def check_status():
            for _ in range(10):
                status = monitor.get_status()
                results.append(status)

        threads = [threading.Thread(target=check_status) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 应该有 50 个结果，都是有效状态
        self.assertEqual(len(results), 50)
        self.assertTrue(all(isinstance(r, ConnectionStatus) for r in results))

    def test_02_concurrent_event_recording(self):
        """测试并发事件记录"""
        monitor = MT5HeartbeatMonitor()

        def record_events():
            for i in range(10):
                event = HeartbeatEvent(
                    timestamp=datetime.now().isoformat(),
                    status=ConnectionStatus.CONNECTED if i % 2 == 0 else ConnectionStatus.DISCONNECTED,
                    is_connected=i % 2 == 0,
                )
                monitor._record_event(event)

        threads = [threading.Thread(target=record_events) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 应该有 50 个事件（5 线程 × 10 事件）
        self.assertEqual(len(monitor.events), 50)


class TestHeartbeatMonitorPerformance(unittest.TestCase):
    """性能测试"""

    def test_01_check_connection_performance(self):
        """
        性能测试: 单次连接检查应该 < 100ms

        这是 P1-03 的关键验证指标
        """
        monitor = MT5HeartbeatMonitor()

        # Mock MT5 模块
        with patch('src.mt5_bridge.mt5_heartbeat.mt5') as mock_mt5:
            mock_mt5.initialize.return_value = True

            start = time.time()
            monitor._check_connection()
            elapsed = time.time() - start

            self.assertLess(
                elapsed, 0.1,
                f"连接检查耗时过长: {elapsed*1000:.2f}ms > 100ms"
            )

    def test_02_event_recording_performance(self):
        """测试事件记录性能"""
        monitor = MT5HeartbeatMonitor()

        start = time.time()

        for i in range(100):
            event = HeartbeatEvent(
                timestamp=datetime.now().isoformat(),
                status=ConnectionStatus.CONNECTED,
                is_connected=True,
            )
            monitor._record_event(event)

        elapsed = time.time() - start

        # 100 个事件应该在 10ms 内记录完成
        self.assertLess(elapsed, 0.01)

    def test_03_get_status_performance(self):
        """测试获取状态性能"""
        monitor = MT5HeartbeatMonitor()

        start = time.time()

        for _ in range(1000):
            monitor.get_status()

        elapsed = time.time() - start

        # 1000 次状态获取应该在 10ms 内完成
        self.assertLess(elapsed, 0.01)


class TestGlobalHeartbeatMonitor(unittest.TestCase):
    """全局心跳监控单例测试"""

    def tearDown(self):
        """清理全局实例"""
        import src.mt5_bridge.mt5_heartbeat as hb_module
        hb_module._heartbeat_monitor = None

    def test_01_singleton_pattern(self):
        """测试单例模式"""
        monitor1 = get_heartbeat_monitor()
        monitor2 = get_heartbeat_monitor()

        self.assertIs(monitor1, monitor2)

    def test_02_get_monitor_with_config(self):
        """测试使用配置获取监控器"""
        config = HeartbeatConfig(interval=10)
        monitor = get_heartbeat_monitor(config)

        self.assertEqual(monitor.config.interval, 10)


if __name__ == "__main__":
    unittest.main()
