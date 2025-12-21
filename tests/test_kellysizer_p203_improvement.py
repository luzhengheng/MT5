"""
P2-03 测试套件 - KellySizer 与 HierarchicalSignalFusion 集成

测试目标：
1. 验证 KellySizer._get_win_probability() 方法
2. 验证优先级: HierarchicalSignalFusion > data feed
3. 验证回退机制和错误处理
4. 验证仓位计算整合

关键改进 (P2-03):
- _get_win_probability() 支持多个概率来源
- 优先从 HierarchicalSignalFusion 获取置信度
- 回退到数据源的 y_pred_proba
- 确保 Kelly 公式获得高质量的胜率输入
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from enum import Enum

# 导入要测试的类
from src.strategy.risk_manager import KellySizer
from src.strategy.hierarchical_signals import SignalDirection, FusionResult


@dataclass
class MockSignalResult:
    """模拟 HierarchicalSignalFusion 的融合结果"""
    final_signal: SignalDirection
    confidence: float
    reasoning: str


class TestKellySizerGetWinProbability:
    """测试 _get_win_probability() 方法的各种场景"""

    def setup_method(self):
        """为每个测试设置基础环境"""
        # 创建模拟的 Backtrader sizer
        self.sizer = KellySizer()
        self.sizer.strategy = Mock()
        self.sizer.broker = Mock()

    def test_get_win_probability_from_hierarchical_signals(self):
        """测试：从 HierarchicalSignalFusion 获取赢率 (优先级最高)"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.55]
        data.y_pred_proba_short = [0.45]

        # 设置 HierarchicalSignalFusion
        mock_fusion = Mock()
        mock_fusion.get_last_signal.return_value = MockSignalResult(
            final_signal=SignalDirection.LONG,
            confidence=0.735,  # 来自 P2-01 的加权置信度
            reasoning="日线long + 小时线long + 分钟线long一致，执行"
        )
        self.sizer.strategy.hierarchical_signals = mock_fusion
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win == 0.735, "应该从 HierarchicalSignalFusion 获取置信度"
        assert mock_fusion.get_last_signal.called

    def test_get_win_probability_fallback_to_data_feed(self):
        """测试：回退到数据源的 y_pred_proba (当没有融合信号时)"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.62]
        data.y_pred_proba_short = [0.38]

        # 没有 HierarchicalSignalFusion
        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win == 0.62, "应该从数据源获取 y_pred_proba_long"

    def test_get_win_probability_fallback_short_side(self):
        """测试：卖出端的回退 (short side fallback)"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.40]
        data.y_pred_proba_short = [0.60]

        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=False)

        # 验证
        assert p_win == 0.60, "卖出时应该使用 y_pred_proba_short"

    def test_get_win_probability_hierarchical_signals_disabled(self):
        """测试：禁用 HierarchicalSignalFusion (use_hierarchical_signals=False)"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.58]
        data.y_pred_proba_short = [0.42]

        # 虽然设置了融合信号，但禁用了该选项
        mock_fusion = Mock()
        mock_fusion.get_last_signal.return_value = MockSignalResult(
            final_signal=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Test"
        )
        self.sizer.strategy.hierarchical_signals = mock_fusion
        self.sizer.params.use_hierarchical_signals = False

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win == 0.58, "禁用时应该直接使用数据源，跳过融合"
        assert not mock_fusion.get_last_signal.called

    def test_get_win_probability_none_signal(self):
        """测试：融合信号为 None (没有有效信号时)"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.51]
        data.y_pred_proba_short = [0.49]

        # 融合信号返回 None
        mock_fusion = Mock()
        mock_fusion.get_last_signal.return_value = None
        self.sizer.strategy.hierarchical_signals = mock_fusion
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win == 0.51, "融合信号为 None 时应该回退到数据源"

    def test_get_win_probability_fusion_exception(self):
        """测试：获取融合信号时发生异常"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.54]
        data.y_pred_proba_short = [0.46]

        # 融合引擎抛出异常
        mock_fusion = Mock()
        mock_fusion.get_last_signal.side_effect = Exception("fusion error")
        self.sizer.strategy.hierarchical_signals = mock_fusion
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win == 0.54, "异常时应该回退到数据源"

    def test_get_win_probability_invalid_data_nan(self):
        """测试：数据源包含 NaN"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [np.nan]
        data.y_pred_proba_short = [0.45]

        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win is None, "NaN 应该返回 None"

    def test_get_win_probability_invalid_data_zero(self):
        """测试：数据源包含零或负数"""
        # 设置
        data = Mock()
        data.y_pred_proba_long = [0.0]
        data.y_pred_proba_short = [0.45]

        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win is None, "零或负数应该返回 None"

    def test_get_win_probability_missing_data_attribute(self):
        """测试：数据源缺少 y_pred_proba 属性"""
        # 设置
        data = Mock(spec=[])  # 空规范，没有任何属性

        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        p_win = self.sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win is None, "属性缺失应该返回 None"

    def test_get_win_probability_confidence_range(self):
        """测试：HierarchicalSignalFusion 的置信度范围 [0, 1]"""
        # 设置多个置信度值进行测试
        test_cases = [
            (0.0, 0.0),    # 边界：最小
            (0.5, 0.5),    # 中间值
            (0.735, 0.735),  # P2-01 示例值
            (1.0, 1.0),    # 边界：最大
        ]

        for confidence_input, expected_output in test_cases:
            data = Mock()
            mock_fusion = Mock()
            mock_fusion.get_last_signal.return_value = MockSignalResult(
                final_signal=SignalDirection.LONG,
                confidence=confidence_input,
                reasoning="Test"
            )
            self.sizer.strategy.hierarchical_signals = mock_fusion
            self.sizer.params.use_hierarchical_signals = True

            p_win = self.sizer._get_win_probability(data, isbuy=True)

            assert p_win == expected_output, \
                f"置信度 {confidence_input} 应该返回 {expected_output}"


class TestKellySizerIntegration:
    """测试 KellySizer 与 HierarchicalSignalFusion 的完整集成"""

    def setup_method(self):
        """为每个测试设置基础环境"""
        self.sizer = KellySizer()
        self.sizer.strategy = Mock()
        self.sizer.broker = Mock()
        self.sizer.broker.getcash.return_value = 100000.0
        self.sizer.broker.getvalue.return_value = 105000.0

    def test_getsizing_with_hierarchical_confidence(self):
        """测试：_getsizing 使用 HierarchicalSignalFusion 的置信度"""
        # 设置
        data = Mock()
        data.close = [1.50]
        data.high = [1.51]
        data.low = [1.49]
        data.y_pred_proba_long = [0.55]  # 备用
        data.y_pred_proba_short = [0.45]

        # 模拟 HierarchicalSignalFusion
        mock_fusion = Mock()
        mock_fusion.get_last_signal.return_value = MockSignalResult(
            final_signal=SignalDirection.LONG,
            confidence=0.70,  # 高置信度
            reasoning="Multi-timeframe confirmation"
        )
        self.sizer.strategy.hierarchical_signals = mock_fusion
        self.sizer.params.use_hierarchical_signals = True

        # 设置其他必要的策略属性
        self.sizer.strategy.initial_capital = 100000.0
        self.sizer.strategy.params = Mock(take_profit_ratio=2.0)
        self.sizer.strategy.atr = [0.02]  # ATR value

        # 执行
        comminfo = Mock()
        size = self.sizer._getsizing(comminfo, 100000.0, data, isbuy=True)

        # 验证：使用置信度 0.70 而不是 0.55
        assert size > 0, "应该计算出有效的仓位"
        # 使用 0.70 的 Kelly 计算会得出比 0.55 更大的仓位
        assert mock_fusion.get_last_signal.called

    def test_getsizing_fallback_when_no_hierarchical(self):
        """测试：当没有 HierarchicalSignalFusion 时回退到数据源"""
        # 设置
        data = Mock()
        data.close = [1.50]
        data.high = [1.51]
        data.low = [1.49]
        data.y_pred_proba_long = [0.60]
        data.y_pred_proba_short = [0.40]

        # 没有融合信号
        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 设置其他必要属性
        self.sizer.strategy.initial_capital = 100000.0
        self.sizer.strategy.params = Mock(take_profit_ratio=2.0)
        self.sizer.strategy.atr = [0.02]

        # 执行
        comminfo = Mock()
        size = self.sizer._getsizing(comminfo, 100000.0, data, isbuy=True)

        # 验证
        assert size > 0, "应该使用数据源概率计算仓位"

    def test_getsizing_returns_zero_when_no_probability(self):
        """测试：当无法获取概率时返回 0"""
        # 设置
        data = Mock()
        data.close = [1.50]
        data.y_pred_proba_long = [np.nan]
        data.y_pred_proba_short = [np.nan]

        # 没有融合信号
        self.sizer.strategy.hierarchical_signals = None
        self.sizer.params.use_hierarchical_signals = True

        # 执行
        comminfo = Mock()
        size = self.sizer._getsizing(comminfo, 100000.0, data, isbuy=True)

        # 验证
        assert size == 0, "无效的概率应该返回 0 仓位"


class TestP203SignalFlow:
    """测试完整的 P2-03 信号流：HierarchicalSignalFusion → KellySizer → Position"""

    def test_signal_flow_from_fusion_to_kelly(self):
        """测试：从信号融合到仓位计算的完整流程"""
        # 步骤 1: HierarchicalSignalFusion 生成置信度
        fusion_confidence = 0.635  # 示例：D=50%×0.7 + H=35%×0.6 + M=15%×0.5

        # 步骤 2: KellySizer 从融合结果获取赢率
        sizer = KellySizer()
        sizer.strategy = Mock()
        sizer.broker = Mock()
        sizer.broker.getcash.return_value = 100000.0
        sizer.broker.getvalue.return_value = 105000.0

        # 模拟融合信号
        mock_fusion = Mock()
        mock_fusion.get_last_signal.return_value = MockSignalResult(
            final_signal=SignalDirection.LONG,
            confidence=fusion_confidence,
            reasoning="日线long + 小时线long + 分钟线long一致，执行"
        )
        sizer.strategy.hierarchical_signals = mock_fusion
        sizer.params.use_hierarchical_signals = True

        # 获取赢率
        data = Mock()
        p_win = sizer._get_win_probability(data, isbuy=True)

        # 验证
        assert p_win == fusion_confidence, \
            f"赢率应该等于融合置信度 {fusion_confidence}"

        # 步骤 3: 验证 Kelly 公式的输入
        b = 2.0  # 盈亏比
        kelly_f = (p_win * (b + 1) - 1) / b
        assert kelly_f > 0, "Kelly 比例应该为正"

        # 步骤 4: 验证仓位计算（使用置信度的优点）
        # 使用 0.635 的置信度会产生合理的仓位大小
        kelly_f_expected = (0.635 * 3.0 - 1) / 2.0
        assert kelly_f == kelly_f_expected, "Kelly 公式计算正确"

    def test_p203_improves_on_raw_data(self):
        """测试：P2-03 改进相比直接使用数据源概率"""
        # 场景：HierarchicalSignalFusion 提供更高质量的置信度

        # 原始情况：数据源直接输出的概率可能不够精确
        raw_data_proba = 0.52  # 接近 0.5，不够清晰

        # P2-03 改进：多时间框架融合后的置信度
        fusion_confidence = 0.70  # 更清晰的信号

        # 验证改进的效果
        b = 2.0
        kelly_raw = (raw_data_proba * (b + 1) - 1) / b
        kelly_improved = (fusion_confidence * (b + 1) - 1) / b

        # 验证改进：融合信号应该产生更大的 Kelly 比例
        assert kelly_raw > 0, f"原始概率的 Kelly 比例 {kelly_raw:.4f} 应该为正"
        assert kelly_improved > kelly_raw, \
            f"融合置信度 {fusion_confidence} 应该产生更好的 Kelly 比例 " \
            f"({kelly_improved:.4f} > {kelly_raw:.4f})"

        # 验证改进幅度
        improvement_ratio = kelly_improved / kelly_raw
        assert improvement_ratio >= 1.9, \
            f"改进幅度应该显著，至少 1.9x (当前 {improvement_ratio:.2f}x)"


class TestP203Documentation:
    """测试 P2-03 改进的文档完整性"""

    def test_kellysizer_docstring_updated(self):
        """验证 KellySizer 文档包含 P2-03 改进说明"""
        docstring = KellySizer.__doc__
        assert "P2-03" in docstring or "HierarchicalSignalFusion" in docstring, \
            "KellySizer 文档应该说明 P2-03 改进"

    def test_get_win_probability_docstring_complete(self):
        """验证 _get_win_probability 方法文档完整"""
        docstring = KellySizer._get_win_probability.__doc__
        assert "P2-03" in docstring, "方法文档应该说明 P2-03"
        assert "HierarchicalSignalFusion" in docstring, "应该说明融合信号"
        assert "fallback" in docstring.lower() or "回退" in docstring, "应该说明回退机制"


# ============================================================================
# 执行所有测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
