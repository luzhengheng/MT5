#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resilience Module - Wait-or-Die 韧性装饰器 (CSO Security Hardened)

实现无限重试逻辑，确保关键操作在网络波动或短期故障下继续等待，
而不是立即失败。这是 Protocol v4.4 的核心机制。

特性:
  - 指数退避算法防止共振
  - Zero-Trust 参数验证
  - 可重试异常类型限制
  - 敏感信息过滤
  - 结构化日志支持

用法:
  @wait_or_die(timeout=None, exponential_backoff=True)
  def critical_api_call():
      # 这个函数会自动在故障时无限重试
      pass
"""

import time
import logging
import re
import uuid
import socket
from functools import wraps
from typing import Callable, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ANSI 颜色代码
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# 配置常量 (消除魔法数字，便于维护)
DEFAULT_MAX_RETRIES = 50  # 经验值：覆盖大多数暂时性故障（30-60s内恢复）
DEFAULT_INITIAL_WAIT = 1.0  # 秒，首次重试等待间隔
DEFAULT_MAX_WAIT = 60.0  # 秒，指数退避上限（防止等待过长）
DEFAULT_NETWORK_TIMEOUT = 2.0  # 秒，网络检查超时

# 可重试的异常类型 (安全: 不重试系统级异常)
RETRYABLE_EXCEPTIONS: Tuple[type, ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
    IOError,
)

# 网络检查目标 (多个备选，提高全球适配性)
NETWORK_CHECK_HOSTS: list = [
    ("8.8.8.8", 53),        # Google DNS
    ("1.1.1.1", 53),        # Cloudflare DNS
    ("208.67.222.222", 53), # OpenDNS
]


class WaitOrDieException(Exception):
    """Wait-or-Die 机制的异常类"""
    pass


def _sanitize_exception_message(e: Exception, max_length: int = 200) -> str:
    """
    清理异常消息，移除潜在敏感信息

    移除可能包含的:
    - API密钥和令牌
    - 密码
    - 本地文件路径
    - 个人信息
    """
    msg = str(e)

    # 定义需要移除的敏感模式
    sensitive_patterns = [
        r'api[_-]?key[=:]\s*\S+',
        r'password[=:]\s*\S+',
        r'token[=:]\s*\S+',
        r'/home/\w+/',
        r'C:\\Users\\\w+\\',
    ]

    for pattern in sensitive_patterns:
        msg = re.sub(pattern, '[REDACTED]', msg, flags=re.IGNORECASE)

    return msg[:max_length]


def _check_network_available() -> bool:
    """
    检查网络是否可用，尝试多个DNS目标
    提高全球部署的适配性（某些地区可能屏蔽特定IP）
    """
    for host, port in NETWORK_CHECK_HOSTS:
        try:
            socket.create_connection(
                (host, port),
                timeout=DEFAULT_NETWORK_TIMEOUT
            )
            return True
        except (socket.error, socket.timeout, OSError):
            continue
    return False


def wait_or_die(
    timeout: Optional[float] = None,
    exponential_backoff: bool = True,
    max_retries: Optional[int] = DEFAULT_MAX_RETRIES,
    initial_wait: float = DEFAULT_INITIAL_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT
) -> Callable:
    """
    Wait-or-Die 装饰器 - Protocol v4.4 核心机制 (CSO Security Hardened)

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

    Raises:
        ValueError: 参数验证失败 (Zero-Trust)
        WaitOrDieException: 超时或达到最大重试次数
        SystemExit/KeyboardInterrupt: 系统级异常，不重试
    """
    # =========================================================================
    # Zero-Trust: 参数验证 (防守入口，拒绝无效配置)
    # =========================================================================
    if timeout is not None:
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(
                f"timeout 必须是正数，得到 {timeout} ({type(timeout).__name__})"
            )

    if max_retries is not None:
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError(
                f"max_retries 必须是非负整数，得到 {max_retries} ({type(max_retries).__name__})"
            )

    if not isinstance(initial_wait, (int, float)) or initial_wait <= 0:
        raise ValueError(
            f"initial_wait 必须是正数，得到 {initial_wait}"
        )

    if not isinstance(max_wait, (int, float)) or max_wait <= 0:
        raise ValueError(
            f"max_wait 必须是正数，得到 {max_wait}"
        )

    if max_wait < initial_wait:
        raise ValueError(
            f"max_wait ({max_wait}s) 必须 >= initial_wait ({initial_wait}s)"
        )

    if not isinstance(exponential_backoff, bool):
        raise ValueError(
            f"exponential_backoff 必须是布尔值，得到 {type(exponential_backoff).__name__}"
        )

    # =========================================================================
    # 装饰器主逻辑
    # =========================================================================
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成追踪ID便于调试和日志分析
            trace_id = str(uuid.uuid4())[:8]
            start_time = datetime.utcnow()
            retry_count = 0
            current_wait = initial_wait
            last_exception = None

            while True:
                try:
                    # 尝试执行函数
                    result = func(*args, **kwargs)

                    # 成功时记录日志并返回
                    if retry_count > 0:
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        logger.info(
                            f"{GREEN}[WAIT-OR-DIE][{trace_id}] ✅ 成功！{RESET} "
                            f"函数={func.__name__} 重试={retry_count} "
                            f"耗时={elapsed:.2f}s"
                        )
                    return result

                # ============================================================
                # 系统级异常 - 不重试，立即传播 (安全性关键)
                # ============================================================
                except (KeyboardInterrupt, SystemExit) as e:
                    logger.critical(
                        f"{RED}[WAIT-OR-DIE][{trace_id}] 🛑 "
                        f"系统级异常，立即退出: {type(e).__name__}{RESET}"
                    )
                    raise

                # ============================================================
                # 业务级异常 - 检查是否可重试
                # ============================================================
                except RETRYABLE_EXCEPTIONS as e:
                    retry_count += 1
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    last_exception = e

                    sanitized_msg = _sanitize_exception_message(e)

                    # 检查是否超时
                    if timeout is not None and elapsed > timeout:
                        logger.error(
                            f"{RED}[WAIT-OR-DIE][{trace_id}] ❌ 超时！{RESET} "
                            f"函数={func.__name__} 总耗时={elapsed:.2f}s > {timeout}s "
                            f"异常={type(e).__name__}: {sanitized_msg}"
                        )
                        raise WaitOrDieException(
                            f"Timeout after {elapsed:.2f}s: {sanitized_msg}"
                        ) from e

                    # 检查是否超过最大重试次数
                    if max_retries is not None and retry_count > max_retries:
                        logger.error(
                            f"{RED}[WAIT-OR-DIE][{trace_id}] ❌ "
                            f"达到最大重试次数！{RESET} "
                            f"函数={func.__name__} 重试数={retry_count} > {max_retries}"
                        )
                        raise WaitOrDieException(
                            f"Max retries exceeded ({retry_count}): {sanitized_msg}"
                        ) from e

                    # 计算下一次等待时间
                    if exponential_backoff:
                        current_wait = min(
                            initial_wait * (2 ** (retry_count - 1)),
                            max_wait
                        )
                    else:
                        current_wait = initial_wait

                    # 记录结构化重试信息
                    logger.warning(
                        f"{YELLOW}[WAIT-OR-DIE][{trace_id}] ⏳ 等待中...{RESET} "
                        f"函数={func.__name__} 重试={retry_count}/"
                        f"{max_retries if max_retries else '∞'} 等待={current_wait:.2f}s "
                        f"异常={type(e).__name__}"
                    )

                    # 等待后继续重试
                    time.sleep(current_wait)

                # ============================================================
                # 非预期异常 - 不可重试，记录后立即传播
                # ============================================================
                except Exception as e:
                    retry_count += 1
                    sanitized_msg = _sanitize_exception_message(e)
                    logger.error(
                        f"{RED}[WAIT-OR-DIE][{trace_id}] ❌ "
                        f"不可重试异常{RESET} "
                        f"函数={func.__name__} 异常={type(e).__name__}: {sanitized_msg}"
                    )
                    raise

        return wrapper

    return decorator


def wait_for_network(
    timeout: Optional[float] = None,
    check_interval: float = 5.0
) -> Callable:
    """
    等待网络恢复的装饰器 (CSO Security Hardened)

    用于那些依赖网络连接的函数。如果网络不可用，
    会自动等待网络恢复后再继续执行。

    使用多个DNS目标进行检测，提高全球适配性。

    Args:
        timeout: 总超时时间（秒），None 表示无限等待
        check_interval: 网络检查间隔（秒）

    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            trace_id = str(uuid.uuid4())[:8]
            start_time = datetime.utcnow()
            check_count = 0

            while True:
                # 使用多目标网络检查函数
                if _check_network_available():
                    if check_count > 0:
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        logger.info(
                            f"{GREEN}[NETWORK][{trace_id}] 网络已恢复{RESET}，"
                            f"耗时={elapsed:.2f}s，执行函数={func.__name__}"
                        )

                    return func(*args, **kwargs)

                # 网络不可用，继续等待
                check_count += 1
                elapsed = (datetime.utcnow() - start_time).total_seconds()

                # 检查超时
                if timeout is not None and elapsed > timeout:
                    logger.error(
                        f"{RED}[NETWORK][{trace_id}] 🛑 网络超时{RESET}，"
                        f"无法在 {timeout}秒 内恢复连接"
                    )
                    raise WaitOrDieException(
                        f"Network unavailable for {elapsed:.2f}s"
                    )

                # 记录等待信息
                logger.warning(
                    f"{YELLOW}[NETWORK][{trace_id}] ⏳ 等待网络恢复...{RESET} "
                    f"检查次数={check_count} 已等待={elapsed:.2f}s"
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
