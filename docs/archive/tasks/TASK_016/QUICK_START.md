# Task #016 快速启动指南

## 前置条件

- Python 3.9+
- 已完成 Task #015 (特征数据已生成)
- 已安装依赖: `pip install lightgbm pandas scikit-learn`

## 步骤 1: 创建训练数据集

```bash
cd /opt/mt5-crs
python3 src/training/create_dataset.py
```

**输出**: `data/training_set.parquet` (约 218KB)

**功能**:
- 加载特征数据
- 生成目标变量 (SMA_7 未来变化量)
- 清理 NaN 值

## 步骤 2: 训练基线模型

```bash
python3 src/training/train_baseline.py
```

**输出**:
- `models/baseline_v1.txt` - LightGBM 模型文件
- `models/model_metadata.json` - 模型元数据

**训练参数**:
- 算法: LightGBM Regressor
- num_leaves: 31
- learning_rate: 0.05
- num_boost_round: 100
- 数据切分: 80/20 (时间序列切分)

## 验证结果

查看训练日志:
```bash
cat docs/archive/logs/TASK_016_METRICS.log
```

运行审计:
```bash
python3 scripts/audit_current_task.py
```

## 故障排查

**问题**: `FileNotFoundError: data/sample_features.parquet`
**解决**: 先运行 `python3 src/feature_engineering/ingest_stream.py`

**问题**: `ModuleNotFoundError: No module named 'lightgbm'`
**解决**: `pip install lightgbm`
