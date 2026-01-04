#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EODHD Real-Time WebSocket Market Data Feed
=============================================

实现 EODHD WebSocket 客户端，提供实时 Forex 行情数据。

架构：
  EODHD Cloud (WebSocket)
    ↓
  EodhdWsClient (this)
    ↓
  ZMQ PUB (Local Broadcast)

功能：
- 实时订阅外汇品种（如 EURUSD）
- 自动重连与指数退避 (Exponential Backoff)
- Heartbeat 保活机制
- 实时转发到 ZMQ PUB 端口
"""

import os
import json
import asyncio
import logging
import datetime
import time
from typing import Optional, Dict, Any, Set, Callable
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

try:
    import websockets
except ImportError:
    websockets = None

try:
    import zmq
except ImportError:
    zmq = None

# 配置日志
logger = logging.getLogger(__name__)


class EodhdWsClient:
    """
    EODHD WebSocket 客户端 - 实时行情数据流

    订阅流程：
      1. 连接到 WSS 端点
      2. 发送订阅请求: {"action": "subscribe", "symbols": "EURUSD"}
      3. 接收实时 Tick 数据: {"s": "EURUSD", "p": 1.0543, "t": 1704153600}
      4. 转发到 ZMQ PUB 端口

    重连策略：
      - 初始延迟: 1 秒
      - 最大延迟: 60 秒
      - 增长因子: 1.5 (exponential backoff)
      - 最多重试: 无限（直到连接恢复）

    Heartbeat:
      - 每 30 秒发送心跳
      - 防止连接因为无活动而被断开
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        ws_url: Optional[str] = None,
        zmq_port: int = 5556,
        symbols: Optional[Set[str]] = None,
        log_file: str = "VERIFY_LOG.log"
    ):
        """
        初始化 EODHD WebSocket 客户端

        参数:
            api_token (str): EODHD API Token（从环境变量读取）
            ws_url (str): WebSocket 端点 URL（从环境变量读取）
            zmq_port (int): ZMQ PUB 端口（默认 5556）
            symbols (set): 初始订阅品种列表
            log_file (str): 日志文件路径
        """
        # 加载环境变量
        self.api_token = api_token or os.getenv("EODHD_API_TOKEN", "demo")
        self.ws_url = ws_url or os.getenv("EODHD_WS_URL", "wss://ws.eodhistoricaldata.com/ws/forex")
        self.zmq_port = zmq_port
        self.log_file = log_file

        # 订阅品种集合
        self.symbols: Set[str] = symbols or {"EURUSD"}

        # WebSocket 连接状态
        self.ws = None
        self.is_connected = False
        self.reconnect_count = 0

        # 重连参数（指数退避）
        self.base_delay = 1.0      # 初始延迟（秒）
        self.max_delay = 60.0      # 最大延迟（秒）
        self.backoff_factor = 1.5  # 增长因子
        self.current_delay = self.base_delay

        # ZMQ 发布者
        self.zmq_context = None
        self.zmq_pub = None

        # 心跳计时
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30  # 秒

        # 统计数据
        self.stats = {
            "ticks_received": 0,
            "ticks_sent": 0,
            "reconnects": 0,
            "start_time": datetime.datetime.now()
        }

        self._init_zmq()
        self._log("[INFO] EodhdWsClient 初始化完成", level="INFO")

    def _init_zmq(self):
        """初始化 ZMQ PUB 发布者"""
        if zmq is None:
            self._log("[WARN] ZMQ 库未安装，数据将不会转发到 PUB 端口", level="WARN")
            return

        try:
            self.zmq_context = zmq.Context()
            self.zmq_pub = self.zmq_context.socket(zmq.PUB)
            self.zmq_pub.bind(f"tcp://0.0.0.0:{self.zmq_port}")
            self._log(f"[INFO] ZMQ PUB 绑定到端口 {self.zmq_port}", level="INFO")
        except Exception as e:
            self._log(f"[ERROR] ZMQ 初始化失败: {e}", level="ERROR")

    def _log(self, msg: str, level: str = "INFO"):
        """
        输出日志到文件和控制台

        参数:
            msg (str): 日志信息
            level (str): 日志级别 (INFO, WARN, ERROR, SUCCESS)
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level:8s}] {msg}\n")

        # 打印到控制台
        colors = {
            "INFO": "\033[0m",
            "WARN": "\033[93m",
            "ERROR": "\033[91m",
            "SUCCESS": "\033[92m"
        }
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"
        print(f"[{timestamp}] {color}{msg}{reset}")

    async def connect(self):
        """
        连接到 EODHD WebSocket 端点

        流程：
          1. 构建 WSS URL (包含 API Token)
          2. 发起连接
          3. 发送订阅请求
          4. 启动消息接收循环
        """
        ws_url_with_token = f"{self.ws_url}?api_token={self.api_token}"

        try:
            self._log(f"[INFO] 正在连接: {self.ws_url}", level="INFO")

            async with websockets.connect(ws_url_with_token, ping_interval=30) as ws:
                self.ws = ws
                self.is_connected = True
                self.current_delay = self.base_delay  # 重置延迟
                self.reconnect_count = 0
                self._log("[SUCCESS] WebSocket 已连接", level="SUCCESS")

                # 订阅品种
                await self._subscribe()

                # 启动接收循环
                await self._receive_loop()

        except asyncio.CancelledError:
            self._log("[INFO] WebSocket 连接被主动取消", level="INFO")
            self.is_connected = False
            raise

        except Exception as e:
            self.is_connected = False
            self._log(f"[ERROR] WebSocket 连接出错: {type(e).__name__}: {str(e)[:200]}", level="ERROR")
            await self._handle_reconnect()

    async def _subscribe(self):
        """
        发送订阅请求

        协议：
          请求格式: {"action": "subscribe", "symbols": "EURUSD,GBPUSD"}
          响应格式: {"status": "subscribed", "symbols": [...]}
        """
        symbols_str = ",".join(self.symbols)
        subscribe_msg = {
            "action": "subscribe",
            "symbols": symbols_str
        }

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            self._log(f"[INFO] 已订阅品种: {symbols_str}", level="INFO")
        except Exception as e:
            self._log(f"[ERROR] 订阅失败: {e}", level="ERROR")
            raise

    async def _receive_loop(self):
        """
        接收实时行情数据循环

        协议：
          Tick 格式: {"s": "EURUSD", "p": 1.0543, "t": 1704153600, ...}
          s: 品种代码
          p: 最新价格
          t: 时间戳
          bid: 买价
          ask: 卖价
        """
        try:
            async for message in self.ws:
                data = json.loads(message)

                # 心跳检测
                if self._should_send_heartbeat():
                    await self._send_heartbeat()

                # 处理订阅确认或其他控制消息
                if data.get("status"):
                    self._log(f"[INFO] {data.get('status')}", level="INFO")
                    continue

                # 处理 Tick 数据
                if "s" in data:  # 包含品种代码
                    self.stats["ticks_received"] += 1
                    await self._process_tick(data)

        except asyncio.CancelledError:
            self._log("[INFO] 接收循环被取消", level="INFO")
            raise

        except Exception as e:
            self._log(f"[ERROR] 接收循环出错: {type(e).__name__}: {str(e)[:200]}", level="ERROR")
            raise

    async def _process_tick(self, tick_data: Dict[str, Any]):
        """
        处理单个 Tick 数据并转发到 ZMQ

        参数:
            tick_data (dict): EODHD Tick 数据
                {
                    "s": "EURUSD",
                    "p": 1.0543,        # 最新价
                    "bid": 1.05425,
                    "ask": 1.05435,
                    "t": 1704153600     # 时间戳
                }
        """
        try:
            symbol = tick_data.get("s")
            price = tick_data.get("p")
            timestamp = tick_data.get("t", int(time.time()))

            # 构建 JSON 格式的行情数据
            market_data = {
                "symbol": symbol,
                "price": price,
                "bid": tick_data.get("bid", price),
                "ask": tick_data.get("ask", price),
                "timestamp": timestamp,
                "source": "EODHD"
            }

            # 转发到 ZMQ PUB
            if self.zmq_pub:
                try:
                    message = json.dumps(market_data).encode("utf-8")
                    self.zmq_pub.send_multipart([
                        symbol.encode("utf-8"),
                        message
                    ])
                    self.stats["ticks_sent"] += 1
                except Exception as e:
                    self._log(f"[ERROR] ZMQ 发送失败: {e}", level="ERROR")

            # 控制台输出（每 10 个 Tick 输出一次）
            if self.stats["ticks_received"] % 10 == 0:
                self._log(
                    f"[INFO] {symbol}: {price:.5f} (Received: {self.stats['ticks_received']}, Sent: {self.stats['ticks_sent']})",
                    level="INFO"
                )

        except Exception as e:
            self._log(f"[ERROR] 处理 Tick 失败: {e}", level="ERROR")

    def _should_send_heartbeat(self) -> bool:
        """检查是否需要发送心跳"""
        return time.time() - self.last_heartbeat >= self.heartbeat_interval

    async def _send_heartbeat(self):
        """发送心跳消息保活连接"""
        try:
            if self.ws:
                heartbeat_msg = {"action": "heartbeat"}
                await self.ws.send(json.dumps(heartbeat_msg))
                self.last_heartbeat = time.time()
        except Exception as e:
            self._log(f"[WARN] 心跳发送失败: {e}", level="WARN")

    async def _handle_reconnect(self):
        """
        处理自动重连逻辑（指数退避）

        流程：
          1. 计算延迟时间（指数增长）
          2. 等待延迟时间
          3. 尝试重新连接
        """
        self.reconnect_count += 1
        self.stats["reconnects"] += 1

        # 计算下一次重连延迟（指数退避）
        delay = min(
            self.current_delay * (self.backoff_factor ** (self.reconnect_count - 1)),
            self.max_delay
        )

        self._log(
            f"[WARN] 将在 {delay:.1f} 秒后重连 (尝试 #{self.reconnect_count})",
            level="WARN"
        )

        await asyncio.sleep(delay)

        # 尝试重新连接
        await self.connect()

    async def run(self):
        """
        运行 WebSocket 客户端（主入口）

        无限循环处理连接/重连
        """
        self._log("[INFO] EODHD WebSocket 客户端已启动", level="INFO")
        try:
            await self.connect()
        except KeyboardInterrupt:
            self._log("[INFO] 用户中断，正在关闭...", level="INFO")
            self.close()
        except Exception as e:
            self._log(f"[ERROR] 致命错误: {e}", level="ERROR")
            self.close()

    def close(self):
        """关闭 WebSocket 连接和 ZMQ 上下文"""
        if self.ws:
            asyncio.create_task(self.ws.close())
            self.is_connected = False
            self._log("[INFO] WebSocket 已关闭", level="INFO")

        if self.zmq_pub:
            self.zmq_pub.close()
            self.zmq_context.term()
            self._log("[INFO] ZMQ PUB 已关闭", level="INFO")

        # 输出统计信息
        self._print_stats()

    def _print_stats(self):
        """输出运行统计信息"""
        elapsed = (datetime.datetime.now() - self.stats["start_time"]).total_seconds()
        tick_rate = self.stats["ticks_received"] / elapsed if elapsed > 0 else 0

        self._log(
            f"[STATS] Ticks: {self.stats['ticks_received']} | "
            f"Sent: {self.stats['ticks_sent']} | "
            f"Rate: {tick_rate:.1f} ticks/sec | "
            f"Reconnects: {self.stats['reconnects']}",
            level="INFO"
        )

    def subscribe(self, *symbols: str):
        """
        添加订阅品种

        参数:
            symbols: 品种代码（如 "EURUSD", "GBPUSD"）
        """
        for symbol in symbols:
            self.symbols.add(symbol)
        self._log(f"[INFO] 已添加订阅: {', '.join(symbols)}", level="INFO")

    def unsubscribe(self, *symbols: str):
        """
        移除订阅品种

        参数:
            symbols: 品种代码
        """
        for symbol in symbols:
            self.symbols.discard(symbol)
        self._log(f"[INFO] 已移除订阅: {', '.join(symbols)}", level="INFO")


async def main():
    """主函数 - 启动 EODHD WebSocket 客户端"""
    # 配置日志级别
    logging.basicConfig(level=logging.INFO)

    # 初始化客户端
    client = EodhdWsClient(
        symbols={"EURUSD", "GBPUSD", "USDJPY"}  # 初始订阅品种
    )

    # 启动客户端（无限循环）
    try:
        await client.run()
    except KeyboardInterrupt:
        client.close()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
