# TASK #022 快速启动指南

## 🚀 一键运行压力测试

### 前置条件
- 已完成 Task 020 & 021（数据接入与 Walk-Forward 验证）
- 数据文件存在: `data/real_market_data.parquet`

### 执行命令

```bash
# 运行压力测试并保存日志
python3 src/backtesting/stress_test.py | tee docs/archive/tasks/TASK_022/VERIFY_LOG.log
```

### 预期输出

```
============================================================
TASK #022: Stress Testing & Scenario Analysis
============================================================

[1/6] Loading data...
  Loaded 4021 samples

[2/6] Engineering features...
  Model trained on 2793 samples, tested on 1198 samples

[3/6] Testing slippage sensitivity...
  Break-even Slippage: 3.00 bps

[4/6] Running Monte Carlo simulation...
  95% VaR: -0.0294
  95% CVaR: -0.0391

[5/6] Injecting flash crash scenario...
  Crash Scenario Sharpe: 1.3782
  Crash Scenario Max DD: -0.74%

============================================================
STRESS TEST SUMMARY
============================================================
Break-even Slippage: 3.00 bps
95% VaR: -0.0294
95% CVaR: -0.0391
Flash Crash Max DD: -0.74%

🎯 VERDICT: PASS - Strategy shows acceptable stress resilience
============================================================
```

### 关键指标解读

| 指标 | 含义 | 合格标准 |
|------|------|----------|
| **Break-even Slippage** | 策略盈亏平衡滑点 | > 1 bps |
| **95% VaR** | 95% 置信度最大损失 | < 5% |
| **95% CVaR** | 尾部平均损失 | < 10% |
| **Flash Crash Max DD** | 闪崩场景最大回撤 | < 20% |

### 结果判定

- **PASS**: 所有指标在安全范围内，策略可进入实盘
- **FAIL**: 任一指标超出阈值，需优化策略或增加风控

---

## 📊 验证审计脚本

```bash
# 运行本地审计（Gate 1）
python3 scripts/audit_current_task.py
```

预期输出:
```
🔍 AUDIT: Task #022 STRESS TESTING
[✔] stress_test_script
[✔] verify_log
[✔] breakeven_slippage (3.00 bps)
[✔] var_metric (-0.0294)
📊 Audit Summary: 7/7 checks passed
```

---

## 🔄 完整工作流

```bash
# Step 1: 运行压力测试
python3 src/backtesting/stress_test.py | tee docs/archive/tasks/TASK_022/VERIFY_LOG.log

# Step 2: 本地审计
python3 scripts/audit_current_task.py

# Step 3: 双重门禁审查（自动提交）
python3 gemini_review_bridge.py
```

---

## 🛠️ 自定义测试参数

编辑 `src/backtesting/stress_test.py` 调整测试强度：

```python
# 滑点范围 (默认 0-10 bps)
slippage_range = np.arange(0, 11, 1)

# Monte Carlo 模拟次数 (默认 1000)
n_simulations = 1000

# 闪崩幅度 (默认 -5%)
crash_df.loc[crash_idx:crash_idx+5, 'close'] *= 0.95
```

---

## 故障排查

**问题**: `FileNotFoundError: data/real_market_data.parquet`
**解决**: 先运行 Task 020 数据接入
```bash
python3 src/feature_engineering/ingest_real_eodhd.py
```

**问题**: `ModuleNotFoundError: No module named 'scipy'`
**解决**: 安装依赖（scipy 用于统计计算）
```bash
pip install scipy numpy
```

---

**耗时**: 约 60-90 秒（包含 1000 次 Monte Carlo 模拟）
**依赖**: LightGBM, VectorBT, Pandas, NumPy, Scikit-learn
