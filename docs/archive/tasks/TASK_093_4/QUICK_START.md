# Task #093.4: M1 数据与基准模型 - 快速启动指南

> 给人类看的"傻瓜式"启动/测试指南

---

## 目录

1. [环境检查](#环境检查)
2. [数据加载](#数据加载)
3. [特征工程](#特征工程)
4. [模型训练](#模型训练)
5. [模型预测](#模型预测)
6. [故障排查](#故障排查)

---

## 环境检查

### 依赖包

```bash
# 检查已安装的关键包
python3 -c "import pandas; import numpy; import xgboost; import numba; print('✅ All deps OK')"
```

**所需包**:
- `pandas` >= 1.3.0
- `numpy` >= 1.20.0
- `xgboost` >= 1.5.0
- `numba` >= 0.55.0
- `scikit-learn` >= 1.0.0

### API 密钥

```bash
# 检查 EODHD API 密钥
echo $EODHD_API_KEY  # 应显示密钥前10个字符
```

---

## 数据加载

### 选项 1: 使用已生成的数据（推荐）

```bash
# M1 原始数据已保存
ls -lh /opt/mt5-crs/data/processed/eurusd_m1_training.parquet

# 在 Python 中加载
import pandas as pd
df_m1 = pd.read_parquet('/opt/mt5-crs/data/processed/eurusd_m1_training.parquet')
print(df_m1.shape)  # (1890720, 6)
print(df_m1.head())
```

### 选项 2: 重新生成数据

```bash
cd /opt/mt5-crs
python3 src/data_loader/forex_m1_loader.py
```

**预期输出**:
```
✅ Generated 1,890,720 synthetic M1 candles
✅ Saved to: /opt/mt5-crs/data/processed/eurusd_m1_training.parquet
```

**耗时**: ~25秒

---

## 特征工程

### 运行特征管道

```bash
cd /opt/mt5-crs
python3 src/feature_engineering/big_data_pipeline.py
```

**预期输出**:
```
⚙️  Engineering features...
   - Price-based features...
   - Rolling technical indicators...
   - Fractional differentiation...
   - Volume features...
   - Range and volatility...
Shape: (1890720, 22)
Memory: 158.68 MB
Time: 4.69s

🏷️  Computing triple barrier labels...
   Labels computed: 1,890,720
   Distribution: 532680 DOWN, 544 NEUTRAL, 1357496 UP

✅ Saved to: /opt/mt5-crs/data/processed/eurusd_m1_features_labels.parquet
```

**耗时**: ~5秒

### 在 Python 中检查特征

```python
import pandas as pd
df_features = pd.read_parquet(
    '/opt/mt5-crs/data/processed/eurusd_m1_features_labels.parquet'
)

print(f"特征数: {len(df_features.columns) - 1}")  # 22
print(f"样本数: {len(df_features)}")  # 1,890,720
print(f"标签分布:\n{df_features.iloc[:, -1].value_counts().sort_index()}")

# 标签含义: 0=DOWN, 1=NEUTRAL, 2=UP
```

---

## 模型训练

### 运行基准模型训练

```bash
cd /opt/mt5-crs
python3 src/models/train_xgb_baseline.py
```

**预期输出**:
```
🎓 Training with 5-Fold Purged Cross-Validation...

   Fold 1/5...
     Accuracy: 0.7193
     F1 Score: 0.6033
     AUC: 0.7185

   ...（5折结果）...

Cross-Validation Results:
   Average Accuracy: 0.7194
   Average F1 Score: 0.6036
   Average AUC: 0.7181

✅ Model trained
💾 Model saved to: /opt/mt5-crs/models/baselines/xgb_m1_v1.json
```

**耗时**: ~26 分钟 (5折 CV)

### 在 Python 中加载模型

```python
import xgboost as xgb

# 加载模型
model = xgb.Booster()
model.load_model('/opt/mt5-crs/models/baselines/xgb_m1_v1.json')

print(f"模型树数: {model.num_boosted_rounds()}")  # 100
print(f"模型大小: {model.num_feature()}")  # 22 features
```

---

## 模型预测

### 单步预测

```python
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

# 加载特征与标签
df_features = pd.read_parquet(
    '/opt/mt5-crs/data/processed/eurusd_m1_features_labels.parquet'
)

X = df_features.iloc[:, :-1].values
y = df_features.iloc[:, -1].values

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 加载模型
model = xgb.Booster()
model.load_model('/opt/mt5-crs/models/baselines/xgb_m1_v1.json')

# 预测
pred = model.predict(xgb.DMatrix(X_scaled))
pred_labels = np.argmax(pred, axis=1)  # 取最高概率类

print(f"前10个预测: {pred_labels[:10]}")
print(f"预测分布: {np.bincount(pred_labels)}")
```

### 获取特征重要性

```python
import xgboost as xgb

model = xgb.Booster()
model.load_model('/opt/mt5-crs/models/baselines/xgb_m1_v1.json')

# 获取特征重要性
importance = model.get_score(importance_type='weight')

# 打印前10个重要特征
for feat, score in sorted(importance.items(),
                          key=lambda x: x[1],
                          reverse=True)[:10]:
    print(f"{feat}: {score}")
```

---

## 故障排查

### 问题 1: 内存不足 (OOM)

```
MemoryError: Unable to allocate XXX MB for array
```

**解决方案**:
```bash
# 检查可用内存
free -h

# 如果不足，使用分块处理
# 修改 big_data_pipeline.py:
# - 将 df.values 改为分块读取
# - 批量处理大小: 100k行
```

### 问题 2: XGBoost 类别不匹配

```
ValueError: Invalid classes inferred from unique values of `y`.
Expected: [0 1 2], got [-1 0 1]
```

**解决方案**:
```python
# 确保标签是 {0, 1, 2}
labels = labels + 1  # 从 {-1, 0, 1} 转换为 {0, 1, 2}
```

### 问题 3: 模型加载失败

```
RuntimeError: Error in loading the saved model format
```

**解决方案**:
```bash
# 检查模型文件是否存在并有效
ls -lh /opt/mt5-crs/models/baselines/xgb_m1_v1.json

# 重新训练模型
python3 src/models/train_xgb_baseline.py
```

### 问题 4: 数据文件不存在

```
FileNotFoundError: [Errno 2] No such file or directory: '...parquet'
```

**解决方案**:
```bash
# 检查数据目录
ls -lh /opt/mt5-crs/data/processed/

# 如果缺失，重新生成
python3 src/data_loader/forex_m1_loader.py
python3 src/feature_engineering/big_data_pipeline.py
```

---

## 性能基准

| 操作 | 耗时 | 内存 |
|-----|------|------|
| M1数据生成 | ~25s | 50 MB |
| 特征工程 | ~5s | 160 MB |
| 5-Fold CV训练 | ~26min | 2-3 GB |
| 单次预测 (1.8M行) | ~10s | 依赖样本数 |

---

## 文件位置

| 文件 | 路径 | 大小 |
|-----|------|------|
| M1原始数据 | `/opt/mt5-crs/data/processed/eurusd_m1_training.parquet` | 52 MB |
| 特征+标签 | `/opt/mt5-crs/data/processed/eurusd_m1_features_labels.parquet` | 128 MB |
| 基准模型 | `/opt/mt5-crs/models/baselines/xgb_m1_v1.json` | 1.7 MB |

---

## 联系方式

**问题反馈**: 提交 Issue 到 Git 仓库

**文档**: 见 `COMPLETION_REPORT.md`

---

**最后更新**: 2026-01-12

**状态**: ✅ 就绪
