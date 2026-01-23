# ========================================
# MT5-CRS 网络配置和 ZeroMQ 通信配置
# ========================================
# 用途: 管理基础设施网络常量、ZeroMQ 连接地址、域名映射等
# 最后更新: 2025-12-21 (工单 #011 Phase 1)
#
# 核心配置:
#   1. VPC 网络识别 (新加坡: 172.19.0.0/16 | 广州: 172.23.0.0/16)
#   2. ZeroMQ 服务器地址 (内网模式 vs 开发模式)
#   3. 基础设施域名映射
#   4. 服务器连接详情
# ========================================

import socket
import ipaddress
import os
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========================================
# 网络拓扑定义
# ========================================

class NetworkTopology:
    """网络拓扑常量定义"""

    # VPC 网段定义
    PROD_VPC_CIDR = ipaddress.ip_network("172.19.0.0/16")  # 新加坡交易网
    TRAIN_VPC_CIDR = ipaddress.ip_network("172.23.0.0/16")  # 广州训练网

    # 区域标识
    REGION_SINGAPORE = "sg"
    REGION_GUANGZHOU = "gz"


class ServerAssets:
    """基础设施服务器资产清单"""

    # ========================================
    # 服务器资产 (新加坡交易网)
    # ========================================

    INF = {
        "shortname": "inf",
        "role": "大脑 (推理节点)",
        "hostname": "sg-infer-core-01",
        "public_ip": "47.84.111.158",
        "private_ip": "172.19.141.250",
        "fqdn": "www.crestive.net",
        "port": 22,
        "user": "root",
        "auth_method": "SSH Key",
        "region": NetworkTopology.REGION_SINGAPORE,
        "vpc_cidr": NetworkTopology.PROD_VPC_CIDR,
    }

    GTW = {
        "shortname": "gtw",
        "role": "手脚 (Windows 网关)",
        "hostname": "sg-mt5-gateway-01",
        "public_ip": "47.237.79.129",
        "private_ip": "172.19.141.255",
        "fqdn": "gtw.crestive.net",
        "port": 22,
        "user": "Administrator",
        "auth_method": "密码 (待迁移至 SSH Key)",
        "region": NetworkTopology.REGION_SINGAPORE,
        "vpc_cidr": NetworkTopology.PROD_VPC_CIDR,
        "os": "Windows Server 2022",
        "zmq_server": True,  # 这是 ZeroMQ 服务器主机
    }

    HUB = {
        "shortname": "hub",
        "role": "中枢 (代码仓库)",
        "hostname": "sg-nexus-hub-01",
        "public_ip": "47.84.1.161",
        "private_ip": "172.19.141.254",
        "fqdn": "www.crestive-code.com",
        "port": 22,
        "user": "root",
        "auth_method": "SSH Key",
        "region": NetworkTopology.REGION_SINGAPORE,
        "vpc_cidr": NetworkTopology.PROD_VPC_CIDR,
        "git_repo": True,  # 这是代码仓库主机
    }

    # ========================================
    # 服务器资产 (广州训练网)
    # ========================================

    GPU = {
        "shortname": "gpu",
        "role": "核武 (GPU 训练节点)",
        "hostname": "cn-train-gpu-01",
        "public_ip": "8.138.100.136",
        "private_ip": "172.23.135.141",
        "fqdn": "www.guangzhoupeak.com",
        "port": 22,
        "user": "root",
        "auth_method": "SSH Key",
        "region": NetworkTopology.REGION_GUANGZHOU,
        "vpc_cidr": NetworkTopology.TRAIN_VPC_CIDR,
        "gpu_trainer": True,  # 这是 GPU 训练主机
        "specs": {
            "cpu": "32 vCPU",
            "memory": "188GB",
            "gpu": "NVIDIA A10",
        }
    }


class MT5Config:
    """
    MT5 交易配置
    Gemini P1 修复: Magic Number 配置化
    """

    # 魔法数字 (Magic Number) - 用于标识订单来源
    # 从环境变量读取，默认 123456
    MAGIC_NUMBER = int(os.getenv("MT5_MAGIC_NUMBER", "123456"))

    # 策略基数 (可选) - 用于给不同策略分配不同 magic
    # 例如: 趋势策略 = 120001, 震荡策略 = 120002
    STRATEGY_MAGIC_BASE = int(os.getenv("MT5_STRATEGY_MAGIC_BASE", "120000"))

    # 交易超时配置
    ORDER_TIMEOUT = float(os.getenv("MT5_ORDER_TIMEOUT", "10.0"))  # 订单超时 (秒)
    INQUIRY_TIMEOUT = float(os.getenv("MT5_INQUIRY_TIMEOUT", "5.0"))  # 查单超时 (秒)

    # 订单重试配置
    MAX_RETRIES = int(os.getenv("MT5_MAX_RETRIES", "3"))  # 最大重试次数
    RETRY_DELAY = float(os.getenv("MT5_RETRY_DELAY", "1.0"))  # 重试延迟 (秒)


class ZeroMQConfig:
    """ZeroMQ 通信配置"""

    # ========================================
    # ZMQ 端口定义
    # ========================================

    ZMQ_REQ_PORT = 5555    # 交易指令通道 (REQ-REP 模式)
    ZMQ_PUB_PORT = 5556    # 行情推送通道 (PUB-SUB 模式)

    # ========================================
    # ZMQ 服务器地址配置
    # ========================================

    # 服务器（GTW）内网 IP - 仅在生产 VPC 内可用
    ZMQ_SERVER_ADDR_INTERNAL = f"tcp://{ServerAssets.GTW['private_ip']}"

    # 本地开发环境 (通过 SSH 隧道转发)
    ZMQ_SERVER_ADDR_LOCAL = "tcp://127.0.0.1"

    # 公网连接 (不推荐，需要特殊安全配置)
    ZMQ_SERVER_ADDR_PUBLIC = f"tcp://{ServerAssets.GTW['public_ip']}"


class DomainMapping:
    """基础设施域名映射表"""

    DOMAINS: Dict[str, Dict[str, str]] = {
        "brain": {
            "shortname": "inf",
            "fqdn": ServerAssets.INF["fqdn"],
            "public_ip": ServerAssets.INF["public_ip"],
            "private_ip": ServerAssets.INF["private_ip"],
        },
        "hand": {
            "shortname": "gtw",
            "fqdn": ServerAssets.GTW["fqdn"],
            "public_ip": ServerAssets.GTW["public_ip"],
            "private_ip": ServerAssets.GTW["private_ip"],
        },
        "repo": {
            "shortname": "hub",
            "fqdn": ServerAssets.HUB["fqdn"],
            "public_ip": ServerAssets.HUB["public_ip"],
            "private_ip": ServerAssets.HUB["private_ip"],
        },
        "train": {
            "shortname": "gpu",
            "fqdn": ServerAssets.GPU["fqdn"],
            "public_ip": ServerAssets.GPU["public_ip"],
            "private_ip": ServerAssets.GPU["private_ip"],
        },
    }

    @classmethod
    def get_fqdn(cls, alias: str) -> Optional[str]:
        """根据别名获取 FQDN"""
        if alias in cls.DOMAINS:
            return cls.DOMAINS[alias]["fqdn"]
        return None

    @classmethod
    def get_all_domains(cls) -> Dict[str, str]:
        """获取所有域名映射 (别名 -> FQDN)"""
        return {k: v["fqdn"] for k, v in cls.DOMAINS.items()}


class NetworkEnvironment:
    """网络环境检测和配置"""

    @staticmethod
    def get_local_ip() -> Optional[str]:
        """获取本机内网 IP"""
        try:
            # 连接到一个远程 DNS 服务器（不实际发送数据）
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except Exception:
            return None

    @staticmethod
    def is_production_environment() -> bool:
        """检测当前环境是否为生产环境 (新加坡 VPC)"""
        local_ip = NetworkEnvironment.get_local_ip()
        if not local_ip:
            return False

        try:
            ip_obj = ipaddress.ip_address(local_ip)
            return ip_obj in NetworkTopology.PROD_VPC_CIDR
        except ValueError:
            return False

    @staticmethod
    def is_training_environment() -> bool:
        """检测当前环境是否为训练环境 (广州 VPC)"""
        local_ip = NetworkEnvironment.get_local_ip()
        if not local_ip:
            return False

        try:
            ip_obj = ipaddress.ip_address(local_ip)
            return ip_obj in NetworkTopology.TRAIN_VPC_CIDR
        except ValueError:
            return False

    @staticmethod
    def is_local_development() -> bool:
        """检测当前环境是否为本地开发环境"""
        return not (NetworkEnvironment.is_production_environment() or
                   NetworkEnvironment.is_training_environment())


class ZeroMQConnectionManager:
    """ZeroMQ 连接管理器"""

    @staticmethod
    def get_zmq_server_address(service: str = "req") -> str:
        """
        获取 ZeroMQ 服务器地址

        参数:
            service: "req" (交易指令) 或 "pub" (行情推送)

        返回:
            完整的 ZMQ 连接地址 (含协议和端口)

        逻辑:
            - 生产环境 (172.19.0.0/16): 使用内网 IP (172.19.141.255)
            - 开发环境: 使用本地 127.0.0.1 (需配合 SSH 隧道)
        """
        port = ZeroMQConfig.ZMQ_REQ_PORT if service == "req" else ZeroMQConfig.ZMQ_PUB_PORT

        if NetworkEnvironment.is_production_environment():
            # 生产环境：使用内网 IP（零延迟，流量免费）
            return f"{ZeroMQConfig.ZMQ_SERVER_ADDR_INTERNAL}:{port}"
        else:
            # 开发环境：使用本地 IP（需配合 SSH 隧道）
            # 使用方法: ssh -L 5555:172.19.141.255:5555 inf
            return f"{ZeroMQConfig.ZMQ_SERVER_ADDR_LOCAL}:{port}"

    @staticmethod
    def get_all_connection_info() -> Dict[str, str]:
        """获取所有 ZMQ 连接地址"""
        return {
            "req_server": ZeroMQConnectionManager.get_zmq_server_address("req"),
            "pub_server": ZeroMQConnectionManager.get_zmq_server_address("pub"),
            "environment": (
                "production" if NetworkEnvironment.is_production_environment() else
                "training" if NetworkEnvironment.is_training_environment() else
                "local"
            ),
            "local_ip": NetworkEnvironment.get_local_ip(),
        }


class SecurityGroups:
    """安全组配置参考"""

    SINGAPORE = {
        "id": "sg-t4n0dtkxxy1sxnbjsgk6",
        "region": "cn-shanghai",
        "description": "新加坡交易网安全组 (INF, GTW, HUB)",
        "rules": {
            5555: {
                "protocol": "TCP",
                "source": "172.19.0.0/16",
                "description": "ZMQ REQ (交易指令) - 仅限内网",
                "security_level": "极高",
            },
            5556: {
                "protocol": "TCP",
                "source": "172.19.0.0/16",
                "description": "ZMQ PUB (行情推送) - 仅限内网",
                "security_level": "极高",
            },
            22: {
                "protocol": "TCP",
                "source": "0.0.0.0/0",
                "description": "SSH 远程管理",
                "security_level": "中",
            },
            80: {
                "protocol": "TCP",
                "source": "0.0.0.0/0",
                "description": "HTTP Web 服务",
                "security_level": "公开",
            },
            443: {
                "protocol": "TCP",
                "source": "0.0.0.0/0",
                "description": "HTTPS Web 服务",
                "security_level": "公开",
            },
            3389: {
                "protocol": "TCP",
                "source": "0.0.0.0/0",
                "description": "RDP 远程桌面 (Windows)",
                "security_level": "中",
            },
        }
    }

    GUANGZHOU = {
        "id": "sg-7xvffzmphblpy15x141f",
        "region": "cn-guangzhou",
        "description": "广州训练网安全组 (GPU)",
        "rules": {
            22: {
                "protocol": "TCP",
                "source": "0.0.0.0/0",
                "description": "SSH 远程管理",
                "security_level": "中",
            },
            6006: {
                "protocol": "TCP",
                "source": "0.0.0.0/0",
                "description": "TensorBoard 训练可视化",
                "security_level": "中",
            },
        }
    }


# ========================================
# 快速访问函数
# ========================================

def get_zmq_req_address() -> str:
    """快速获取 ZMQ REQ (交易指令) 服务器地址"""
    return ZeroMQConnectionManager.get_zmq_server_address("req")


def get_zmq_pub_address() -> str:
    """快速获取 ZMQ PUB (行情推送) 服务器地址"""
    return ZeroMQConnectionManager.get_zmq_server_address("pub")


def get_server_info(shortname: str) -> Optional[Dict]:
    """根据简称获取服务器信息"""
    servers = {
        "inf": ServerAssets.INF,
        "gtw": ServerAssets.GTW,
        "hub": ServerAssets.HUB,
        "gpu": ServerAssets.GPU,
    }
    return servers.get(shortname)


def print_network_status():
    """打印网络环境和连接状态"""
    print("\n" + "="*60)
    print("MT5-CRS 网络配置状态")
    print("="*60)

    local_ip = NetworkEnvironment.get_local_ip()
    print(f"\n本机 IP: {local_ip}")

    if NetworkEnvironment.is_production_environment():
        print("环境: 🟢 生产环境 (新加坡 VPC)")
        print(f"ZMQ 服务器地址: {get_zmq_req_address()}")
    elif NetworkEnvironment.is_training_environment():
        print("环境: 🟡 训练环境 (广州 VPC)")
    else:
        print("环境: 🔵 本地开发")
        print("注意: 需要配置 SSH 隧道来访问 ZMQ 服务器")
        print(f"  命令: ssh -L 5555:172.19.141.255:5555 inf")
        print(f"ZMQ 服务器地址: {get_zmq_req_address()}")

    print("\n" + "="*60)
    print("域名映射表:")
    print("="*60)
    for alias, info in DomainMapping.DOMAINS.items():
        print(f"  {alias:8} -> {info['fqdn']:<30} (Public: {info['public_ip']})")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # 测试配置
    print_network_status()

    print("ZMQ 连接信息:")
    print(ZeroMQConnectionManager.get_all_connection_info())

    print("\nSingapore 安全组规则:")
    for port, rule in SecurityGroups.SINGAPORE["rules"].items():
        print(f"  端口 {port}: {rule['description']}")
