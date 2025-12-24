#!/usr/bin/env python3
"""
Task #016 Audit Script - Basic Order Execution Service
========================================================

验证 Task #016 的完成情况：
- .env 自动加载修复（MT5Service）
- src/gateway/trade_service.py 文件存在
- TradeService 类已实现
- buy(), sell(), close_position() 方法已实现
- scripts/verify_trade.py 验证脚本存在
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
    """主函数：执行 Task #016 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #016 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/gateway/trade_service.py")
    check_file_exists("src/gateway/mt5_service.py")
    check_file_exists("scripts/verify_trade.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查 .env 自动加载修复（MT5Service）
    # ---------------------------------------------------------
    log_info("检查 .env 自动加载修复...")
    print()

    MT5_KEYWORDS = [
        "from pathlib import Path",  # Path 导入
        "project_root = Path(__file__).resolve().parent.parent.parent",  # 项目根目录
        "env_path = project_root / '.env'",  # .env 路径
        "load_dotenv(dotenv_path=env_path, override=True)",  # 强制加载
    ]

    check_keywords_in_file("src/gateway/mt5_service.py", MT5_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 3. 检查 TradeService 类存在
    # ---------------------------------------------------------
    log_info("检查 TradeService 类...")
    print()

    check_class_exists("src.gateway.trade_service", "TradeService")
    print()

    # ---------------------------------------------------------
    # 4. 检查 buy 方法存在
    # ---------------------------------------------------------
    log_info("检查 buy 方法...")
    print()

    check_method_exists("src.gateway.trade_service", "TradeService", "buy")
    print()

    # ---------------------------------------------------------
    # 5. 检查 sell 方法存在
    # ---------------------------------------------------------
    log_info("检查 sell 方法...")
    print()

    check_method_exists("src.gateway.trade_service", "TradeService", "sell")
    print()

    # ---------------------------------------------------------
    # 6. 检查 close_position 方法存在
    # ---------------------------------------------------------
    log_info("检查 close_position 方法...")
    print()

    check_method_exists("src.gateway.trade_service", "TradeService", "close_position")
    print()

    # ---------------------------------------------------------
    # 7. 检查 get_positions 方法存在
    # ---------------------------------------------------------
    log_info("检查 get_positions 方法...")
    print()

    check_method_exists("src.gateway.trade_service", "TradeService", "get_positions")
    print()

    # ---------------------------------------------------------
    # 8. 检查 trade_service.py 中的核心业务逻辑关键字
    # ---------------------------------------------------------
    log_info("检查核心业务逻辑关键字...")
    print()

    TRADE_KEYWORDS = [
        "class TradeService",  # 类定义
        "def buy",  # buy 方法
        "def sell",  # sell 方法
        "def close_position",  # close_position 方法
        "def get_positions",  # get_positions 方法
        "TRADE_ACTION_DEAL",  # 交易动作
        "ORDER_TYPE_BUY",  # 买单类型
        "ORDER_TYPE_SELL",  # 卖单类型
        "order_send",  # 订单发送
        "positions_get",  # 获取持仓
        "def __init__",  # 初始化方法
        "def __new__",  # 单例模式
        "_instance",  # 单例实例
    ]

    check_keywords_in_file("src/gateway/trade_service.py", TRADE_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 9. 检查 verify_trade.py 中的测试逻辑关键字
    # ---------------------------------------------------------
    log_info("检查验证脚本的测试逻辑...")
    print()

    VERIFY_KEYWORDS = [
        "TradeService",  # 导入服务
        "trade_service.buy",  # 调用 buy 方法
        "trade_service.close_position",  # 调用 close_position 方法
        "trade_service.get_positions",  # 调用 get_positions 方法
        "TEST_VOLUME = 0.01",  # 测试手数
        "import os",  # 导入 os 模块
        'os.getenv("MT5_SYMBOL"',  # 从环境变量读取品种
    ]

    check_keywords_in_file("scripts/verify_trade.py", VERIFY_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 10. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #016 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ .env 自动加载修复（MT5Service）")
    print("  ✅ TradeService 单例类")
    print("  ✅ buy(symbol, volume, ...) 方法实现")
    print("  ✅ sell(symbol, volume, ...) 方法实现")
    print("  ✅ close_position(ticket) 方法实现")
    print("  ✅ get_positions() 方法实现")
    print("  ✅ verify_trade.py 验证脚本")
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
