"""
工单 #010.5 - Kelly Criterion 修正验证测试

测试场景：
1. 旧公式：P=0.45, b=1 (隐含) -> kelly_pct < 0 -> 仓位 = 0
2. 新公式：P=0.45, b=2.0 -> f* = 0.175 -> 仓位 > 0
"""

import sys
import numpy as np


def test_old_kelly_formula():
    """
    测试旧的 Kelly 公式（错误版本）

    假设：b=1 (隐含)
    """
    p_win = 0.45
    normalized_vol = 0.02  # 2% 波动率

    # 旧公式
    kelly_pct = (p_win - 0.5) / normalized_vol

    print("=" * 60)
    print("旧 Kelly 公式测试（错误版本）")
    print("=" * 60)
    print(f"胜率 P: {p_win:.2%}")
    print(f"波动率: {normalized_vol:.2%}")
    print(f"Kelly%: {kelly_pct:.4f}")
    print(f"结果: {'🚨 负数，仓位会被过滤为 0' if kelly_pct < 0 else '✅ 正数'}")
    print()

    return kelly_pct


def test_new_kelly_formula():
    """
    测试新的通用 Kelly 公式（正确版本）

    适用于低胜率高赔率策略
    """
    p_win = 0.45
    b = 2.0  # 盈亏比 2:1
    kelly_fraction = 0.25  # 四分之一 Kelly

    # 新公式
    kelly_f = (p_win * (b + 1) - 1) / b
    risk_pct = kelly_f * kelly_fraction

    print("=" * 60)
    print("新 Kelly 公式测试（通用版本）")
    print("=" * 60)
    print(f"胜率 P: {p_win:.2%}")
    print(f"赔率 b: {b:.1f}")
    print(f"Kelly f*: {kelly_f:.4f}")
    print(f"风险比例 (f* × {kelly_fraction}): {risk_pct:.4f}")
    print(f"结果: {'🚨 负数或零' if kelly_f <= 0 else '✅ 正数，会产生仓位'}")
    print()

    # 计算示例仓位
    account_value = 100000  # 10万美元
    current_price = 100
    atr = 2.0
    stop_loss_multiplier = 2.0

    risk_amount = account_value * risk_pct
    risk_per_share = atr * stop_loss_multiplier
    target_shares = risk_amount / risk_per_share
    position_value = target_shares * current_price
    position_pct = position_value / account_value

    print(f"示例计算（账户价值 ${account_value:,}）:")
    print(f"  - 目标风险金额: ${risk_amount:,.2f}")
    print(f"  - 单股风险 (ATR×{stop_loss_multiplier}): ${risk_per_share:.2f}")
    print(f"  - 目标股数: {target_shares:.0f}")
    print(f"  - 持仓价值: ${position_value:,.2f}")
    print(f"  - 持仓占比: {position_pct:.2%}")
    print()

    return kelly_f


def test_edge_cases():
    """
    测试边界情况
    """
    print("=" * 60)
    print("边界情况测试")
    print("=" * 60)

    test_cases = [
        {"p": 0.33, "b": 2.0, "desc": "胜率 33%, 赔率 2:1（期望值为 0）"},
        {"p": 0.40, "b": 2.0, "desc": "胜率 40%, 赔率 2:1（略低于阈值）"},
        {"p": 0.45, "b": 2.0, "desc": "胜率 45%, 赔率 2:1（典型趋势策略）"},
        {"p": 0.50, "b": 1.5, "desc": "胜率 50%, 赔率 1.5:1（中性）"},
        {"p": 0.60, "b": 1.0, "desc": "胜率 60%, 赔率 1:1（高胜率低赔率）"},
    ]

    for case in test_cases:
        p = case["p"]
        b = case["b"]
        desc = case["desc"]

        kelly_f = (p * (b + 1) - 1) / b
        expected_value = p * b - (1 - p)

        status = "✅" if kelly_f > 0 else "🚨"
        print(f"{status} {desc}")
        print(f"   Kelly f*: {kelly_f:+.4f} | 期望值: {expected_value:+.4f}")
        print()


def test_comparison():
    """
    对比旧公式 vs 新公式
    """
    print("=" * 60)
    print("旧公式 vs 新公式对比（典型趋势策略）")
    print("=" * 60)

    p = 0.45
    b = 2.0
    normalized_vol = 0.02

    # 旧公式
    old_kelly = (p - 0.5) / normalized_vol

    # 新公式
    new_kelly = (p * (b + 1) - 1) / b

    print(f"胜率: {p:.2%}, 赔率: {b:.1f}, 波动率: {normalized_vol:.2%}")
    print()
    print(f"旧公式结果: {old_kelly:+.4f} {'🚨 会被过滤' if old_kelly <= 0 else '✅'}")
    print(f"新公式结果: {new_kelly:+.4f} {'🚨 会被过滤' if new_kelly <= 0 else '✅'}")
    print()

    if old_kelly <= 0 and new_kelly > 0:
        print("✅ 验证通过：新公式修复了低胜率高赔率策略被错误过滤的问题！")
        return True
    else:
        print("🚨 验证失败：新公式未能修复问题")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║  工单 #010.5 - Kelly Criterion 修正验证测试           ║")
    print("╚" + "═" * 58 + "╝")
    print()

    # 运行所有测试
    test_old_kelly_formula()
    test_new_kelly_formula()
    test_edge_cases()
    success = test_comparison()

    # 返回状态码
    sys.exit(0 if success else 1)
