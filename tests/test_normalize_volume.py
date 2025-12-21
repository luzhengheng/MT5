"""
测试 MT5Bridge.normalize_volume() 函数

该函数确保订单量符合MT5合约规范：
- volume >= volume_min（最小手数）
- (volume - volume_min) % volume_step == 0（按步长递增）
- volume <= volume_max（最大手数）

基于Gemini Pro审查建议的P0优先级改进。
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 在导入MT5Bridge之前，mock MetaTrader5模块
sys.modules['MetaTrader5'] = MagicMock()

import unittest
import logging

from src.connection.mt5_bridge import MT5Bridge, MT5OrderError

logger = logging.getLogger(__name__)


class TestNormalizeVolume(unittest.TestCase):
    """测试 normalize_volume 函数的各种场景"""

    def setUp(self):
        """测试前准备"""
        self.bridge = MT5Bridge(symbol="EURUSD")

    @patch('src.connection.mt5_bridge.mt5')
    def test_01_normal_volume_no_adjustment_needed(self, mock_mt5):
        """
        测试：标准情况 - 手数无需调整

        场景：
        - 请求手数: 1.0
        - 最小手数: 0.01
        - 步长: 0.01
        - 最大手数: 100.0

        预期：返回 1.0（无调整）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 100.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 1.0)

        self.assertEqual(result, 1.0)
        logger.info("✅ 测试通过：标准情况下手数无需调整")

    @patch('src.connection.mt5_bridge.mt5')
    def test_02_volume_below_minimum(self, mock_mt5):
        """
        测试：手数低于最小值

        场景：
        - 请求手数: 0.001
        - 最小手数: 0.01
        - 步长: 0.01

        预期：返回 0.0（拒绝下单）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 100.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 0.001)

        self.assertEqual(result, 0.0)
        logger.info("✅ 测试通过：低于最小值的手数返回0.0")

    @patch('src.connection.mt5_bridge.mt5')
    def test_03_volume_needs_step_adjustment(self, mock_mt5):
        """
        测试：手数需按步长对齐

        场景：
        - 请求手数: 1.15
        - 最小手数: 0.01
        - 步长: 0.1（Backtrader可能计算出的非标准值）
        - 最大手数: 100.0

        预期：返回 1.1（向下对齐到最近的步长）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.1
        mock_symbol_info.volume_max = 100.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 1.15)

        # int(1.15 / 0.1) * 0.1 = int(11.5) * 0.1 = 11 * 0.1 = 1.1
        self.assertEqual(result, 1.1)
        logger.info("✅ 测试通过：手数按步长对齐（1.15 → 1.1）")

    @patch('src.connection.mt5_bridge.mt5')
    def test_04_volume_exceeds_maximum(self, mock_mt5):
        """
        测试：手数超过最大限制

        场景：
        - 请求手数: 150.0
        - 最小手数: 0.01
        - 步长: 0.01
        - 最大手数: 100.0

        预期：返回 100.0（限制到最大值）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 100.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 150.0)

        self.assertEqual(result, 100.0)
        logger.info("✅ 测试通过：超过最大值的手数被限制（150.0 → 100.0）")

    @patch('src.connection.mt5_bridge.mt5')
    def test_05_volume_with_zero_max_limit(self, mock_mt5):
        """
        测试：最大手数为0（无限制）

        场景：
        - 请求手数: 500.5
        - 最小手数: 0.01
        - 步长: 0.1
        - 最大手数: 0.0（表示无限制）

        预期：返回 500.5（按步长对齐但不受最大值限制）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.1
        mock_symbol_info.volume_max = 0.0  # 0表示无限制

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 500.5)

        # int(500.5 / 0.1) * 0.1 = 5005 * 0.1 = 500.5
        self.assertEqual(result, 500.5)
        logger.info("✅ 测试通过：无最大限制的手数正确处理（500.5）")

    @patch('src.connection.mt5_bridge.mt5')
    def test_06_floating_point_precision(self, mock_mt5):
        """
        测试：浮点数精度处理

        场景：
        - 请求手数: 1.234567（ML模型计算出的精度值）
        - 最小手数: 0.01
        - 步长: 0.01
        - 最大手数: 100.0

        预期：返回 1.23（四舍五入到2位小数，防止浮点精度问题）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 100.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 1.234567)

        # int(1.234567 / 0.01) * 0.01 = 123 * 0.01 = 1.23
        # float(f"{1.23:.2f}") = 1.23
        self.assertEqual(result, 1.23)
        logger.info("✅ 测试通过：浮点精度正确处理（1.234567 → 1.23）")

    @patch('src.connection.mt5_bridge.mt5')
    def test_07_zero_step_edge_case(self, mock_mt5):
        """
        测试：步长为0的边界情况

        场景：
        - 请求手数: 1.5
        - 最小手数: 0.01
        - 步长: 0.0（异常情况，不应该出现但需要处理）
        - 最大手数: 100.0

        预期：使用原值1.5（记录警告）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.0  # 异常值
        mock_symbol_info.volume_max = 100.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 1.5)

        self.assertEqual(result, 1.5)
        logger.info("✅ 测试通过：步长为0时使用原值（1.5）")

    @patch('src.connection.mt5_bridge.mt5')
    def test_08_symbol_select_fails(self, mock_mt5):
        """
        测试：品种选择失败

        场景：
        - symbol_select 返回 False（品种不存在或账户不支持）

        预期：抛出 MT5OrderError 异常
        """
        mock_mt5.symbol_select.return_value = False

        with self.assertRaises(MT5OrderError):
            self.bridge.normalize_volume("INVALID_SYMBOL", 1.0)

        logger.info("✅ 测试通过：品种选择失败时抛出异常")

    @patch('src.connection.mt5_bridge.mt5')
    def test_09_symbol_info_not_found(self, mock_mt5):
        """
        测试：无法获取品种信息

        场景：
        - symbol_info 返回 None（品种不存在或数据缺失）

        预期：抛出 MT5OrderError 异常
        """
        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = None

        with self.assertRaises(MT5OrderError):
            self.bridge.normalize_volume("EURUSD", 1.0)

        logger.info("✅ 测试通过：无法获取品种信息时抛出异常")

    @patch('src.connection.mt5_bridge.mt5')
    def test_10_real_world_forex_eurusd(self, mock_mt5):
        """
        测试：真实世界场景 - 外汇EURUSD

        真实MT5规格（典型值）：
        - volume_min: 0.01（0.01手 = 1000单位）
        - volume_step: 0.01
        - volume_max: 10000.0

        场景：
        - Backtrader/KellySizer计算出 0.847 手（ML模型输出）
        - 需要对齐到 0.84 手

        预期：返回 0.84（符合MT5规范）
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 10000.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("EURUSD", 0.847)

        # int(0.847 / 0.01) * 0.01 = 84 * 0.01 = 0.84
        self.assertEqual(result, 0.84)
        logger.info("✅ 测试通过：真实EURUSD规范化（0.847 → 0.84）")

    @patch('src.connection.mt5_bridge.mt5')
    def test_11_real_world_futures_es(self, mock_mt5):
        """
        测试：真实世界场景 - 期货ES（标普500微型合约）

        真实MT5规格：
        - volume_min: 0.01（微型合约）
        - volume_step: 0.01
        - volume_max: 500.0

        场景：
        - 计算出 2.345 合约
        - 需要对齐到 2.34

        预期：返回 2.34
        """
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 500.0

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info

        result = self.bridge.normalize_volume("ES", 2.345)

        self.assertEqual(result, 2.34)
        logger.info("✅ 测试通过：期货ES规范化（2.345 → 2.34）")


class TestNormalizeVolumeIntegration(unittest.TestCase):
    """集成测试：验证normalize_volume在send_order中的正确使用"""

    @patch('src.connection.mt5_bridge.mt5')
    def test_send_order_with_volume_normalization(self, mock_mt5):
        """
        集成测试：send_order调用normalize_volume

        验证流程：
        1. send_order接收一个volume
        2. 调用normalize_volume进行规范化
        3. 使用规范化的volume进行下单
        """
        bridge = MT5Bridge(symbol="EURUSD")
        bridge.is_connected = True

        # Mock MT5方法
        mock_symbol_info = Mock()
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_step = 0.01
        mock_symbol_info.volume_max = 100.0

        mock_tick = Mock()
        mock_tick.ask = 1.0950

        mock_result = Mock()
        mock_result.retcode = 10009  # TRADE_RETCODE_DONE
        mock_result.order = 12345

        mock_mt5.symbol_select.return_value = True
        mock_mt5.symbol_info.return_value = mock_symbol_info
        mock_mt5.symbol_info_tick.return_value = mock_tick
        mock_mt5.order_send.return_value = mock_result
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.ORDER_TIME_GTC = 0
        mock_mt5.ORDER_FILLING_FOK = 1

        from src.connection.mt5_bridge import OrderInfo, OrderType

        order = OrderInfo(
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=1.234567,  # 需要规范化
            price=0.0,
            comment="Test order with volume normalization"
        )

        success, ticket = bridge.send_order(order)

        # 验证
        self.assertTrue(success)
        self.assertEqual(ticket, 12345)
        # 验证order.volume已被规范化
        self.assertEqual(order.volume, 1.23)
        logger.info("✅ 集成测试通过：send_order正确规范化volume（1.234567 → 1.23）")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    unittest.main()
