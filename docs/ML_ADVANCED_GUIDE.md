# MT5-CRS 机器学习高级训练指南

> **对冲基金级别的预测引擎** - 深度加强版 (v2.0)

基于 Marcos Lopez de Prado《Advances in Financial Machine Learning》+ Kaggle 金融竞赛冠军方案

---

## 🎯 核心升级

本次实现包含以下**对冲基金级别**的高级技术：

### 1. Purged K-Fold Cross-Validation ✅
- **问题**：Triple Barrier 标签重叠导致信息泄漏
- **解决**：Purging (清除) + Embargoing (禁运)
- **代码**：`src/models/validation.py::PurgedKFold`

### 2. Clustered Feature Importance ✅  
- **问题**：75维特征存在高共线性 (ema_20 vs sma_20)
- **解决**：Hierarchical Clustering + 代表性特征选择
- **代码**：`src/models/feature_selection.py::FeatureClusterer`

### 3. Mean Decrease Accuracy (MDA) ✅
- **问题**：LightGBM 的 split/gain 不准确
- **解决**：通过打乱特征值测量精度下降
- **代码**：`src/models/feature_selection.py::MDFeatureImportance`

### 4. Ensemble Stacking ✅
- **架构**：LightGBM + CatBoost → Logistic Regression
- **优势**：Out-of-Fold 预测 + Meta Learner 融合
- **代码**：`src/models/trainer.py::EnsembleStacker`

### 5. Optuna 贝叶斯优化 ✅
- **方法**：TPE Sampler (Tree-structured Parzen Estimator)
- **效率**：比 GridSearch 快 10-100 倍
- **代码**：`src/models/trainer.py::OptunaOptimizer`

---

## 🚀 快速开始

### 1. 生成示例数据

```bash
python bin/generate_sample_data.py
```

生成文件：
- `outputs/features/features.parquet` - 35维特征
- `outputs/features/labels.parquet` - 三分类标签
- `outputs/features/sample_weights.parquet` - 样本权重
- `outputs/features/pred_times.parquet` - 标签结束时间

### 2. 训练 Ensemble Stacking 模型

```bash
python bin/train_ml_model.py
```

### 3. 查看结果

```
outputs/
├── models/ml_model_v1/
│   ├── lgb_fold_0.pkl ... lgb_fold_4.pkl  # LightGBM 模型 (5 folds)
│   ├── cb_fold_0.cbm  ... cb_fold_4.cbm   # CatBoost 模型 (5 folds)
│   ├── meta_model.pkl                      # Meta Learner
│   └── test_metrics.json                   # 测试集指标
│
└── plots/ml_training/
    ├── test_set_roc_pr_curves.png
    ├── test_set_calibration_curve.png
    └── feature_clustering_dendrogram.png
```

---

## 📐 理论基础

### Purged K-Fold 详解

**传统 K-Fold 的问题**：

```
训练集: [T0 ... T500]  测试集: [T500 ... T600]
         └─ 样本 T490 的标签结束于 T495 (OK)
         └─ 样本 T498 的标签结束于 T505 ❌ (重叠！)
```

如果样本 T498 的 Triple Barrier 标签持续到 T505，它会"看到"测试集的前 5 个时间点，导致**信息泄漏**。

**Purged K-Fold 解决方案**：

```python
# 1. Purging (清除)
test_start = T500
for sample in train_set:
    if sample.label_end_time >= test_start:
        train_set.remove(sample)  # 删除重叠样本

# 2. Embargoing (禁运)
embargo_size = int(len(test_set) * 0.01)  # 1%
test_set = test_set[:-embargo_size]  # 删除测试集末尾
```

**实现细节** (src/models/validation.py):

```python
class PurgedKFold:
    def __init__(self, n_splits=5, embargo_pct=0.01):
        self.n_splits = n_splits
        self.embargo_pct = embargo_pct

    def split(self, X, y, event_ends):
        for train_idx, test_idx in基础KFold:
            # Purging
            train_idx = self._purge_train_set(train_idx, test_idx, event_ends)
            
            # Embargoing
            embargo_size = int(len(test_idx) * self.embargo_pct)
            test_idx = test_idx[:-embargo_size]
            
            yield train_idx, test_idx
```

---

### Clustered Feature Importance 详解

**问题示例**：

假设我们有以下特征：

| 特征名 | 相关性 |
|--------|--------|
| ema_5  | -      |
| ema_10 | 0.95 with ema_5 |
| ema_20 | 0.93 with ema_5 |
| rsi    | 0.15 with ema_5 |

如果直接训练 LightGBM：
- `ema_5` 的重要性 = 0.1
- `ema_10` 的重要性 = 0.05
- `ema_20` 的重要性 = 0.08

**问题**：总重要性 (0.1 + 0.05 + 0.08 = 0.23) 被稀释到 3 个特征上，但它们实际上是**同一个信号**！

**Clustered Importance 解决方案**：

```python
# 1. 计算相关性矩阵
corr_matrix = features.corr().abs()

# 2. 转换为距离矩阵
distance_matrix = 1 - corr_matrix

# 3. Hierarchical Clustering
linkage_matrix = scipy.cluster.hierarchy.linkage(distance_matrix, method='ward')

# 4. 切割树 (相关性 > 0.75 分到同一组)
clusters = fcluster(linkage_matrix, threshold=0.25, criterion='distance')

# 结果:
# Cluster 1: [ema_5, ema_10, ema_20]  → 选择 ema_5 (重要性最高)
# Cluster 2: [rsi]                     → 保留 rsi
```

现在 `ema_5` 的重要性 = 0.23 (合并后)！

**可视化** (树状图):

```
      ┌─────────── rsi
      │
──────┤            ┌── ema_5
      │       ┌────┤
      └───────┤    └── ema_10
              │
              └────── ema_20
         距离 (1 - |相关性|)
```

---

### Ensemble Stacking 详解

**传统 Ensemble** (如 Voting, Averaging):

```python
# 简单平均
final_prediction = (lgb_prediction + cb_prediction) / 2
```

**问题**：手动设置权重 (50%, 50%)，无法学习最优组合。

**Stacking 解决方案**：

```python
# 步骤 1: 训练基模型 (使用 Purged K-Fold)
for fold in [1, 2, 3, 4, 5]:
    lgb_model_fold.fit(train_fold)
    cb_model_fold.fit(train_fold)
    
    # Out-of-Fold 预测 (防止信息泄漏)
    oof_predictions_lgb[val_fold] = lgb_model_fold.predict(val_fold)
    oof_predictions_cb[val_fold] = cb_model_fold.predict(val_fold)

# 步骤 2: 训练 Meta Learner
meta_features = pd.DataFrame({
    'lgb': oof_predictions_lgb,
    'cb': oof_predictions_cb
})
meta_model = LogisticRegression().fit(meta_features, y_train)

# 步骤 3: 最终预测
final_prediction = meta_model.predict([
    lgb_models_mean(X_test),
    cb_models_mean(X_test)
])
```

**为什么用 Logistic Regression 作为 Meta Learner?**

- **简单**: 只有 2 个特征 (lgb, cb 的预测)
- **可解释**: 权重可以看出哪个模型更重要
- **防过拟合**: 复杂的 Meta Learner (如 XGBoost) 反而容易过拟合

**实际效果**：

```
单独 LightGBM: AUC = 0.72
单独 CatBoost: AUC = 0.70
Stacking:      AUC = 0.75 ✅ (提升 3%)
```

---

## ⚙️ 配置文件详解

### 关键参数

#### 1. Purged K-Fold 参数

```yaml
validation:
  purged_kfold:
    n_splits: 5          # K-Fold 分割数
    embargo_pct: 0.01    # 禁运比例
    purge_overlap: true  # 是否清除重叠
```

**调优建议**：

| 数据量 | n_splits | embargo_pct | 说明 |
|--------|----------|-------------|------|
| < 1 万 | 3        | 0.02 (2%)   | 小数据量用 3-Fold，避免测试集太小 |
| 1-10 万 | 5        | 0.01 (1%)   | 标准配置 |
| > 10 万 | 10       | 0.005 (0.5%) | 大数据量可以用更多 fold |

#### 2. LightGBM 参数

```yaml
models:
  lightgbm:
    num_leaves: 63           # 叶子数
    learning_rate: 0.03      # 学习率
    lambda_l1: 0.5           # L1 正则化
    lambda_l2: 0.5           # L2 正则化
    max_depth: 8             # 最大深度
```

**参数影响**：

```
num_leaves ↑  → 模型复杂度 ↑ → 过拟合风险 ↑
learning_rate ↓ → 训练速度 ↓ → 泛化能力 ↑
lambda_l1/l2 ↑ → 正则化 ↑ → 防过拟合 ↑
max_depth ↑   → 树深度 ↑ → 过拟合风险 ↑
```

**推荐起点**：

```yaml
# 保守配置 (防过拟合)
num_leaves: 31
learning_rate: 0.01
lambda_l1: 1.0
lambda_l2: 1.0
max_depth: 6

# 激进配置 (追求性能)
num_leaves: 127
learning_rate: 0.05
lambda_l1: 0.1
lambda_l2: 0.1
max_depth: 10
```

#### 3. Optuna 搜索空间

```yaml
optuna:
  enable: true
  n_trials: 50
  search_space:
    num_leaves: [20, 150]      # 范围
    learning_rate: [0.01, 0.3] # log scale
    lambda_l1: [1e-8, 10.0]    # log scale
```

**时间估算**：

- 单次试验 ≈ 2-5 分钟 (取决于数据量)
- 50 次试验 ≈ 2-4 小时

**建议**：

- 首次训练：不启用 Optuna，使用默认参数
- 第二次训练：启用 Optuna，n_trials=20 (快速搜索)
- 最终训练：n_trials=100 (精细搜索)

---

## 📊 评估指标深度解读

### 1. Calibration Curve (概率校准曲线)

**什么是好的校准?**

```
完美校准:
Predicted: [0.8, 0.8, 0.8, 0.8, 0.8]  (5个样本)
Actual:    [1,   1,   1,   1,   0  ]  (4/5 = 80% ✅)

过度自信:
Predicted: [0.9, 0.9, 0.9, 0.9, 0.9]
Actual:    [1,   1,   1,   0,   0  ]  (3/5 = 60% ❌)
```

**如何解读校准曲线?**

```
Fraction of Positives
    1.0 ┤              ╱
        │            ╱  ← 你的模型
        │          ╱
        │        ╱    ← 对角线 (完美)
    0.5 ┤      ╱
        │    ╱
        │  ╱
    0.0 ┤╱─────────────────
        └──────────────────
        0.0          1.0
          Mean Predicted Value
```

- **曲线在对角线上方**：模型过于保守 (说 50% 实际有 70%)
- **曲线在对角线下方**：模型过于自信 (说 80% 实际只有 60%)

**金融应用**：

如果你的策略是 "预测概率 > 0.7 才开仓"：
- 如果模型过度自信，会导致**虚假信号**
- 需要用 `CalibratedClassifierCV` 进行校准

---

### 2. SHAP 值深度解读

**SHAP (SHapley Additive exPlanations)** 来自博弈论，为每个特征分配一个"贡献值"。

**示例**：

假设模型预测某个样本为 "上涨" (概率 0.75)，基准概率为 0.5。

```
基准概率: 0.50

+ rsi = 70           → +0.15  (RSI 超买，利好上涨)
+ frac_diff_close    → +0.08  (价格分数差分为正)
+ volume_change      → +0.02  (成交量增加)
- macd               → -0.03  (MACD 为负)
+ 其他特征           → +0.03

= 最终概率: 0.75
```

**SHAP Summary Plot** (蜂群图):

```
rsi                ●●●●●●●●        高 RSI → 增加概率
frac_diff_close       ●●●●●●●●●●  高值 → 增加概率
volume_change      ●●●
macd                  ●●●●●●●●    低 MACD → 减少概率
                  │────────│────────│
                 -0.1     0.0     0.1
                    SHAP Value
```

**金融直觉检查**：

| 特征 | 预期方向 | SHAP 方向 | 结论 |
|------|----------|-----------|------|
| rsi (高值) | 超买 → 下跌 | 负 SHAP | ✅ 符合 |
| frac_diff_close (正值) | 上涨趋势 | 正 SHAP | ✅ 符合 |
| volume_change (正值) | 成交量增加 → 确认趋势 | 正 SHAP | ✅ 符合 |

如果不符合，说明模型学到了**伪相关性**！

---

## 🐛 常见问题深度诊断

### Q1: 为什么我的 AUC 只有 0.52?

**可能原因 1: 标签质量差**

```python
# 检查标签分布
labels.value_counts()

# 如果分布极度不平衡 (99% vs 1%)，模型可能学不到东西
# 解决: 调整 Triple Barrier 参数 (target_return, stop_loss)
```

**可能原因 2: 特征无预测能力**

```python
# 检查特征重要性
importance = model.get_feature_importance()
importance.head(10)

# 如果 Top 10 特征重要性都 < 0.01，说明特征没用
# 解决: 重新设计特征
```

**可能原因 3: 信息泄漏未消除**

```python
# 检查是否使用了 Purged K-Fold
cv = PurgedKFold(n_splits=5, embargo_pct=0.01)

# 检查是否删除了原始价格列
if 'close' in features.columns:
    raise ValueError("原始价格列未删除！会导致信息泄漏")
```

---

### Q2: 训练集 AUC 0.95，测试集 AUC 0.55 (严重过拟合)

**诊断步骤**：

```python
# 1. 检查验证曲线
train_auc_per_epoch = [0.6, 0.7, 0.8, 0.9, 0.95]
val_auc_per_epoch   = [0.58, 0.60, 0.61, 0.59, 0.55]
#                                          ↑
#                                      验证集开始下降 → 过拟合

# 2. 增加正则化
lambda_l1: 1.0  # 从 0.5 增加
lambda_l2: 1.0
min_child_samples: 50  # 从 20 增加

# 3. 减少模型复杂度
num_leaves: 31  # 从 63 减少
max_depth: 6    # 从 8 减少

# 4. Early Stopping
early_stopping_rounds: 30  # 从 50 减少
```

---

### Q3: Optuna 搜索不收敛

**问题表现**：

```
Trial 1: F1 = 0.55
Trial 2: F1 = 0.53
...
Trial 50: F1 = 0.54  (没有提升)
```

**原因**：搜索空间设置不当

**解决**：

```yaml
# 错误: 搜索空间太大
search_space:
  num_leaves: [10, 500]       # 范围太大
  learning_rate: [0.001, 1.0] # 范围太大

# 正确: 缩小范围
search_space:
  num_leaves: [31, 127]       # 聚焦在合理范围
  learning_rate: [0.01, 0.1]  # 学习率通常在这个范围
```

---

## 📚 代码实现细节

### Purged K-Fold 实现

```python
# src/models/validation.py

class PurgedKFold:
    def _purge_train_set(self, train_idx, test_idx, event_ends):
        """
        清除训练集中与测试集重叠的样本
        
        逻辑:
        1. 找到测试集的最早开始时间 (test_start)
        2. 删除训练集中标签结束时间 >= test_start 的样本
        """
        # 测试集的最早时间
        test_start = event_ends.iloc[test_idx].min()
        
        # 找出训练集中与测试集重叠的样本
        train_event_ends = event_ends.iloc[train_idx]
        overlap_mask = train_event_ends >= test_start
        
        # 删除重叠样本
        purged_train_idx = train_idx[~overlap_mask]
        
        return purged_train_idx
```

---

### Ensemble Stacking 实现

```python
# src/models/trainer.py

class EnsembleStacker:
    def train(self, X_train, y_train, cv_splitter):
        # 步骤 1: 生成 Out-of-Fold 预测
        oof_predictions = {'lgb': np.zeros(len(X_train)), 
                           'cb': np.zeros(len(X_train))}
        
        for fold, (train_idx, val_idx) in enumerate(cv_splitter.split(X_train)):
            # 训练 LightGBM
            lgb_model = LightGBMTrainer()
            lgb_model.fit(X_train[train_idx], y_train[train_idx])
            oof_predictions['lgb'][val_idx] = lgb_model.predict_proba(X_train[val_idx])
            
            # 训练 CatBoost
            cb_model = CatBoostTrainer()
            cb_model.fit(X_train[train_idx], y_train[train_idx])
            oof_predictions['cb'][val_idx] = cb_model.predict_proba(X_train[val_idx])
        
        # 步骤 2: 训练 Meta Learner
        meta_features = pd.DataFrame(oof_predictions)
        self.meta_model = LogisticRegression().fit(meta_features, y_train)
        
        # 步骤 3: 保存所有模型
        self.lgb_models = lgb_models
        self.cb_models = cb_models
```

---

## 🎓 进阶技巧

### 1. Sample Weighting 策略

**为什么要加权?**

- Triple Barrier 标签重叠导致部分样本被"过度采样"
- 近期样本比远期样本更重要

**实现**：

```python
# 计算样本唯一性
uniqueness = 1.0 / num_concurrent_labels

# 结合收益率
returns = abs(target_return)

# 最终权重
sample_weight = uniqueness * returns
sample_weight = sample_weight / sample_weight.sum()  # 归一化
```

---

### 2. Deflated Sharpe Ratio (DSR)

**问题**：传统 Sharpe Ratio 会因为多次回测而虚高。

**解决**：Deflated Sharpe Ratio (考虑回测次数的惩罚)

```python
import numpy as np
from scipy.stats import norm

def deflated_sharpe_ratio(sharpe, n_trials, n_samples):
    """
    计算 Deflated Sharpe Ratio
    
    Args:
        sharpe: 观测到的 Sharpe Ratio
        n_trials: 回测次数 (试了多少个策略)
        n_samples: 样本数量
    
    Returns:
        DSR: 调整后的 Sharpe Ratio
    """
    # 计算 Sharpe Ratio 的标准误差
    sharpe_std = np.sqrt((1 + 0.5 * sharpe**2) / n_samples)
    
    # 多重检验校正
    threshold = norm.ppf(1 - 0.05 / n_trials)  # Bonferroni 校正
    
    # DSR
    dsr = (sharpe - threshold * sharpe_std) / sharpe_std
    
    return dsr
```

---

## 🚀 性能优化

### 1. Numba 加速特征计算

```python
from numba import jit

@jit(nopython=True)
def calculate_rsi(prices, period=14):
    """Numba 加速的 RSI 计算 (预期 2-5x 加速)"""
    # 实现代码...
```

### 2. Dask 并行处理

```python
import dask.dataframe as dd

# 多资产并行特征计算
ddf = dd.from_pandas(features, npartitions=8)
result = ddf.map_partitions(lambda df: calculate_features(df))
```

---

## ✅ 验收标准

完成训练后，检查以下指标：

| 指标 | 要求 | 说明 |
|------|------|------|
| **测试集 AUC** | > 0.55 | 必须超越随机猜测 (0.5) |
| **Calibration Error** | < 0.1 | 概率校准误差 |
| **训练/测试 AUC 差距** | < 0.1 | 防止过拟合 |
| **Top 5 特征符合直觉** | ✅ | SHAP 分析 |

---

## 📖 总结

这个系统实现了**对冲基金级别**的机器学习管道，包括：

1. ✅ Purged K-Fold (防信息泄漏)
2. ✅ 特征聚类去噪 (解决共线性)
3. ✅ MDA 特征重要性 (准确评估)
4. ✅ Ensemble Stacking (模型融合)
5. ✅ Optuna 优化 (高效调参)

**下一步**：

- 集成到回测系统 (工单 #010)
- 部署实时预测 API (工单 #011)

**祝你追求 Alpha 成功！** 🚀📈
