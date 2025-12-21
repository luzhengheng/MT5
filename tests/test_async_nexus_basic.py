"""
异步 Nexus 基础单元测试 (Python 3.6+ 兼容)

根据 Gemini Pro P1-01 建议，验证异步 API 调用不会阻塞交易系统

这是简化版本，重点测试：
- AsyncNexus 初始化和配置
- TradeLog 数据结构
- 统计信息追踪
- 非阻塞日志推送的即时性
"""

import unittest
import time
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.nexus.async_nexus import (
    AsyncNexus,
    TradeLog,
    APIConfig,
    get_nexus,
)


class TestAsyncNexusInitialization(unittest.TestCase):
    """AsyncNexus 初始化测试"""

    def test_01_basic_initialization(self):
        """测试基本初始化"""
        nexus = AsyncNexus()

        self.assertFalse(nexus.running)
        self.assertIsNone(nexus.queue)
        self.assertIsNotNone(nexus.config)
        self.assertEqual(nexus._stats["queued"], 0)
        self.assertEqual(nexus._stats["processed"], 0)
        self.assertEqual(nexus._stats["failed"], 0)

    def test_02_custom_config(self):
        """测试自定义配置"""
        config = APIConfig(
            gemini_key="test_key",
            gemini_model="gemini-1.5-flash",
            timeout=60,
            max_retries=5,
        )

        nexus = AsyncNexus(config=config)

        self.assertEqual(nexus.config.gemini_key, "test_key")
        self.assertEqual(nexus.config.gemini_model, "gemini-1.5-flash")
        self.assertEqual(nexus.config.timeout, 60)
        self.assertEqual(nexus.config.max_retries, 5)

    def test_03_config_from_env(self):
        """测试从环境变量加载配置"""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "env_key",
            "GEMINI_MODEL": "gemini-1.5-pro",
            "NEXUS_TIMEOUT": "45",
            "NEXUS_MAX_RETRIES": "7",
        }):
            config = AsyncNexus._load_config_from_env()

            self.assertEqual(config.gemini_key, "env_key")
            self.assertEqual(config.gemini_model, "gemini-1.5-pro")
            self.assertEqual(config.timeout, 45)
            self.assertEqual(config.max_retries, 7)


class TestTradeLog(unittest.TestCase):
    """TradeLog 数据结构测试"""

    def test_01_create_basic_log(self):
        """测试创建基本交易日志"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="BUY",
        )

        self.assertEqual(log.timestamp, "2025-12-21T19:00:00")
        self.assertEqual(log.symbol, "EURUSD")
        self.assertEqual(log.action, "BUY")
        self.assertEqual(log.price, 0.0)
        self.assertEqual(log.volume, 0.0)
        self.assertEqual(log.profit, 0.0)
        self.assertEqual(log.status, "PENDING")

    def test_02_create_full_log(self):
        """测试创建完整的交易日志"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="BUY",
            price=1.0950,
            volume=1.0,
            profit=50.0,
            status="FILLED",
            error_msg=None,
            comment="Test buy order",
        )

        self.assertEqual(log.price, 1.0950)
        self.assertEqual(log.volume, 1.0)
        self.assertEqual(log.profit, 50.0)
        self.assertEqual(log.status, "FILLED")
        self.assertEqual(log.comment, "Test buy order")

    def test_03_log_to_dict(self):
        """测试将日志转换为字典"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="GBPUSD",
            action="SELL",
            price=1.2650,
            volume=0.5,
        )

        log_dict = log.to_dict()

        self.assertIsInstance(log_dict, dict)
        self.assertEqual(log_dict["symbol"], "GBPUSD")
        self.assertEqual(log_dict["action"], "SELL")
        self.assertEqual(log_dict["price"], 1.2650)
        self.assertIn("timestamp", log_dict)

    def test_04_log_with_error(self):
        """测试包含错误信息的日志"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="ERROR",
            status="FAILED",
            error_msg="Connection timeout",
        )

        self.assertEqual(log.status, "FAILED")
        self.assertEqual(log.error_msg, "Connection timeout")


class TestAsyncNexusNonblocking(unittest.TestCase):
    """
    非阻塞推送性能测试

    关键验证: 日志推送应该在微秒级完成，不阻塞交易系统
    """

    def test_01_single_push_latency(self):
        """测试单条日志推送延迟"""
        nexus = AsyncNexus()
        nexus.start()

        try:
            start_time = time.time()

            # 推送日志
            nexus.push_trade_log(
                symbol="EURUSD",
                action="BUY",
                price=1.0950,
                volume=1.0,
            )

            elapsed = time.time() - start_time

            # 推送应该在 10ms 内完成（远快于网络请求）
            self.assertLess(
                elapsed, 0.01,
                f"推送延迟过高: {elapsed*1000:.2f}ms (应该 < 10ms)"
            )

            # 验证日志已入队
            self.assertEqual(nexus._stats["queued"], 1)

        finally:
            if nexus.running:
                # 同步停止（不支持 await）
                nexus.running = False

    def test_02_multiple_pushes_latency(self):
        """测试多条日志推送的总延迟"""
        nexus = AsyncNexus()
        nexus.start()

        try:
            start_time = time.time()

            # 推送 100 条日志
            for i in range(100):
                nexus.push_trade_log(
                    symbol=f"PAIR{i % 5}",
                    action="BUY" if i % 2 == 0 else "SELL",
                    price=1.0000 + (i * 0.0001),
                    volume=0.5 + (i * 0.01),
                )

            elapsed = time.time() - start_time

            # 100 条日志应该在 100ms 内推送完成
            self.assertLess(
                elapsed, 0.1,
                f"100 条日志推送耗时: {elapsed*1000:.2f}ms (应该 < 100ms)"
            )

            # 验证都被入队
            self.assertEqual(nexus._stats["queued"], 100)

        finally:
            if nexus.running:
                nexus.running = False

    def test_03_push_nonblocking_characteristic(self):
        """验证推送的非阻塞特性"""
        nexus = AsyncNexus()
        nexus.start()

        try:
            # 模拟交易循环：快速推送多条日志
            loop_times = []

            for iteration in range(10):
                start = time.time()

                # 推送日志（应该非常快）
                nexus.push_trade_log("EURUSD", "BUY", price=1.0950)

                elapsed = time.time() - start
                loop_times.append(elapsed)

            # 所有推送都应该非常快（< 1ms）
            max_loop_time = max(loop_times)
            avg_loop_time = sum(loop_times) / len(loop_times)

            self.assertLess(
                max_loop_time, 0.001,
                f"最长推送时间: {max_loop_time*1000:.3f}ms (应该 < 1ms)"
            )

            # 平均推送时间应该更短
            self.assertLess(avg_loop_time, 0.0005)

        finally:
            if nexus.running:
                nexus.running = False


class TestPromptFormatting(unittest.TestCase):
    """Gemini 提示格式化测试"""

    def test_01_format_simple_log(self):
        """测试简单日志的提示格式化"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="BUY",
        )

        prompt = AsyncNexus._format_gemini_prompt(log)

        # 验证包含关键信息
        self.assertIn("2025-12-21T19:00:00", prompt)
        self.assertIn("EURUSD", prompt)
        self.assertIn("BUY", prompt)
        self.assertIn("交易分析", prompt)

    def test_02_format_detailed_log(self):
        """测试详细日志的提示格式化"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="BUY",
            price=1.0950,
            volume=1.0,
            profit=50.0,
            status="FILLED",
        )

        prompt = AsyncNexus._format_gemini_prompt(log)

        # 验证价格信息（可能因浮点精度而不同）
        self.assertIn("1.09", prompt)  # 包含浮点值
        self.assertIn("1.0", prompt)  # 成交量
        self.assertIn("50.0", prompt)
        self.assertIn("FILLED", prompt)

    def test_03_format_error_log(self):
        """测试错误日志的提示格式化"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="ERROR",
            status="FAILED",
        )

        prompt = AsyncNexus._format_gemini_prompt(log)

        self.assertIn("ERROR", prompt)
        self.assertIn("FAILED", prompt)


class TestGlobalNexus(unittest.TestCase):
    """全局 Nexus 实例测试"""

    def test_01_singleton_pattern(self):
        """测试全局 Nexus 单例模式"""
        nexus1 = get_nexus()
        nexus2 = get_nexus()

        # 应该返回同一个实例
        self.assertIs(nexus1, nexus2)

    def test_02_global_config(self):
        """测试全局实例的配置"""
        nexus = get_nexus()

        self.assertIsNotNone(nexus.config)
        self.assertIsNotNone(nexus._stats)


class TestAsyncNexusRepr(unittest.TestCase):
    """字符串表示测试"""

    def test_01_repr_when_stopped(self):
        """测试停止状态的字符串表示"""
        nexus = AsyncNexus()

        repr_str = repr(nexus)

        self.assertIn("AsyncNexus", repr_str)
        self.assertIn("running=False", repr_str)

    def test_02_repr_when_running(self):
        """测试运行状态的字符串表示"""
        nexus = AsyncNexus()
        nexus.start()

        try:
            repr_str = repr(nexus)

            self.assertIn("AsyncNexus", repr_str)
            self.assertIn("running=True", repr_str)

        finally:
            if nexus.running:
                nexus.running = False


if __name__ == "__main__":
    unittest.main()
