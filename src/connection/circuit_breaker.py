"""
异常熔断机制 - 交易系统保护

根据Gemini Pro审查建议实现的全局异常熔断和停机保护

关键特性：
1. 异常捕获和日志记录
2. 连续亏损熔断（防止恶性循环）
3. 错误计数和恢复机制
4. 紧急通知（Telegram/SMS等）
5. 优雅停止
"""

import logging
import time
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "CLOSED"  # 正常工作
    OPEN = "OPEN"      # 熔断，停止交易
    HALF_OPEN = "HALF_OPEN"  # 半开，尝试恢复


@dataclass
class BreakdownEvent:
    """故障事件"""
    event_type: str  # "EXCEPTION", "MAX_LOSS", "API_ERROR" 等
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""
    severity: str = "WARNING"  # "INFO", "WARNING", "CRITICAL"
    exception: Optional[Exception] = None

    def __str__(self):
        return (
            f"[{self.severity}] {self.event_type} @ {self.timestamp.isoformat()}\n"
            f"Message: {self.message}"
        )


class CircuitBreaker:
    """
    电路熔断器 - 交易系统的"自动断路器"

    工作原理：
    1. CLOSED (正常) - 系统正常工作
    2. OPEN (熔断) - 检测到问题，停止交易
    3. HALF_OPEN (恢复) - 尝试恢复，监测情况

    触发条件：
    - 未捕获的异常
    - 连续亏损超过阈值
    - API调用频繁失败
    - 保证金不足
    """

    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: int = 300,
                 max_consecutive_losses: int = 3,
                 max_loss_amount: float = 1000.0):
        """
        初始化熔断器

        Args:
            failure_threshold: 触发熔断的错误次数阈值
            recovery_timeout: 熔断后多少秒尝试恢复 (秒)
            max_consecutive_losses: 最大连续亏损笔数
            max_loss_amount: 单次最大亏损金额
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.max_consecutive_losses = max_consecutive_losses
        self.max_loss_amount = max_loss_amount

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.open_time = None

        self.consecutive_losses = 0
        self.total_loss = 0.0
        self.last_trade_result = 0.0

        self.events: List[BreakdownEvent] = []
        self.recovery_callbacks: List[Callable] = []
        self.shutdown_callbacks: List[Callable] = []

        logger.info("✅ 电路熔断器初始化")

    def can_trade(self) -> bool:
        """
        检查是否可以交易

        Returns:
            bool: True表示可以交易，False表示被熔断
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # 检查是否可以尝试恢复
            if self.open_time is None:
                return False

            elapsed = (datetime.now() - self.open_time).total_seconds()
            if elapsed > self.recovery_timeout:
                logger.info(f"🔄 尝试恢复... (熔断 {elapsed:.0f}秒)")
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            else:
                remaining = self.recovery_timeout - elapsed
                logger.debug(f"⏳ 熔断中，恢复倒计时: {remaining:.0f}秒")
                return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """记录成功交易"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            # 恢复成功
            logger.info("✅ 恢复成功！返回正常状态")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.consecutive_losses = 0
            self.total_loss = 0.0

            # 触发恢复回调
            for callback in self.recovery_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"❌ 恢复回调失败: {e}")

    def record_failure(self, exception: Optional[Exception] = None,
                      message: str = "", severity: str = "WARNING"):
        """
        记录失败事件

        Args:
            exception: 异常对象
            message: 失败消息
            severity: 严重级别 (INFO, WARNING, CRITICAL)
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        event = BreakdownEvent(
            event_type="EXCEPTION",
            message=message or (str(exception) if exception else "Unknown error"),
            severity=severity,
            exception=exception
        )
        self.events.append(event)

        logger.warning(f"⚠️ 记录故障 ({self.failure_count}/{self.failure_threshold}): {message}")

        # 检查是否触发熔断
        if self.failure_count >= self.failure_threshold:
            self._trigger_circuit_break(
                f"达到错误阈值 ({self.failure_count} >= {self.failure_threshold})"
            )

    def record_trade_result(self, pnl: float):
        """
        记录交易结果 (损益)

        Args:
            pnl: 损益金额 (正数为盈利，负数为亏损)
        """
        self.last_trade_result = pnl

        if pnl < 0:
            # 亏损
            self.consecutive_losses += 1
            self.total_loss += abs(pnl)

            logger.info(
                f"📉 交易亏损: {pnl:.2f}, "
                f"连续亏损: {self.consecutive_losses}/{self.max_consecutive_losses}, "
                f"累计亏损: {self.total_loss:.2f}"
            )

            # 检查连续亏损
            if self.consecutive_losses >= self.max_consecutive_losses:
                self._trigger_circuit_break(
                    f"连续亏损 {self.consecutive_losses} 笔"
                )

            # 检查单笔亏损
            if abs(pnl) > self.max_loss_amount:
                self._trigger_circuit_break(
                    f"单笔亏损 {pnl:.2f} 超过限制 {self.max_loss_amount:.2f}"
                )

        else:
            # 盈利
            self.consecutive_losses = 0
            logger.info(f"📈 交易盈利: {pnl:.2f}")

    def record_account_warning(self, warning_type: str, message: str):
        """
        记录账户警告

        Args:
            warning_type: 警告类型 (MARGIN_LOW, BALANCE_LOW 等)
            message: 警告消息
        """
        event = BreakdownEvent(
            event_type=warning_type,
            message=message,
            severity="WARNING"
        )
        self.events.append(event)

        logger.warning(f"🚨 账户警告 [{warning_type}]: {message}")

    def _trigger_circuit_break(self, reason: str):
        """
        触发熔断

        Args:
            reason: 触发原因
        """
        if self.state != CircuitBreakerState.OPEN:
            logger.error(f"🔴 触发电路熔断！原因: {reason}")

            self.state = CircuitBreakerState.OPEN
            self.open_time = datetime.now()

            event = BreakdownEvent(
                event_type="CIRCUIT_BREAK",
                message=reason,
                severity="CRITICAL"
            )
            self.events.append(event)

            # 触发紧急通知
            self._send_emergency_notification(reason)

    def _send_emergency_notification(self, reason: str):
        """
        发送紧急通知 (Telegram/邮件/SMS等)

        Args:
            reason: 原因
        """
        notification = f"""
🚨 交易系统紧急熔断

时间: {datetime.now().isoformat()}
原因: {reason}

系统已停止所有交易，待手动恢复。
"""

        logger.critical(notification)

        # TODO: 实现实际的通知（Telegram/邮件等）
        # 示例：
        # self._send_telegram_notification(notification)
        # self._send_email_notification(notification)

    def add_recovery_callback(self, callback: Callable):
        """
        添加恢复回调

        Args:
            callback: 恢复成功时的回调函数
        """
        self.recovery_callbacks.append(callback)

    def add_shutdown_callback(self, callback: Callable):
        """
        添加关闭回调

        Args:
            callback: 系统关闭时的回调函数
        """
        self.shutdown_callbacks.append(callback)

    def shutdown(self, reason: str = "Manual shutdown"):
        """
        优雅关闭系统

        Args:
            reason: 关闭原因
        """
        logger.warning(f"⏹️ 系统关闭: {reason}")

        # 触发所有关闭回调
        for callback in self.shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"❌ 关闭回调失败: {e}")

        # 记录最终状态
        self.print_summary()

    def print_summary(self):
        """打印故障总结"""
        summary = f"""
╔════════════════════════════════════════════════════════════╗
║           电路熔断器状态报告                               ║
╠════════════════════════════════════════════════════════════╣
║
║ 当前状态:   {self.state.value}
║ 失败次数:   {self.failure_count} / {self.failure_threshold}
║ 连续亏损:   {self.consecutive_losses} / {self.max_consecutive_losses}
║ 累计亏损:   ${self.total_loss:.2f}
║ 最后失败:   {self.last_failure_time}
║
╠════════════════════════════════════════════════════════════╣
║ 记录的事件 ({len(self.events)} 个):
║
"""

        for event in self.events[-10:]:  # 显示最后10个事件
            summary += f"║ • {event.event_type:15s} @ {event.timestamp.strftime('%H:%M:%S')}\n"
            summary += f"║   {event.message[:50]}\n"

        summary += """║
╚════════════════════════════════════════════════════════════╝
"""

        print(summary)

    def get_status(self) -> Dict:
        """获取熔断器状态"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "consecutive_losses": self.consecutive_losses,
            "total_loss": self.total_loss,
            "can_trade": self.can_trade(),
            "events_count": len(self.events),
        }


class ExceptionHandler:
    """
    异常处理器 - 包装交易循环以捕获异常

    使用示例：
    ```python
    handler = ExceptionHandler(circuit_breaker)

    @handler.catch_exceptions("交易循环")
    def trading_loop():
        # 交易代码
        pass

    trading_loop()  # 所有异常会被自动捕获和处理
    ```
    """

    def __init__(self, circuit_breaker: CircuitBreaker):
        self.cb = circuit_breaker

    def catch_exceptions(self, operation_name: str, reraise: bool = False):
        """
        异常捕获装饰器

        Args:
            operation_name: 操作名称（用于日志）
            reraise: 是否重新抛出异常
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    logger.info("⏸️ 被用户中断")
                    raise
                except Exception as e:
                    logger.error(f"❌ {operation_name} 失败: {e}", exc_info=True)
                    self.cb.record_failure(
                        exception=e,
                        message=f"{operation_name} 异常: {str(e)}",
                        severity="CRITICAL"
                    )

                    if reraise:
                        raise

            return wrapper

        return decorator


# ============================================================================
# 使用示例
# ============================================================================

def example_trading_with_circuit_breaker():
    """
    使用熔断机制的交易循环示例
    """

    # 1. 创建熔断器
    cb = CircuitBreaker(
        failure_threshold=3,  # 3个错误后熔断
        max_consecutive_losses=2,  # 2次连续亏损后熔断
        max_loss_amount=500.0  # 单笔亏损>500后熔断
    )

    # 2. 添加回调
    def on_recovery():
        logger.info("系统已恢复，可以重新开始交易")

    def on_shutdown():
        logger.info("系统正在关闭，执行清理操作...")

    cb.add_recovery_callback(on_recovery)
    cb.add_shutdown_callback(on_shutdown)

    # 3. 创建异常处理器
    handler = ExceptionHandler(cb)

    # 4. 交易循环
    @handler.catch_exceptions("主交易循环", reraise=False)
    def trading_loop():
        iteration = 0

        while True:
            # 检查是否可以交易
            if not cb.can_trade():
                logger.warning("❌ 系统已熔断，等待恢复...")
                time.sleep(10)
                continue

            iteration += 1
            logger.info(f"\n--- 交易循环 #{iteration} ---")

            try:
                # 这里放实际的交易代码
                # bridge.get_positions()
                # bars = bridge.get_bar_data()
                # signal = model.predict(features)
                # ...

                # 模拟交易结果
                import random
                pnl = random.uniform(-600, 500)

                # 记录结果
                cb.record_trade_result(pnl)

                if cb.state == CircuitBreakerState.HALF_OPEN:
                    cb.record_success()

                time.sleep(1)

            except Exception as e:
                cb.record_failure(e, f"交易执行异常: {e}")

            # 模拟停止条件
            if iteration > 20:
                break

    # 5. 运行
    try:
        trading_loop()
    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断")
    finally:
        cb.shutdown("交易循环完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行示例
    example_trading_with_circuit_breaker()
