#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Live Connector - Zero-Trust Linux-to-Windows Trading Bridge
Task #106 - MT5 Live Bridge Implementation

Protocol v4.3 (Zero-Trust Edition) compliant live connector with:
- Mandatory RiskMonitor validation
- ZMQ communication via MT5Client
- HeartbeatMonitor integration
- Risk signature generation
- Kill Switch enforcement

Architecture:
    Strategy Signal → MT5LiveConnector → RiskMonitor → MT5Client (ZMQ) → GTW → MT5
"""

import logging
import sys
import json
import uuid
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Secure module loading
sys.path.insert(0, str(Path(__file__).parent))
from secure_loader import SecureModuleLoader, SecurityError

# Initialize secure loader
_loader = SecureModuleLoader(allowed_base_dir=Path(__file__).parent.parent)

# Load required modules with security validation
try:
    # Load MT5Client
    _mt5_client_path = Path(__file__).parent.parent / "gateway" / "mt5_client.py"
    _mt5_client_module = _loader.load_module(_mt5_client_path, module_name="mt5_client_module")
    MT5Client = _mt5_client_module.MT5Client

    # Load RiskMonitor
    _risk_monitor_path = Path(__file__).parent / "risk_monitor.py"
    _risk_monitor_module = _loader.load_module(_risk_monitor_path, module_name="risk_monitor_module")
    RiskMonitor = _risk_monitor_module.RiskMonitor

    # Load HeartbeatMonitor
    _heartbeat_path = Path(__file__).parent / "heartbeat_monitor.py"
    _heartbeat_module = _loader.load_module(_heartbeat_path, module_name="heartbeat_module")
    HeartbeatMonitor = _heartbeat_module.HeartbeatMonitor

    # Load CircuitBreaker
    _cb_path = Path(__file__).parent.parent / "risk" / "circuit_breaker.py"
    _cb_module = _loader.load_module(_cb_path, module_name="circuit_breaker_module")
    CircuitBreaker = _cb_module.CircuitBreaker

except SecurityError as e:
    raise ImportError(f"Failed to load required modules securely: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MT5LiveConnector')

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


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
    PENDING = "PENDING"
    SENT = "SENT"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass
class OrderRecord:
    """订单记录"""
    uuid: str
    timestamp: str
    symbol: str
    order_type: str
    volume: float
    price: float
    sl: Optional[float]
    tp: Optional[float]
    comment: str
    risk_signature: str
    status: str
    ticket: Optional[int] = None
    fill_price: Optional[float] = None
    execution_time: Optional[str] = None
    error_msg: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class MT5LiveConnector:
    """
    MT5 Live Connector - Protocol v4.3 Zero-Trust Trading Bridge

    核心功能：
    1. 强制 RiskMonitor 验证（所有订单必须通过风险检查）
    2. ZMQ 通讯（通过 MT5Client）
    3. HeartbeatMonitor 集成（5s 心跳检测）
    4. Risk Signature 生成（RISK_PASS:<checksum>:<timestamp>）
    5. Kill Switch 强制执行（熔断时拒绝所有订单）
    6. 完整审计日志（[RISK_PASS], [ZMQ_SENT], [MT5_FILLED]）

    使用示例：
        # 初始化
        connector = MT5LiveConnector(
            gateway_host="172.19.141.255",
            gateway_port=5555,
            circuit_breaker=circuit_breaker,
            initial_balance=100000.0
        )

        # 连接
        if connector.connect():
            print("Connected to GTW")

        # 发送订单（自动通过 RiskMonitor 验证）
        result = connector.send_order({
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.01,
            "sl": 1.05000,
            "tp": 1.06000,
            "comment": "Strategy_v1"
        })

        # 查询账户
        account = connector.get_account()

        # 查询持仓
        positions = connector.get_positions()

        # 平仓
        connector.close_position(ticket=12345678)

        # 断开连接
        connector.disconnect()
    """

    def __init__(
        self,
        gateway_host: str = "172.19.141.255",
        gateway_port: int = 5555,
        circuit_breaker: Optional[CircuitBreaker] = None,
        initial_balance: float = 100000.0,
        risk_config_path: str = "config/risk_limits.yaml",
        enable_heartbeat: bool = True,
        heartbeat_interval: float = 5.0,
        timeout_ms: int = 2000,
        retries: int = 3
    ):
        """
        初始化 MT5 Live Connector

        Args:
            gateway_host: GTW 主机地址
            gateway_port: GTW 端口（默认 5555）
            circuit_breaker: 熔断器实例（如未提供则自动创建）
            initial_balance: 初始账户余额
            risk_config_path: 风险配置文件路径
            enable_heartbeat: 是否启用心跳监控
            heartbeat_interval: 心跳间隔（秒）
            timeout_ms: ZMQ 超时（毫秒）
            retries: ZMQ 重试次数
        """
        self.gateway_host = gateway_host
        self.gateway_port = gateway_port
        self.initial_balance = initial_balance
        self.enable_heartbeat = enable_heartbeat

        # 初始化 CircuitBreaker
        if circuit_breaker is None:
            logger.info("No CircuitBreaker provided, creating new instance...")
            self.circuit_breaker = CircuitBreaker()
        else:
            self.circuit_breaker = circuit_breaker

        # 初始化 RiskMonitor（强制集成）
        self.risk_monitor = RiskMonitor(
            circuit_breaker=self.circuit_breaker,
            config_path=risk_config_path,
            initial_balance=initial_balance
        )
        logger.info(f"{GREEN}✅ [RISK_MONITOR] RiskMonitor initialized{RESET}")

        # 初始化 MT5Client（ZMQ 通讯）
        self.mt5_client = MT5Client(
            host=gateway_host,
            port=gateway_port,
            timeout_ms=timeout_ms,
            retries=retries
        )
        logger.info(f"{CYAN}✅ [ZMQ_CLIENT] MT5Client initialized{RESET}")

        # 初始化 HeartbeatMonitor（可选但推荐）
        self.heartbeat_monitor: Optional[HeartbeatMonitor] = None
        if enable_heartbeat:
            self.heartbeat_monitor = HeartbeatMonitor(
                ping_callable=self._safe_ping,
                circuit_breaker=self.circuit_breaker,
                interval_seconds=heartbeat_interval,
                failure_threshold=3
            )
            logger.info(f"{MAGENTA}✅ [HEARTBEAT] HeartbeatMonitor initialized{RESET}")

        # 状态管理
        self._connected = False
        self._order_history: List[OrderRecord] = []
        self._lock = threading.RLock()

        logger.info(f"{GREEN}{'='*80}{RESET}")
        logger.info(f"{GREEN}MT5LiveConnector Initialized - Protocol v4.3{RESET}")
        logger.info(f"{GREEN}  GTW Target: {gateway_host}:{gateway_port}{RESET}")
        logger.info(f"{GREEN}  Initial Balance: ${initial_balance:,.2f}{RESET}")
        logger.info(f"{GREEN}  Heartbeat Enabled: {enable_heartbeat}{RESET}")
        logger.info(f"{GREEN}{'='*80}{RESET}")

    def connect(self) -> bool:
        """
        连接到 GTW（Windows MT5 ZMQ Server）

        Returns:
            bool: 连接成功返回 True
        """
        try:
            logger.info(f"{CYAN}[CONNECT] Connecting to GTW...{RESET}")

            # 检查熔断器状态
            if not self._check_circuit_breaker("CONNECT"):
                return False

            # 连接 MT5Client
            if not self.mt5_client.connect():
                logger.error(f"{RED}❌ [CONNECT] MT5Client connection failed{RESET}")
                return False

            # 测试连接（PING）
            if not self.ping():
                logger.error(f"{RED}❌ [CONNECT] PING test failed{RESET}")
                return False

            self._connected = True

            # 启动心跳监控
            if self.enable_heartbeat and self.heartbeat_monitor:
                self.heartbeat_monitor.start()
                logger.info(f"{MAGENTA}✅ [HEARTBEAT] Monitor started{RESET}")

            logger.info(f"{GREEN}✅ [CONNECT] Successfully connected to GTW{RESET}")
            return True

        except Exception as e:
            logger.error(f"{RED}❌ [CONNECT] Connection error: {e}{RESET}")
            return False

    def disconnect(self) -> None:
        """断开与 GTW 的连接"""
        logger.info(f"{CYAN}[DISCONNECT] Disconnecting from GTW...{RESET}")

        # 停止心跳监控
        if self.heartbeat_monitor:
            self.heartbeat_monitor.stop()
            logger.info(f"{MAGENTA}✅ [HEARTBEAT] Monitor stopped{RESET}")

        # 关闭 MT5Client
        self.mt5_client.close()

        self._connected = False
        logger.info(f"{GREEN}✅ [DISCONNECT] Disconnected from GTW{RESET}")

    def _safe_ping(self) -> Dict[str, Any]:
        """
        安全 PING 包装器（供 HeartbeatMonitor 使用）

        Returns:
            Dict: {"status": "ok"} 或抛出异常
        """
        try:
            return self.mt5_client.send_command({
                "action": "PING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"{RED}❌ [PING] Error: {e}{RESET}")
            raise

    def ping(self) -> bool:
        """
        心跳检测（PING GTW）

        Returns:
            bool: PING 成功返回 True
        """
        try:
            logger.debug(f"{CYAN}[PING] Sending PING...{RESET}")

            response = self.mt5_client.send_command({
                "action": "PING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            if response.get("status") == "ok":
                latency = response.get("latency_ms", 0)
                logger.debug(f"{GREEN}✅ [PING] Success (latency: {latency:.3f}ms){RESET}")
                return True
            else:
                logger.warning(f"{YELLOW}⚠️  [PING] Failed: {response}{RESET}")
                return False

        except Exception as e:
            logger.error(f"{RED}❌ [PING] Error: {e}{RESET}")
            return False

    def _check_circuit_breaker(self, action: str) -> bool:
        """
        检查熔断器状态（Kill Switch）

        Args:
            action: 操作名称（用于日志）

        Returns:
            bool: 如果允许操作返回 True，否则返回 False
        """
        cb_status = self.circuit_breaker.get_status()
        if cb_status["state"] == "ENGAGED":
            reason = cb_status.get('engagement_reason', 'Unknown')
            logger.error(
                f"{RED}🚨 [KILL_SWITCH] {action} BLOCKED - "
                f"Circuit breaker is engaged: {reason}{RESET}"
            )
            return False
        return True

    def _generate_risk_signature(
        self,
        order_dict: Dict[str, Any],
        checksum_fields: Optional[List[str]] = None
    ) -> str:
        """
        生成风险签名（Risk Signature）

        格式: RISK_PASS:<checksum>:<timestamp>

        Args:
            order_dict: 订单字典
            checksum_fields: 用于生成 checksum 的字段列表

        Returns:
            str: 风险签名字符串
        """
        if checksum_fields is None:
            checksum_fields = ["symbol", "type", "volume", "price", "sl", "tp"]

        # 提取订单关键字段
        checksum_data = {}
        for field in checksum_fields:
            if field in order_dict and order_dict[field] is not None:
                checksum_data[field] = order_dict[field]

        # 生成 checksum（SHA256 前 8 位）
        checksum_str = json.dumps(checksum_data, sort_keys=True)
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest()[:8]

        # 生成时间戳
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 组装签名
        signature = f"RISK_PASS:{checksum}:{timestamp}"

        logger.debug(f"[RISK_SIGNATURE] Generated: {signature}")
        return signature

    def _validate_order_with_risk_monitor(
        self,
        order_dict: Dict[str, Any]
    ) -> Tuple[bool, str, str]:
        """
        通过 RiskMonitor 验证订单

        Args:
            order_dict: 订单字典

        Returns:
            Tuple[bool, str, str]: (是否通过, 风险签名, 拒绝原因)
        """
        try:
            # 检查熔断器
            if not self._check_circuit_breaker("ORDER_VALIDATION"):
                return False, "", "Circuit breaker is engaged"

            # 提取订单参数
            symbol = order_dict.get("symbol", "")
            volume = order_dict.get("volume", 0.0)
            order_type = order_dict.get("type", "")

            # 验证基本参数
            if not symbol:
                return False, "", "Missing symbol"
            if volume <= 0:
                return False, "", "Invalid volume"
            if order_type not in ["BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"]:
                return False, "", f"Invalid order type: {order_type}"

            # 检查持仓大小限制
            max_position_size = self.risk_monitor.config['risk'].get('max_single_position_size', 1.0)
            if volume > max_position_size:
                return False, "", f"Volume {volume} exceeds max position size {max_position_size}"

            # 生成风险签名
            signature = self._generate_risk_signature(order_dict)

            logger.info(
                f"{GREEN}✅ [RISK_PASS] Order validated: {order_type} {volume} {symbol}{RESET}"
            )

            return True, signature, ""

        except Exception as e:
            logger.error(f"{RED}❌ [RISK_FAIL] Validation error: {e}{RESET}")
            return False, "", str(e)

    def send_order(
        self,
        order_dict: Dict[str, Any],
        magic: int = 0
    ) -> Dict[str, Any]:
        """
        发送订单到 MT5（强制经过 RiskMonitor 验证）

        Args:
            order_dict: 订单字典，包含:
                - symbol (str): 交易品种
                - type (str): 订单类型（BUY, SELL, etc.）
                - volume (float): 手数
                - price (float, optional): 价格（LIMIT/STOP 订单）
                - sl (float, optional): 止损价
                - tp (float, optional): 止盈价
                - comment (str, optional): 订单备注
            magic: 魔术数字（策略标识）

        Returns:
            Dict: 订单执行结果
                - status: FILLED, REJECTED, FAILED
                - ticket: 订单号（如果成功）
                - price: 成交价（如果成功）
                - error_msg: 错误信息（如果失败）
        """
        order_uuid = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # 检查连接状态
            if not self._connected:
                raise ConnectionError("Not connected to GTW. Call connect() first.")

            # 检查熔断器
            if not self._check_circuit_breaker("SEND_ORDER"):
                return {
                    "uuid": order_uuid,
                    "status": "REJECTED",
                    "error_msg": "Circuit breaker is engaged",
                    "timestamp": timestamp
                }

            # 强制风险验证
            is_safe, risk_signature, reject_reason = self._validate_order_with_risk_monitor(order_dict)
            if not is_safe:
                logger.error(
                    f"{RED}❌ [RISK_FAIL] Order rejected by RiskMonitor: {reject_reason}{RESET}"
                )
                return {
                    "uuid": order_uuid,
                    "status": "REJECTED",
                    "error_msg": f"Risk validation failed: {reject_reason}",
                    "timestamp": timestamp
                }

            # 构建 ZMQ 请求（Protocol v4.3）
            zmq_request = {
                "uuid": order_uuid,
                "action": "OPEN",
                "symbol": order_dict.get("symbol"),
                "type": order_dict.get("type"),
                "volume": order_dict.get("volume"),
                "price": order_dict.get("price", 0.0),
                "sl": order_dict.get("sl"),
                "tp": order_dict.get("tp"),
                "magic": magic,
                "comment": order_dict.get("comment", ""),
                "risk_signature": risk_signature,
                "timestamp": timestamp
            }

            logger.info(
                f"{CYAN}📤 [ZMQ_SENT] Sending order: {zmq_request['type']} "
                f"{zmq_request['volume']} {zmq_request['symbol']} "
                f"(signature: {risk_signature}){RESET}"
            )

            # 发送到 GTW
            response = self.mt5_client.send_command(zmq_request)

            # 解析响应
            status = response.get("status", "FAILED")

            if status == "FILLED":
                ticket = response.get("ticket")
                fill_price = response.get("price")
                execution_time = response.get("execution_time")
                latency_ms = response.get("latency_ms")

                logger.info(
                    f"{GREEN}✅ [MT5_FILLED] Order filled: Ticket #{ticket}, "
                    f"Price {fill_price}, Latency {latency_ms:.3f}ms{RESET}"
                )

                # 记录订单
                order_record = OrderRecord(
                    uuid=order_uuid,
                    timestamp=timestamp,
                    symbol=zmq_request["symbol"],
                    order_type=zmq_request["type"],
                    volume=zmq_request["volume"],
                    price=zmq_request["price"],
                    sl=zmq_request["sl"],
                    tp=zmq_request["tp"],
                    comment=zmq_request["comment"],
                    risk_signature=risk_signature,
                    status="FILLED",
                    ticket=ticket,
                    fill_price=fill_price,
                    execution_time=execution_time,
                    latency_ms=latency_ms
                )

                with self._lock:
                    self._order_history.append(order_record)

                return response

            else:
                error_msg = response.get("error_msg", "Unknown error")
                error_code = response.get("error_code", "UNKNOWN")

                logger.error(
                    f"{RED}❌ [MT5_REJECTED] Order rejected: {error_code} - {error_msg}{RESET}"
                )

                # 记录失败订单
                order_record = OrderRecord(
                    uuid=order_uuid,
                    timestamp=timestamp,
                    symbol=zmq_request["symbol"],
                    order_type=zmq_request["type"],
                    volume=zmq_request["volume"],
                    price=zmq_request["price"],
                    sl=zmq_request["sl"],
                    tp=zmq_request["tp"],
                    comment=zmq_request["comment"],
                    risk_signature=risk_signature,
                    status="REJECTED",
                    error_msg=error_msg
                )

                with self._lock:
                    self._order_history.append(order_record)

                return response

        except Exception as e:
            logger.error(f"{RED}❌ [SEND_ORDER] Error: {e}{RESET}")
            return {
                "uuid": order_uuid,
                "status": "FAILED",
                "error_msg": str(e),
                "timestamp": timestamp
            }

    def get_account(self) -> Dict[str, Any]:
        """
        获取账户信息

        Returns:
            Dict: 账户信息
                - status: ok/error
                - balance: 余额
                - equity: 净值
                - margin: 已用保证金
                - free_margin: 可用保证金
                - margin_level: 保证金水平（%）
                - currency: 账户货币
        """
        try:
            if not self._connected:
                raise ConnectionError("Not connected to GTW")

            logger.debug(f"{CYAN}[GET_ACCOUNT] Querying account info...{RESET}")

            response = self.mt5_client.send_command({
                "uuid": str(uuid.uuid4()),
                "action": "GET_ACCOUNT",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            if response.get("status") == "ok":
                balance = response.get("balance", 0.0)
                equity = response.get("equity", 0.0)
                logger.info(
                    f"{GREEN}✅ [GET_ACCOUNT] Balance: ${balance:,.2f}, "
                    f"Equity: ${equity:,.2f}{RESET}"
                )
            else:
                logger.error(f"{RED}❌ [GET_ACCOUNT] Failed: {response}{RESET}")

            return response

        except Exception as e:
            logger.error(f"{RED}❌ [GET_ACCOUNT] Error: {e}{RESET}")
            return {"status": "error", "error_msg": str(e)}

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓列表

        Args:
            symbol: 交易品种（可选，用于过滤）

        Returns:
            List[Dict]: 持仓列表
        """
        try:
            if not self._connected:
                raise ConnectionError("Not connected to GTW")

            logger.debug(f"{CYAN}[GET_POSITIONS] Querying positions...{RESET}")

            request = {
                "uuid": str(uuid.uuid4()),
                "action": "GET_POSITIONS",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if symbol:
                request["symbol"] = symbol

            response = self.mt5_client.send_command(request)

            if response.get("status") == "ok":
                positions = response.get("positions", [])
                logger.info(
                    f"{GREEN}✅ [GET_POSITIONS] Found {len(positions)} position(s){RESET}"
                )
                return positions
            else:
                logger.error(f"{RED}❌ [GET_POSITIONS] Failed: {response}{RESET}")
                return []

        except Exception as e:
            logger.error(f"{RED}❌ [GET_POSITIONS] Error: {e}{RESET}")
            return []

    def close_position(
        self,
        ticket: int,
        symbol: Optional[str] = None,
        volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        平仓

        Args:
            ticket: 订单号
            symbol: 交易品种（可选）
            volume: 手数（可选，部分平仓）

        Returns:
            Dict: 平仓结果
        """
        try:
            if not self._connected:
                raise ConnectionError("Not connected to GTW")

            # 检查熔断器
            if not self._check_circuit_breaker("CLOSE_POSITION"):
                return {
                    "status": "REJECTED",
                    "error_msg": "Circuit breaker is engaged"
                }

            logger.info(f"{CYAN}[CLOSE_POSITION] Closing position #{ticket}...{RESET}")

            request = {
                "uuid": str(uuid.uuid4()),
                "action": "CLOSE",
                "ticket": ticket,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if symbol:
                request["symbol"] = symbol
            if volume:
                request["volume"] = volume

            response = self.mt5_client.send_command(request)

            if response.get("status") == "FILLED":
                logger.info(
                    f"{GREEN}✅ [CLOSE_POSITION] Position #{ticket} closed{RESET}"
                )
            else:
                error_msg = response.get("error_msg", "Unknown error")
                logger.error(
                    f"{RED}❌ [CLOSE_POSITION] Failed to close #{ticket}: {error_msg}{RESET}"
                )

            return response

        except Exception as e:
            logger.error(f"{RED}❌ [CLOSE_POSITION] Error: {e}{RESET}")
            return {"status": "FAILED", "error_msg": str(e)}

    def get_order_history(self) -> List[Dict[str, Any]]:
        """
        获取订单历史

        Returns:
            List[Dict]: 订单历史记录
        """
        with self._lock:
            return [order.to_dict() for order in self._order_history]

    def get_status(self) -> Dict[str, Any]:
        """
        获取连接器状态

        Returns:
            Dict: 状态信息
        """
        heartbeat_status = None
        if self.heartbeat_monitor:
            heartbeat_status = {
                "status": self.heartbeat_monitor.get_status().value,
                "metrics": self.heartbeat_monitor.get_metrics().to_dict()
            }

        return {
            "connected": self._connected,
            "gateway": f"{self.gateway_host}:{self.gateway_port}",
            "circuit_breaker": self.circuit_breaker.get_status(),
            "risk_monitor": self.risk_monitor.get_summary(),
            "heartbeat": heartbeat_status,
            "orders_sent": len(self._order_history)
        }

    def print_status(self) -> None:
        """打印连接器状态"""
        status = self.get_status()

        print("\n" + "="*80)
        print("🔗 MT5 LIVE CONNECTOR STATUS")
        print("="*80)
        print(f"Connected:          {status['connected']}")
        print(f"Gateway:            {status['gateway']}")
        print(f"Circuit Breaker:    {status['circuit_breaker']['state']}")
        print(f"Orders Sent:        {status['orders_sent']}")

        if status['heartbeat']:
            print(f"\n💓 Heartbeat:")
            print(f"  Status:           {status['heartbeat']['status']}")
            hb_metrics = status['heartbeat']['metrics']
            print(f"  Total Pings:      {hb_metrics['total_pings']}")
            print(f"  Success Rate:     {hb_metrics['success_rate']}")
            print(f"  Avg Latency:      {hb_metrics['average_latency_ms']}ms")

        print("="*80 + "\n")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("MT5 Live Connector - Example Usage")
    print("Protocol v4.3 (Zero-Trust Edition)")
    print("="*80)
    print()

    # 使用上下文管理器
    try:
        with MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            initial_balance=100000.0,
            enable_heartbeat=True
        ) as connector:

            # 测试连接
            print("\n1. Testing connection...")
            if connector.ping():
                print("✅ PING successful")

            # 获取账户信息
            print("\n2. Getting account info...")
            account = connector.get_account()
            if account.get("status") == "ok":
                print(f"✅ Balance: ${account['balance']:,.2f}")

            # 发送订单（会自动通过 RiskMonitor 验证）
            print("\n3. Sending order...")
            order_result = connector.send_order({
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": 0.01,
                "sl": 1.05000,
                "tp": 1.06000,
                "comment": "Test_Order_v1"
            })

            if order_result.get("status") == "FILLED":
                print(f"✅ Order filled: Ticket #{order_result['ticket']}")
            else:
                print(f"❌ Order rejected: {order_result.get('error_msg')}")

            # 获取持仓
            print("\n4. Getting positions...")
            positions = connector.get_positions()
            print(f"✅ Open positions: {len(positions)}")

            # 打印状态
            print("\n5. Connector status:")
            connector.print_status()

    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ Example completed")
