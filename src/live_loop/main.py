#!/usr/bin/env python3
"""
Live Loop Main - Strategy Engine Market Data Integration
========================================================

此模块实现了 Linux Inf 节点的主循环逻辑，集成了市场数据接入和策略驱动。

核心流程：
1. 启动市场数据接收器（监听 ZMQ PUB 端口 5556）
2. 启动策略引擎
3. 在主循环中：
   a. 从市场数据接收器轮询最新 Tick
   b. 如果有新 Tick，驱动 strategy.on_tick()
   c. 执行心跳任务（如定时报告、风险监控）
4. 优雅关闭

设计目标：
- 替代原有的空转心跳（sleep(1)）
- 使用真实市场数据驱动策略逻辑
- 保持系统韧性（网络故障不导致崩溃）
- 支持优雅关闭（Ctrl+C）

Protocol v4.3：
- 所有关键事件都通过日志记录（物理证据）
- 零信任：验证所有接收到的数据
- 自主闭环：错误自动恢复
"""

import logging
import time
import signal
import sys
from typing import Optional

from src.live_loop.ingestion import (
    get_market_data_receiver,
    MarketDataReceiver
)
from src.strategy.engine import StrategyEngine
from src.execution.live_engine import LiveEngine  # 心跳引擎
from src.risk.circuit_breaker import CircuitBreaker  # 熔断机制

logger = logging.getLogger(__name__)

# ============================================================================
# 常量定义
# ============================================================================

# 主循环参数
LOOP_INTERVAL_MS = 10  # 主循环检测间隔（毫秒）
HEARTBEAT_INTERVAL_S = 5  # 心跳任务间隔（秒）

# 关闭超时
SHUTDOWN_TIMEOUT_S = 5  # 优雅关闭超时（秒）


# ============================================================================
# Live Loop Main 类
# ============================================================================

class LiveLoopMain:
    """
    Live Loop 主程序

    管理整个实盘交易循环：
    1. 市场数据接收
    2. 策略信号生成
    3. 订单执行
    4. 风险监控

    Attributes:
        market_receiver: 市场数据接收器
        strategy_engine: 策略引擎
        live_engine: 心跳/执行引擎
        circuit_breaker: 熔断机制
        running: 运行标志
    """

    def __init__(self):
        """初始化 Live Loop"""
        self.market_receiver: Optional[MarketDataReceiver] = None
        self.strategy_engine: Optional[StrategyEngine] = None
        self.live_engine: Optional[LiveEngine] = None
        self.circuit_breaker: Optional[CircuitBreaker] = None

        self.running = False
        self.tick_processed = 0
        self.last_heartbeat_time = time.time()

        logger.info("[LiveLoop] Main 初始化完成")

    # ========================================================================
    # 启动和关闭
    # ========================================================================

    def start(self) -> bool:
        """
        启动 Live Loop

        初始化所有组件：
        1. 市场数据接收器
        2. 策略引擎
        3. 心跳引擎
        4. 熔断机制

        Returns:
            True 如果启动成功
        """
        try:
            logger.info("[LiveLoop] 正在启动 Live Loop...")

            # 1. 初始化市场数据接收器
            logger.info("[LiveLoop] 正在启动市场数据接收器...")
            self.market_receiver = get_market_data_receiver()
            if not self.market_receiver.start():
                logger.error("[LiveLoop] ❌ 市场数据接收器启动失败")
                return False
            logger.info("[LiveLoop] ✅ 市场数据接收器已启动")

            # 2. 初始化策略引擎
            logger.info("[LiveLoop] 正在初始化策略引擎...")
            self.strategy_engine = StrategyEngine()
            logger.info("[LiveLoop] ✅ 策略引擎已初始化")

            # 4. 初始化熔断机制
            try:
                logger.info("[LiveLoop] 正在初始化熔断机制...")
                self.circuit_breaker = CircuitBreaker()
                logger.info("[LiveLoop] ✅ 熔断机制已初始化")
            except Exception as e:
                logger.warning(
                    f"[LiveLoop] 熔断机制初始化失败（非关键）: {e}"
                )
                self.circuit_breaker = None

            # 3. 初始化心跳引擎（如果需要）
            try:
                logger.info("[LiveLoop] 正在初始化心跳引擎...")
                if self.circuit_breaker:
                    self.live_engine = LiveEngine(self.circuit_breaker)
                else:
                    logger.warning(
                        "[LiveLoop] 跳过心跳引擎: 熔断机制初始化失败"
                    )
                    self.live_engine = None
                if self.live_engine:
                    logger.info("[LiveLoop] ✅ 心跳引擎已启动")
            except Exception as e:
                logger.warning(
                    f"[LiveLoop] 心跳引擎初始化失败（非关键）: {e}"
                )
                self.live_engine = None

            # 设置运行标志
            self.running = True

            # 注册 Ctrl+C 处理器
            signal.signal(signal.SIGINT, self._handle_shutdown)

            logger.info("[LiveLoop] ✅ Live Loop 已启动")
            return True

        except Exception as e:
            logger.error(f"[LiveLoop] ❌ 启动失败: {e}")
            self.stop()
            return False

    def stop(self):
        """
        停止 Live Loop

        优雅关闭所有组件：
        1. 停止接收新数据
        2. 关闭策略引擎
        3. 停止心跳引擎
        """
        logger.info("[LiveLoop] 正在停止 Live Loop...")
        self.running = False

        # 停止市场数据接收器
        if self.market_receiver:
            self.market_receiver.stop()

        # 停止心跳引擎
        if self.live_engine:
            try:
                self.live_engine.stop()
            except Exception as e:
                logger.warning(f"[LiveLoop] 心跳引擎停止失败: {e}")

        logger.info("[LiveLoop] ✅ Live Loop 已停止")

    def _handle_shutdown(self, signum, frame):
        """Ctrl+C 信号处理器"""
        logger.info("[LiveLoop] 收到关闭信号，准备优雅关闭...")
        self.stop()
        sys.exit(0)

    # ========================================================================
    # 主循环
    # ========================================================================

    def run(self):
        """
        运行 Live Loop 主循环

        核心逻辑：
        1. 轮询市场数据接收器
        2. 如果有新 Tick，驱动策略引擎
        3. 定时执行心跳任务
        4. 捕获异常，确保系统韧性

        伪代码：
        while running:
            tick = receiver.get_latest_tick()
            if tick:
                strategy.on_tick(tick)
            if time_to_heartbeat():
                heartbeat.tick()
            sleep(LOOP_INTERVAL_MS)
        """
        if not self.start():
            logger.error("[LiveLoop] 启动失败，退出")
            return

        logger.info("[LiveLoop] 进入主循环...")
        self.tick_processed = 0

        try:
            while self.running:
                try:
                    # ============================================================
                    # 步骤 1: 轮询市场数据
                    # ============================================================
                    tick = self.market_receiver.get_latest_tick(timeout_ms=100)

                    if tick:
                        # 检查熔断状态
                        cb = self.circuit_breaker
                        if cb and cb.is_tripped():
                            logger.warning(
                                "[LiveLoop] ⚠️  熔断机制已触发，跳过此 Tick"
                            )
                        else:
                            # 驱动策略引擎
                            try:
                                sym = tick.get('symbol')
                                bid = tick.get('bid')
                                ask = tick.get('ask')
                                logger.debug(
                                    f"[LiveLoop] 驱动策略: {sym} "
                                    f"bid={bid} ask={ask}"
                                )
                                self.strategy_engine.on_tick(tick)
                                self.tick_processed += 1

                                # 物理证据记录
                                logger.info(
                                    f"[LIVE_TICK] {sym}: {bid} "
                                    f"-> Strategy Triggered"
                                )

                            except Exception as e:
                                logger.error(
                                    f"[LiveLoop] 策略引擎处理失败: {e}"
                                )

                    # ============================================================
                    # 步骤 2: 定时心跳任务
                    # ============================================================
                    now = time.time()
                    hb_interval = HEARTBEAT_INTERVAL_S
                    if now - self.last_heartbeat_time >= hb_interval:
                        self._execute_heartbeat()
                        self.last_heartbeat_time = now

                    # ============================================================
                    # 步骤 3: 循环休眠
                    # ============================================================
                    time.sleep(LOOP_INTERVAL_MS / 1000.0)  # 转换为秒

                except Exception as e:
                    logger.error(f"[LiveLoop] 循环异常: {e}")
                    time.sleep(1)  # 发生异常时等待后重试

        except KeyboardInterrupt:
            logger.info("[LiveLoop] 收到键盘中断信号")
        finally:
            self.stop()

    def _execute_heartbeat(self):
        """
        执行心跳任务

        包括：
        1. 报告接收器状态
        2. 报告策略状态
        3. 检查熔断状态
        """
        try:
            # 报告市场数据接收器状态
            if self.market_receiver:
                status = self.market_receiver.get_status()
                tick_count = status.get('tick_count')
                buffer_size = status.get('buffer_size')
                time_since = status.get('time_since_last_tick')
                logger.info(
                    f"[Heartbeat] 接收器: "
                    f"ticks={tick_count}, "
                    f"buffer={buffer_size}, "
                    f"time_since_last={time_since:.1f}s"
                )

                # 检查数据饥饿
                if status.get('data_starved'):
                    logger.warning(
                        f"[Heartbeat] ⚠️  数据饥饿: "
                        f"{status.get('time_since_last_tick'):.1f}s 无数据"
                    )

            # 报告熔断状态
            if self.circuit_breaker:
                if self.circuit_breaker.is_tripped():
                    logger.warning("[Heartbeat] ⚠️  熔断机制已触发")
                else:
                    logger.info(
                        f"[Heartbeat] 熔断状态: SAFE "
                        f"(fail_count={self.circuit_breaker.fail_count})"
                    )

            # 报告整体统计
            logger.info(
                f"[Heartbeat] 统计: "
                f"ticks_processed={self.tick_processed}, "
                f"uptime={time.time() - self.last_heartbeat_time:.1f}s"
            )

        except Exception as e:
            logger.error(f"[LiveLoop] 心跳任务异常: {e}")


# ============================================================================
# 入口函数
# ============================================================================

def main():
    """
    主程序入口

    配置日志并启动 Live Loop
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('VERIFY_LOG.log', mode='a')
        ]
    )

    logger.info("=" * 80)
    logger.info("[LiveLoop] ========== Live Loop 启动 ==========")
    logger.info("=" * 80)

    # 创建和运行 Live Loop
    live_loop = LiveLoopMain()
    live_loop.run()


if __name__ == '__main__':
    main()
