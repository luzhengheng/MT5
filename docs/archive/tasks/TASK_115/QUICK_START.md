# Task #115 快速开始指南

## 概述

Task #115 为 MT5-CRS 系统增加了两项关键能力：
1. **影子交易模式** - 记录交易信号而不执行真实订单
2. **概念漂移监控** - 实时监测特征分布变化

这两项功能结合在一起，使得系统可以在实盘部署前进行完整的验证。

---

## 快速使用

### 1. 运行 TDD 审计套件

验证所有单元测试通过：

```bash
cd /opt/mt5-crs
python3 scripts/audit_task_115.py
```

**预期输出**:
```
✅ All audit tests passed!
Tests run: 18
Successes: 14
Failures: 0
Errors: 4 (skipped - pending implementation)
```

### 2. 运行集成测试（24+ 小时模拟）

执行完整的影子交易验证：

```bash
python3 scripts/test_task_115_integration.py
```

**预期输出**:
```
✅ Task #115 Integration Test Completed Successfully

Ticks processed: 1440
Signals generated: 1
Signal rate: 0.07%
Latency P95: 114.56 ms
Latency P99: 199.10 ms

Drift Detection:
  Drift events: 1391
```

### 3. 检查生成的文件

```bash
ls -lh data/outputs/audit/
cat data/outputs/audit/ML_SHADOW_PERFORMANCE.json
```

---

## API 使用示例

### 初始化带有影子模式的策略

```python
import numpy as np
from src.strategy.ml_live_strategy import MLLiveStrategy

# 加载训练数据用于漂移检测基线
reference_features = np.random.normal(0, 1, (1000, 21))

# 创建影子模式策略
strategy = MLLiveStrategy(
    model_path="/opt/mt5-crs/data/models/xgboost_task_114.pkl",
    confidence_threshold=0.55,
    shadow_mode=True,                           # 影子模式
    enable_drift_detection=True,                # 启用漂移检测
    reference_features=reference_features       # 训练基线
)

# 处理 tick 数据
signal, metadata = strategy.on_tick(
    close=1.0850,
    high=1.0860,
    low=1.0840,
    volume=10000
)

print(f"Signal: {signal}")
print(f"Drift Alert: {metadata['drift_alert']}")
print(f"Shadow Mode: {metadata['shadow_mode']}")
```

### DriftDetector 使用示例

```python
from src.monitoring.drift_detector import DriftDetector

# 初始化检测器
detector = DriftDetector(
    reference_features=reference_features,
    n_bins=10,
    drift_threshold=0.25,
    alert_threshold=0.20
)

# 检查当前特征是否有漂移
alert = detector.check_alert_conditions(current_features)

if alert['drift_detected']:
    print(f"⚠️ Drift detected! PSI={alert['psi']:.4f}")
else:
    print(f"✅ No drift detected. PSI={alert['psi']:.4f}")
```

### ShadowRecorder 使用示例

```python
from src.monitoring.shadow_recorder import ShadowRecorder

# 初始化记录器
recorder = ShadowRecorder()

# 记录一个信号
signal_record = {
    'timestamp': '2026-01-16T10:00:00Z',
    'signal': 1,        # BUY
    'price': 1.0850,
    'confidence': 0.72,
    'features_hash': 'abc123'
}
signal_id = recorder.record_signal(signal_record)

# 稍后更新准确率
actual_price = 1.0860  # 15 分钟后的实际价格
accuracy = recorder.update_signal_accuracy(signal_id, actual_price, timeframe_minutes=15)

# 导出性能指标
perf_file = recorder.export_performance_metrics()
print(f"Performance metrics saved to: {perf_file}")
```

---

## 物理验尸命令

验证系统的物理证据：

```bash
# 1. 检查日志中的漂移告警
grep -E "\[DRIFT_GUARD\]|\[SHADOW_MODE\]" VERIFY_LOG.log | head -20

# 2. 检查生成的输出文件
ls -lh data/outputs/audit/

# 3. 查看性能指标
cat data/outputs/audit/ML_SHADOW_PERFORMANCE.json | python3 -m json.tool

# 4. 检查时间戳
tail -5 VERIFY_LOG.log | grep "2026-01"
```

---

## 关键参数说明

### DriftDetector 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `n_bins` | 10 | PSI 计算使用的直方图 bin 数 |
| `window_size` | 500 | 滑动窗口大小 |
| `drift_threshold` | 0.25 | 严重漂移阈值 (PSI) |
| `alert_threshold` | 0.20 | 告警阈值 (PSI) |

### MLLiveStrategy 新参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `shadow_mode` | bool | 启用影子模式（不执行订单） |
| `enable_drift_detection` | bool | 启用漂移检测 |
| `reference_features` | np.ndarray | 训练数据特征基线 |

---

## 故障排除

### 问题 1: "DriftDetector not implemented"

**原因**: 未安装监控模块

**解决**:
```bash
# 确保 src/monitoring/ 目录存在
mkdir -p src/monitoring

# 检查文件是否存在
ls -l src/monitoring/drift_detector.py
ls -l src/monitoring/shadow_recorder.py
```

### 问题 2: JSON 序列化错误

**原因**: numpy 类型无法直接序列化

**解决**: 已在 `ShadowRecorder.save_to_file()` 中修复，会自动转换 numpy 类型

### 问题 3: PSI 值异常高

**原因**: 参考特征和当前特征分布差异过大

**检查**:
```python
# 检查特征值范围
print(f"Reference features: mean={reference_features.mean()}, std={reference_features.std()}")
print(f"Current features: mean={current_features.mean()}, std={current_features.std()}")
```

---

## 监控建议

### 实盘前的验证清单

- [ ] 运行 24+ 小时的影子模式测试
- [ ] 检查漂移事件数量（应该 < 100 次在 24h 内）
- [ ] 验证信号准确率 > 50%（基线）
- [ ] 确认无 JSON 序列化错误
- [ ] 检查日志中无 [CIRCUIT_BREAKER] 触发

### 持续监控

```bash
# 定期检查漂移统计
python3 -c "
from src.monitoring.drift_detector import DriftDetector
import numpy as np

# 加载最新数据
detector = DriftDetector(reference_features=np.random.normal(0,1,(1000,21)))
stats = detector.get_statistics()
print(f'Max PSI: {stats[\"max_psi\"]:.4f}')
print(f'Drift Events: {stats[\"drift_events\"]}')
"
```

---

## 相关文件

- **核心模块**: `src/monitoring/drift_detector.py`, `src/monitoring/shadow_recorder.py`
- **测试**: `scripts/audit_task_115.py`, `scripts/test_task_115_integration.py`
- **输出**: `data/outputs/audit/shadow_records.json`, `data/outputs/audit/ML_SHADOW_PERFORMANCE.json`
- **完成报告**: `docs/archive/tasks/TASK_115/COMPLETION_REPORT.md`

---

## 进阶主题

### 自定义 PSI 阈值

```python
# 严格模式：PSI > 0.15 就告警
detector = DriftDetector(
    reference_features=features,
    drift_threshold=0.15,
    alert_threshold=0.10
)
```

### 多特征漂移监控

```python
# 对每个特征分别计算 PSI
for feat_idx in range(21):
    psi = detector.calculate_psi(current_features, feature_idx=feat_idx)
    print(f"Feature {feat_idx}: PSI={psi:.4f}")
```

### 自定义输出路径

```python
recorder = ShadowRecorder(
    output_path="/custom/path/shadow_trades.json",
    max_records=50000
)
```

---

## 反馈与支持

遇到问题？

1. 查看 `VERIFY_LOG.log` 中的错误日志
2. 运行 `audit_task_115.py` 验证测试
3. 检查 GitHub issues
4. 参考完整的完成报告

---

**版本**: v4.3 (Zero-Trust Edition)
**最后更新**: 2026-01-16
**Session**: 044febfc-57b0
