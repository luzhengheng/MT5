# TASK #021 快速启动指南

## 🚀 一键运行 Walk-Forward 验证

### 前置条件
- 已完成 Task 020（真实数据接入）
- 数据文件存在: `data/real_market_data.parquet`

### 执行命令

```bash
# 运行 Walk-Forward 验证并保存日志
python3 src/backtesting/walk_forward.py | tee docs/archive/tasks/TASK_021/VERIFY_LOG.log
```

### 预期输出

```
============================================================
TASK #021: Walk-Forward Analysis
============================================================

[1/6] Loading data...
  Loaded 4021 samples (2015-01-01 to 2026-01-03)

[2/6] Engineering features...
  Features ready: 3991 samples after dropna

[3/6] Configuring Walk-Forward...
  Generated 7 rolling windows

[4/6] Running Walk-Forward validation...
  Window 1/7: Train 2015-01-30 to 2018-01-28, Test 2018-01-29 to 2019-01-28
  Window 2/7: Train 2016-01-30 to 2019-01-28, Test 2019-01-29 to 2020-01-28
  ...

[5/6] Running OOS backtest...

============================================================
OOS BACKTEST RESULTS
============================================================
OOS Sharpe Ratio: 1.0535
✅ VERDICT: Strategy ROBUST - Good generalization
============================================================
```

### 关键指标解读

| 指标 | 含义 | 目标值 |
|------|------|--------|
| **OOS Sharpe Ratio** | 样本外夏普比率 | > 1.0 为鲁棒 |
| **Win Rate** | 胜率 | > 50% |
| **Max Drawdown** | 最大回撤 | < 5% |
| **Total Trades** | 交易次数 | > 100 (样本充足) |

### 故障排查

**问题**: `FileNotFoundError: data/real_market_data.parquet`
**解决**: 先运行 Task 020 数据接入脚本
```bash
python3 src/feature_engineering/ingest_real_eodhd.py
```

**问题**: `ModuleNotFoundError: No module named 'vectorbt'`
**解决**: 安装依赖
```bash
pip install vectorbt lightgbm scikit-learn
```

---

## 📊 验证审计脚本

```bash
# 运行本地审计（Gate 1）
python3 scripts/audit_current_task.py
```

预期输出:
```
🔍 AUDIT: Task #021 WALK-FORWARD VALIDATION
[✔] walk_forward_script
[✔] verify_log
[✔] multiple_test_periods (7 periods)
[✔] oos_sharpe (1.0535)
📊 Audit Summary: 7/7 checks passed
```

---

## 🔄 完整工作流

```bash
# Step 1: 运行 Walk-Forward 验证
python3 src/backtesting/walk_forward.py | tee docs/archive/tasks/TASK_021/VERIFY_LOG.log

# Step 2: 本地审计
python3 scripts/audit_current_task.py

# Step 3: 双重门禁审查（自动提交）
python3 gemini_review_bridge.py
```

---

**耗时**: 约 30-60 秒（取决于数据量）
**依赖**: LightGBM, VectorBT, Pandas, NumPy, Scikit-learn
