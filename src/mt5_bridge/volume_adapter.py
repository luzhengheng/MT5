"""
MT5 Volume Adapter - 手数规范化模块

核心功能：
1. 将 Backtrader 计算的 size (单位数量) 转换为 MT5 的 lots (手数)
2. 应用 MT5 规范约束 (volume_min, volume_step, volume_max)
3. 确保订单符合 MT5 要求，避免下单失败

P2-04 改进 (2025-12-21):
- 解决 Gemini Pro P0 问题 #2
- 实现精确的手数规范化算法
- 支持所有 MT5 交易品种

Gemini Pro 审查引用:
> "Backtrader 计算出的 size 通常是'单位数量'（如 10000 欧元），
>  而 MT5 订单需要'手数'（Lots，如 0.1 手）。"
"""

import logging
import math
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MT5SymbolInfo:
    """
    MT5 交易品种信息

    属性：
        symbol: 交易品种代码 (如 "EURUSD", "XAUUSD")
        contract_size: 合约大小 (如外汇通常为 100,000)
        volume_min: 最小交易手数 (如 0.01)
        volume_max: 最大交易手数 (如 100.0)
        volume_step: 手数步进 (如 0.01)
        point: 最小价格变动 (如 0.00001 for EURUSD)
        trade_tick_size: 交易报价步进 (如 0.00001)

    示例 (EURUSD):
        contract_size = 100,000
        volume_min = 0.01
        volume_max = 100.0
        volume_step = 0.01
        point = 0.00001
    """
    symbol: str
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    point: float
    trade_tick_size: float

    def __post_init__(self):
        """验证参数有效性"""
        if self.contract_size <= 0:
            raise ValueError(f"contract_size 必须为正数: {self.contract_size}")
        if self.volume_min <= 0:
            raise ValueError(f"volume_min 必须为正数: {self.volume_min}")
        if self.volume_step <= 0:
            raise ValueError(f"volume_step 必须为正数: {self.volume_step}")
        if self.volume_max < self.volume_min:
            raise ValueError(
                f"volume_max ({self.volume_max}) 必须 >= volume_min ({self.volume_min})"
            )

    @staticmethod
    def from_mt5(mt5_symbol_info) -> 'MT5SymbolInfo':
        """
        从 MT5 的 SymbolInfo 对象创建适配器

        Args:
            mt5_symbol_info: MetaTrader5.SymbolInfo 对象

        Returns:
            MT5SymbolInfo: 适配器对象
        """
        return MT5SymbolInfo(
            symbol=mt5_symbol_info.name,
            contract_size=mt5_symbol_info.trade_contract_size,
            volume_min=mt5_symbol_info.volume_min,
            volume_max=mt5_symbol_info.volume_max,
            volume_step=mt5_symbol_info.volume_step,
            point=mt5_symbol_info.point,
            trade_tick_size=mt5_symbol_info.trade_tick_size
        )


class MT5VolumeAdapter:
    """
    MT5 手数适配器

    功能：
    1. 将 Backtrader size (单位数) 转换为 MT5 lots (手数)
    2. 规范化手数，确保符合 MT5 规范
    3. 应用最小/最大约束

    P2-04 核心算法 (Gemini Pro 建议):
        normalized_lots = floor(raw_lots / volume_step) * volume_step

    使用示例：
        >>> symbol_info = MT5SymbolInfo(
        ...     symbol="EURUSD",
        ...     contract_size=100000,
        ...     volume_min=0.01,
        ...     volume_max=100.0,
        ...     volume_step=0.01,
        ...     point=0.00001,
        ...     trade_tick_size=0.00001
        ... )
        >>> adapter = MT5VolumeAdapter(symbol_info)
        >>> lots = adapter.normalize_volume(10000)  # 10,000 欧元
        >>> print(lots)
        0.1  # 0.1 手 = 10,000 EUR (100,000 × 0.1)
    """

    def __init__(self, symbol_info: MT5SymbolInfo):
        """
        初始化适配器

        Args:
            symbol_info: MT5 交易品种信息
        """
        self.symbol_info = symbol_info
        logger.info(
            f"初始化 MT5VolumeAdapter - {symbol_info.symbol}: "
            f"contract_size={symbol_info.contract_size}, "
            f"volume_min={symbol_info.volume_min}, "
            f"volume_step={symbol_info.volume_step}"
        )

    def backtrader_size_to_lots(self, bt_size: float, current_price: float = 1.0) -> float:
        """
        将 Backtrader size (单位数) 转换为 MT5 lots (手数)

        Args:
            bt_size: Backtrader 计算的仓位大小 (单位数)
            current_price: 当前价格 (用于某些资产类型，如股票)

        Returns:
            float: MT5 手数 (未规范化)

        示例:
            对于 EURUSD (contract_size=100,000):
            - bt_size = 10,000 EUR → lots = 0.1
            - bt_size = 50,000 EUR → lots = 0.5
        """
        if bt_size <= 0:
            return 0.0

        # 计算原始手数
        # lots = bt_size / contract_size
        raw_lots = bt_size / self.symbol_info.contract_size

        logger.debug(
            f"转换 Backtrader size → MT5 lots: "
            f"bt_size={bt_size:.2f}, contract_size={self.symbol_info.contract_size}, "
            f"raw_lots={raw_lots:.4f}"
        )

        return raw_lots

    def normalize_volume(self, raw_lots: float) -> float:
        """
        规范化手数，确保符合 MT5 要求

        核心算法 (Gemini Pro 建议):
            1. 向下取整到最近的 volume_step
            2. 应用 volume_min 约束
            3. 应用 volume_max 约束
            4. 防止浮点精度问题

        Args:
            raw_lots: 原始手数 (可能不符合规范)

        Returns:
            float: 规范化后的手数 (符合 MT5 要求)

        示例:
            volume_step = 0.01
            - raw_lots = 0.123 → normalized = 0.12
            - raw_lots = 0.005 → normalized = 0.00 (低于 volume_min)
            - raw_lots = 150.0 → normalized = 100.0 (超过 volume_max)
        """
        if raw_lots <= 0:
            logger.debug("手数 <= 0，返回 0.0")
            return 0.0

        # 步骤 1: 向下取整到最近的 volume_step
        # 使用 Gemini Pro 建议的算法
        steps = math.floor(raw_lots / self.symbol_info.volume_step)
        normalized_lots = steps * self.symbol_info.volume_step

        logger.debug(
            f"规范化手数 (步骤 1): raw_lots={raw_lots:.4f}, "
            f"steps={steps}, normalized={normalized_lots:.4f}"
        )

        # 步骤 2: 应用 volume_min 约束
        if normalized_lots < self.symbol_info.volume_min:
            logger.debug(
                f"手数 {normalized_lots:.4f} 低于最小值 {self.symbol_info.volume_min}, "
                f"返回 0.0"
            )
            return 0.0

        # 步骤 3: 应用 volume_max 约束
        if self.symbol_info.volume_max > 0:  # volume_max = 0 表示无限制
            if normalized_lots > self.symbol_info.volume_max:
                logger.warning(
                    f"手数 {normalized_lots:.4f} 超过最大值 {self.symbol_info.volume_max}, "
                    f"限制为 {self.symbol_info.volume_max}"
                )
                normalized_lots = self.symbol_info.volume_max

        # 步骤 4: 防止浮点精度问题
        # 使用 round() 避免类似 0.010000000001 的精度问题
        decimal_places = self._get_decimal_places(self.symbol_info.volume_step)
        normalized_lots = round(normalized_lots, decimal_places)

        logger.debug(
            f"最终规范化手数: {normalized_lots:.4f} "
            f"(原始: {raw_lots:.4f})"
        )

        return normalized_lots

    def bt_size_to_mt5_lots(self, bt_size: float, current_price: float = 1.0) -> float:
        """
        一步转换：Backtrader size → MT5 normalized lots

        组合 backtrader_size_to_lots() 和 normalize_volume() 的功能

        Args:
            bt_size: Backtrader 计算的仓位大小 (单位数)
            current_price: 当前价格

        Returns:
            float: 规范化的 MT5 手数

        示例:
            >>> adapter.bt_size_to_mt5_lots(10500)
            0.10  # 10,500 → 0.105 raw → 0.10 normalized
        """
        raw_lots = self.backtrader_size_to_lots(bt_size, current_price)
        normalized_lots = self.normalize_volume(raw_lots)

        logger.info(
            f"Backtrader size {bt_size:.2f} → MT5 lots {normalized_lots:.4f} "
            f"(symbol: {self.symbol_info.symbol})"
        )

        return normalized_lots

    def validate_volume(self, lots: float) -> Tuple[bool, Optional[str]]:
        """
        验证手数是否符合 MT5 要求

        检查项：
        1. 是否 >= volume_min
        2. 是否 <= volume_max (如果有限制)
        3. 是否符合 volume_step

        Args:
            lots: 要验证的手数

        Returns:
            tuple: (是否有效, 错误信息)
                - (True, None): 有效
                - (False, "错误原因"): 无效

        示例:
            >>> adapter.validate_volume(0.1)
            (True, None)
            >>> adapter.validate_volume(0.005)
            (False, "手数 0.005 低于最小值 0.01")
        """
        # 检查最小值
        if lots < self.symbol_info.volume_min:
            return False, f"手数 {lots:.4f} 低于最小值 {self.symbol_info.volume_min}"

        # 检查最大值
        if self.symbol_info.volume_max > 0 and lots > self.symbol_info.volume_max:
            return False, f"手数 {lots:.4f} 超过最大值 {self.symbol_info.volume_max}"

        # 检查步进 - 验证手数是 volume_min + n*volume_step 的形式
        # 允许小的浮点精度误差
        if lots < self.symbol_info.volume_min:
            return False, f"手数 {lots:.4f} 低于最小值 {self.symbol_info.volume_min}"

        # 检查是否是合法的步进倍数
        offset_from_min = lots - self.symbol_info.volume_min
        remainder = offset_from_min % self.symbol_info.volume_step
        tolerance = max(1e-9, self.symbol_info.volume_step * 1e-9)

        if abs(remainder) > tolerance and abs(remainder - self.symbol_info.volume_step) > tolerance:
            return False, f"手数 {lots:.4f} 不符合步进 {self.symbol_info.volume_step}"

        return True, None

    @staticmethod
    def _get_decimal_places(value: float) -> int:
        """
        获取浮点数的小数位数

        Args:
            value: 浮点数 (如 0.01)

        Returns:
            int: 小数位数 (如 2)

        示例:
            >>> _get_decimal_places(0.01)
            2
            >>> _get_decimal_places(0.001)
            3
        """
        # 转换为字符串并计算小数位数
        str_value = f"{value:.10f}".rstrip('0')
        if '.' in str_value:
            return len(str_value.split('.')[1])
        return 0


# ============================================================================
# 便捷工厂函数
# ============================================================================

def create_eurusd_adapter() -> MT5VolumeAdapter:
    """
    创建 EURUSD 适配器 (常用预设)

    Returns:
        MT5VolumeAdapter: EURUSD 适配器
    """
    symbol_info = MT5SymbolInfo(
        symbol="EURUSD",
        contract_size=100000.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        point=0.00001,
        trade_tick_size=0.00001
    )
    return MT5VolumeAdapter(symbol_info)


def create_xauusd_adapter() -> MT5VolumeAdapter:
    """
    创建 XAUUSD (黄金) 适配器 (常用预设)

    Returns:
        MT5VolumeAdapter: XAUUSD 适配器
    """
    symbol_info = MT5SymbolInfo(
        symbol="XAUUSD",
        contract_size=100.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        point=0.01,
        trade_tick_size=0.01
    )
    return MT5VolumeAdapter(symbol_info)
