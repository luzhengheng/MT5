#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 环境探针脚本

Purpose:
  在远程 GPU 节点上运行，检测：
  - CUDA 可用性和版本
  - GPU 硬件型号和显存
  - Python 版本和关键依赖
  - 磁盘空间
  - 网络连接

Design:
  - 独立脚本，无外部依赖（除了系统工具）
  - 返回 JSON 格式的诊断信息
  - 支持远程 SSH 执行

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-12
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, Optional


# ============================================================================
# 探针函数
# ============================================================================

class GPUProbe:
    """GPU 和系统环境探针"""

    def __init__(self):
        """初始化探针"""
        self.results: Dict[str, Any] = {}
        self.errors: list = []

    def _run_command(self, cmd: str, shell: bool = True) -> tuple[Optional[str], Optional[str]]:
        """
        执行系统命令。

        Returns:
            (stdout, stderr) 元组
        """
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                timeout=10,
                text=True,
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return None, f"Command timed out: {cmd}"
        except Exception as e:
            return None, str(e)

    def probe_system(self) -> Dict[str, Any]:
        """探针系统信息"""
        self.results["system"] = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
        }
        return self.results["system"]

    def probe_cuda(self) -> Dict[str, Any]:
        """探针 CUDA 信息"""
        cuda_info = {
            "cuda_available": False,
            "cuda_version": None,
            "nvidia_smi_output": None,
            "gpu_count": 0,
            "gpus": [],
        }

        # 检查 nvidia-smi
        stdout, stderr = self._run_command("which nvidia-smi")
        if not stdout:
            self.errors.append("nvidia-smi not found (CUDA may not be installed)")
            self.results["cuda"] = cuda_info
            return cuda_info

        cuda_info["cuda_available"] = True

        # 获取 CUDA 版本
        stdout, stderr = self._run_command("nvidia-smi --query-gpu=driver_version --format=csv,noheader")
        if stdout:
            cuda_info["driver_version"] = stdout.split("\n")[0]

        # 获取 GPU 信息
        stdout, stderr = self._run_command(
            "nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader"
        )
        if stdout:
            cuda_info["nvidia_smi_output"] = stdout
            gpus = []
            for line in stdout.split("\n"):
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 3:
                        gpus.append({
                            "index": int(parts[0].strip()),
                            "name": parts[1].strip(),
                            "memory_mb": int(parts[2].strip().split()[0]),
                        })
            cuda_info["gpus"] = gpus
            cuda_info["gpu_count"] = len(gpus)

        self.results["cuda"] = cuda_info
        return cuda_info

    def probe_disk(self) -> Dict[str, Any]:
        """探针磁盘空间"""
        disk_info = {}

        # 检查根目录和 home 目录
        for path in ["/", os.path.expanduser("~")]:
            try:
                stat = os.statvfs(path)
                available = stat.f_bavail * stat.f_frsize / (1024 ** 3)  # GB
                total = stat.f_blocks * stat.f_frsize / (1024 ** 3)  # GB
                disk_info[path] = {
                    "total_gb": round(total, 2),
                    "available_gb": round(available, 2),
                    "percent_free": round((available / total * 100), 2),
                }
            except Exception as e:
                self.errors.append(f"Failed to check disk space for {path}: {e}")

        self.results["disk"] = disk_info
        return disk_info

    def probe_dependencies(self) -> Dict[str, Any]:
        """探针关键 Python 依赖"""
        deps_info = {}

        packages = ["torch", "numpy", "pandas", "boto3", "sklearn"]
        for pkg in packages:
            try:
                module = __import__(pkg)
                version = getattr(module, "__version__", "unknown")
                deps_info[pkg] = {
                    "installed": True,
                    "version": version,
                }
            except ImportError:
                deps_info[pkg] = {
                    "installed": False,
                    "version": None,
                }

        self.results["dependencies"] = deps_info
        return deps_info

    def probe_network(self) -> Dict[str, Any]:
        """探针网络连接"""
        network_info = {}

        # 获取主机名
        try:
            import socket
            network_info["hostname"] = socket.gethostname()
            network_info["fqdn"] = socket.getfqdn()
        except Exception as e:
            self.errors.append(f"Failed to get hostname: {e}")

        # 获取 IP 地址
        stdout, stderr = self._run_command("hostname -I")
        if stdout:
            network_info["ip_addresses"] = stdout.split()

        self.results["network"] = network_info
        return network_info

    def run_full_probe(self) -> Dict[str, Any]:
        """运行完整探针"""
        print("[PROBE] Starting full GPU probe...", file=sys.stderr)

        self.probe_system()
        self.probe_cuda()
        self.probe_disk()
        self.probe_dependencies()
        self.probe_network()

        probe_result = {
            "success": len(self.errors) == 0,
            "timestamp": self._get_timestamp(),
            "data": self.results,
            "errors": self.errors if self.errors else None,
        }

        return probe_result

    @staticmethod
    def _get_timestamp() -> str:
        """获取 ISO 8601 时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主入口"""
    probe = GPUProbe()
    result = probe.run_full_probe()

    # 输出 JSON 到 stdout
    print(json.dumps(result, indent=2))

    # 返回状态码
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
