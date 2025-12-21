"""
P2-04 测试套件 - MT5 Volume Adapter

测试目标：
1. 验证 Backtrader size 到 MT5 lots 的转换
2. 验证手数规范化算法
3. 验证 MT5 约束的应用 (min, max, step)
4. 验证浮点精度处理
5. 验证与 KellySizer 的集成

Gemini Pro P0 问题 #2:
"Backtrader 计算出的 size 通常是'单位数量'（如 10000 欧元），
 而 MT5 订单需要'手数'（Lots，如 0.1 手）。"

P2-04 解决方案:
- MT5SymbolInfo: 交易品种规范信息
- MT5VolumeAdapter: 精确的手数规范化
"""

import pytest
import math
from src.mt5_bridge.volume_adapter import (
    MT5SymbolInfo,
    MT5VolumeAdapter,
    create_eurusd_adapter,
    create_xauusd_adapter
)


class TestMT5SymbolInfo:
    """测试 MT5 交易品种信息类"""

    def test_eurusd_creation(self):
        """测试 EURUSD 品种信息创建"""
        symbol_info = MT5SymbolInfo(
            symbol="EURUSD",
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.00001,
            trade_tick_size=0.00001
        )

        assert symbol_info.symbol == "EURUSD"
        assert symbol_info.contract_size == 100000.0
        assert symbol_info.volume_min == 0.01
        assert symbol_info.volume_step == 0.01

    def test_xauusd_creation(self):
        """测试 XAUUSD 品种信息创建"""
        symbol_info = MT5SymbolInfo(
            symbol="XAUUSD",
            contract_size=100.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.01,
            trade_tick_size=0.01
        )

        assert symbol_info.symbol == "XAUUSD"
        assert symbol_info.contract_size == 100.0

    def test_invalid_contract_size(self):
        """测试无效的合约大小"""
        with pytest.raises(ValueError, match="contract_size 必须为正数"):
            MT5SymbolInfo(
                symbol="TEST",
                contract_size=-100000.0,
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                point=0.00001,
                trade_tick_size=0.00001
            )

    def test_invalid_volume_max(self):
        """测试无效的最大手数"""
        with pytest.raises(ValueError, match="volume_max.*必须"):
            MT5SymbolInfo(
                symbol="TEST",
                contract_size=100000.0,
                volume_min=0.01,
                volume_max=0.005,  # 小于 volume_min
                volume_step=0.01,
                point=0.00001,
                trade_tick_size=0.00001
            )


class TestMT5VolumeAdapterBasics:
    """测试 MT5 手数适配器的基础功能"""

    def setup_method(self):
        """为每个测试设置环境"""
        self.eurusd_info = MT5SymbolInfo(
            symbol="EURUSD",
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.00001,
            trade_tick_size=0.00001
        )
        self.adapter = MT5VolumeAdapter(self.eurusd_info)

    def test_backtrader_size_to_lots_basic(self):
        """测试基础的 size 到 lots 转换"""
        # 10,000 EUR → 0.1 lot
        lots = self.adapter.backtrader_size_to_lots(10000)
        assert lots == 0.1, f"应该转换为 0.1 lot，得到 {lots}"

        # 50,000 EUR → 0.5 lot
        lots = self.adapter.backtrader_size_to_lots(50000)
        assert lots == 0.5

        # 100,000 EUR → 1.0 lot
        lots = self.adapter.backtrader_size_to_lots(100000)
        assert lots == 1.0

    def test_backtrader_size_to_lots_zero(self):
        """测试零大小的处理"""
        assert self.adapter.backtrader_size_to_lots(0) == 0.0
        assert self.adapter.backtrader_size_to_lots(-100) == 0.0

    def test_normalize_volume_basic(self):
        """测试基本的手数规范化"""
        # 0.123 → 0.12 (向下取整到 0.01)
        normalized = self.adapter.normalize_volume(0.123)
        assert normalized == 0.12, f"应该规范化为 0.12，得到 {normalized}"

        # 0.115 → 0.11
        normalized = self.adapter.normalize_volume(0.115)
        assert normalized == 0.11

        # 1.999 → 1.99
        normalized = self.adapter.normalize_volume(1.999)
        assert normalized == 1.99

    def test_normalize_volume_exact_multiple(self):
        """测试恰好是 volume_step 的倍数"""
        # 0.10 → 0.10 (恰好符合)
        assert self.adapter.normalize_volume(0.10) == 0.10

        # 0.50 → 0.50
        assert self.adapter.normalize_volume(0.50) == 0.50

        # 1.00 → 1.00
        assert self.adapter.normalize_volume(1.00) == 1.00

    def test_normalize_volume_below_minimum(self):
        """测试低于最小手数"""
        # 0.005 < 0.01 (volume_min) → 0.0
        assert self.adapter.normalize_volume(0.005) == 0.0

        # 0.009 < 0.01 → 0.0
        assert self.adapter.normalize_volume(0.009) == 0.0


class TestMT5VolumeAdapterConstraints:
    """测试 MT5 约束的应用"""

    def setup_method(self):
        """为每个测试设置环境"""
        self.eurusd_info = MT5SymbolInfo(
            symbol="EURUSD",
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.00001,
            trade_tick_size=0.00001
        )
        self.adapter = MT5VolumeAdapter(self.eurusd_info)

    def test_normalize_respects_minimum(self):
        """验证规范化尊重最小手数"""
        # 0.001 < volume_min (0.01) → 0.0
        assert self.adapter.normalize_volume(0.001) == 0.0

    def test_normalize_respects_maximum(self):
        """验证规范化尊重最大手数"""
        # 150.0 > volume_max (100.0) → 100.0
        normalized = self.adapter.normalize_volume(150.0)
        assert normalized == 100.0, f"应该限制为 100.0，得到 {normalized}"

        # 200.5 > 100.0 → 100.0
        assert self.adapter.normalize_volume(200.5) == 100.0

    def test_normalize_respects_step(self):
        """验证规范化尊重步进"""
        # volume_step = 0.01
        # 0.127 → 0.12 (向下到最近的步进)
        assert self.adapter.normalize_volume(0.127) == 0.12

        # 0.999 → 0.99
        assert self.adapter.normalize_volume(0.999) == 0.99

    def test_volume_step_small(self):
        """测试小的 volume_step"""
        info = MT5SymbolInfo(
            symbol="TEST",
            contract_size=100000.0,
            volume_min=0.001,
            volume_max=100.0,
            volume_step=0.001,  # 更小的步进
            point=0.00001,
            trade_tick_size=0.00001
        )
        adapter = MT5VolumeAdapter(info)

        # 0.0127 → 0.012 (步进为 0.001)
        normalized = adapter.normalize_volume(0.0127)
        assert normalized == 0.012


class TestMT5VolumeAdapterFullConversion:
    """测试完整的 Backtrader → MT5 转换流程"""

    def setup_method(self):
        """为每个测试设置环境"""
        self.eurusd_adapter = create_eurusd_adapter()

    def test_bt_size_to_mt5_lots_basic(self):
        """测试基础的完整转换"""
        # 10,000 EUR → 0.1 lot
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(10000)
        assert lots == 0.1

        # 50,000 EUR → 0.5 lot
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(50000)
        assert lots == 0.5

    def test_bt_size_to_mt5_lots_with_fractional(self):
        """测试包含小数的转换"""
        # 10,500 EUR → 0.105 raw → 0.10 normalized
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(10500)
        assert lots == 0.10, f"应该规范化为 0.10，得到 {lots}"

        # 10,750 EUR → 0.1075 raw → 0.10 normalized
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(10750)
        assert lots == 0.10

    def test_bt_size_to_mt5_lots_large_size(self):
        """测试大额交易"""
        # 5,000,000 EUR → 50.0 lot
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(5000000)
        assert lots == 50.0

        # 10,500,000 EUR → 105.0 raw → 100.0 normalized (受 volume_max 限制)
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(10500000)
        assert lots == 100.0

    def test_bt_size_to_mt5_lots_small_size(self):
        """测试小额交易"""
        # 500 EUR → 0.005 lot < volume_min (0.01) → 0.0
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(500)
        assert lots == 0.0

        # 1,000 EUR → 0.01 lot (恰好符合最小值)
        lots = self.eurusd_adapter.bt_size_to_mt5_lots(1000)
        assert lots == 0.01


class TestMT5VolumeAdapterValidation:
    """测试手数验证功能"""

    def setup_method(self):
        """为每个测试设置环境"""
        self.adapter = create_eurusd_adapter()

    def test_validate_volume_valid(self):
        """测试有效的手数"""
        is_valid, error = self.adapter.validate_volume(0.1)
        assert is_valid is True
        assert error is None

        is_valid, error = self.adapter.validate_volume(1.0)
        assert is_valid is True

        is_valid, error = self.adapter.validate_volume(100.0)
        assert is_valid is True

    def test_validate_volume_below_minimum(self):
        """测试低于最小值"""
        is_valid, error = self.adapter.validate_volume(0.005)
        assert is_valid is False
        assert "低于最小值" in error

    def test_validate_volume_above_maximum(self):
        """测试超过最大值"""
        is_valid, error = self.adapter.validate_volume(150.0)
        assert is_valid is False
        assert "超过最大值" in error

    def test_validate_volume_not_step_aligned(self):
        """测试不符合步进的手数"""
        is_valid, error = self.adapter.validate_volume(0.115)
        assert is_valid is False
        assert "不符合步进" in error

    def test_validate_volume_floating_point_tolerance(self):
        """测试浮点精度容忍度"""
        # 0.01 + 1e-9 应该仍然被认为是有效的（在容忍度内）
        is_valid, error = self.adapter.validate_volume(0.01 + 1e-9)
        assert is_valid is True


class TestMT5DifferentSymbols:
    """测试不同交易品种的适配"""

    def test_eurusd_adapter_factory(self):
        """测试 EURUSD 工厂函数"""
        adapter = create_eurusd_adapter()
        assert adapter.symbol_info.symbol == "EURUSD"
        assert adapter.symbol_info.contract_size == 100000.0

        # 10,000 EUR → 0.1 lot
        lots = adapter.bt_size_to_mt5_lots(10000)
        assert lots == 0.1

    def test_xauusd_adapter_factory(self):
        """测试 XAUUSD (黄金) 工厂函数"""
        adapter = create_xauusd_adapter()
        assert adapter.symbol_info.symbol == "XAUUSD"
        assert adapter.symbol_info.contract_size == 100.0

        # 10 ounces → 0.1 lot (contract_size = 100)
        lots = adapter.bt_size_to_mt5_lots(10)
        assert lots == 0.1

        # 1,000 ounces → 10.0 lot
        lots = adapter.bt_size_to_mt5_lots(1000)
        assert lots == 10.0

    def test_custom_symbol(self):
        """测试自定义品种"""
        # 自定义品种：纳斯达克 100 指数
        symbol_info = MT5SymbolInfo(
            symbol="NQ",
            contract_size=20.0,
            volume_min=1.0,
            volume_max=1000.0,
            volume_step=1.0,
            point=0.25,
            trade_tick_size=0.25
        )
        adapter = MT5VolumeAdapter(symbol_info)

        # 100 contract → 5.0 lot
        lots = adapter.bt_size_to_mt5_lots(100)
        assert lots == 5.0

        # 105 contract → 5.25 raw → 5.0 normalized
        lots = adapter.bt_size_to_mt5_lots(105)
        assert lots == 5.0


class TestMT5FloatingPointPrecision:
    """测试浮点精度处理"""

    def setup_method(self):
        """为每个测试设置环境"""
        self.adapter = create_eurusd_adapter()

    def test_floating_point_precision_issue(self):
        """测试典型的浮点精度问题"""
        # 0.1 + 0.2 = 0.30000000000000004 (浮点精度问题)
        raw_lots = 0.1 + 0.2
        normalized = self.adapter.normalize_volume(raw_lots)
        # 应该返回 0.3 而不是 0.30000000000000004
        assert abs(normalized - 0.3) < 1e-10
        assert normalized == 0.3

    def test_decimal_places_calculation(self):
        """测试小数位数计算"""
        assert MT5VolumeAdapter._get_decimal_places(0.01) == 2
        assert MT5VolumeAdapter._get_decimal_places(0.001) == 3
        assert MT5VolumeAdapter._get_decimal_places(0.1) == 1
        assert MT5VolumeAdapter._get_decimal_places(1.0) == 0

    def test_precise_normalization_sequence(self):
        """测试一系列数字的精确规范化"""
        test_cases = [
            (0.011, 0.01),   # 向下取整
            (0.019, 0.01),
            (0.021, 0.02),
            (0.099, 0.09),
            (0.101, 0.10),
            (1.234, 1.23),
        ]

        for raw, expected in test_cases:
            result = self.adapter.normalize_volume(raw)
            assert result == expected, \
                f"normalize({raw}) 应该返回 {expected}，得到 {result}"


class TestMT5IntegrationWithKellySizer:
    """测试与 KellySizer 的集成"""

    def test_kelly_position_to_mt5_lots(self):
        """测试 Kelly 计算的仓位转换为 MT5 手数"""
        adapter = create_eurusd_adapter()

        # 假设 Kelly 计算出的仓位大小是 25,000 EUR
        kelly_position = 25000

        # 转换为 MT5 手数
        lots = adapter.bt_size_to_mt5_lots(kelly_position)

        # 25,000 EUR → 0.25 lot
        assert lots == 0.25, f"Kelly 仓位应该转换为 0.25 lot，得到 {lots}"

    def test_kelly_with_constraint_checking(self):
        """测试 Kelly 仓位经过约束检查"""
        adapter = create_eurusd_adapter()

        # Kelly 计算出的大仓位：500,000 EUR
        kelly_position = 500000
        lots = adapter.bt_size_to_mt5_lots(kelly_position)

        # 500,000 EUR → 5.0 lot (未超过最大值 100.0)
        assert lots == 5.0

        # Kelly 计算出的超大仓位：10,500,000 EUR
        huge_position = 10500000
        lots = adapter.bt_size_to_mt5_lots(huge_position)

        # 10,500,000 EUR → 105.0 raw → 100.0 normalized (受最大值限制)
        assert lots == 100.0, f"超大仓位应该被限制在 100.0，得到 {lots}"

    def test_kelly_zero_position(self):
        """测试 Kelly 返回零仓位"""
        adapter = create_eurusd_adapter()

        # Kelly 没有信号，返回 0
        lots = adapter.bt_size_to_mt5_lots(0)
        assert lots == 0.0

        # Kelly 计算出的极小仓位：100 EUR
        small_position = 100
        lots = adapter.bt_size_to_mt5_lots(small_position)

        # 100 EUR → 0.001 lot < volume_min (0.01) → 0.0
        assert lots == 0.0


class TestP204EdgeCases:
    """测试 P2-04 的边界情况"""

    def test_rounding_down_behavior(self):
        """验证向下取整的行为"""
        adapter = create_eurusd_adapter()

        # Gemini 建议的算法: floor(raw_lots / volume_step) * volume_step
        # 这应该导致向下取整，而不是四舍五入

        # 0.149 → floor(14.9) × 0.01 = 14 × 0.01 = 0.14
        assert adapter.normalize_volume(0.149) == 0.14

        # 0.199 → floor(19.9) × 0.01 = 19 × 0.01 = 0.19
        assert adapter.normalize_volume(0.199) == 0.19

        # 0.999 → floor(99.9) × 0.01 = 99 × 0.01 = 0.99
        assert adapter.normalize_volume(0.999) == 0.99

    def test_boundary_at_minimum(self):
        """测试边界情况：恰好在最小值"""
        adapter = create_eurusd_adapter()

        # 恰好等于 volume_min
        is_valid, error = adapter.validate_volume(0.01)
        assert is_valid is True

        # 低于 volume_min
        is_valid, error = adapter.validate_volume(0.009)
        assert is_valid is False

    def test_boundary_at_maximum(self):
        """测试边界情况：恰好在最大值"""
        adapter = create_eurusd_adapter()

        # 恰好等于 volume_max
        is_valid, error = adapter.validate_volume(100.0)
        assert is_valid is True

        # 超过 volume_max
        is_valid, error = adapter.validate_volume(100.01)
        assert is_valid is False


# ============================================================================
# 执行所有测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
