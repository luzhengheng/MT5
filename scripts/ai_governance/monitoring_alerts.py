#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成本优化器监控告警系统
Monitoring and Alerting System for Cost Optimizer

监控指标:
1. API 调用次数 - 检测异常高的调用量
2. 缓存命中率 - 验证缓存有效性
3. 成本节省率 - 确保优化效果
4. 批处理效率 - 检测批处理是否有效

告警规则:
1. WARNING: API 调用次数异常高
2. CRITICAL: 缓存命中率过低
3. WARNING: 成本节省不足预期
4. CRITICAL: 优化器故障
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

# 颜色定义
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class AlertLevel(Enum):
    """告警级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class MonitoringAlert:
    """单个告警"""

    def __init__(self, name, level, metric, threshold, actual):
        self.name = name
        self.level = level
        self.metric = metric
        self.threshold = threshold
        self.actual = actual
        self.timestamp = datetime.now()

    def __str__(self):
        color = {
            AlertLevel.INFO: CYAN,
            AlertLevel.WARNING: YELLOW,
            AlertLevel.CRITICAL: RED,
        }.get(self.level, RESET)

        return (
            f"{color}[{self.level.value}] {self.name}\n"
            f"  Metric: {self.metric}\n"
            f"  Threshold: {self.threshold}\n"
            f"  Actual: {self.actual}\n"
            f"  Time: {self.timestamp.isoformat()}{RESET}"
        )


class MonitoringConfig:
    """监控配置"""

    def __init__(self):
        """初始化监控配置"""
        # API 调用次数告警
        self.api_calls_warning = 100  # 单次 > 100 次调用触发警告
        self.api_calls_critical = 500  # 单次 > 500 次调用触发严重告警

        # 缓存命中率告警
        self.cache_hit_warning = 0.3  # 缓存命中率 < 30% 触发警告
        self.cache_hit_critical = 0.1  # 缓存命中率 < 10% 触发严重告警

        # 成本节省告警
        self.cost_reduction_warning = 0.8  # 成本节省 < 80% 触发警告
        self.cost_reduction_critical = 0.5  # 成本节省 < 50% 触发严重告警

        # 批处理效率告警
        self.batch_size_warning = 3  # 平均批大小 < 3 触发警告
        self.batch_efficiency_warning = 0.5  # 批处理效率 < 50% 触发警告


class CostOptimizerMonitor:
    """成本优化器监控系统"""

    def __init__(self, config=None, log_file="monitoring_alerts.log"):
        """
        初始化监控系统

        Args:
            config: MonitoringConfig 实例
            log_file: 日志文件路径
        """
        self.config = config or MonitoringConfig()
        self.log_file = log_file
        self.alerts = []
        self.alert_history = []

        # 设置日志
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger("CostOptimizerMonitor")
        logger.setLevel(logging.INFO)

        # 文件处理器
        if self.log_file:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def check_api_calls(self, api_calls):
        """
        检查 API 调用次数

        Args:
            api_calls: API 调用次数

        Returns:
            bool: 是否正常
        """
        if api_calls > self.config.api_calls_critical:
            alert = MonitoringAlert(
                "API Calls Critical",
                AlertLevel.CRITICAL,
                "api_calls",
                f"<= {self.config.api_calls_critical}",
                api_calls,
            )
            self.alerts.append(alert)
            self.logger.error(f"API calls exceeded critical threshold: {api_calls}")
            return False

        elif api_calls > self.config.api_calls_warning:
            alert = MonitoringAlert(
                "API Calls Warning",
                AlertLevel.WARNING,
                "api_calls",
                f"<= {self.config.api_calls_warning}",
                api_calls,
            )
            self.alerts.append(alert)
            self.logger.warning(f"API calls exceeded warning threshold: {api_calls}")
            return True

        return True

    def check_cache_hit_rate(self, cache_hit_rate):
        """
        检查缓存命中率

        Args:
            cache_hit_rate: 缓存命中率 (0-1)

        Returns:
            bool: 是否正常
        """
        if cache_hit_rate < self.config.cache_hit_critical:
            alert = MonitoringAlert(
                "Cache Hit Rate Critical",
                AlertLevel.CRITICAL,
                "cache_hit_rate",
                f">= {self.config.cache_hit_critical:.1%}",
                f"{cache_hit_rate:.1%}",
            )
            self.alerts.append(alert)
            self.logger.error(f"Cache hit rate critically low: {cache_hit_rate:.1%}")
            return False

        elif cache_hit_rate < self.config.cache_hit_warning:
            alert = MonitoringAlert(
                "Cache Hit Rate Warning",
                AlertLevel.WARNING,
                "cache_hit_rate",
                f">= {self.config.cache_hit_warning:.1%}",
                f"{cache_hit_rate:.1%}",
            )
            self.alerts.append(alert)
            self.logger.warning(f"Cache hit rate low: {cache_hit_rate:.1%}")
            return True

        return True

    def check_cost_reduction(self, cost_reduction_rate):
        """
        检查成本节省率

        Args:
            cost_reduction_rate: 成本节省率 (0-1)

        Returns:
            bool: 是否正常
        """
        if cost_reduction_rate < self.config.cost_reduction_critical:
            alert = MonitoringAlert(
                "Cost Reduction Critical",
                AlertLevel.CRITICAL,
                "cost_reduction_rate",
                f">= {self.config.cost_reduction_critical:.1%}",
                f"{cost_reduction_rate:.1%}",
            )
            self.alerts.append(alert)
            self.logger.error(
                f"Cost reduction rate critically low: {cost_reduction_rate:.1%}"
            )
            return False

        elif cost_reduction_rate < self.config.cost_reduction_warning:
            alert = MonitoringAlert(
                "Cost Reduction Warning",
                AlertLevel.WARNING,
                "cost_reduction_rate",
                f">= {self.config.cost_reduction_warning:.1%}",
                f"{cost_reduction_rate:.1%}",
            )
            self.alerts.append(alert)
            self.logger.warning(
                f"Cost reduction rate below expectations: {cost_reduction_rate:.1%}"
            )
            return True

        return True

    def check_batch_efficiency(self, total_files, api_calls):
        """
        检查批处理效率

        Args:
            total_files: 总文件数
            api_calls: API 调用次数

        Returns:
            bool: 是否正常
        """
        if api_calls == 0:
            efficiency = 1.0
            avg_batch_size = total_files
        else:
            efficiency = 1 - (api_calls / total_files)
            avg_batch_size = total_files / api_calls

        if avg_batch_size < self.config.batch_size_warning:
            alert = MonitoringAlert(
                "Batch Size Warning",
                AlertLevel.WARNING,
                "avg_batch_size",
                f">= {self.config.batch_size_warning}",
                f"{avg_batch_size:.1f}",
            )
            self.alerts.append(alert)
            self.logger.warning(f"Average batch size too small: {avg_batch_size:.1f}")
            return True

        if efficiency < self.config.batch_efficiency_warning:
            alert = MonitoringAlert(
                "Batch Efficiency Warning",
                AlertLevel.WARNING,
                "batch_efficiency",
                f">= {self.config.batch_efficiency_warning:.1%}",
                f"{efficiency:.1%}",
            )
            self.alerts.append(alert)
            self.logger.warning(f"Batch efficiency low: {efficiency:.1%}")
            return True

        return True

    def check_stats(self, stats):
        """
        检查优化器统计信息

        Args:
            stats: 来自 AIReviewCostOptimizer.process_files() 的统计字典

        Returns:
            bool: 是否所有检查都通过
        """
        self.alerts.clear()

        # 提取统计信息
        total_files = stats.get("total_files", 0)
        api_calls = stats.get("api_calls", 0)
        cache_hit_rate = stats.get("cache_hit_rate", 0)
        cost_reduction_rate = stats.get("cost_reduction_rate", 0)

        # 运行所有检查
        api_ok = self.check_api_calls(api_calls)
        cache_ok = self.check_cache_hit_rate(cache_hit_rate)
        cost_ok = self.check_cost_reduction(cost_reduction_rate)
        batch_ok = self.check_batch_efficiency(total_files, api_calls)

        # 记录告警历史
        self.alert_history.extend(self.alerts)

        # 返回结果
        return api_ok and cache_ok and cost_ok and batch_ok

    def print_alerts(self):
        """打印当前告警"""
        if not self.alerts:
            print(f"{GREEN}✅ 无告警 - 所有指标正常{RESET}")
            return

        print(f"\n{RED}{'='*80}{RESET}")
        print(f"{RED}⚠️  检测到 {len(self.alerts)} 个告警{RESET}")
        print(f"{RED}{'='*80}{RESET}\n")

        for alert in self.alerts:
            print(alert)
            print()

    def get_alert_summary(self):
        """获取告警摘要"""
        if not self.alerts:
            return "无告警 - 所有指标正常"

        critical_count = sum(
            1 for a in self.alerts if a.level == AlertLevel.CRITICAL
        )
        warning_count = sum(1 for a in self.alerts if a.level == AlertLevel.WARNING)

        return (
            f"{critical_count} 个严重告警, {warning_count} 个警告"
        )


def create_default_config():
    """创建默认监控配置"""
    return MonitoringConfig()


def example_usage():
    """示例使用"""
    print(f"{CYAN}成本优化器监控系统 - 示例{RESET}\n")

    # 创建监控器
    monitor = CostOptimizerMonitor()

    # 模拟统计数据 - 正常情况
    print(f"{BLUE}测试 1: 正常统计数据{RESET}")
    stats_ok = {
        "total_files": 50,
        "api_calls": 3,
        "cached_files": 35,
        "uncached_files": 15,
        "cache_hit_rate": 0.7,
        "cost_reduction_rate": 0.94,
    }
    result = monitor.check_stats(stats_ok)
    monitor.print_alerts()
    print(f"检查结果: {'✅ 通过' if result else '❌ 失败'}\n")

    # 模拟统计数据 - 警告
    print(f"{BLUE}测试 2: 缓存命中率低的统计数据{RESET}")
    stats_warn = {
        "total_files": 50,
        "api_calls": 30,
        "cached_files": 5,
        "uncached_files": 45,
        "cache_hit_rate": 0.15,  # 低于警告阈值
        "cost_reduction_rate": 0.4,  # 低于严重告警阈值
    }
    result = monitor.check_stats(stats_warn)
    monitor.print_alerts()
    print(f"检查结果: {'✅ 通过（有告警）' if not result else '❌ 失败'}\n")

    # 监控配置参考
    print(f"{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}监控配置参考{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}\n")

    config = monitor.config
    print(f"API 调用次数:")
    print(f"  WARNING: > {config.api_calls_warning}")
    print(f"  CRITICAL: > {config.api_calls_critical}\n")

    print(f"缓存命中率:")
    print(f"  WARNING: < {config.cache_hit_warning:.1%}")
    print(f"  CRITICAL: < {config.cache_hit_critical:.1%}\n")

    print(f"成本节省率:")
    print(f"  WARNING: < {config.cost_reduction_warning:.1%}")
    print(f"  CRITICAL: < {config.cost_reduction_critical:.1%}\n")

    print(f"批处理效率:")
    print(f"  WARNING (batch size): < {config.batch_size_warning}")
    print(f"  WARNING (efficiency): < {config.batch_efficiency_warning:.1%}\n")


if __name__ == "__main__":
    example_usage()
