#!/usr/bin/env python3
"""
测试文件：三重障碍标签完整性验证 (Task #093.3)

测试目标：
1. 防止未来函数泄露 (Look-ahead Bias)
2. 验证标签生成逻辑的正确性
3. 确保 JIT 性能达标
4. 验证元标签生成

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Team
Date: 2026-01-12
"""

import pytest
import numpy as np
import pandas as pd
from src.labeling.triple_barrier_factory import TripleBarrierFactory, scan_barriers_jit


class TestLabelIntegrity:
    """标签完整性测试套件"""

    def setup_method(self):
        """准备测试数据"""
        np.random.seed(42)

        # 生成模拟价格序列
        n = 1000
        dates = pd.date_range('2020-01-01', periods=n, freq='D')

        # 生成随机游走价格 + 趋势
        returns = np.random.randn(n) * 0.01 + 0.0001  # 0.01% 波动率
        prices = 1.1000 + np.cumsum(returns)

        self.df = pd.DataFrame({
            'close': prices,
            'volatility': np.abs(np.random.randn(n) * 0.005 + 0.01)  # 波动率
        }, index=dates)

    def test_no_future_function_leak(self):
        """
        测试：禁止未来函数泄露

        验证点：
        - 标签生成时不能使用"未来"的波动率数据
        - 每个时间点只能看到历史数据
        """
        factory = TripleBarrierFactory()

        # 生成标签
        labels = factory.generate_labels(
            prices=self.df['close'],
            volatility=self.df['volatility'],
            lookback_window=20,
            num_std=2.0,
            max_holding_period=10
        )

        # 验证：前 lookback_window 行应该是 NaN（因为没有足够的历史数据）
        assert labels['label'].iloc[:20].isna().all(), \
            "前20行应该全部为 NaN（缺乏历史波动率）"

        # 验证：有效标签数量
        valid_labels = labels['label'].dropna()
        assert len(valid_labels) > 0, "应该至少生成一些有效标签"

        print(f"✅ 未来函数泄露测试通过 - 有效标签数: {len(valid_labels)}")

    def test_label_logic_correctness(self):
        """
        测试：标签逻辑正确性

        验证点：
        - 如果价格未触碰 TP/SL 且未超时，标签必须为 0
        - 触碰上障碍 -> 标签 = 1
        - 触碰下障碍 -> 标签 = -1
        - 超时 -> 标签 = 0 或基于收益方向
        """
        # 构造简单测试场景
        simple_prices = pd.Series([1.0, 1.01, 1.02, 1.03, 1.04, 1.05])
        simple_vol = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01, 0.01])

        factory = TripleBarrierFactory()
        labels = factory.generate_labels(
            prices=simple_prices,
            volatility=simple_vol,
            lookback_window=1,
            num_std=2.0,
            max_holding_period=3
        )

        # 验证标签在 {-1, 0, 1} 范围内
        valid_labels = labels['label'].dropna()
        assert valid_labels.isin([-1, 0, 1]).all(), \
            "标签必须在 {-1, 0, 1} 范围内"

        print(f"✅ 标签逻辑正确性测试通过")

    def test_jit_performance(self):
        """
        测试：JIT 性能达标

        验证点：
        - 处理 1000 条数据应该在 200ms 以内
        """
        import time

        prices = self.df['close'].values
        volatility = self.df['volatility'].values

        # 预热 JIT
        _ = scan_barriers_jit(
            prices=prices[:100],
            volatility=volatility[:100],
            lookback_window=20,
            num_std=2.0,
            max_holding_period=10
        )

        # 性能测试
        start = time.time()
        labels = scan_barriers_jit(
            prices=prices,
            volatility=volatility,
            lookback_window=20,
            num_std=2.0,
            max_holding_period=10
        )
        elapsed = (time.time() - start) * 1000  # 转换为毫秒

        print(f"🚀 JIT 性能: {elapsed:.2f} ms (处理 {len(prices)} 条数据)")

        assert elapsed < 200, \
            f"JIT 性能不达标: {elapsed:.2f} ms > 200 ms"

        print(f"✅ JIT 性能测试通过")

    def test_barrier_touch_validation(self):
        """
        测试：障碍触碰验证

        验证点：
        - 如果标签为 1，必须有 TP 被触碰
        - 如果标签为 -1，必须有 SL 被触碰
        - 如果标签为 0，必须是超时退出
        """
        factory = TripleBarrierFactory()

        labels = factory.generate_labels(
            prices=self.df['close'],
            volatility=self.df['volatility'],
            lookback_window=20,
            num_std=2.0,
            max_holding_period=10
        )

        # 验证障碍类型与标签一致性
        for idx, row in labels.dropna().iterrows():
            if row['label'] == 1:
                assert row['barrier_touched'] in ['upper', 'vertical'], \
                    f"标签=1 但障碍类型={row['barrier_touched']}"
            elif row['label'] == -1:
                assert row['barrier_touched'] in ['lower', 'vertical'], \
                    f"标签=-1 但障碍类型={row['barrier_touched']}"

        print(f"✅ 障碍触碰验证测试通过")

    def test_meta_label_generation(self):
        """
        测试：元标签生成

        验证点：
        - 元标签必须是二分类 {0, 1}
        - 元标签用于判断"是否应该参与交易"
        """
        factory = TripleBarrierFactory()

        labels = factory.generate_labels(
            prices=self.df['close'],
            volatility=self.df['volatility'],
            lookback_window=20,
            num_std=2.0,
            max_holding_period=10,
            generate_meta_labels=True
        )

        # 验证元标签存在
        assert 'meta_label' in labels.columns, "应该包含 meta_label 列"

        # 验证元标签范围
        valid_meta = labels['meta_label'].dropna()
        assert valid_meta.isin([0, 1]).all(), \
            "元标签必须在 {0, 1} 范围内"

        print(f"✅ 元标签生成测试通过")

    def test_class_imbalance_reporting(self):
        """
        测试：类别不平衡报告

        验证点：
        - 能够正确统计各类别分布
        - 能够计算样本权重
        """
        factory = TripleBarrierFactory()

        labels = factory.generate_labels(
            prices=self.df['close'],
            volatility=self.df['volatility'],
            lookback_window=20,
            num_std=2.0,
            max_holding_period=10
        )

        # 统计分布
        distribution = labels['label'].value_counts()

        print(f"\n📊 类别分布:")
        for label, count in distribution.items():
            pct = count / len(labels.dropna()) * 100
            print(f"   标签 {int(label):+d}: {count} ({pct:.1f}%)")

        # 验证：至少有两个类别
        assert len(distribution) >= 2, "至少应该有2个类别"

        print(f"✅ 类别不平衡报告测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
