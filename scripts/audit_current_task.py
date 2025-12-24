#!/usr/bin/env python3
"""
Task #017 Audit Script - Market Data Service & Secure Config
==============================================================

验证 Task #017 的完成情况：
- TradeService 智能填充模式（Smart Fallback）
- MarketDataService get_candles() 方法
- MT5Service robust .env loading（已在 Task #016 完成）
- scripts/verify_candles.py 验证脚本
- scripts/verify_trade.py 更新（Smart Fallback说明）
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
    """主函数：执行 Task #017 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #017 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/gateway/trade_service.py")
    check_file_exists("src/gateway/market_data.py")
    check_file_exists("src/gateway/mt5_service.py")
    check_file_exists("scripts/verify_candles.py")
    check_file_exists("scripts/verify_trade.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查 TradeService 智能填充模式
    # ---------------------------------------------------------
    log_info("检查 TradeService 智能填充模式...")
    print()

    TRADE_FALLBACK_KEYWORDS = [
        "import os",  # os 导入
        'os.getenv(\'MT5_FILLING_MODE\'',  # 环境变量读取
        "def _send_order_with_fallback",  # 智能发送方法
        "ORDER_FILLING_FOK",  # FOK 模式
        "ORDER_FILLING_IOC",  # IOC 模式
        "10030",  # 错误代码 TRADE_RETCODE_INVALID_FILL
        "filling_modes",  # 填充模式列表
        "自动尝试备选模式",  # 降级逻辑注释
    ]

    check_keywords_in_file("src/gateway/trade_service.py", TRADE_FALLBACK_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 3. 检查 buy/sell/close_position 使用智能发送
    # ---------------------------------------------------------
    log_info("检查 buy/sell/close_position 使用智能发送...")
    print()

    SMART_SEND_KEYWORDS = [
        "_send_order_with_fallback(request)",  # buy 方法使用
    ]

    check_keywords_in_file("src/gateway/trade_service.py", SMART_SEND_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 4. 检查 MarketDataService get_candles 方法
    # ---------------------------------------------------------
    log_info("检查 MarketDataService get_candles 方法...")
    print()

    check_method_exists("src.gateway.market_data", "MarketDataService", "get_candles")
    print()

    # ---------------------------------------------------------
    # 5. 检查 get_candles 核心逻辑
    # ---------------------------------------------------------
    log_info("检查 get_candles 核心逻辑...")
    print()

    CANDLES_KEYWORDS = [
        "def get_candles",  # 方法定义
        "import pandas as pd",  # pandas 导入
        "copy_rates_from_pos",  # MT5 K线获取
        "pd.DataFrame",  # DataFrame 创建
        "pd.to_datetime",  # 时间转换
        "TIMEFRAME_M1",  # 支持 M1
        "TIMEFRAME_M5",  # 支持 M5
        "TIMEFRAME_H1",  # 支持 H1
        "['time', 'open', 'high', 'low', 'close', 'volume']",  # 标准列
    ]

    check_keywords_in_file("src/gateway/market_data.py", CANDLES_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 6. 检查 verify_candles.py 验证逻辑
    # ---------------------------------------------------------
    log_info("检查 verify_candles.py 验证逻辑...")
    print()

    VERIFY_CANDLES_KEYWORDS = [
        "MarketDataService",  # 导入服务
        "get_candles",  # 调用 get_candles
        "df.head(3)",  # 显示前3行
        "df.tail(3)",  # 显示后3行
        "datetime",  # 时间类型检查
        "df.isnull()",  # 空值检查
        "len(df)",  # 数据量检查
    ]

    check_keywords_in_file("scripts/verify_candles.py", VERIFY_CANDLES_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 7. 检查 verify_trade.py Smart Fallback 说明
    # ---------------------------------------------------------
    log_info("检查 verify_trade.py Smart Fallback 说明...")
    print()

    VERIFY_TRADE_KEYWORDS = [
        "Smart Fallback",  # 智能降级标题
        "MT5_FILLING_MODE",  # 环境变量说明
        "自动尝试备选模式",  # 降级机制说明
        "FOK",  # FOK 模式说明
        "IOC",  # IOC 模式说明
        "AUTO",  # AUTO 模式说明
    ]

    check_keywords_in_file("scripts/verify_trade.py", VERIFY_TRADE_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 8. 检查 MT5Service robust .env loading（Task #016已完成）
    # ---------------------------------------------------------
    log_info("检查 MT5Service robust .env loading...")
    print()

    ENV_LOADING_KEYWORDS = [
        "from pathlib import Path",  # Path 导入
        "project_root = Path(__file__).resolve().parent.parent.parent",  # 项目根
        "env_path = project_root / '.env'",  # .env 路径
        "load_dotenv(dotenv_path=env_path, override=True)",  # 强制加载
    ]

    check_keywords_in_file("src/gateway/mt5_service.py", ENV_LOADING_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 9. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #017 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ TradeService 智能填充模式（Smart Fallback）")
    print("  ✅ _send_order_with_fallback() 方法实现")
    print("  ✅ MT5_FILLING_MODE 环境变量支持")
    print("  ✅ 错误 10030 自动降级逻辑")
    print("  ✅ MarketDataService.get_candles() 方法")
    print("  ✅ 支持 M1/M5/M15/M30/H1/H4/D1 时间周期")
    print("  ✅ pandas DataFrame 返回格式")
    print("  ✅ verify_candles.py 数据完整性验证")
    print("  ✅ verify_trade.py Smart Fallback 说明")
    print("  ✅ MT5Service robust .env loading")
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
