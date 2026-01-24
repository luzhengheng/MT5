#!/usr/bin/env python3
"""
Risk Modules Deployment Script
RFC-136: Risk Modules 部署与熔断器功能验证

将 Task #135 产出的 Risk Modules 部署至 INF 节点
Protocol v4.4 compliant
"""

import os
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 部署配置
INF_NODE_IP = "172.19.141.250"
INF_NODE_USER = "root"
INF_BASE_PATH = "/opt/mt5-crs"

PROJECT_ROOT = Path(__file__).parent.parent.parent


class DeploymentManager:
    """风险模块部署管理器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.src_path = self.project_root / "src"
        self.config_path = self.project_root / "config"
        self.deployment_log = []

    def log_action(self, action: str, status: str, details: str = ""):
        """记录部署动作"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {action}: {status}"
        if details:
            log_entry += f" - {details}"
        self.deployment_log.append(log_entry)
        logger.info(log_entry)

    def verify_local_artifacts(self) -> bool:
        """验证本地风险模块文件"""
        logger.info("=== 验证本地风险模块文件 ===")

        required_files = [
            self.src_path / "risk" / "__init__.py",
            self.src_path / "risk" / "enums.py",
            self.src_path / "risk" / "models.py",
            self.src_path / "risk" / "config.py",
            self.src_path / "risk" / "circuit_breaker.py",
            self.src_path / "risk" / "drawdown_monitor.py",
            self.src_path / "risk" / "exposure_monitor.py",
            self.src_path / "risk" / "risk_manager.py",
            self.src_path / "risk" / "events.py",
            self.config_path / "trading_config.yaml",
        ]

        all_exist = True
        for file_path in required_files:
            if file_path.exists():
                size = file_path.stat().st_size
                logger.info(f"✅ {file_path.name} ({size} bytes)")
                self.log_action("VERIFY_FILE", "OK", f"{file_path.name}")
            else:
                logger.error(f"❌ {file_path} 不存在")
                self.log_action("VERIFY_FILE", "MISSING", str(file_path))
                all_exist = False

        return all_exist

    def deploy_to_inf(self) -> bool:
        """使用 rsync 将代码同步到 INF 节点"""
        logger.info(f"\n=== 部署到 INF 节点 ({INF_NODE_IP}) ===")

        ssh_destination = f"{INF_NODE_USER}@{INF_NODE_IP}:{INF_BASE_PATH}"

        # 部署 src/ 目录（包括 risk 模块）
        logger.info("同步 src/ 目录...")
        rsync_src_cmd = [
            "rsync", "-avz", "--delete",
            str(self.src_path) + "/",
            f"{ssh_destination}/src/",
            "--exclude=__pycache__",
            "--exclude=.pytest_cache",
        ]

        try:
            result = subprocess.run(rsync_src_cmd, check=True, capture_output=True, text=True)
            logger.info(f"✅ src/ 同步成功")
            self.log_action("DEPLOY_SRC", "OK", "rsync completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ src/ 同步失败: {e.stderr}")
            self.log_action("DEPLOY_SRC", "FAILED", str(e))
            return False

        # 部署 config/ 目录
        logger.info("同步 config/ 目录...")
        rsync_config_cmd = [
            "rsync", "-avz",
            str(self.config_path) + "/",
            f"{ssh_destination}/config/",
        ]

        try:
            result = subprocess.run(rsync_config_cmd, check=True, capture_output=True, text=True)
            logger.info(f"✅ config/ 同步成功")
            self.log_action("DEPLOY_CONFIG", "OK", "rsync completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ config/ 同步失败: {e.stderr}")
            self.log_action("DEPLOY_CONFIG", "FAILED", str(e))
            return False

        return True

    def verify_deployment_on_inf(self) -> bool:
        """在 INF 节点上验证部署"""
        logger.info(f"\n=== 验证 INF 节点上的部署 ===")

        ssh_cmd = [
            "ssh", f"{INF_NODE_USER}@{INF_NODE_IP}",
            f"python3 -c 'import sys; sys.path.insert(0, \"{INF_BASE_PATH}\"); "
            f"from src.risk import RiskManager, RiskConfig; "
            f"config = RiskConfig.from_yaml(\"{INF_BASE_PATH}/config/trading_config.yaml\"); "
            f"manager = RiskManager(config); "
            f"print(\"✅ Risk modules imported successfully\")'"
        ]

        try:
            result = subprocess.run(ssh_cmd, check=True, capture_output=True, text=True, timeout=30)
            logger.info(f"✅ 远程导入验证成功")
            logger.info(result.stdout)
            self.log_action("VERIFY_REMOTE", "OK", "Import test passed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 远程导入验证失败: {e.stderr}")
            self.log_action("VERIFY_REMOTE", "FAILED", e.stderr)
            return False
        except subprocess.TimeoutExpired:
            logger.error("❌ 远程验证超时")
            self.log_action("VERIFY_REMOTE", "TIMEOUT", "SSH command timeout")
            return False

    def generate_deployment_report(self):
        """生成部署报告"""
        logger.info(f"\n=== 部署报告 ===")
        report_path = self.project_root / "TASK_136_DEPLOYMENT_REPORT.log"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Task #136 部署报告\n")
            f.write("="*80 + "\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write(f"目标节点: {INF_NODE_IP}\n")
            f.write(f"部署路径: {INF_BASE_PATH}\n")
            f.write("\n部署日志:\n")
            f.write("-"*80 + "\n")
            for log_entry in self.deployment_log:
                f.write(log_entry + "\n")

        logger.info(f"✅ 部署报告已保存: {report_path}")

    def run(self) -> bool:
        """执行完整的部署流程"""
        logger.info("🚀 开始 Risk Modules 部署流程")
        logger.info(f"项目根目录: {self.project_root}")
        logger.info(f"目标节点: {INF_NODE_IP}")

        # 步骤 1: 验证本地文件
        if not self.verify_local_artifacts():
            logger.error("❌ 本地文件验证失败")
            self.generate_deployment_report()
            return False

        # 步骤 2: 部署到 INF
        if not self.deploy_to_inf():
            logger.error("❌ 部署到 INF 失败")
            self.generate_deployment_report()
            return False

        # 步骤 3: 验证远程部署
        if not self.verify_deployment_on_inf():
            logger.error("❌ 远程部署验证失败")
            self.generate_deployment_report()
            return False

        logger.info("\n" + "="*80)
        logger.info("✅ 部署流程完成!")
        logger.info("="*80)

        self.generate_deployment_report()
        return True


def main():
    """主函数"""
    manager = DeploymentManager()
    success = manager.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
