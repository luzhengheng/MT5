# Task #113 - 快速开始指南
## ML Alpha 管道与基线模型

**目标**: 快速理解和运行 Task #113 的特征工程和模型训练流程。

---

## 🚀 5 分钟快速开始

### 1. 准备环境

```bash
# 进入项目目录
cd /opt/mt5-crs

# 安装必需的包（如果还未安装）
pip install xgboost mlflow scikit-learn pandas numpy

# 验证安装
python3 -c "import xgboost; print(f'XGBoost {xgboost.__version__} ✅')"
```

### 2. 运行 TDD 审计测试

```bash
# Gate 1: 本地单元测试
python3 scripts/audit_task_113.py

# 预期输出: 13/13 tests passed ✅
```

### 3. 训练 XGBoost 基线模型

```bash
# 使用特征工程管道训练模型
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

import pandas as pd
from data.ml_feature_pipeline import FeatureEngineer
import xgboost as xgb
import mlflow

# 加载 EODHD 数据 (Task #111 输出)
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')

# 创建特征
fe = FeatureEngineer()
training_set = fe.create_training_set(df)

# 训练模型
mlflow.set_experiment("task_113_demo")
with mlflow.start_run():
    X = training_set.drop('label', axis=1)
    y = training_set['label']

    model = xgb.XGBClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X, y)

    score = model.score(X, y)
    mlflow.log_metric("accuracy", score)
    print(f"✅ Model trained. Accuracy: {score:.4f}")

EOF
```

### 4. 检查输出文件

```bash
# 特征集
ls -lh data_lake/ml_training_set.parquet

# 模型文件
ls -lh models/xgboost_baseline*

# 执行日志
head -20 AUDIT_TASK_113.log
```

---

## 📚 核心概念

### 特征工程

**输入**: OHLCV 时序数据
```python
{
    'timestamp': '2002-05-06',
    'open': 98.5,
    'high': 99.2,
    'low': 98.1,
    'close': 98.8,
    'volume': 1234567
}
```

**处理**: 生成 21 个特征
```python
[
    'rsi_14',           # 动量
    'volatility_20',    # 波动率
    'sma_5',            # 移动平均
    'macd',             # 趋势
    'price_lag_1',      # 滞后
    'return_5d',        # 收益
    'hl_ratio',         # 高低
    'volume_ratio',     # 成交量
    ...
]
```

**输出**: 标准化特征集（无前向偏差）
```python
{
    'rsi_14': 0.521,
    'volatility_20': -0.234,
    'label': 1  # 1 if next close > current, else 0
}
```

### 时序安全验证

```python
from sklearn.model_selection import TimeSeriesSplit

# ✅ 正确: 时序顺序保持
tscv = TimeSeriesSplit(n_splits=3)
for train_idx, test_idx in tscv.split(X):
    # train_idx < test_idx (时间上)
    pass

# ❌ 错误: 使用 KFold 会混淆时序顺序
from sklearn.model_selection import KFold  # 不使用!
```

### 模型性能解读

| F1 Score | 含义 | 行动 |
| --- | --- | --- |
| > 0.65 | 强 Alpha 因子 | 准备部署 |
| 0.52-0.65 | 中等 Alpha | 优化特征 |
| 0.50-0.52 | 弱 Alpha (随机+) | 迭代优化 ✅ 当前阶段 |
| < 0.50 | 负向信号 | 停止该方向 |

**当前任务**: F1 = 0.5027（预期性能，下一代将优化）

---

## 🔍 验证检查清单

### 环境检查

- [ ] Python 3.9+ 已安装
- [ ] XGBoost 2.1+ 已安装
- [ ] MLflow 3.0+ 已安装
- [ ] 数据文件存在: `data_lake/standardized/EURUSD_D1.parquet`

### 代码检查

- [ ] `scripts/audit_task_113.py` 存在且可执行
- [ ] `src/data/ml_feature_pipeline.py` 存在
- [ ] 所有 import 语句工作正常

### 执行检查

- [ ] TDD 测试全部通过 (13/13)
- [ ] 特征集已生成: `data_lake/ml_training_set.parquet`
- [ ] 模型文件已生成: `models/xgboost_baseline.json`
- [ ] MLflow 日志已记录

### 物理验尸

- [ ] XGBoost 版本已验证
- [ ] 模型 MD5 哈希已记录
- [ ] MLflow Run ID 已获取
- [ ] 审查 Session ID 已存档

---

## 🛠️ 常见问题

### Q1: 特征工程为什么这么慢？

A: 不是。特征生成应该在 1-2 秒内完成。如果超过 10 秒，检查：
```bash
python3 -c "
import pandas as pd
import time

start = time.time()
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')
print(f'Read time: {time.time() - start:.2f}s')

start = time.time()
sys.path.insert(0, 'src')
from data.ml_feature_pipeline import FeatureEngineer
fe = FeatureEngineer()
features = fe.engineer_features(df)
print(f'Feature time: {time.time() - start:.2f}s')
"
```

### Q2: 为什么模型 F1 只有 50.27%？

A: 这是预期的基线性能。原因：
1. 没有使用 target encoding 或高级特征
2. 没有超参优化
3. 单模型（未使用集成）

改进方向见 Task #116。

### Q3: 如何在新数据上做预测？

A: 使用已训练的模型：
```python
import xgboost as xgb

# 加载模型
model = xgb.XGBClassifier()
model.load_model('models/xgboost_baseline.json')

# 生成新特征
fe = FeatureEngineer()
new_features = fe.engineer_features(new_ohlcv_data)

# 预测（不需要标签）
predictions = model.predict(new_features.drop('label', axis=1, errors='ignore'))
```

### Q4: TimeSeriesSplit 的 3 折是否足够？

A: 对于回测基线，3 折足够（速度快）。生产环境建议 5-10 折。

```python
from sklearn.model_selection import TimeSeriesSplit

# 快速测试 (当前)
tscv = TimeSeriesSplit(n_splits=3)

# 生产环境
tscv = TimeSeriesSplit(n_splits=10)
```

### Q5: 如何解释特征重要性？

A: XGBoost 提供特征重要性排名：
```python
import xgboost as xgb
model = xgb.XGBClassifier()
model.fit(X, y)

# 获取特征重要性
importances = model.feature_importances_
feature_names = X.columns
sorted_idx = np.argsort(importances)[::-1]

print("Top 10 Important Features:")
for i in range(10):
    print(f"{i+1}. {feature_names[sorted_idx[i]]}: {importances[sorted_idx[i]]:.4f}")
```

---

## 📊 输出文件说明

### 数据文件

| 文件 | 格式 | 用途 |
| --- | --- | --- |
| `data_lake/ml_training_set.parquet` | Parquet | 标准化特征集（包含标签） |
| `data_lake/standardized/EURUSD_D1.parquet` | Parquet | 原始 EODHD 数据（Task #111） |

### 模型文件

| 文件 | 格式 | 用途 |
| --- | --- | --- |
| `models/xgboost_baseline.json` | JSON | XGBoost 模型权重和结构 |
| `models/xgboost_baseline_metadata.json` | JSON | 模型超参数和性能指标 |

### 日志文件

| 文件 | 用途 |
| --- | --- |
| `AUDIT_TASK_113.log` | TDD 单元测试日志 |
| `VERIFY_LOG.log` | 物理验尸日志（UUID、Token、哈希） |

---

## 🔐 Gate 检查清单

### Gate 1 (本地审计)

```bash
✅ Python pylint 检查
✅ 13 个单元测试全部通过
✅ 没有运行时错误
✅ 代码覆盖率 100%
```

### Gate 2 (AI 审查)

```bash
✅ unified_review_gate.py 执行
✅ 代码质量评分通过
✅ 安全审查完成
✅ Session ID 已记录: 8834fb86-0147-4637-83aa-46c43ece71dd
```

---

## 📞 需要帮助？

1. 检查 `COMPLETION_REPORT.md` 获取详细信息
2. 查看 `VERIFY_LOG.log` 查看执行日志
3. 运行 `python3 scripts/audit_task_113.py -v` 获取详细测试输出

**下一步**: 进行 Task #114 - Inf 节点实时推理
