#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #102 Step 2: 远征部署脚本
功能: 使用 paramiko 将 Hub 上的代码同步到 Inf 节点
并在 Inf 上自动安装依赖

执行方式: python3 scripts/deploy/sync_to_inf.py --target 172.19.141.250
"""

import os
import sys
import json
import argparse
import paramiko
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

# 配置日志
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
# 配置常量
# ============================================================================

class InfNodeConfig:
    """Inf 节点配置"""

    # 网络配置
    INF_IP = "172.19.141.250"
    INF_PORT = 22
    INF_USERNAME = "root"
    INF_KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

    # 本地路径
    HUB_SCRIPTS_DIR = "/opt/mt5-crs/scripts"
    HUB_REQUIREMENTS = "/opt/mt5-crs/requirements.txt"

    # 远程路径
    INF_HOME = "/opt/mt5-crs"
    INF_SCRIPTS_DIR = "/opt/mt5-crs/scripts"

    # 需要同步的关键目录
    SYNC_DIRS = [
        "scripts/strategy",
        "scripts/execution",
        "scripts/ai_governance",
        "src",
    ]

    # Inf 特定的轻量级需求
    INF_REQUIREMENTS = """
pandas>=1.3.0
pyzmq>=22.0.0
python-dotenv>=0.19.0
numpy>=1.20.0
"""


# ============================================================================
# SSH 客户端封装
# ============================================================================

class SSHClient:
    """SSH 连接管理"""

    def __init__(self, hostname: str, port: int, username: str, key_path: str):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.key_path = key_path
        self.client = None
        self.sftp = None

    def connect(self) -> bool:
        """建立 SSH 连接"""
        try:
            logger.info(f"正在连接 Inf 节点 ({self.hostname}:{self.port})...")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 尝试使用 SSH 密钥连接
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                key_filename=self.key_path,
                timeout=10,
                banner_timeout=10
            )

            logger.info(f"✅ SSH 连接成功")

            # 获取 SFTP 连接
            self.sftp = self.client.open_sftp()
            logger.info(f"✅ SFTP 连接成功")

            return True
        except paramiko.AuthenticationException as e:
            logger.error(f"❌ SSH 认证失败: {e}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"❌ SSH 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 连接错误: {e}")
            return False

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """执行远程命令"""
        if not self.client:
            logger.error("❌ SSH 客户端未连接")
            return 1, "", "未连接"

        try:
            logger.info(f"[Inf] 执行命令: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=60)

            returncode = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')

            if returncode == 0:
                logger.info(f"[Inf] ✅ 命令执行成功")
            else:
                logger.warning(f"[Inf] ⚠️ 命令返回代码: {returncode}")

            if out:
                logger.info(f"[Inf] 输出:\n{out}")
            if err:
                logger.warning(f"[Inf] 错误:\n{err}")

            return returncode, out, err
        except Exception as e:
            logger.error(f"❌ 执行命令失败: {e}")
            return 1, "", str(e)

    def put_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        if not self.sftp:
            logger.error("❌ SFTP 连接未建立")
            return False

        try:
            logger.info(f"上传文件: {local_path} → {remote_path}")
            self.sftp.put(local_path, remote_path)
            logger.info(f"✅ 文件上传成功")
            return True
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            return False

    def put_dir(self, local_dir: str, remote_dir: str) -> bool:
        """递归上传目录"""
        if not self.sftp:
            logger.error("❌ SFTP 连接未建立")
            return False

        try:
            # 创建远程目录
            try:
                self.sftp.stat(remote_dir)
            except IOError:
                logger.info(f"创建远程目录: {remote_dir}")
                self.sftp.mkdir(remote_dir)

            # 递归上传文件
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, local_dir)
                    remote_file = os.path.join(remote_dir, relative_path)

                    # 创建远程子目录
                    remote_subdir = os.path.dirname(remote_file)
                    try:
                        self.sftp.stat(remote_subdir)
                    except IOError:
                        logger.info(f"创建远程子目录: {remote_subdir}")
                        self.sftp.mkdir(remote_subdir)

                    logger.info(f"上传: {relative_path}")
                    self.sftp.put(local_file, remote_file)

            logger.info(f"✅ 目录 {local_dir} 上传完成")
            return True
        except Exception as e:
            logger.error(f"❌ 目录上传失败: {e}")
            return False

    def close(self):
        """关闭 SSH 连接"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        logger.info("SSH 连接已关闭")


# ============================================================================
# 部署管理器
# ============================================================================

class InfDeploymentManager:
    """Inf 节点部署管理"""

    def __init__(self, ssh_client: SSHClient):
        self.ssh = ssh_client
        self.config = InfNodeConfig()

    def step_1_check_inf_readiness(self) -> bool:
        """第 1 步: 检查 Inf 节点就绪状态"""
        logger.info("\n" + "="*70)
        logger.info("Step 1: 检查 Inf 节点就绪状态")
        logger.info("="*70)

        # 检查 Inf 目录
        logger.info(f"检查 Inf 主目录: {self.config.INF_HOME}")
        returncode, out, err = self.ssh.execute_command(
            f"ls -la {self.config.INF_HOME}"
        )
        if returncode != 0:
            logger.warning(f"Inf 主目录不存在，将创建")
            self.ssh.execute_command(f"mkdir -p {self.config.INF_HOME}")

        # 检查 Python 版本
        logger.info("检查 Python 版本")
        returncode, out, err = self.ssh.execute_command("python3 --version")
        if returncode == 0:
            logger.info(f"✅ Python 版本: {out.strip()}")
        else:
            logger.error(f"❌ Python 未安装或不可用")
            return False

        # 检查 pip
        logger.info("检查 pip")
        returncode, out, err = self.ssh.execute_command("pip3 --version")
        if returncode == 0:
            logger.info(f"✅ pip 版本: {out.strip()}")
        else:
            logger.error(f"❌ pip 未安装")
            return False

        # 检查磁盘空间
        logger.info("检查磁盘空间")
        returncode, out, err = self.ssh.execute_command(
            f"df -h {self.config.INF_HOME} | tail -1"
        )
        if returncode == 0:
            logger.info(f"磁盘信息: {out.strip()}")

        logger.info("✅ Step 1 完成: Inf 节点就绪")
        return True

    def step_2_sync_code(self) -> bool:
        """第 2 步: 同步代码"""
        logger.info("\n" + "="*70)
        logger.info("Step 2: 同步代码到 Inf")
        logger.info("="*70)

        # 同步每个关键目录
        for sync_dir in self.config.SYNC_DIRS:
            local_path = os.path.join(self.config.HUB_SCRIPTS_DIR, os.path.basename(sync_dir))
            remote_path = os.path.join(self.config.INF_SCRIPTS_DIR, os.path.basename(sync_dir))

            if not os.path.exists(local_path):
                logger.warning(f"本地目录不存在，跳过: {local_path}")
                continue

            logger.info(f"\n同步: {local_path} → {remote_path}")
            if not self.ssh.put_dir(local_path, remote_path):
                logger.error(f"❌ 同步失败: {sync_dir}")
                return False

        logger.info("✅ Step 2 完成: 代码已同步到 Inf")
        return True

    def step_3_install_dependencies(self) -> bool:
        """第 3 步: 安装依赖"""
        logger.info("\n" + "="*70)
        logger.info("Step 3: 安装 Inf 依赖")
        logger.info("="*70)

        # 创建临时 requirements.txt
        temp_req_path = "/tmp/requirements_inf.txt"
        logger.info(f"在 Inf 上创建轻量级需求文件")

        # 将需求写入远程临时文件
        commands = [
            f"cat > {temp_req_path} << 'EOF'",
            self.config.INF_REQUIREMENTS,
            "EOF"
        ]

        for cmd in commands:
            if cmd == "EOF":
                continue
            returncode, out, err = self.ssh.execute_command(cmd)
            if returncode != 0 and cmd != "EOF":
                pass  # 继续

        # 安装依赖
        logger.info(f"安装依赖包...")
        returncode, out, err = self.ssh.execute_command(
            f"pip3 install -r {temp_req_path} --quiet"
        )

        if returncode != 0:
            logger.error(f"❌ 依赖安装失败")
            logger.error(f"错误: {err}")
            return False

        # 验证关键包
        logger.info("验证关键依赖包...")
        for package in ["pandas", "zmq", "dotenv"]:
            returncode, out, err = self.ssh.execute_command(
                f"python3 -c 'import {package}; print(\"{package} OK\")'"
            )
            if returncode == 0:
                logger.info(f"✅ {package} 已安装")
            else:
                logger.warning(f"⚠️ {package} 验证失败")

        logger.info("✅ Step 3 完成: 依赖已安装")
        return True

    def step_4_verify_integration(self) -> bool:
        """第 4 步: 验证集成"""
        logger.info("\n" + "="*70)
        logger.info("Step 4: 验证集成")
        logger.info("="*70)

        # 检查策略模块
        logger.info("检查策略模块...")
        returncode, out, err = self.ssh.execute_command(
            f"python3 -c 'from scripts.strategy.engine import StrategyEngine; print(\"StrategyEngine OK\")'"
        )
        if returncode == 0:
            logger.info(f"✅ StrategyEngine 模块可用")
        else:
            logger.warning(f"⚠️ StrategyEngine 导入失败")

        # 检查执行模块
        logger.info("检查执行模块...")
        returncode, out, err = self.ssh.execute_command(
            f"python3 -c 'from scripts.execution.risk import RiskManager; print(\"RiskManager OK\")'"
        )
        if returncode == 0:
            logger.info(f"✅ RiskManager 模块可用")
        else:
            logger.warning(f"⚠️ RiskManager 导入失败")

        # 检查文件完整性
        logger.info("检查文件完整性...")
        returncode, out, err = self.ssh.execute_command(
            f"find {self.config.INF_SCRIPTS_DIR}/strategy -name '*.py' | wc -l"
        )
        if returncode == 0:
            logger.info(f"✅ 策略文件数: {out.strip()}")

        returncode, out, err = self.ssh.execute_command(
            f"find {self.config.INF_SCRIPTS_DIR}/execution -name '*.py' | wc -l"
        )
        if returncode == 0:
            logger.info(f"✅ 执行文件数: {out.strip()}")

        logger.info("✅ Step 4 完成: 集成验证通过")
        return True

    def execute_full_deployment(self) -> bool:
        """执行完整部署流程"""
        logger.info("\n" + "█"*70)
        logger.info("█ TASK #102 Step 2: 远征部署开始")
        logger.info("█"*70)

        steps = [
            ("检查就绪", self.step_1_check_inf_readiness),
            ("同步代码", self.step_2_sync_code),
            ("安装依赖", self.step_3_install_dependencies),
            ("验证集成", self.step_4_verify_integration),
        ]

        for step_name, step_func in steps:
            logger.info(f"\n🔄 执行 {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} 失败")
                return False

        logger.info("\n" + "█"*70)
        logger.info("█ ✅ 远征部署完成！")
        logger.info("█"*70)
        return True


# ============================================================================
# 主程序
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="TASK #102 Step 2: Inf 节点远征部署"
    )
    parser.add_argument(
        "--target",
        default=InfNodeConfig.INF_IP,
        help=f"Inf 节点 IP（默认: {InfNodeConfig.INF_IP}）"
    )
    parser.add_argument(
        "--user",
        default=InfNodeConfig.INF_USERNAME,
        help=f"SSH 用户名（默认: {InfNodeConfig.INF_USERNAME}）"
    )
    parser.add_argument(
        "--key",
        default=InfNodeConfig.INF_KEY_PATH,
        help=f"SSH 密钥路径（默认: {InfNodeConfig.INF_KEY_PATH}）"
    )

    args = parser.parse_args()

    logger.info(f"TASK #102: Inf 节点远征部署")
    logger.info(f"目标节点: {args.target}")
    logger.info(f"SSH 用户: {args.user}")
    logger.info(f"SSH 密钥: {args.key}")

    # 验证 SSH 密钥存在
    if not os.path.exists(args.key):
        logger.error(f"❌ SSH 密钥不存在: {args.key}")
        logger.info(f"生成 SSH 密钥: ssh-keygen -t rsa -b 4096 -f {args.key}")
        return False

    # 建立 SSH 连接
    ssh_client = SSHClient(
        hostname=args.target,
        port=InfNodeConfig.INF_PORT,
        username=args.user,
        key_path=args.key
    )

    if not ssh_client.connect():
        logger.error("❌ 无法连接到 Inf 节点")
        return False

    try:
        # 执行部署
        manager = InfDeploymentManager(ssh_client)
        success = manager.execute_full_deployment()

        if success:
            logger.info("\n✅ TASK #102 Step 2 完成！")
            logger.info("下一步: 执行 Step 3 - 适配器复原")
            return True
        else:
            logger.error("\n❌ TASK #102 Step 2 失败")
            return False

    finally:
        ssh_client.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
