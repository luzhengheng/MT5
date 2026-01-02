# TASK #020 - Sync Guide (同步指南)

## 同步目标

将真实数据流水线同步至生产节点，确保所有节点使用统一的数据源和模型。

## 受影响节点

| 节点 | 主机名 | 同步优先级 | 说明 |
|:---|:---|:---|:---|
| **INF** | sg-infer-core-01 | 🔴 HIGH | 需要真实数据和新模型 |
| **GTW** | sg-mt5-gateway-01 | ⚪ NONE | Windows 节点，无需数据管道 |
| **GPU** | cn-train-gpu-01 | 🟡 MEDIUM | 训练节点，可选同步 |
| **HUB** | sg-nexus-hub-01 | 🟢 LOW | 代码仓库，Git 自动同步 |

## 文件变更

### 新增文件
- `src/feature_engineering/ingest_real_eodhd.py` - 真实数据接入脚本
- `data/real_market_data.parquet` - 真实市场数据（4,021 行，11年）
- `.env` - 环境变量配置（��选）

### 修改文件
- `src/training/create_dataset_v2.py` - 自适应数据源选择
- `src/backtesting/vbt_runner.py` - 修复频率参数（freq='1D'）
- `scripts/audit_current_task.py` - 添加 audit_task_020()

### 数据文件
- `data/training_set.parquet` - 更新为真实数据训练集（3,991 行）
- `models/baseline_v1.txt` - 基于真实数据重新训练的模型

## 环境变量配置

### INF 节点

```bash
# 可选：配置 EODHD API Key
export EODHD_API_TOKEN="your_api_key_here"

# 添加到 ~/.bashrc 或 ~/.profile
echo 'export EODHD_API_TOKEN="your_key"' >> ~/.bashrc
```

**注意**: 如果不配置 API Token，系统会自动使用 fallback 模拟数据。

### 网络要求

如果使用真实 EODHD API，INF 节点需要：
- 外网访问权限（访问 eodhd.com）
- HTTPS 出站连接（端口 443）
- 无代理或配置正确的代理

## 同步命令

### 方式 1: Git Pull (推荐)

```bash
# 在 INF 节点执行
ssh root@www.crestive.net
cd /opt/mt5-crs
git pull origin main

# 重新生成数据和模型
python3 src/feature_engineering/ingest_real_eodhd.py
python3 src/training/create_dataset_v2.py
python3 src/training/train_baseline.py
```

### 方式 2: 手动 rsync

```bash
# 同步代码
rsync -avz --progress \
  src/feature_engineering/ingest_real_eodhd.py \
  src/training/create_dataset_v2.py \
  src/backtesting/vbt_runner.py \
  root@www.crestive.net:/opt/mt5-crs/src/

# 同步数据（可选，也可以在 INF 上重新生成）
rsync -avz --progress \
  data/real_market_data.parquet \
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
ssh root@www.crestive.net "python3 -c 'import pandas as pd; df = pd.read_parquet(\"/opt/mt5-crs/data/real_market_data.parquet\"); print(f\"Rows: {len(df)}, Date range: {(df[\"timestamp\"].max() - df[\"timestamp\"].min()).days} days\")'"

# 应输出: Rows: 4021, Date range: 4020 days (约11年)
```

```bash
# 验证训练数据
ssh root@www.crestive.net "python3 -c 'import pandas as pd; df = pd.read_parquet(\"/opt/mt5-crs/data/training_set.parquet\"); print(f\"Rows: {len(df)}, Has close: {\\\"close\\\" in df.columns}\")'"

# 应输出: Rows: 3991, Has close: True
```

```bash
# 验证模型
ssh root@www.crestive.net "python3 -c 'import lightgbm as lgb; m = lgb.Booster(model_file=\"/opt/mt5-crs/models/baseline_v1.txt\"); print(f\"Trees: {m.num_trees()}\")'"

# 应输出: Trees: 100
```

## 无需重启服务

此次同步仅涉及数据和模型文件，不影响运行中的交易系统。

## 数据更新策略

### 定期更新（建议）

```bash
# 每周执行一次数据更新
0 0 * * 0 cd /opt/mt5-crs && python3 src/feature_engineering/ingest_real_eodhd.py && python3 src/training/create_dataset_v2.py && python3 src/training/train_baseline.py
```

### 手动更新

```bash
# 当需要更新模型时
cd /opt/mt5-crs
python3 src/feature_engineering/ingest_real_eodhd.py
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

# 恢复旧数据
cp data/raw_market_data.parquet data/real_market_data.parquet
```

## 注意事项

1. **数据规模**: 真实数据是日线（4,021行），比模拟小时线（43,825行）少，但时间跨度更长（11年 vs 5年）
2. **内存需求**: 日线数据内存占用更小（< 1MB）
3. **API 限制**: 如使用 EODHD API，注意请求频率限制（免费版 20 req/day）
4. **模型版本**: 建议保留旧模型备份以便回滚
5. **频率匹配**: 确保回测脚本使用 `freq='1D'`（日线）

## 性能对比

| 指标 | Task #019 (模拟) | Task #020 (真实) |
|:---|:---|:---|
| 数据规模 | 43,795 行 | 3,991 行 |
| 时间跨度 | 5 年 | 11 年 |
| Sharpe Ratio | 2.26 | 4.97 |
| Win Rate | 61.88% | 82.29% |
| Total Trades | 160 | 943 |

## 故障排查

**问题**: API 无法访问
- **症状**: Connection timeout, Network unreachable
- **解决**: 检查 INF 节点外网权限，配置代理
- **Fallback**: 系统会自动使用模拟数据

**问题**: 数据文件损坏
- **症状**: ParquetException, File not found
- **解决**: 重新运行 `ingest_real_eodhd.py`
- **验证**: 检查文件大小 > 100KB

**问题**: 模型性能下降
- **症状**: 实盘 Sharpe < 1.0
- **解决**: 回滚至旧模型，重新评估
- **分析**: 检查市场环境是否变化

---

**执行时间**: 2026-01-03
**执行者**: Data Engineer
**同步状态**: ⏳ 待执行
