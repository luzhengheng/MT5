# TASK #018 - 向量化回测与验伪

**Protocol**: v3.8 (Deep Verification & Asset Persistence)
**Priority**: CRITICAL
**Date**: 2025-01-03

## 目标

搭建基于 VectorBT 的高性能回测框架，验证 Task #016 模型是否存在数据泄露。

## 验收标准

- Sharpe Ratio > 5.0 → 判定为 LEAKED
- Sharpe Ratio < 5.0 → 判定为 SAFE

## 执行策略

1. 安装 VectorBT 和兼容依赖
2. 开发回测引擎 (vbt_runner.py)
3. 使用 Task #016 模型进行全量回测
4. 分析结果并诊断泄露
5. 生成完整文档

## 关键发现

⚠️ **Task #016 模型存在严重数据泄露**
- Sharpe Ratio: 52.03 (远超阈值)
- Win Rate: 92% (不现实)
- 需要启动 TASK #019 修复

## 交付物

- vbt_runner.py - 回测引擎
- VERIFY_LOG.log - 完整回测日志
- Quad-Artifact 文档集
