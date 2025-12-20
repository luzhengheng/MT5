"""
工单 #010.5 - DSR 试验计数器测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reporting.trial_recorder import TrialRegistry, calculate_dsr, get_global_registry


def test_trial_registry():
    """
    测试试验计数器的基本功能
    """
    print("=" * 60)
    print("测试 1: 试验计数器基本功能")
    print("=" * 60)

    # 使用临时文件测试
    import tempfile
    import os

    temp_path = Path(tempfile.mktemp(suffix='.json'))

    registry = TrialRegistry(registry_path=temp_path)

    # 初始计数应为 0
    initial_count = registry.get_trial_count()
    print(f"初始计数: {initial_count}")
    assert initial_count == 0, "初始计数应为 0"

    # 递增计数
    n1 = registry.increment_and_get()
    print(f"第 1 次递增: {n1}")
    assert n1 == 1, "第一次递增应为 1"

    n2 = registry.increment_and_get()
    print(f"第 2 次递增: {n2}")
    assert n2 == 2, "第二次递增应为 2"

    n3 = registry.increment_and_get()
    print(f"第 3 次递增: {n3}")
    assert n3 == 3, "第三次递增应为 3"

    # 验证持久化（重新加载）
    registry2 = TrialRegistry(registry_path=temp_path)
    current_count = registry2.get_trial_count()
    print(f"重新加载后的计数: {current_count}")
    assert current_count == 3, "重新加载后计数应保持不变"

    # 清理
    os.remove(temp_path)

    print("✅ 测试 1 通过\n")


def test_calculate_dsr():
    """
    测试 DSR 计算
    """
    print("=" * 60)
    print("测试 2: DSR 计算")
    print("=" * 60)

    # 场景 1: 高 Sharpe Ratio，少量试验
    sr1 = 2.0
    n1 = 10
    t1 = 252  # 1年日频数据

    dsr1 = calculate_dsr(sr1, n1, t1)
    print(f"场景 1 - SR={sr1}, N={n1}, T={t1} -> DSR={dsr1:.3f}")

    # 场景 2: 高 Sharpe Ratio，大量试验（过拟合风险）
    sr2 = 2.0
    n2 = 1000
    t2 = 252

    dsr2 = calculate_dsr(sr2, n2, t2)
    print(f"场景 2 - SR={sr2}, N={n2}, T={t2} -> DSR={dsr2:.3f}")

    # 场景 3: 低 Sharpe Ratio
    sr3 = 0.5
    n3 = 100
    t3 = 252

    dsr3 = calculate_dsr(sr3, n3, t3)
    print(f"场景 3 - SR={sr3}, N={n3}, T={t3} -> DSR={dsr3:.3f}")

    # 验证：更多试验应该降低 DSR（惩罚过拟合）
    assert dsr2 < dsr1, "更多试验应导致更低的 DSR"

    print("\n观察:")
    print(f"  - 相同 SR，试验从 {n1} 增加到 {n2} 时，DSR 从 {dsr1:.3f} 降至 {dsr2:.3f}")
    print(f"  - 这反映了 '选择偏差' 的惩罚")

    print("✅ 测试 2 通过\n")


def test_global_registry():
    """
    测试全局单例注册表
    """
    print("=" * 60)
    print("测试 3: 全局单例注册表")
    print("=" * 60)

    registry = get_global_registry()
    print(registry.get_summary())

    print("✅ 测试 3 通过\n")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║  工单 #010.5 - DSR 试验计数器测试                    ║")
    print("╚" + "═" * 58 + "╝")
    print()

    try:
        test_trial_registry()
        test_calculate_dsr()
        test_global_registry()

        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)

        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
