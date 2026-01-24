#!/usr/bin/env python3
"""
Task #135 审计脚本 (Policy-as-Code)
功能: 验证动态风险管理系统的实现正确性
Protocol: v4.4
生成时间: 2026-01-23
作者: System Architect
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 审计规则定义
AUDIT_RULES = [
    {"id": "RULE_135_001", "name": "风险模块导入验证", "severity": "CRITICAL"},
    {"id": "RULE_135_002", "name": "枚举类型验证", "severity": "CRITICAL"},
    {"id": "RULE_135_003", "name": "数据模型验证", "severity": "CRITICAL"},
    {"id": "RULE_135_004", "name": "配置定义验证", "severity": "HIGH"},
    {"id": "RULE_135_005", "name": "熔断器验证", "severity": "HIGH"},
    {"id": "RULE_135_006", "name": "回撤监控验证", "severity": "HIGH"},
    {"id": "RULE_135_007", "name": "敞口监控验证", "severity": "HIGH"},
    {"id": "RULE_135_008", "name": "配置文件验证", "severity": "HIGH"},
]


class Task135Auditor:
    """Task #135 审计器"""

    def __init__(self, project_root: Path = None):
        """初始化审计器"""
        self.project_root = project_root or Path("/opt/mt5-crs")
        self.issues = []
        self.passed_rules = []

    def run_all_audits(self) -> bool:
        """运行所有审计"""
        logger.info("[AUDIT START] Task #135 动态风险管理系统")
        logger.info(f"项目根目录: {self.project_root}")

        self.audit_module_import()
        self.audit_enums()
        self.audit_models()
        self.audit_config()
        self.audit_circuit_breaker()
        self.audit_drawdown_monitor()
        self.audit_exposure_monitor()
        self.audit_yaml_config()

        self.generate_report()
        return len(self.issues) == 0

    def audit_module_import(self):
        """检查风险模块导入"""
        rule_id = "RULE_135_001"
        try:
            sys.path.insert(0, str(self.project_root))
            import src.risk
            logger.info(f"✅ {rule_id}: 风险模块成功导入")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"模块导入失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_enums(self):
        """检查枚举类型"""
        rule_id = "RULE_135_002"
        try:
            from src.risk.enums import RiskLevel, CircuitState, RiskAction, TrackType
            
            # 验证RiskLevel
            assert hasattr(RiskLevel, 'NORMAL')
            assert hasattr(RiskLevel, 'WARNING')
            assert hasattr(RiskLevel, 'CRITICAL')
            assert hasattr(RiskLevel, 'HALT')
            
            # 验证CircuitState
            assert hasattr(CircuitState, 'CLOSED')
            assert hasattr(CircuitState, 'OPEN')
            assert hasattr(CircuitState, 'HALF_OPEN')
            
            # 验证RiskAction
            assert hasattr(RiskAction, 'ALLOW')
            assert hasattr(RiskAction, 'REJECT')
            assert hasattr(RiskAction, 'REDUCE_ONLY')
            assert hasattr(RiskAction, 'FORCE_CLOSE')
            
            # 验证TrackType
            track_types = {t.value for t in TrackType}
            assert 'EUR' in track_types
            assert 'BTC' in track_types
            assert 'GBP' in track_types
            
            logger.info(f"✅ {rule_id}: 所有枚举类型验证通过")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"枚举类型验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_models(self):
        """检查数据模型"""
        rule_id = "RULE_135_003"
        try:
            from src.risk.models import (
                RiskContext, PositionInfo, RiskDecision,
                RiskEvent, SymbolRiskState, AccountRiskState
            )
            
            # 验证RiskContext
            assert hasattr(RiskContext, 'symbol')
            assert hasattr(RiskContext, 'order_value')
            assert hasattr(RiskContext, 'is_opening')
            
            # 验证RiskDecision
            assert hasattr(RiskDecision, 'is_allowed')
            assert hasattr(RiskDecision, 'to_dict')
            
            # 验证AccountRiskState
            assert hasattr(AccountRiskState, 'daily_total_pnl')
            assert hasattr(AccountRiskState, 'drawdown_percentage')
            
            logger.info(f"✅ {rule_id}: 所有数据模型验证通过")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"数据模型验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_config(self):
        """检查配置定义"""
        rule_id = "RULE_135_004"
        try:
            from src.risk.config import (
                CircuitBreakerConfig, DrawdownConfig,
                ExposureConfig, RiskConfig
            )
            
            # 验证配置实例化
            cb_config = CircuitBreakerConfig()
            assert cb_config.max_consecutive_losses == 3
            assert cb_config.cooldown_seconds == 300
            
            dd_config = DrawdownConfig()
            assert dd_config.warning_threshold > 0
            assert dd_config.halt_threshold > dd_config.critical_threshold
            
            exp_config = ExposureConfig()
            assert exp_config.max_positions > 0
            
            risk_config = RiskConfig()
            assert risk_config.circuit_breaker is not None
            assert risk_config.drawdown is not None
            assert risk_config.exposure is not None
            
            logger.info(f"✅ {rule_id}: 所有配置定义验证通过")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"配置定义验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_circuit_breaker(self):
        """检查熔断器"""
        rule_id = "RULE_135_005"
        try:
            from src.risk.circuit_breaker import CircuitBreaker
            from src.risk.config import CircuitBreakerConfig
            from src.risk.enums import CircuitState
            
            # 创建熔断器实例
            cb_config = CircuitBreakerConfig()
            cb = CircuitBreaker("EURUSD.s", cb_config)
            
            # 验证初始状态
            assert cb.state.circuit_state == CircuitState.CLOSED
            assert cb.state.consecutive_losses == 0
            
            # 验证状态转换方法
            assert hasattr(cb, 'check')
            assert hasattr(cb, 'record_trade_result')
            assert hasattr(cb, 'get_status')
            
            logger.info(f"✅ {rule_id}: 熔断器验证通过")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"熔断器验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_drawdown_monitor(self):
        """检查回撤监控"""
        rule_id = "RULE_135_006"
        try:
            from src.risk.drawdown_monitor import DrawdownMonitor
            from src.risk.config import DrawdownConfig
            from src.risk.enums import RiskLevel
            
            # 创建回撤监控器实例
            dd_config = DrawdownConfig()
            dm = DrawdownMonitor(dd_config)
            
            # 验证初始状态
            assert dm.state.risk_level == RiskLevel.NORMAL
            assert dm.state.current_drawdown == 0
            
            # 验证方法
            assert hasattr(dm, 'check')
            assert hasattr(dm, 'update_daily_pnl')
            assert hasattr(dm, 'reset_daily')
            
            logger.info(f"✅ {rule_id}: 回撤监控验证通过")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"回撤监控验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_exposure_monitor(self):
        """检查敞口监控"""
        rule_id = "RULE_135_007"
        try:
            from src.risk.exposure_monitor import ExposureMonitor
            from src.risk.config import ExposureConfig
            
            # 创建敞口监控器实例
            exp_config = ExposureConfig()
            em = ExposureMonitor(exp_config)
            
            # 验证方法
            assert hasattr(em, 'check')
            assert hasattr(em, 'get_status')
            assert hasattr(em, '_calculate_exposure_after_order')
            
            logger.info(f"✅ {rule_id}: 敞口监控验证通过")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"敞口监控验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_yaml_config(self):
        """检查YAML配置"""
        rule_id = "RULE_135_008"
        try:
            import yaml
            config_path = self.project_root / "config" / "trading_config.yaml"
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 验证风险配置存在
            assert 'risk' in config
            risk_config = config['risk']
            
            # 验证三层风险配置
            assert 'circuit_breaker' in risk_config
            assert 'drawdown' in risk_config
            assert 'exposure' in risk_config
            assert 'track_limits' in risk_config
            
            # 验证轨道限制
            track_limits = risk_config['track_limits']
            assert 'EUR' in track_limits
            assert 'BTC' in track_limits
            assert 'GBP' in track_limits
            
            logger.info(f"✅ {rule_id}: YAML配置验证通过")
            logger.info(f"   - Circuit Breaker: ✅")
            logger.info(f"   - Drawdown Monitor: ✅")
            logger.info(f"   - Exposure Monitor: ✅")
            logger.info(f"   - 3-Track Limits: EUR/BTC/GBP ✅")
            
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"YAML配置验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def generate_report(self):
        """生成审计报告"""
        logger.info("\n" + "="*60)
        logger.info("[AUDIT REPORT] Task #135 动态风险管理系统")
        logger.info("="*60)

        logger.info(f"\n✅ 通过规则: {len(self.passed_rules)}/{len(AUDIT_RULES)}")
        for rule_id in self.passed_rules:
            rule = next((r for r in AUDIT_RULES if r['id'] == rule_id), None)
            if rule:
                logger.info(f"   ✅ {rule_id}: {rule['name']}")

        if self.issues:
            logger.error(f"\n❌ 失败规则: {len(self.issues)}")
            for rule_id, msg in self.issues:
                logger.error(f"   ❌ {rule_id}: {msg}")

        logger.info("\n" + "="*60)

        if not self.issues:
            logger.info("[PHYSICAL_EVIDENCE] 审计结果: ✅ PASS")
            logger.info("[UnifiedGate] PASS - Task #135 代码审计通过")
        else:
            logger.error("[PHYSICAL_EVIDENCE] 审计结果: ❌ FAIL")
            logger.error("[UnifiedGate] FAIL - 存在需要修复的问题")

        logger.info("="*60)


def main():
    """主函数"""
    auditor = Task135Auditor()
    success = auditor.run_all_audits()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
