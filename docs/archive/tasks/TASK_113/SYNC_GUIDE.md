# Task #113 - 部署变更清单
## ML Alpha 管道与基线模型 - 同步指南

**适用范围**: Hub 节点、Inf 节点（数据同步）
**协议**: Protocol v4.3 (Zero-Trust Edition)

---

## 1. 依赖包管理

### 1.1 Hub 节点 (已安装)

```bash
# 已安装的 ML 相关包
pip list | grep -E "xgboost|mlflow|scikit-learn|pandas|numpy"

# 输出示例:
mlflow                    3.1.4
numpy                     1.24.3
pandas                    2.0.3
scikit-learn              1.3.0
xgboost                   2.1.4
```

### 1.2 Inf 节点 (需要同步)

**SSH 同步脚本**:
```bash
#!/bin/bash
# 在 Hub 节点执行

INF_HOST="172.19.141.250"
INF_USER="root"

# 安装依赖
ssh $INF_USER@$INF_HOST << 'EOF'
pip install xgboost==2.1.4 mlflow==3.1.4 scikit-learn==1.3.0 -q
echo "✅ Inf dependencies installed"
EOF

# 验证
ssh $INF_USER@$INF_HOST "python3 -c \"import xgboost; print(f'XGBoost {xgboost.__version__}')\""
```

---

## 2. 代码文件变更

### 2.1 新增文件

```
✅ scripts/audit_task_113.py              397 行
   └─ TDD 审计脚本，13 个单元测试

✅ src/data/ml_feature_pipeline.py        420 行
   └─ 特征工程管道，5 个特征工程类

✅ models/xgboost_baseline.json           80 KB
   └─ 训练好的 XGBoost 模型

✅ models/xgboost_baseline_metadata.json  2 KB
   └─ 模型元数据和超参数
```

### 2.2 新增数据文件

```
✅ data_lake/ml_training_set.parquet      ~5 MB
   └─ 标准化特征集 (7,933 rows × 22 cols)

✅ data_lake/standardized/EURUSD_D1.parquet  ~8 MB
   └─ 来自 Task #111 的 EODHD 数据
   └─ (可选，如果还未同步)
```

### 2.3 修改的文件

```
✅ docs/archive/tasks/TASK_113/
   ├─ COMPLETION_REPORT.md       (新)
   ├─ QUICK_START.md             (新)
   ├─ SYNC_GUIDE.md              (本文件)
   └─ VERIFY_LOG.log             (新)
```

---

## 3. 环境变量配置

### 3.1 MLflow 配置

```bash
# Hub 节点 (可选，默认本地存储)
export MLFLOW_TRACKING_URI="file://$(pwd)/mlruns"
# 或指向远程 MLflow 服务器
export MLFLOW_TRACKING_URI="http://hub.mt5-crs:5000"
```

### 3.2 数据路径

```bash
# 确保以下路径存在且可访问
export DATA_LAKE_PATH="/opt/mt5-crs/data_lake"
export MODEL_PATH="/opt/mt5-crs/models"
export AUDIT_PATH="/opt/mt5-crs/scripts"

# 验证
ls -la $DATA_LAKE_PATH/ml_training_set.parquet
ls -la $MODEL_PATH/xgboost_baseline.json
```

---

## 4. 数据资产同步

### 4.1 Hub → Inf 同步流程

**方案 A: SCP 直接复制**
```bash
#!/bin/bash
INF_HOST="172.19.141.250"
INF_USER="root"

# 复制模型文件到 Inf
scp models/xgboost_baseline.json \
    $INF_USER@$INF_HOST:/opt/mt5-crs/models/

scp models/xgboost_baseline_metadata.json \
    $INF_USER@$INF_HOST:/opt/mt5-crs/models/

# 验证
ssh $INF_USER@$INF_HOST "ls -lh /opt/mt5-crs/models/xgboost_baseline*"
```

**方案 B: 通过 OSS 中转**
```bash
#!/bin/bash
# Hub 节点上传到 OSS
aws s3 cp models/xgboost_baseline.json \
    s3://mt5-models/xgboost_baseline.json \
    --endpoint-url http://oss-ap-southeast-1-internal.aliyuncs.com

# Inf 节点从 OSS 下载
ssh root@172.19.141.250 << 'EOF'
aws s3 cp s3://mt5-models/xgboost_baseline.json models/ \
    --endpoint-url http://oss-ap-southeast-1-internal.aliyuncs.com
EOF
```

### 4.2 特征集同步

```bash
# 仅在需要推理时同步（大文件警告: ~5 MB）
scp data_lake/ml_training_set.parquet \
    root@172.19.141.250:/opt/mt5-crs/data_lake/

# 或者在 Inf 节点运行特征工程管道生成本地副本
```

---

## 5. 数据库变更

### 5.1 TimescaleDB (Hub)

**新表**: （无）
**新列**: （无）
**修改**: （无）

特征工程完全基于 Parquet 文件，不涉及数据库。

### 5.2 ChromaDB (Hub)

**新集合**: （无）
**修改**: （无）

---

## 6. Git 提交检查清单

### 6.1 分支管理

```bash
# 确认当前分支
git branch
# 输出: * main

# 查看待提交文件
git status

# 输出:
# Untracked files:
#   scripts/audit_task_113.py
#   src/data/ml_feature_pipeline.py
#   models/xgboost_baseline.json
#   models/xgboost_baseline_metadata.json
#   data_lake/ml_training_set.parquet
#   docs/archive/tasks/TASK_113/
```

### 6.2 提交文件清单

```bash
# 添加所有文件
git add scripts/audit_task_113.py
git add src/data/ml_feature_pipeline.py
git add models/xgboost_baseline.json
git add models/xgboost_baseline_metadata.json
git add docs/archive/tasks/TASK_113/
git add AUDIT_TASK_113.log
git add VERIFY_LOG.log

# 可选: 添加特征集 (大文件警告)
git add data_lake/ml_training_set.parquet

# 查看 diff
git diff --cached --stat
```

### 6.3 提交信息模板

```bash
git commit -m "feat(task-113): ML Alpha pipeline & XGBoost baseline model

- Feature engineering: 21 indicators (RSI, MACD, Volatility, etc)
- XGBoost baseline: CV F1 = 0.5027 (baseline performance)
- MLflow integration: Run ID 9fce9d31531f4ca2b9a3a532ac3b2e31
- Unit tests: 13/13 passed (100% coverage)
- Physical forensics: UUID, Token, MD5 hash verified

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 6.4 推送验证

```bash
# 查看将要推送的提交
git log --oneline origin/main..HEAD

# 推送到远程
git push origin main

# 验证
git log --oneline -5
```

---

## 7. 部署验证流程

### 7.1 Hub 节点验证

```bash
#!/bin/bash
echo "🔍 Hub Node Verification"

# 1. 代码文件检查
echo "✓ Checking code files..."
test -f scripts/audit_task_113.py && echo "  ✅ audit_task_113.py"
test -f src/data/ml_feature_pipeline.py && echo "  ✅ ml_feature_pipeline.py"

# 2. 模型文件检查
echo "✓ Checking model files..."
test -f models/xgboost_baseline.json && echo "  ✅ xgboost_baseline.json"
ls -lh models/xgboost_baseline_metadata.json

# 3. 数据文件检查
echo "✓ Checking data files..."
test -f data_lake/ml_training_set.parquet && echo "  ✅ ml_training_set.parquet"

# 4. 单元测试验证
echo "✓ Running unit tests..."
python3 scripts/audit_task_113.py 2>&1 | grep -E "^Ran|^OK|^FAILED"

# 5. 模型加载验证
echo "✓ Verifying model loads..."
python3 << 'EOF'
import xgboost as xgb
model = xgb.XGBClassifier()
model.load_model('models/xgboost_baseline.json')
print("  ✅ Model loads successfully")
print(f"  Estimators: {model.n_estimators}")
print(f"  Max depth: {model.max_depth}")
EOF

echo "✅ Hub verification complete"
```

### 7.2 Inf 节点验证

```bash
#!/bin/bash
# 在 Hub 节点执行，验证 Inf 上的文件

INF_HOST="172.19.141.250"
INF_USER="root"

echo "🔍 Inf Node Verification"

ssh $INF_USER@$INF_HOST << 'EOF'
echo "✓ Checking dependencies..."
python3 -c "import xgboost; print(f'  ✅ XGBoost {xgboost.__version__}')"

echo "✓ Checking model files..."
test -f /opt/mt5-crs/models/xgboost_baseline.json && \
  echo "  ✅ xgboost_baseline.json"

echo "✓ Verifying model loading..."
python3 << 'PYEOF'
import xgboost as xgb
model = xgb.XGBClassifier()
model.load_model('/opt/mt5-crs/models/xgboost_baseline.json')
print("  ✅ Model loads successfully on Inf")
PYEOF

echo "✅ Inf verification complete"
EOF
```

---

## 8. 回滚步骤

### 8.1 如果部署失败

```bash
# 1. 撤销最后一次提交
git reset --soft HEAD~1

# 2. 恢复文件
git checkout -- scripts/audit_task_113.py
git checkout -- src/data/ml_feature_pipeline.py

# 3. 删除生成的文件（如果需要）
rm -f models/xgboost_baseline.json
rm -f data_lake/ml_training_set.parquet
rm -rf docs/archive/tasks/TASK_113/

# 4. 验证回滚
git status
```

### 8.2 如果 Inf 同步失败

```bash
# 在 Inf 节点上
rm -f /opt/mt5-crs/models/xgboost_baseline.json
rm -f /opt/mt5-crs/models/xgboost_baseline_metadata.json

# 重新从 Hub 同步
ssh root@172.19.141.250 << 'EOF'
scp root@172.19.141.254:/opt/mt5-crs/models/xgboost_baseline*.json \
    /opt/mt5-crs/models/
EOF
```

---

## 9. 监控和维护

### 9.1 定期检查

```bash
# 每周检查一次
crontab -e

# 添加:
0 9 * * 1 /opt/mt5-crs/scripts/verify_task_113.sh

# 内容:
#!/bin/bash
python3 scripts/audit_task_113.py > /tmp/task_113_check.log 2>&1
if [ $? -ne 0 ]; then
    echo "Alert: Task #113 tests failed" | mail admin@mt5-crs
fi
```

### 9.2 模型版本管理

```bash
# 保留多个版本
cp models/xgboost_baseline.json models/xgboost_baseline_v1.0.json
cp models/xgboost_baseline_metadata.json models/xgboost_baseline_v1.0_metadata.json

# 记录版本历史
echo "v1.0: CV F1 = 0.5027 (baseline)" >> MODELS_VERSION.log
```

---

## 10. 故障排除

| 问题 | 症状 | 解决方案 |
| --- | --- | --- |
| 导入错误 | `ModuleNotFoundError: xgboost` | 运行 `pip install xgboost` |
| 数据缺失 | `FileNotFoundError: ml_training_set.parquet` | 检查 `data_lake/` 路径，重新运行特征工程 |
| 模型损坏 | 加载模型时 `ValueError` | 验证 `xgboost_baseline.json` MD5: `501872fc854eda5c126d47fb15e76e6e` |
| Inf 同步失败 | SSH 超时 | 检查网络连接 (`ping 172.19.141.250`) |

---

## 11. 下一步

**部署完成后**:
1. ✅ 验证 Gate 1 和 Gate 2 通过
2. ✅ 同步到 Inf 节点
3. ⏭️ 启动 Task #114 - Inf 节点实时推理

**文档链接**:
- [完成报告](COMPLETION_REPORT.md)
- [快速开始](QUICK_START.md)
- [中央命令文件](../../[MT5-CRS]%20Central%20Comman.md)

---

**同步指南生成**: 2026-01-15 23:54:18 UTC
**Protocol**: v4.3 (Zero-Trust Edition)
