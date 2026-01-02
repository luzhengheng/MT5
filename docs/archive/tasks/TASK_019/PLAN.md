# TASK #019 - 数据泄露修复计划

**Protocol**: v3.8 (Deep Verification & Asset Persistence)
**Priority**: CRITICAL
**Date**: 2025-01-03

## 目标

修复 Task #018 发现的数据泄露问题，将 Sharpe Ratio 从 52.03 降至合理范围 (< 5.0)。

## 根因

1. 特征计算未使用滚动窗口
2. 数据集缺少原��� close 价格列
3. 数据规模不足（仅 2,131 行）

## 修复策略

1. 接入更大规模的模拟数据（43,825 行）
2. 重构特征工程使用滚动窗口
3. 确保数据集包含 close 列
4. 重新训练和回测验证

## 验收标准

- Sharpe Ratio < 5.0 ✅
- Win Rate: 55-65% ✅
- 数据集包含 close 列 ✅

## 执行结果

✅ **修复成功**
- Sharpe Ratio: 2.26 (从 52.03)
- Win Rate: 61.88% (从 92%)
- 数据量: 43,795 行 (从 2,131)

## 交付物

- ingest_eodhd.py - 数据接入
- create_dataset_v2.py - 修复后的特征工程
- 重新训练的模型
- Quad-Artifact 文档集
