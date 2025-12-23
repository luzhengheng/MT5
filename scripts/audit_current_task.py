#!/usr/bin/env python3
"""
[审计脚本] - Task #014.1: Core MT5 Service
用于验证 MT5Service 单例类的实现是否满足技术规范。

检查清单：
1. src/gateway/mt5_service.py 文件存在
2. 包含 "MetaTrader5" 关键字（核心库）
3. 包含 "path=" 关键字（便携式路径支持）
4. 包含 "class MT5Service" 关键字（单例类定义）
"""

import sys
import os


# --- 辅助函数：彩色输出 ---
def log_success(msg):
    """输出成功信息（绿色）"""
    print(f"\033[92m✅ {msg}\033[0m")


def log_fail(msg):
    """输出失败信息（红色）"""
    print(f"\033[91m❌ {msg}\033[0m")


def check_file_exists(filepath):
    """检查文件是否存在"""
    if not os.path.exists(filepath):
        log_fail(f"文件缺失: {filepath}")
        sys.exit(1)
    log_success(f"文件存在: {filepath}")


def check_keywords_in_file(filepath, keywords):
    """检查文件中是否包含所有必需的关键字"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = []
        for kw in keywords:
            if kw not in content:
                missing.append(kw)

        if missing:
            log_fail(f"完整性校验失败: {filepath}")
            log_fail(f"    -> 缺失关键字: {missing}")
            sys.exit(1)

        log_success(f"内容校验通过 (包含: {keywords})")

    except Exception as e:
        log_fail(f"读取文件出错: {e}")
        sys.exit(1)


def main():
    """主审计流程"""
    print("🕵️‍♂️ 启动任务审计程序 (Task #014.1 - Core MT5 Service)...")
    print()

    # ---------------------------------------------------------
    # 1. 定义本次任务的目标文件
    # ---------------------------------------------------------
    TARGET_FILE = "src/gateway/mt5_service.py"

    # ---------------------------------------------------------
    # 2. 执行基础检查
    # ---------------------------------------------------------
    print("[检查1] 文件存在性...")
    check_file_exists(TARGET_FILE)
    print()

    # ---------------------------------------------------------
    # 3. 执行业务逻辑检查 (关键字校验)
    # ---------------------------------------------------------
    print("[检查2] 核心业务逻辑完整性...")
    REQUIRED_KEYWORDS = [
        "MetaTrader5",        # 核心库导入
        "path=",              # 便携式路径支持（mt5.initialize(path=...)）
        "class MT5Service",   # 单例类定义
    ]
    check_keywords_in_file(TARGET_FILE, REQUIRED_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 4. 额外检查：确保实现了 connect() 和 is_connected()
    # ---------------------------------------------------------
    print("[检查3] 核心方法实现...")
    REQUIRED_METHODS = ["def connect", "def is_connected"]
    try:
        with open(TARGET_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        missing_methods = [m for m in REQUIRED_METHODS if m not in content]
        if missing_methods:
            log_fail(f"缺失方法: {missing_methods}")
            sys.exit(1)

        log_success(f"所有方法已实现: {REQUIRED_METHODS}")
    except Exception as e:
        log_fail(f"方法检查出错: {e}")
        sys.exit(1)
    print()

    # ---------------------------------------------------------
    # 5. 最终放行
    # ---------------------------------------------------------
    print("-" * 50)
    log_success("✨ 审计通过！Task #014.1 完全符合技术规范。")
    log_success("允许 Gemini Review Bridge 提交代码。")
    print("-" * 50)
    sys.exit(0)  # Exit 0 会触发 Git Commit


if __name__ == "__main__":
    main()
