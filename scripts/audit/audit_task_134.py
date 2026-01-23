#!/usr/bin/env python3
"""
Task #134 审计脚本 (Policy-as-Code)
功能: 验证三轨交易系统实现的正确性
Protocol: v4.4
生成时间: 2026-01-23
作者: System Architect
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# ========================================
# 常量定义
# ========================================

AUDIT_RULES = [
    {
        "id": "RULE_134_001",
        "name": "三轨配置验证",
        "description": "验证 trading_config.yaml 中正确定义了三个活跃的交易符号（EURUSD.s、BTCUSD.s、GBPUSD.s）",
        "severity": "CRITICAL",
    },
    {
        "id": "RULE_134_002",
        "name": "交易模块导入验证",
        "description": "验证 src/trading 模块可以正常导入，包含所有必要的子模块",
        "severity": "CRITICAL",
    },
    {
        "id": "RULE_134_003",
        "name": "资产类型验证",
        "description": "验证 AssetType 枚举包含 EUR、BTC、GBP 三种资产",
        "severity": "CRITICAL",
    },
    {
        "id": "RULE_134_004",
        "name": "并发限制验证",
        "description": "验证全局并发限制和轨道级限制配置正确",
        "severity": "HIGH",
    },
    {
        "id": "RULE_134_005",
        "name": "订单状态机验证",
        "description": "验证订单状态转换的有限状态机实现正确",
        "severity": "HIGH",
    },
    {
        "id": "RULE_134_006",
        "name": "调度器路由验证",
        "description": "验证 TrackDispatcher 能够正确路由到对应的轨道",
        "severity": "HIGH",
    },
    {
        "id": "RULE_134_007",
        "name": "原子操作验证",
        "description": "验证 AtomicCounter 和 AtomicFlag 的线程安全性",
        "severity": "MEDIUM",
    },
    {
        "id": "RULE_134_008",
        "name": "指标收集验证",
        "description": "验证 MetricsCollector 能够正确收集系统指标",
        "severity": "MEDIUM",
    },
]


class Task134Auditor:
    """Task #134 审计器"""

    def __init__(self, project_root: Path = None):
        """初始化审计器"""
        self.project_root = project_root or Path("/opt/mt5-crs")
        self.issues = []
        self.warnings = []
        self.passed_rules = []

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def run_all_audits(self) -> bool:
        """运行所有审计检查"""
        self.logger.info("[AUDIT START] Task #134 三轨交易系统审计")
        self.logger.info(f"项目根目录: {self.project_root}")

        # 执行所有审计规则
        self.audit_trading_config()
        self.audit_trading_module_import()
        self.audit_asset_types()
        self.audit_concurrency_limits()
        self.audit_order_state_machine()
        self.audit_dispatcher_routing()
        self.audit_atomic_operations()
        self.audit_metrics_collection()

        # 生成报告
        self.generate_report()

        return len(self.issues) == 0

    def audit_trading_config(self):
        """检查 trading_config.yaml 配置"""
        rule_id = "RULE_134_001"
        config_path = self.project_root / "config" / "trading_config.yaml"

        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # 检查符号配置
            symbols = config.get('symbols', [])
            active_symbols = [s for s in symbols if s.get('active', False)]
            symbol_names = [s['symbol'] for s in active_symbols]

            required_symbols = ['EURUSD.s', 'BTCUSD.s', 'GBPUSD.s']
            missing = set(required_symbols) - set(symbol_names)

            if missing:
                msg = f"缺失必要的活跃符号: {missing}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")
            else:
                self.logger.info(f"✅ {rule_id}: 所有三个符号已正确配置为活跃状态")
                self.passed_rules.append(rule_id)

                # 检查配置详情
                for symbol in active_symbols:
                    symbol_name = symbol['symbol']
                    magic = symbol.get('magic_number')
                    lot = symbol.get('lot_size')
                    self.logger.info(f"   - {symbol_name}: magic={magic}, lot_size={lot}")

        except Exception as e:
            msg = f"配置文件检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_trading_module_import(self):
        """检查交易模块导入"""
        rule_id = "RULE_134_002"

        try:
            # 检查目录结构
            trading_dir = self.project_root / "src" / "trading"
            required_dirs = ["models", "core", "utils"]
            required_files = {
                "models": ["__init__.py", "enums.py", "config.py", "order.py"],
                "core": ["__init__.py", "limiter.py", "track.py", "dispatcher.py"],
                "utils": ["__init__.py", "atomic.py", "metrics.py"],
            }

            missing_dirs = []
            for dir_name in required_dirs:
                dir_path = trading_dir / dir_name
                if not dir_path.exists():
                    missing_dirs.append(dir_name)

            missing_files = []
            for dir_name, files in required_files.items():
                for file_name in files:
                    file_path = trading_dir / dir_name / file_name
                    if not file_path.exists():
                        missing_files.append(f"{dir_name}/{file_name}")

            if missing_dirs or missing_files:
                msg = f"缺失目录/文件 - 目录: {missing_dirs}, 文件: {missing_files}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")
            else:
                # 尝试导入模块
                sys.path.insert(0, str(self.project_root))
                try:
                    import src.trading
                    self.logger.info(f"✅ {rule_id}: 交易模块目录结构完整且可导入")
                    self.passed_rules.append(rule_id)
                except ImportError as e:
                    msg = f"模块导入失败: {str(e)}"
                    self.issues.append((rule_id, msg))
                    self.logger.error(f"❌ {rule_id}: {msg}")

        except Exception as e:
            msg = f"模块导入检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_asset_types(self):
        """检查资产类型"""
        rule_id = "RULE_134_003"

        try:
            sys.path.insert(0, str(self.project_root))
            from src.trading.models import AssetType

            required_types = {'EUR', 'BTC', 'GBP'}
            actual_types = {asset.value for asset in AssetType}

            if required_types == actual_types:
                self.logger.info(f"✅ {rule_id}: AssetType 包含所有三种资产类型")
                self.passed_rules.append(rule_id)
                for asset in AssetType:
                    self.logger.info(f"   - {asset.value}")
            else:
                msg = f"资产类型不匹配 - 期望: {required_types}, 实际: {actual_types}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")

        except Exception as e:
            msg = f"资产类型检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_concurrency_limits(self):
        """检查并发限制"""
        rule_id = "RULE_134_004"

        try:
            sys.path.insert(0, str(self.project_root))
            from src.trading import DispatcherConfig

            config = DispatcherConfig()

            # 验证全局限制
            if config.global_max_concurrent > 0:
                self.logger.info(f"✅ {rule_id}: 并发限制配置正确")
                self.logger.info(f"   - 全局最大并发: {config.global_max_concurrent}")
                self.logger.info(f"   - 全局限制/秒: {config.global_rate_limit_per_second}")

                # 检查轨道配置
                for asset_type, track_config in config.track_configs.items():
                    self.logger.info(
                        f"   - {asset_type.value} 轨道: "
                        f"max_concurrent={track_config.max_concurrent}, "
                        f"rate={track_config.rate_limit_per_second}/sec"
                    )

                self.passed_rules.append(rule_id)
            else:
                msg = "全局并发限制配置无效"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")

        except Exception as e:
            msg = f"并发限制检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_order_state_machine(self):
        """检查订单状态机"""
        rule_id = "RULE_134_005"

        try:
            sys.path.insert(0, str(self.project_root))
            from src.trading.models import OrderStatus

            # 检查所有状态都有定义
            expected_states = {
                'PENDING', 'QUEUED', 'PROCESSING', 'EXECUTED',
                'FAILED', 'CANCELLED', 'REJECTED'
            }
            actual_states = {status.value for status in OrderStatus}

            if expected_states == actual_states:
                self.logger.info(f"✅ {rule_id}: 订单状态机完整")

                # 检查状态转换规则
                test_transitions = [
                    (OrderStatus.PENDING, OrderStatus.QUEUED, True),
                    (OrderStatus.PENDING, OrderStatus.REJECTED, True),
                    (OrderStatus.QUEUED, OrderStatus.PROCESSING, True),
                    (OrderStatus.QUEUED, OrderStatus.CANCELLED, True),
                    (OrderStatus.PROCESSING, OrderStatus.EXECUTED, True),
                    (OrderStatus.PROCESSING, OrderStatus.FAILED, True),
                    (OrderStatus.EXECUTED, OrderStatus.PENDING, False),  # 不允许
                ]

                all_correct = True
                for from_status, to_status, should_allow in test_transitions:
                    can_transition = from_status.can_transition_to(to_status)
                    if can_transition != should_allow:
                        all_correct = False
                        self.logger.warning(
                            f"   状态转换异常: {from_status.value} -> {to_status.value}"
                        )

                if all_correct:
                    self.logger.info("   状态转换规则验证正确")
                    self.passed_rules.append(rule_id)
                else:
                    msg = "订单状态转换规则验证失败"
                    self.issues.append((rule_id, msg))
                    self.logger.error(f"❌ {rule_id}: {msg}")
            else:
                msg = f"订单状态不完整 - 缺失: {expected_states - actual_states}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")

        except Exception as e:
            msg = f"订单状态机检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_dispatcher_routing(self):
        """检查调度器路由"""
        rule_id = "RULE_134_006"

        try:
            sys.path.insert(0, str(self.project_root))
            from src.trading import TrackDispatcher, AssetType

            dispatcher = TrackDispatcher()

            # 检查所有轨道都被创建
            expected_assets = {AssetType.EUR, AssetType.BTC, AssetType.GBP}
            actual_tracks = set(dispatcher.tracks.keys())

            if expected_assets == actual_tracks:
                self.logger.info(f"✅ {rule_id}: 调度器包含所有三个轨道")

                for asset_type, track in dispatcher.tracks.items():
                    self.logger.info(
                        f"   - {track.get_track_id()}: "
                        f"asset={asset_type.value}, "
                        f"active_orders={track.get_active_count()}"
                    )

                self.passed_rules.append(rule_id)
                dispatcher.shutdown_all()
            else:
                msg = f"轨道数量不正确 - 缺失: {expected_assets - actual_tracks}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")
                dispatcher.shutdown_all()

        except Exception as e:
            msg = f"调度器路由检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_atomic_operations(self):
        """检查原子操作"""
        rule_id = "RULE_134_007"

        try:
            sys.path.insert(0, str(self.project_root))
            from src.trading.utils import AtomicCounter, AtomicFlag
            import threading

            # 测试 AtomicCounter
            counter = AtomicCounter(0)

            def increment_counter():
                for _ in range(100):
                    counter.increment()

            threads = [threading.Thread(target=increment_counter) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            if counter.get() == 1000:
                self.logger.info(f"✅ {rule_id}: 原子操作验证正确")
                self.logger.info(f"   - AtomicCounter: 10线程 x 100增量 = {counter.get()}")

                # 测试 AtomicFlag
                flag = AtomicFlag(False)
                old_val = flag.set()
                if old_val == False and flag.get() == True:
                    self.logger.info("   - AtomicFlag: 工作正确")
                    self.passed_rules.append(rule_id)
                else:
                    raise AssertionError("AtomicFlag 状态转换异常")
            else:
                msg = f"并发计数异常: 期望1000，得到{counter.get()}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")

        except Exception as e:
            msg = f"原子操作检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def audit_metrics_collection(self):
        """检查指标收集"""
        rule_id = "RULE_134_008"

        try:
            sys.path.insert(0, str(self.project_root))
            from src.trading.utils import MetricsCollector

            metrics = MetricsCollector()

            # 记录一些操作
            metrics.record_order_submitted()
            metrics.record_order_success(100.5, "TRACK_EUR")
            metrics.record_order_submitted()
            metrics.record_order_failure("TRACK_BTC", "TIMEOUT")

            summary = metrics.get_summary()

            if (summary['total_orders'] == 2 and
                summary['successful_orders'] == 1 and
                summary['failed_orders'] == 1):
                self.logger.info(f"✅ {rule_id}: 指标收集工作正确")
                self.logger.info(f"   - 总订单数: {summary['total_orders']}")
                self.logger.info(f"   - 成功: {summary['successful_orders']}")
                self.logger.info(f"   - 失败: {summary['failed_orders']}")
                self.logger.info(f"   - 成功率: {summary['success_rate_percent']}%")
                self.passed_rules.append(rule_id)
            else:
                msg = f"指标数据异常: {summary}"
                self.issues.append((rule_id, msg))
                self.logger.error(f"❌ {rule_id}: {msg}")

        except Exception as e:
            msg = f"指标收集检查异常: {str(e)}"
            self.issues.append((rule_id, msg))
            self.logger.error(f"❌ {rule_id}: {msg}")

    def generate_report(self):
        """生成审计报告"""
        self.logger.info("\n" + "="*60)
        self.logger.info("[AUDIT REPORT] Task #134 三轨交易系统")
        self.logger.info("="*60)

        self.logger.info(f"\n✅ 通过规则: {len(self.passed_rules)}/{len(AUDIT_RULES)}")
        for rule_id in self.passed_rules:
            rule = next((r for r in AUDIT_RULES if r['id'] == rule_id), None)
            if rule:
                self.logger.info(f"   ✅ {rule_id}: {rule['name']}")

        if self.issues:
            self.logger.error(f"\n❌ 失败规则: {len(self.issues)}")
            for rule_id, msg in self.issues:
                self.logger.error(f"   ❌ {rule_id}: {msg}")

        self.logger.info("\n" + "="*60)

        if not self.issues:
            self.logger.info("[PHYSICAL_EVIDENCE] 审计结果: ✅ PASS")
            self.logger.info("[UnifiedGate] PASS - Task #134 代码审计通过")
        else:
            self.logger.error("[PHYSICAL_EVIDENCE] 审计结果: ❌ FAIL")
            self.logger.error("[UnifiedGate] FAIL - 存在需要修复的问题")

        self.logger.info("="*60)


def main():
    """主函数"""
    auditor = Task134Auditor()
    success = auditor.run_all_audits()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
