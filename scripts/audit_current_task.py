#!/usr/bin/env python3
"""
Task #020 Audit Script - Integrated Trading Bot Loop
======================================================

验证 Task #020 的完成情况：
- TradingBot 类实现（src/bot/trading_bot.py）
- run_cycle() 方法
- 依赖注入（MT5Service, MarketDataService, TradeService, TechnicalIndicators, SignalEngine）
- 完整工作流：数据获取 → 指标计算 → 信号生成 → 交易执行
- verify_bot_cycle.py 验证脚本
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
    """主函数：执行 Task #020 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #020 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/bot/trading_bot.py")
    check_file_exists("scripts/verify_bot_cycle.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查 TradingBot 类存在
    # ---------------------------------------------------------
    log_info("检查 TradingBot 类...")
    print()

    check_class_exists("src.bot.trading_bot", "TradingBot")
    print()

    # ---------------------------------------------------------
    # 3. 检查 run_cycle 方法存在
    # ---------------------------------------------------------
    log_info("检查核心方法...")
    print()

    check_method_exists("src.bot.trading_bot", "TradingBot", "run_cycle")
    print()

    # ---------------------------------------------------------
    # 4. 检查依赖注入
    # ---------------------------------------------------------
    log_info("检查依赖注入...")
    print()

    DEPENDENCY_KEYWORDS = [
        "from src.gateway.mt5_service import MT5Service",
        "from src.gateway.market_data import MarketDataService",
        "from src.gateway.trade_service import TradeService",
        "from src.strategy.indicators import TechnicalIndicators",
        "from src.strategy.signal_engine import SignalEngine",
        "def __init__",
        "mt5_service: Optional[MT5Service]",
        "market_data: Optional[MarketDataService]",
        "trade_service: Optional[TradeService]",
        "indicators: Optional[TechnicalIndicators]",
        "signal_engine: Optional[SignalEngine]"
    ]

    check_keywords_in_file("src/bot/trading_bot.py", DEPENDENCY_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 5. 检查 run_cycle 工作流
    # ---------------------------------------------------------
    log_info("检查 run_cycle 工作流...")
    print()

    WORKFLOW_KEYWORDS = [
        "def run_cycle",
        "symbol: str",
        "timeframe: str",
        "strategy_name: str",
        "self.market_data.get_candles",
        "self.indicators.calculate_sma",
        "self.signal_engine.apply_strategy",
        "latest_signal",
        "if latest_signal == 1:",
        "self.trade_service.buy",
        "elif latest_signal == -1:",
        "self.trade_service.sell"
    ]

    check_keywords_in_file("src/bot/trading_bot.py", WORKFLOW_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 6. 检查返回值结构
    # ---------------------------------------------------------
    log_info("检查返回值结构...")
    print()

    RETURN_KEYWORDS = [
        "'success':",
        "'step':",
        "'data_fetched':",
        "'indicators_calculated':",
        "'signal_generated':",
        "'signal_value':",
        "'trade_executed':",
        "'trade_result':",
        "'message':"
    ]

    check_keywords_in_file("src/bot/trading_bot.py", RETURN_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 7. 检查错误处理
    # ---------------------------------------------------------
    log_info("检查错误处理...")
    print()

    ERROR_HANDLING_KEYWORDS = [
        "try:",
        "except Exception as e:",
        "logger.error",
        "if df is None",
        "if not self.mt5_service.is_connected()"
    ]

    check_keywords_in_file("src/bot/trading_bot.py", ERROR_HANDLING_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 8. 检查 verify_bot_cycle.py 验证逻辑
    # ---------------------------------------------------------
    log_info("检查 verify_bot_cycle.py 验证逻辑...")
    print()

    VERIFY_KEYWORDS = [
        "from src.bot.trading_bot import TradingBot",
        "bot = TradingBot()",
        "bot.run_cycle",
        "result['data_fetched']",
        "result['indicators_calculated']",
        "result['signal_generated']",
        "result['success']"
    ]

    check_keywords_in_file("scripts/verify_bot_cycle.py", VERIFY_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 9. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #020 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ TradingBot 类实现")
    print("  ✅ run_cycle(symbol, timeframe, strategy_name) 方法")
    print("  ✅ 依赖注入（5个服务组件）")
    print("  ✅ 完整工作流：数据 → 指标 → 信号 → 交易")
    print("  ✅ 信号处理逻辑（1:买入, -1:卖出, 0:持有）")
    print("  ✅ 错误处理和日志记录")
    print("  ✅ 结构化返回值（9个字段）")
    print("  ✅ verify_bot_cycle.py 单周期验证脚本")
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
