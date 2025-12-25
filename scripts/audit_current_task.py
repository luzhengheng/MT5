#!/usr/bin/env python3
"""
Task #019 Audit Script - Signal Generation Engine
===================================================

验证 Task #019 的完成情况：
- SignalEngine 类实现（src/strategy/signal_engine.py）
- apply_strategy() 方法
- MA Crossover 策略逻辑
- RSI Reversion 策略逻辑
- 严格向量化：无行迭代
- verify_signals.py 验证脚本
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
    """主函数：执行 Task #019 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #019 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/strategy/signal_engine.py")
    check_file_exists("scripts/verify_signals.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查 SignalEngine 类存在
    # ---------------------------------------------------------
    log_info("检查 SignalEngine 类...")
    print()

    check_class_exists("src.strategy.signal_engine", "SignalEngine")
    print()

    # ---------------------------------------------------------
    # 3. 检查 apply_strategy 方法存在
    # ---------------------------------------------------------
    log_info("检查核心方法...")
    print()

    check_method_exists("src.strategy.signal_engine", "SignalEngine", "apply_strategy")
    print()

    # ---------------------------------------------------------
    # 4. 检查 MA Crossover 策略实现
    # ---------------------------------------------------------
    log_info("检查 MA Crossover 策略实现...")
    print()

    MA_CROSSOVER_KEYWORDS = [
        "def _ma_crossover_strategy",
        ".shift(1)",
        "golden_cross",
        "death_cross",
        "df['signal'] = 0",
        "df.loc[golden_cross, 'signal'] = 1",
        "df.loc[death_cross, 'signal'] = -1"
    ]

    check_keywords_in_file("src/strategy/signal_engine.py", MA_CROSSOVER_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 5. 检查 RSI Reversion 策略实现
    # ---------------------------------------------------------
    log_info("检查 RSI Reversion 策略实现...")
    print()

    RSI_REVERSION_KEYWORDS = [
        "def _rsi_reversion_strategy",
        "OVERBOUGHT = 70",
        "OVERSOLD = 30",
        "df['signal'] = 0",
        "df.loc[df[rsi_col] > OVERBOUGHT, 'signal'] = -1",
        "df.loc[df[rsi_col] < OVERSOLD, 'signal'] = 1"
    ]

    check_keywords_in_file("src/strategy/signal_engine.py", RSI_REVERSION_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 6. 检查信号值约束（1, -1, 0）
    # ---------------------------------------------------------
    log_info("检查信号值约束...")
    print()

    SIGNAL_VALUES_KEYWORDS = [
        "'signal'] = 0",
        "'signal'] = 1",
        "'signal'] = -1"
    ]

    check_keywords_in_file("src/strategy/signal_engine.py", SIGNAL_VALUES_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 7. 检查向量化约束（禁止行迭代）
    # ---------------------------------------------------------
    log_info("检查向量化约束（禁止行迭代）...")
    print()

    try:
        with open("src/strategy/signal_engine.py", 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 iterrows 或 for 循环（排除注释）
        lines = content.split('\n')
        iteration_found = False
        for line in lines:
            stripped = line.strip()
            # 跳过注释行
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            # 检查行迭代
            if 'iterrows' in line or 'for i in' in line or 'for idx in' in line:
                log_fail(f"发现行迭代: {line.strip()}")
                iteration_found = True
                break

        if iteration_found:
            log_fail("违反向量化约束：发现行迭代")
            sys.exit(1)

        log_success("向量化约束检查通过（未发现行迭代）")

    except Exception as e:
        log_fail(f"检查向量化约束失败: {str(e)}")
        sys.exit(1)

    print()

    # ---------------------------------------------------------
    # 8. 检查 verify_signals.py 验证逻辑
    # ---------------------------------------------------------
    log_info("检查 verify_signals.py 验证逻辑...")
    print()

    VERIFY_KEYWORDS = [
        "MarketDataService",
        "TechnicalIndicators",
        "SignalEngine",
        "get_candles",
        "calculate_sma",
        "calculate_rsi",
        "apply_strategy",
        "strategy_name='ma_crossover'",
        "strategy_name='rsi_reversion'",
        "['signal'] != 0",
        ".tail("
    ]

    check_keywords_in_file("scripts/verify_signals.py", VERIFY_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 9. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #019 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ SignalEngine 类实现")
    print("  ✅ apply_strategy(df, strategy_name) 方法")
    print("  ✅ MA Crossover 策略（金叉买入，死叉卖出）")
    print("  ✅ RSI Reversion 策略（超买卖出，超卖买入）")
    print("  ✅ 信号值约束（1, -1, 0）")
    print("  ✅ 严格向量化（无行迭代）")
    print("  ✅ verify_signals.py 功能验证脚本")
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
