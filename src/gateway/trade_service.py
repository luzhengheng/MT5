#!/usr/bin/env python3
"""
Trade Service - 交易执行服务
==============================

提供 TradeService 类，用于执行 MetaTrader 5 的交易操作。

功能：
- 单例模式确保全局只有一个交易服务
- buy(symbol, volume, ...) - 开多单
- sell(symbol, volume, ...) - 开空单
- close_position(ticket) - 平仓
- get_positions() - 获取当前持仓
"""

import logging
from typing import Optional, Dict, Any, List
from src.gateway.mt5_service import MT5Service, get_mt5_service

# 配置日志
logger = logging.getLogger(__name__)


class TradeService:
    """
    交易单例服务

    管理 MetaTrader 5 的交易操作（开仓、平仓）。

    属性：
        _instance: 单例实例（类级别）
        _mt5_service: MT5Service 单例引用
    """

    _instance: Optional['TradeService'] = None
    _mt5_service: Optional[MT5Service] = None

    def __new__(cls) -> 'TradeService':
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super(TradeService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 TradeService（单例，仅执行一次）"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._mt5_service = get_mt5_service()
            logger.info("TradeService 初始化完成")

    def buy(
        self,
        symbol: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = "MT5-CRS Buy"
    ) -> Optional[Dict[str, Any]]:
        """
        开多单（买入）

        参数：
            symbol (str): 品种代码，如 "EURUSD.s"
            volume (float): 交易手数，如 0.01
            price (float, optional): 指定价格（None 表示市价单）
            sl (float, optional): 止损价格
            tp (float, optional): 止盈价格
            deviation (int): 允许的价格偏差点数（默认 20）
            comment (str): 订单备注

        返回：
            Dict 或 None:
                成功：{
                    'ticket': 订单号,
                    'volume': 成交手数,
                    'price': 成交价格,
                    'comment': 备注
                }
                失败：None
        """
        # 检查连接状态
        if not self._mt5_service.is_connected():
            logger.error("MT5 未连接，无法执行买入操作")
            return None

        try:
            mt5 = self._mt5_service._mt5

            # 获取当前价格（如果未指定）
            if price is None:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    logger.error(f"无法获取 {symbol} 的价格信息")
                    return None
                price = tick.ask  # 买入使用卖价

            # 构建订单请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": deviation,
                "magic": 234000,  # 策略标识符
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,  # 有效期：取消前一直有效
                "type_filling": mt5.ORDER_FILLING_IOC,  # 立即成交或取消
            }

            # 添加止损和止盈（如果指定）
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp

            # 发送订单
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"订单发送失败: 未收到响应")
                return None

            # 检查订单结果
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(
                    f"买入订单失败: {result.retcode}, "
                    f"描述: {result.comment}"
                )
                return None

            logger.info(
                f"买入成功 - Ticket: {result.order}, "
                f"手数: {volume}, 价格: {result.price}"
            )

            return {
                'ticket': result.order,
                'volume': volume,
                'price': result.price,
                'comment': comment,
                'sl': sl,
                'tp': tp
            }

        except Exception as e:
            logger.error(f"买入操作异常: {str(e)}")
            return None

    def sell(
        self,
        symbol: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = "MT5-CRS Sell"
    ) -> Optional[Dict[str, Any]]:
        """
        开空单（卖出）

        参数：
            symbol (str): 品种代码，如 "EURUSD.s"
            volume (float): 交易手数，如 0.01
            price (float, optional): 指定价格（None 表示市价单）
            sl (float, optional): 止损价格
            tp (float, optional): 止盈价格
            deviation (int): 允许的价格偏差点数（默认 20）
            comment (str): 订单备注

        返回：
            Dict 或 None:
                成功：订单信息字典
                失败：None
        """
        # 检查连接状态
        if not self._mt5_service.is_connected():
            logger.error("MT5 未连接，无法执行卖出操作")
            return None

        try:
            mt5 = self._mt5_service._mt5

            # 获取当前价格（如果未指定）
            if price is None:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    logger.error(f"无法获取 {symbol} 的价格信息")
                    return None
                price = tick.bid  # 卖出使用买价

            # 构建订单请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": deviation,
                "magic": 234000,  # 策略标识符
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # 添加止损和止盈（如果指定）
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp

            # 发送订单
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"订单发送失败: 未收到响应")
                return None

            # 检查订单结果
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(
                    f"卖出订单失败: {result.retcode}, "
                    f"描述: {result.comment}"
                )
                return None

            logger.info(
                f"卖出成功 - Ticket: {result.order}, "
                f"手数: {volume}, 价格: {result.price}"
            )

            return {
                'ticket': result.order,
                'volume': volume,
                'price': result.price,
                'comment': comment,
                'sl': sl,
                'tp': tp
            }

        except Exception as e:
            logger.error(f"卖出操作异常: {str(e)}")
            return None

    def close_position(
        self,
        ticket: int,
        deviation: int = 20,
        comment: str = "MT5-CRS Close"
    ) -> bool:
        """
        平仓指定持仓

        参数：
            ticket (int): 持仓订单号
            deviation (int): 允许的价格偏差点数（默认 20）
            comment (str): 平仓备注

        返回：
            bool: 平仓成功返回 True，失败返回 False
        """
        # 检查连接状态
        if not self._mt5_service.is_connected():
            logger.error("MT5 未连接，无法执行平仓操作")
            return False

        try:
            mt5 = self._mt5_service._mt5

            # 获取持仓信息
            positions = mt5.positions_get(ticket=ticket)

            if positions is None or len(positions) == 0:
                logger.error(f"未找到持仓: Ticket {ticket}")
                return False

            position = positions[0]

            # 确定平仓类型（买入平仓 or 卖出平仓）
            if position.type == mt5.POSITION_TYPE_BUY:
                # 多单平仓 = 卖出
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                # 空单平仓 = 买入
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask

            # 构建平仓请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,  # 指定要平仓的持仓号
                "price": price,
                "deviation": deviation,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # 发送平仓订单
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"平仓请求发送失败: Ticket {ticket}")
                return False

            # 检查结果
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(
                    f"平仓失败: {result.retcode}, "
                    f"描述: {result.comment}"
                )
                return False

            logger.info(f"平仓成功 - Ticket: {ticket}, 价格: {result.price}")
            return True

        except Exception as e:
            logger.error(f"平仓操作异常: {str(e)}")
            return False

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取当前持仓列表

        参数：
            symbol (str, optional): 品种代码（None 表示所有持仓）

        返回：
            List[Dict]: 持仓信息列表
                [{
                    'ticket': 持仓号,
                    'symbol': 品种,
                    'type': 类型（buy/sell）,
                    'volume': 手数,
                    'price_open': 开仓价,
                    'price_current': 当前价,
                    'profit': 盈亏,
                    'sl': 止损,
                    'tp': 止盈
                }, ...]
        """
        # 检查连接状态
        if not self._mt5_service.is_connected():
            logger.error("MT5 未连接，无法获取持仓信息")
            return []

        try:
            mt5 = self._mt5_service._mt5

            # 获取持仓
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()

            if positions is None:
                logger.warning("未获取到持仓数据")
                return []

            # 转换为字典列表
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'buy' if pos.type == mt5.POSITION_TYPE_BUY else 'sell',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'time': pos.time
                })

            return result

        except Exception as e:
            logger.error(f"获取持仓异常: {str(e)}")
            return []


# 便利函数：获取全局 TradeService 实例
def get_trade_service() -> TradeService:
    """获取 TradeService 单例实例"""
    return TradeService()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    service = TradeService()
    print("TradeService 实例已创建")
