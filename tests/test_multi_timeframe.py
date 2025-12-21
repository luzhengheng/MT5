"""多周期数据对齐和融合测试"""

import pytest
from datetime import datetime, timedelta
from src.data.multi_timeframe import (
    OHLC,
    TimeframeConfig,
    TimeframeBuffer,
    MultiTimeframeDataFeed,
)


class TestTimeframeConfig:
    """TimeframeConfig 单元测试"""

    def test_period_name_m5(self):
        """测试 M5 周期名称"""
        config = TimeframeConfig(5)
        assert config.period_name == "M5"

    def test_period_name_h1(self):
        """测试 H1 周期名称"""
        config = TimeframeConfig(60)
        assert config.period_name == "H1"

    def test_period_name_d1(self):
        """测试 D1 周期名称"""
        config = TimeframeConfig(1440)
        assert config.period_name == "D1"

    def test_period_name_custom(self):
        """测试自定义周期名称"""
        config = TimeframeConfig(15)
        assert config.period_name == "M15"

    def test_invalid_period_zero(self):
        """测试无效周期 (0)"""
        with pytest.raises(ValueError, match="周期必须 > 0"):
            TimeframeConfig(0)

    def test_invalid_period_negative(self):
        """测试无效周期 (负数)"""
        with pytest.raises(ValueError, match="周期必须 > 0"):
            TimeframeConfig(-5)

    def test_invalid_lookback_zero(self):
        """测试无效回溯数 (0)"""
        with pytest.raises(ValueError, match="回溯数必须 > 0"):
            TimeframeConfig(5, lookback=0)

    def test_invalid_lookback_negative(self):
        """测试无效回溯数 (负数)"""
        with pytest.raises(ValueError, match="回溯数必须 > 0"):
            TimeframeConfig(5, lookback=-10)


class TestTimeframeBuffer:
    """TimeframeBuffer 单元测试"""

    def test_buffer_append(self):
        """测试添加 bar 到缓冲区"""
        config = TimeframeConfig(5, lookback=10)
        buffer = TimeframeBuffer(config)

        now = datetime.now()
        ohlc = OHLC(now, 1.0, 1.1, 0.9, 1.05, 100)
        buffer.append(ohlc)

        assert len(buffer) == 1
        assert buffer.bar_count == 1

    def test_buffer_maxlen(self):
        """测试缓冲区最大长度限制"""
        config = TimeframeConfig(5, lookback=5)
        buffer = TimeframeBuffer(config)

        now = datetime.now()
        for i in range(10):
            ohlc = OHLC(now + timedelta(minutes=i), 1.0 + i*0.01, 1.1, 0.9, 1.05, 100)
            buffer.append(ohlc)

        assert len(buffer) == 5  # 最多保留 5 根 bar
        assert buffer.bar_count == 10  # 但计数器继续增加

    def test_buffer_get_last(self):
        """测试获取最后 n 根 bar"""
        config = TimeframeConfig(5, lookback=10)
        buffer = TimeframeBuffer(config)

        now = datetime.now()
        for i in range(5):
            ohlc = OHLC(now + timedelta(minutes=i), 1.0, 1.1, 0.9, 1.05, 100)
            buffer.append(ohlc)

        last_3 = buffer.get_last(3)
        assert len(last_3) == 3

    def test_buffer_is_full(self):
        """测试缓冲区是否满"""
        config = TimeframeConfig(5, lookback=3)
        buffer = TimeframeBuffer(config)

        now = datetime.now()
        assert not buffer.is_full()

        for i in range(3):
            ohlc = OHLC(now + timedelta(minutes=i), 1.0, 1.1, 0.9, 1.05, 100)
            buffer.append(ohlc)

        assert buffer.is_full()


class TestMultiTimeframeDataFeed:
    """MultiTimeframeDataFeed 核心测试"""

    def test_initialization(self):
        """测试初始化"""
        feed = MultiTimeframeDataFeed(base_period=5)
        assert feed.base_period == 5
        assert 5 in feed.timeframes  # 基础周期自动添加

    def test_add_timeframe(self):
        """测试添加周期"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(60)  # H1

        assert 60 in feed.timeframes
        assert feed.timeframes[60].period == 60

    def test_add_timeframe_invalid_not_multiple(self):
        """测试添加无效周期 (不是倍数)"""
        feed = MultiTimeframeDataFeed(base_period=5)

        with pytest.raises(ValueError, match="必须是基础周期"):
            feed.add_timeframe(67)  # 不是 5 的倍数

    def test_add_timeframe_invalid_less_than_base(self):
        """测试添加小于基础周期的周期"""
        feed = MultiTimeframeDataFeed(base_period=5)

        with pytest.raises(ValueError, match="不能小于基础周期"):
            feed.add_timeframe(3)

    def test_on_base_bar_single_period(self):
        """测试处理单周期 bar"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(5)  # 只有 M5

        now = datetime.now()
        ohlc = OHLC(now, 1.0, 1.1, 0.9, 1.05, 100)
        completed = feed.on_base_bar(ohlc)

        assert len(completed) == 0  # M5 本身不完成，只有高级周期才完成
        assert feed.get_buffer_size(5) == 1
        assert feed.get_bar_count(5) == 1

    def test_data_alignment_m5_to_h1(self):
        """测试 M5 到 H1 对齐: 12 根 M5 = 1 根 H1"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(5)  # M5
        feed.add_timeframe(60)  # H1 = 12 * M5

        now = datetime.now()
        completed_count = 0

        # 处理 12 根 M5 bar
        for i in range(12):
            ohlc = OHLC(
                now + timedelta(minutes=i*5),
                1.0 + i*0.01,
                1.1 + i*0.01,
                0.9 + i*0.01,
                1.05 + i*0.01,
                100
            )
            completed = feed.on_base_bar(ohlc)

            if 60 in completed:
                completed_count += 1

        # 应该完成 1 根 H1 bar
        assert completed_count == 1
        assert feed.get_buffer_size(60) == 1
        assert feed.get_bar_count(60) == 1

    def test_data_alignment_72_m5_bars(self):
        """测试 72 根 M5 bar (6 小时) 应完成 6 根 H1 bar"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(60)  # H1

        now = datetime.now()
        completed_count = 0

        for i in range(72):
            ohlc = OHLC(
                now + timedelta(minutes=i*5),
                1.0 + i*0.001,
                1.1 + i*0.001,
                0.9 + i*0.001,
                1.05 + i*0.001,
                100
            )
            completed = feed.on_base_bar(ohlc)

            if 60 in completed:
                completed_count += 1

        assert completed_count == 6  # 72 / 12 = 6 个 H1 bar
        assert feed.get_buffer_size(60) == 6
        assert feed.get_bar_count(60) == 6

    def test_ohlc_aggregation_correctness(self):
        """测试 OHLC 聚合正确性"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(60)

        now = datetime.now()

        # 构造 12 根特定的 M5 bar
        prices = [1.00, 1.01, 1.02, 1.01, 1.03, 1.02, 1.04, 1.03, 1.05, 1.04, 1.06, 1.05]

        for i, price in enumerate(prices):
            ohlc = OHLC(
                now + timedelta(minutes=i*5),
                open=price,
                high=price + 0.01,
                low=price - 0.01,
                close=price,
                volume=100 + i*10
            )
            feed.on_base_bar(ohlc)

        # 获取聚合的 H1 bar
        h1_bars = feed.get_bars(60, 1)
        assert len(h1_bars) == 1

        h1_bar = h1_bars[0]

        # 验证 OHLC
        assert h1_bar.open == prices[0]  # 第一根的 open
        assert h1_bar.close == prices[-1]  # 最后一根的 close
        assert h1_bar.high == max(prices) + 0.01  # 最大 high
        assert h1_bar.low == min(prices) - 0.01  # 最小 low
        assert h1_bar.volume == sum(100 + i*10 for i in range(12))  # 总成交量

    def test_multi_timeframe_hierarchy(self):
        """测试多层级周期: M5, H1, D1"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(5)   # M5
        feed.add_timeframe(60)  # H1 = 12 * M5
        feed.add_timeframe(1440)  # D1 = 288 * M5

        now = datetime.now()

        # 处理 288 根 M5 bar (1 整天)
        for i in range(288):
            ohlc = OHLC(
                now + timedelta(minutes=i*5),
                1.0 + i*0.001,
                1.1 + i*0.001,
                0.9 + i*0.001,
                1.05 + i*0.001,
                100
            )
            feed.on_base_bar(ohlc)

        # 验证各周期的 bar 数量
        assert feed.get_bar_count(5) == 288  # M5: 288 根
        assert feed.get_bar_count(60) == 24  # H1: 288 / 12 = 24 根
        assert feed.get_bar_count(1440) == 1  # D1: 288 / 288 = 1 根

    def test_is_timeframe_complete(self):
        """测试周期完成检测"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(60)

        now = datetime.now()

        # 处理 11 根 bar (H1 未完成)
        for i in range(11):
            ohlc = OHLC(now + timedelta(minutes=i*5), 1.0, 1.1, 0.9, 1.05, 100)
            completed = feed.on_base_bar(ohlc)
            assert 60 not in completed
            assert not feed.is_timeframe_complete(60)

        # 处理第 12 根 bar (H1 完成)
        ohlc = OHLC(now + timedelta(minutes=55), 1.0, 1.1, 0.9, 1.05, 100)
        completed = feed.on_base_bar(ohlc)
        assert 60 in completed
        assert feed.is_timeframe_complete(60)

    def test_get_status(self):
        """测试获取状态"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(5)
        feed.add_timeframe(60)

        now = datetime.now()
        for i in range(12):
            ohlc = OHLC(now + timedelta(minutes=i*5), 1.0, 1.1, 0.9, 1.05, 100)
            feed.on_base_bar(ohlc)

        status = feed.get_status()

        assert status['base_period'] == 5
        assert 'M5' in status['timeframes']
        assert 'H1' in status['timeframes']
        assert status['timeframes']['M5']['bar_count'] == 12
        assert status['timeframes']['H1']['bar_count'] == 1

    def test_reset(self):
        """测试重置"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(60)

        now = datetime.now()
        for i in range(12):
            ohlc = OHLC(now + timedelta(minutes=i*5), 1.0, 1.1, 0.9, 1.05, 100)
            feed.on_base_bar(ohlc)

        assert feed.get_bar_count(60) == 1

        feed.reset()

        assert feed.get_bar_count(60) == 0
        assert feed.get_buffer_size(60) == 0


class TestDataAlignmentEdgeCases:
    """数据对齐边界情况测试"""

    def test_buffer_circular_overwrite(self):
        """测试缓冲区循环覆盖"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(5, lookback=5)  # 只保留 5 根

        now = datetime.now()
        for i in range(10):
            ohlc = OHLC(now + timedelta(minutes=i*5), 1.0, 1.1, 0.9, 1.05, 100)
            feed.on_base_bar(ohlc)

        # 缓冲区只有 5 根，但计数是 10
        assert feed.get_buffer_size(5) == 5
        assert feed.get_bar_count(5) == 10

    def test_high_frequency_completion_detection(self):
        """测试高频周期完成检测"""
        feed = MultiTimeframeDataFeed(base_period=5)
        feed.add_timeframe(5)
        feed.add_timeframe(15)  # 3 * M5

        now = datetime.now()
        h1_completions = []

        for i in range(10):
            ohlc = OHLC(now + timedelta(minutes=i*5), 1.0, 1.1, 0.9, 1.05, 100)
            completed = feed.on_base_bar(ohlc)

            if 15 in completed:
                h1_completions.append(i)

        # M5 第 2, 5, 8 根时 (索引 2, 5, 8) M15 应完成
        # 使用 0-based 计数: 第 3 根 (i=2), 第 6 根 (i=5), 第 9 根 (i=8)
        assert h1_completions == [2, 5, 8]

    def test_empty_buffer_get_last(self):
        """测试空缓冲区 get_last"""
        config = TimeframeConfig(5, lookback=10)
        buffer = TimeframeBuffer(config)

        last = buffer.get_last(5)
        assert last == []

    def test_get_bars_nonexistent_period(self):
        """测试获取不存在周期的 bar"""
        feed = MultiTimeframeDataFeed(base_period=5)

        bars = feed.get_bars(999)  # 不存在的周期
        assert bars == []
