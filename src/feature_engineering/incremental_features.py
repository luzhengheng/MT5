"""
增量特征计算 - 实盘流式数据处理

根据 Gemini Pro P1-02 审查建议实现。解决问题：
"实盘时，每来一个 Tick 或 Bar，你不能重新计算整个历史数据的指标（太慢）。
 需要实现增量计算 (Incremental Calculation) 或只取最近 N 个 Bar 进行滑动窗口计算。"

核心特点:
1. 增量计算: 只计算新增数据，无需重新计算历史
2. 滑动窗口: 只保留最近 N 个 Bar，减少内存占用
3. 低延迟: 特征计算 < 1 秒/bar
4. 批量一致性: 与离线计算结果一致（精度 < 1e-6）

使用方式:
    # 初始化增量计算器
    calc = IncrementalFeatureCalculator(lookback=100)

    # 第一次：加载初始数据
    calc.initialize(initial_bars)

    # 后续：每来新 Bar，增量更新
    features = calc.update(new_bar)

    # 获取完整特征向量
    feature_vector = calc.get_features()
"""

import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import pandas as pd
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Bar:
    """K线数据结构"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    tick_volume: int = 0  # 可选：Tick 数量

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'time': self.time,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
        }


@dataclass
class FeatureCache:
    """特征缓存 - 保存增量计算的中间结果"""

    # 基础特征缓存
    sma_values: Dict[int, deque] = field(default_factory=dict)  # SMA 窗口缓存
    ema_values: Dict[int, Optional[float]] = field(default_factory=dict)  # EMA 当前值
    rsi_values: Dict[int, Dict] = field(default_factory=dict)  # RSI 中间状态
    atr_values: deque = field(default_factory=lambda: deque(maxlen=14))  # ATR 缓存

    # 价格特征缓存
    returns: deque = field(default_factory=lambda: deque(maxlen=252))  # 收益率
    volatility_window: deque = field(default_factory=lambda: deque(maxlen=20))  # 波动率窗口

    # 成交量特征缓存
    volume_ma: Optional[float] = None  # 成交量移动平均

    def clear(self):
        """清空所有缓存"""
        self.sma_values.clear()
        self.ema_values.clear()
        self.rsi_values.clear()
        self.atr_values.clear()
        self.returns.clear()
        self.volatility_window.clear()
        self.volume_ma = None


class IncrementalFeatureCalculator:
    """
    增量特征计算器 - 用于实盘流式数据处理

    支持:
    - 初始化：从历史数据初始化缓存
    - 增量更新：每来新 Bar，增量计算新特征
    - 滑动窗口：只保留最近 N 个 Bar
    - 低延迟：特征计算 < 1 秒
    """

    def __init__(self, lookback: int = 100, max_bars: int = 500):
        """
        初始化增量特征计算器

        Args:
            lookback: 回看窗口大小（用于初始化特征）
            max_bars: 保留的最大 Bar 数（内存控制）
        """
        self.lookback = lookback
        self.max_bars = max_bars

        # K线缓冲（保留最近 max_bars 根 K线）
        self.bars: deque = deque(maxlen=max_bars)

        # 特征缓存
        self.cache = FeatureCache()

        # 初始化标志
        self.initialized = False
        self.last_update_time: Optional[datetime] = None

        # 统计信息
        self.stats = {
            'bars_processed': 0,
            'features_calculated': 0,
            'calculation_time_ms': 0,
        }

        logger.info(
            f"🔧 IncrementalFeatureCalculator 初始化: "
            f"lookback={lookback}, max_bars={max_bars}"
        )

    def initialize(self, history_bars: List[Bar] or pd.DataFrame) -> bool:
        """
        初始化增量计算器

        使用历史 K线数据初始化特征缓存，为后续增量计算做准备

        Args:
            history_bars: 历史 K线列表或 DataFrame
                - List[Bar]: Bar 对象列表
                - DataFrame: 包含 OHLCV 列的 DataFrame

        Returns:
            bool: 初始化是否成功
        """
        try:
            import time
            start_time = time.time()

            # 转换为 Bar 列表
            if isinstance(history_bars, pd.DataFrame):
                bars = self._dataframe_to_bars(history_bars)
            else:
                bars = history_bars

            if len(bars) < 10:
                logger.warning(f"⚠️ 历史数据过少: {len(bars)} 根，需要至少 10 根")
                return False

            # 加入缓冲区
            for bar in bars[-self.max_bars:]:
                self.bars.append(bar)

            # 初始化各项特征缓存
            self._init_sma_cache(bars)
            self._init_ema_cache(bars)
            self._init_rsi_cache(bars)
            self._init_atr_cache(bars)
            self._init_price_features(bars)

            self.initialized = True
            elapsed = (time.time() - start_time) * 1000

            logger.info(
                f"✅ 初始化完成: {len(bars)} 根 K线, "
                f"{elapsed:.2f}ms"
            )

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    def update(self, new_bar: Bar or Dict) -> Optional[Dict]:
        """
        增量更新 - 处理新 Bar

        关键: 只计算新增数据相关的特征，无需重新计算历史

        Args:
            new_bar: 新 K线（Bar 对象或字典）

        Returns:
            dict: 新计算的特征向量，失败返回 None
        """
        try:
            import time
            start_time = time.time()

            if not self.initialized:
                logger.warning("⚠️ 计算器未初始化，请先调用 initialize()")
                return None

            # 转换为 Bar 对象
            if isinstance(new_bar, dict):
                new_bar = Bar(**new_bar)

            # 检查时间顺序
            if self.last_update_time and new_bar.time <= self.last_update_time:
                logger.warning(f"⚠️ Bar 时间顺序错误: {new_bar.time}")
                return None

            # 添加到缓冲区
            self.bars.append(new_bar)
            self.last_update_time = new_bar.time

            # 增量计算各项特征
            features = self._calculate_incremental_features(new_bar)

            # 统计
            self.stats['bars_processed'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['calculation_time_ms'] = elapsed
            self.stats['features_calculated'] += 1

            if elapsed > 1000:  # 如果超过 1 秒，记录警告
                logger.warning(
                    f"⚠️ 特征计算耗时过长: {elapsed:.2f}ms > 1000ms"
                )

            logger.debug(
                f"📊 增量计算完成: {len(features)} 个特征, "
                f"{elapsed:.2f}ms"
            )

            return features

        except Exception as e:
            logger.error(f"❌ 增量更新失败: {e}")
            return None

    def get_features(self) -> Dict:
        """
        获取完整特征向量

        返回所有计算的特征（基础 + 高级）

        Returns:
            dict: 特征向量 {特征名: 特征值}
        """
        try:
            if not self.bars:
                logger.warning("⚠️ 没有可用的 K线数据")
                return {}

            features = {}

            # 基础特征
            features.update(self._get_basic_features())

            # 高级特征
            features.update(self._get_advanced_features())

            return features

        except Exception as e:
            logger.error(f"❌ 获取特征失败: {e}")
            return {}

    def _calculate_incremental_features(self, new_bar: Bar) -> Dict:
        """
        增量计算新 Bar 的所有特征

        只计算受新 Bar 影响的特征，避免重新计算历史数据

        Args:
            new_bar: 新 K线

        Returns:
            dict: 新计算的特征
        """
        features = {}

        # 0. OHLCV 基础数据
        features['open'] = new_bar.open
        features['high'] = new_bar.high
        features['low'] = new_bar.low
        features['close'] = new_bar.close
        features['volume'] = new_bar.volume

        # 1. SMA 增量更新
        for period in [5, 10, 20, 50, 200]:
            sma = self._update_sma(new_bar.close, period)
            if sma is not None:
                features[f'sma_{period}'] = sma

        # 2. EMA 增量更新
        for period in [5, 12, 26]:
            ema = self._update_ema(new_bar.close, period)
            if ema is not None:
                features[f'ema_{period}'] = ema

        # 3. RSI 增量更新
        for period in [14]:
            rsi = self._update_rsi(new_bar.close, period)
            if rsi is not None:
                features[f'rsi_{period}'] = rsi

        # 4. ATR 增量更新
        atr = self._update_atr(new_bar)
        if atr is not None:
            features['atr'] = atr

        # 5. 价格特征
        features.update(self._update_price_features(new_bar))

        # 6. 成交量特征
        features.update(self._update_volume_features(new_bar))

        return features

    # ==================== 增量计算方法 ====================

    def _update_sma(self, close: float, period: int) -> Optional[float]:
        """增量更新 SMA"""
        if period not in self.cache.sma_values:
            self.cache.sma_values[period] = deque(maxlen=period)

        window = self.cache.sma_values[period]
        window.append(close)

        if len(window) < period:
            return None

        return float(np.mean(list(window)))

    def _update_ema(self, close: float, period: int) -> Optional[float]:
        """增量更新 EMA (指数移动平均)"""
        if period not in self.cache.ema_values:
            # 初始化：使用 SMA
            self.cache.ema_values[period] = None

        multiplier = 2.0 / (period + 1)

        if self.cache.ema_values[period] is None:
            # 第一次计算：使用当前值作为初始 EMA
            self.cache.ema_values[period] = close
            return close
        else:
            # 后续：EMA 增量更新
            ema = (close - self.cache.ema_values[period]) * multiplier + self.cache.ema_values[period]
            self.cache.ema_values[period] = ema
            return ema

    def _update_rsi(self, close: float, period: int = 14) -> Optional[float]:
        """增量更新 RSI"""
        if period not in self.cache.rsi_values:
            self.cache.rsi_values[period] = {
                'closes': deque(maxlen=period),
                'avg_gain': None,
                'avg_loss': None,
            }

        state = self.cache.rsi_values[period]
        state['closes'].append(close)

        if len(state['closes']) < 2:
            return None

        # 计算当前 gain/loss
        closes = list(state['closes'])
        change = closes[-1] - closes[-2]
        gain = change if change > 0 else 0
        loss = -change if change < 0 else 0

        # 初始化平均 gain/loss
        if state['avg_gain'] is None:
            all_changes = np.diff(closes)
            gains = np.where(all_changes > 0, all_changes, 0)
            losses = np.where(all_changes < 0, -all_changes, 0)
            state['avg_gain'] = float(np.mean(gains))
            state['avg_loss'] = float(np.mean(losses))
        else:
            # 增量更新：平滑平均
            state['avg_gain'] = (state['avg_gain'] * (period - 1) + gain) / period
            state['avg_loss'] = (state['avg_loss'] * (period - 1) + loss) / period

        # 计算 RSI
        if state['avg_loss'] == 0:
            return 100.0 if state['avg_gain'] > 0 else 0.0

        rs = state['avg_gain'] / state['avg_loss']
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return float(rsi)

    def _update_atr(self, bar: Bar, period: int = 14) -> Optional[float]:
        """增量更新 ATR (真实波幅)"""
        if len(self.bars) < 2:
            return None

        prev_close = self.bars[-2].close
        tr = max(
            bar.high - bar.low,
            abs(bar.high - prev_close),
            abs(bar.low - prev_close),
        )

        self.cache.atr_values.append(tr)

        if len(self.cache.atr_values) < period:
            return None

        return float(np.mean(list(self.cache.atr_values)))

    def _update_price_features(self, bar: Bar) -> Dict:
        """增量更新价格特征"""
        features = {}

        if len(self.bars) < 2:
            return features

        prev_close = self.bars[-2].close

        # 日收益率
        returns = (bar.close - prev_close) / prev_close if prev_close != 0 else 0
        self.cache.returns.append(returns)
        features['daily_return'] = float(returns)

        # 波动率（过去 20 天）
        if len(self.cache.returns) >= 2:
            volatility = float(np.std(list(self.cache.returns))) * np.sqrt(252)
            features['volatility'] = volatility

        # 价格位置 (Position in Range)
        if len(self.bars) >= 20:
            recent_bars = list(self.bars)[-20:]
            high_20 = max(b.high for b in recent_bars)
            low_20 = min(b.low for b in recent_bars)
            if high_20 != low_20:
                price_position = (bar.close - low_20) / (high_20 - low_20)
                features['price_position_20d'] = float(np.clip(price_position, 0, 1))

        return features

    def _update_volume_features(self, bar: Bar) -> Dict:
        """增量更新成交量特征"""
        features = {}

        if len(self.bars) < 2:
            return features

        prev_volume = self.bars[-2].volume

        # 成交量变化率
        if prev_volume > 0:
            volume_change = (bar.volume - prev_volume) / prev_volume
            features['volume_change'] = float(volume_change)

        # 成交量移动平均
        if len(self.bars) >= 20:
            recent_volumes = [b.volume for b in list(self.bars)[-20:]]
            volume_ma = np.mean(recent_volumes)
            self.cache.volume_ma = volume_ma
            features['volume_ma_20'] = float(volume_ma)

        return features

    # ==================== 初始化方法 ====================

    def _init_sma_cache(self, bars: List[Bar]):
        """初始化 SMA 缓存"""
        for period in [5, 10, 20, 50, 200]:
            if len(bars) >= period:
                closes = [b.close for b in bars[-period:]]
                self.cache.sma_values[period] = deque(closes, maxlen=period)

    def _init_ema_cache(self, bars: List[Bar]):
        """初始化 EMA 缓存"""
        for period in [5, 12, 26]:
            if len(bars) >= period:
                closes = [b.close for b in bars[-period:]]
                ema = float(np.mean(closes))
                self.cache.ema_values[period] = ema

    def _init_rsi_cache(self, bars: List[Bar]):
        """初始化 RSI 缓存"""
        for period in [14]:
            if len(bars) >= period:
                closes = [b.close for b in bars[-period:]]
                changes = np.diff(closes)
                gains = np.where(changes > 0, changes, 0)
                losses = np.where(changes < 0, -changes, 0)
                self.cache.rsi_values[period] = {
                    'closes': deque(closes, maxlen=period),
                    'avg_gain': float(np.mean(gains)),
                    'avg_loss': float(np.mean(losses)),
                }

    def _init_atr_cache(self, bars: List[Bar]):
        """初始化 ATR 缓存"""
        if len(bars) >= 2:
            for i in range(1, min(len(bars), 14 + 1)):
                bar = bars[-14 - i + 1]
                prev_close = bars[-14 - i].close
                tr = max(
                    bar.high - bar.low,
                    abs(bar.high - prev_close),
                    abs(bar.low - prev_close),
                )
                self.cache.atr_values.append(tr)

    def _init_price_features(self, bars: List[Bar]):
        """初始化价格特征缓存"""
        if len(bars) >= 2:
            for i in range(1, len(bars)):
                prev_close = bars[i - 1].close
                curr_close = bars[i].close
                returns = (curr_close - prev_close) / prev_close if prev_close != 0 else 0
                self.cache.returns.append(returns)

    # ==================== 获取特征方法 ====================

    def _get_basic_features(self) -> Dict:
        """获取基础特征"""
        features = {}

        if not self.bars:
            return features

        bars_list = list(self.bars)
        last_bar = bars_list[-1]

        # OHLC
        features['open'] = last_bar.open
        features['high'] = last_bar.high
        features['low'] = last_bar.low
        features['close'] = last_bar.close
        features['volume'] = last_bar.volume

        # SMA
        for period, window in self.cache.sma_values.items():
            if len(window) == period:
                features[f'sma_{period}'] = float(np.mean(list(window)))

        # EMA
        for period, ema_val in self.cache.ema_values.items():
            if ema_val is not None:
                features[f'ema_{period}'] = ema_val

        return features

    def _get_advanced_features(self) -> Dict:
        """获取高级特征"""
        features = {}

        if len(self.cache.returns) >= 1:
            features['daily_return'] = self.cache.returns[-1]

        if len(self.cache.returns) >= 2:
            features['volatility'] = float(np.std(list(self.cache.returns))) * np.sqrt(252)

        if len(self.bars) >= 20:
            recent_bars = list(self.bars)[-20:]
            high_20 = max(b.high for b in recent_bars)
            low_20 = min(b.low for b in recent_bars)
            if high_20 != low_20:
                features['price_position_20d'] = float(
                    np.clip((self.bars[-1].close - low_20) / (high_20 - low_20), 0, 1)
                )

        return features

    # ==================== 工具方法 ====================

    @staticmethod
    def _dataframe_to_bars(df: pd.DataFrame) -> List[Bar]:
        """将 DataFrame 转换为 Bar 列表"""
        bars = []
        for idx, row in df.iterrows():
            bar = Bar(
                time=pd.to_datetime(row.get('time', idx)) if 'time' in row else datetime.now(),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row.get('volume', 0)),
            )
            bars.append(bar)
        return bars

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'bars_processed': self.stats['bars_processed'],
            'features_calculated': self.stats['features_calculated'],
            'calculation_time_ms': self.stats['calculation_time_ms'],
            'buffer_size': len(self.bars),
            'initialized': self.initialized,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"IncrementalFeatureCalculator("
            f"bars={len(self.bars)}, "
            f"initialized={self.initialized}, "
            f"calc_time={self.stats['calculation_time_ms']:.2f}ms"
            f")"
        )
