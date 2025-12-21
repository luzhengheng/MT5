"""分层信号融合测试"""

import pytest
from src.strategy.hierarchical_signals import (
    HierarchicalSignalFusion,
    TimeframeSignal,
    SignalDirection,
    SignalPriority,
    FusionResult,
)


class TestTimeframeSignal:
    """TimeframeSignal 单元测试"""

    def test_signal_creation(self):
        """测试创建信号"""
        signal = TimeframeSignal(
            timeframe='H',
            y_pred_proba_long=0.7,
            y_pred_proba_short=0.3,
        )
        assert signal.timeframe == 'H'
        assert signal.y_pred_proba_long == 0.7
        assert signal.y_pred_proba_short == 0.3

    def test_signal_strength(self):
        """测试信号强度计算"""
        signal = TimeframeSignal('H', 0.8, 0.2)
        assert signal.signal_strength == pytest.approx(0.3)  # 0.8 - 0.5

    def test_signal_direction_long(self):
        """测试看涨信号方向"""
        signal = TimeframeSignal('H', 0.75, 0.25)
        assert signal.direction == SignalDirection.LONG

    def test_signal_direction_short(self):
        """测试看跌信号方向"""
        signal = TimeframeSignal('H', 0.25, 0.75)
        assert signal.direction == SignalDirection.SHORT

    def test_signal_direction_no_signal(self):
        """测试无信号"""
        signal = TimeframeSignal('H', 0.5, 0.5)
        assert signal.direction == SignalDirection.NO_SIGNAL

    def test_signal_direction_weak_long(self):
        """测试弱看涨信号 (不足阈值)"""
        signal = TimeframeSignal('H', 0.52, 0.48)  # 差距小
        assert signal.direction == SignalDirection.NO_SIGNAL


class TestHierarchicalSignalFusion:
    """分层信号融合引擎测试"""

    def test_initialization(self):
        """测试初始化"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        assert fusion.periods == {'D': 1440, 'H': 60, 'M': 5}
        assert len(fusion.signals) == 0

    def test_unknown_timeframe(self):
        """测试未知周期"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        with pytest.raises(ValueError, match="未知周期"):
            fusion.update_signal('W', 0.7, 0.3)

    def test_daily_trend_missing(self):
        """测试日线信号缺失"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 只有小时线信号，无日线
        result = fusion.update_signal('H', 0.75, 0.25)

        assert result.final_signal == SignalDirection.NO_SIGNAL
        assert "日线信号缺失" in result.reasoning

    def test_daily_no_trend(self):
        """测试日线无趋势"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线信号不足阈值
        result = fusion.update_signal('D', 0.52, 0.48)

        assert result.final_signal == SignalDirection.NO_SIGNAL
        assert "日线无趋势确认" in result.reasoning

    def test_hourly_missing(self):
        """测试小时线缺失"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 只有日线信号
        result = fusion.update_signal('D', 0.75, 0.25)

        assert result.final_signal == SignalDirection.NO_SIGNAL
        assert result.daily_trend == SignalDirection.LONG
        assert "等待小时线入场信号" in result.reasoning

    def test_hourly_no_entry(self):
        """测试小时线无入场信号"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线看涨，小时线无信号
        fusion.update_signal('D', 0.75, 0.25)
        result = fusion.update_signal('H', 0.52, 0.48)

        assert result.final_signal == SignalDirection.NO_SIGNAL
        assert result.daily_trend == SignalDirection.LONG
        assert "小时线无入场信号" in result.reasoning

    def test_direction_conflict(self):
        """测试日线和小时线方向冲突"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线看涨，小时线看跌
        fusion.update_signal('D', 0.75, 0.25)
        result = fusion.update_signal('H', 0.25, 0.75)

        assert result.final_signal == SignalDirection.NO_TRADE
        assert result.daily_trend == SignalDirection.LONG
        assert result.hourly_entry == SignalDirection.SHORT
        assert "冲突，停止交易" in result.reasoning

    def test_valid_long_signal(self):
        """测试有效看涨信号"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线和小时线都看涨
        fusion.update_signal('D', 0.75, 0.25)
        result = fusion.update_signal('H', 0.70, 0.30)

        assert result.final_signal == SignalDirection.LONG
        assert result.daily_trend == SignalDirection.LONG
        assert result.hourly_entry == SignalDirection.LONG
        # 没有分钟线时，等待分钟线
        assert "等待分钟线" in result.reasoning

    def test_valid_short_signal(self):
        """测试有效看跌信号"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线和小时线都看跌
        fusion.update_signal('D', 0.25, 0.75)
        result = fusion.update_signal('H', 0.30, 0.70)

        assert result.final_signal == SignalDirection.SHORT
        assert result.daily_trend == SignalDirection.SHORT
        assert result.hourly_entry == SignalDirection.SHORT

    def test_minute_confirms(self):
        """测试分钟线确认"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线、小时线、分钟线都看涨
        fusion.update_signal('D', 0.75, 0.25)
        fusion.update_signal('H', 0.70, 0.30)
        result = fusion.update_signal('M', 0.65, 0.35)

        assert result.final_signal == SignalDirection.LONG
        assert result.minute_detail == SignalDirection.LONG
        assert "一致，执行" in result.reasoning

    def test_minute_disagrees_but_ok(self):
        """测试分钟线不一致但可接受"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线、小时线看涨，分钟线无信号
        fusion.update_signal('D', 0.75, 0.25)
        fusion.update_signal('H', 0.70, 0.30)
        result = fusion.update_signal('M', 0.52, 0.48)

        assert result.final_signal == SignalDirection.LONG
        assert result.minute_detail == SignalDirection.NO_SIGNAL
        assert "分钟线无信号，标准执行" in result.reasoning

    def test_minute_warns_disagreement(self):
        """测试分钟线弱化警告"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线、小时线看涨，分钟线看跌
        fusion.update_signal('D', 0.75, 0.25)
        fusion.update_signal('H', 0.70, 0.30)
        result = fusion.update_signal('M', 0.30, 0.70)

        # 分钟线看跌，小时线看涨，保守执行
        assert result.final_signal == SignalDirection.LONG
        assert result.minute_detail == SignalDirection.SHORT
        assert "保守执行" in result.reasoning


class TestSignalConfidence:
    """信号置信度测试"""

    def test_confidence_no_signal(self):
        """测试无信号置信度"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        result = fusion.update_signal('D', 0.5, 0.5)
        assert result.confidence == 0.0

    def test_confidence_conflict(self):
        """测试冲突信号置信度"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        fusion.update_signal('D', 0.75, 0.25)
        result = fusion.update_signal('H', 0.25, 0.75)
        assert result.confidence == 0.0  # 冲突信号

    def test_confidence_only_daily(self):
        """测试仅有日线的置信度"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        result = fusion.update_signal('D', 0.8, 0.2)
        # 只有日线没有小时线，信号不成立，置信度为 0
        assert result.confidence == 0.0

    def test_confidence_daily_and_hourly(self):
        """测试日线和小时线置信度"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        fusion.update_signal('D', 0.8, 0.2)  # 强度 = 0.6
        result = fusion.update_signal('H', 0.75, 0.25)  # 强度 = 0.5
        # 日线贡献 50% × 0.6 = 0.3
        # 小时线贡献 35% × 0.5 = 0.175
        # 总计 = 0.475
        assert result.confidence == pytest.approx(0.3 + 0.175)

    def test_confidence_all_timeframes(self):
        """测试所有周期置信度"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})
        fusion.update_signal('D', 0.9, 0.1)   # 强度 = 0.8
        fusion.update_signal('H', 0.8, 0.2)   # 强度 = 0.6
        result = fusion.update_signal('M', 0.7, 0.3)  # 强度 = 0.4
        # 日线贡献 50% × 0.8 = 0.4
        # 小时线贡献 35% × 0.6 = 0.21
        # 分钟线贡献 15% × 0.4 = 0.06
        # 总计 = 0.67
        assert result.confidence == pytest.approx(0.4 + 0.21 + 0.06)


class TestSignalHistory:
    """信号历史记录测试"""

    def test_signal_history_recording(self):
        """测试信号历史记录"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        fusion.update_signal('D', 0.75, 0.25)
        fusion.update_signal('H', 0.70, 0.30)

        assert len(fusion.signal_history) == 2
        assert fusion.signal_history[0]['timeframe'] == 'D'
        assert fusion.signal_history[1]['timeframe'] == 'H'

    def test_get_last_signal(self):
        """测试获取最后一个信号"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        fusion.update_signal('D', 0.75, 0.25)
        result = fusion.update_signal('H', 0.70, 0.30)

        last = fusion.get_last_signal()
        assert last is not None
        assert last.final_signal == SignalDirection.LONG

    def test_reset_signals(self):
        """测试重置信号"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        fusion.update_signal('D', 0.75, 0.25)
        fusion.reset_signals()

        assert len(fusion.signals) == 0
        assert len(fusion.last_signal_timestamp) == 0


class TestRealWorldScenarios:
    """实际交易场景测试"""

    def test_strong_uptrend_confirmation(self):
        """强势上升趋势确认"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线强势看涨
        fusion.update_signal('D', 0.85, 0.15)
        # 小时线确认看涨，强度更高
        fusion.update_signal('H', 0.80, 0.20)
        # 分钟线精确看涨
        result = fusion.update_signal('M', 0.75, 0.25)

        assert result.final_signal == SignalDirection.LONG
        # 计算置信度: D: 50%×0.7, H: 35%×0.6, M: 15%×0.5 = 0.635
        assert result.confidence > 0.6  # 相对高置信度

    def test_daily_trend_exhaustion(self):
        """日线趋势衰竭"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 日线看涨强度刚好足够
        fusion.update_signal('D', 0.70, 0.30)
        # 小时线反向看跌，强度足够
        result = fusion.update_signal('H', 0.30, 0.70)

        assert result.final_signal == SignalDirection.NO_TRADE
        assert "冲突" in result.reasoning

    def test_missing_minute_bars(self):
        """缺少分钟线数据"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 完整的日线和小时线
        fusion.update_signal('D', 0.75, 0.25)
        result = fusion.update_signal('H', 0.70, 0.30)

        # 没有分钟线，应该等待
        assert result.final_signal == SignalDirection.LONG
        assert "等待分钟线" in result.reasoning

    def test_multiple_signal_updates(self):
        """多次信号更新"""
        fusion = HierarchicalSignalFusion({'D': 1440, 'H': 60, 'M': 5})

        # 第一个交易信号
        fusion.update_signal('D', 0.75, 0.25)
        result1 = fusion.update_signal('H', 0.70, 0.30)
        assert result1.final_signal == SignalDirection.LONG

        # H1 bar 更新，信号反转
        result2 = fusion.update_signal('H', 0.30, 0.70)
        assert result2.final_signal == SignalDirection.NO_TRADE

        # 日线依然看涨，等待新的小时线确认
        assert len(fusion.signal_history) == 3


class TestFusionResult:
    """融合结果测试"""

    def test_fusion_result_to_dict(self):
        """测试转换为字典"""
        result = FusionResult(
            final_signal=SignalDirection.LONG,
            daily_trend=SignalDirection.LONG,
            hourly_entry=SignalDirection.LONG,
            confidence=0.75,
            reasoning="test"
        )

        d = result.to_dict()
        assert d['final_signal'] == 'long'
        assert d['daily_trend'] == 'long'
        assert d['confidence'] == 0.75
        assert d['reasoning'] == 'test'
