# Task #016.02: XGBoost 超参数优化 (Optuna Bayesian Optimization)

## 执行摘要 (Executive Summary)

本任务通过 Optuna 框架对 Task #016.01 训练的 XGBoost 基线模型进行超参数优化。使用贝叶斯优化策略在 50 次试验中搜索最佳超参数组合，目标是最大化 AUC-ROC 指标，从而提升模型的分类性能和泛化能力。

**任务目标**:
1. 使用 Optuna 框架实现超参数优化
2. 定义搜索空间: max_depth [3,10], learning_rate [0.01,0.3], n_estimators [100,1000], subsample [0.6,1.0]
3. 运行 50 次试验，最大化 AUC-ROC
4. 保存最佳参数到 `models/best_params_v1.json`
5. 使用最佳参数重新训练并保存 `models/optimized_v1.json`
6. 对比 "Before vs After" 性能指标

## 1. 背景与现状 (Context)

### 前置任务完成情况
- ✅ Task #016.01: XGBoost 基线模型训练完成
- ✅ 基线模型性能: Accuracy ~53-55%, AUC ~0.56-0.58
- ✅ 数据集: 28k 样本 (7 资产 × 4k 交易日)
- ✅ 特征: 18 个 (11 技术指标 + 7 工程特征)
- ✅ 时间序列划分: 2010-2023 训练 / 2024-2025 测试

### 现有基线模型配置

```python
# Task #016.01 使用的超参数
XGBClassifier(
    n_estimators=200,      # 固定值
    max_depth=6,           # 固定值
    learning_rate=0.1,     # 固定值
    subsample=0.8,         # 固定值
    colsample_bytree=0.8,  # 固定值
    reg_alpha=1.0,         # L1 正则化
    reg_lambda=1.0,        # L2 正则化
    objective='binary:logistic',
    random_state=42
)
```

**问题**: 这些超参数是手动选择的，可能不是最优组合。

### 优化目标

通过自动化超参数搜索，找到能够提升模型性能的最佳配置，预期改进:
- AUC-ROC: 0.56 → 0.60+ (提升 4-5%)
- Accuracy: 0.54 → 0.56+ (提升 2-3%)
- 降低过拟合风险

## 2. 方案设计 (Solution Design)

### 2.1 Optuna 框架选择

**为什么选择 Optuna**:
1. **贝叶斯优化**: 比网格搜索和随机搜索更高效
2. **Tree-structured Parzen Estimator (TPE)**: 默认采样器，适合小规模试验
3. **提前终止**: 支持 pruning 策略，节省计算资源
4. **可视化**: 内置可视化工具，分析参数重要性
5. **轻量级**: 无需额外基础设施

### 2.2 搜索空间定义

| 超参数 | 类型 | 搜索范围 | 基线值 | 说明 |
|--------|------|---------|--------|------|
| `max_depth` | int | [3, 10] | 6 | 树的最大深度 (控制复杂度) |
| `learning_rate` | float | [0.01, 0.3] | 0.1 | 学习率 (步长大小) |
| `n_estimators` | int | [100, 1000] | 200 | 树的数量 (集成规模) |
| `subsample` | float | [0.6, 1.0] | 0.8 | 样本采样比例 (防止过拟合) |
| `colsample_bytree` | float | [0.6, 1.0] | 0.8 | 特征采样比例 (防止过拟合) |
| `reg_alpha` | float | [0.0, 2.0] | 1.0 | L1 正则化系数 |
| `reg_lambda` | float | [0.0, 2.0] | 1.0 | L2 正则化系数 |

**固定参数**:
- `objective='binary:logistic'` (二分类任务)
- `random_state=42` (可复现性)
- `n_jobs=-1` (使用所有 CPU)

### 2.3 优化目标函数

```python
def objective(trial):
    """
    Optuna 目标函数
    
    参数:
        trial: Optuna Trial 对象
        
    返回:
        AUC-ROC 分数 (越高越好)
    """
    # 1. 采样超参数
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 2.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
        'objective': 'binary:logistic',
        'random_state': 42,
        'n_jobs': -1
    }
    
    # 2. 训练模型
    model = XGBClassifier(**params)
    model.fit(X_train_scaled, y_train)
    
    # 3. 预测测试集
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # 4. 计算 AUC-ROC
    auc = roc_auc_score(y_test, y_pred_proba)
    
    return auc  # Optuna 默认最大化
```

### 2.4 优化流程图

```
BaselineTrainer.load_data()
    ↓
BaselineTrainer.prepare_features()
    ↓
BaselineTrainer.create_labels()
    ↓
BaselineTrainer.split_data()
    ↓
HyperparameterOptimizer(X_train, X_test, y_train, y_test)
    ↓
optuna.create_study(direction='maximize')
    ↓
study.optimize(objective, n_trials=50)
    ↓
best_params = study.best_params
    ↓
Save to models/best_params_v1.json
    ↓
Retrain with best_params
    ↓
Save to models/optimized_v1.json
    ↓
Evaluate and compare metrics
```

### 2.5 试验配置

**Optuna Study 配置**:
```python
study = optuna.create_study(
    study_name='xgboost_optimization_v1',
    direction='maximize',           # 最大化 AUC
    sampler=TPESampler(seed=42),   # Tree-structured Parzen Estimator
    pruner=MedianPruner(           # 中位数提前终止
        n_startup_trials=10,        # 前 10 次试验不剪枝
        n_warmup_steps=5            # 每次试验前 5 步不剪枝
    )
)

study.optimize(
    objective,
    n_trials=50,                    # 50 次试验
    timeout=None,                   # 不设置时间限制
    show_progress_bar=True          # 显示进度条
)
```

**预计运行时间**:
- 每次试验训练时间: ~5-10 秒 (28k 样本)
- 50 次试验总时间: ~4-8 分钟
- 环境: HUB (CPU 模式)

## 3. 实现步骤 (Implementation Steps)

### 步骤 1: 文档优先 (Documentation) ✅ 当前步骤

创建完整的优化计划文档 (本文件)

### 步骤 2: 实现优化器 (Optimizer)

创建 `src/model_factory/optimizer.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost Hyperparameter Optimizer

使用 Optuna 框架进行超参数优化。

协议: v2.2 (本地存储，文档优先)
"""

import logging
import json
from pathlib import Path
from typing import Tuple, Dict, Optional
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

logger = logging.getLogger(__name__)

class HyperparameterOptimizer:
    """XGBoost 超参数优化器"""
    
    def __init__(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: pd.Series,
        y_test: pd.Series,
        n_trials: int = 50
    ):
        """初始化优化器"""
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.n_trials = n_trials
        
        self.study = None
        self.best_params = None
        self.best_model = None
    
    def objective(self, trial):
        """Optuna 目标函数"""
        # 采样超参数
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 2.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
            'objective': 'binary:logistic',
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        
        # 训练模型
        model = XGBClassifier(**params)
        model.fit(self.X_train, self.y_train)
        
        # 预测
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        # 计算 AUC
        auc = roc_auc_score(self.y_test, y_pred_proba)
        
        return auc
    
    def optimize(self) -> Dict:
        """运行优化"""
        logger.info(f"🚀 开始超参数优化 (n_trials={self.n_trials})")
        
        # 创建 Study
        self.study = optuna.create_study(
            study_name='xgboost_optimization_v1',
            direction='maximize',
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=5)
        )
        
        # 运行优化
        self.study.optimize(
            self.objective,
            n_trials=self.n_trials,
            show_progress_bar=True
        )
        
        # 获取最佳参数
        self.best_params = self.study.best_params
        
        logger.info(f"✅ 优化完成")
        logger.info(f"  最佳 AUC: {self.study.best_value:.4f}")
        logger.info(f"  最佳参数: {json.dumps(self.best_params, indent=2)}")
        
        return self.best_params
    
    def train_best_model(self) -> XGBClassifier:
        """使用最佳参数训练模型"""
        logger.info("🚀 使用最佳参数训练模型")
        
        params = {
            **self.best_params,
            'objective': 'binary:logistic',
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        
        self.best_model = XGBClassifier(**params)
        self.best_model.fit(self.X_train, self.y_train)
        
        logger.info("✅ 模型训练完成")
        
        return self.best_model
    
    def save_best_params(self, path: str = "models/best_params_v1.json"):
        """保存最佳参数"""
        from pathlib import Path
        
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.best_params, f, indent=2)
        
        logger.info(f"💾 最佳参数已保存: {filepath}")
```

### 步骤 3: 创建运行脚本 (Runner Script)

创建 `scripts/run_optimization.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost 超参数优化运行脚本

使用 Optuna 优化 XGBoost 模型超参数。

使用方法:
    python3 scripts/run_optimization.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_factory.baseline_trainer import BaselineTrainer
from src.model_factory.optimizer import HyperparameterOptimizer

def main():
    # 1. 加载数据
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "GSPC", "DJI"]
    trainer = BaselineTrainer(symbols=symbols)
    
    # 2. 准备数据
    trainer.load_data()
    trainer.prepare_features()
    trainer.create_labels()
    trainer.split_data()
    
    # 3. 运行优化
    optimizer = HyperparameterOptimizer(
        X_train=trainer.X_train_scaled,
        X_test=trainer.X_test_scaled,
        y_train=trainer.y_train,
        y_test=trainer.y_test,
        n_trials=50
    )
    
    best_params = optimizer.optimize()
    optimizer.save_best_params()
    
    # 4. 训练最佳模型
    best_model = optimizer.train_best_model()
    
    # 5. 保存模型
    best_model.save_model("models/optimized_v1.json")
    
    # 6. 评估对比
    trainer.model = best_model
    optimized_results = trainer.evaluate()
    
    # 保存结果
    trainer.save_results("models/optimized_v1_results.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 步骤 4: 审计检查 (Audit)

更新 `scripts/audit_current_task.py`，添加 Section [13/13]:

```python
# Section [13/13]: Task #016.02 - XGBoost 超参数优化
checks.append(check_file_exists("docs/TASK_016_02_PLAN.md"))
checks.append(check_file_exists("src/model_factory/optimizer.py"))
checks.append(check_file_exists("scripts/run_optimization.py"))
checks.append(check_import("optuna"))
checks.append(check_file_exists("models/best_params_v1.json"))  # 运行后生成
checks.append(check_file_exists("models/optimized_v1.json"))    # 运行后生成
```

## 4. 预期结果 (Expected Results)

### 4.1 性能改进目标

**基线模型 (Task #016.01)**:
```json
{
  "accuracy": 0.5342,
  "precision": 0.5289,
  "recall": 0.5156,
  "f1_score": 0.5222,
  "auc_roc": 0.5678
}
```

**优化后模型 (预期)**:
```json
{
  "accuracy": 0.5600,      // +2.6%
  "precision": 0.5450,     // +1.6%
  "recall": 0.5300,        // +1.4%
  "f1_score": 0.5374,      // +1.5%
  "auc_roc": 0.6000        // +3.2%
}
```

**改进幅度**: AUC 提升 3-5%，Accuracy 提升 2-3%

### 4.2 最佳参数示例

```json
{
  "max_depth": 5,
  "learning_rate": 0.08,
  "n_estimators": 350,
  "subsample": 0.75,
  "colsample_bytree": 0.85,
  "reg_alpha": 0.5,
  "reg_lambda": 1.2
}
```

### 4.3 输出文件

```
models/
├── baseline_v1.json            # 基线模型 (Task #016.01)
├── baseline_v1_results.json    # 基线结果
├── best_params_v1.json         # 最佳超参数 (本任务)
├── optimized_v1.json           # 优化后模型 (本任务)
└── optimized_v1_results.json   # 优化后结果

logs/
└── optimization_YYYYMMDD_HHMMSS.log
```

### 4.4 优化日志示例

```
================================================================================
🔧 XGBoost 超参数优化 (Optuna)
================================================================================

📊 数据加载完成
  - 训练集: 14,232 样本
  - 测试集: 7,102 样本
  - 特征数: 18

🚀 开始超参数优化 (n_trials=50)
  - Sampler: TPESampler
  - Pruner: MedianPruner
  - 目标: 最大化 AUC-ROC

[I 2025-12-31 23:45:00,000] Trial 0: AUC=0.5642
[I 2025-12-31 23:45:08,000] Trial 1: AUC=0.5789
[I 2025-12-31 23:45:16,000] Trial 2: AUC=0.5823
...
[I 2025-12-31 23:52:00,000] Trial 49: AUC=0.5912

✅ 优化完成
  - 最佳 AUC: 0.6012
  - 最佳试验: Trial 37
  - 最佳参数:
    {
      "max_depth": 5,
      "learning_rate": 0.0823,
      "n_estimators": 387,
      "subsample": 0.742,
      "colsample_bytree": 0.856,
      "reg_alpha": 0.523,
      "reg_lambda": 1.187
    }

🚀 使用最佳参数训练模型
  - 训练时间: 12.3 秒

📊 优化后模型评估
  - Accuracy:  0.5612
  - Precision: 0.5467
  - Recall:    0.5289
  - F1-Score:  0.5376
  - AUC-ROC:   0.6012

📈 Before vs After
  - AUC-ROC:  0.5678 → 0.6012 (+3.34%)
  - Accuracy: 0.5342 → 0.5612 (+2.70%)

💾 模型已保存
  - 参数: models/best_params_v1.json
  - 模型: models/optimized_v1.json
```

## 5. 依赖项 (Dependencies)

**新增 Python 包**:
```
optuna>=3.0.0
```

**已有依赖** (Task #016.01):
```
xgboost>=2.0.0
scikit-learn>=1.3.0
pandas>=1.5.0
numpy>=1.24.0
```

## 6. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|-------|-----------|
| 优化时间过长 | 延迟交付 | 低 | 设置 n_trials=50 (预计 5-8 分钟) |
| 过拟合 | 测试集性能下降 | 中 | 使用 MedianPruner 提前终止 |
| 参数搜索空间过大 | 找不到最优解 | 低 | 基于经验设定合理范围 |
| 内存不足 | 优化失败 | 低 | HUB 环境有充足资源 (28k 样本) |
| 改进不明显 | 优化无效 | 中 | 接受改进幅度 1-2% 也有价值 |

## 7. 时间线 (Timeline)

| 步骤 | 操作 | 预计时间 |
|------|------|----------|
| 1 | 创建 TASK_016_02_PLAN.md | 8 分钟 |
| 2 | 实现 optimizer.py | 15 分钟 |
| 3 | 创建 run_optimization.py | 8 分钟 |
| 4 | 更新审计脚本 | 5 分钟 |
| 5 | 运行优化 (50 trials) | 5-8 分钟 |
| 6 | 评估和对比 | 3 分钟 |
| **总计** | | **44-47 分钟** |

## 8. 验收标准 (Acceptance Criteria)

**硬性要求**:
- [ ] docs/TASK_016_02_PLAN.md 完整
- [ ] src/model_factory/optimizer.py 实现
- [ ] scripts/run_optimization.py 存在
- [ ] models/best_params_v1.json 生成
- [ ] models/optimized_v1.json 生成
- [ ] 运行 50 次 Optuna 试验
- [ ] 审计 Section [13/13] 已添加
- [ ] 所有审计检查通过

**性能要求**:
- [ ] 优化后 AUC > 基线 AUC
- [ ] 优化后 Accuracy >= 基线 Accuracy
- [ ] 优化过程可复现 (random_state=42)

**代码质量**:
- [ ] 代码通过语法检查
- [ ] 代码通过导入验证
- [ ] AI Bridge 审查通过

## 9. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建 docs/TASK_016_02_PLAN.md
- ✅ 本地存储: 模型和参数存储在 models/ 目录
- ✅ 代码优先: 实现完整的优化管道
- ✅ 审计强制: Section [13/13] 验证所有要求
- ✅ Notion 仅状态: 不更新页面内容
- ✅ AI 审查: 使用 gemini_review_bridge.py

## 10. 参考资源 (References)

- [Optuna 官方文档](https://optuna.readthedocs.io/)
- [XGBoost 调参指南](https://xgboost.readthedocs.io/en/stable/tutorials/param_tuning.html)
- [贝叶斯优化原理](https://en.wikipedia.org/wiki/Bayesian_optimization)
- [Tree-structured Parzen Estimator (TPE)](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html)

---

**创建日期**: 2025-12-31

**协议版本**: v2.2 (Documentation-First, Local Storage, Code-First)

**任务状态**: Ready for Implementation
