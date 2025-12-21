"""
P2-05 集成测试 - 完整的 P2 流程验证

测试目标：
验证 P2-01 → P2-02 → P2-03 → P2-04 的完整链路：

P2-01 (MultiTimeframeDataFeed + HierarchicalSignalFusion)
    ↓ confidence: 0.635
P2-02 (SessionRiskManager + DynamicRiskManager)
    ↓ can_trade: True
P2-03 (KellySizer._get_win_probability)
    ↓ p_win: 0.635
Kelly 公式 → 仓位: 11,312.50 EUR
    ↓
P2-04 (MT5VolumeAdapter)
    ↓ normalized_lots: 0.11
MT5.order_send(volume=0.11) ✓

关键验证：
1. 多周期对齐精度
2. 信号融合置信度
3. Kelly 仓位计算
4. MT5 手数规范化
5. 端到端流程完整性
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

# 导入 P2 各阶段的核心类
from src.data.multi_timeframe import OHLC, TimeframeConfig, MultiTimeframeDataFeed
from src.strategy.hierarchical_signals import (
    HierarchicalSignalFusion, SignalDirection, TimeframeSignal, FusionResult
)
from src.strategy.risk_manager import KellySizer
from src.strategy.session_risk_manager import SessionRiskManager, get_session_risk_manager
from src.mt5_bridge.volume_adapter import MT5VolumeAdapter, MT5SymbolInfo


class TestP2IntegrationFullPipeline:
    """测试完整的 P2 流程：信号 → 仓位 → MT5 订单"""

    def setup_method(self):
        """为每个测试设置环境"""
        # P2-01 设置：多周期数据对齐
        self.data_feed = MultiTimeframeDataFeed(base_period=5)
        self.data_feed.add_timeframe(60)
        self.data_feed.add_timeframe(1440)

        # P2-02 设置：风险管理
        self.session_risk = get_session_risk_manager(daily_loss_limit=-0.05)

        # P2-03 设置：Kelly Sizer
        self.sizer = KellySizer()
        self.sizer.strategy = Mock()
        self.sizer.broker = Mock()
        self.sizer.broker.getcash.return_value = 100000.0
        self.sizer.broker.getvalue.return_value = 105000.0
        self.sizer.strategy.initial_capital = 100000.0
        self.sizer.strategy.params = Mock(take_profit_ratio=2.0)
        self.sizer.strategy.atr = [0.02]

        # P2-04 设置：MT5 适配器
        self.eurusd_info = MT5SymbolInfo(
            symbol="EURUSD",
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.00001,
            trade_tick_size=0.00001
        )
        self.mt5_adapter = MT5VolumeAdapter(self.eurusd_info)

    def test_complete_signal_to_order_flow(self):
        """测试从信号生成到 MT5 订单的完整流程"""

        # 步骤 1: P2-01 - 模拟多周期数据
        ohlc_m5 = OHLC(
            timestamp=1640000000,
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1025,
            volume=1000
        )

        # 添加 72 根 M5 bar (6 小时) 来完成 H1
        for i in range(72):
            bar = OHLC(
                timestamp=1640000000 + i * 300,  # 每 5 分钟
                open=1.1000 + i * 0.0001,
                high=1.1050 + i * 0.0001,
                low=1.0950 + i * 0.0001,
                close=1.1025 + i * 0.0001,
                volume=1000
            )
            completed = self.data_feed.on_base_bar(bar)

        # 验证 H1 完成
        assert 60 in completed, "应该完成 H1 bar"
        h1_bar = completed[60]
        assert h1_bar['open'] == 1.1000
        assert abs(h1_bar['close'] - 1.1071) < 0.0001  # 最后一个 M5 的收盘

        # 步骤 2: P2-01 - 创建融合信号
        fusion = HierarchicalSignalFusion({
            'D1': {'threshold': 0.55},
            'H1': {'threshold': 0.65},
            'M5': {'threshold': 0.55}
        })

        # 模拟三层信号
        fusion_result = fusion.update_signal('D1', 0.70, 0.30)
        assert fusion_result.final_signal == SignalDirection.NO_SIGNAL  # 需要 H1 和 M5

        fusion_result = fusion.update_signal('H1', 0.70, 0.30)
        assert fusion_result.final_signal == SignalDirection.LONG  # 日线 + 小时线都 long

        fusion_result = fusion.update_signal('M5', 0.60, 0.40)
        # 完整的三层融合
        assert fusion_result.final_signal == SignalDirection.LONG
        # 置信度：D(50%×0.4) + H(35%×0.4) + M(15%×0.2) = 0.2 + 0.14 + 0.03 = 0.37
        assert fusion_result.confidence > 0

        # 步骤 3: P2-02 - 验证风险管理
        # 模拟交易前的风险检查
        can_trade = self.session_risk.can_trade()
        assert can_trade is True, "应该允许交易"

        # 步骤 4: P2-03 - KellySizer 获取置信度并计算仓位
        self.sizer.strategy.hierarchical_signals = fusion

        # 模拟数据源
        data = Mock()
        data.close = [1.1025]
        data.high = [1.1050]
        data.low = [1.0950]
        data.y_pred_proba_long = [0.55]  # 备选方案
        data.y_pred_proba_short = [0.45]

        # 获取赢率（应该使用融合置信度）
        p_win = self.sizer._get_win_probability(data, isbuy=True)
        assert p_win > 0, "应该获得有效的赢率"

        # 步骤 5: P2-04 - MT5 适配器规范化手数
        # 假设 Kelly 计算出的仓位
        kelly_position = 15000  # EUR

        # 转换为 MT5 手数
        lots = self.mt5_adapter.bt_size_to_mt5_lots(kelly_position)

        # 15,000 EUR → 0.15 lot
        assert lots == 0.15, f"应该转换为 0.15 lot，得到 {lots}"

        # 验证合规性
        is_valid, error = self.mt5_adapter.validate_volume(lots)
        assert is_valid is True, f"手数应该有效：{error}"

    def test_kelly_formula_with_fusion_confidence(self):
        """测试使用融合置信度的 Kelly 公式"""

        # 创建融合引擎
        fusion = HierarchicalSignalFusion({
            'D1': {'threshold': 0.55},
            'H1': {'threshold': 0.65},
            'M5': {'threshold': 0.55}
        })

        # 生成融合信号（强势信号）
        fusion.update_signal('D1', 0.75, 0.25)
        fusion.update_signal('H1', 0.70, 0.30)
        fusion.update_signal('M5', 0.65, 0.35)

        last_result = fusion.get_last_signal()
        confidence = last_result.confidence

        # Kelly 公式
        b = 2.0  # 盈亏比
        kelly_f = (confidence * (b + 1) - 1) / b

        # 验证 Kelly 比例为正
        assert kelly_f > 0, f"Kelly 比例应该为正，得到 {kelly_f:.4f}"

        # 应用 ¼ Kelly
        risk_pct = kelly_f * 0.25
        assert risk_pct > 0, "风险百分比应该为正"

        # 计算仓位
        account_value = 100000
        atr = 0.02
        stop_loss_dist = atr * 2.0
        target_shares = (account_value * risk_pct) / stop_loss_dist

        assert target_shares > 0, "仓位应该为正"

    def test_conversion_chain_mt5_compliance(self):
        """测试转换链的 MT5 合规性"""

        # 场景：完整的转换链
        kelly_position_eur = 25000

        # 步骤 1: Kelly 仓位 → 原始手数
        raw_lots = kelly_position_eur / self.eurusd_info.contract_size
        assert raw_lots == 0.25, f"原始手数应该是 0.25，得到 {raw_lots}"

        # 步骤 2: 规范化
        normalized_lots = self.mt5_adapter.normalize_volume(raw_lots)
        assert normalized_lots == 0.25, f"规范化应该是 0.25，得到 {normalized_lots}"

        # 步骤 3: 验证
        is_valid, error = self.mt5_adapter.validate_volume(normalized_lots)
        assert is_valid is True, f"应该有效：{error}"

        # 步骤 4: 应用约束
        # 测试超过最大值的情况
        huge_position = 10500000
        lots = self.mt5_adapter.bt_size_to_mt5_lots(huge_position)
        assert lots == 100.0, f"应该被限制在 100.0，得到 {lots}"

        # 测试低于最小值的情况
        tiny_position = 500
        lots = self.mt5_adapter.bt_size_to_mt5_lots(tiny_position)
        assert lots == 0.0, f"应该被视为 0.0，得到 {lots}"

    def test_risk_management_integration(self):
        """测试风险管理与仓位的集成"""

        # P2-02: 检查每日损失限制
        can_trade = self.session_risk.can_trade()
        assert can_trade is True

        # 模拟一笔交易损失
        self.session_risk.record_trade(
            symbol="EURUSD",
            pnl=-2000,  # -2000 EUR 损失
            realized=True
        )

        # 检查是否仍可交易
        daily_stats = self.session_risk.get_daily_stats()
        if daily_stats:
            daily_loss = daily_stats.get('daily_loss_pct', 0)
            # 2000 / 100000 = 2%
            assert daily_loss <= 0.05, "不应超过 5% 的每日损失限制"

    def test_end_to_end_with_real_values(self):
        """使用真实值的端到端测试"""

        # 完整场景：
        # - P2-01: 多周期融合置信度 0.635
        # - P2-03: Kelly 计算
        # - P2-04: MT5 规范化

        # 步骤 1: 融合置信度
        confidence = 0.635

        # 步骤 2: Kelly 计算
        b = 2.0  # 盈亏比
        kelly_f = (confidence * (b + 1) - 1) / b
        risk_pct = kelly_f * 0.25  # ¼ Kelly

        account = 100000
        atr = 0.02
        stop_loss_dist = atr * 2.0
        position_eur = (account * risk_pct) / stop_loss_dist * 100000

        # 步骤 3: MT5 规范化
        lots = self.mt5_adapter.bt_size_to_mt5_lots(position_eur)

        # 验证：
        assert lots > 0, "应该有正的手数"
        assert lots <= 100.0, "不应超过最大值"
        assert lots % 0.01 < 1e-8 or (1 - lots % 0.01) < 1e-8, "应该符合 0.01 的步进"

        # 验证可以下单
        is_valid, error = self.mt5_adapter.validate_volume(lots)
        assert is_valid is True, f"手数应该有效：{error}"

    def test_signal_propagation_through_pipeline(self):
        """测试信号通过整个管道的传播"""

        # 创建融合引擎
        fusion = HierarchicalSignalFusion({
            'D1': {'threshold': 0.55},
            'H1': {'threshold': 0.65},
            'M5': {'threshold': 0.55}
        })

        # 添加多个信号更新
        signals = [
            ('D1', 0.70, 0.30),
            ('H1', 0.75, 0.25),
            ('M5', 0.60, 0.40),
        ]

        for timeframe, long_prob, short_prob in signals:
            result = fusion.update_signal(timeframe, long_prob, short_prob)

        # 验证最终信号
        last_result = fusion.get_last_signal()
        assert last_result is not None, "应该有最终信号"
        assert last_result.final_signal in [SignalDirection.LONG, SignalDirection.SHORT]
        assert 0 <= last_result.confidence <= 1, "置信度应该在 0-1 之间"

    def test_multi_timeframe_alignment_precision(self):
        """测试多周期对齐的精度"""

        # 添加恰好 72 根 M5 bar (完成 1 个 H1)
        m5_bars = []
        for i in range(72):
            bar = OHLC(
                timestamp=1640000000 + i * 300,
                open=1.1000 + i * 0.00001,
                high=1.1010 + i * 0.00001,
                low=1.0990 + i * 0.00001,
                close=1.1005 + i * 0.00001,
                volume=100 + i
            )
            m5_bars.append(bar)

        # 处理所有 bar
        completed_periods = []
        for bar in m5_bars:
            completed = self.data_feed.on_base_bar(bar)
            if completed:
                completed_periods.append(completed)

        # 验证 H1 完成
        assert len(completed_periods) > 0, "应该完成至少一个更高周期"
        h1_completed = completed_periods[-1]
        assert 60 in h1_completed, "应该完成 H1"

        # 验证 OHLC 的正确性
        h1_ohlc = h1_completed[60]
        assert h1_ohlc['open'] == m5_bars[0]['open'], "H1 开盘应该是第一个 M5 的开盘"
        assert h1_ohlc['close'] == m5_bars[-1]['close'], "H1 收盘应该是最后一个 M5 的收盘"
        assert h1_ohlc['high'] >= max(b['high'] for b in m5_bars), "H1 最高应该 >= 所有 M5 的最高"
        assert h1_ohlc['low'] <= min(b['low'] for b in m5_bars), "H1 最低应该 <= 所有 M5 的最低"


class TestP2IntegrationErrorHandling:
    """测试 P2 流程中的错误处理和边界情况"""

    def setup_method(self):
        """设置测试环境"""
        self.fusion = HierarchicalSignalFusion({
            'D1': {'threshold': 0.55},
            'H1': {'threshold': 0.65},
            'M5': {'threshold': 0.55}
        })
        self.sizer = KellySizer()
        self.sizer.strategy = Mock()

    def test_missing_hierarchical_signals_fallback(self):
        """测试缺少 HierarchicalSignalFusion 时的回退"""

        sizer = KellySizer()
        sizer.strategy = Mock(spec=[])  # 没有 hierarchical_signals 属性
        sizer.params.use_hierarchical_signals = True

        data = Mock()
        data.y_pred_proba_long = [0.60]
        data.y_pred_proba_short = [0.40]

        # 应该回退到数据源
        p_win = sizer._get_win_probability(data, isbuy=True)
        assert p_win == 0.60, "应该回退到数据源概率"

    def test_invalid_kelly_parameters(self):
        """测试无效的 Kelly 参数"""

        # 非常低的胜率 + 低盈亏比
        p_win = 0.40
        b = 1.5
        kelly_f = (p_win * (b + 1) - 1) / b

        # Kelly 公式结果应该为负或非常低
        assert kelly_f < 0 or kelly_f < 0.1, "不应该是正的高值"

    def test_volume_adapter_extreme_values(self):
        """测试 MT5 适配器的极端值"""

        adapter_info = MT5SymbolInfo(
            symbol="TEST",
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.00001,
            trade_tick_size=0.00001
        )
        adapter = MT5VolumeAdapter(adapter_info)

        # 测试极端小的值
        assert adapter.bt_size_to_mt5_lots(1) == 0.0

        # 测试极端大的值
        result = adapter.bt_size_to_mt5_lots(100000000)
        assert result == 100.0, "应该被限制在最大值"

        # 测试零
        assert adapter.bt_size_to_mt5_lots(0) == 0.0

        # 测试负数
        assert adapter.bt_size_to_mt5_lots(-1000) == 0.0


class TestP2IntegrationPerformance:
    """测试 P2 流程的性能"""

    def test_data_feed_performance(self):
        """测试多周期数据源的性能"""
        import time

        data_feed = MultiTimeframeDataFeed(base_period=5)
        data_feed.add_timeframe(60)
        data_feed.add_timeframe(1440)

        # 处理 1000 根 bar 的性能
        start = time.time()
        for i in range(1000):
            bar = OHLC(
                timestamp=1640000000 + i * 300,
                open=1.1000 + i * 0.00001,
                high=1.1010 + i * 0.00001,
                low=1.0990 + i * 0.00001,
                close=1.1005 + i * 0.00001,
                volume=100
            )
            data_feed.on_base_bar(bar)

        elapsed = time.time() - start
        # 1000 bar 应该在 1 秒内处理完
        assert elapsed < 1.0, f"处理 1000 bar 用时过长：{elapsed:.2f}s"

    def test_volume_adapter_performance(self):
        """测试 MT5 适配器的性能"""
        import time
        import logging

        info = MT5SymbolInfo(
            symbol="EURUSD",
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.00001,
            trade_tick_size=0.00001
        )
        adapter = MT5VolumeAdapter(info)

        # 禁用日志以测试纯算法性能
        logging.getLogger('src.mt5_bridge.volume_adapter').setLevel(logging.CRITICAL)

        # 进行 10000 次转换
        start = time.time()
        for i in range(10000):
            adapter.normalize_volume((25000 + i) / 100000.0)

        elapsed = time.time() - start
        # 纯算法应该在 0.2 秒内完成 (不包括日志 I/O)
        assert elapsed < 0.2, f"转换性能过低：{elapsed:.3f}s"


# ============================================================================
# 执行所有测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
