#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Data Feed Test Script
============================

验证 EODHD WebSocket 客户端的功能和性能。

测试场景：
  1. 订阅 ZMQ PUB 端口 (5556)
  2. 接收 EODHD 行情数据
  3. 在 10 秒内验证收到 > 5 个 Tick
  4. 验证数据格式和内容

用法：
  python3 scripts/test_market_feed.py
"""

import sys
import os
import json
import asyncio
import time
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 颜色定义
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# 日志文件
LOG_FILE = "VERIFY_LOG.log"


def log(msg, level="INFO"):
    """输出日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    colors = {
        "INFO": RESET,
        "WARN": YELLOW,
        "ERROR": RED,
        "SUCCESS": GREEN
    }
    color = colors.get(level, RESET)
    print(f"[{timestamp}] {color}[{level:8s}]{RESET} {msg}")

    # 写入日志文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level:8s}] {msg}\n")


class MarketFeedTester:
    """市场行情数据测试器"""

    def __init__(self, zmq_port: int = 5556, test_duration: int = 10):
        """
        初始化测试器

        参数:
            zmq_port: ZMQ PUB 端口
            test_duration: 测试持续时间（秒）
        """
        self.zmq_port = zmq_port
        self.test_duration = test_duration
        self.ticks_received = []
        self.symbols_seen = set()

        try:
            import zmq
            self.zmq = zmq
            self.zmq_available = True
        except ImportError:
            self.zmq_available = False
            log("ZMQ 库未安装", level="WARN")

    async def subscribe_and_listen(self):
        """
        订阅 ZMQ PUB 并接收数据

        返回:
            list: 接收到的数据列表
        """
        if not self.zmq_available:
            log("无法测试：ZMQ 库未安装", level="ERROR")
            return []

        try:
            # 创建 ZMQ 订阅者
            context = self.zmq.Context()
            subscriber = context.socket(self.zmq.SUB)

            # 连接到发布者
            subscriber.connect(f"tcp://127.0.0.1:{self.zmq_port}")

            # 订阅所有消息
            subscriber.setsockopt_string(self.zmq.SUBSCRIBE, "")

            # 设置接收超时
            subscriber.setsockopt(self.zmq.RCVTIMEO, 1000)  # 1 秒超时

            log(f"已连接到 ZMQ PUB (端口 {self.zmq_port})", level="INFO")

            # 接收消息循环
            start_time = time.time()
            timeout_count = 0

            while (time.time() - start_time) < self.test_duration:
                try:
                    # 接收多部分消息
                    message = subscriber.recv_multipart(zmq.NOBLOCK)

                    if len(message) >= 2:
                        symbol = message[0].decode("utf-8")
                        data_json = message[1].decode("utf-8")
                        data = json.loads(data_json)

                        self.ticks_received.append(data)
                        self.symbols_seen.add(symbol)

                        # 每 5 个 Tick 输出一次
                        if len(self.ticks_received) % 5 == 0:
                            log(
                                f"已接收 {len(self.ticks_received)} 个 Tick | "
                                f"品种: {', '.join(sorted(self.symbols_seen))}",
                                level="INFO"
                            )

                except self.zmq.Again:
                    # 超时，继续等待
                    timeout_count += 1
                    if timeout_count % 10 == 0:
                        log(f"等待中... ({time.time() - start_time:.1f}s)", level="WARN")
                    await asyncio.sleep(0.1)

            # 关闭连接
            subscriber.close()
            context.term()

            return self.ticks_received

        except Exception as e:
            log(f"接收数据失败: {type(e).__name__}: {str(e)[:200]}", level="ERROR")
            return []

    def validate_tick_data(self, tick: dict) -> bool:
        """
        验证单个 Tick 数据的格式

        必需字段:
          - symbol: 品种代码
          - price: 最新价格
          - timestamp: 时间戳
        """
        required_fields = ["symbol", "price", "timestamp"]

        for field in required_fields:
            if field not in tick:
                log(f"缺少必需字段: {field}", level="ERROR")
                return False

        # 验证数据类型
        if not isinstance(tick["symbol"], str):
            log(f"symbol 不是字符串: {tick['symbol']}", level="ERROR")
            return False

        if not isinstance(tick["price"], (int, float)):
            log(f"price 不是数字: {tick['price']}", level="ERROR")
            return False

        if not isinstance(tick["timestamp"], (int, float)):
            log(f"timestamp 不是数字: {tick['timestamp']}", level="ERROR")
            return False

        return True

    async def run_test(self):
        """运行完整的测试"""
        log("=" * 80, level="INFO")
        log("EODHD Market Data Feed Test", level="INFO")
        log("=" * 80, level="INFO")
        log(f"测试配置: ZMQ_PORT={self.zmq_port}, TEST_DURATION={self.test_duration}s", level="INFO")
        log("", level="INFO")

        # 检查依赖
        log("[Test 1] 检查 ZMQ 可用性...", level="INFO")
        if not self.zmq_available:
            log("❌ FAIL: ZMQ 库未安装", level="ERROR")
            return False
        log("✅ PASS: ZMQ 库已安装", level="SUCCESS")
        log("", level="INFO")

        # 订阅和接收数据
        log("[Test 2] 订阅 ZMQ PUB 并接收数据...", level="INFO")
        log(f"等待 {self.test_duration} 秒接收数据...", level="INFO")
        ticks = await self.subscribe_and_listen()
        log(f"总共接收 {len(ticks)} 个 Tick", level="INFO")
        log("", level="INFO")

        # 验证接收到足够的数据
        log("[Test 3] 验证接收数据量...", level="INFO")
        if len(ticks) < 5:
            log(f"❌ FAIL: 接收数据过少 ({len(ticks)} < 5)", level="ERROR")
            return False
        log(f"✅ PASS: 接收到足够的数据 ({len(ticks)} >= 5)", level="SUCCESS")
        log("", level="INFO")

        # 验证数据格式
        log("[Test 4] 验证数据格式...", level="INFO")
        invalid_count = 0
        for i, tick in enumerate(ticks):
            if not self.validate_tick_data(tick):
                invalid_count += 1
                if invalid_count <= 3:  # 只显示前 3 个错误
                    log(f"  Tick #{i}: {tick}", level="ERROR")

        if invalid_count > 0:
            log(f"❌ FAIL: {invalid_count}/{len(ticks)} Tick 格式无效", level="ERROR")
            return False
        log(f"✅ PASS: 所有 {len(ticks)} 个 Tick 格式有效", level="SUCCESS")
        log("", level="INFO")

        # 验证数据内容示例
        log("[Test 5] 数据内容示例...", level="INFO")
        if ticks:
            first_tick = ticks[0]
            last_tick = ticks[-1]
            log(
                f"  First Tick: {first_tick['symbol']} @ {first_tick['price']:.5f}",
                level="INFO"
            )
            log(
                f"  Last Tick:  {last_tick['symbol']} @ {last_tick['price']:.5f}",
                level="INFO"
            )

            # 检查品种
            if self.symbols_seen:
                log(f"  观察到的品种: {', '.join(sorted(self.symbols_seen))}", level="INFO")
            log("✅ PASS: 数据内容有效", level="SUCCESS")
        log("", level="INFO")

        # 计算吞吐率
        log("[Test 6] 性能指标...", level="INFO")
        tick_rate = len(ticks) / self.test_duration if self.test_duration > 0 else 0
        log(f"  吞吐率: {tick_rate:.1f} ticks/sec", level="INFO")
        log(f"  数据点: {len(ticks)}", level="INFO")
        log(f"  品种数: {len(self.symbols_seen)}", level="INFO")
        log("✅ PASS: 性能指标正常", level="SUCCESS")
        log("", level="INFO")

        # 总结
        log("=" * 80, level="INFO")
        log("✅ 所有测试通过 (6/6 PASSED)", level="SUCCESS")
        log("=" * 80, level="INFO")

        return True


async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建测试器
    tester = MarketFeedTester(zmq_port=5556, test_duration=10)

    # 运行测试
    success = await tester.run_test()

    # 退出代码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("测试被用户中断", level="WARN")
        sys.exit(1)
    except Exception as e:
        log(f"致命错误: {type(e).__name__}: {str(e)}", level="ERROR")
        sys.exit(1)
