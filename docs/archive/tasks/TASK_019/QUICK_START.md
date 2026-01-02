# TASK #019 - Quick Start Guide

## 快速运行数据修复流程

### 前置条件
- Python 3.9+
- 已安装依赖: pandas, numpy, lightgbm, vectorbt

### 完整执行流程

```bash
# 1. 数据接入（生成模拟数据）
python3 src/feature_engineering/ingest_eodhd.py

# 2. 创建特征数据集（v2 - 无泄露版本）
python3 src/training/create_dataset_v2.py

# 3. 训练模型
python3 src/training/train_baseline.py

# 4. 回测验证
python3 src/backtesting/vbt_runner.py

# 或者一键执行全流程
(python3 src/feature_engineering/ingest_eodhd.py && \
 python3 src/training/create_dataset_v2.py && \
 python3 src/training/train_baseline.py && \
 python3 src/backtesting/vbt_runner.py) | tee pipeline.log
```

### 使用真实 EODHD API（可选）

```bash
# 1. 设置 API Key
export EODHD_API_KEY="your_api_key_here"

# 2. 修改 ingest_eodhd.py 启用 API 调用
# （当前版本使用模拟数据）

# 3. 执行数据接入
python3 src/feature_engineering/ingest_eodhd.py
```

### 预期输出

**数据接入**:
- 生成 43,825 行市场数据
- 保存到 `data/raw_market_data.parquet`

**特征工程**:
- 计算 15 个技术指标
- 输出 43,795 行（去除 NaN）
- 保存到 `data/training_set.parquet`

**模型训练**:
- Test MSE: ~0.000000
- 模型保存到 `models/baseline_v1.txt`

**回测验证**:
- Sharpe Ratio: 2.0 - 3.0 ✅
- Win Rate: 55% - 65% ✅
- Total Trades: > 100 ✅

### 验证修复成功

检查回测日志中的 Sharpe Ratio：

```bash
grep "Sharpe Ratio" docs/archive/tasks/TASK_019/VERIFY_LOG.log
```

**成功标准**: Sharpe Ratio < 5.0

### 故障排查

**问题**: TypeError: datetime64 cannot be promoted
- **原因**: 训练脚本未排除 timestamp 列
- **解决**: 已在 `train_baseline.py` 中修复

**问题**: Total Trades = 0
- **原因**: 预测值范围太小，未触发交易信号
- **解决**: 降低阈值至 0.0001

**问题**: Sharpe Ratio 仍然 > 5.0
- **原因**: 特征计算仍有泄露
- **解决**: 检查所有指标是否使用 `.rolling()`

---

**维护者**: Data Engineer
**最后更新**: 2025-01-03
