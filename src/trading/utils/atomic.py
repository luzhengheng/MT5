"""
原子操作工具模块

提供线程安全的原子计数器和其他并发原语。
"""

import threading
from typing import Optional


class AtomicCounter:
    """
    线程安全的原子计数器

    使用锁机制确保计数操作的原子性。
    支持增加、减少、获取当前值等操作。
    """

    def __init__(self, initial_value: int = 0):
        """
        初始化计数器

        Args:
            initial_value: 初始值
        """
        self._value = initial_value
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> int:
        """
        原子增加计数器

        Args:
            delta: 增加量

        Returns:
            int: 增加后的值
        """
        with self._lock:
            self._value += delta
            return self._value

    def decrement(self, delta: int = 1) -> int:
        """
        原子减少计数器

        Args:
            delta: 减少量

        Returns:
            int: 减少后的值
        """
        with self._lock:
            self._value -= delta
            return self._value

    def get(self) -> int:
        """
        获取当前值

        Returns:
            int: 当前计数值
        """
        with self._lock:
            return self._value

    def set(self, value: int) -> None:
        """
        设置计数器值

        Args:
            value: 新值
        """
        with self._lock:
            self._value = value

    def compare_and_set(self, expected: int, new_value: int) -> bool:
        """
        比较并设置（CAS操作）

        Args:
            expected: 期望的当前值
            new_value: 要设置的新值

        Returns:
            bool: 如果当前值等于期望值则设置成功返回True
        """
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False

    def increment_if_less_than(self, limit: int) -> bool:
        """
        如果当前值小于限制则增加

        用于实现有上限的计数器。

        Args:
            limit: 上限值

        Returns:
            bool: 是否成功增加
        """
        with self._lock:
            if self._value < limit:
                self._value += 1
                return True
            return False


class AtomicFlag:
    """
    线程安全的原子标志

    用于实现简单的开关状态。
    """

    def __init__(self, initial_value: bool = False):
        """
        初始化标志

        Args:
            initial_value: 初始值
        """
        self._value = initial_value
        self._lock = threading.Lock()

    def set(self) -> bool:
        """
        设置标志为True

        Returns:
            bool: 之前的值
        """
        with self._lock:
            old_value = self._value
            self._value = True
            return old_value

    def clear(self) -> bool:
        """
        清除标志（设为False）

        Returns:
            bool: 之前的值
        """
        with self._lock:
            old_value = self._value
            self._value = False
            return old_value

    def get(self) -> bool:
        """
        获取当前值

        Returns:
            bool: 当前标志值
        """
        with self._lock:
            return self._value
