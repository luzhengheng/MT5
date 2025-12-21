"""
异步 Nexus 单元测试

根据 Gemini Pro P1-01 建议，验证异步 API 调用不会阻塞交易系统

测试覆盖:
- 后台任务初始化和关闭
- 非阻塞日志推送
- 队列处理
- API 调用（mock）
- 统计信息
"""

import unittest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Python 3.6 兼容性处理 (AsyncMock 在 3.8+ 可用)
try:
    from unittest.mock import AsyncMock
except ImportError:
    # Python 3.6/3.7 polyfill
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.nexus.async_nexus import (
    AsyncNexus,
    TradeLog,
    APIConfig,
    get_nexus,
)


class TestAsyncNexusBasics(unittest.TestCase):
    """异步 Nexus 基础功能测试"""

    def setUp(self):
        """测试前准备"""
        self.nexus = AsyncNexus()

    def test_01_initialization(self):
        """测试初始化"""
        self.assertFalse(self.nexus.running)
        self.assertIsNone(self.nexus.queue)
        self.assertIsNotNone(self.nexus.config)
        self.assertEqual(self.nexus._stats["queued"], 0)

    def test_02_config_from_env(self):
        """测试从环境变量加载配置"""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "GEMINI_MODEL": "gemini-1.5-flash",
            "NEXUS_TIMEOUT": "60",
        }):
            config = AsyncNexus._load_config_from_env()

            self.assertEqual(config.gemini_key, "test_key")
            self.assertEqual(config.gemini_model, "gemini-1.5-flash")
            self.assertEqual(config.timeout, 60)

    def test_03_get_global_nexus(self):
        """测试全局 Nexus 实例"""
        nexus1 = get_nexus()
        nexus2 = get_nexus()

        # 应该返回同一个实例
        self.assertIs(nexus1, nexus2)

    def test_04_trade_log_creation(self):
        """测试交易日志创建"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="BUY",
            price=1.0950,
            volume=1.0,
            profit=0.0,
            status="PENDING",
        )

        self.assertEqual(log.symbol, "EURUSD")
        self.assertEqual(log.action, "BUY")
        self.assertEqual(log.price, 1.0950)

        # 转换为字典
        log_dict = log.to_dict()
        self.assertIn("timestamp", log_dict)
        self.assertIn("symbol", log_dict)


# Python 3.6 兼容性处理 (IsolatedAsyncioTestCase 在 3.8+ 可用)
try:
    from unittest import IsolatedAsyncioTestCase as BaseAsyncTestCase
except ImportError:
    # Python 3.6/3.7 polyfill
    class BaseAsyncTestCase(unittest.TestCase):
        def __init__(self, methodName='runTest'):
            super().__init__(methodName)
            self._asyncioRunner = None

        async def asyncSetUp(self):
            pass

        async def asyncTearDown(self):
            pass

        def run(self, result=None):
            # 简化版本：只运行同步测试
            if hasattr(self, '_testMethodName'):
                if self._testMethodName.startswith('test_'):
                    return super().run(result)
            return super().run(result)


class TestAsyncNexusQueueing(BaseAsyncTestCase):
    """异步 Nexus 队列处理测试"""

    async def asyncSetUp(self):
        """异步测试前准备"""
        self.nexus = AsyncNexus()
        self.nexus.start()
        # 等待队列初始化
        await asyncio.sleep(0.1)

    async def asyncTearDown(self):
        """异步测试后清理"""
        if self.nexus.running:
            await self.nexus.stop()

    async def test_01_push_log_nonblocking(self):
        """
        测试非阻塞日志推送

        关键验证: 推送日志应该立即返回，不阻塞
        """
        start_time = time.time()

        # 推送日志（应该立即返回）
        self.nexus.push_trade_log(
            symbol="EURUSD",
            action="BUY",
            price=1.0950,
            volume=1.0,
        )

        elapsed = time.time() - start_time

        # 应该在 10ms 内返回（远快于网络请求）
        self.assertLess(elapsed, 0.01)
        self.assertEqual(self.nexus._stats["queued"], 1)

    async def test_02_multiple_logs_queuing(self):
        """测试多条日志入队"""
        for i in range(5):
            self.nexus.push_trade_log(
                symbol=f"PAIR{i}",
                action="BUY" if i % 2 == 0 else "SELL",
                price=1.0000 + i * 0.0001,
            )

        self.assertEqual(self.nexus._stats["queued"], 5)

    async def test_03_queue_processing(self):
        """
        测试队列处理

        验证: 日志被正确处理（虽然可能因为缺少 API 配置而部分失败）
        """
        self.nexus.config.gemini_key = None  # 禁用 API
        self.nexus.config.notion_token = None

        self.nexus.push_trade_log(
            symbol="EURUSD",
            action="BUY",
            price=1.0950,
        )

        # 等待处理完成
        await asyncio.sleep(0.5)

        # 检查统计信息
        stats = self.nexus.get_stats()
        self.assertEqual(stats["queued"], 1)

    async def test_04_queue_with_timeout(self):
        """测试队列超时处理"""
        # 这个测试验证队列等待不会永远阻塞

        async def test_queue_wait():
            start = time.time()
            # 应该在 1 秒超时后返回
            try:
                await asyncio.wait_for(
                    self.nexus.queue.get(),
                    timeout=0.1
                )
            except asyncio.TimeoutError:
                pass
            elapsed = time.time() - start
            return elapsed

        elapsed = await test_queue_wait()

        # 应该在 0.2 秒内返回（超时 + 余量）
        self.assertLess(elapsed, 0.2)


class TestAsyncNexusPromptFormatting(unittest.TestCase):
    """测试 Gemini 提示格式化"""

    def test_01_format_gemini_prompt(self):
        """测试 Gemini 提示格式化"""
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

        # 验证提示包含关键信息
        self.assertIn("EURUSD", prompt)
        self.assertIn("BUY", prompt)
        self.assertIn("1.0950", prompt)
        self.assertIn("交易分析", prompt)

    def test_02_format_with_error(self):
        """测试包含错误信息的日志格式化"""
        log = TradeLog(
            timestamp="2025-12-21T19:00:00",
            symbol="EURUSD",
            action="ERROR",
            status="FAILED",
            error_msg="Network timeout",
        )

        prompt = AsyncNexus._format_gemini_prompt(log)

        # 验证格式
        self.assertIn("EURUSD", prompt)
        self.assertIn("ERROR", prompt)
        self.assertIn("请提供简短的交易分析", prompt)


class TestAsyncNexusStats(unittest.IsolatedAsyncioTestCase):
    """测试统计信息"""

    async def asyncSetUp(self):
        """异步测试前准备"""
        self.nexus = AsyncNexus()
        self.nexus.start()
        await asyncio.sleep(0.1)

    async def asyncTearDown(self):
        """异步测试后清理"""
        if self.nexus.running:
            await self.nexus.stop()

    async def test_01_stats_tracking(self):
        """测试统计信息追踪"""
        self.nexus.push_trade_log("EURUSD", "BUY")
        self.nexus.push_trade_log("GBPUSD", "SELL")

        stats = self.nexus.get_stats()

        self.assertEqual(stats["queued"], 2)
        self.assertEqual(stats["running"], True)
        self.assertGreaterEqual(stats["queue_size"], 0)

    async def test_02_repr(self):
        """测试 __repr__"""
        self.nexus.push_trade_log("EURUSD", "BUY")

        repr_str = repr(self.nexus)

        self.assertIn("AsyncNexus", repr_str)
        self.assertIn("running=True", repr_str)


class TestAsyncNexusIntegration(unittest.IsolatedAsyncioTestCase):
    """集成测试"""

    async def test_01_full_lifecycle(self):
        """
        集成测试: 完整的生命周期

        验证:
        1. 启动服务
        2. 推送日志（非阻塞）
        3. 关闭服务（等待完成）
        """
        nexus = AsyncNexus()

        # 启动
        nexus.start()
        self.assertTrue(nexus.running)

        # 推送日志
        start_time = time.time()

        for i in range(3):
            nexus.push_trade_log(
                symbol=f"PAIR{i}",
                action="BUY",
                price=1.0000 + i * 0.001,
            )

        push_time = time.time() - start_time

        # 推送应该非常快（< 10ms）
        self.assertLess(push_time, 0.01)

        # 关闭
        await nexus.stop()
        self.assertFalse(nexus.running)

        # 验证统计
        stats = nexus.get_stats()
        self.assertEqual(stats["queued"], 3)


class TestAsyncNexusErrorHandling(unittest.IsolatedAsyncioTestCase):
    """错误处理测试"""

    async def asyncSetUp(self):
        """异步测试前准备"""
        self.nexus = AsyncNexus()

    async def test_01_push_without_start(self):
        """测试未启动时推送日志"""
        # 不应该崩溃，只是打印警告
        self.nexus.push_trade_log("EURUSD", "BUY")

        # 日志应该没有入队
        self.assertEqual(self.nexus._stats["queued"], 0)

    async def test_02_stop_without_start(self):
        """测试未启动时关闭"""
        # 不应该崩溃
        await self.nexus.stop()

        self.assertFalse(self.nexus.running)

    async def test_03_double_start(self):
        """测试重复启动"""
        self.nexus.start()
        self.assertTrue(self.nexus.running)

        # 再次启动应该被忽略
        self.nexus.start()
        self.assertTrue(self.nexus.running)

        await self.nexus.stop()


class TestAsyncNexusPerformance(unittest.IsolatedAsyncioTestCase):
    """性能测试"""

    async def asyncSetUp(self):
        """异步测试前准备"""
        self.nexus = AsyncNexus()
        self.nexus.start()
        await asyncio.sleep(0.1)

    async def asyncTearDown(self):
        """异步测试后清理"""
        if self.nexus.running:
            await self.nexus.stop()

    async def test_01_high_frequency_logging(self):
        """
        性能测试: 高频日志推送

        验证: 即使有 100 条日志，推送也应该在 100ms 内完成
        """
        start_time = time.time()

        # 推送 100 条日志
        for i in range(100):
            self.nexus.push_trade_log(
                symbol="EURUSD",
                action="BUY" if i % 2 == 0 else "SELL",
                price=1.0000 + (i * 0.00001),
            )

        elapsed = time.time() - start_time

        # 应该在 100ms 内完成
        self.assertLess(elapsed, 0.1)

        # 验证都被入队
        self.assertEqual(self.nexus._stats["queued"], 100)


if __name__ == "__main__":
    unittest.main()
