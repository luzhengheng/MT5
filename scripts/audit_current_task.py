#!/usr/bin/env python3
"""
Task #021 Audit Script - Live Trading Runner
==============================================

验证 Task #021 的完成情况：
- src/main.py 主入口文件
- 连续交易循环（while True）
- 配置加载（环境变量）
- KeyboardInterrupt 处理（优雅退出）
- Exception 处理（错误重试）
- MT5 断开连接逻辑
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径（确保审计脚本在任何目录下都能运行）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 辅助函数：带颜色的输出 ---
def log_success(msg):
    print(f"\033[92m✅ {msg}\033[0m")


def log_fail(msg):
    print(f"\033[91m❌ {msg}\033[0m")


def log_info(msg):
    print(f"\033[94mℹ️  {msg}\033[0m")


def check_file_exists(filepath):
    """检查文件是否存在"""
    if not os.path.exists(filepath):
        log_fail(f"文件缺失: {filepath}")
        sys.exit(1)
    log_success(f"文件存在: {filepath}")


def check_keywords_in_file(filepath, keywords):
    """检查文件中是否包含核心业务逻辑关键字"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = []
        for kw in keywords:
            if kw not in content:
                missing.append(kw)

        if missing:
            log_fail(f"内容校验失败: {filepath}")
            log_fail(f"    -> 缺失关键字: {missing}")
            sys.exit(1)

        log_success(f"内容校验通过 (包含必需关键字)")

    except Exception as e:
        log_fail(f"读取文件出错: {e}")
        sys.exit(1)


def main():
    """主函数：执行 Task #021 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #021 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/main.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查导入依赖
    # ---------------------------------------------------------
    log_info("检查导入依赖...")
    print()

    IMPORT_KEYWORDS = [
        "from src.bot.trading_bot import TradingBot",
        "from src.gateway.mt5_service import MT5Service",
        "import time",
        "import logging"
    ]

    check_keywords_in_file("src/main.py", IMPORT_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 3. 检查配置加载逻辑
    # ---------------------------------------------------------
    log_info("检查配置加载逻辑...")
    print()

    CONFIG_KEYWORDS = [
        "def load_config",
        "os.getenv('MT5_SYMBOL'",
        "os.getenv('MT5_TIMEFRAME'",
        "os.getenv('TRADING_STRATEGY'",
        "os.getenv('TRADING_VOLUME'",
        "os.getenv('TRADING_INTERVAL'"
    ]

    check_keywords_in_file("src/main.py", CONFIG_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 4. 检查 MT5 连接初始化
    # ---------------------------------------------------------
    log_info("检查 MT5 连接初始化...")
    print()

    MT5_KEYWORDS = [
        "mt5_service = MT5Service()",
        "mt5_service.connect()",
        "if not mt5_service.connect():"
    ]

    check_keywords_in_file("src/main.py", MT5_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 5. 检查 TradingBot 初始化
    # ---------------------------------------------------------
    log_info("检查 TradingBot 初始化...")
    print()

    BOT_KEYWORDS = [
        "bot = TradingBot()"
    ]

    check_keywords_in_file("src/main.py", BOT_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 6. 检查无限循环
    # ---------------------------------------------------------
    log_info("检查无限循环...")
    print()

    LOOP_KEYWORDS = [
        "while True:",
        "bot.run_cycle"
    ]

    check_keywords_in_file("src/main.py", LOOP_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 7. 检查 KeyboardInterrupt 处理
    # ---------------------------------------------------------
    log_info("检查 KeyboardInterrupt 处理...")
    print()

    KEYBOARD_KEYWORDS = [
        "except KeyboardInterrupt:",
        "mt5_service.disconnect()"
    ]

    check_keywords_in_file("src/main.py", KEYBOARD_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 8. 检查异常处理
    # ---------------------------------------------------------
    log_info("检查异常处理...")
    print()

    EXCEPTION_KEYWORDS = [
        "try:",
        "except Exception as e:",
        "logger.error"
    ]

    check_keywords_in_file("src/main.py", EXCEPTION_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 9. 检查循环间隔
    # ---------------------------------------------------------
    log_info("检查循环间隔...")
    print()

    SLEEP_KEYWORDS = [
        "time.sleep"
    ]

    check_keywords_in_file("src/main.py", SLEEP_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 10. 检查日志配置
    # ---------------------------------------------------------
    log_info("检查日志配置...")
    print()

    LOGGING_KEYWORDS = [
        "logging.basicConfig",
        "logging.FileHandler",
        "logger = logging.getLogger(__name__)"
    ]

    check_keywords_in_file("src/main.py", LOGGING_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 11. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #021 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ src/main.py 主入口文件")
    print("  ✅ 配置加载（6个环境变量）")
    print("  ✅ MT5Service 初始化和连接")
    print("  ✅ TradingBot 初始化")
    print("  ✅ 无限交易循环（while True）")
    print("  ✅ bot.run_cycle() 调用")
    print("  ✅ KeyboardInterrupt 优雅退出")
    print("  ✅ Exception 错误重试")
    print("  ✅ 循环间隔（time.sleep）")
    print("  ✅ 日志配置（文件 + 控制台）")
    print()

    sys.exit(0)  # 返回 0 表示审计通过


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_fail(f"审计程序异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
