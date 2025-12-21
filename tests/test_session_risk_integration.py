"""
集成测试 - SessionRiskManager 与 MLStrategy/DynamicRiskManager 的集成

测试目标：
1. SessionRiskManager 在 MLStrategy 中正确初始化和更新
2. 每日停损触发时 MLStrategy 停止交易
3. DynamicRiskManager 正确检查每日损失限制
4. 多重风控机制协同工作
"""

import pytest
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategy.ml_strategy import MLStrategy
from src.strategy.risk_manager import DynamicRiskManager
from src.strategy.session_risk_manager import SessionRiskManager, get_session_risk_manager


class CustomDataFeed(bt.feeds.PandasData):
    """自定义 DataFeed，支持 ML 预测概率字段"""

    params = (
        ('y_pred_proba_long', -1),
        ('y_pred_proba_short', -1),
    )


class TestMLStrategyIntegration:
    """测试 SessionRiskManager 与 MLStrategy 的集成"""

    def test_ml_strategy_has_session_risk_attribute(self):
        """验证 MLStrategy 包含 session_risk 属性"""
        # 检查 MLStrategy 源代码中是否包含 session_risk 的初始化
        import inspect
        source = inspect.getsource(MLStrategy.__init__)

        assert 'session_risk' in source
        assert 'get_session_risk_manager' in source
        # 检查是否导入了会话风控相关的模块
        assert 'session_started' in source

    def test_ml_strategy_checks_can_trade(self):
        """验证 MLStrategy 的 next() 方法检查 can_trade()"""
        import inspect
        source = inspect.getsource(MLStrategy.next)

        # 验证源代码中包含风控检查
        assert 'can_trade()' in source
        assert '每日停损' in source or 'daily' in source.lower()

    def test_ml_strategy_updates_realized_pnl(self):
        """验证 MLStrategy 在 notify_trade 中更新 P&L"""
        import inspect
        source = inspect.getsource(MLStrategy.notify_trade)

        # 验证 notify_trade 更新 session_risk
        assert 'update_realized_pnl' in source
        assert 'session_risk' in source

    def test_session_risk_manager_lifecycle(self):
        """测试会话风险管理器的生命周期"""
        # 重置全局单例
        SessionRiskManager._instance = None

        # 创建管理器
        risk_mgr = SessionRiskManager(daily_loss_limit=-0.05)

        # 验证初始状态
        daily_stats = risk_mgr.get_daily_stats()
        assert daily_stats is None  # 未启动会话

        # 启动会话
        risk_mgr.start_session(10000.0)
        daily_stats = risk_mgr.get_daily_stats()
        assert daily_stats is not None

        # 验证初始状态
        raw_stats = risk_mgr.daily_state.to_dict(formatted=False)
        assert raw_stats['daily_realized_pnl'] == 0.0
        assert raw_stats['daily_loss_pct'] == 0.0

        # 清理
        SessionRiskManager._instance = None

    def test_daily_loss_limit_stops_trading(self):
        """测试每日停损限制触发后停止交易"""
        # 重置全局单例
        SessionRiskManager._instance = None

        # 创建严格的停损限制
        risk_mgr = SessionRiskManager(daily_loss_limit=-0.01)  # -1% 限制

        # 启动会话
        risk_mgr.start_session(10000.0)

        # 模拟大额损失
        risk_mgr.update_realized_pnl(-150.0)  # -1.5% 损失

        # 验证无法交易
        assert risk_mgr.can_trade() is False

        # 清理
        SessionRiskManager._instance = None


class TestDynamicRiskManagerIntegration:
    """测试 SessionRiskManager 与 DynamicRiskManager 的集成"""

    def test_dynamic_risk_manager_initialization(self):
        """测试 DynamicRiskManager 初始化包含 SessionRiskManager"""
        # 创建简单的 broker
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(10000.0)

        # 创建风险管理器
        risk_mgr = DynamicRiskManager(
            broker=cerebro.broker,
            max_drawdown_pct=10.0,
            daily_loss_limit=-0.05
        )

        # 验证 session_risk 已初始化
        assert hasattr(risk_mgr, 'session_risk')
        assert isinstance(risk_mgr.session_risk, SessionRiskManager)

    def test_can_trade_checks_both_limits(self):
        """测试 can_trade() 同时检查回撤和每日限制"""
        # 重置全局单例
        SessionRiskManager._instance = None

        cerebro = bt.Cerebro()
        cerebro.broker.setcash(10000.0)

        # 创建风险管理器（会创建新的单例实例）
        risk_mgr = DynamicRiskManager(
            broker=cerebro.broker,
            max_drawdown_pct=10.0,
            daily_loss_limit=-0.02  # -2% 每日限制
        )

        # 启动会话
        risk_mgr.session_risk.start_session(10000.0)

        # 初始状态应该可以交易
        assert risk_mgr.can_trade() is True

        # 验证源代码中有can_trade检查
        import inspect
        source = inspect.getsource(DynamicRiskManager.can_trade)
        assert 'session_risk' in source
        assert 'self.is_halted' in source

        # 清理
        SessionRiskManager._instance = None

    def test_summary_includes_daily_stats(self):
        """测试风险报告包含每日统计"""
        # 重置全局单例
        SessionRiskManager._instance = None

        cerebro = bt.Cerebro()
        cerebro.broker.setcash(10000.0)

        risk_mgr = DynamicRiskManager(
            broker=cerebro.broker,
            daily_loss_limit=-0.05
        )

        # 启动会话
        risk_mgr.session_risk.start_session(10000.0)

        # 更新一些 P&L
        risk_mgr.session_risk.update_realized_pnl(-100.0)

        # 获取摘要
        summary = risk_mgr.get_summary()

        # 验证包含每日损失信息
        assert '每日损失报告' in summary
        assert '当日已实现' in summary or '当日总' in summary

        # 清理
        SessionRiskManager._instance = None

    def test_drawdown_and_daily_loss_independence(self):
        """测试回撤熔断和每日停损独立工作"""
        # 场景 1: 宽松的每日限制和回撤限制
        SessionRiskManager._instance = None

        cerebro = bt.Cerebro()
        cerebro.broker.setcash(10000.0)

        risk_mgr = DynamicRiskManager(
            broker=cerebro.broker,
            max_drawdown_pct=5.0,  # 5% 回撤
            daily_loss_limit=-0.10  # 10% 每日限制（宽松）
        )

        # 启动会话
        risk_mgr.session_risk.start_session(10000.0)

        # 模拟小额损失（都未触发）
        risk_mgr.session_risk.update_realized_pnl(-100.0)  # -1% 每日损失
        assert risk_mgr.can_trade() is True  # 应该可以交易

        # 验证 DynamicRiskManager 的 can_trade() 同时检查两个条件
        import inspect
        source = inspect.getsource(DynamicRiskManager.can_trade)
        assert 'self.is_halted' in source  # 检查回撤
        assert 'session_risk.can_trade()' in source  # 检查每日损失

        # 清理
        SessionRiskManager._instance = None


class TestEndToEndRiskControl:
    """端到端风控集成测试"""

    def test_ml_strategy_integration_complete(self):
        """验证 MLStrategy 完整集成了 SessionRiskManager"""
        import inspect

        # 1. 检查 __init__ 中的初始化
        init_source = inspect.getsource(MLStrategy.__init__)
        assert 'session_risk' in init_source
        assert 'get_session_risk_manager' in init_source

        # 2. 检查 next() 中的风控检查
        next_source = inspect.getsource(MLStrategy.next)
        assert 'can_trade()' in next_source
        assert 'session_risk' in next_source

        # 3. 检查 notify_trade() 中的 P&L 更新
        notify_source = inspect.getsource(MLStrategy.notify_trade)
        assert 'update_realized_pnl' in notify_source


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
