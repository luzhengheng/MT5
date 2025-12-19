# 🚀 机器学习模块快速开始

**工单 #009**: 对冲基金级机器学习预测引擎

---

## ⚡ 5分钟快速上手

### 1. 检查依赖

```bash
pip3 install lightgbm optuna scikit-learn shap pandas
```

### 2. 准备数据

确保特征工程已完成:

```bash
python -m src.feature_engineering.feature_engineer
```

数据路径: `/opt/mt5-crs/data/features/combined_features.parquet`

### 3. 训练模型

**选项 A: PurgedKFold 训练 (推荐)**

```bash
python bin/run_training.py --mode train --n-splits 5
```

**选项 B: Optuna 超参数优化**

```bash
python bin/run_training.py --mode optuna --n-trials 50
```

### 4. 查看结果

```bash
ls outputs/
# models/       - 训练好的模型
# plots/        - 评估图表 (ROC/PR/SHAP)
# *.csv         - 特征重要性、优化历史
```

---

## 📊 输出示例

训练完成后会生成:

```
outputs/
├── models/
│   └── best_model_20250120_150000.pkl    # 模型文件
│
├── plots/
│   ├── final_roc_pr_curves.png           # ROC & PR 曲线
│   ├── final_confusion_matrix.png        # 混淆矩阵
│   ├── final_calibration_curve.png       # 概率校准
│   ├── final_shap_summary.png            # SHAP 分析
│   └── feature_dendrogram.png            # 特征聚类
│
└── feature_importance.csv                # 特征重要性
```

---

## 🧪 快速测试

运行单元测试:

```bash
pytest tests/models/test_models.py -v

# 预期结果: 11 passed in 4.31s ✅
```

---

## 📖 完整文档

详细使用指南: [docs/ML_TRAINING_GUIDE.md](docs/ML_TRAINING_GUIDE.md)

工单完成报告: [docs/issues/ISSUE_009_COMPLETION_REPORT.md](docs/issues/ISSUE_009_COMPLETION_REPORT.md)

---

## 🎯 核心特性

| 特性 | 说明 | 文件 |
|------|------|------|
| PurgedKFold | 防止信息泄漏的验证方法 | `src/models/validation.py` |
| 特征聚类 | 解决75维特征共线性 | `src/models/feature_selection.py` |
| Optuna优化 | 自动超参数搜索 | `src/models/trainer.py` |
| 全面评估 | ROC/PR/SHAP分析 | `src/models/evaluator.py` |

---

## 💡 常用命令

```bash
# 训练模型 (5折交叉验证)
python bin/run_training.py --mode train --n-splits 5

# 超参数优化 (100次试验)
python bin/run_training.py --mode optuna --n-trials 100

# 禁用特征聚类 (使用全部75维特征)
python bin/run_training.py --mode train --no-feature-clustering

# 运行测试
pytest tests/models/test_models.py -v

# 测试单个模块
python -m src.models.validation
python -m src.models.trainer
```

---

## 🆘 问题排查

**Q: 数据文件不存在?**

```bash
# 先运行特征工程
python -m src.feature_engineering.feature_engineer
```

**Q: 训练很慢?**

```bash
# 减少 Optuna 试验次数
python bin/run_training.py --mode optuna --n-trials 20

# 或使用更快的 PurgedKFold
python bin/run_training.py --mode train --n-splits 3
```

**Q: SHAP 报错?**

```bash
# 安装 SHAP
pip3 install shap

# 或跳过 SHAP 分析 (代码会自动跳过)
```

---

**祝训练顺利! 🎉**
