"""
MT5 Bridge - MetaTrader5 实盘交易连接模块

根据Gemini Pro审查建议实现的完整MT5桥接层，提供：
1. 初始化和连接管理
2. 数据获取（报价、历史数据）
3. 下单执行和风险控制
4. 持仓和账户状态同步
5. 错误处理和重试机制
"""

import logging
import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)


class MT5ConnectionError(Exception):
    """MT5连接错误"""
    pass


class MT5OrderError(Exception):
    """MT5下单错误"""
    pass


class OrderType(Enum):
    """订单类型"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


class OrderStatus(Enum):
    """订单状态"""
    PLACED = "PLACED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class TickData:
    """Tick数据"""
    symbol: str
    bid: float
    ask: float
    time: datetime
    volume: int = 0

    @property
    def mid_price(self) -> float:
        """中间价格"""
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float:
        """点差"""
        return self.ask - self.bid


@dataclass
class BarData:
    """K线数据"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    time: datetime
    volume: int
    bid_open: Optional[float] = None
    bid_high: Optional[float] = None
    bid_low: Optional[float] = None
    bid_close: Optional[float] = None


@dataclass
class OrderInfo:
    """订单信息"""
    symbol: str
    order_type: OrderType
    volume: float
    price: float = 0.0
    sl: float = 0.0  # Stop Loss
    tp: float = 0.0  # Take Profit
    comment: str = ""
    ticket: int = 0
    status: OrderStatus = OrderStatus.PLACED
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_pending(self) -> bool:
        """是否待成交"""
        return self.status in [OrderStatus.PLACED, OrderStatus.PARTIAL]


@dataclass
class PositionInfo:
    """持仓信息"""
    symbol: str
    volume: float
    entry_price: float
    current_price: float
    type: str  # "BUY" or "SELL"
    profit: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    ticket: int = 0

    @property
    def is_long(self) -> bool:
        """是否多头"""
        return self.type == "BUY"

    @property
    def is_short(self) -> bool:
        """是否空头"""
        return self.type == "SELL"

    @property
    def unrealized_pnl(self) -> float:
        """未实现盈亏"""
        if self.is_long:
            return (self.current_price - self.entry_price) * self.volume
        else:
            return (self.entry_price - self.current_price) * self.volume


@dataclass
class AccountInfo:
    """账户信息"""
    balance: float = 0.0
    equity: float = 0.0
    free_margin: float = 0.0
    used_margin: float = 0.0
    margin_level: float = 0.0
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def margin_utilization(self) -> float:
        """保证金使用率"""
        if self.used_margin == 0:
            return 0.0
        return self.used_margin / (self.used_margin + self.free_margin)

    @property
    def is_in_danger(self) -> bool:
        """是否处于风险状态 (保证金水平<200%)"""
        return self.margin_level < 200


class MT5Bridge:
    """
    MT5 桥接类 - 实现实盘交易的核心功能

    根据Gemini Pro审查建议设计，包含：
    - 重试机制
    - 错误处理
    - 状态同步
    - 风险控制
    """

    def __init__(self, symbol: str = "EURUSD", account_number: Optional[int] = None,
                 password: Optional[str] = None, server: Optional[str] = None,
                 max_retries: int = 3, retry_delay: float = 1.0):
        """
        初始化MT5桥接

        Args:
            symbol: 交易品种 (如 "EURUSD")
            account_number: MT5账户号
            password: MT5账户密码
            server: MT5服务器
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.symbol = symbol
        self.account_number = account_number
        self.password = password
        self.server = server
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.is_connected = False
        self.last_bar_time = None
        self._cached_rates = {}
        self._last_sync_time = None

        logger.info(f"🔧 MT5Bridge 初始化: symbol={symbol}")

    def connect(self) -> bool:
        """
        连接MT5终端

        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("🔌 正在连接MT5终端...")

            # 初始化MT5
            if not mt5.initialize():
                error_code = mt5.last_error()
                raise MT5ConnectionError(
                    f"MT5初始化失败: {error_code}"
                )

            # 如果提供了账户信息，则登录
            if self.account_number and self.password and self.server:
                if not mt5.login(self.account_number, self.password, self.server):
                    error_code = mt5.last_error()
                    raise MT5ConnectionError(
                        f"MT5登录失败 (Account: {self.account_number}): {error_code}"
                    )
                logger.info(f"✅ 已登录账户 {self.account_number} @ {self.server}")

            self.is_connected = True
            logger.info("✅ MT5连接成功")
            return True

        except MT5ConnectionError as e:
            logger.error(f"❌ {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"❌ 连接出错: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """
        断开MT5连接

        Returns:
            bool: 断开是否成功
        """
        try:
            if self.is_connected:
                mt5.shutdown()
                self.is_connected = False
                logger.info("✅ MT5连接已断开")
            return True
        except Exception as e:
            logger.error(f"❌ 断开连接出错: {e}")
            return False

    def _retry_operation(self, operation, *args, **kwargs):
        """
        重试机制 - 包装任何需要重试的操作

        Args:
            operation: 可调用的操作
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            操作的返回值，或None如果所有重试都失败
        """
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"⚠️ 操作失败 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ 操作在{self.max_retries}次重试后仍失败: {e}")
                    raise
        return None

    def get_tick_data(self, symbol: Optional[str] = None) -> Optional[TickData]:
        """
        获取最新Tick数据

        Args:
            symbol: 品种代码，不提供则使用默认symbol

        Returns:
            TickData 对象，或None如果获取失败
        """
        symbol = symbol or self.symbol

        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.warning(f"⚠️ 无法获取 {symbol} 的Tick数据")
                return None

            return TickData(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                time=datetime.fromtimestamp(tick.time),
                volume=tick.volume
            )

        except Exception as e:
            logger.error(f"❌ 获取Tick数据出错: {e}")
            return None

    def get_bar_data(self, symbol: Optional[str] = None, timeframe: int = mt5.TIMEFRAME_H1,
                     lookback_bars: int = 100) -> Optional[List[BarData]]:
        """
        获取K线数据

        Args:
            symbol: 品种代码
            timeframe: 时间周期 (mt5.TIMEFRAME_*)
            lookback_bars: 回看的K线数量

        Returns:
            BarData 列表，或None如果获取失败
        """
        symbol = symbol or self.symbol

        try:
            rates = mt5.copy_rates_from_pos(
                symbol,
                timeframe,
                0,  # 从最近的K线开始
                lookback_bars
            )

            if rates is None or len(rates) == 0:
                logger.warning(f"⚠️ 无法获取 {symbol} 的K线数据")
                return None

            bars = []
            for rate in rates:
                bar = BarData(
                    symbol=symbol,
                    open=rate['open'],
                    high=rate['high'],
                    low=rate['low'],
                    close=rate['close'],
                    time=datetime.fromtimestamp(rate['time']),
                    volume=rate['tick_volume']
                )
                bars.append(bar)

            # 缓存最新的K线数据
            self._cached_rates[symbol] = bars

            return bars

        except Exception as e:
            logger.error(f"❌ 获取K线数据出错: {e}")
            return None

    def is_new_bar(self, symbol: Optional[str] = None, timeframe: int = mt5.TIMEFRAME_H1) -> bool:
        """
        检查是否产生了新的K线

        重要: 这是避免重复计算的关键逻辑

        Args:
            symbol: 品种代码
            timeframe: 时间周期

        Returns:
            bool: 是否有新K线
        """
        symbol = symbol or self.symbol

        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
            if rates is None or len(rates) == 0:
                return False

            current_time = datetime.fromtimestamp(rates[0]['time'])

            if self.last_bar_time is None:
                self.last_bar_time = current_time
                return True

            if current_time > self.last_bar_time:
                self.last_bar_time = current_time
                logger.info(f"🔔 新K线产生: {symbol} @ {current_time}")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ 检查新K线出错: {e}")
            return False

    def normalize_volume(self, symbol: str, volume: float) -> float:
        """
        规范化手数 - 确保订单量符合MT5合约规范

        根据Gemini Pro审查建议实现。MT5订单要求：
        - volume >= volume_min（最小手数）
        - (volume - volume_min) % volume_step == 0（按步长递增）
        - volume <= volume_max（最大手数，如果限制的话）

        参考Gemini建议的normalize_volume函数：
        ```python
        def normalize_volume(symbol_info, volume):
            if volume < symbol_info.volume_min:
                return 0.0

            steps = int(volume / symbol_info.volume_step)
            norm_vol = steps * symbol_info.volume_step

            if symbol_info.volume_max > 0:
                norm_vol = min(norm_vol, symbol_info.volume_max)

            return float(f"{norm_vol:.2f}")
        ```

        Args:
            symbol: 品种代码（如 "EURUSD"）
            volume: 原始手数

        Returns:
            规范化后的手数，0.0表示低于最小手数

        Raises:
            MT5OrderError: 无法获取品种信息时
        """
        try:
            # 选中品种
            if not mt5.symbol_select(symbol, True):
                raise MT5OrderError(f"无法选择品种 {symbol}")

            # 获取品种信息
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                raise MT5OrderError(f"无法获取品种 {symbol} 的信息")

            # 检查是否低于最小手数
            if volume < symbol_info.volume_min:
                logger.warning(
                    f"⚠️ {symbol} 手数 {volume} 低于最小值 {symbol_info.volume_min}，"
                    f"将返回0.0（不下单）"
                )
                return 0.0

            # 按照 volume_step 进行对齐
            # 计算可以按 step 递增多少次
            if symbol_info.volume_step > 0:
                steps = int(volume / symbol_info.volume_step)
                normalized = steps * symbol_info.volume_step
            else:
                logger.warning(f"⚠️ {symbol} 的 volume_step={symbol_info.volume_step}，使用原值")
                normalized = volume

            # 检查最大手数限制
            if symbol_info.volume_max > 0 and normalized > symbol_info.volume_max:
                logger.warning(
                    f"⚠️ {symbol} 规范化手数 {normalized} 超过最大值 {symbol_info.volume_max}，"
                    f"将限制为 {symbol_info.volume_max}"
                )
                normalized = symbol_info.volume_max

            # 防止浮点精度问题，四舍五入到2位小数
            normalized = float(f"{normalized:.2f}")

            if normalized != volume:
                logger.info(
                    f"📏 {symbol} 手数规范化: {volume} → {normalized} "
                    f"(min={symbol_info.volume_min}, step={symbol_info.volume_step}, "
                    f"max={symbol_info.volume_max})"
                )

            return normalized

        except MT5OrderError as e:
            logger.error(f"❌ 手数规范化失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 手数规范化出错: {e}")
            raise MT5OrderError(f"手数规范化异常: {e}")

    def send_order(self, order: OrderInfo, deviation: int = 20) -> Tuple[bool, Optional[int]]:
        """
        发送订单

        Args:
            order: OrderInfo 对象
            deviation: 允许的偏差（点数）

        Returns:
            (成功标志, 订单ticket) 元组
        """
        try:
            logger.info(
                f"📤 发送订单: {order.order_type.value} {order.volume} {order.symbol} "
                f"@ {order.price}"
            )

            # 确保已连接
            if not self.is_connected:
                raise MT5OrderError("未连接到MT5")

            # 检查账户是否可交易
            if not mt5.symbol_select(order.symbol, True):
                raise MT5OrderError(f"无法选择品种 {order.symbol}")

            # 映射订单类型
            order_type_map = {
                OrderType.BUY: mt5.ORDER_TYPE_BUY,
                OrderType.SELL: mt5.ORDER_TYPE_SELL,
                OrderType.BUY_LIMIT: mt5.ORDER_TYPE_BUY_LIMIT,
                OrderType.SELL_LIMIT: mt5.ORDER_TYPE_SELL_LIMIT,
                OrderType.BUY_STOP: mt5.ORDER_TYPE_BUY_STOP,
                OrderType.SELL_STOP: mt5.ORDER_TYPE_SELL_STOP,
            }

            mt5_order_type = order_type_map.get(order.order_type)
            if mt5_order_type is None:
                raise MT5OrderError(f"不支持的订单类型: {order.order_type}")

            # 规范化手数（P0优先级 - Gemini建议）
            try:
                normalized_volume = self.normalize_volume(order.symbol, order.volume)
                if normalized_volume == 0.0:
                    raise MT5OrderError(
                        f"规范化手数为0（低于{order.symbol}最小手数），拒绝下单"
                    )
                order.volume = normalized_volume
            except MT5OrderError as e:
                logger.error(f"❌ 手数规范化失败，拒绝下单: {e}")
                order.status = OrderStatus.REJECTED
                return (False, None)

            # 构建订单请求
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": order.symbol,
                "volume": order.volume,
                "type": mt5_order_type,
                "price": order.price if order.price > 0 else mt5.symbol_info_tick(order.symbol).ask,
                "sl": order.sl,
                "tp": order.tp,
                "deviation": deviation,
                "magic": 123456,
                "comment": order.comment,
                "type_time": mt5.ORDER_TIME_GTC,  # Good Till Cancel
                "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill
            }

            # 发送订单 (带重试)
            result = self._retry_operation(mt5.order_send, request)

            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error_code = result.retcode if result else -1
                raise MT5OrderError(
                    f"订单发送失败: {error_code}"
                )

            order.ticket = result.order
            order.status = OrderStatus.FILLED
            logger.info(f"✅ 订单已成交: ticket={result.order}")

            return (True, result.order)

        except MT5OrderError as e:
            logger.error(f"❌ {e}")
            order.status = OrderStatus.REJECTED
            return (False, None)
        except Exception as e:
            logger.error(f"❌ 下单出错: {e}")
            order.status = OrderStatus.REJECTED
            return (False, None)

    def get_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        """
        获取所有持仓（或指定品种的持仓）

        关键: Gemini建议每次循环都调用此方法强制同步持仓状态

        Args:
            symbol: 品种代码，不提供则获取所有持仓

        Returns:
            PositionInfo 列表
        """
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()

            if positions is None:
                return []

            position_list = []
            for pos in positions:
                current_tick = mt5.symbol_info_tick(pos.symbol)
                if current_tick is None:
                    continue

                position = PositionInfo(
                    symbol=pos.symbol,
                    volume=pos.volume,
                    entry_price=pos.price_open,
                    current_price=current_tick.bid if pos.type == mt5.ORDER_TYPE_BUY else current_tick.ask,
                    type="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                    profit=pos.profit,
                    ticket=pos.ticket
                )
                position_list.append(position)

            logger.info(f"📊 获取持仓: {len(position_list)} 个")
            return position_list

        except Exception as e:
            logger.error(f"❌ 获取持仓出错: {e}")
            return []

    def get_account_info(self) -> Optional[AccountInfo]:
        """
        获取账户信息

        根据Gemini建议，使用 balance 而非 equity 进行风险管理

        Returns:
            AccountInfo 对象
        """
        try:
            account = mt5.account_info()
            if account is None:
                logger.warning("⚠️ 无法获取账户信息")
                return None

            info = AccountInfo(
                balance=account.balance,
                equity=account.equity,
                free_margin=account.margin_free,
                used_margin=account.margin,
                margin_level=account.margin_level if account.margin != 0 else 0,
                currency=account.currency
            )

            # 警告: 如果处于风险状态
            if info.is_in_danger:
                logger.warning(
                    f"🚨 账户风险警告! 保证金水平: {info.margin_level:.2f}%"
                )

            self._last_sync_time = datetime.now()
            return info

        except Exception as e:
            logger.error(f"❌ 获取账户信息出错: {e}")
            return None

    def close_position(self, ticket: int, symbol: str, volume: float,
                       deviation: int = 20) -> Tuple[bool, Optional[int]]:
        """
        平仓

        Args:
            ticket: 持仓ticket
            symbol: 品种代码
            volume: 平仓手数
            deviation: 允许偏差

        Returns:
            (成功标志, 平仓订单ticket) 元组
        """
        try:
            logger.info(f"📥 平仓: ticket={ticket}, {symbol}, {volume}手")

            # 获取当前持仓
            positions = mt5.positions_get(ticket=ticket)
            if positions is None or len(positions) == 0:
                raise MT5OrderError(f"持仓不存在: {ticket}")

            pos = positions[0]
            tick = mt5.symbol_info_tick(symbol)

            # 确定订单类型（与持仓方向相反）
            if pos.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": deviation,
                "magic": 123456,
                "comment": f"Close position {ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            result = self._retry_operation(mt5.order_send, request)

            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                raise MT5OrderError(f"平仓失败: {result.retcode if result else -1}")

            logger.info(f"✅ 已平仓: ticket={result.order}")
            return (True, result.order)

        except Exception as e:
            logger.error(f"❌ {e}")
            return (False, None)

    def wait_for_new_bar(self, symbol: Optional[str] = None,
                        timeframe: int = mt5.TIMEFRAME_H1,
                        timeout_seconds: int = 3600,
                        check_interval: float = 1.0) -> bool:
        """
        等待新K线产生

        用于交易循环中的同步点

        Args:
            symbol: 品种代码
            timeframe: 时间周期
            timeout_seconds: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            bool: 是否产生了新K线
        """
        symbol = symbol or self.symbol
        start_time = datetime.now()

        while True:
            if self.is_new_bar(symbol, timeframe):
                return True

            # 检查超时
            if (datetime.now() - start_time).total_seconds() > timeout_seconds:
                logger.warning(f"⏱️ 等待新K线超时 ({timeout_seconds}s)")
                return False

            time.sleep(check_interval)


# ============================================================================
# 使用示例 (根据Gemini建议的架构)
# ============================================================================

def example_live_trading_loop():
    """
    根据Gemini审查建议实现的实盘交易循环示例
    """

    bridge = MT5Bridge(symbol="EURUSD")

    # 1. 连接
    if not bridge.connect():
        logger.error("连接失败，退出")
        return

    try:
        # 2. 交易循环
        while True:
            # 关键: 每次循环开始时强制同步持仓状态
            positions = bridge.get_positions()
            account_info = bridge.get_account_info()

            # 检查账户状态
            if account_info and account_info.is_in_danger:
                logger.error("账户处于风险状态，停止交易")
                break

            # 3. 检查新K线
            if not bridge.is_new_bar("EURUSD", mt5.TIMEFRAME_H1):
                time.sleep(1)
                continue

            logger.info("🔔 处理新K线...")

            # 4. 获取K线数据
            bars = bridge.get_bar_data("EURUSD", mt5.TIMEFRAME_H1, lookback_bars=50)
            if not bars:
                continue

            # 5. 特征工程 (此处应实现实际的特征计算)
            # features = feature_engineer.calculate(bars)  # TODO: 实现特征工程

            # 6. 模型推理
            # signal, prob = model.predict(features)  # TODO: 实现模型推理

            # 7. 风控和仓位计算
            # size = risk_manager.get_size(account_info, prob)  # TODO: 实现风控

            # 8. 执行订单（示例）
            # if size != 0:
            #     order = OrderInfo(...)
            #     bridge.send_order(order)

            logger.info("✅ 循环完成，等待下一个K线...")

    except KeyboardInterrupt:
        logger.info("⚠️ 被用户中断")
    except Exception as e:
        logger.error(f"❌ 交易循环出错: {e}")
    finally:
        # 9. 断开连接
        bridge.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行示例
    # example_live_trading_loop()

    # 或简单测试连接
    bridge = MT5Bridge("EURUSD")
    if bridge.connect():
        tick = bridge.get_tick_data()
        if tick:
            print(f"✅ {tick.symbol}: Bid={tick.bid}, Ask={tick.ask}, Spread={tick.spread:.5f}")
        bridge.disconnect()
