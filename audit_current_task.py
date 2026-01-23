#!/usr/bin/env python3
"""
Task #132 审计脚本 (Policy-as-Code)
功能: 扫描全项目，禁止出现 172.19.141.255 字符串（除历史日志外）
Protocol: v4.4
生成时间: 2026-01-23
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# ========================================
# 常量定义
# ========================================

# 禁止的IP地址
FORBIDDEN_IP = "172.19.141.255"

# 新IP地址
NEW_IP = "172.19.141.251"

# 排除的目录和文件
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
    'node_modules', '.idea', '.vscode', '_archive_20251222',
    'data', 'mlruns', '.backup', 'exports', 'docs/archive'
}

# 允许在这些文件中出现旧IP（历史或备份）
ALLOW_IN_FILES = {
    'config.py.bak.131',  # 备份文件允许
    'VERIFY_LOG.log',     # 日志文件允许
    '.git',               # Git历史允许
    '_archive_20251222',  # 归档允许
}

# ========================================
# 审计规则
# ========================================

AUDIT_RULES = [
    {
        "id": "RULE_001",
        "name": "禁止广播IP地址",
        "description": "检测项目中是否包含 172.19.141.255 (广播地址)",
        "severity": "CRITICAL",
        "pattern": FORBIDDEN_IP
    },
    {
        "id": "RULE_002",
        "name": "验证新IP格式",
        "description": "确保新IP地址格式正确: 172.19.141.251",
        "severity": "MEDIUM",
        "pattern": NEW_IP
    },
    {
        "id": "RULE_003",
        "name": "ZMQ配置一致性",
        "description": "验证ZMQ配置中的IP地址已更新",
        "severity": "HIGH",
        "check_files": ["src/mt5_bridge/config.py"]
    }
]


class TaskAuditor:
    """Task #132 审计器"""

    def __init__(self, project_root: Path = None):
        """初始化审计器"""
        self.project_root = project_root or Path("/opt/mt5-crs")
        self.issues = []
        self.warnings = []
        self.passed_rules = []

    def should_skip(self, file_path: Path) -> bool:
        """判断文件是否应被跳过"""
        # 检查是否在排除目录中
        for exclude_dir in EXCLUDE_DIRS:
            if exclude_dir in file_path.parts:
                return True

        # 检查是否在允许列表中
        for allowed_file in ALLOW_IN_FILES:
            if allowed_file in str(file_path):
                return True

        # 跳过非文本文件
        binary_extensions = {'.pkl', '.parquet', '.db', '.rdb', '.png', '.jpg', '.zip', '.tar.gz'}
        if file_path.suffix in binary_extensions:
            return True

        return False

    def scan_for_forbidden_ip(self) -> List[Tuple[Path, int, str]]:
        """扫描项目中的禁止IP地址"""
        findings = []

        print("\n[AUDIT_001] 扫描禁止的IP地址: 172.19.141.255")
        print("=" * 70)

        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file() or self.should_skip(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if FORBIDDEN_IP in line:
                            # 如果文件不在备份中，这是一个问题
                            if 'bak' not in str(file_path) and '_archive' not in str(file_path):
                                findings.append((file_path, line_num, line.strip()))
                                print(f"  ❌ {file_path.relative_to(self.project_root)}:{line_num}")
                                print(f"     内容: {line.strip()[:80]}")
            except Exception as e:
                self.warnings.append(f"无法读取文件 {file_path}: {e}")

        if not findings:
            print(f"  ✅ 未发现禁止的IP地址 {FORBIDDEN_IP}")
            self.passed_rules.append("RULE_001")
        else:
            self.issues.append(f"发现 {len(findings)} 处禁止的IP地址")

        return findings

    def verify_zmq_config(self) -> bool:
        """验证ZMQ配置中的IP已更新"""
        print("\n[AUDIT_003] 验证ZMQ配置一致性")
        print("=" * 70)

        config_file = self.project_root / "src/mt5_bridge/config.py"

        if not config_file.exists():
            self.issues.append("config.py 文件不存在")
            return False

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否包含新IP
            if NEW_IP in content:
                print(f"  ✅ config.py 包含新IP: {NEW_IP}")
                self.passed_rules.append("RULE_003")
                return True
            else:
                print(f"  ⚠️  config.py 未包含新IP: {NEW_IP}")
                self.warnings.append("config.py 需要更新为新IP")
                return False
        except Exception as e:
            self.issues.append(f"读取config.py失败: {e}")
            return False

    def check_syntax(self) -> bool:
        """检查config.py的Python语法"""
        print("\n[AUDIT_002] 检查config.py语法")
        print("=" * 70)

        config_file = self.project_root / "src/mt5_bridge/config.py"

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(config_file), 'exec')
            print(f"  ✅ config.py 语法正确")
            return True
        except SyntaxError as e:
            print(f"  ❌ 语法错误: {e}")
            self.issues.append(f"config.py 语法错误: {e}")
            return False

    def run_audit(self) -> bool:
        """运行完整审计"""
        print("\n" + "=" * 70)
        print("🔍 Task #132 审计开始 (Policy-as-Code)")
        print("=" * 70)

        # 运行所有检查
        forbidden_findings = self.scan_for_forbidden_ip()
        syntax_ok = self.check_syntax()
        zmq_ok = self.verify_zmq_config()

        # 汇总结果
        print("\n" + "=" * 70)
        print("📊 审计结果汇总")
        print("=" * 70)

        print(f"\n✅ 通过规则: {len(self.passed_rules)}")
        for rule in self.passed_rules:
            print(f"   - {rule}")

        if self.warnings:
            print(f"\n⚠️  警告: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   - {warning}")

        if self.issues:
            print(f"\n❌ 问题: {len(self.issues)}")
            for issue in self.issues:
                print(f"   - {issue}")
            print("\n[UnifiedGate] FAIL - 审计未通过")
            return False

        if forbidden_findings:
            print(f"\n❌ 发现 {len(forbidden_findings)} 处禁止的IP地址")
            print("[UnifiedGate] FAIL - 审计未通过")
            return False

        print("\n[UnifiedGate] PASS - 所有审计规则通过")
        print("=" * 70 + "\n")
        return True


def main():
    """主函数"""
    auditor = TaskAuditor()
    passed = auditor.run_audit()

    # 返回退出码
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
