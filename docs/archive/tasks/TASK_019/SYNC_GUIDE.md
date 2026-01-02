# TASK #019 - Sync Guide (同步指南)

## 同步目标

将修复后的数据管道和模型同步至生产节点。

## 受影响节点

| 节点 | 主机名 | 同步优先级 | 说明 |
|:---|:---|:---|:---|
| **INF** | sg-infer-core-01 | 🔴 HIGH | 需要新数据和模型 |
| **GTW** | sg-mt5-gateway-01 | ⚪ NONE | Windows 节点，无需数据管道 |
| **GPU** | cn-train-gpu-01 | 🟡 MEDIUM | 训练节点，可选同步 |
| **HUB** | sg-nexus-hub-01 | 🟢 LOW | 代码仓库，Git 自动同步 |

## 文件变更

### 新增文件
- `src/feature_engineering/ingest_eodhd.py` - 数据接入脚本
- `src/training/create_dataset_v2.py` - 修复后的特征工程
- `data/raw_market_data.parquet` - 原始市场数据（43,825 行）
- `data/training_set.parquet` - 训练数据集（43,795 行，含 close 列）
- `models/baseline_v1.txt` - 重新训练的模型

### 修改文件
- `src/training/train_baseline.py` - 排除 timestamp 列
- `src/backtesting/vbt_runner.py` - 使用真实 close 价格

## 环境变量配置

### INF 节点

```bash
# 可选：配置 EODHD API Key
export EODHD_API_KEY="your_api_key_here"

# 添加到 ~/.bashrc 或 ~/.profile
echo 'export EODHD_API_KEY="your_key"' >> ~/.bashrc
```

## 同步命令

### 方式 1: Git Pull (推荐)

```bash
# 在 INF 节点执行
ssh root@www.crestive.net
cd /opt/mt5-crs
git pull origin main

# 重新生成数据和模型
python3 src/feature_engineering/ingest_eodhd.py
python3 src/training/create_dataset_v2.py
python3 src/training/train_baseline.py
```

### 方式 2: 手动 rsync

```bash
# 同步代码
rsync -avz --progress \
  src/feature_engineering/ingest_eodhd.py \
  src/training/create_dataset_v2.py \
  root@www.crestive.net:/opt/mt5-crs/src/

# 同步数据（可选，也可以在 INF 上重新生成）
rsync -avz --progress \
  data/raw_market_data.parquet \
  data/training_set.parquet \
  root@www.crestive.net:/opt/mt5-crs/data/

# 同步模型
rsync -avz --progress \
  models/baseline_v1.txt \
  root@www.crestive.net:/opt/mt5-crs/models/
```

## 验证同步结果

```bash
# 在 INF 节点验证数据
ssh root@www.crestive.net "python3 -c 'import pandas as pd; df = pd.read_parquet(\"/opt/mt5-crs/data/training_set.parquet\"); print(f\"Rows: {len(df)}, Has close: {\"close\" in df.columns}\")'"

# 应输出: Rows: 43795, Has close: True
```

## 无需重启服务

此次同步仅涉及数据和模型文件，不影响运行中的交易系统。

## 数据更新策略

### 定期更新（建议）

```bash
# 每周执行一次数据更新
0 0 * * 0 cd /opt/mt5-crs && python3 src/feature_engineering/ingest_eodhd.py && python3 src/training/create_dataset_v2.py && python3 src/training/train_baseline.py
```

### 手动更新

```bash
# 当需要更新模型时
cd /opt/mt5-crs
python3 src/feature_engineering/ingest_eodhd.py
python3 src/training/create_dataset_v2.py
python3 src/training/train_baseline.py
```

## 回滚方案

如果新模型表现不佳：

```bash
# 恢复旧模型
cp models/baseline_v1.txt.backup models/baseline_v1.txt

# 或从 Git 恢复
git checkout HEAD~1 -- models/baseline_v1.txt
```

## 注意事项

1. **数据规模**: 新数据集是旧数据集的 20 倍，训练时间会增加
2. **内存需求**: 确保 INF 节点有足够内存（建议 > 4GB）
3. **API 限制**: 如使用 EODHD API，注意请求频率限制
4. **模型版本**: 建议保留旧模型备份以便回滚

---

**执行时间**: 2025-01-03
**执行者**: Data Engineer
**同步状态**: ⏳ 待执行
