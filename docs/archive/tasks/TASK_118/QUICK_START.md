# 🚀 Shadow Autopsy Engine - 快速启动指南

## 概述

Shadow Autopsy Engine 是 Task #118 核心交付物，用于自动化分析 72 小时影子模式数据，并基于量化指标生成实盘交易的 GO/NO-GO 决策。

---

## 1. 前置要求

### 环境要求
- Python 3.9+
- Task #117 已完成（影子模式数据已生成）
- 依赖包已安装：`json`, `logging`, `dataclasses`, `datetime`, `pathlib`, `typing`

### 数据源
- `data/outputs/audit/shadow_records.json` (Task #117 生成)
- `docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json` (Task #117 生成)

---

## 2. 快速使用

### 方式 A: 运行完整分析流程（推荐）

```bash
# 步骤 1: 清理旧数据
rm -f VERIFY_LOG.log docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md

# 步骤 2: 运行分析脚本
python3 scripts/governance/generate_admission_report.py | tee VERIFY_LOG.log

# 步骤 3: 查看生成的报告
cat docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md
```

**预期输出**:
```
2026-01-17 02:17:13,285 [INFO] 🔐 Shadow Autopsy Engine - Live Trading Admission Report Generator
2026-01-17 02:17:13,285 [INFO] ✅ Loaded: data/outputs/audit/shadow_records.json
2026-01-17 02:17:13,284 [INFO] ✅ Loaded: docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json
2026-01-17 02:17:13,285 [INFO] 📋 Decision: ✅ GO
2026-01-17 02:17:13,285 [INFO]    Confidence: 86.6%
2026-01-17 02:17:13,285 [INFO] ✅ Report written to: docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md
2026-01-17 02:17:13,285 [INFO] 🎯 Shadow Autopsy Analysis Complete
```

### 方式 B: 在 Python 中使用 API

```python
from src.analytics.shadow_autopsy import ShadowAutopsy
import json

# 加载数据
with open('data/outputs/audit/shadow_records.json') as f:
    shadow_data = json.load(f)

with open('docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json') as f:
    comparison_report = json.load(f)

# 创建验尸引擎
autopsy = ShadowAutopsy(shadow_data, comparison_report)

# 生成决策
decision = autopsy.generate_gatekeeping_decision()

# 打印决策信息
print(f"Decision: {'GO' if decision.is_approved else 'NO-GO'}")
print(f"Confidence: {decision.approval_confidence * 100:.1f}%")
print(f"P99 Latency: {decision.p99_latency_ms:.2f}ms")
print(f"Drift Events (24h): {decision.drift_events_24h}")

# 生成报告
report = autopsy.generate_admission_report(decision)
print(report)
```

---

## 3. 核心类和方法

### ShadowAutopsy (主类)

```python
from src.analytics.shadow_autopsy import ShadowAutopsy, GatekeepingDecision

# 初始化
autopsy = ShadowAutopsy(shadow_data, comparison_report)

# 生成决策 (返回 GatekeepingDecision 对象)
decision = autopsy.generate_gatekeeping_decision()

# 生成 Markdown 报告
report_md = autopsy.generate_admission_report(decision)
```

### LatencyAnalyzer (延迟分析)

```python
from src.analytics.shadow_autopsy import LatencyAnalyzer

analyzer = LatencyAnalyzer(records)
stats = analyzer.analyze()

# 返回值
{
    'p95_latency_ms': float,        # P95 百分位延迟
    'p99_latency_ms': float,        # P99 百分位延迟
    'critical_latency_count': int,  # 超过 100ms 的记录数
    'warning_latency_count': int,   # 50-100ms 的记录数
    'total_records': int,
    'avg_latency_ms': float
}
```

### PnLSimulator (P&L 模拟)

```python
from src.analytics.shadow_autopsy import PnLSimulator

simulator = PnLSimulator(records, initial_balance=10000, slippage_pips=1)
pnl = simulator.simulate()

# 返回值
{
    'initial_balance': float,
    'final_balance': float,
    'total_pnl': float,
    'net_return_pct': float,
    'total_trades': int,
    'win_rate': float,
    'avg_pnl_per_trade': float
}
```

### DriftAuditor (漂移检测)

```python
from src.analytics.shadow_autopsy import DriftAuditor

auditor = DriftAuditor(records, window_size=500)
drift_stats = auditor.detect_drift()

# 返回值
{
    'total_drift_events': int,
    'entropy_variance': float,
    'drift_events': List[Dict],
    'status': str  # 'OK' or 'WARNING'
}
```

---

## 4. 决策规则详解

系统基于 **5 个关键规则** 判定是否允许进入实盘:

| 规则 | 条件 | 失败时 |
|------|------|--------|
| 1. 临界错误 | `critical_errors == 0` | NO-GO (0/100) |
| 2. P99 延迟 | `p99_latency_ms < 100` | NO-GO (推理引擎响应不及时) |
| 3. 漂移事件 | `drift_events_24h < 5` | NO-GO (信号质量衰减) |
| 4. 模型性能 | `challenger_f1 > 0.5` | 警告 (但可通过高多样性补偿) |
| 5. 信号多样性 | `diversity_index > 0.4` | 警告 (基线模型和挑战者差异不足) |

**决策逻辑**:
- 如果 5 个规则都通过 → **✅ GO** (100% 批准)
- 如果 1-2 个警告规则失败 → **⚠️ WARNING** (需人工审查)
- 如果任何 P0 规则失败 → **❌ NO-GO** (阻断)

---

## 5. 理解报告输出

### LIVE_TRADING_ADMISSION_REPORT.md 结构

```markdown
# 🔐 Live Trading Admission Report (Task #118)

## Executive Summary
- Final Decision: ✅ **GO** or ❌ **NO-GO**
- Approval Confidence: 86.6%

## Performance Audit Results
### Signal Latency Analysis
- P95 Latency: 0.00ms
- P99 Latency: 0.00ms
- Threshold: <100ms

### Model Quality Metrics
- Challenger F1 Score: 0.5985
- Baseline F1 Score: 0.1865
- F1 Improvement: 221%
- Signal Diversity: 59.3%

### Risk Metrics
- Critical Data Errors: 0 records
- Drift Events (24h): 0 events
- Simulated P&L Return: -0.00%

## Gatekeeping Rules Verification
[表格显示 5 个规则的通过/失败状态]

## Rejection Reasons (if any)
[如果有 NO-GO，列出具体原因]

## Recommendation
[GO/NO-GO 的详细建议]

## Metadata
- Analysis Timestamp: [UTC时间]
- Shadow Mode Records Analyzed: [数量]
- Decision Hash: [16位哈希值]
```

### ADMISSION_DECISION_METADATA.json 字段

```json
{
  "timestamp": "2026-01-16T18:17:13.285050Z",
  "decision": "GO",
  "approval_confidence": 0.866,
  "critical_errors": 0,
  "p95_latency_ms": 0.0,
  "p99_latency_ms": 0.0,
  "drift_events_24h": 0,
  "pnl_net_return": -0.0,
  "diversity_index": 0.593,
  "rejection_reasons": [],
  "decision_hash": "1ac7db5b277d4dd1"
}
```

---

## 6. 常见场景处理

### 场景 A: 发现 P99 延迟过高

**症状**:
```
P99 Latency: 125.34ms ❌ FAIL
Decision: ❌ NO-GO
```

**原因分析**:
- 推理引擎响应变慢（CPU 负载过高）
- 网络延迟增加（Inf 节点到 GTW 的 ZMQ 消息队列堆积）
- 数据处理流水线阻塞

**解决方案**:
1. 检查 Inf 节点 CPU 使用率: `top` 或 `htop`
2. 检查 ZMQ 队列深度: `ss -tlnp | grep 5555`
3. 减少特征计算复杂度
4. 增加并发线程数
5. 重新运行 72 小时影子模式，再次生成报告

### 场景 B: 检测到高漂移

**症状**:
```
Drift Events (24h): 8 events ⚠️ WARNING
Decision: ❌ NO-GO
Reason: "Too many drift events: 8 >= 5 per 24h"
```

**原因分析**:
- 市场结构变化（新闻事件、央行政策）
- 模型泛化能力不足
- 特征工程需要迭代

**解决方案**:
1. 分析漂移事件发生的时间点
2. 检查该时间段的市场新闻事件
3. 考虑重新训练模型，添加新的市场特征
4. 扩展特征工程（如：波动率、相对强弱指标）
5. 增加模型多样性（集成多个不同架构的模型）

### 场景 C: 模型 F1 分数低

**症状**:
```
Challenger F1 Score: 0.4235 ⚠️ BORDERLINE
Threshold: > 0.50
```

**原因分析**:
- 模型训练数据不足
- 类别不平衡（BUY/SELL/HOLD 分布不均匀）
- 超参数需要优化

**解决方案**:
1. 增加训练数据 (运行更长的历史回测)
2. 使用类权重平衡: `class_weight='balanced'` in XGBoost
3. 运行 Optuna 超参数优化 (Task #112 框架)
4. 尝试集成模型 (Stacking/Voting)
5. 审查特征质量 (删除低信息增益特征)

---

## 7. 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 运行分析
autopsy = ShadowAutopsy(shadow_data, comparison_report)
decision = autopsy.generate_gatekeeping_decision()
```

### 逐步分析各个模块

```python
# 仅分析延迟
from src.analytics.shadow_autopsy import LatencyAnalyzer
analyzer = LatencyAnalyzer(records)
latency_stats = analyzer.analyze()
print(f"P99 Latency: {latency_stats['p99_latency_ms']}ms")

# 仅分析漂移
from src.analytics.shadow_autopsy import DriftAuditor
auditor = DriftAuditor(records)
drift_stats = auditor.detect_drift()
print(f"Drift Events: {drift_stats['total_drift_events']}")

# 仅分析 P&L
from src.analytics.shadow_autopsy import PnLSimulator
simulator = PnLSimulator(records)
pnl = simulator.simulate()
print(f"Win Rate: {pnl['win_rate']:.2%}")
```

### 检查原始数据

```python
import json

# 查看影子记录
with open('data/outputs/audit/shadow_records.json') as f:
    shadow = json.load(f)
print(f"Total Records: {shadow['metadata']['total_records']}")
print(f"Total Signals: {shadow['statistics']['total_signals']}")

# 查看模型对比报告
with open('docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json') as f:
    report = json.load(f)
print(f"Challenger F1: {report['comparison_results']['challenger_f1']}")
print(f"Diversity: {report['diversity_results']['diversity_index']}")
```

---

## 8. 性能优化

### 批量处理多个报告

```python
from pathlib import Path
import json
from src.analytics.shadow_autopsy import ShadowAutopsy

shadow_dir = Path("data/outputs/audit")
comparison_dir = Path("docs/archive/tasks/TASK_117")

for shadow_file in shadow_dir.glob("shadow_records_*.json"):
    # 加载数据
    with open(shadow_file) as f:
        shadow_data = json.load(f)
    with open(comparison_dir / "MODEL_COMPARISON_REPORT.json") as f:
        comparison = json.load(f)

    # 生成报告
    autopsy = ShadowAutopsy(shadow_data, comparison)
    decision = autopsy.generate_gatekeeping_decision()

    # 保存报告
    report_name = f"REPORT_{shadow_file.stem}.md"
    with open(report_name, 'w') as f:
        f.write(autopsy.generate_admission_report(decision))
```

### 使用缓存避免重复计算

```python
from functools import lru_cache
import hashlib
import json

@lru_cache(maxsize=128)
def compute_hash(data_str):
    return hashlib.md5(data_str.encode()).hexdigest()

# 缓存分析结果
shadow_hash = compute_hash(json.dumps(shadow_data, sort_keys=True))
if shadow_hash in cache:
    decision = cache[shadow_hash]
else:
    autopsy = ShadowAutopsy(shadow_data, comparison_report)
    decision = autopsy.generate_gatekeeping_decision()
    cache[shadow_hash] = decision
```

---

## 9. 故障排除

| 问题 | 错误信息 | 解决方案 |
|------|---------|---------|
| 找不到数据文件 | `FileNotFoundError: data/outputs/audit/shadow_records.json` | 确保 Task #117 已完成并生成了影子数据 |
| JSON 解析错误 | `json.JSONDecodeError` | 检查 JSON 文件格式，使用 `python3 -m json.tool` 验证 |
| 导入错误 | `ModuleNotFoundError: src.analytics` | 确保在项目根目录运行，或调整 PYTHONPATH |
| 内存溢出 | `MemoryError` | 减少 `window_size` (DriftAuditor) 或批量处理数据 |
| 时间戳解析失败 | `ValueError: time data does not match format` | 确保时间戳格式为 ISO 8601 (例: `2026-01-17T02:24:05Z`) |

---

## 10. 生产部署清单

- [x] 代码已审查 (Gate 1 + Gate 2)
- [x] 单元测试已通过 (14/14)
- [x] 依赖项已安装
- [x] 数据源已验证 (Task #117 完成)
- [ ] 监控告警已设置 (待 Phase 6)
- [ ] 日志持久化已配置
- [ ] 备份策略已实施
- [ ] 运维团队已培训

---

## 参考文档

- **主报告**: COMPLETION_REPORT.md
- **同步指南**: SYNC_GUIDE.md
- **验证日志**: VERIFY_LOG.log
- **源代码**: `src/analytics/shadow_autopsy.py`
- **执行脚本**: `scripts/governance/generate_admission_report.py`
- **单元测试**: `tests/test_shadow_autopsy.py`

---

**快速启动指南 v1.0**
**Protocol**: v4.3 (Zero-Trust Edition)
**最后更新**: 2026-01-17
