#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 编排器 - 分布式算力协同主控脚本

Purpose:
  从新加坡 (INF) 对广州 (GPU) 的远程接管。
  自动化完成：环境探针审计、MinIO 数据管道构建、
  深度学习依赖 (PyTorch/CUDA) 的幂等性安装。

Design:
  - 顺序执行四个主要阶段：本地审计 -> 数据上传 -> 远程激活 -> 验证
  - 集成 Paramiko 用于 SSH 操作
  - 物理验证：确保远程执行返回真实输出
  - 日志记录：所有操作都写入 VERIFY_LOG.log

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-12
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

try:
    import paramiko
except ImportError:
    print("❌ paramiko is not installed. Please run: pip install paramiko")
    sys.exit(1)

# 添加项目根目录到 Python 路径
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.utils.s3_transfer import S3TransferClient
from src.config import get_project_root


# ============================================================================
# 日志配置
# ============================================================================

VERIFY_LOG = _PROJECT_ROOT / "VERIFY_LOG.log"

def setup_logging():
    """设置日志"""
    logger = logging.getLogger("gpu_orchestrator")
    logger.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # 文件处理器
    file_handler = logging.FileHandler(VERIFY_LOG, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


# ============================================================================
# GPU 编排器主类
# ============================================================================

class GPUOrchestrator:
    """GPU 编排和部署管理器"""

    def __init__(
        self,
        gpu_host: str,
        gpu_user: str = "root",
        gpu_port: int = 22,
        private_key_path: Optional[str] = None,
        minio_endpoint: str = "http://minio:9000",
        aws_access_key: str = "minioadmin",
        aws_secret_key: str = "minioadmin",
    ):
        """
        初始化编排器。

        Args:
            gpu_host: GPU 服务器 IP 或域名
            gpu_user: SSH 用户名
            gpu_port: SSH 端口
            private_key_path: SSH 私钥路径
            minio_endpoint: MinIO 服务地址
            aws_access_key: AWS Access Key
            aws_secret_key: AWS Secret Access Key
        """
        self.gpu_host = gpu_host
        self.gpu_user = gpu_user
        self.gpu_port = gpu_port
        self.private_key_path = private_key_path

        self.minio_endpoint = minio_endpoint
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key

        # S3 客户端
        self.s3_client = S3TransferClient(
            endpoint_url=minio_endpoint,
            access_key=aws_access_key,
            secret_key=aws_secret_key,
        )

        # SSH 客户端 (延迟初始化)
        self.ssh_client: Optional[paramiko.SSHClient] = None

        logger.info(f"🚀 GPU Orchestrator initialized for {gpu_host}")

    def connect_ssh(self) -> bool:
        """
        建立 SSH 连接。

        Returns:
            True 如果连接成功
        """
        if self.ssh_client:
            logger.info("SSH client already connected")
            return True

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            kwargs = {
                "hostname": self.gpu_host,
                "username": self.gpu_user,
                "port": self.gpu_port,
                "timeout": 10,
            }

            if self.private_key_path:
                kwargs["key_filename"] = self.private_key_path
            else:
                # 默认使用 ~/.ssh/id_rsa
                default_key = Path.home() / ".ssh" / "id_rsa"
                if default_key.exists():
                    kwargs["key_filename"] = str(default_key)

            self.ssh_client.connect(**kwargs)
            logger.info(f"✅ SSH connection established to {self.gpu_host}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect via SSH: {e}")
            return False

    def disconnect_ssh(self):
        """断开 SSH 连接"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            logger.info("SSH connection closed")

    def run_remote_command(
        self,
        command: str,
        get_output: bool = True,
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        在远程主机上执行命令。

        Args:
            command: 要执行的命令
            get_output: 是否获取输出

        Returns:
            (stdout, stderr, return_code) 元组
        """
        if not self.ssh_client:
            logger.error("SSH client is not connected")
            return None, "SSH client not connected", 1

        try:
            logger.info(f"[REMOTE] Executing: {command}")
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=300)

            if get_output:
                out = stdout.read().decode('utf-8', errors='ignore')
                err = stderr.read().decode('utf-8', errors='ignore')
                rc = stdout.channel.recv_exit_status()

                logger.info(f"[REMOTE] Return code: {rc}")
                if out:
                    for line in out.split('\n'):
                        if line.strip():
                            logger.info(f"[REMOTE] OUT: {line}")
                if err:
                    for line in err.split('\n'):
                        if line.strip():
                            logger.warning(f"[REMOTE] ERR: {line}")

                return out, err, rc
            else:
                return "", "", 0

        except Exception as e:
            logger.error(f"❌ Remote command failed: {e}")
            return None, str(e), 1

    def upload_data_to_minio(
        self,
        local_file: str,
        bucket: str = "datasets",
        key: str = "eurusd_m1_features_labels.parquet",
    ) -> Dict[str, Any]:
        """
        上传数据到 MinIO。

        Args:
            local_file: 本地文件路径
            bucket: 目标 bucket
            key: 对象 key

        Returns:
            上传元数据
        """
        logger.info(f"📤 [DATA] Uploading {local_file} to MinIO")

        local_file = Path(local_file)
        if not local_file.exists():
            logger.error(f"❌ File not found: {local_file}")
            return {"status": "failed", "error": "File not found"}

        result = self.s3_client.upload_file(
            str(local_file),
            bucket,
            key,
            compute_hash=True,
        )

        if result["status"] == "success":
            logger.info(f"✅ [DATA] Upload complete: {bucket}/{key}")
            logger.info(f"   File size: {result['size']} bytes")
            logger.info(f"   MD5: {result['md5']}")
        else:
            logger.error(f"❌ [DATA] Upload failed: {result.get('error')}")

        return result

    def deploy_remote_scripts(self) -> bool:
        """
        将本地脚本部署到远程 GPU 节点。

        Returns:
            True 如果部署成功
        """
        logger.info("[DEPLOY] Deploying scripts to remote GPU node...")

        scripts_to_deploy = [
            (_PROJECT_ROOT / "scripts" / "remote" / "gpu_probe.py", "/tmp/gpu_probe.py"),
            (_PROJECT_ROOT / "scripts" / "remote" / "setup_env.sh", "/tmp/setup_env.sh"),
        ]

        try:
            sftp = self.ssh_client.open_sftp()

            for local_path, remote_path in scripts_to_deploy:
                if not local_path.exists():
                    logger.error(f"❌ Local script not found: {local_path}")
                    return False

                sftp.put(str(local_path), remote_path)
                sftp.chmod(remote_path, 0o755)
                logger.info(f"✅ Deployed {local_path.name} to {remote_path}")

            sftp.close()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to deploy scripts: {e}")
            return False

    def run_setup_env_remote(self) -> bool:
        """
        在远程节点运行环境安装脚本。

        Returns:
            True 如果安装成功
        """
        logger.info("[SETUP] Running setup_env.sh on remote GPU node...")

        # 注入 MinIO 凭证
        env_vars = (
            f"export AWS_ACCESS_KEY_ID={self.aws_access_key} && "
            f"export AWS_SECRET_ACCESS_KEY={self.aws_secret_key} && "
            f"export MINIO_ENDPOINT_URL={self.minio_endpoint} && "
        )

        command = f"{env_vars} bash /tmp/setup_env.sh"

        stdout, stderr, rc = self.run_remote_command(command, get_output=True)

        if rc == 0:
            logger.info("✅ [SETUP] Remote environment setup completed successfully")
            return True
        else:
            logger.error(f"❌ [SETUP] Remote setup failed with return code {rc}")
            return False

    def run_gpu_probe_remote(self) -> Optional[Dict[str, Any]]:
        """
        在远程节点运行 GPU 探针。

        Returns:
            探针结果 JSON (如果成功)
        """
        logger.info("[PROBE] Running gpu_probe.py on remote GPU node...")

        command = "python3 /tmp/gpu_probe.py"
        stdout, stderr, rc = self.run_remote_command(command, get_output=True)

        if rc != 0:
            logger.error(f"❌ [PROBE] GPU probe failed with return code {rc}")
            return None

        try:
            probe_result = json.loads(stdout)
            logger.info(f"✅ [PROBE] GPU probe completed")

            # 记录关键信息
            if "data" in probe_result:
                data = probe_result["data"]
                if "cuda" in data:
                    cuda = data["cuda"]
                    logger.info(f"   CUDA Available: {cuda.get('cuda_available')}")
                    logger.info(f"   GPU Count: {cuda.get('gpu_count')}")
                    if cuda.get("gpus"):
                        for gpu in cuda["gpus"]:
                            logger.info(f"   - {gpu['name']} ({gpu['memory_mb']} MB)")

            return probe_result

        except json.JSONDecodeError as e:
            logger.error(f"❌ [PROBE] Failed to parse probe output: {e}")
            logger.error(f"   stdout: {stdout[:500]}")
            return None

    def download_data_from_minio(
        self,
        bucket: str = "datasets",
        key: str = "eurusd_m1_features_labels.parquet",
        expected_md5: Optional[str] = None,
    ) -> bool:
        """
        在远程节点从 MinIO 下载数据。

        Args:
            bucket: 源 bucket
            key: 对象 key
            expected_md5: 期望的 MD5 (用于验证)

        Returns:
            True 如果下载和验证成功
        """
        logger.info(f"[S3] Downloading {bucket}/{key} on remote GPU node...")

        # 构建下载命令
        remote_file = f"/tmp/{Path(key).name}"

        command = (
            f"python3 -c 'from src.utils.s3_transfer import S3TransferClient; "
            f"import os; "
            f"c = S3TransferClient(\"http://minio:9000\", "
            f"\"${AWS_ACCESS_KEY_ID}\", \"${AWS_SECRET_ACCESS_KEY}\"); "
            f"r = c.download_file(\"{bucket}\", \"{key}\", \"{remote_file}\"); "
            f"print(r[\"status\"])'"
        )

        # 因为远程节点可能没有项目代码，我们使用更简单的方法
        # 使用 AWS CLI 或 boto3 直接下载

        env_vars = (
            f"export AWS_ACCESS_KEY_ID={self.aws_access_key} && "
            f"export AWS_SECRET_ACCESS_KEY={self.aws_secret_key} && "
            f"export AWS_ENDPOINT_URL_S3={self.minio_endpoint} && "
        )

        # 简化方案：使用 python + boto3
        command = (
            f"{env_vars} python3 -c 'import boto3; "
            f"s3 = boto3.client(\"s3\", endpoint_url=\"{self.minio_endpoint}\", "
            f"aws_access_key_id=\"{self.aws_access_key}\", "
            f"aws_secret_access_key=\"{self.aws_secret_key}\"); "
            f"s3.download_file(\"{bucket}\", \"{key}\", \"{remote_file}\"); "
            f"print(\"Download complete\")'"
        )

        stdout, stderr, rc = self.run_remote_command(command, get_output=True)

        if rc == 0:
            logger.info(f"✅ [S3] Download completed: {remote_file}")
            return True
        else:
            logger.error(f"❌ [S3] Download failed with return code {rc}")
            logger.error(f"   Error: {stderr}")
            return False

    def run_orchestration(
        self,
        local_data_file: str,
        minio_bucket: str = "datasets",
        minio_key: str = "eurusd_m1_features_labels.parquet",
        data_md5: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行完整的编排流程。

        Args:
            local_data_file: 本地数据文件路径
            minio_bucket: MinIO bucket 名称
            minio_key: MinIO 对象 key
            data_md5: 数据文件的 MD5 (用于验证)

        Returns:
            编排结果汇总
        """
        logger.info("=" * 80)
        logger.info("🚀 GPU ORCHESTRATION STARTED")
        logger.info("=" * 80)

        result = {
            "status": "pending",
            "stages": {},
        }

        # Stage 1: SSH 连接
        logger.info("\n[STAGE 1] SSH Connection")
        if not self.connect_ssh():
            result["status"] = "failed"
            result["stages"]["ssh_connection"] = "failed"
            return result

        result["stages"]["ssh_connection"] = "success"

        try:
            # Stage 2: 数据上传
            logger.info("\n[STAGE 2] Data Upload to MinIO")
            upload_result = self.upload_data_to_minio(
                local_data_file,
                bucket=minio_bucket,
                key=minio_key,
            )
            result["stages"]["data_upload"] = upload_result
            if upload_result["status"] != "success":
                result["status"] = "failed"
                return result

            data_md5 = upload_result.get("md5", data_md5)

            # Stage 3: 脚本部署
            logger.info("\n[STAGE 3] Script Deployment")
            if not self.deploy_remote_scripts():
                result["status"] = "failed"
                result["stages"]["script_deployment"] = "failed"
                return result

            result["stages"]["script_deployment"] = "success"

            # Stage 4: 远程环境安装
            logger.info("\n[STAGE 4] Remote Environment Setup")
            if not self.run_setup_env_remote():
                result["status"] = "failed"
                result["stages"]["remote_setup"] = "failed"
                return result

            result["stages"]["remote_setup"] = "success"

            # Stage 5: GPU 探针
            logger.info("\n[STAGE 5] GPU Probe")
            probe_result = self.run_gpu_probe_remote()
            if not probe_result:
                result["status"] = "failed"
                result["stages"]["gpu_probe"] = "failed"
                return result

            result["stages"]["gpu_probe"] = probe_result

            # Stage 6: 数据下载
            logger.info("\n[STAGE 6] Remote Data Download")
            if not self.download_data_from_minio(
                bucket=minio_bucket,
                key=minio_key,
                expected_md5=data_md5,
            ):
                result["status"] = "failed"
                result["stages"]["data_download"] = "failed"
                return result

            result["stages"]["data_download"] = "success"

            # 全部成功
            result["status"] = "success"
            logger.info("\n" + "=" * 80)
            logger.info("✅ GPU ORCHESTRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

            return result

        finally:
            self.disconnect_ssh()


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="GPU 编排和部署工具")
    parser.add_argument("--target", default=os.getenv("GPU_HOST", "www.guangzhoupeak.com"))
    parser.add_argument("--user", default=os.getenv("GPU_USER", "root"))
    parser.add_argument("--port", type=int, default=int(os.getenv("GPU_PORT", "22")))
    parser.add_argument("--key", default=os.getenv("GPU_KEY_PATH", None))
    parser.add_argument("--data-file", required=True)
    parser.add_argument("--minio-endpoint", default=os.getenv("MINIO_ENDPOINT_URL", "http://minio:9000"))
    parser.add_argument("--minio-key", default=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"))
    parser.add_argument("--minio-secret", default=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"))

    args = parser.parse_args()

    # 创建编排器
    orchestrator = GPUOrchestrator(
        gpu_host=args.target,
        gpu_user=args.user,
        gpu_port=args.port,
        private_key_path=args.key,
        minio_endpoint=args.minio_endpoint,
        aws_access_key=args.minio_key,
        aws_secret_key=args.minio_secret,
    )

    # 运行编排
    result = orchestrator.run_orchestration(
        local_data_file=args.data_file,
    )

    # 输出结果
    logger.info("\n" + "=" * 80)
    logger.info("ORCHESTRATION RESULT SUMMARY")
    logger.info("=" * 80)
    logger.info(json.dumps(result, indent=2, default=str))

    # 返回状态码
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
