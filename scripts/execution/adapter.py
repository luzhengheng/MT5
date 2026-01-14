#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #102 Step 3: GTW 适配器
功能: 运行在 Inf 节点上，实现与 GTW 的 ZMQ 通讯
将 Task #101 生成的 Order Dict 转换为 GTW 能理解的格式

执行环境: Inf 节点 (172.19.141.250)
依赖: pyzmq, zmq
"""

import os
import sys
import json
import logging
import zmq
from datetime import datetime
from typing import Dict, Tuple, Optional, Any
from enum import Enum

# ============================================================================
# 日志配置
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/opt/mt5-crs/gtw_adapter.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("GTWAdapter")


# ============================================================================
# 枚举定义
# ============================================================================

class OrderType(Enum):
    """订单类型"""
    MARKET = "MARKET"      # 市价单
    LIMIT = "LIMIT"        # 限价单
    STOP = "STOP"          # 止损单


class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"             # 买入
    SELL = "SELL"           # 卖出


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"     # 待处理
    ACCEPTED = "ACCEPTED"   # 已接受
    FILLED = "FILLED"       # 已成交
    CANCELLED = "CANCELLED" # 已取消
    REJECTED = "REJECTED"   # 已拒绝


# ============================================================================
# GTW 通讯协议定义
# ============================================================================

class GTWProtocol:
    """GTW 通讯协议（ZeroMQ REQ/REP）"""

    # 通讯地址（内网）
    GTW_SERVER_ADDR = os.getenv("GTW_SERVER_ADDR", "tcp://172.19.141.255:5555")

    # 可配置的开发环境
    if os.getenv("DEV_MODE"):
        GTW_SERVER_ADDR = "tcp://127.0.0.1:5555"

    # 命令类型
    class Command:
        PING = "PING"                  # 心跳探针
        ORDER = "ORDER"                # 下单命令
        CANCEL = "CANCEL"              # 取消订单
        GET_BALANCE = "GET_BALANCE"    # 获取账户余额
        GET_POSITION = "GET_POSITION"  # 获取持仓

    # 响应状态码
    class ResponseCode:
        SUCCESS = 200
        BAD_REQUEST = 400
        SERVER_ERROR = 500
        TIMEOUT = 504


# ============================================================================
# 订单模型
# ============================================================================

class OrderModel:
    """订单数据模型"""

    def __init__(self, order_dict: Dict[str, Any]):
        """
        初始化订单，从 Task #101 生成的 Order Dict

        Expected fields from Task #101:
        {
            "symbol": "AUDUSD",
            "side": "BUY" | "SELL",
            "type": "MARKET" | "LIMIT",
            "volume": 0.1,
            "price": 0.6850,          # 限价单必需
            "stop_loss": 0.6800,      # 可选
            "take_profit": 0.6900,    # 可选
            "timestamp": "2026-01-14T18:40:00Z",
            "risk_score": 0.35        # 风控评分
        }
        """
        self.order_dict = order_dict
        self.validate()

    def validate(self) -> bool:
        """验证订单字段"""
        required_fields = ["symbol", "side", "type", "volume"]

        for field in required_fields:
            if field not in self.order_dict:
                logger.error(f"❌ 订单缺少必需字段: {field}")
                raise ValueError(f"缺少字段: {field}")

        # 验证 side
        if self.order_dict["side"] not in [OrderSide.BUY.value, OrderSide.SELL.value]:
            raise ValueError(f"无效的订单方向: {self.order_dict['side']}")

        # 验证 type
        if self.order_dict["type"] not in [OrderType.MARKET.value, OrderType.LIMIT.value]:
            raise ValueError(f"无效的订单类型: {self.order_dict['type']}")

        # 限价单必须有价格
        if self.order_dict["type"] == OrderType.LIMIT.value and "price" not in self.order_dict:
            raise ValueError("限价单必须提供 price 字段")

        return True

    def to_gtw_format(self) -> Dict[str, Any]:
        """转换为 GTW 理解的格式"""
        return {
            "symbol": self.order_dict["symbol"],
            "side": self.order_dict["side"],
            "type": self.order_dict["type"],
            "volume": float(self.order_dict["volume"]),
            "price": float(self.order_dict.get("price", 0.0)),
            "stop_loss": float(self.order_dict.get("stop_loss", 0.0)),
            "take_profit": float(self.order_dict.get("take_profit", 0.0)),
            "timestamp": self.order_dict.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "risk_score": float(self.order_dict.get("risk_score", 0.0))
        }


# ============================================================================
# ZMQ 客户端
# ============================================================================

class ZMQClient:
    """ZeroMQ 客户端（REQ 模式）"""

    def __init__(self, server_addr: str = GTWProtocol.GTW_SERVER_ADDR):
        self.server_addr = server_addr
        self.context = zmq.Context()
        self.socket = None
        self.logger = logging.getLogger("ZMQClient")

    def connect(self) -> bool:
        """连接到 GTW 服务器"""
        try:
            self.logger.info(f"正在连接 GTW 服务器: {self.server_addr}")
            self.socket = self.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5秒超时
            self.socket.setsockopt(zmq.LINGER, 0)       # 禁用阻塞关闭
            self.socket.connect(self.server_addr)
            self.logger.info(f"✅ ZMQ 连接成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ ZMQ 连接失败: {e}")
            return False

    def send_request(self, request_data: Dict[str, Any], timeout_ms: int = 5000) -> Optional[Dict]:
        """发送请求并接收响应"""
        if not self.socket:
            self.logger.error("❌ ZMQ 套接字未初始化")
            return None

        try:
            # 序列化请求
            request_json = json.dumps(request_data, default=str)
            self.logger.info(f"发送请求: {request_json[:100]}...")
            self.socket.send_string(request_json)

            # 接收响应
            response_json = self.socket.recv_string(timeout=timeout_ms)
            response_data = json.loads(response_json)
            self.logger.info(f"收到响应: {response_json[:100]}...")

            return response_data
        except zmq.Again:
            self.logger.error(f"❌ ZMQ 超时 ({timeout_ms}ms)")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ 响应 JSON 解析失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ ZMQ 通讯失败: {e}")
            return None

    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        self.logger.info("ZMQ 连接已关闭")


# ============================================================================
# GTW 适配器
# ============================================================================

class GTWAdapter:
    """GTW 通讯适配器（运行在 Inf 上）"""

    def __init__(self, gtw_addr: str = GTWProtocol.GTW_SERVER_ADDR):
        self.gtw_addr = gtw_addr
        self.zmq_client = ZMQClient(gtw_addr)
        self.logger = logging.getLogger("GTWAdapter")

    def connect(self) -> bool:
        """连接到 GTW"""
        return self.zmq_client.connect()

    def ping(self) -> Tuple[bool, Optional[Dict]]:
        """
        心跳测试 (Ping GTW)

        返回: (success, response)
        """
        request = {
            "command": GTWProtocol.Command.PING,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info("📡 Ping GTW...")
        response = self.zmq_client.send_request(request)

        if response and response.get("status") == "ONLINE":
            self.logger.info(f"✅ GTW 在线: {response}")
            return True, response
        else:
            self.logger.error(f"❌ GTW 离线或无响应")
            return False, response

    def send_command(
        self,
        action: str,
        symbol: str,
        volume: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        risk_score: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        发送下单命令到 GTW

        参数:
            action: BUY 或 SELL
            symbol: 交易对符号 (如 AUDUSD)
            volume: 交易量
            order_type: MARKET 或 LIMIT
            price: 限价单的价格
            stop_loss: 止损价格 (可选)
            take_profit: 止盈价格 (可选)
            risk_score: 风控评分 (0.0-1.0)

        返回: (success, order_id)
        """
        # 构建订单
        order_dict = {
            "symbol": symbol,
            "side": action,
            "type": order_type,
            "volume": volume,
            "price": price or 0.0,
            "stop_loss": stop_loss or 0.0,
            "take_profit": take_profit or 0.0,
            "risk_score": risk_score,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        try:
            # 验证订单
            order = OrderModel(order_dict)
            gtw_order = order.to_gtw_format()

            # 构建请求
            request = {
                "command": GTWProtocol.Command.ORDER,
                "order": gtw_order,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            self.logger.info(f"📤 发送下单命令: {action} {volume} {symbol} @ {price}")
            response = self.zmq_client.send_request(request)

            if response and response.get("code") == GTWProtocol.ResponseCode.SUCCESS:
                order_id = response.get("order_id", "UNKNOWN")
                self.logger.info(f"✅ 订单已接受 (OrderID: {order_id})")
                return True, order_id
            else:
                error_msg = response.get("message", "未知错误") if response else "无响应"
                self.logger.error(f"❌ 订单被拒绝: {error_msg}")
                return False, None

        except ValueError as e:
            self.logger.error(f"❌ 订单验证失败: {e}")
            return False, None
        except Exception as e:
            self.logger.error(f"❌ 下单异常: {e}")
            return False, None

    def get_balance(self) -> Tuple[bool, Optional[float]]:
        """获取账户余额"""
        request = {
            "command": GTWProtocol.Command.GET_BALANCE,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info("💰 查询账户余额...")
        response = self.zmq_client.send_request(request)

        if response and response.get("code") == GTWProtocol.ResponseCode.SUCCESS:
            balance = response.get("balance", 0.0)
            self.logger.info(f"✅ 账户余额: ${balance:.2f}")
            return True, balance
        else:
            self.logger.error(f"❌ 查询失败")
            return False, None

    def get_position(self, symbol: str) -> Tuple[bool, Optional[Dict]]:
        """获取特定交易对的持仓"""
        request = {
            "command": GTWProtocol.Command.GET_POSITION,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info(f"📊 查询 {symbol} 持仓...")
        response = self.zmq_client.send_request(request)

        if response and response.get("code") == GTWProtocol.ResponseCode.SUCCESS:
            position = response.get("position", {})
            self.logger.info(f"✅ 持仓信息: {position}")
            return True, position
        else:
            self.logger.error(f"❌ 查询失败")
            return False, None

    def close(self):
        """关闭连接"""
        self.zmq_client.close()


# ============================================================================
# 主程序和测试
# ============================================================================

def test_gtw_connection():
    """测试 GTW 连接（用于 Step 4: 物理验尸）"""
    logger.info("\n" + "="*70)
    logger.info("GTW 适配器连接测试")
    logger.info("="*70)

    adapter = GTWAdapter()

    # 连接
    if not adapter.connect():
        logger.error("❌ 无法连接到 GTW")
        return False

    # Ping 测试
    success, response = adapter.ping()
    if not success:
        logger.error("❌ GTW Ping 失败")
        adapter.close()
        return False

    logger.info(f"✅ GTW Ping 成功")

    # 查询余额
    success, balance = adapter.get_balance()
    if success:
        logger.info(f"✅ 账户余额: {balance}")

    adapter.close()
    return True


if __name__ == "__main__":
    logger.info("GTW 适配器 - 独立测试模式")
    test_gtw_connection()
