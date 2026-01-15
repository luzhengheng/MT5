#!/usr/bin/env python3
"""
Protocol Reconnaissance Script - ZMQ Market Data Listener
=========================================================

此脚本监听 Windows Gateway (GTW) 的 ZMQ PUB 端口 (5556)，
捕获并解析原始数据格式，确认数据指纹（JSON key 结构、时间戳格式等）。

用途：
  1. 确认 GTW 发送的数据格式是 JSON 还是二进制
  2. 验证 JSON key 的大小写（bid vs Bid）
  3. 确认时间戳格式（Unix Timestamp vs ISO String）
  4. 测试连接性和数据流

Usage:
  python3 scripts/tools/listen_zmq_pub.py --host 172.19.141.255 --port 5556 --timeout 30

Protocol v4.3 要求：
  - 物理证据：必须展示真实接收到的数据行
  - 没有幻觉：不能模拟数据，必须真实握手
"""

import zmq
import json
import time
import logging
import argparse
from typing import Optional, Dict, Any
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ZMQPublisherListener:
    """ZMQ 发布者监听器"""

    def __init__(self, host: str, port: int, timeout_sec: int = 30):
        """
        初始化监听器

        Args:
            host: 目标 GTW 的内网 IP（如 172.19.141.255）
            port: 目标端口（5556）
            timeout_sec: 监听超时时间（秒）
        """
        self.host = host
        self.port = port
        self.timeout_sec = timeout_sec
        self.context = None
        self.socket = None
        self.tick_count = 0

    def connect(self) -> bool:
        """
        连接到 ZMQ PUB 端口

        Returns:
            True 如果连接成功，False 否则
        """
        try:
            logger.info(f"[RECONNAISSANCE] 正在连接到 {self.host}:{self.port}...")

            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)

            # 订阅所有消息（空字符串订阅过滤器）
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

            # 设置接收超时
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 秒超时

            # 连接
            conn_addr = f"tcp://{self.host}:{self.port}"
            self.socket.connect(conn_addr)

            # 等待连接建立（ZMQ 需要时间）
            time.sleep(1)

            logger.info(f"[RECONNAISSANCE] ✅ 成功连接到 {conn_addr}")
            return True

        except Exception as e:
            logger.error(f"[RECONNAISSANCE] ❌ 连接失败: {e}")
            return False

    def listen(self) -> Optional[Dict[str, Any]]:
        """
        监听一条消息

        Returns:
            解析后的 tick 数据字典，或 None 如果超时/失败
        """
        if not self.socket:
            logger.error("[RECONNAISSANCE] Socket 未初始化")
            return None

        try:
            # 接收原始数据
            raw_data = self.socket.recv()

            # 尝试解析为 JSON
            try:
                tick_data = json.loads(raw_data.decode('utf-8'))
                self.tick_count += 1
                return tick_data

            except json.JSONDecodeError as e:
                logger.warning(f"[RECONNAISSANCE] 无法解析为 JSON: {e}")
                logger.warning(f"[RECONNAISSANCE] 原始数据 (前 100 字节): {raw_data[:100]}")
                return None

        except zmq.Again:
            # 超时 - 没有数据
            return None

        except Exception as e:
            logger.error(f"[RECONNAISSANCE] 接收错误: {e}")
            return None

    def run(self) -> bool:
        """
        运行监听循环，捕获多条 tick 数据并分析格式

        Returns:
            True 如果成功捕获至少一条消息
        """
        if not self.connect():
            return False

        logger.info(f"[RECONNAISSANCE] 开始监听，超时时间 {self.timeout_sec} 秒...")

        start_time = time.time()
        sample_ticks = []

        while time.time() - start_time < self.timeout_sec:
            tick = self.listen()

            if tick:
                sample_ticks.append(tick)
                logger.info(f"[LIVE_TICK] 收到第 {self.tick_count} 条数据: {json.dumps(tick, indent=2)}")

                # 显示数据结构分析
                self._analyze_tick_structure(tick)

                # 收集足够样本后停止
                if len(sample_ticks) >= 3:
                    logger.info("[RECONNAISSANCE] 已收集 3 条样本数据，停止监听")
                    break
            else:
                # 未收到数据，继续等待
                elapsed = time.time() - start_time
                remaining = self.timeout_sec - elapsed
                logger.info(f"[RECONNAISSANCE] 等待中... ({remaining:.1f}s 剩余)")
                time.sleep(0.5)

        # 关闭连接
        self.close()

        # 返回成功状态
        success = len(sample_ticks) > 0
        if success:
            logger.info(f"[RECONNAISSANCE] ✅ 成功捕获 {len(sample_ticks)} 条数据")
        else:
            logger.warning(f"[RECONNAISSANCE] ⚠️  监听超时，未收到任何数据（检查网络/GTW 状态）")

        return success

    def _analyze_tick_structure(self, tick: Dict[str, Any]):
        """
        分析 tick 数据的结构，确认数据指纹

        Args:
            tick: Tick 数据字典
        """
        logger.info("[RECONNAISSANCE] 数据结构分析:")

        # Key 检查
        keys = list(tick.keys())
        logger.info(f"  - Keys: {keys}")

        # 字段检查
        if 'symbol' in tick:
            logger.info(f"  - 符号: {tick['symbol']}")

        if 'bid' in tick:
            logger.info(f"  - Bid 价格: {tick['bid']} (key: 'bid')")
        elif 'Bid' in tick:
            logger.info(f"  - Bid 价格: {tick['Bid']} (key: 'Bid')")

        if 'ask' in tick:
            logger.info(f"  - Ask 价格: {tick['ask']} (key: 'ask')")
        elif 'Ask' in tick:
            logger.info(f"  - Ask 价格: {tick['Ask']} (key: 'Ask')")

        # 时间戳检查
        timestamp_keys = [k for k in tick.keys() if 'time' in k.lower()]
        for ts_key in timestamp_keys:
            ts_value = tick[ts_key]
            logger.info(f"  - 时间戳字段: '{ts_key}' = {ts_value} (类型: {type(ts_value).__name__})")

            # 如果是 Unix 时间戳
            if isinstance(ts_value, (int, float)):
                dt = datetime.fromtimestamp(ts_value)
                logger.info(f"    └─ 转换为: {dt.isoformat()}")
            # 如果是字符串
            elif isinstance(ts_value, str):
                logger.info(f"    └─ 字符串格式（无需转换）")

    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("[RECONNAISSANCE] 连接已关闭")


def main():
    """主程序"""
    parser = argparse.ArgumentParser(
        description="ZMQ 市场数据监听器 - 协议侦察"
    )
    parser.add_argument(
        '--host',
        default='172.19.141.255',
        help='目标 GTW 的内网 IP (默认: 172.19.141.255)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5556,
        help='目标端口 (默认: 5556)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='监听超时时间（秒，默认: 30）'
    )

    args = parser.parse_args()

    listener = ZMQPublisherListener(
        host=args.host,
        port=args.port,
        timeout_sec=args.timeout
    )

    success = listener.run()
    exit(0 if success else 1)


if __name__ == '__main__':
    main()
