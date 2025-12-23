#!/usr/bin/env python3
"""
审计脚本 - Task #014.2: Verify MT5 Connectivity
验证 MT5 连接验证脚本是否正确实现
"""
import sys
import os

# --- 辅助函数 ---
def log_success(msg):
    print(f"\033[92m✅ {msg}\033[0m")

def log_fail(msg):
    print(f"\033[91m❌ {msg}\033[0m")

def check_file_exists(filepath):
    """检查文件是否存在"""
    if not os.path.exists(filepath):
        log_fail(f"文件缺失: {filepath}")
        sys.exit(1)
    log_success(f"文件存在: {filepath}")

def check_keywords_in_file(filepath, keywords):
    """检查文件中是否包含核心关键字"""
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
    print("🕵️‍♂️ 启动任务审计程序 (Task #014.2 - Verify MT5 Connectivity)...")
    print()

    # ---------------------------------------------------------
    # 1. 验证 MT5 连接验证脚本存在
    # ---------------------------------------------------------
    print("[检查1] 验证脚本存在性...")
    TARGET_FILE = "scripts/verify_mt5_connection.py"
    check_file_exists(TARGET_FILE)
    print()

    # ---------------------------------------------------------
    # 2. 验证脚本包含必要的导入和逻辑
    # ---------------------------------------------------------
    print("[检查2] 验证脚本内容完整性...")
    REQUIRED_KEYWORDS = [
        "from src.gateway.mt5_service import MT5Service",  # 正确导入
        "MT5Service()",                                     # 实例化
        "connect()",                                        # 连接方法
        "is_connected()",                                   # 状态检查
    ]
    check_keywords_in_file(TARGET_FILE, REQUIRED_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 3. 验证 MT5Service 源文件存在
    # ---------------------------------------------------------
    print("[检查3] MT5Service 源文件...")
    MT5_SERVICE_FILE = "src/gateway/mt5_service.py"
    check_file_exists(MT5_SERVICE_FILE)
    print()

    # ---------------------------------------------------------
    # 4. 验证 MT5Service 包含核心方法
    # ---------------------------------------------------------
    print("[检查4] MT5Service 核心方法...")
    MT5_KEYWORDS = [
        "class MT5Service",
        "def connect",
        "def is_connected",
        "MetaTrader5"
    ]
    check_keywords_in_file(MT5_SERVICE_FILE, MT5_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 5. 最终放行
    # ---------------------------------------------------------
    print("-" * 50)
    log_success("✨ 审计通过！Task #014.2 符合技术规范。")
    log_success("允许 Gemini Review Bridge 提交代码。")
    print("-" * 50)
    sys.exit(0)

if __name__ == "__main__":
    main()
