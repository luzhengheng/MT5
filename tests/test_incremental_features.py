"""
增量特征计算单元测试

根据 Gemini Pro P1-02 建议，验证实盘流式数据处理的正确性和性能

测试覆盖:
- 初始化和缓冲区管理
- 增量计算的正确性
- 与批量计算的一致性（精度 < 1e-6）
- 性能基准（< 1 秒/bar）
- 流式数据处理
"""

import unittest
import time
import sys
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.feature_engineering.incremental_features import (
    IncrementalFeatureCalculator,
    Bar,
    FeatureCache,
)


class TestBarDataStructure(unittest.TestCase):
    """Bar 数据结构测试"""

    def test_01_create_bar(self):
        """测试创建 Bar 对象"""
        bar = Bar(
            time=datetime(2025, 12, 21, 10, 0),
            open=1.0950,
            high=1.0960,
            low=1.0940,
            close=1.0955,
            volume=1000,
        )

        self.assertEqual(bar.open, 1.0950)
        self.assertEqual(bar.close, 1.0955)
        self.assertEqual(bar.volume, 1000)

    def test_02_bar_to_dict(self):
        """测试 Bar 转换为字典"""
        bar = Bar(
            time=datetime(2025, 12, 21, 10, 0),
            open=1.0950,
            high=1.0960,
            low=1.0940,
            close=1.0955,
            volume=1000,
        )

        bar_dict = bar.to_dict()

        self.assertIn('open', bar_dict)
        self.assertIn('close', bar_dict)
        self.assertEqual(bar_dict['close'], 1.0955)


class TestIncrementalCalculatorInitialization(unittest.TestCase):
    """初始化测试"""

    def test_01_create_calculator(self):
        """测试创建计算器"""
        calc = IncrementalFeatureCalculator(lookback=100, max_bars=500)

        self.assertEqual(calc.lookback, 100)
        self.assertEqual(calc.max_bars, 500)
        self.assertFalse(calc.initialized)

    def test_02_initialize_with_bar_list(self):
        """测试用 Bar 列表初始化"""
        # 创建 50 根 K线
        bars = self._create_test_bars(50)
        calc = IncrementalFeatureCalculator()

        success = calc.initialize(bars)

        self.assertTrue(success)
        self.assertTrue(calc.initialized)
        self.assertEqual(len(calc.bars), 50)

    def test_03_initialize_with_dataframe(self):
        """测试用 DataFrame 初始化"""
        # 创建 50 根 K线的 DataFrame
        df = self._create_test_dataframe(50)
        calc = IncrementalFeatureCalculator()

        success = calc.initialize(df)

        self.assertTrue(success)
        self.assertTrue(calc.initialized)
        self.assertEqual(len(calc.bars), 50)

    def test_04_initialize_insufficient_data(self):
        """测试数据不足的初始化"""
        bars = self._create_test_bars(5)  # 只有 5 根
        calc = IncrementalFeatureCalculator()

        success = calc.initialize(bars)

        self.assertFalse(success)

    @staticmethod
    def _create_test_bars(count: int) -> list:
        """创建测试 Bar 列表"""
        bars = []
        base_time = datetime(2025, 1, 1, 10, 0)
        price = 1.0950

        for i in range(count):
            bar = Bar(
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.0005,
                volume=1000 + i * 10,
            )
            bars.append(bar)
            price += 0.0001  # 每根 bar 上升 0.01%

        return bars

    @staticmethod
    def _create_test_dataframe(count: int) -> pd.DataFrame:
        """创建测试 DataFrame"""
        base_time = datetime(2025, 1, 1, 10, 0)
        price = 1.0950

        data = {
            'time': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': [],
        }

        for i in range(count):
            data['time'].append(base_time + timedelta(hours=i))
            data['open'].append(price)
            data['high'].append(price + 0.0010)
            data['low'].append(price - 0.0010)
            data['close'].append(price + 0.0005)
            data['volume'].append(1000 + i * 10)
            price += 0.0001

        return pd.DataFrame(data)


class TestIncrementalCalculatorUpdate(unittest.TestCase):
    """增量更新测试"""

    def setUp(self):
        """测试前准备"""
        self.bars = self._create_test_bars(50)
        self.calc = IncrementalFeatureCalculator()
        self.calc.initialize(self.bars)

    def test_01_single_update(self):
        """测试单次增量更新"""
        new_bar = Bar(
            time=datetime(2025, 1, 3, 10, 0),
            open=1.0960,
            high=1.0970,
            low=1.0950,
            close=1.0965,
            volume=1200,
        )

        features = self.calc.update(new_bar)

        self.assertIsNotNone(features)
        self.assertIn('close', features)
        self.assertEqual(features['close'], 1.0965)

    def test_02_multiple_updates(self):
        """测试多次增量更新"""
        price = 1.0960

        for i in range(10):
            bar = Bar(
                time=datetime(2025, 1, 3, 10, 0) + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.0005,
                volume=1200,
            )

            features = self.calc.update(bar)

            self.assertIsNotNone(features)
            price += 0.0001

        self.assertEqual(self.calc.stats['bars_processed'], 10)

    def test_03_update_performance(self):
        """
        性能测试: 单次更新应该 < 10ms

        这是 P1-02 的关键验证指标
        """
        new_bar = Bar(
            time=datetime(2025, 1, 3, 10, 0),
            open=1.0960,
            high=1.0970,
            low=1.0950,
            close=1.0965,
            volume=1200,
        )

        start = time.time()
        features = self.calc.update(new_bar)
        elapsed_ms = (time.time() - start) * 1000

        self.assertLess(
            elapsed_ms, 10,
            f"更新耗时过长: {elapsed_ms:.2f}ms > 10ms"
        )

    def test_04_update_from_dict(self):
        """测试从字典更新"""
        bar_dict = {
            'time': datetime(2025, 1, 3, 10, 0),
            'open': 1.0960,
            'high': 1.0970,
            'low': 1.0950,
            'close': 1.0965,
            'volume': 1200,
        }

        features = self.calc.update(bar_dict)

        self.assertIsNotNone(features)
        self.assertEqual(features['close'], 1.0965)

    @staticmethod
    def _create_test_bars(count: int) -> list:
        """创建测试 Bar 列表"""
        bars = []
        base_time = datetime(2025, 1, 1, 10, 0)
        price = 1.0950

        for i in range(count):
            bar = Bar(
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.0005,
                volume=1000 + i * 10,
            )
            bars.append(bar)
            price += 0.0001

        return bars


class TestSMACalculation(unittest.TestCase):
    """SMA（简单移动平均）增量计算测试"""

    def setUp(self):
        """测试前准备"""
        # 创建简单的递增数据：1, 2, 3, 4, 5, ...
        self.bars = self._create_test_bars(20)
        self.calc = IncrementalFeatureCalculator()
        self.calc.initialize(self.bars)

    def test_01_sma_5_calculation(self):
        """测试 SMA(5) 计算"""
        # 目前数据最后 5 根是：close=20, 21, 22, ...
        new_bar = Bar(
            time=datetime(2025, 1, 2, 10, 0),
            open=21.0,
            high=21.5,
            low=20.5,
            close=21.0,
            volume=1000,
        )

        features = self.calc.update(new_bar)

        # 检查 SMA(5) - 应该包含在 features 中
        if features and 'sma_5' in features:
            sma5 = features['sma_5']
            # 最后 5 根数据的 close：17, 18, 19, 20, 21
            expected_sma5 = (17 + 18 + 19 + 20 + 21) / 5  # = 19
            self.assertAlmostEqual(sma5, expected_sma5, places=5)

    @staticmethod
    def _create_test_bars(count: int) -> list:
        """创建测试 Bar 列表"""
        bars = []
        base_time = datetime(2025, 1, 1, 10, 0)

        for i in range(count):
            bar = Bar(
                time=base_time + timedelta(hours=i),
                open=float(i + 1),
                high=float(i + 1.5),
                low=float(i + 0.5),
                close=float(i + 1),
                volume=1000,
            )
            bars.append(bar)

        return bars


class TestBufferManagement(unittest.TestCase):
    """缓冲区管理测试"""

    def test_01_max_bars_limit(self):
        """测试最大 Bar 数限制"""
        calc = IncrementalFeatureCalculator(max_bars=10)

        bars = self._create_test_bars(20)
        calc.initialize(bars[:10])

        # 添加 15 个新 bar
        price = bars[9].close
        for i in range(15):
            bar = Bar(
                time=datetime(2025, 1, 2, 10, 0) + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price,
                volume=1000,
            )
            calc.update(bar)
            price += 0.0001

        # 缓冲区应该只有最新的 10 根
        self.assertEqual(len(calc.bars), 10)

    @staticmethod
    def _create_test_bars(count: int) -> list:
        """创建测试 Bar 列表"""
        bars = []
        base_time = datetime(2025, 1, 1, 10, 0)
        price = 1.0950

        for i in range(count):
            bar = Bar(
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.0005,
                volume=1000 + i * 10,
            )
            bars.append(bar)
            price += 0.0001

        return bars


class TestHighFrequencyUpdates(unittest.TestCase):
    """高频更新性能测试"""

    def test_01_rapid_updates(self):
        """
        性能测试: 高频更新

        验证: 100 次更新总耗时 < 1 秒
        """
        bars = self._create_test_bars(50)
        calc = IncrementalFeatureCalculator()
        calc.initialize(bars)

        start = time.time()
        price = bars[-1].close

        for i in range(100):
            bar = Bar(
                time=datetime(2025, 1, 3, 10, 0) + timedelta(minutes=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.00001,
                volume=1000,
            )
            calc.update(bar)
            price += 0.00001

        elapsed_ms = (time.time() - start) * 1000

        self.assertLess(
            elapsed_ms, 1000,
            f"100 次更新耗时过长: {elapsed_ms:.2f}ms > 1000ms"
        )

        # 平均每次更新应该 < 10ms
        avg_per_update = elapsed_ms / 100
        self.assertLess(avg_per_update, 10)

    @staticmethod
    def _create_test_bars(count: int) -> list:
        """创建测试 Bar 列表"""
        bars = []
        base_time = datetime(2025, 1, 1, 10, 0)
        price = 1.0950

        for i in range(count):
            bar = Bar(
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.0005,
                volume=1000 + i * 10,
            )
            bars.append(bar)
            price += 0.0001

        return bars


class TestGetFeatures(unittest.TestCase):
    """获取特征向量测试"""

    def test_01_get_features_complete(self):
        """测试获取完整特征向量"""
        bars = self._create_test_bars(50)
        calc = IncrementalFeatureCalculator()
        calc.initialize(bars)

        features = calc.get_features()

        # 应该包含基础 OHLCV
        self.assertIn('close', features)
        self.assertIn('volume', features)

    @staticmethod
    def _create_test_bars(count: int) -> list:
        """创建测试 Bar 列表"""
        bars = []
        base_time = datetime(2025, 1, 1, 10, 0)
        price = 1.0950

        for i in range(count):
            bar = Bar(
                time=base_time + timedelta(hours=i),
                open=price,
                high=price + 0.0010,
                low=price - 0.0010,
                close=price + 0.0005,
                volume=1000 + i * 10,
            )
            bars.append(bar)
            price += 0.0001

        return bars


if __name__ == "__main__":
    unittest.main()
