#!/usr/bin/env python3
"""
Task #135 审计脚本 (Policy-as-Code) - Fixed Version
功能: 验证动态风险管理系统的实现正确性
Protocol: v4.4
"""

import os
import sys
import logging
from pathlib import Path
from decimal import Decimal

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
    {"id": "RULE_135_003", "name": "数据模型实例化验证", "severity": "CRITICAL"},
    {"id": "RULE_135_004", "name": "配置定义验证", "severity": "HIGH"},
    {"id": "RULE_135_005", "name": "熔断器功能验证", "severity": "HIGH"},
    {"id": "RULE_135_006", "name": "回撤监控功能验证", "severity": "HIGH"},
    {"id": "RULE_135_007", "name": "敞口监控功能验证", "severity": "HIGH"},
    {"id": "RULE_135_008", "name": "YAML配置验证", "severity": "HIGH"},
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
        self.audit_models_instantiation()
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
            
            # 验证主要导出
            from src.risk import (
                RiskLevel, CircuitState, RiskAction,
                RiskContext, RiskDecision,
                CircuitBreaker, DrawdownMonitor, ExposureMonitor
            )
            
            logger.info(f"✅ {rule_id}: 风险模块所有组件成功导入")
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
            
            # 验证RiskLevel (4个值)
            risk_levels = [RiskLevel.NORMAL, RiskLevel.WARNING, RiskLevel.CRITICAL, RiskLevel.HALT]
            assert len(risk_levels) == 4
            
            # 验证CircuitState (3个值)
            circuit_states = [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
            assert len(circuit_states) == 3
            
            # 验证RiskAction (4个值)
            risk_actions = [RiskAction.ALLOW, RiskAction.REJECT, RiskAction.REDUCE_ONLY, RiskAction.FORCE_CLOSE]
            assert len(risk_actions) == 4
            
            # 验证TrackType (3个轨道)
            track_types = {t.value for t in TrackType}
            assert 'EUR' in track_types and 'BTC' in track_types and 'GBP' in track_types
            
            logger.info(f"✅ {rule_id}: 枚举类型验证通过 (RiskLevel: 4, CircuitState: 3, RiskAction: 4, TrackType: 3)")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"枚举类型验证失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_models_instantiation(self):
        """检查数据模型实例化"""
        rule_id = "RULE_135_003"
        try:
            from src.risk.models import RiskContext, PositionInfo, RiskDecision, RiskEvent, SymbolRiskState, AccountRiskState
            from src.risk.enums import RiskLevel, RiskAction, TrackType, OrderSide
            
            # 测试RiskContext实例化
            ctx = RiskContext(
                symbol="EURUSD.s",
                track=TrackType.EUR,
                order_side=OrderSide.BUY,
                order_size=Decimal("0.01"),
                order_price=Decimal("1.1000"),
                account_equity=Decimal("10000"),
                available_margin=Decimal("8000")
            )
            assert ctx.symbol == "EURUSD.s"
            assert ctx.order_value == Decimal("0.011")
            
            # 测试RiskDecision实例化
            decision = RiskDecision(
                action=RiskAction.ALLOW,
                level=RiskLevel.NORMAL,
                reason="Test decision"
            )
            assert decision.is_allowed == True
            assert 'action' in decision.to_dict()
            
            # 测试AccountRiskState实例化
            state = AccountRiskState()
            assert state.daily_total_pnl == Decimal("0")
            assert state.drawdown_percentage >= 0
            
            logger.info(f"✅ {rule_id}: 数据模型实例化验证通过")
            logger.info(f"   - RiskContext: ✅")
            logger.info(f"   - RiskDecision: ✅")
            logger.info(f"   - AccountRiskState: ✅")
            self.passed_rules.append(rule_id)
        except Exception as e:
            msg = f"数据模型实例化失败: {str(e)}"
            self.issues.append((rule_id, msg))
            logger.error(f"❌ {rule_id}: {msg}")

    def audit_config(self):
        """检查配置定义"""
        rule_id = "RULE_135_004"
        try:
            from src.risk.config import CircuitBreakerConfig, DrawdownConfig, ExposureConfig, RiskConfig
            
            # 验证配置实例化及默认值
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
            assert risk_config.enabled == True
            
            logger.info(f"✅ {rule_id}: 配置定义验证通过")
            logger.info(f"   - CircuitBreakerConfig: max_losses={cb_config.max_consecutive_losses}")
            logger.info(f"   - DrawdownConfig: halt_threshold={dd_config.halt_threshold}%")
            logger.info(f"   - ExposureConfig: max_positions={exp_config.max_positions}")
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
            from decimal import Decimal
            
            # 创建熔断器实例
            cb_config = CircuitBreakerConfig()
            cb = CircuitBreaker("EURUSD.s", cb_config)
            
            # 验证初始状态
            assert cb.state.circuit_state == CircuitState.CLOSED
            assert cb.state.consecutive_losses == 0
            
            # 模拟记录亏损交易
            cb.record_trade_result(Decimal("-100"), False)
            assert cb.state.consecutive_losses == 1
            
            # 获取状态
            status = cb.get_status()
            assert 'symbol' in status
            assert status['symbol'] == "EURUSD.s"
            
            logger.info(f"✅ {rule_id}: 熔断器验证通过")
            logger.info(f"   - 初始状态: CLOSED ✅")
            logger.info(f"   - 记录交易: ✅")
            logger.info(f"   - 状态查询: ✅")
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
            from decimal import Decimal
            
            # 创建回撤监控器实例
            dd_config = DrawdownConfig()
            dm = DrawdownMonitor(dd_config)
            
            # 验证初始状态
            assert dm.state.risk_level == RiskLevel.NORMAL
            assert dm.state.current_drawdown == 0
            
            # 重置每日统计
            dm.reset_daily(Decimal("10000"))
            assert dm.state.daily_starting_equity == Decimal("10000")
            
            # 获取状态
            status = dm.get_status()
            assert 'drawdown_percentage' in status
            
            logger.info(f"✅ {rule_id}: 回撤监控验证通过")
            logger.info(f"   - 初始风险级别: NORMAL ✅")
            logger.info(f"   - 每日重置: ✅")
            logger.info(f"   - 状态查询: ✅")
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
            
            # 获取状态
            status = em.get_status()
            assert 'max_total_exposure' in status
            assert 'max_positions' in status
            assert status['max_positions'] > 0
            
            logger.info(f"✅ {rule_id}: 敞口监控验证通过")
            logger.info(f"   - 最大总敞口: {status['max_total_exposure']}% ✅")
            logger.info(f"   - 最大持仓数: {status['max_positions']} ✅")
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
            
            # 验证每个轨道的配置完整性
            for track in ['EUR', 'BTC', 'GBP']:
                track_cfg = track_limits[track]
                assert 'max_exposure_pct' in track_cfg
                assert 'max_positions' in track_cfg
                assert 'max_single_position_pct' in track_cfg
                assert 'max_daily_loss_pct' in track_cfg
            
            logger.info(f"✅ {rule_id}: YAML配置验证通过")
            logger.info(f"   - Circuit Breaker: ✅")
            logger.info(f"   - Drawdown Monitor: ✅")
            logger.info(f"   - Exposure Monitor: ✅")
            logger.info(f"   - EUR Track: max_exposure={track_limits['EUR']['max_exposure_pct']}% ✅")
            logger.info(f"   - BTC Track: max_exposure={track_limits['BTC']['max_exposure_pct']}% ✅")
            logger.info(f"   - GBP Track: max_exposure={track_limits['GBP']['max_exposure_pct']}% ✅")
            
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
