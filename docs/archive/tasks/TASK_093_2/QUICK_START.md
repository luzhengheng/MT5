# Task #093.2 快速启动指南

**5 分钟上手指南**

---

## 🚀 快速开始

### 1. 加载外汇数据

```bash
python3 src/data_loader/forex_loader.py --symbol EURUSD.FOREX --from 2020-01-01
```

### 2. 运行 JIT 性能测试

```bash
python3 -m pytest tests/test_jit_performance.py -v
```

### 3. 执行跨资产分析

```bash
python3 scripts/task_093_2_cross_asset_analysis.py
```

---

## 📦 核心组件使用

### Forex Loader

```python
from src.data_loader.forex_loader import ForexLoader

loader = ForexLoader()
loader.process_symbol('EURUSD.FOREX', period='d', start_date='2020-01-01')
```

### JIT Feature Engine

```python
from src.feature_engineering.jit_operators import JITFeatureEngine
import pandas as pd

# 分数差分
df['frac_diff'] = JITFeatureEngine.fractional_diff(df['close'], d=0.5)

# 滚动波动率
df['volatility'] = JITFeatureEngine.rolling_volatility(df['close'], window=20)
```

---

## 📊 查看结果

**跨资产对比报告**:
```bash
cat docs/archive/tasks/TASK_093_2/FOREX_CROSS_ASSET_REPORT.md
```

**最优 d 值 (JSON)**:
```bash
cat docs/archive/tasks/TASK_093_2/cross_asset_optimal_d.json
```

---

## ✅ 验证

```bash
# 验证 TimescaleDB
docker ps | grep timescale

# 查询数据
psql -h localhost -U mt5_user -d mt5_db -c \
  "SELECT COUNT(*) FROM market_candles WHERE symbol='EURUSD.FOREX';"
```

---

**完成时间**: < 5 分钟

**协议**: v4.3 Zero-Trust Edition
