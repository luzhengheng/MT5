#!/usr/bin/env python3
"""
Task #015 Audit Script - Windows Deployment & MT5 Stream
==========================================================

验证 Task #015 的完成情况：
- src/gateway/market_data.py 文件存在
- MarketDataService 类已实现
- get_tick() 方法已实现
- scripts/verify_stream.py 验证脚本存在
"""

import sys
import os
import inspect
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


def check_class_exists(module_path, class_name):
    """检查模块中是否存在指定的类"""
    try:
        # 动态导入模块
        spec = __import__(module_path, fromlist=[class_name])
        if not hasattr(spec, class_name):
            log_fail(f"类 {class_name} 不存在于 {module_path}")
            sys.exit(1)
        log_success(f"类存在: {module_path}.{class_name}")
    except ImportError as e:
        log_fail(f"模块导入失败: {module_path} - {str(e)}")
        sys.exit(1)
    except Exception as e:
        log_fail(f"检查类时发生异常: {str(e)}")
        sys.exit(1)


def check_method_exists(module_path, class_name, method_name):
    """检查类中是否存在指定的方法"""
    try:
        # 动态导入模块和类
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)

        if not hasattr(cls, method_name):
            log_fail(f"方法 {method_name} 不存在于 {class_name}")
            sys.exit(1)

        # 检查是否真的是方法
        method = getattr(cls, method_name)
        if not callable(method):
            log_fail(f"{method_name} 不是可调用的方法")
            sys.exit(1)

        log_success(f"方法存在: {class_name}.{method_name}()")

    except Exception as e:
        log_fail(f"检查方法失败: {str(e)}")
        sys.exit(1)


def main():
    """主函数：执行 Task #015 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #015 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/gateway/market_data.py")
    check_file_exists("scripts/verify_stream.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查 MarketDataService 类存在
    # ---------------------------------------------------------
    log_info("检查 MarketDataService 类...")
    print()

    check_class_exists("src.gateway.market_data", "MarketDataService")
    print()

    # ---------------------------------------------------------
    # 3. 检查 get_tick 方法存在
    # ---------------------------------------------------------
    log_info("检查 get_tick 方法...")
    print()

    check_method_exists("src.gateway.market_data", "MarketDataService", "get_tick")
    print()

    # ---------------------------------------------------------
    # 4. 检查 market_data.py 中的核心业务逻辑关键字
    # ---------------------------------------------------------
    log_info("检查核心业务逻辑关键字...")
    print()

    REQUIRED_KEYWORDS = [
        "class MarketDataService",  # 类定义
        "def get_tick",  # get_tick 方法
        "symbol_info_tick",  # 核心调用：获取 tick 数据
        "symbol_select",  # 核心调用：确保符号可见性
        "is_connected",  # 连接检查
        "MT5Service",  # MT5 服务引用
        "def __init__",  # 初始化方法
        "def __new__",  # 单例模式
        "_instance",  # 单例实例
    ]

    check_keywords_in_file("src/gateway/market_data.py", REQUIRED_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 5. 检查 verify_stream.py 中的测试逻辑关键字
    # ---------------------------------------------------------
    log_info("检查验证脚本的测试逻辑...")
    print()

    VERIFY_KEYWORDS = [
        "MarketDataService",  # 导入服务
        "get_tick",  # 调用 get_tick 方法
        "import os",  # 导入 os 模块
        'os.getenv("MT5_SYMBOL"',  # 从环境变量读取品种
        "EURUSD",  # 默认品种
        "loop_count = 5",  # 循环次数
        "time.sleep",  # 延迟 1 秒
    ]

    check_keywords_in_file("scripts/verify_stream.py", VERIFY_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 6. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #015 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ MarketDataService 单例类")
    print("  ✅ get_tick(symbol) 方法实现")
    print("  ✅ Market Watch 符号可见性处理")
    print("  ✅ verify_stream.py 验证脚本")
    print("  ✅ MT5_SYMBOL 环境变量支持（可配置品种代码）")
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
