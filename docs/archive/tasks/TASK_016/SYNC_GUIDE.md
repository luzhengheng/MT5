# Task #016 节点同步指南

## 重要说明

**Task #016 不需要节点同步**

本任务的所有操作均在 **HUB 节点**完成，无需同步到 INF/GPU 节点。

## 原因

1. **训练环境**: LightGBM 基线模型训练在 CPU 上进行，不需要 GPU
2. **数据位置**: 训练数据 (`data/training_set.parquet`) 仅在 HUB 节点使用
3. **模型部署**: 模型文件 (`models/baseline_v1.txt`) 已被 `.gitignore` 排除，不进入版本控制

## 需要同步的内容

仅需通过 Git 同步以下代码文件:
- `src/training/create_dataset.py`
- `src/training/train_baseline.py`
- `scripts/audit_current_task.py` (更新的审计函数)
- `.gitignore` (更新的忽略规则)

## 同步命令

```bash
# 在 HUB 节点
git push origin main

# 在 INF/GPU 节点
git pull origin main
```

## 后续任务说明

如果未来需要在 GPU 节点训练深度学习模型 (如 Transformer)，届时会有专门的同步指南。
