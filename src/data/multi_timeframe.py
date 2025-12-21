"""多周期数据管理和对齐模块"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TimeframeConfig:
    """单个周期的配置"""
    period: int                         # 周期 (分钟): 5=M5, 60=H1, 1440=D1
    lookback: int = 100                 # 回溯数量 (bar 数)
    features_enabled: List[str] = field(default_factory=list)  # 启用的特征列表

    @property
    def period_name(self) -> str:
        """周期名称"""
        if self.period == 5:
            return "M5"
        if self.period == 60:
            return "H1"
        if self.period == 1440:
            return "D1"
        return f"M{self.period}"

    def __post_init__(self):
        """验证配置有效性"""
        if self.period <= 0:
            raise ValueError(f"周期必须 > 0, 得到 {self.period}")
        if self.lookback <= 0:
            raise ValueError(f"回溯数必须 > 0, 得到 {self.lookback}")


@dataclass
class OHLC:
    """OHLC bar 数据"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
        }


class TimeframeBuffer:
    """单个周期的数据缓冲区"""

    def __init__(self, config: TimeframeConfig):
        """初始化缓冲区

        Args:
            config: 周期配置
        """
        self.config = config
        self.buffer = deque(maxlen=config.lookback)  # 限制历史 bar 数量
        self.bar_count = 0  # 累积 bar 计数

    def append(self, ohlc: OHLC) -> None:
        """添加新 bar"""
        self.buffer.append(ohlc)
        self.bar_count += 1

    def get_last(self, n: int = 1) -> List[OHLC]:
        """获取最后 n 根 bar"""
        if n <= 0:
            raise ValueError(f"n 必须 > 0, 得到 {n}")
        return list(self.buffer)[-n:] if len(self.buffer) > 0 else []

    def __len__(self) -> int:
        """缓冲区内 bar 数量"""
        return len(self.buffer)

    def is_full(self) -> bool:
        """缓冲区是否已满"""
        return len(self.buffer) == self.config.lookback


class MultiTimeframeDataFeed:
    """多周期数据管理和对齐引擎

    支持多个不同周期的数据对齐和聚合。基础周期为 M5 (5 分钟),
    其他周期必须是 M5 的整数倍。
    """

    def __init__(self, base_period: int = 5):
        """初始化多周期数据源

        Args:
            base_period: 基础周期 (分钟), 默认 5 分钟 (M5)
        """
        self.base_period = base_period
        self.timeframes: Dict[int, TimeframeConfig] = {}  # {period: config}
        self.buffers: Dict[int, TimeframeBuffer] = {}     # {period: buffer}
        self.bar_counters: Dict[int, int] = {}            # {period: count}
        self.completed_timeframes: Set[int] = set()       # 本次完成的高级周期

        # 自动添加基础周期缓冲区
        base_config = TimeframeConfig(base_period)
        self.timeframes[base_period] = base_config
        self.buffers[base_period] = TimeframeBuffer(base_config)
        self.bar_counters[base_period] = 0

        logger.info(f"✓ MultiTimeframeDataFeed 初始化: 基础周期 {base_period} 分钟")

    def add_timeframe(self, period: int, lookback: int = 100) -> None:
        """添加新周期

        Args:
            period: 周期 (分钟)
            lookback: 回溯数量 (bar 数), 默认 100

        Raises:
            ValueError: 如果周期不是基础周期的倍数
        """
        # 验证周期有效性
        if period < self.base_period:
            raise ValueError(
                f"周期 {period} 不能小于基础周期 {self.base_period}"
            )

        if period % self.base_period != 0:
            raise ValueError(
                f"周期 {period} 必须是基础周期 {self.base_period} 的倍数"
            )

        if period in self.timeframes:
            logger.warning(f"周期 {period} 已存在, 覆盖旧配置")

        # 创建配置和缓冲区
        config = TimeframeConfig(period, lookback)
        self.timeframes[period] = config
        self.buffers[period] = TimeframeBuffer(config)
        self.bar_counters[period] = 0

        logger.info(f"✓ 添加周期: {config.period_name} (period={period}, lookback={lookback})")

    def on_base_bar(self, ohlc: OHLC) -> Dict[int, OHLC]:
        """处理基础周期新 bar, 返回完成的高级周期 bar

        Args:
            ohlc: 新 bar 数据

        Returns:
            {period: ohlc} - 完成的高级周期 bar 映射
        """
        completed = {}
        self.completed_timeframes.clear()

        # 更新基础周期缓冲区和计数
        self.buffers[self.base_period].append(ohlc)
        self.bar_counters[self.base_period] += 1

        # 按周期大小升序处理，支持分层聚合
        sorted_periods = sorted(self.timeframes.keys())

        for period in sorted_periods:
            if period == self.base_period:
                continue

            # 找到最接近的下级周期用于聚合
            source_period = self.base_period
            for lower_period in sorted_periods:
                if lower_period < period and lower_period > source_period:
                    source_period = lower_period

            multiplier = period // source_period

            # 判断该周期是否完成
            if self.bar_counters[source_period] % multiplier == 0:
                # 聚合 bar
                aggregated = self._aggregate_bars(source_period, period)
                if aggregated is not None:
                    completed[period] = aggregated
                    self.buffers[period].append(aggregated)
                    self.bar_counters[period] += 1
                    self.completed_timeframes.add(period)
                    logger.debug(
                        f"✓ {self.timeframes[period].period_name} bar 完成 "
                        f"(第 {self.bar_counters[period]} 根)"
                    )

        return completed

    def _aggregate_bars(self, from_period: int, to_period: int) -> Optional[OHLC]:
        """将基础周期 bar 聚合成高级周期 bar

        Args:
            from_period: 源周期
            to_period: 目标周期

        Returns:
            聚合后的 OHLC, 若数据不足则返回 None
        """
        source_buffer = self.buffers[from_period]
        multiplier = to_period // from_period

        # 检查是否有足够的 bar
        if len(source_buffer) < multiplier:
            return None

        # 获取最后 multiplier 根 bar
        bars = source_buffer.get_last(multiplier)
        if len(bars) < multiplier:
            return None

        # 聚合 OHLC
        return OHLC(
            timestamp=bars[-1].timestamp,  # 最后一根 bar 的时间戳
            open=bars[0].open,             # 第一根 bar 的 open
            high=max(b.high for b in bars),  # 最大 high
            low=min(b.low for b in bars),    # 最小 low
            close=bars[-1].close,          # 最后一根 bar 的 close
            volume=sum(b.volume for b in bars),  # 总成交量
        )

    def get_bars(self, period: int, count: int = 1) -> List[OHLC]:
        """获取指定周期的最后 n 根 bar

        Args:
            period: 周期 (分钟)
            count: bar 数量, 默认 1

        Returns:
            OHLC bar 列表
        """
        if period not in self.buffers:
            logger.warning(f"周期 {period} 未配置")
            return []

        return self.buffers[period].get_last(count)

    def get_buffer_size(self, period: int) -> int:
        """获取指定周期的缓冲区大小

        Args:
            period: 周期 (分钟)

        Returns:
            缓冲区内 bar 数量
        """
        if period not in self.buffers:
            return 0

        return len(self.buffers[period])

    def get_bar_count(self, period: int) -> int:
        """获取指定周期的累积 bar 计数

        Args:
            period: 周期 (分钟)

        Returns:
            累积 bar 数量
        """
        return self.bar_counters.get(period, 0)

    def is_timeframe_complete(self, period: int) -> bool:
        """判断指定周期是否刚完成新 bar

        Args:
            period: 周期 (分钟)

        Returns:
            是否刚完成
        """
        return period in self.completed_timeframes

    def get_status(self) -> Dict:
        """获取所有周期的状态

        Returns:
            状态字典
        """
        status = {
            'base_period': self.base_period,
            'timeframes': {},
        }

        for period in sorted(self.timeframes.keys()):
            config = self.timeframes[period]
            buffer = self.buffers[period]

            status['timeframes'][config.period_name] = {
                'period': period,
                'buffer_size': len(buffer),
                'bar_count': self.bar_counters[period],
                'is_full': buffer.is_full(),
                'is_complete': self.is_timeframe_complete(period),
            }

        return status

    def reset(self) -> None:
        """重置所有缓冲区"""
        for buffer in self.buffers.values():
            buffer.buffer.clear()
            buffer.bar_count = 0

        for period in self.bar_counters:
            self.bar_counters[period] = 0

        self.completed_timeframes.clear()
        logger.info("✓ MultiTimeframeDataFeed 已重置")
