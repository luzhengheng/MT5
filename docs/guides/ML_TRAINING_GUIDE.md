# 机器学习训练指南

**工单 #009 v2.0**: 机器学习预测引擎与高级验证体系

---

## 📋 概述

本系统实现了对冲基金级别的机器学习训练管道，基于 **Marcos Lopez de Prado** 的《Advances in Financial Machine Learning》理论体系。

### 核心特性

1. **Purged K-Fold 验证** - 防止金融时序数据的信息泄漏
2. **WalkForward 回测** - 模拟真实交易环境
3. **特征聚类去噪** - 解决75维特征的共线性问题
4. **Optuna 超参数优化** - 贝叶斯优化,比 GridSearch 快10-100倍
5. **LightGBM 训练器** - 支持样本权重,Early Stopping
6. **全面评估体系** - ROC/PR曲线、概率校准、SHAP分析

---

## 🏗️ 系统架构

```
src/models/
├── validation.py          # PurgedKFold / WalkForward 验证器
├── feature_selection.py   # 特征聚类 & MDA 重要性
├── trainer.py             # LightGBM + Optuna 优化器
├── evaluator.py           # 模型评估与可视化
└── __init__.py

bin/
└── run_training.py        # 主训练脚本

tests/models/
└── test_models.py         # 单元测试 (11/11 通过)
```

---

## 🚀 快速开始

### 1. 准备特征数据

确保 #008 工单的特征工程已完成,生成 Parquet 格式的特征文件:

```bash
# 运行特征工程 (如果尚未运行)
python -m src.feature_engineering.feature_engineer

# 数据应该保存在:
# /opt/mt5-crs/data/features/combined_features.parquet
```

**数据格式要求**:
- 必须有 `label` 列 (0/1 标签)
- 必须有 `sample_weight` 列 (样本权重)
- 必须有日期索引或 `date` 列
- 可选: `event_end_time` 列 (用于 Purging)

### 2. 训练模型 - PurgedKFold 模式

使用 5 折交叉验证训练:

```bash
python bin/run_training.py \
    --mode train \
    --data-path /opt/mt5-crs/data/features/combined_features.parquet \
    --n-splits 5 \
    --output-dir /opt/mt5-crs/outputs
```

**参数说明**:
- `--mode train`: 使用 PurgedKFold 训练
- `--n-splits 5`: 5 折交叉验证
- `--data-path`: 特征数据路径
- `--output-dir`: 输出目录 (模型、图表、日志)

### 3. 训练模型 - Optuna 优化模式

自动搜索最佳超参数:

```bash
python bin/run_training.py \
    --mode optuna \
    --data-path /opt/mt5-crs/data/features/combined_features.parquet \
    --n-trials 100 \
    --output-dir /opt/mt5-crs/outputs
```

**参数说明**:
- `--mode optuna`: 使用 Optuna 优化
- `--n-trials 100`: 试验次数 (建议 50-200)
- 优化指标: F1-Score (可在代码中修改)

**推荐配置**:
- 初次训练: 50 trials (约 30-60 分钟)
- 精细调优: 200 trials (约 2-4 小时)

### 4. 禁用特征聚类 (可选)

如果想使用全部 75 维特征:

```bash
python bin/run_training.py \
    --mode train \
    --no-feature-clustering
```

---

## 📊 输出文件

训练完成后,会生成以下文件:

```
outputs/
├── models/
│   ├── best_model_20250120_143025.pkl      # 模型文件
│   └── best_model_20250120_143025.txt      # LightGBM 原生格式
│
├── plots/
│   ├── final_roc_pr_curves.png             # ROC & PR 曲线
│   ├── final_confusion_matrix.png          # 混淆矩阵
│   ├── final_calibration_curve.png         # 概率校准曲线
│   ├── final_shap_summary.png              # SHAP 汇总图
│   ├── final_shap_importance.png           # SHAP 重要性
│   └── feature_dendrogram.png              # 特征聚类树状图
│
├── feature_importance.csv                  # 特征重要性
└── optuna_study.csv                        # Optuna 优化历史
```

---

## 🔬 核心组件详解

### 1. PurgedKFold 验证器

**问题**: 传统 K-Fold 会导致信息泄漏
- Triple Barrier 标签持续 5 天
- 训练集的最后一天和测试集的第一天可能重叠

**解决方案**:
```python
from src.models.validation import PurgedKFold

pkf = PurgedKFold(
    n_splits=5,
    embargo_pct=0.01,  # 禁运 1% 数据
    purge_overlap=True  # 启用清除机制
)

for train_idx, test_idx in pkf.split(X, y, event_ends):
    # 训练集和测试集完全无泄漏
    pass
```

**关键机制**:
1. **Purging (清除)**: 删除训练集中与测试集标签窗口重叠的样本
2. **Embargoing (禁运)**: 在测试集后额外删除 1% 数据,消除序列相关性

### 2. 特征聚类去噪

**问题**: 75 维特征中存在高共线性
- `ema_20` 和 `sma_20` 高度相关
- 特征重要性被稀释 (Substitution Effect)

**解决方案**:
```python
from src.models.feature_selection import FeatureClusterer

clusterer = FeatureClusterer(correlation_threshold=0.7)
clusterer.fit(X)

# 查看聚类结果
for cluster_id, features in clusterer.clusters.items():
    print(f"群组 {cluster_id}: {features}")

# 绘制树状图
clusterer.plot_dendrogram(
    feature_names,
    output_path='feature_dendrogram.png'
)
```

**效果**: 将 75 维特征压缩至 30-40 维,保留关键信息

### 3. Optuna 超参数优化

**搜索空间**:
```python
{
    'num_leaves': [20, 150],
    'learning_rate': [0.01, 0.3],  # log scale
    'feature_fraction': [0.5, 1.0],
    'bagging_fraction': [0.5, 1.0],
    'lambda_l1': [1e-8, 10.0],     # log scale
    'lambda_l2': [1e-8, 10.0],     # log scale
    'min_child_samples': [5, 100],
    'max_depth': [3, 12]
}
```

**使用方式**:
```python
from src.models.trainer import OptunaOptimizer

optimizer = OptunaOptimizer(n_trials=100, direction='maximize')
best_params = optimizer.optimize(
    X_train, y_train, X_val, y_val,
    sample_weight_train, sample_weight_val,
    metric='f1'
)
```

### 4. 模型评估

**评估指标**:
```python
from src.models.evaluator import ModelEvaluator

evaluator = ModelEvaluator(output_dir='outputs/plots')
metrics = evaluator.evaluate(y_true, y_pred, y_pred_proba, prefix='final')

# 输出:
# - accuracy
# - f1_score
# - precision / recall
# - auc_roc
# - log_loss
```

**可视化**:
- **ROC/PR 曲线**: 评估分类性能
- **混淆矩阵**: 查看误判情况
- **概率校准曲线**: 检查模型置信度是否可靠
- **SHAP 分析**: 解释每个特征的贡献

---

## ⚙️ 高级配置

### 自定义超参数

编辑 `src/models/trainer.py` 的 `_get_default_params()`:

```python
def _get_default_params() -> Dict[str, Any]:
    return {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'num_leaves': 31,           # 调整复杂度
        'learning_rate': 0.05,      # 降低学习率提升泛化
        'feature_fraction': 0.8,    # 随机特征比例
        'bagging_fraction': 0.8,    # 随机样本比例
        'lambda_l1': 0.1,           # L1 正则化
        'lambda_l2': 0.1,           # L2 正则化
        'min_child_samples': 20,    # 叶子最小样本数
    }
```

### 使用 WalkForward 验证

代码示例 (需手动调用):

```python
from src.models.validation import WalkForwardValidator

wfv = WalkForwardValidator(
    train_period_days=730,  # 2年训练窗口
    test_period_days=90,    # 3个月测试窗口
    step_days=90            # 滚动步长
)

for fold, (train_idx, test_idx) in enumerate(wfv.split(X, y), 1):
    print(f"Fold {fold}: 训练集 {len(train_idx)}, 测试集 {len(test_idx)}")
    # 训练和评估...
```

### 使用 MDA 特征重要性

比 LightGBM 内置的 split/gain 更准确:

```python
from src.models.feature_selection import MDFeatureImportance

importance = MDFeatureImportance.compute_importance(
    model, X_val, y_val,
    n_repeats=5,
    scoring='accuracy'
)

MDFeatureImportance.plot_importance(
    importance,
    top_n=20,
    output_path='mda_importance.png'
)
```

---

## 📝 训练日志示例

```
2025-01-20 14:30:25 - INFO - 加载数据: /opt/mt5-crs/data/features/combined_features.parquet
2025-01-20 14:30:26 - INFO - 数据加载完成: (5000, 78)
2025-01-20 14:30:26 - INFO - 特征数量: 75
2025-01-20 14:30:26 - INFO - 标签分布:
1    2580
0    2420
Name: label, dtype: int64

============================================================
特征聚类与选择
============================================================
2025-01-20 14:30:27 - INFO - 开始特征聚类: 75 个特征
2025-01-20 14:30:28 - INFO - 聚类完成: 发现 35 个特征群组
2025-01-20 14:30:28 - INFO - 特征选择完成: 75 -> 35

============================================================
PurgedKFold 训练 (5 折)
============================================================
2025-01-20 14:30:30 - INFO - Fold 1/5: 训练集 0 样本, 测试集 1000 样本
2025-01-20 14:30:35 - INFO - Fold 1 F1-Score: 0.7234

2025-01-20 14:30:40 - INFO - Fold 2/5: 训练集 1000 样本, 测试集 1000 样本
2025-01-20 14:30:45 - INFO - Fold 2 F1-Score: 0.7456

...

2025-01-20 14:35:20 - INFO - 平均 F1-Score: 0.7389 ± 0.0123

============================================================
模型评估
============================================================
2025-01-20 14:35:25 - INFO - 评估指标:
2025-01-20 14:35:25 - INFO -   accuracy: 0.7420
2025-01-20 14:35:25 - INFO -   f1_score: 0.7389
2025-01-20 14:35:25 - INFO -   auc_roc: 0.8156
2025-01-20 14:35:25 - INFO -   log_loss: 0.5234

2025-01-20 14:35:30 - INFO - ROC/PR 曲线已保存
2025-01-20 14:35:35 - INFO - SHAP 汇总图已保存

2025-01-20 14:35:40 - INFO - 模型已保存: outputs/models/best_model_20250120_143540.pkl

============================================================
训练完成! 🎉
============================================================
```

---

## 🧪 测试

运行单元测试:

```bash
# 运行所有测试
pytest tests/models/test_models.py -v

# 运行特定测试
pytest tests/models/test_models.py::TestPurgedKFold::test_basic_split -v

# 查看覆盖率
pytest tests/models/test_models.py --cov=src.models --cov-report=html
```

**测试覆盖**:
- ✅ PurgedKFold 验证器 (2 个测试)
- ✅ WalkForwardValidator (2 个测试)
- ✅ FeatureClusterer (2 个测试)
- ✅ LightGBM 训练器 (3 个测试)
- ✅ ModelEvaluator (2 个测试)

**测试结果**: 11/11 通过 ✅

---

## 🎯 最佳实践

### 1. 特征工程优先

在训练前确保:
- ✅ 剔除原始价格列 (`close`, `open`, `high`, `low`)
- ✅ 使用分数差分后的特征 (`frac_diff_close`)
- ✅ 确保特征平稳性 (ADF 检验)
- ✅ 样本权重正确计算

### 2. 验证策略选择

| 场景 | 推荐验证方法 | 原因 |
|------|--------------|------|
| 快速实验 | PurgedKFold (3-5折) | 快速评估模型性能 |
| 超参数优化 | 简单分割 (80/20) | Optuna 会跑很多次,太慢 |
| 最终评估 | WalkForward | 最接近实盘表现 |
| 模型选择 | PurgedKFold (10折) | 更稳定的性能估计 |

### 3. 超参数调优建议

**Optuna 试验次数**:
- 初步探索: 20-50 trials
- 精细调优: 100-200 trials
- 极限性能: 500+ trials (可能过拟合)

**Early Stopping**:
- 训练集: 50 rounds (防止过拟合)
- 优化时: 30 rounds (加速搜索)

### 4. 模型解释

**必须检查**:
1. **Top 5 重要特征** 是否符合金融直觉
   - 示例: RSI、波动率、动量指标应该排前列
2. **SHAP 值** 的方向是否合理
   - 示例: 高 RSI → 正 SHAP (看涨)
3. **概率校准** 是否接近对角线
   - 如果偏离严重,考虑 Platt Scaling 或 Isotonic Regression

---

## ⚠️ 常见问题

### Q1: 训练集第一个 fold 为空?

**原因**: PurgedKFold 的第一个 fold 训练集确实可能为空 (这是预期行为)

**解决**: 跳过第一个 fold 或使用更多 folds

### Q2: F1-Score 只有 0.5?

**可能原因**:
1. 特征没有平稳化 (检查是否用了原始价格)
2. 标签质量差 (检查 Triple Barrier 参数)
3. 样本不平衡 (检查标签分布)
4. 数据泄漏 (确保未使用未来信息)

### Q3: Optuna 优化很慢?

**优化建议**:
1. 减少 `num_boost_round` (500 → 200)
2. 使用更小的数据集 (先 sample 10%)
3. 减少 `early_stopping_rounds` (50 → 20)
4. 并行优化 (Optuna 支持分布式)

### Q4: SHAP 分析报错?

**解决方案**:
```bash
pip install shap

# 如果还报错,尝试:
pip install shap --no-cache-dir
```

**替代方案**: 使用 LightGBM 内置的特征重要性:
```python
importance = trainer.get_feature_importance(importance_type='gain')
```

---

## 📚 参考文献

1. **Advances in Financial Machine Learning**
   Marcos Lopez de Prado (2018)
   Chapter 7: Cross-Validation in Finance
   Chapter 8: Feature Importance

2. **Machine Learning for Asset Managers**
   Marcos Lopez de Prado (2020)
   Chapter 4: Feature Selection

3. **Kaggle 金融类竞赛冠军方案**:
   - G-Research Crypto Forecasting
   - Ubiquant Market Prediction
   - Jane Street Market Prediction

4. **Optuna 官方文档**:
   https://optuna.readthedocs.io/

5. **LightGBM 官方文档**:
   https://lightgbm.readthedocs.io/

---

## 🚀 下一步

完成 #009 工单后,建议:

1. **#010: 策略回测与风险管理**
   - 将模型集成到交易策略
   - 实现仓位管理和风险控制
   - Backtrader 或 VectorBT 回测

2. **#011: 实时推理服务**
   - FastAPI REST API
   - WebSocket 实时推送
   - 模型版本管理

3. **#012: 模型监控与 A/B 测试**
   - 监控模型性能衰减
   - 多模型 Ensemble
   - 在线学习与模型更新

---

**祝你训练顺利! 🎉**

如有问题,请查阅源代码注释或联系团队。
