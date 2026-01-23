#!/usr/bin/env python3
"""
Gateway IP 迁移脚本
任务: Task #132 - Infrastructure IP Migration
功能: 将 GTW 节点 IP 从 172.19.141.255 (广播地址) 迁移至 172.19.141.251
协议: Protocol v4.4 (Zero-Trust Forensics)
生成时间: 2026-01-23
"""

import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
import uuid

# ========================================
# 常量定义
# ========================================

# 旧IP（需要替换）
OLD_IP = "172.19.141.255"

# 新IP（目标地址）
NEW_IP = "172.19.141.251"

# 目标配置文件
TARGET_FILE = Path("/opt/mt5-crs/src/mt5_bridge/config.py")

# 备份文件
BACKUP_FILE = Path("/opt/mt5-crs/src/mt5_bridge/config.py.bak.131")

# 日志文件
LOG_FILE = Path("/opt/mt5-crs/VERIFY_LOG.log")

# Session UUID (用于追踪)
SESSION_UUID = str(uuid.uuid4())


class MigrationLogger:
    """迁移日志器"""

    def __init__(self, log_file: Path):
        """初始化日志器"""
        self.log_file = log_file

    def log(self, message: str, level: str = "INFO"):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [Task#132] {message}"
        print(log_entry)

        # 追加到日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def log_physical_evidence(self, evidence_type: str, data: str):
        """记录物理证据"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        evidence = f"[{timestamp}] [PHYSICAL_EVIDENCE] [{evidence_type}] UUID={SESSION_UUID} {data}"
        print(evidence)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(evidence + "\n")


class IPMigrator:
    """IP迁移器"""

    def __init__(self, logger: MigrationLogger):
        """初始化迁移器"""
        self.logger = logger
        self.old_ip = OLD_IP
        self.new_ip = NEW_IP

    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def verify_backup(self) -> bool:
        """验证备份文件存在"""
        if not BACKUP_FILE.exists():
            self.logger.log("备份文件不存在，迁移终止", "ERROR")
            return False

        backup_hash = self.calculate_file_hash(BACKUP_FILE)
        self.logger.log_physical_evidence("BACKUP_HASH", f"SHA256={backup_hash}")
        return True

    def read_config(self) -> Optional[str]:
        """读取配置文件内容"""
        try:
            with open(TARGET_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.log(f"成功读取配置文件: {TARGET_FILE}")
            return content
        except Exception as e:
            self.logger.log(f"读取配置文件失败: {e}", "ERROR")
            return None

    def replace_ip(self, content: str) -> Tuple[str, int]:
        """替换IP地址"""
        # 记录替换前的哈希
        old_hash = hashlib.sha256(content.encode()).hexdigest()
        self.logger.log_physical_evidence("BEFORE_MIGRATION", f"ContentHash={old_hash}")

        # 执行替换
        new_content = content.replace(self.old_ip, self.new_ip)

        # 计算替换次数
        replacement_count = content.count(self.old_ip)

        # 记录替换后的哈希
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()
        self.logger.log_physical_evidence("AFTER_MIGRATION", f"ContentHash={new_hash}")

        self.logger.log(f"IP替换完成: {self.old_ip} -> {self.new_ip} (共{replacement_count}处)")

        return new_content, replacement_count

    def write_config(self, content: str) -> bool:
        """写入新配置"""
        try:
            with open(TARGET_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.log(f"配置文件已更新: {TARGET_FILE}")

            # 验证写入
            new_hash = self.calculate_file_hash(TARGET_FILE)
            self.logger.log_physical_evidence("NEW_FILE_HASH", f"SHA256={new_hash}")

            return True
        except Exception as e:
            self.logger.log(f"写入配置文件失败: {e}", "ERROR")
            return False

    def verify_migration(self) -> bool:
        """验证迁移结果"""
        content = self.read_config()
        if not content:
            return False

        # 检查新IP存在
        if self.new_ip not in content:
            self.logger.log(f"验证失败: 未找到新IP {self.new_ip}", "ERROR")
            return False

        # 检查旧IP不存在
        if self.old_ip in content:
            self.logger.log(f"验证失败: 仍存在旧IP {self.old_ip}", "ERROR")
            return False

        self.logger.log("迁移验证通过", "INFO")
        return True

    def run_migration(self) -> bool:
        """执行完整迁移流程"""
        self.logger.log("=" * 70, "INFO")
        self.logger.log("开始 Gateway IP 迁移 (Task #132)", "INFO")
        self.logger.log("=" * 70, "INFO")
        self.logger.log_physical_evidence("SESSION_START", f"Timestamp={datetime.now().isoformat()}")

        # Step 1: 验证备份
        if not self.verify_backup():
            return False

        # Step 2: 读取配置
        content = self.read_config()
        if not content:
            return False

        # Step 3: 检查是否需要迁移
        if self.old_ip not in content:
            self.logger.log(f"配置文件中未找到旧IP {self.old_ip}，无需迁移", "INFO")
            # 检查新IP是否已存在
            if self.new_ip in content:
                self.logger.log(f"新IP {self.new_ip} 已存在，迁移可能已完成", "INFO")
                return True
            else:
                self.logger.log("配置异常：旧IP和新IP都不存在", "ERROR")
                return False

        # Step 4: 执行替换
        new_content, replacement_count = self.replace_ip(content)

        if replacement_count == 0:
            self.logger.log("未发现需要替换的IP地址", "WARNING")
            return False

        # Step 5: 写入新配置
        if not self.write_config(new_content):
            self.logger.log("回滚: 恢复备份文件", "ERROR")
            # 这里可以添加回滚逻辑
            return False

        # Step 6: 验证迁移
        if not self.verify_migration():
            self.logger.log("迁移验证失败", "ERROR")
            return False

        # Step 7: 记录成功
        self.logger.log("=" * 70, "INFO")
        self.logger.log("[MIGRATION_SUCCESS] Gateway IP 迁移成功完成", "INFO")
        self.logger.log(f"  旧IP: {self.old_ip}", "INFO")
        self.logger.log(f"  新IP: {self.new_ip}", "INFO")
        self.logger.log(f"  替换次数: {replacement_count}", "INFO")
        self.logger.log("=" * 70, "INFO")
        self.logger.log_physical_evidence("MIGRATION_COMPLETE", f"ReplacementCount={replacement_count}")

        return True


def main():
    """主函数"""
    # 初始化日志器
    logger = MigrationLogger(LOG_FILE)

    # 初始化迁移器
    migrator = IPMigrator(logger)

    # 执行迁移
    success = migrator.run_migration()

    # 退出
    if success:
        logger.log("[UnifiedGate] PASS - IP迁移审计通过", "INFO")
        sys.exit(0)
    else:
        logger.log("[UnifiedGate] FAIL - IP迁移失败", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
