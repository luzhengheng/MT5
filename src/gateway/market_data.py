#!/usr/bin/env python3
"""
Market Data Service - 实时行情数据获取
========================================

提供 MarketDataService 类，用于从 MetaTrader 5 获取实时 tick 数据。

功能：
- 单例模式确保全局只有一个市场数据服务
- get_tick(symbol) 方法获取指定品种的最新 tick 数据
- 自动处理 Market Watch 中的符号可见性问题
"""

import logging
from typing import Optional, Dict, Any
from src.gateway.mt5_service import MT5Service, get_mt5_service

# 配置日志
logger = logging.getLogger(__name__)


class MarketDataService:
    """
    市场数据单例服务

    管理从 MetaTrader 5 获取实时 tick 数据的操作。

    属性：
        _instance: 单例实例（类级别）
        _mt5_service: MT5Service 单例引用
    """

    _instance: Optional['MarketDataService'] = None
    _mt5_service: Optional[MT5Service] = None

    def __new__(cls) -> 'MarketDataService':
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super(MarketDataService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 MarketDataService（单例，仅执行一次）"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._mt5_service = get_mt5_service()
            logger.info("MarketDataService 初始化完成")

    def get_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取指定品种的最新 tick 数据

        参数：
            symbol (str): 品种代码，如 "EURUSD"

        返回：
            Dict 或 None:
                成功：{
                    'symbol': 品种代码,
                    'time': 时间戳,
                    'bid': 买价,
                    'ask': 卖价,
                    'volume': 成交量
                }
                失败：None

        工作流：
            1. 检查连接状态
            2. 调用 mt5.symbol_info_tick(symbol)
            3. 如果为 None，通过 mt5.symbol_select(symbol, True) 确保符号在 Market Watch 中可见
            4. 重试获取 tick 数据
        """
        # 步骤 1: 检查连接
        if not self._mt5_service.is_connected():
            logger.error(f"MT5 未连接，无法获取 {symbol} 的 tick 数据")
            return None

        try:
            mt5 = self._mt5_service._mt5

            # 步骤 2: 尝试获取 tick 数据
            tick = mt5.symbol_info_tick(symbol)

            # 步骤 3: 如果 tick 为 None，检查符号可见性
            if tick is None:
                logger.warning(
                    f"符号 {symbol} 的 tick 为 None，"
                    f"正在尝试添加到 Market Watch..."
                )

                # 确保符号在 Market Watch 中可见
                selected = mt5.symbol_select(symbol, True)

                if not selected:
                    logger.error(
                        f"无法将 {symbol} 添加到 Market Watch"
                    )
                    return None

                # 步骤 4: 重试获取 tick 数据
                tick = mt5.symbol_info_tick(symbol)

                if tick is None:
                    logger.error(
                        f"重试后仍无法获取 {symbol} 的 tick 数据"
                    )
                    return None

            # 返回字典格式的 tick 数据
            return {
                'symbol': symbol,
                'time': tick.time,
                'bid': tick.bid,
                'ask': tick.ask,
                'volume': tick.volume
            }

        except Exception as e:
            logger.error(
                f"获取 {symbol} tick 数据时出异常: {str(e)}"
            )
            return None


# 便利函数：获取全局 MarketDataService 实例
def get_market_data_service() -> MarketDataService:
    """获取 MarketDataService 单例实例"""
    return MarketDataService()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    service = MarketDataService()
    print("MarketDataService 实例已创建")
