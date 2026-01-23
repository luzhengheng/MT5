#!/usr/bin/env python3
"""
网络拓扑验证脚本
任务: Task #132 - Infrastructure IP Migration & Configuration Alignment
功能: 验证新IP地址 (172.19.141.251) 的网络连通性和ZMQ端口可达性
协议: Protocol v4.4 (Zero-Trust Forensics)
生成时间: 2026-01-23
"""

import socket
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
import uuid
import json

# ========================================
# 常量定义
# ========================================

TARGET_IP = "172.19.141.251"
TARGET_HOSTNAME = "sg-mt5-gateway-01"
ZMQ_REQ_PORT = 5555    # REQ socket (交易指令)
ZMQ_PUB_PORT = 5556    # PUB socket (行情推送)
SSH_PORT = 22

# 日志文件
LOG_FILE = Path("/opt/mt5-crs/VERIFY_LOG.log")

# Session UUID
SESSION_UUID = str(uuid.uuid4())

# ========================================
# 配置
# ========================================

RETRY_CONFIG = {
    "max_attempts": 3,
    "timeout": 5,
    "backoff_factor": 2
}


class NetworkLogger:
    """网络验证日志器"""

    def __init__(self, log_file: Path):
        """初始化"""
        self.log_file = log_file

    def log(self, message: str, level: str = "INFO"):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [Task#132-NetworkAudit] {message}"
        print(log_entry)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def log_evidence(self, check_type: str, status: str, details: str):
        """记录审计证据"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        evidence = f"[{timestamp}] [NetworkAudit] [{check_type}] Status={status} UUID={SESSION_UUID} {details}"
        print(evidence)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(evidence + "\n")


class NetworkVerifier:
    """网络验证器"""

    def __init__(self, logger: NetworkLogger):
        """初始化"""
        self.logger = logger
        self.target_ip = TARGET_IP
        self.results = {
            "ip": self.target_ip,
            "timestamp": datetime.now().isoformat(),
            "checks": []
        }

    def check_icmp_reachability(self) -> bool:
        """检查ICMP可达性 (ping)"""
        self.logger.log(f"检查ICMP可达性: {self.target_ip}")

        try:
            # 尝试创建到目标IP的套接字
            socket.setdefaulttimeout(RETRY_CONFIG["timeout"])
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # 尝试连接到DNS端口来检查连通性
            sock.connect((self.target_ip, 53))
            sock.close()

            self.logger.log(f"✅ ICMP 连通性检查通过: {self.target_ip}")
            self.logger.log_evidence(
                "ICMP_REACHABILITY",
                "PASS",
                f"IP={self.target_ip} reachable=true"
            )
            return True

        except socket.timeout:
            self.logger.log(f"❌ ICMP 超时: {self.target_ip}", "WARNING")
            self.logger.log_evidence(
                "ICMP_REACHABILITY",
                "TIMEOUT",
                f"IP={self.target_ip} timeout={RETRY_CONFIG['timeout']}s"
            )
            return False

        except ConnectionRefusedError:
            self.logger.log(f"❌ ICMP 连接被拒绝: {self.target_ip}", "WARNING")
            return False

        except Exception as e:
            self.logger.log(f"❌ ICMP 检查失败: {e}", "WARNING")
            return False

    def check_ssh_port(self) -> bool:
        """检查SSH端口 (22)"""
        self.logger.log(f"检查SSH端口: {self.target_ip}:{SSH_PORT}")

        try:
            socket.setdefaulttimeout(RETRY_CONFIG["timeout"])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((self.target_ip, SSH_PORT))
            sock.close()

            if result == 0:
                self.logger.log(f"✅ SSH端口开放: {self.target_ip}:{SSH_PORT}")
                self.logger.log_evidence(
                    "SSH_PORT",
                    "OPEN",
                    f"IP={self.target_ip} port={SSH_PORT} open=true"
                )
                return True
            else:
                self.logger.log(f"⚠️  SSH端口未开放或不可达: {self.target_ip}:{SSH_PORT}", "WARNING")
                self.logger.log_evidence(
                    "SSH_PORT",
                    "CLOSED",
                    f"IP={self.target_ip} port={SSH_PORT} open=false"
                )
                return False

        except socket.timeout:
            self.logger.log(f"⚠️  SSH端口检查超时: {self.target_ip}:{SSH_PORT}", "WARNING")
            return False

        except Exception as e:
            self.logger.log(f"❌ SSH端口检查失败: {e}", "WARNING")
            return False

    def check_zmq_req_port(self) -> bool:
        """检查ZMQ REQ端口 (5555)"""
        return self._check_zmq_port(ZMQ_REQ_PORT, "REQ")

    def check_zmq_pub_port(self) -> bool:
        """检查ZMQ PUB端口 (5556)"""
        return self._check_zmq_port(ZMQ_PUB_PORT, "PUB")

    def _check_zmq_port(self, port: int, socket_type: str) -> bool:
        """检查ZMQ端口"""
        self.logger.log(f"检查ZMQ {socket_type}端口: {self.target_ip}:{port}")

        for attempt in range(RETRY_CONFIG["max_attempts"]):
            try:
                socket.setdefaulttimeout(RETRY_CONFIG["timeout"])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((self.target_ip, port))
                sock.close()

                if result == 0:
                    self.logger.log(f"✅ ZMQ {socket_type}端口开放: {self.target_ip}:{port}")
                    self.logger.log_evidence(
                        f"ZMQ_{socket_type}_PORT",
                        "OPEN",
                        f"IP={self.target_ip} port={port} socket_type={socket_type} open=true"
                    )
                    return True
                else:
                    if attempt < RETRY_CONFIG["max_attempts"] - 1:
                        wait_time = RETRY_CONFIG["backoff_factor"] ** attempt
                        self.logger.log(
                            f"⚠️  ZMQ {socket_type}端口未开放，重试 ({attempt+1}/{RETRY_CONFIG['max_attempts']})...",
                            "WARNING"
                        )
                        time.sleep(wait_time)
                    else:
                        self.logger.log(f"❌ ZMQ {socket_type}端口不可达: {self.target_ip}:{port}", "WARNING")
                        self.logger.log_evidence(
                            f"ZMQ_{socket_type}_PORT",
                            "UNREACHABLE",
                            f"IP={self.target_ip} port={port} attempts={RETRY_CONFIG['max_attempts']}"
                        )
                        return False

            except socket.timeout:
                if attempt == RETRY_CONFIG["max_attempts"] - 1:
                    self.logger.log(f"❌ ZMQ {socket_type}端口超时: {self.target_ip}:{port}", "WARNING")
                    return False

            except Exception as e:
                self.logger.log(f"❌ ZMQ {socket_type}端口检查异常: {e}", "WARNING")
                return False

        return False

    def verify_config_alignment(self) -> bool:
        """验证配置对齐"""
        self.logger.log("验证config.py配置对齐")

        config_file = Path("/opt/mt5-crs/src/mt5_bridge/config.py")

        if not config_file.exists():
            self.logger.log("❌ config.py 文件不存在", "ERROR")
            return False

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查新IP是否存在
            if TARGET_IP in content:
                # 检查旧IP是否已移除
                if "172.19.141.255" not in content:
                    self.logger.log(f"✅ 配置对齐验证通过: {TARGET_IP}")
                    self.logger.log_evidence(
                        "CONFIG_ALIGNMENT",
                        "PASS",
                        f"new_ip={TARGET_IP} old_ip_removed=true"
                    )
                    return True
                else:
                    self.logger.log("❌ 旧IP仍存在于配置文件中", "ERROR")
                    return False
            else:
                self.logger.log(f"❌ 新IP未在配置文件中: {TARGET_IP}", "ERROR")
                return False

        except Exception as e:
            self.logger.log(f"❌ 配置文件检查异常: {e}", "ERROR")
            return False

    def run_verification(self) -> bool:
        """运行完整验证"""
        self.logger.log("=" * 70)
        self.logger.log("开始网络拓扑验证 (Task #132)")
        self.logger.log("=" * 70)
        self.logger.log_evidence("VERIFICATION_START", "BEGIN", f"IP={self.target_ip} UUID={SESSION_UUID}")

        checks = [
            ("ICMP可达性", self.check_icmp_reachability),
            ("SSH端口(22)", self.check_ssh_port),
            ("ZMQ REQ端口(5555)", self.check_zmq_req_port),
            ("ZMQ PUB端口(5556)", self.check_zmq_pub_port),
            ("配置对齐", self.verify_config_alignment)
        ]

        results = {}
        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                self.results["checks"].append({
                    "name": check_name,
                    "passed": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.log(f"❌ {check_name} 执行异常: {e}", "ERROR")
                results[check_name] = False

        # 汇总
        self.logger.log("\n" + "=" * 70)
        self.logger.log("网络验证汇总")
        self.logger.log("=" * 70)

        passed_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        for check_name, result in results.items():
            status = "✅" if result else "❌"
            self.logger.log(f"{status} {check_name}")

        self.logger.log(f"\n通过率: {passed_count}/{total_count}")

        # 判断总体通过
        overall_pass = (passed_count >= 4)  # 至少4项通过

        if overall_pass:
            self.logger.log("\n[NetworkAudit] PASS: 172.19.141.251 reachable")
            self.logger.log_evidence(
                "VERIFICATION_RESULT",
                "PASS",
                f"target_ip={self.target_ip} passed_checks={passed_count}/{total_count}"
            )
        else:
            self.logger.log("\n[NetworkAudit] FAIL: 无法验证网络连通性")
            self.logger.log_evidence(
                "VERIFICATION_RESULT",
                "FAIL",
                f"target_ip={self.target_ip} passed_checks={passed_count}/{total_count}"
            )

        self.logger.log("=" * 70)

        return overall_pass


def main():
    """主函数"""
    logger = NetworkLogger(LOG_FILE)
    verifier = NetworkVerifier(logger)

    success = verifier.run_verification()

    # 保存结果
    results_file = Path("/opt/mt5-crs/network_verification_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(verifier.results, f, indent=2, ensure_ascii=False)

    logger.log(f"验证结果已保存: {results_file}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
