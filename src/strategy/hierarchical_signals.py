"""分层信号融合模块 - 支持日线→小时线→分钟线的多周期信号融合"""

import logging
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class SignalPriority(Enum):
    """信号优先级层级"""
    DAILY = 3       # 日线: 趋势确认 (必须)
    HOURLY = 2      # 小时线: 入场机会 (必须与日线一致)
    MINUTE = 1      # 分钟线: 执行/止损 (可选微调)


class SignalDirection(Enum):
    """交易信号方向"""
    LONG = 'long'           # 看涨信号
    SHORT = 'short'         # 看跌信号
    NO_SIGNAL = 'no_signal' # 无信号
    NO_TRADE = 'no_trade'   # 不交易 (冲突)


@dataclass
class TimeframeSignal:
    """单个周期的信号数据"""
    timeframe: str          # 周期标识 ('D', 'H', 'M')
    y_pred_proba_long: float = 0.5  # 看涨概率
    y_pred_proba_short: float = 0.5  # 看跌概率
    timestamp: Optional[str] = None  # 信号时间戳

    @property
    def signal_strength(self) -> float:
        """信号强度 (置信度)"""
        return max(self.y_pred_proba_long, self.y_pred_proba_short) - 0.5

    @property
    def direction(self) -> SignalDirection:
        """判断信号方向"""
        if self.y_pred_proba_long > self.y_pred_proba_short:
            if self.y_pred_proba_long > 0.55:
                return SignalDirection.LONG
        elif self.y_pred_proba_short > self.y_pred_proba_long:
            if self.y_pred_proba_short > 0.55:
                return SignalDirection.SHORT

        return SignalDirection.NO_SIGNAL

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'timeframe': self.timeframe,
            'y_pred_proba_long': self.y_pred_proba_long,
            'y_pred_proba_short': self.y_pred_proba_short,
            'signal_strength': self.signal_strength,
            'direction': self.direction.value,
            'timestamp': self.timestamp,
        }


@dataclass
class FusionResult:
    """分层信号融合结果"""
    final_signal: SignalDirection = SignalDirection.NO_SIGNAL  # 最终信号
    daily_trend: Optional[SignalDirection] = None              # 日线趋势
    hourly_entry: Optional[SignalDirection] = None             # 小时线入场
    minute_detail: Optional[SignalDirection] = None            # 分钟线细节
    confidence: float = 0.0                                     # 总体置信度
    reasoning: str = ""                                         # 融合逻辑说明

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'final_signal': self.final_signal.value,
            'daily_trend': self.daily_trend.value if self.daily_trend else None,
            'hourly_entry': self.hourly_entry.value if self.hourly_entry else None,
            'minute_detail': self.minute_detail.value if self.minute_detail else None,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
        }


class HierarchicalSignalFusion:
    """分层信号融合引擎

    实现日线→小时线→分钟线的多周期信号融合:
    1. **日线趋势确认** (必须): 确定整体趋势方向
    2. **小时线入场时机** (必须): 必须与日线一致，提供具体入场点
    3. **分钟线精确执行** (可选): 微调执行策略，非必须

    融合规则:
    - 日线和小时线方向冲突 → 不交易 (NO_TRADE)
    - 只有小时线信号，无日线确认 → 等待 (WAIT)
    - 日线趋势 + 小时线信号一致 → 执行 (日线>小时线>分钟线优先级)
    """

    # 置信度阈值
    DAILY_THRESHOLD = 0.55      # 日线信号阈值
    HOURLY_THRESHOLD = 0.65     # 小时线信号阈值 (更严格)
    MINUTE_THRESHOLD = 0.55     # 分钟线信号阈值

    def __init__(self, periods: Dict[str, int]):
        """初始化分层信号融合引擎

        Args:
            periods: 周期映射 {'D': 1440, 'H': 60, 'M': 5}
        """
        self.periods = periods  # 周期映射
        self.signals: Dict[str, TimeframeSignal] = {}  # 存储各周期信号
        self.last_signal_timestamp: Dict[str, str] = {}  # 避免重复信号
        self.signal_history: list = []  # 信号历史记录

        logger.info(
            f"✓ HierarchicalSignalFusion 初始化: "
            f"周期={list(periods.keys())}"
        )

    def update_signal(
        self,
        timeframe: str,
        y_pred_proba_long: float,
        y_pred_proba_short: float,
        timestamp: Optional[str] = None,
    ) -> FusionResult:
        """更新某周期的信号并进行分层融合

        Args:
            timeframe: 周期标识 ('D', 'H', 'M')
            y_pred_proba_long: 看涨概率 [0, 1]
            y_pred_proba_short: 看跌概率 [0, 1]
            timestamp: 信号时间戳 (可选)

        Returns:
            FusionResult - 融合结果

        Raises:
            ValueError: 如果周期未配置
        """
        if timeframe not in self.periods:
            raise ValueError(
                f"未知周期: {timeframe}, 可用周期: {list(self.periods.keys())}"
            )

        # 创建周期信号
        signal = TimeframeSignal(
            timeframe=timeframe,
            y_pred_proba_long=y_pred_proba_long,
            y_pred_proba_short=y_pred_proba_short,
            timestamp=timestamp,
        )

        self.signals[timeframe] = signal
        logger.debug(
            f"更新信号: {timeframe} - "
            f"long={y_pred_proba_long:.3f}, short={y_pred_proba_short:.3f}"
        )

        # 执行分层融合
        result = self._fuse_signals()

        # 记录到历史
        self.signal_history.append({
            'timeframe': timeframe,
            'signal': signal.to_dict(),
            'fusion_result': result.to_dict(),
        })

        return result

    def _fuse_signals(self) -> FusionResult:
        """执行分层信号融合

        Returns:
            FusionResult
        """
        result = FusionResult()

        # 第 1 层: 日线趋势确认 (必须)
        daily_signal = self.signals.get('D')
        if daily_signal is None:
            result.reasoning = "日线信号缺失"
            result.final_signal = SignalDirection.NO_SIGNAL
            return result

        daily_trend = self._get_direction(
            daily_signal.y_pred_proba_long,
            daily_signal.y_pred_proba_short,
            self.DAILY_THRESHOLD
        )
        result.daily_trend = daily_trend

        if daily_trend == SignalDirection.NO_SIGNAL:
            result.reasoning = "日线无趋势确认 (阈值 0.55)"
            result.final_signal = SignalDirection.NO_SIGNAL
            return result

        # 第 2 层: 小时线入场时机 (必须与日线一致)
        hourly_signal = self.signals.get('H')
        if hourly_signal is None:
            result.reasoning = f"日线{daily_trend.value}趋势已确认，等待小时线入场信号"
            result.final_signal = SignalDirection.NO_SIGNAL
            return result

        hourly_entry = self._get_direction(
            hourly_signal.y_pred_proba_long,
            hourly_signal.y_pred_proba_short,
            self.HOURLY_THRESHOLD  # 更严格的阈值
        )
        result.hourly_entry = hourly_entry

        # 检查日线和小时线一致性
        if hourly_entry == SignalDirection.NO_SIGNAL:
            result.reasoning = f"日线{daily_trend.value}，但小时线无入场信号"
            result.final_signal = SignalDirection.NO_SIGNAL
            return result

        if daily_trend != hourly_entry:
            result.reasoning = (
                f"日线{daily_trend.value}与小时线{hourly_entry.value}冲突，停止交易"
            )
            result.final_signal = SignalDirection.NO_TRADE
            return result

        # 第 3 层: 分钟线精确执行 (可选)
        minute_signal = self.signals.get('M')
        if minute_signal is not None:
            minute_detail = self._get_direction(
                minute_signal.y_pred_proba_long,
                minute_signal.y_pred_proba_short,
                self.MINUTE_THRESHOLD
            )
            result.minute_detail = minute_detail

            # M5 可以微调方向，但不能反向
            if minute_detail != SignalDirection.NO_SIGNAL:
                if minute_detail == hourly_entry:
                    result.reasoning = (
                        f"日线{daily_trend.value} + "
                        f"小时线{hourly_entry.value} + "
                        f"分钟线{minute_detail.value}一致，执行"
                    )
                else:
                    result.reasoning = (
                        f"日线{daily_trend.value} + "
                        f"小时线{hourly_entry.value}一致，"
                        f"分钟线{minute_detail.value}不一致，保守执行"
                    )
            else:
                result.reasoning = (
                    f"日线{daily_trend.value} + "
                    f"小时线{hourly_entry.value}一致，"
                    f"分钟线无信号，标准执行"
                )
        else:
            result.reasoning = (
                f"日线{daily_trend.value} + "
                f"小时线{hourly_entry.value}一致，等待分钟线"
            )

        # 设置最终信号为日线和小时线的一致方向
        result.final_signal = hourly_entry

        # 计算总体置信度
        result.confidence = self._calculate_confidence(result)

        return result

    def _get_direction(
        self,
        proba_long: float,
        proba_short: float,
        threshold: float = 0.55
    ) -> SignalDirection:
        """判断信号方向

        Args:
            proba_long: 看涨概率
            proba_short: 看跌概率
            threshold: 信号阈值

        Returns:
            SignalDirection
        """
        if proba_long > proba_short and proba_long > threshold:
            return SignalDirection.LONG
        elif proba_short > proba_long and proba_short > threshold:
            return SignalDirection.SHORT
        else:
            return SignalDirection.NO_SIGNAL

    def _calculate_confidence(self, result: FusionResult) -> float:
        """计算融合结果的总体置信度

        Args:
            result: 融合结果

        Returns:
            置信度 [0, 1]
        """
        if result.final_signal == SignalDirection.NO_SIGNAL:
            return 0.0

        if result.final_signal == SignalDirection.NO_TRADE:
            return 0.0

        # 计算各层级的强度
        daily_strength = 0.0
        hourly_strength = 0.0
        minute_strength = 0.0

        if result.daily_trend is not None:
            daily_signal = self.signals.get('D')
            if daily_signal:
                daily_strength = (
                    abs(daily_signal.y_pred_proba_long - daily_signal.y_pred_proba_short)
                )

        if result.hourly_entry is not None:
            hourly_signal = self.signals.get('H')
            if hourly_signal:
                hourly_strength = (
                    abs(hourly_signal.y_pred_proba_long - hourly_signal.y_pred_proba_short)
                )

        if result.minute_detail is not None:
            minute_signal = self.signals.get('M')
            if minute_signal:
                minute_strength = (
                    abs(minute_signal.y_pred_proba_long - minute_signal.y_pred_proba_short)
                )

        # 加权平均: 日线 50%, 小时线 35%, 分钟线 15%
        confidence = (
            daily_strength * 0.50 +
            hourly_strength * 0.35 +
            minute_strength * 0.15
        )

        return min(confidence, 1.0)  # 限制在 [0, 1]

    def get_last_signal(self) -> Optional[FusionResult]:
        """获取最后一次融合结果

        Returns:
            FusionResult 或 None
        """
        if len(self.signal_history) == 0:
            return None

        last_entry = self.signal_history[-1]
        return self._dict_to_fusion_result(last_entry['fusion_result'])

    def reset_signals(self) -> None:
        """重置所有信号 (用于交易日切换)"""
        self.signals.clear()
        self.last_signal_timestamp.clear()
        logger.info("✓ 所有分层信号已重置")

    def get_status(self) -> Dict:
        """获取融合引擎状态"""
        status = {
            'periods': self.periods,
            'active_signals': list(self.signals.keys()),
            'signal_count': len(self.signal_history),
        }

        # 各周期当前信号
        for timeframe, signal in self.signals.items():
            status[f'signal_{timeframe}'] = signal.to_dict()

        return status

    def _dict_to_fusion_result(self, data: Dict) -> FusionResult:
        """从字典转换为 FusionResult"""
        return FusionResult(
            final_signal=SignalDirection(data.get('final_signal')),
            daily_trend=SignalDirection(data.get('daily_trend')) if data.get('daily_trend') else None,
            hourly_entry=SignalDirection(data.get('hourly_entry')) if data.get('hourly_entry') else None,
            minute_detail=SignalDirection(data.get('minute_detail')) if data.get('minute_detail') else None,
            confidence=data.get('confidence', 0.0),
            reasoning=data.get('reasoning', ''),
        )
