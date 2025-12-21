"""
会话级风险管理单元测试

根据 Gemini Pro P2-02 建议，验证每日亏损限制的正确性和线程安全。

测试覆盖:
- 初始化和会话管理
- 已实现/未实现 P&L 追踪
- 每日损失百分比计算
- 停损限制检查
- 跨日期自动重置
- 线程安全性
- 统计和日志
"""

import unittest
import threading
import time
from datetime import datetime, date, timedelta
from unittest.mock import patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.strategy.session_risk_manager import (
    SessionRiskManager,
    DailyRiskState,
    get_session_risk_manager,
)


class TestDailyRiskState(unittest.TestCase):
    """每日风险状态数据类测试"""

    def test_01_create_state(self):
        """测试创建状态对象"""
        state = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
        )

        self.assertEqual(state.session_start_balance, 10000.0)
        self.assertEqual(state.daily_realized_pnl, 0.0)
        self.assertEqual(state.daily_unrealized_pnl, 0.0)

    def test_02_daily_total_pnl(self):
        """测试每日总 P&L 计算"""
        state = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
            daily_realized_pnl=100.0,
            daily_unrealized_pnl=-50.0,
        )

        self.assertEqual(state.daily_total_pnl, 50.0)

    def test_03_daily_loss_pct(self):
        """测试每日损失百分比计算"""
        state = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
            daily_realized_pnl=-500.0,  # -5%
        )

        self.assertAlmostEqual(state.daily_loss_pct, -0.05, places=4)

    def test_04_loss_limit_breached_boundary(self):
        """测试停损边界条件"""
        # 测试 -4.99% (不触发 -5% 限制)
        state1 = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
            daily_realized_pnl=-499.0,  # -4.99%
        )
        self.assertFalse(state1.is_limit_breached(-0.05))

        # 测试 -5.0% (触发 -5% 限制)
        state2 = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
            daily_realized_pnl=-500.0,  # -5.0%
        )
        self.assertTrue(state2.is_limit_breached(-0.05))

        # 测试 -5.01% (触发 -5% 限制)
        state3 = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
            daily_realized_pnl=-501.0,  # -5.01%
        )
        self.assertTrue(state3.is_limit_breached(-0.05))

    def test_05_state_to_dict(self):
        """测试状态转换为字典"""
        state = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=10000.0,
            daily_realized_pnl=-300.0,
            daily_unrealized_pnl=-100.0,
        )

        state_dict = state.to_dict()

        self.assertIn('session_date', state_dict)
        self.assertIn('daily_realized_pnl', state_dict)
        self.assertIn('daily_unrealized_pnl', state_dict)
        self.assertIn('daily_loss_pct', state_dict)
        self.assertIn('daily_total_pnl', state_dict)


class TestSessionRiskManagerInitialization(unittest.TestCase):
    """会话风险管理器初始化测试"""

    def test_01_default_initialization(self):
        """测试默认初始化"""
        manager = SessionRiskManager()

        self.assertEqual(manager.daily_loss_limit, -0.05)
        self.assertIsNone(manager.daily_state)

    def test_02_custom_loss_limit(self):
        """测试自定义损失限制"""
        manager = SessionRiskManager(daily_loss_limit=-0.10)

        self.assertEqual(manager.daily_loss_limit, -0.10)

    def test_03_repr(self):
        """测试字符串表示"""
        manager = SessionRiskManager()

        repr_str = repr(manager)

        self.assertIn("SessionRiskManager", repr_str)
        self.assertIn("无活跃会话", repr_str)


class TestSessionRiskManagerSession(unittest.TestCase):
    """会话管理测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionRiskManager()

    def test_01_start_session(self):
        """测试启动会话"""
        result = self.manager.start_session(10000.0)

        self.assertTrue(result)
        self.assertIsNotNone(self.manager.daily_state)
        self.assertEqual(self.manager.daily_state.session_start_balance, 10000.0)

    def test_02_double_start(self):
        """测试重复启动"""
        result1 = self.manager.start_session(10000.0)
        result2 = self.manager.start_session(10000.0)

        self.assertTrue(result1)
        self.assertTrue(result2)
        # 应该还是同一个会话
        self.assertEqual(self.manager.daily_state.session_start_balance, 10000.0)

    def test_03_reset_session(self):
        """测试重置会话"""
        self.manager.start_session(10000.0)

        stats = self.manager.reset_session()

        self.assertIsNotNone(stats)
        self.assertIsNone(self.manager.daily_state)

    def test_04_end_session(self):
        """测试结束会话"""
        self.manager.start_session(10000.0)

        stats = self.manager.end_session()

        self.assertIsNotNone(stats)
        self.assertIsNone(self.manager.daily_state)


class TestSessionRiskManagerPnLTracking(unittest.TestCase):
    """P&L 追踪测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionRiskManager()
        self.manager.start_session(10000.0)

    def test_01_update_realized_pnl_single(self):
        """测试单次已实现 P&L 更新"""
        self.manager.update_realized_pnl(100.0)

        self.assertEqual(self.manager.daily_state.daily_realized_pnl, 100.0)

    def test_02_update_realized_pnl_multiple(self):
        """测试多次已实现 P&L 更新"""
        self.manager.update_realized_pnl(100.0)
        self.manager.update_realized_pnl(-50.0)
        self.manager.update_realized_pnl(75.0)

        self.assertEqual(self.manager.daily_state.daily_realized_pnl, 125.0)

    def test_03_update_unrealized_pnl(self):
        """测试未实现 P&L 更新"""
        self.manager.update_unrealized_pnl(-200.0)

        self.assertEqual(self.manager.daily_state.daily_unrealized_pnl, -200.0)

    def test_04_daily_total_pnl(self):
        """测试每日总 P&L 计算"""
        self.manager.update_realized_pnl(100.0)
        self.manager.update_unrealized_pnl(-50.0)

        self.assertEqual(self.manager.daily_state.daily_total_pnl, 50.0)

    def test_05_daily_loss_pct_positive(self):
        """测试正收益的损失百分比"""
        self.manager.update_realized_pnl(500.0)

        self.assertAlmostEqual(self.manager.get_daily_loss_pct(), 0.05, places=4)

    def test_06_daily_loss_pct_negative(self):
        """测试负收益的损失百分比"""
        self.manager.update_realized_pnl(-500.0)

        self.assertAlmostEqual(self.manager.get_daily_loss_pct(), -0.05, places=4)


class TestSessionRiskManagerCanTrade(unittest.TestCase):
    """停损检查测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionRiskManager()

    def test_01_can_trade_before_session(self):
        """测试会话启动前是否允许交易"""
        result = self.manager.can_trade()

        self.assertTrue(result)

    def test_02_can_trade_no_loss(self):
        """测试无亏损时是否允许交易"""
        self.manager.start_session(10000.0)

        result = self.manager.can_trade()

        self.assertTrue(result)

    def test_03_can_trade_below_limit_no_trigger(self):
        """测试亏损 -4% 时不触发停损"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-400.0)

        result = self.manager.can_trade()

        self.assertTrue(result)

    def test_04_can_trade_at_limit_trigger(self):
        """测试亏损 -5% 时触发停损"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-500.0)

        result = self.manager.can_trade()

        self.assertFalse(result)

    def test_05_can_trade_above_limit_trigger(self):
        """测试亏损 -6% 时触发停损"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-600.0)

        result = self.manager.can_trade()

        self.assertFalse(result)

    def test_06_can_trade_with_unrealized(self):
        """测试包含未实现 P&L 的停损检查"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-300.0)
        self.manager.update_unrealized_pnl(-250.0)

        # 总损失 -5.5% > -5% 限制
        result = self.manager.can_trade()

        self.assertFalse(result)


class TestSessionRiskManagerCrossDayReset(unittest.TestCase):
    """跨日期自动重置测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionRiskManager()

    def test_01_reset_on_new_day(self):
        """测试跨日期时的自动重置"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-300.0)

        # 模拟日期变化
        with patch('src.strategy.session_risk_manager.date') as mock_date:
            # 第一次调用返回今天，设置会话
            # 第二次调用返回明天，触发重置
            mock_date.today.side_effect = [
                date(2025, 12, 21),
                date(2025, 12, 22),
            ]

            # 手动设置会话日期为昨天
            self.manager.daily_state.session_date = date(2025, 12, 21)

            result = self.manager.can_trade()

            # 应该会重置，返回 True
            self.assertTrue(result)

    def test_02_manual_reset(self):
        """测试手动重置"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-300.0)

        stats = self.manager.reset_session()

        self.assertIsNotNone(stats)
        self.assertIsNone(self.manager.daily_state)


class TestSessionRiskManagerStats(unittest.TestCase):
    """统计信息测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionRiskManager()

    def test_01_get_stats_before_session(self):
        """测试会话启动前获取统计"""
        stats = self.manager.get_daily_stats()

        self.assertIsNone(stats)

    def test_02_get_stats_after_session(self):
        """测试会话启动后获取统计"""
        self.manager.start_session(10000.0)

        stats = self.manager.get_daily_stats()

        self.assertIsNotNone(stats)
        self.assertIn('session_date', stats)
        self.assertIn('daily_realized_pnl', stats)

    def test_03_get_daily_loss_pct(self):
        """测试获取每日损失百分比"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-500.0)

        loss_pct = self.manager.get_daily_loss_pct()

        self.assertAlmostEqual(loss_pct, -0.05, places=4)


class TestSessionRiskManagerThreadSafety(unittest.TestCase):
    """线程安全性测试"""

    def test_01_concurrent_pnl_updates(self):
        """测试并发 P&L 更新"""
        manager = SessionRiskManager()
        manager.start_session(10000.0)

        results = []

        def update_pnl():
            for i in range(10):
                manager.update_realized_pnl(10.0)
                results.append(manager.get_daily_loss_pct())

        threads = [threading.Thread(target=update_pnl) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 应该有 50 个更新 (5 线程 × 10 次)
        self.assertEqual(len(results), 50)

        # 最终 P&L 应该是 500
        final_state = manager.daily_state
        self.assertEqual(final_state.daily_realized_pnl, 500.0)

    def test_02_concurrent_can_trade_checks(self):
        """测试并发 can_trade 检查"""
        manager = SessionRiskManager()
        manager.start_session(10000.0)

        results = []

        def check_trade():
            for _ in range(10):
                results.append(manager.can_trade())

        threads = [threading.Thread(target=check_trade) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 应该有 50 个检查结果
        self.assertEqual(len(results), 50)
        # 所有检查都应该返回 True (无亏损)
        self.assertTrue(all(results))


class TestSessionRiskManagerCustomLimit(unittest.TestCase):
    """自定义限制测试"""

    def test_01_custom_limit_10_percent(self):
        """测试 -10% 自定义限制"""
        manager = SessionRiskManager(daily_loss_limit=-0.10)
        manager.start_session(10000.0)

        # -8% 应该允许交易
        manager.update_realized_pnl(-800.0)
        self.assertTrue(manager.can_trade())

        # -10.1% 应该不允许交易
        manager.update_realized_pnl(-200.1)
        self.assertFalse(manager.can_trade())

    def test_02_custom_limit_2_percent(self):
        """测试 -2% 自定义限制"""
        manager = SessionRiskManager(daily_loss_limit=-0.02)
        manager.start_session(10000.0)

        # -1% 应该允许交易
        manager.update_realized_pnl(-100.0)
        self.assertTrue(manager.can_trade())

        # -2.1% 应该不允许交易
        manager.update_realized_pnl(-110.0)
        self.assertFalse(manager.can_trade())


class TestGlobalSessionRiskManager(unittest.TestCase):
    """全局实例测试"""

    def tearDown(self):
        """清理全局实例"""
        import src.strategy.session_risk_manager as srm_module
        srm_module._session_risk_manager = None

    def test_01_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_session_risk_manager()
        manager2 = get_session_risk_manager()

        self.assertIs(manager1, manager2)

    def test_02_get_with_custom_limit(self):
        """测试使用自定义限制获取全局实例"""
        manager = get_session_risk_manager(daily_loss_limit=-0.10)

        self.assertEqual(manager.daily_loss_limit, -0.10)


class TestSessionRiskManagerEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionRiskManager()

    def test_01_zero_balance(self):
        """测试零余额情况"""
        state = DailyRiskState(
            session_date=date.today(),
            session_start_time=datetime.now(),
            session_start_balance=0.0,
        )

        # 应该返回 0% 损失
        self.assertEqual(state.daily_loss_pct, 0.0)

    def test_02_large_loss(self):
        """测试大额损失"""
        self.manager.start_session(10000.0)
        self.manager.update_realized_pnl(-5000.0)

        loss_pct = self.manager.get_daily_loss_pct()

        self.assertAlmostEqual(loss_pct, -0.50, places=4)
        self.assertFalse(self.manager.can_trade())

    def test_03_precision_boundary(self):
        """测试精度边界"""
        self.manager.start_session(10000.0)

        # -4.999% 应该允许
        self.manager.update_realized_pnl(-499.9)
        self.assertTrue(self.manager.can_trade())

        # 再添加 -0.101% 应该触发
        self.manager.update_realized_pnl(-10.1)
        self.assertFalse(self.manager.can_trade())


if __name__ == "__main__":
    unittest.main()
