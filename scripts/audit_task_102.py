#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #102 Step 4: 物理验尸（链路测试）
功能: 在 Hub 上运行，远程指挥 Inf 与 GTW 进行连通性测试
验证完整的 Hub → Inf → GTW 数据链路

执行方式: python3 scripts/audit_task_102.py --target inf --action ping_gtw
"""

import os
import sys
import json
import argparse
import logging
import paramiko
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

# ============================================================================
# 日志配置
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('VERIFY_LOG.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 配置
# ============================================================================

class AuditConfig:
    """审计配置"""

    INF_IP = "172.19.141.250"
    INF_PORT = 22
    INF_USERNAME = "root"
    INF_KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

    GTW_IP = "172.19.141.255"
    GTW_PORT = 5555

    # Inf 上的脚本路径
    INF_ADAPTER_PATH = "/opt/mt5-crs/scripts/execution/adapter.py"


# ============================================================================
# SSH 远程执行
# ============================================================================

class RemoteExecutor:
    """远程命令执行器"""

    def __init__(self, hostname: str, port: int, username: str, key_path: str):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.key_path = key_path
        self.client = None

    def connect(self) -> bool:
        """建立 SSH 连接"""
        try:
            logger.info(f"[Hub] 正在连接 {self.hostname}:{self.port}...")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                key_filename=self.key_path,
                timeout=10
            )
            logger.info(f"[Hub] ✅ 连接 {self.hostname} 成功")
            return True
        except Exception as e:
            logger.error(f"[Hub] ❌ 连接失败: {e}")
            return False

    def execute(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行远程命令"""
        if not self.client:
            logger.error("[Hub] ❌ 未连接")
            return 1, "", "未连接"

        try:
            logger.info(f"[Hub] 执行远程命令: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            returncode = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')

            logger.info(f"[Inf] ← 返回代码: {returncode}")
            if out:
                logger.info(f"[Inf] ← 输出:\n{out}")
            if err:
                logger.warning(f"[Inf] ← 错误:\n{err}")

            return returncode, out, err
        except Exception as e:
            logger.error(f"[Hub] ❌ 执行失败: {e}")
            return 1, "", str(e)

    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
        logger.info("[Hub] SSH 连接已关闭")


# ============================================================================
# 链路测试
# ============================================================================

class LinkAudit:
    """链路审计"""

    def __init__(self, executor: RemoteExecutor):
        self.executor = executor
        self.results = []

    def log_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.results.append(result)

        status_icon = "✅" if success else "❌"
        logger.info(f"{status_icon} [{test_name}] {message}")

    def test_inf_alive(self) -> bool:
        """测试 1: Inf 节点存活检测"""
        logger.info("\n" + "="*70)
        logger.info("测试 1: Inf 节点存活检测")
        logger.info("="*70)

        returncode, out, err = self.executor.execute("echo '✅ Inf alive' && pwd")

        success = returncode == 0
        message = f"Inf 工作目录: {out.strip()}" if out else "未知"
        self.log_result("Inf 存活", success, message)
        return success

    def test_inf_python(self) -> bool:
        """测试 2: Python 环境检测"""
        logger.info("\n" + "="*70)
        logger.info("测试 2: Python 环境检测")
        logger.info("="*70)

        returncode, out, err = self.executor.execute("python3 --version")

        success = returncode == 0
        message = out.strip() if out else "Python 未安装"
        self.log_result("Python 环境", success, message)
        return success

    def test_inf_pyzmq(self) -> bool:
        """测试 3: ZMQ 库检测"""
        logger.info("\n" + "="*70)
        logger.info("测试 3: ZMQ 库检测")
        logger.info("="*70)

        returncode, out, err = self.executor.execute(
            "python3 -c 'import zmq; print(f\"ZMQ version: {zmq.zmq_version()}\")'"
        )

        success = returncode == 0
        message = out.strip() if out else "ZMQ 未安装"
        self.log_result("ZMQ 库", success, message)
        return success

    def test_inf_adapter_exists(self) -> bool:
        """测试 4: GTW 适配器检测"""
        logger.info("\n" + "="*70)
        logger.info("测试 4: GTW 适配器文件检测")
        logger.info("="*70)

        returncode, out, err = self.executor.execute(
            f"test -f {AuditConfig.INF_ADAPTER_PATH} && echo 'EXISTS' || echo 'MISSING'"
        )

        success = "EXISTS" in out
        message = f"适配器: {AuditConfig.INF_ADAPTER_PATH}"
        self.log_result("适配器存在", success, message)
        return success

    def test_gtw_network_reachable(self) -> bool:
        """测试 5: GTW 网络可达性 (从 Inf)"""
        logger.info("\n" + "="*70)
        logger.info("测试 5: GTW 网络可达性")
        logger.info("="*70)

        returncode, out, err = self.executor.execute(
            f"ping -c 1 {AuditConfig.GTW_IP} 2>&1 | grep -q 'bytes from' && echo 'OK' || echo 'FAIL'"
        )

        success = "OK" in out or returncode == 0
        message = f"GTW IP {AuditConfig.GTW_IP} {'可达' if success else '不可达'}"
        self.log_result("GTW 可达性", success, message)
        return success

    def test_gtw_port_open(self) -> bool:
        """测试 6: GTW ZMQ 端口检测 (从 Inf)"""
        logger.info("\n" + "="*70)
        logger.info("测试 6: GTW ZMQ 端口检测")
        logger.info("="*70)

        returncode, out, err = self.executor.execute(
            f"nc -zv {AuditConfig.GTW_IP} {AuditConfig.GTW_PORT} 2>&1"
        )

        success = returncode == 0
        message = f"GTW {AuditConfig.GTW_IP}:{AuditConfig.GTW_PORT} {'开放' if success else '关闭'}"
        self.log_result("ZMQ 端口", success, message)
        return success

    def test_gtw_zmq_ping(self) -> bool:
        """测试 7: GTW ZMQ Ping (从 Inf)"""
        logger.info("\n" + "="*70)
        logger.info("测试 7: GTW ZMQ Ping")
        logger.info("="*70)

        # 在 Inf 上运行 adapter.py 的测试
        test_script = f"""
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/mt5-crs')
from scripts.execution.adapter import GTWAdapter

adapter = GTWAdapter()
if adapter.connect():
    success, response = adapter.ping()
    if success:
        print("ZMQ_PING_OK")
        print(json.dumps(response))
    else:
        print("ZMQ_PING_FAIL")
else:
    print("ZMQ_CONNECT_FAIL")
adapter.close()
PYTHON_EOF
"""

        returncode, out, err = self.executor.execute(test_script, timeout=15)

        success = "ZMQ_PING_OK" in out
        if success:
            logger.info(f"[Inf] GTW 响应: {out}")

        message = f"GTW ZMQ {'响应正常' if success else '无响应或连接失败'}"
        self.log_result("ZMQ Ping", success, message)
        return success

    def test_inf_strategy_module(self) -> bool:
        """测试 8: 策略模块导入 (从 Inf)"""
        logger.info("\n" + "="*70)
        logger.info("测试 8: 策略模块导入")
        logger.info("="*70)

        returncode, out, err = self.executor.execute(
            "python3 -c 'import sys; sys.path.insert(0, \\\"/opt/mt5-crs\\\"); "
            "from scripts.strategy.engine import StrategyEngine; print(\\\"OK\\\")'"
        )

        success = "OK" in out and returncode == 0
        message = "策略模块 StrategyEngine 可导入"
        self.log_result("策略模块", success, message)
        return success

    def test_inf_execution_module(self) -> bool:
        """测试 9: 执行模块导入 (从 Inf)"""
        logger.info("\n" + "="*70)
        logger.info("测试 9: 执行模块导入")
        logger.info("="*70)

        returncode, out, err = self.executor.execute(
            "python3 -c 'import sys; sys.path.insert(0, \\\"/opt/mt5-crs\\\"); "
            "from scripts.execution.risk import RiskManager; print(\\\"OK\\\")'"
        )

        success = "OK" in out and returncode == 0
        message = "执行模块 RiskManager 可导入"
        self.log_result("执行模块", success, message)
        return success

    def run_full_audit(self) -> bool:
        """执行完整审计"""
        logger.info("\n" + "█"*70)
        logger.info("█ TASK #102 Step 4: 物理验尸 (链路测试)")
        logger.info("█"*70)

        tests = [
            ("Inf 存活", self.test_inf_alive),
            ("Python", self.test_inf_python),
            ("ZMQ", self.test_inf_pyzmq),
            ("适配器", self.test_inf_adapter_exists),
            ("网络", self.test_gtw_network_reachable),
            ("端口", self.test_gtw_port_open),
            ("Ping", self.test_gtw_zmq_ping),
            ("策略", self.test_inf_strategy_module),
            ("执行", self.test_inf_execution_module),
        ]

        passed = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                logger.error(f"❌ 测试异常: {e}")
                self.log_result(test_name, False, str(e))

        # 生成报告
        logger.info("\n" + "="*70)
        logger.info("审计报告总结")
        logger.info("="*70)

        total = len(tests)
        logger.info(f"总测试数: {total}")
        logger.info(f"通过数: {passed}")
        logger.info(f"失败数: {total - passed}")
        logger.info(f"通过率: {passed/total*100:.1f}%")

        # 保存报告
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "task": "TASK #102 Step 4",
            "inf_node": AuditConfig.INF_IP,
            "gtw_node": AuditConfig.GTW_IP,
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed/total*100,
            "results": self.results
        }

        report_file = "audit_task_102_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"\n✅ 报告已保存: {report_file}")

        logger.info("\n" + "█"*70)
        if passed == total:
            logger.info("█ ✅ 物理验尸完成 - 所有测试通过！")
        else:
            logger.info(f"█ ⚠️ 物理验尸完成 - 部分测试失败 ({total-passed}/{total})")
        logger.info("█"*70)

        return passed == total


# ============================================================================
# 主程序
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TASK #102 Step 4: 物理验尸（链路测试）"
    )
    parser.add_argument(
        "--target",
        default=AuditConfig.INF_IP,
        help=f"目标节点 IP（默认: {AuditConfig.INF_IP}）"
    )
    parser.add_argument(
        "--user",
        default=AuditConfig.INF_USERNAME,
        help=f"SSH 用户名（默认: {AuditConfig.INF_USERNAME}）"
    )
    parser.add_argument(
        "--key",
        default=AuditConfig.INF_KEY_PATH,
        help=f"SSH 密钥路径（默认: {AuditConfig.INF_KEY_PATH}）"
    )
    parser.add_argument(
        "--action",
        choices=["ping_gtw", "full_audit"],
        default="full_audit",
        help="执行的测试（默认: full_audit）"
    )

    args = parser.parse_args()

    logger.info(f"TASK #102 Step 4: 物理验尸")
    logger.info(f"目标节点: {args.target}")

    # 建立连接
    executor = RemoteExecutor(
        hostname=args.target,
        port=AuditConfig.INF_PORT,
        username=args.user,
        key_path=args.key
    )

    if not executor.connect():
        logger.error("❌ 无法连接到 Inf 节点")
        return False

    try:
        # 执行审计
        audit = LinkAudit(executor)

        if args.action == "full_audit":
            success = audit.run_full_audit()
        elif args.action == "ping_gtw":
            success = audit.test_gtw_zmq_ping()

        return success
    finally:
        executor.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
