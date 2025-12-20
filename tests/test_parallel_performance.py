"""
工单 #010.5 - 并行回测性能验证

对比串行 vs 并行执行的性能差异
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from bin.run_backtest import BacktestRunner


def generate_test_data(n_days=365*2):
    """
    生成测试数据（2年日频数据）
    """
    dates = pd.date_range(start='2022-01-01', periods=n_days, freq='D')
    n = len(dates)

    # 生成随机游走价格
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.01, n)
    price = 1.1000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'open': price,
        'high': price * (1 + np.random.uniform(0, 0.005, n)),
        'low': price * (1 - np.random.uniform(0, 0.005, n)),
        'close': price,
        'volume': np.random.randint(100, 1000, n),
        'y_pred_proba_long': np.random.uniform(0.4, 0.7, n),
        'y_pred_proba_short': np.random.uniform(0.4, 0.7, n),
        'volatility': np.random.uniform(0.005, 0.02, n)
    }, index=dates)

    return df


def test_performance_comparison():
    """
    性能对比测试
    """
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║  工单 #010.5 - 并行回测性能验证                      ║")
    print("╚" + "═" * 58 + "╝")
    print()

    # 生成测试数据
    print("正在生成测试数据...")
    df = generate_test_data(n_days=365*2)  # 2年数据
    print(f"数据生成完成 - 共 {len(df)} 条记录\n")

    # 配置
    config = {
        'initial_cash': 100000.0,
        'commission': 0.0002,
        'spread': 0.0002,
        'slippage': 0.0005,
        'use_kelly_sizer': True,
        'kelly_fraction': 0.25,
        'max_position_pct': 0.50,
    }

    runner = BacktestRunner(config)

    # ============================================================
    # 测试 1: 串行执行
    # ============================================================
    print("=" * 60)
    print("测试 1: 串行回测（单线程）")
    print("=" * 60)

    start_serial = time.time()
    results_serial = runner.run_walkforward(
        df,
        train_months=6,
        test_months=2,
        parallel=False  # 禁用并行
    )
    elapsed_serial = time.time() - start_serial

    print(f"\n⏱️  串行执行耗时: {elapsed_serial:.2f}s")
    print(f"完成窗口数: {len(results_serial)}\n")

    # ============================================================
    # 测试 2: 并行执行
    # ============================================================
    print("=" * 60)
    print("测试 2: 并行回测（多进程）")
    print("=" * 60)

    start_parallel = time.time()
    results_parallel = runner.run_walkforward(
        df,
        train_months=6,
        test_months=2,
        parallel=True  # 启用并行
    )
    elapsed_parallel = time.time() - start_parallel

    print(f"\n⏱️  并行执行耗时: {elapsed_parallel:.2f}s")
    print(f"完成窗口数: {len(results_parallel)}\n")

    # ============================================================
    # 性能对比
    # ============================================================
    print("=" * 60)
    print("性能对比分析")
    print("=" * 60)

    speedup = elapsed_serial / elapsed_parallel if elapsed_parallel > 0 else 0
    time_saved = elapsed_serial - elapsed_parallel
    efficiency = (1 - elapsed_parallel / elapsed_serial) * 100 if elapsed_serial > 0 else 0

    print(f"串行耗时: {elapsed_serial:.2f}s")
    print(f"并行耗时: {elapsed_parallel:.2f}s")
    print(f"加速比: {speedup:.2f}x")
    print(f"节省时间: {time_saved:.2f}s")
    print(f"效率提升: {efficiency:.1f}%")
    print()

    # 验收标准：并行版应小于串行版的 40%
    threshold = 0.40
    passed = (elapsed_parallel / elapsed_serial) < threshold if elapsed_serial > 0 else False

    if passed:
        print(f"✅ 验收通过: 并行版耗时占串行版 {elapsed_parallel/elapsed_serial*100:.1f}% < {threshold*100}%")
    else:
        print(f"⚠️  验收未达标: 并行版耗时占串行版 {elapsed_parallel/elapsed_serial*100:.1f}% >= {threshold*100}%")
        print("   （注：这可能是由于数据量较小或CPU核心数较少导致的）")

    print("=" * 60)
    print()

    return passed


if __name__ == "__main__":
    import logging
    # 降低日志级别以减少输出干扰
    logging.basicConfig(level=logging.WARNING)

    try:
        passed = test_performance_comparison()
        sys.exit(0 if passed else 1)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
