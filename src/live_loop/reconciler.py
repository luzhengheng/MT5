#!/usr/bin/env python3
"""
State Reconciliation Engine for Task #108
==========================================

此模块实现了 Linux 策略节点与 Windows 交易网关之间的状态同步机制。
确保策略引擎在重启或崩溃恢复后能立即获取真实的持仓和账户信息。

核心流程：
1. 启动时向网关发送 SYNC_ALL 请求
2. 获取真实的持仓（positions）和账户资金（account）
3. 更新本地策略引擎的状态
4. 阻塞式等待 - 直到同步成功才允许策略启动

Protocol v4.3 零信任原则：
- MT5 是唯一的真理来源 (Single Source of Truth)
- 本地内存仅作为缓存，启动时必须被覆盖
- Magic Number 用于区分不同策略的订单
"""

import json
import logging
import time
import zmq
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# 常量定义
# ============================================================================

# ZMQ 连接配置
ZMQ_GATEWAY_IP = "172.19.141.255"  # Windows Gateway 内网 IP
ZMQ_REQ_PORT = 5555  # 交易指令通道

# 同步参数
SYNC_TIMEOUT_S = 3  # 同步超时（秒）
SYNC_RETRY_COUNT = 3  # 同步重试次数
SYNC_RETRY_INTERVAL_S = 1  # 重试间隔（秒）

# Magic Number（策略唯一标识）
MAGIC_NUMBER = 202401  # Task #108 策略的全局唯一标识


# ============================================================================
# 异常定义
# ============================================================================

class SystemHaltException(Exception):
    """
    系统暂停异常

    当状态同步失败时抛出此异常，表示系统处于未知状态，
    严禁启动策略引擎。
    """
    pass


class SyncTimeoutException(SystemHaltException):
    """同步超时异常"""
    pass


class SyncResponseException(SystemHaltException):
    """同步响应错误异常"""
    pass


# ============================================================================
# 数据结构
# ============================================================================

class Position:
    """单个持仓信息"""
    def __init__(self, data: Dict[str, Any]):
        self.symbol = data.get('symbol')
        self.ticket = data.get('ticket')
        self.volume = data.get('volume', 0.0)
        self.profit = data.get('profit', 0.0)
        self.price_current = data.get('price_current', 0.0)
        self.price_open = data.get('price_open', 0.0)
        self.type = data.get('type', 'BUY')  # BUY or SELL
        self.time_open = data.get('time_open', 0)

    def __repr__(self):
        return (f"Position(symbol={self.symbol}, ticket={self.ticket}, "
                f"volume={self.volume}, type={self.type}, profit={self.profit})")


class AccountInfo:
    """账户信息"""
    def __init__(self, data: Dict[str, Any]):
        self.balance = data.get('balance', 0.0)
        self.equity = data.get('equity', 0.0)
        self.margin_free = data.get('margin_free', 0.0)
        self.margin_used = data.get('margin_used', 0.0)
        self.margin_level = data.get('margin_level', 0.0)
        self.leverage = data.get('leverage', 1)

    def __repr__(self):
        return (f"AccountInfo(balance={self.balance}, equity={self.equity}, "
                f"margin_free={self.margin_free})")


class SyncResponse:
    """状态同步响应"""
    def __init__(self, data: Dict[str, Any]):
        self.status = data.get('status', 'ERROR')
        self.account = AccountInfo(data.get('account', {}))
        self.positions = [Position(p) for p in data.get('positions', [])]
        self.message = data.get('message', '')

    def is_ok(self) -> bool:
        return self.status == 'OK'

    def __repr__(self):
        return (f"SyncResponse(status={self.status}, "
                f"positions={len(self.positions)}, account={self.account})")


# ============================================================================
# Reconciler 主类
# ============================================================================

class StateReconciler:
    """
    状态对账引擎

    负责与 Windows 网关同步持仓和账户信息。
    采用阻塞式设计 - 同步失败时直接抛异常，阻止策略启动。
    """

    def __init__(self):
        """初始化 Reconciler"""
        self.zmq_context = None
        self.zmq_socket = None
        self.last_sync_time = 0
        self.sync_count = 0

        logger.info("[Reconciler] 初始化完成")

    def connect_to_gateway(self) -> bool:
        """
        连接到 Windows 网关

        Returns:
            True 如果连接成功，False 否则
        """
        try:
            if not self.zmq_context:
                self.zmq_context = zmq.Context()

            if not self.zmq_socket:
                self.zmq_socket = self.zmq_context.socket(zmq.REQ)
                # 设置超时
                self.zmq_socket.setsockopt(zmq.RCVTIMEO, int(SYNC_TIMEOUT_S * 1000))
                self.zmq_socket.setsockopt(zmq.LINGER, 0)

                gateway_addr = f"tcp://{ZMQ_GATEWAY_IP}:{ZMQ_REQ_PORT}"
                self.zmq_socket.connect(gateway_addr)

            logger.info(f"[Reconciler] ✅ 已连接到网关: tcp://{ZMQ_GATEWAY_IP}:{ZMQ_REQ_PORT}")
            return True

        except Exception as e:
            logger.error(f"[Reconciler] ❌ 网关连接失败: {e}")
            return False

    def disconnect_from_gateway(self):
        """断开网关连接"""
        if self.zmq_socket:
            try:
                self.zmq_socket.close()
            except Exception as e:
                logger.warning(f"[Reconciler] Socket 关闭失败: {e}")
            self.zmq_socket = None

        if self.zmq_context:
            try:
                self.zmq_context.term()
            except Exception as e:
                logger.warning(f"[Reconciler] Context 销毁失败: {e}")
            self.zmq_context = None

    def send_sync_request(self) -> SyncResponse:
        """
        发送状态同步请求

        Returns:
            SyncResponse 对象

        Raises:
            SyncTimeoutException: 如果请求超时
            SyncResponseException: 如果响应格式错误
        """
        try:
            # 构造同步请求
            sync_request = {
                "action": "SYNC_ALL",
                "magic_number": MAGIC_NUMBER,
                "timestamp": int(time.time())
            }

            logger.debug(f"[Reconciler] 发送同步请求: {json.dumps(sync_request)}")

            # 发送请求
            self.zmq_socket.send_json(sync_request)

            # 等待响应
            try:
                response_data = self.zmq_socket.recv_json()
            except zmq.error.Again:
                raise SyncTimeoutException(
                    f"同步请求超时 ({SYNC_TIMEOUT_S}s)"
                )

            # 解析响应
            response = SyncResponse(response_data)

            if not response.is_ok():
                raise SyncResponseException(
                    f"网关返回错误: {response.message}"
                )

            logger.debug(f"[Reconciler] 收到同步响应: {response}")
            return response

        except zmq.error.ZMQError as e:
            raise SyncResponseException(f"ZMQ 通讯错误: {e}")
        except json.JSONDecodeError as e:
            raise SyncResponseException(f"JSON 解析错误: {e}")

    def perform_startup_sync(self) -> SyncResponse:
        """
        执行启动同步 (Blocking Sync Gate)

        这是一个阻塞操作 - 如果同步失败，会抛异常并阻止策略启动。

        Returns:
            SyncResponse 对象

        Raises:
            SystemHaltException: 如果同步失败
        """
        logger.info("[Reconciler] ========== 启动状态同步 ==========")
        logger.info("[Reconciler] 正在从网关恢复持仓和账户信息...")

        last_error = None

        for attempt in range(1, SYNC_RETRY_COUNT + 1):
            try:
                logger.info(f"[Reconciler] 尝试 {attempt}/{SYNC_RETRY_COUNT}...")

                # 连接到网关
                if not self.connect_to_gateway():
                    raise SystemHaltException("无法连接到网关")

                # 发送同步请求
                response = self.send_sync_request()

                # 同步成功
                self.last_sync_time = time.time()
                self.sync_count += 1

                logger.info("[Reconciler] ========== 启动同步成功 ==========")
                logger.info(f"[Reconciler] ✅ 已同步 {len(response.positions)} 个持仓")
                logger.info(f"[Reconciler] ✅ 账户余额: {response.account.balance}")
                logger.info(f"[Reconciler] ✅ 可用保证金: {response.account.margin_free}")

                for pos in response.positions:
                    logger.info(
                        f"[Reconciler] [SYNC_POSITION] {pos.symbol} "
                        f"({pos.type}) Volume={pos.volume} Profit={pos.profit}"
                    )

                return response

            except SystemHaltException as e:
                last_error = e
                logger.warning(f"[Reconciler] 第 {attempt} 次尝试失败: {e}")

                # 等待后重试
                if attempt < SYNC_RETRY_COUNT:
                    logger.info(
                        f"[Reconciler] 等待 {SYNC_RETRY_INTERVAL_S} 秒后重试..."
                    )
                    time.sleep(SYNC_RETRY_INTERVAL_S)

        # 所有重试均失败
        logger.error("[Reconciler] ❌ 启动同步最终失败")
        raise SystemHaltException(
            f"经过 {SYNC_RETRY_COUNT} 次重试，仍无法同步状态: {last_error}"
        )

    def get_last_sync_time(self) -> float:
        """获取上次同步时间"""
        return self.last_sync_time

    def get_sync_count(self) -> int:
        """获取同步次数"""
        return self.sync_count

    def __del__(self):
        """清理资源"""
        self.disconnect_from_gateway()


# ============================================================================
# 全局 Reconciler 单例
# ============================================================================

_reconciler_instance = None


def get_state_reconciler() -> StateReconciler:
    """获取 Reconciler 单例"""
    global _reconciler_instance
    if _reconciler_instance is None:
        _reconciler_instance = StateReconciler()
    return _reconciler_instance
