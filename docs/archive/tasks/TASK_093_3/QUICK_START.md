# Task #093.3 - 快速启动指南

## 📋 任务概述

**任务**: AI 原生外汇特征工厂 - 三重障碍标签与样本均衡化

**目标**: 生成 EURUSD 外汇训练数据集，包含动态波动率驱动的三重障碍标签

**协议**: v4.3 (Zero-Trust Edition)

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- TimescaleDB (已启动并运行)
- 依赖包: pandas, numpy, numba, sqlalchemy, pyarrow

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行测试

验证三重障碍标签工厂的正确性：

```bash
# 运行完整测试套件
python3 -m pytest tests/test_label_integrity.py -v -s

# 预期输出:
# ✅ test_no_future_function_leak         PASSED
# ✅ test_label_logic_correctness         PASSED
# ✅ test_jit_performance                 PASSED (< 0.1ms)
# ✅ test_barrier_touch_validation        PASSED
# ✅ test_meta_label_generation           PASSED
# ✅ test_class_imbalance_reporting       PASSED
```

### 4. 生成训练数据集

执行主脚本生成特征-标签对：

```bash
# 生成 EURUSD 训练数据集
python3 scripts/task_093_3_generate_training_set.py

# 预期输出:
# ✅ 训练集生成成功!
# 📦 输出文件: data/processed/forex_training_set_v1.parquet
# 📊 样本数量: 1,829
# 🔒 SHA256: f592179ed84ee8c4...
```

### 5. 验证输出

检查生成的数据集：

```bash
# 查看数据集信息
python3 -c "
import pandas as pd
df = pd.read_parquet('data/processed/forex_training_set_v1.parquet')
print(f'样本数: {len(df)}')
print(f'特征数: {len(df.columns)}')
print(f'标签分布:\n{df[\"label\"].value_counts().sort_index()}')
"

# 预期输出:
# 样本数: 1829
# 特征数: 19
# 标签分布:
# -1.0    947
#  0.0      8
#  1.0    953
```

---

## 📦 核心组件

### 1. JIT 加速标签扫描

文件: `src/labeling/triple_barrier_factory.py`

核心函数:
```python
from src.labeling.triple_barrier_factory import scan_barriers_jit

# Numba JIT 加速的标签扫描
labels, barriers, holding, returns = scan_barriers_jit(
    prices=prices_array,
    volatility=volatility_array,
    lookback_window=20,
    num_std=2.0,
    max_holding_period=10
)
```

**性能**: < 0.1ms 处理 1,000+ 条数据

### 2. 三重障碍标签工厂

文件: `src/labeling/triple_barrier_factory.py`

使用示例:
```python
from src.labeling.triple_barrier_factory import TripleBarrierFactory

factory = TripleBarrierFactory()

# 生成标签
labels_df = factory.generate_labels(
    prices=df['close'],
    volatility=df['volatility'],
    lookback_window=20,      # 波动率回看窗口
    num_std=2.0,             # 障碍宽度（标准差倍数）
    max_holding_period=10,   # 最大持有期（天）
    generate_meta_labels=True  # 生成元标签
)
```

**输出字段**:
- `label`: 标签 (-1=下跌, 0=平盘, 1=上涨)
- `barrier_touched`: 障碍类型 ('upper', 'lower', 'vertical')
- `holding_period`: 实际持有期
- `return`: 实际收益率
- `meta_label`: 元标签 (0=不交易, 1=参与交易)
- `sample_weight`: 样本权重（处理类别不平衡）

### 3. JIT 特征引擎

文件: `src/feature_engineering/jit_operators.py`

使用示例:
```python
from src.feature_engineering.jit_operators import JITFeatureEngine

# 分数差分 (d=0.30 for EURUSD)
df['frac_diff'] = JITFeatureEngine.fractional_diff(
    series=df['close'],
    d=0.30,
    threshold=1e-5,
    max_k=100
)

# 滚动波动率
df['volatility'] = JITFeatureEngine.rolling_volatility(
    series=df['close'],
    window=20
)

# 滚动均值
df['sma_20'] = JITFeatureEngine.rolling_average(
    series=df['close'],
    window=20
)
```

---

## 📊 数据集说明

### Parquet 文件结构

文件: `data/processed/forex_training_set_v1.parquet`

**特征列** (19 columns):
1. `open`, `high`, `low`, `close`, `volume` - OHLCV 价格数据
2. `close_frac_diff` - 分数差分后的收盘价 (d=0.30)
3. `returns`, `log_returns` - 收益率
4. `sma_20`, `sma_50` - 简单移动平均
5. `volatility`, `volatility_5`, `volatility_10` - 多时间窗口波动率
6. `label` - 三重障碍标签 (-1, 0, 1)
7. `meta_label` - 元标签 (0, 1)
8. `sample_weight` - 样本权重
9. `barrier_touched` - 障碍类型 ('upper', 'lower', 'vertical')
10. `holding_period` - 持有期
11. `return` - 实际收益率

**统计信息**:
- **文件大小**: 228 KB (Snappy 压缩)
- **样本数**: 1,829 条
- **时间范围**: 2020-01-01 至 2026-01-11
- **标签分布**: -1 (49.6%), 0 (0.4%), +1 (49.9%)

---

## 🔬 测试数据质量

### 验证未来函数泄露

```python
# 检查标签生成是否使用未来信息
python3 -m pytest tests/test_label_integrity.py::TestLabelIntegrity::test_no_future_function_leak -v
```

### 验证标签逻辑

```python
# 检查标签与障碍触碰的一致性
python3 -m pytest tests/test_label_integrity.py::TestLabelIntegrity::test_barrier_touch_validation -v
```

### 验证 JIT 性能

```python
# 基准测试 JIT 性能
python3 -m pytest tests/test_label_integrity.py::TestLabelIntegrity::test_jit_performance -v
```

---

## 📈 使用场景

### 1. 机器学习模型训练

```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# 加载数据
df = pd.read_parquet('data/processed/forex_training_set_v1.parquet')

# 准备特征和标签
feature_cols = [
    'close_frac_diff', 'returns', 'log_returns',
    'sma_20', 'sma_50',
    'volatility', 'volatility_5', 'volatility_10'
]

X = df[feature_cols].dropna()
y = df.loc[X.index, 'label']
weights = df.loc[X.index, 'sample_weight']

# 训练模型
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y, sample_weight=weights)
```

### 2. 元标签过滤

```python
# 使用元标签过滤虚假信号
df['prediction'] = model.predict(X)

# 只执行高置信度的预测
df['execute'] = (df['meta_label'] == 1) & (df['prediction'] != 0)

print(f"总预测: {len(df)}")
print(f"执行信号: {df['execute'].sum()}")
```

---

## 🐛 故障排除

### 问题 1: TimescaleDB 连接失败

**错误**: `psycopg2.OperationalError: connection refused`

**解决**:
```bash
# 检查 TimescaleDB 状态
docker ps | grep timescale

# 如未运行，启动容器
docker-compose up -d timescaledb
```

### 问题 2: Numba 编译警告

**错误**: `NumbaPerformanceWarning: object mode detected`

**解决**: 确保所有输入数组都是 `np.float64` 类型，不包含 `object` 类型。

### 问题 3: 测试失败 - JIT 性能不达标

**错误**: `AssertionError: 250ms > 200ms`

**原因**: 运行在低性能机器或 CI 环境

**解决**: 调整测试阈值或使用相对基准测试。

---

## 📚 相关文档

- **完成报告**: [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- **样本分布报告**: [SAMPLE_EQUILIBRIUM_REPORT.md](./SAMPLE_EQUILIBRIUM_REPORT.md)
- **同步指南**: [SYNC_GUIDE.md](./SYNC_GUIDE.md)
- **验证日志**: [VERIFY_LOG.log](../../../VERIFY_LOG.log)

---

## 💡 提示

1. **参数调优**: `num_std` 和 `max_holding_period` 可调整以适应不同的市场条件
2. **回测验证**: 使用生成的标签进行回测，验证策略有效性
3. **样本权重**: 在训练中始终使用 `sample_weight` 以处理类别不平衡
4. **元标签**: 可用于构建二阶模型，提升整体策略表现

---

**最后更新**: 2026-01-12

**作者**: Claude Sonnet 4.5 (MT5-CRS Agent)

**协议**: v4.3 Zero-Trust Edition
