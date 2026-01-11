#!/usr/bin/env python3
"""
MT5 Gateway Service - MetaTrader 5 连接管理
=============================================

提供单例 MT5Service 类，用于管理 MetaTrader 5 terminal 的连接。
支持便携式安装（通过环境变量指定 MT5 路径）。

功能：
- 单例模式确保全局只有一个 MT5 连接
- 从环境变量加载配置（MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER）
- connect() 方法初始化 MT5 连接
- is_connected() 方法检查连接状态
"""

import os
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv

# 配置日志（必须在导入 MetaTrader5 之前）
logger = logging.getLogger(__name__)

# 导入 MetaTrader5 库（生产环境需要）
try:
    import MetaTrader5
except ImportError:
    logger.warning("MetaTrader5 module not available - running in STUB mode")
    MetaTrader5 = None


# ============================================================================
# STUB MT5 Implementation (for testing when MetaTrader5 is unavailable)
# ============================================================================

class _StubMT5:
    """
    Mock MT5 implementation for testing/demo purposes.
    Used when the actual MetaTrader5 library is not installed.
    """

    # MT5 constants
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5

    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5

    def __init__(self):
        self.account_data = {
            'balance': 200.00,
            'equity': 205.50,
            'margin': 15.00,
            'margin_free': 185.00,
            'margin_level': 1370.0,
            'currency': 'USD'
        }
        self.positions = []

    def account_info(self):
        """Return account information as stub object"""
        class AccountInfo:
            def __init__(self, data):
                self.balance = data['balance']
                self.equity = data['equity']
                self.margin = data['margin']
                self.margin_free = data['margin_free']
                self.margin_level = data['margin_level']
                self.currency = data['currency']
        return AccountInfo(self.account_data)

    def positions_get(self):
        """Return open positions"""
        return self.positions

    def position_get(self, ticket):
        """Get position by ticket"""
        for pos in self.positions:
            if hasattr(pos, 'ticket') and pos.ticket == ticket:
                return pos
        return None

    def symbol_info_tick(self, symbol):
        """Return tick data for symbol"""
        class TickInfo:
            def __init__(self):
                self.bid = 1.05123
                self.ask = 1.05125
                self.time = int(__import__('time').time())
                self.volume = 1000
        return TickInfo()

    def order_send(self, request):
        """Send order - stub implementation"""
        class OrderResult:
            def __init__(self):
                self.order = 12345
                self.volume = request.get('volume', 0.1)
                self.price = request.get('price', 1.05125)
                self.retcode = 10009  # TRADE_RETCODE_DONE
        return OrderResult()

    def initialize(self, path=None):
        """Initialize MT5 - stub"""
        return True

    def login(self, login, password, server):
        """Login to MT5 - stub"""
        return True

    def shutdown(self):
        """Shutdown MT5 - stub"""
        pass

    def terminal_info(self):
        """Get terminal info - stub"""
        class TerminalInfo:
            connected = True
        return TerminalInfo()


class MT5Service:
    """
    MetaTrader5 单例服务

    管理与本地 MetaTrader 5 terminal 的连接，支持便携式部署。

    属性：
        _instance: 单例实例（类级别）
        _mt5: MetaTrader5 连接对象
        _connected: 连接状态标志
    """

    _instance: Optional['MT5Service'] = None
    _mt5 = None
    _connected: bool = False

    def __new__(cls) -> 'MT5Service':
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super(MT5Service, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 MT5Service（单例，仅执行一次）"""
        # 仅在首次创建时初始化
        if not hasattr(self, '_initialized'):
            # 确定项目根目录（src/gateway 的上两级）
            project_root = Path(__file__).resolve().parent.parent.parent
            env_path = project_root / '.env'

            # 强制加载 .env 文件，override=True 确保覆盖已有的环境变量
            load_dotenv(dotenv_path=env_path, override=True)

            self._initialized = True
            self._mt5 = None
            self._connected = False

            # 从环境变量加载配置
            self.mt5_path = os.getenv('MT5_PATH', '')
            self.mt5_login = os.getenv('MT5_LOGIN', '')
            self.mt5_password = os.getenv('MT5_PASSWORD', '')
            self.mt5_server = os.getenv('MT5_SERVER', '')

            logger.info(
                f"MT5Service 初始化完成 - "
                f"Path: {self.mt5_path}, "
                f"Server: {self.mt5_server}, "
                f"ENV Loaded: {env_path.exists()}"
            )

    def connect(self) -> bool:
        """
        建立与 MetaTrader 5 的连接

        使用 mt5.initialize(path=...) 以支持便携式安装。
        如果 MetaTrader5 库不可用，使用 STUB 模式（用于测试/演示）。

        返回：
            bool: 连接成功返回 True，失败返回 False
        """
        if self._connected:
            logger.warning("已存在活跃的 MT5 连接")
            return True

        try:
            if MetaTrader5 is None:
                # 只有显式启用 STUB 模式时才使用虚拟数据
                use_stub = os.getenv("USE_MT5_STUB", "false").lower() == "true"
                if not use_stub:
                    logger.error("MetaTrader5 库未安装，且 USE_MT5_STUB 未启用。无法继续。")
                    return False

                logger.warning("MetaTrader5 库未安装，使用 STUB 模式 (仅限测试/演示)")
                # 使用 STUB 模式 - 返回虚拟数据以供测试/演示
                self._connected = True
                self._mt5 = _StubMT5()
                logger.info("MT5 连接成功建立 (STUB 模式)")
                return True

            # 核心步骤：使用 path= 参数实现便携式连接
            initialized = MetaTrader5.initialize(path=self.mt5_path)

            if not initialized:
                logger.error(
                    f"MT5 初始化失败: {MetaTrader5.last_error()}"
                )
                return False

            # 尝试登录
            if self.mt5_login and self.mt5_password:
                logged_in = MetaTrader5.login(
                    login=int(self.mt5_login),
                    password=self.mt5_password,
                    server=self.mt5_server
                )

                if not logged_in:
                    logger.error(
                        f"MT5 登录失败: {MetaTrader5.last_error()}"
                    )
                    MetaTrader5.shutdown()
                    return False

            self._connected = True
            self._mt5 = MetaTrader5
            logger.info("MT5 连接成功建立")
            return True

        except Exception as e:
            logger.error(f"MT5 连接异常: {str(e)}")
            return False

    def is_connected(self) -> bool:
        """
        检查 MetaTrader 5 连接状态

        返回：
            bool: 已连接返回 True，未连接返回 False
        """
        if not self._connected or self._mt5 is None:
            return False

        try:
            # 验证连接的实际状态
            if hasattr(self._mt5, 'terminal_info'):
                info = self._mt5.terminal_info()
                return info is not None
            return self._connected
        except Exception as e:
            logger.error(f"连接状态检查异常: {str(e)}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """断开 MetaTrader 5 连接"""
        if self._connected and self._mt5 is not None:
            try:
                self._mt5.shutdown()
                self._connected = False
                logger.info("MT5 连接已断开")
            except Exception as e:
                logger.error(f"MT5 断开异常: {str(e)}")

    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        if not self._connected or self._mt5 is None:
            return {"error": "MT5 not connected"}

        try:
            account = self._mt5.account_info()
            if account is None:
                return {"error": "Failed to retrieve account info"}

            return {
                "balance": float(account.balance),
                "equity": float(account.equity),
                "free_margin": float(account.margin_free),
                "used_margin": float(account.margin),
                "margin_level": float(account.margin_level) if account.margin != 0 else 0,
                "currency": account.currency
            }
        except Exception as e:
            logger.error(f"获取账户信息异常: {str(e)}")
            return {"error": str(e)}

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓列表"""
        if not self._connected or self._mt5 is None:
            return []

        try:
            positions = self._mt5.positions_get()
            if positions is None:
                return []

            return [
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": float(pos.volume),
                    "open_price": float(pos.price_open),
                    "current_price": float(pos.price_current),
                    "profit": float(pos.profit)
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"获取持仓异常: {str(e)}")
            return []

    def execute_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行订单

        支持两种 payload 格式：
        1. 旧格式: {"type": "BUY", ...}
        2. 新格式: {"side": "BUY", "type": "LIMIT", ...}
        """
        if not self._connected or self._mt5 is None:
            return {"status": "ERROR", "error": "MT5 not connected"}

        try:
            symbol = payload.get('symbol', 'EURUSD')
            volume = payload.get('volume', 0.1)
            price = payload.get('price', 0)
            sl = payload.get('sl', 0)
            tp = payload.get('tp', 0)

            # 支持两种格式的 order type 字段
            # 新格式：side + type (BUY + LIMIT -> BUY_LIMIT)
            side = payload.get('side', '')  # BUY, SELL
            order_type = payload.get('type', 'BUY')  # BUY, SELL, LIMIT, STOP, etc.

            if side and order_type and order_type.upper() != 'BUY' and order_type.upper() != 'SELL':
                # 新格式：side + type
                order_type = f"{side.upper()}_{order_type.upper()}"
            elif not side:
                # 旧格式：直接使用 type
                order_type = order_type.upper()

            # 确定订单类型
            if order_type == 'BUY':
                mt5_type = self._mt5.ORDER_TYPE_BUY
            elif order_type == 'SELL':
                mt5_type = self._mt5.ORDER_TYPE_SELL
            elif order_type == 'BUY_LIMIT':
                mt5_type = self._mt5.ORDER_TYPE_BUY_LIMIT
            elif order_type == 'SELL_LIMIT':
                mt5_type = self._mt5.ORDER_TYPE_SELL_LIMIT
            elif order_type == 'BUY_STOP':
                mt5_type = self._mt5.ORDER_TYPE_BUY_STOP
            elif order_type == 'SELL_STOP':
                mt5_type = self._mt5.ORDER_TYPE_SELL_STOP
            else:
                return {"status": "ERROR", "error": f"Unknown order type: {order_type}"}

            # 获取当前报价
            tick = self._mt5.symbol_info_tick(symbol)
            if tick is None:
                return {"status": "ERROR", "error": f"Cannot get tick for {symbol}"}

            # 确定 action 类型：市价单用 DEAL，挂单用 PENDING
            is_market_order = mt5_type in (self._mt5.ORDER_TYPE_BUY, self._mt5.ORDER_TYPE_SELL)
            action = self._mt5.TRADE_ACTION_DEAL if is_market_order else self._mt5.TRADE_ACTION_PENDING

            # 构建订单请求
            request = {
                "action": action,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_type,
                "price": price if price > 0 else tick.ask,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 0,
                "comment": "MT5 Gateway Order"
            }

            result = self._mt5.order_send(request)
            if result is None:
                return {"status": "ERROR", "error": "Order send failed"}

            return {
                "status": "SUCCESS",
                "ticket": result.order,
                "volume": result.volume,
                "price": result.price
            }
        except Exception as e:
            logger.error(f"执行订单异常: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """平仓"""
        if not self._connected or self._mt5 is None:
            return {"status": "ERROR", "error": "MT5 not connected"}

        try:
            position = self._mt5.position_get(ticket=ticket)
            if position is None:
                return {"status": "ERROR", "error": f"Position {ticket} not found"}

            # 获取当前报价
            tick = self._mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return {"status": "ERROR", "error": f"Cannot get tick for {position.symbol}"}

            # 构建平仓请求
            # 注意：平多单(type==0)用卖出+Bid价格，平空单(type==1)用买入+Ask价格
            is_buy_position = position.type == 0
            close_type = self._mt5.ORDER_TYPE_SELL if is_buy_position else self._mt5.ORDER_TYPE_BUY
            close_price = tick.bid if is_buy_position else tick.ask

            request = {
                "action": self._mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket,
                "price": close_price,
                "deviation": 20,
                "magic": 0,
                "comment": "MT5 Gateway Close"
            }

            result = self._mt5.order_send(request)
            if result is None:
                return {"status": "ERROR", "error": "Close order send failed"}

            return {
                "status": "SUCCESS",
                "ticket": result.order,
                "volume": result.volume,
                "price": result.price
            }
        except Exception as e:
            logger.error(f"平仓异常: {str(e)}")
            return {"status": "ERROR", "error": str(e)}


# 便利函数：获取全局 MT5Service 实例
def get_mt5_service() -> MT5Service:
    """获取 MT5Service 单例实例"""
    return MT5Service()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    service = MT5Service()
    print(f"MT5 路径: {service.mt5_path}")
    print(f"MT5 服务器: {service.mt5_server}")
    # 实际连接需要真实的 MetaTrader 5 安装和凭证
