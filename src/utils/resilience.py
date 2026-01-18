#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resilience Module - Wait-or-Die 韧性装饰器

实现无限重试逻辑，确保关键操作在网络波动或短期故障下继续等待，
而不是立即失败。这是 Protocol v4.4 的核心机制。

用法:
  @wait_or_die(timeout=None, exponential_backoff=True)
  def critical_api_call():
      # 这个函数会自动在故障时无限重试
      pass
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


class WaitOrDieException(Exception):
    """Wait-or-Die 机制的异常类"""
    pass


def wait_or_die(
    timeout: Optional[float] = None,
    exponential_backoff: bool = True,
    max_retries: int = 50,
    initial_wait: float = 1.0,
    max_wait: float = 60.0
) -> Callable:
    """
    Wait-or-Die 装饰器 - Protocol v4.4 核心机制

    当被装饰的函数抛出异常时，自动进入无限等待模式，
    而不是立即失败。这样可以应对网络波动、API速率限制等暂时故障。

    Args:
        timeout: 总超时时间（秒），None 表示无限等待
        exponential_backoff: 是否使用指数退避算法
        max_retries: 最多重试次数（无穷时忽略）
        initial_wait: 初始等待时间（秒）
        max_wait: 最大等待时间（秒）

    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.utcnow()
            retry_count = 0
            current_wait = initial_wait

            while True:
                try:
                    # 尝试执行函数
                    result = func(*args, **kwargs)

                    # 成功时记录日志并返回
                    if retry_count > 0:
                        logger.info(
                            f"{GREEN}[WAIT-OR-DIE] ✅ 成功！{RESET} "
                            f"函数: {func.__name__} "
                            f"重试次数: {retry_count} "
                            f"总耗时: {(datetime.utcnow() - start_time).total_seconds():.2f}秒"
                        )
                    return result

                except Exception as e:
                    retry_count += 1
                    elapsed = (datetime.utcnow() - start_time).total_seconds()

                    # 检查是否超时
                    if timeout is not None and elapsed > timeout:
                        logger.error(
                            f"{RED}[WAIT-OR-DIE] ❌ 超时！{RESET} "
                            f"函数: {func.__name__} "
                            f"总耗时: {elapsed:.2f}秒 > {timeout}秒 "
                            f"异常: {str(e)}"
                        )
                        raise WaitOrDieException(
                            f"Timeout after {elapsed:.2f}s: {str(e)}"
                        ) from e

                    # 检查是否超过最大重试次数
                    if max_retries is not None and retry_count > max_retries:
                        logger.error(
                            f"{RED}[WAIT-OR-DIE] ❌ 达到最大重试次数！{RESET} "
                            f"函数: {func.__name__} "
                            f"重试次数: {retry_count} > {max_retries}"
                        )
                        raise WaitOrDieException(
                            f"Max retries exceeded ({retry_count}): {str(e)}"
                        ) from e

                    # 计算下一次等待时间
                    if exponential_backoff:
                        current_wait = min(
                            initial_wait * (2 ** (retry_count - 1)),
                            max_wait
                        )
                    else:
                        current_wait = initial_wait

                    # 记录重试信息
                    logger.warning(
                        f"{YELLOW}[WAIT-OR-DIE] ⏳ 等待中...{RESET} "
                        f"函数: {func.__name__} "
                        f"重试: {retry_count}/{max_retries if max_retries else '∞'} "
                        f"等待: {current_wait:.2f}秒 "
                        f"异常: {type(e).__name__}: {str(e)}"
                    )

                    # 等待后继续重试
                    time.sleep(current_wait)

        return wrapper

    return decorator


def wait_for_network(
    timeout: Optional[float] = None,
    check_interval: float = 5.0
) -> Callable:
    """
    等待网络恢复的装饰器

    用于那些依赖网络连接的函数。如果网络不可用，
    会自动等待网络恢复后再继续执行。

    Args:
        timeout: 总超时时间（秒），None 表示无限等待
        check_interval: 网络检查间隔（秒）

    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import socket

            start_time = datetime.utcnow()
            check_count = 0

            while True:
                try:
                    # 检查网络连接（尝试连接 Google DNS）
                    socket.create_connection(("8.8.8.8", 53), timeout=2)

                    # 网络可用，执行函数
                    if check_count > 0:
                        logger.info(
                            f"{GREEN}[NETWORK] 网络已恢复{RESET}，"
                            f"执行函数: {func.__name__}"
                        )

                    return func(*args, **kwargs)

                except (socket.error, socket.timeout, OSError):
                    check_count += 1
                    elapsed = (datetime.utcnow() - start_time).total_seconds()

                    # 检查超时
                    if timeout is not None and elapsed > timeout:
                        logger.error(
                            f"{RED}[NETWORK] 网络超时{RESET}，"
                            f"无法在 {timeout}秒 内恢复连接"
                        )
                        raise WaitOrDieException(
                            f"Network unavailable for {elapsed:.2f}s"
                        )

                    # 记录等待信息
                    logger.warning(
                        f"{YELLOW}[NETWORK] ⏳ 等待网络恢复...{RESET} "
                        f"检查次数: {check_count} "
                        f"已等待: {elapsed:.2f}秒"
                    )

                    # 等待后重试
                    time.sleep(check_interval)

        return wrapper

    return decorator


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 示例 1: 基本的 Wait-or-Die
    @wait_or_die(timeout=10, max_retries=3)
    def flaky_api_call():
        import random
        if random.random() < 0.7:
            raise Exception("API 返回 500 错误")
        return {"status": "success"}

    try:
        result = flaky_api_call()
        print(f"结果: {result}")
    except WaitOrDieException as e:
        print(f"失败: {e}")

    # 示例 2: 网络恢复等待
    @wait_for_network(timeout=30)
    def api_requiring_network():
        return "✅ 数据已下载"

    print(api_requiring_network())
