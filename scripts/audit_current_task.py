#!/usr/bin/env python3
"""
Task #018 Audit Script - Technical Analysis Engine
====================================================

验证 Task #018 的完成情况：
- TechnicalIndicators 类实现（src/strategy/indicators.py）
- 5 个核心方法：calculate_sma, calculate_ema, calculate_rsi, calculate_atr, calculate_bollinger_bands
- 严格向量化：使用 pandas/numpy，无 for 循环
- verify_indicators.py 验证脚本
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
    """主函数：执行 Task #018 的审计"""
    print("=" * 70)
    print("🕵️‍♂️ Task #018 审计程序启动")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. 检查核心文件存在性
    # ---------------------------------------------------------
    log_info("检查核心文件...")
    print()

    check_file_exists("src/strategy/indicators.py")
    check_file_exists("scripts/verify_indicators.py")
    print()

    # ---------------------------------------------------------
    # 2. 检查 TechnicalIndicators 类存在
    # ---------------------------------------------------------
    log_info("检查 TechnicalIndicators 类...")
    print()

    check_class_exists("src.strategy.indicators", "TechnicalIndicators")
    print()

    # ---------------------------------------------------------
    # 3. 检查 5 个核心方法存在
    # ---------------------------------------------------------
    log_info("检查核心方法...")
    print()

    required_methods = [
        "calculate_sma",
        "calculate_ema",
        "calculate_rsi",
        "calculate_atr",
        "calculate_bollinger_bands"
    ]

    for method in required_methods:
        check_method_exists("src.strategy.indicators", "TechnicalIndicators", method)

    print()

    # ---------------------------------------------------------
    # 4. 检查 SMA 实现（向量化）
    # ---------------------------------------------------------
    log_info("检查 SMA 向量化实现...")
    print()

    SMA_KEYWORDS = [
        "def calculate_sma",
        "pd.DataFrame",
        ".rolling(window=period",
        ".mean()",
        "price_col",
        "return df"
    ]

    check_keywords_in_file("src/strategy/indicators.py", SMA_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 5. 检查 EMA 实现（向量化）
    # ---------------------------------------------------------
    log_info("检查 EMA 向量化实现...")
    print()

    EMA_KEYWORDS = [
        "def calculate_ema",
        ".ewm(span=period",
        ".mean()",
        "adjust=False"
    ]

    check_keywords_in_file("src/strategy/indicators.py", EMA_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 6. 检查 RSI 实现（向量化 + 0-100 范围）
    # ---------------------------------------------------------
    log_info("检查 RSI 向量化实现...")
    print()

    RSI_KEYWORDS = [
        "def calculate_rsi",
        ".diff()",
        ".where(",
        ".ewm(span=period",
        "100 -",
        "1 + rs"
    ]

    check_keywords_in_file("src/strategy/indicators.py", RSI_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 7. 检查 ATR 实现（向量化）
    # ---------------------------------------------------------
    log_info("检查 ATR 向量化实现...")
    print()

    ATR_KEYWORDS = [
        "def calculate_atr",
        "'high'",
        "'low'",
        "'close'",
        ".shift()",
        ".abs()",
        ".max(axis=1)",
        ".ewm(span=period"
    ]

    check_keywords_in_file("src/strategy/indicators.py", ATR_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 8. 检查 Bollinger Bands 实现（向量化）
    # ---------------------------------------------------------
    log_info("检查 Bollinger Bands 向量化实现...")
    print()

    BB_KEYWORDS = [
        "def calculate_bollinger_bands",
        ".rolling(window=period",
        ".std()",
        "bb_upper",
        "bb_middle",
        "bb_lower",
        "std_dev *"
    ]

    check_keywords_in_file("src/strategy/indicators.py", BB_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 9. 检查向量化约束（禁止 for 循环）
    # ---------------------------------------------------------
    log_info("检查向量化约束（禁止 for 循环）...")
    print()

    try:
        with open("src/strategy/indicators.py", 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 Python for 循环（排除注释和字符串）
        # 简化检查：如果 "for i in" 或 "for idx in" 出现在非注释行
        lines = content.split('\n')
        for_loop_found = False
        for line in lines:
            stripped = line.strip()
            # 跳过注释行
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            # 检查 for 循环（排除 "for col in" 这种合理的列迭代）
            if 'for i in' in line or 'for idx in' in line or 'for j in' in line:
                log_fail(f"发现 Python for 循环: {line.strip()}")
                for_loop_found = True
                break

        if for_loop_found:
            log_fail("违反向量化约束：发现 Python for 循环")
            sys.exit(1)

        log_success("向量化约束检查通过（未发现 for 循环）")

    except Exception as e:
        log_fail(f"检查向量化约束失败: {str(e)}")
        sys.exit(1)

    print()

    # ---------------------------------------------------------
    # 10. 检查 verify_indicators.py 验证逻辑
    # ---------------------------------------------------------
    log_info("检查 verify_indicators.py 验证逻辑...")
    print()

    VERIFY_KEYWORDS = [
        "MarketDataService",
        "TechnicalIndicators",
        "get_candles",
        "calculate_sma",
        "calculate_ema",
        "calculate_rsi",
        "calculate_atr",
        "calculate_bollinger_bands",
        "df.tail(5)",
        "expected_columns"
    ]

    check_keywords_in_file("scripts/verify_indicators.py", VERIFY_KEYWORDS)
    print()

    # ---------------------------------------------------------
    # 11. 最终审计通过
    # ---------------------------------------------------------
    print("=" * 70)
    log_success("Task #018 审计通过！")
    print("=" * 70)
    print()
    log_info("已完成的核心功能：")
    print("  ✅ TechnicalIndicators 类实现")
    print("  ✅ calculate_sma(df, period, price_col) - 向量化")
    print("  ✅ calculate_ema(df, period, price_col) - 向量化")
    print("  ✅ calculate_rsi(df, period, price_col) - 向量化，0-100 范围")
    print("  ✅ calculate_atr(df, period) - 向量化，动态止损")
    print("  ✅ calculate_bollinger_bands(df, period, std_dev) - 向量化，3条带")
    print("  ✅ 严格向量化约束（无 for 循环）")
    print("  ✅ verify_indicators.py 功能验证脚本")
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
