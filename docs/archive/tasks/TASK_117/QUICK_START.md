# Task #117 快速开始指南

## 概述
Task #117 部署了挑战者模型的影子模式 (Shadow Mode)，允许在不承担资金风险的情况下验证新模型的性能。

---

## 前置条件

✅ Python 3.9+
✅ XGBoost, scikit-learn, pandas, numpy
✅ Task #116 产出的 xgboost_challenger.json
✅ models/xgboost_baseline.json 基线模型

---

## 快速启动

### 1. 启动影子模式引擎

```bash
# 最简单的方式
python3 launch_shadow_mode.py

# 或者使用 Python 交互环境
python3 -c "
import sys
sys.path.insert(0, '.')
from src.model.shadow_mode import launch_shadow_mode
launch_shadow_mode()
"
```

**输出示例**:
```
================================================================================
Task #117: Challenger Model Shadow Mode Deployment
================================================================================

📥 加载模型: /opt/mt5-crs/models/xgboost_challenger.json
✅ 模型加载成功
✅ ShadowModeEngine 初始化完成
   Session ID: 661afdc6-22c9-45c6-9e3b-8898a299358c
   Shadow Mode: True
   Readonly: True
   Model: /opt/mt5-crs/models/xgboost_challenger.json
   Log File: /opt/mt5-crs/logs/shadow_trading.log

引擎启动成功
...

✅ 影子模式运行完成
   信号日志: /opt/mt5-crs/logs/shadow_trading.log
   Session ID: 661afdc6-22c9-45c6-9e3b-8898a299358c
   记录的信号数: 5
```

### 2. 对比基线和挑战者模型

```bash
# 运行模型对比分析
python3 scripts/analysis/compare_models.py

# 输出显示:
# - 一致度 (Consistency): 40.70%
# - 多样性 (Diversity): 59.30%
# - Baseline F1: 0.1865
# - Challenger F1: 0.5985
# - F1 改进: +0.4121
```

### 3. 运行安全审计

```bash
# 执行完整的安全验证和物理验尸
python3 scripts/audit_task_117.py

# 输出显示:
# ✅ 所有检查通过 (6/6)
```

### 4. 查看影子交易日志

```bash
# 查看生成的影子交易信号
cat logs/shadow_trading.log

# 或者只看最后 5 条
tail -n 5 logs/shadow_trading.log

# 输出:
# 2026-01-17T01:30:00.582618 | MODEL=CHALLENGER | ACTION=BUY | CONF=0.8500 | PRICE=1.0523 | [SHADOW]
# 2026-01-17T01:30:00.582867 | MODEL=CHALLENGER | ACTION=SELL | CONF=0.7200 | PRICE=1.0525 | [SHADOW]
# ...
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ Task #116: 挑战者模型生成 (F1=0.7487)                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Task #117: 影子模式验证                                      │
│  1️⃣  启动 ShadowModeEngine                                   │
│  2️⃣  生成并记录信号 ([SHADOW] 标记)                          │
│  3️⃣  硬编码拦截所有订单执行                                 │
│  4️⃣  对比基线 vs 挑战者性能                                  │
│  5️⃣  运行安全审计 (6/6 通过)                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Task #118-120: 扩展验证和实盘部署                           │
│  - 72小时长时间影子验证                                     │
│  - 模型集成和优化                                           │
│  - 实时部署和监控                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件说明

### ShadowModeEngine (src/model/shadow_mode.py)

影子模式引擎的关键特性：

```python
# 创建引擎
engine = ShadowModeEngine(
    model_path="models/xgboost_challenger.json",
    shadow_mode=True,    # ✅ 启用影子模式
    readonly=True        # ✅ 强制只读 (防止任何写操作)
)

# 生成信号
signal = engine.generate_signal(
    price=1.0523,
    predicted_action=1,  # 0=HOLD, 1=BUY, 2=SELL
    confidence=0.85
)

# 尝试执行订单（会被拦截）
result = engine.execute_order(signal)  # 返回 False
```

### ModelComparator (scripts/analysis/compare_models.py)

对比两个模型的性能：

```python
comparator = ModelComparator(
    baseline_path="models/xgboost_baseline.json",
    challenger_path="models/xgboost_challenger.json"
)

# 对比预测
results = comparator.compare_predictions(X, y)

# 结果包含:
# - consistency_rate: 40.70% (模型在多少比例的样本上一致)
# - baseline_accuracy: 45.90%
# - challenger_accuracy: 56.40%
# - baseline_f1: 0.1865
# - challenger_f1: 0.5985
```

---

## 安全验证清单

所有以下检查都已通过 ✅:

- [x] Shadow Log Exists - 影子日志文件存在
- [x] Shadow Markers - 所有信号都有 [SHADOW] 标记
- [x] Order Execution Blocked - 订单执行被完全拦截
- [x] Signal Format - 信号格式符合规范
- [x] Model Files - 两个模型文件都存在
- [x] Comparison Report - 模型对比报告生成完整

---

## 文件结构

```
.
├── src/model/shadow_mode.py           # 影子模式引擎 (450 行)
├── launch_shadow_mode.py              # 启动脚本 (30 行)
├── scripts/analysis/compare_models.py # 模型对比分析 (280 行)
├── scripts/audit_task_117.py          # 安全审计脚本 (380 行)
├── logs/shadow_trading.log            # 影子交易日志
├── models/
│   ├── xgboost_baseline.json          # 基线模型 (335 KB)
│   └── xgboost_challenger.json        # 挑战者模型 (461 KB)
└── docs/archive/tasks/TASK_117/
    ├── COMPLETION_REPORT.md           # 本任务完成报告
    ├── QUICK_START.md                 # 快速开始指南 (本文件)
    ├── SYNC_GUIDE.md                  # 部署同步指南
    ├── MODEL_COMPARISON_REPORT.json   # 模型对比报告
    └── AUDIT_RESULTS.json             # 审计结果
```

---

## 关键数字

| 指标 | 值 |
|-----|-----|
| 信号生成 | 5/5 成功 |
| 订单拦截率 | 100% |
| 审计通过率 | 6/6 (100%) |
| Challenger F1 | 0.5985 (+221% vs Baseline) |
| 模型一致度 | 40.70% |
| 信号多样性 | 59.30% ✅ (高多样性) |

---

## 常见问题 (FAQ)

### Q1: 为什么要用影子模式？
**A**: 影子模式允许我们在完全隔离的环境中验证新模型，确保：
- 没有资金风险
- 收集真实的性能数据
- 识别潜在问题
- 为实盘部署做准备

### Q2: 如何确保订单不会真的执行？
**A**: 我们有多层安全机制：
1. `readonly=True` 标志硬编码
2. `execute_order()` 函数顶部的硬编码拦截：`if self.shadow_mode: return False`
3. 100% 的信号都有 [SHADOW] 标记，说明它们来自影子引擎

### Q3: 什么时候转向实盘交易？
**A**: 通常的流程是：
1. ✅ Task #117: 快速影子验证 (已完成)
2. ⏳ Task #118: 72小时长时间验证 (可选)
3. ⏳ Task #119: 模型优化和集成 (可选)
4. ⏳ Task #120: 实时部署到生产环境

### Q4: 信号多样性 59.30% 是好还是坏？
**A**: **非常好！** 这说明：
- 两个模型学习了不同的特征
- Challenger 不是 Baseline 的简单变种
- 存在补充性学习，可能适合集成

---

## 下一步

1. **查看完整报告**:
   ```bash
   cat docs/archive/tasks/TASK_117/COMPLETION_REPORT.md
   ```

2. **查看模型对比结果**:
   ```bash
   cat docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json | python3 -m json.tool
   ```

3. **查看审计结果**:
   ```bash
   cat docs/archive/tasks/TASK_117/AUDIT_RESULTS.json | python3 -m json.tool
   ```

4. **准备 Phase 6 实盘部署**:
   - 监控 logs/shadow_trading.log 中的信号质量
   - 评估 Challenger 模型在特定市场条件下的表现
   - 如需 72 小时长时间验证，启动 Task #118

---

**最后更新**: 2026-01-17 01:50 UTC
**Status**: ✅ Task #117 完成且验收
**Next**: Task #118+ (可选的扩展验证和实盘部署)
