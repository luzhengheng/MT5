# Task #114 快速启动指南
## ML 推理引擎集成与实时信号生成

**版本**: 1.0
**最后更新**: 2026-01-16
**状态**: ✅ 生产就绪

---

## 快速开始 (5 分钟)

### 1. 验证环境

```bash
# 检查 Python 版本
python3 --version  # 需要 3.9+

# 检查 XGBoost
python3 -c "import xgboost; print(xgboost.__version__)"

# 检查模型文件
ls -lh /opt/mt5-crs/data/models/xgboost_task_114.pkl
```

### 2. 导入并初始化

```python
from src.strategy.ml_live_strategy import MLLiveStrategy

# 创建策略实例
strategy = MLLiveStrategy(
    model_path="/opt/mt5-crs/data/models/xgboost_task_114.pkl",
    confidence_threshold=0.55,
    throttle_seconds=60
)

print(f"✅ 策略初始化完成")
print(f"   Model: {strategy.predictor.get_model_info()['model_path']}")
print(f"   Threshold: {strategy.predictor.confidence_threshold}")
```

### 3. 处理实时 Tick

```python
import pandas as pd

# 加载示例数据
df = pd.read_parquet('/opt/mt5-crs/data_lake/eodhd_standardized/EURUSD_D1.parquet')

# 处理每个 Tick
for i, row in df.iterrows():
    signal, metadata = strategy.on_tick(
        close=row['close'],
        high=row['high'],
        low=row['low'],
        volume=row['volume']
    )

    # 处理信号
    if signal == 1:
        print(f"🟢 BUY Signal | Confidence: {metadata['confidence']:.4f}")
    elif signal == -1:
        print(f"🔴 SELL Signal | Confidence: {metadata['confidence']:.4f}")
    # signal == 0: HOLD (低置信度或节流)

# 获取统计信息
stats = strategy.get_statistics()
print(f"\n📊 Session Statistics:")
print(f"   Ticks:    {stats['tick_count']}")
print(f"   Signals:  {stats['signal_count']}")
print(f"   P95 Lat:  {stats['p95_latency_ms']:.2f}ms")
```

---

## 常见用法

### A. 自定义置信度阈值

```python
# 降低阈值 → 更多信号（更敏感）
strategy.predictor.set_confidence_threshold(0.50)

# 提高阈值 → 更少信号（更谨慎）
strategy.predictor.set_confidence_threshold(0.60)
```

### B. 自定义信号节流

```python
# 创建无节流策略（谨慎！可能过度交易）
strategy_aggressive = MLLiveStrategy(throttle_seconds=0)

# 创建保守策略（信号间隔 2 分钟）
strategy_conservative = MLLiveStrategy(throttle_seconds=120)
```

### C. 手动特征计算

```python
from src.inference.online_features import OnlineFeatureCalculator

calculator = OnlineFeatureCalculator(max_lookback=50)

# 更新数据
for tick in data_stream:
    ready = calculator.update(
        close=tick.close,
        high=tick.high,
        low=tick.low,
        volume=tick.volume
    )

    if ready:
        feature_vector = calculator.get_feature_vector()
        print(f"✅ Features: {feature_vector.shape}")
```

### D. 直接推理

```python
from src.inference.ml_predictor import MLPredictor
import numpy as np

predictor = MLPredictor()

# 随机特征（实际应用应来自 OnlineFeatureCalculator）
features = np.random.randn(21)

signal, confidence, latency = predictor.predict(features)

print(f"Signal: {signal}")
print(f"Confidence: {confidence:.4f}")
print(f"Latency: {latency:.2f}ms")
```

---

## 运行单元测试

### 1. 完整测试套件

```bash
python3 scripts/audit_task_114.py
```

**预期输出**:
```
Ran 19 tests in 0.5s
Tests run:    19
Failures:     0
Errors:       0
Success rate: 100.0%

✅ All tests PASSED
```

### 2. 特定测试

```bash
# 仅运行 OnlineFeatureCalculator 测试
python3 -m pytest scripts/audit_task_114.py::TestOnlineFeatureCalculator -v

# 仅运行延迟性能测试
python3 -m pytest scripts/audit_task_114.py::TestMLPredictor::test_predict_latency_target -v
```

---

## 特征一致性验证

验证在线特征计算与离线特征工程的一致性：

```bash
python3 scripts/verify_feature_parity.py
```

**预期输出**:
```
================================================================================
Task #114: Feature Parity Verification
================================================================================

Loading test data from /opt/mt5-crs/data_lake/eodhd_standardized/EURUSD_D1.parquet
Loaded 100 rows

Computing features with OFFLINE method (Task #113)
Computing features with ONLINE method (Task #114)

================================================================================
Feature Parity Comparison
================================================================================

Comparing 50 rows

✅ rsi_14:                max_diff = 0.000000000 (PASS)
✅ rsi_21:                max_diff = 0.000000000 (PASS)
...
✅ volume_price_trend:    max_diff = 0.000000000 (PASS)

================================================================================
Summary
================================================================================

Total features compared: 21
Matching features:       21
Mismatched features:     0

✅ PARITY CHECK PASSED: All features match within tolerance
```

---

## 故障排查

### Q1. 模型加载失败

```
ERROR: Failed to load model: Model integrity check FAILED!
Expected MD5: 2310ff8b54c1edfb5e2a2528bfc3a468
Actual MD5:   xxxxx
```

**解决方案**:
```bash
# 重新计算模型的 MD5
md5sum /opt/mt5-crs/data/models/xgboost_task_114.pkl

# 更新源代码中的 EXPECTED_MODEL_MD5
# src/inference/ml_predictor.py:23
```

### Q2. 特征维度不匹配

```
ValueError: Feature shape mismatch, expected: 21, got 10
```

**解决方案**:
```python
# 确保 OnlineFeatureCalculator 已准备足够数据（50 ticks）
print(f"Buffer size: {len(calculator.close_buffer)}")

# 必须 >= 50 才能计算完整特征
if len(calculator.close_buffer) >= 50:
    features = calculator.get_feature_vector()
```

### Q3. 延迟过高

```
P95 latency = 150.5ms (超过 100ms 目标)
```

**优化建议**:

1. **减少特征计算开销**:
```python
# 预先计算常用特征，缓存结果
```

2. **使用 ONNX 加速**:
```python
# 将模型转换为 ONNX 格式
import skl2onnx
# ... (需要额外配置)
```

3. **GPU 推理** (可选):
```python
# 使用 RAPIDS 或 CuDF 加速
# (需要 NVIDIA GPU 支持)
```

---

## 集成到现有系统

### 与 Live Loop 集成

```python
# src/execution/live_engine.py 中的 on_tick 回调

async def on_tick(self, tick_data):
    """处理实时 Tick"""

    # 运行 ML 推理
    signal, metadata = self.ml_strategy.on_tick(
        close=tick_data.close,
        high=tick_data.high,
        low=tick_data.low,
        volume=tick_data.volume
    )

    # 转换为订单
    if signal == 1:
        await self.execute_buy(tick_data.price)
    elif signal == -1:
        await self.execute_sell(tick_data.price)
```

### 与 Risk Manager 集成

```python
# src/execution/risk_manager.py 中的 validate_signal

def validate_signal(self, signal: int, confidence: float) -> bool:
    """验证 ML 信号的风险"""

    # 只有高置信度信号才通过风控
    if confidence < 0.55:
        return False

    # 检查账户风险
    if self.is_account_at_risk():
        return False

    return True
```

---

## 性能监控

### 实时监控脚本

```python
import time
from datetime import datetime

# 监控延迟分布
latencies = []
start_time = time.time()

while len(latencies) < 1000:
    signal, metadata = strategy.on_tick(...)
    latencies.append(metadata['latency_ms'])

    if time.time() - start_time > 300:  # 5 分钟
        break

# 打印统计
print(f"Mean:  {np.mean(latencies):.2f}ms")
print(f"P50:   {np.percentile(latencies, 50):.2f}ms")
print(f"P95:   {np.percentile(latencies, 95):.2f}ms")
print(f"P99:   {np.percentile(latencies, 99):.2f}ms")
print(f"Max:   {np.max(latencies):.2f}ms")
```

---

## 下一步

1. **部署到 Inf 节点**
   - 同步模型文件到 `/opt/mt5-crs/data/models/`
   - 验证模型 MD5 一致性
   - 运行单元测试确保环境正确

2. **与实盘集成**
   - 集成 MLLiveStrategy 到 Live Loop
   - 部署到 Inf 节点的生产环境
   - 监控推理延迟和信号质量

3. **性能优化**
   - 收集真实市场数据进行延迟基准测试
   - 根据市场条件调整信号节流参数
   - 考虑 ONNX/GPU 加速

4. **模型迭代**
   - 收集推理结果反馈
   - 进行 Task #115：特征工程迭代 2
   - 训练更强的基线模型

---

**相关链接**:
- [完成报告](./COMPLETION_REPORT.md)
- [部署指南](./SYNC_GUIDE.md)
- [源代码](../../src/inference/)

**需要帮助？**
- 查看单元测试：`scripts/audit_task_114.py`
- 查看特征验证：`scripts/verify_feature_parity.py`
- 检查执行日志：`VERIFY_LOG.log`
