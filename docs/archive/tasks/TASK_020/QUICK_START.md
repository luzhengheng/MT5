# TASK #020 - Quick Start Guide

## 快速运行真实数据流水线

### 前置条件
- Python 3.9+
- 已安装依赖: pandas, numpy, lightgbm, vectorbt, requests
- (可选) EODHD API Token

### 完整执行流程

```bash
# 1. 真实数据接入
python3 src/feature_engineering/ingest_real_eodhd.py

# 2. 创建特征数据集（自动使用真实数据）
python3 src/training/create_dataset_v2.py

# 3. 训练模型
python3 src/training/train_baseline.py

# 4. 回测验证
python3 src/backtesting/vbt_runner.py

# 或者一键执行全流程
(python3 src/feature_engineering/ingest_real_eodhd.py && \
 python3 src/training/create_dataset_v2.py && \
 python3 src/training/train_baseline.py && \
 python3 src/backtesting/vbt_runner.py) | tee pipeline.log
```

### 使用真实 EODHD API

#### 1. 获取 API Token
访问 [EODHD.com](https://eodhd.com/) 注册并获取 API Token

#### 2. 配置环境变量

**方式 A: 临时设置**
```bash
export EODHD_API_TOKEN="your_token_here"
```

**方式 B: 永久配置**
```bash
# 创建 .env 文件
echo 'EODHD_API_TOKEN=your_token_here' >> .env

# 或添加到 ~/.bashrc
echo 'export EODHD_API_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

#### 3. 执行数据接入
```bash
python3 src/feature_engineering/ingest_real_eodhd.py
```

### Fallback 模式

如果未配置 API Token，脚本会自动使用 fallback 模拟数据：
- 基于几何布朗运动生成
- 11年日线数据（2015-2026）
- 4,000+ 行数据
- 适合开发和测试

### 预期输出

**数据接入**:
```
✅ Downloaded 4,021 rows from EODHD API
   (或 Generated 4,021 rows of fallback data)
✅ Download Complete: data/real_market_data.parquet
```

**特征工程**:
```
Loaded 4,021 rows (real data)
Final dataset: 3,991 rows (after dropna)
✅ Dataset saved: data/training_set.parquet
```

**模型训练**:
```
Test MSE: 0.000000
Test MAE: 0.000534
✅ Model saved to: models/baseline_v1.txt
```

**回测验证**:
```
Sharpe Ratio: 4.9672
✅ VERDICT: SAFE - Sharpe Ratio 合理
Total Trades: 943
Win Rate: 82.29%
Total Return: 66.35%
```

### 验证成功标准

检查回测日志中的关键指标：

```bash
grep "Sharpe Ratio" pipeline.log
grep "VERDICT" pipeline.log
```

**成功标准**:
- Sharpe Ratio < 5.0 ✅
- VERDICT: SAFE ✅
- Total Trades > 100 ✅
- No errors in log ✅

### 故障排查

**问题**: API Token 无效
- **症状**: HTTP 401 Unauthorized
- **解决**: 检查 Token 是否正确，是否过期
- **Fallback**: 系统会自动切换到模拟数据

**问题**: 数据下载失败
- **症状**: Network timeout, Connection error
- **解决**: 检查网络连接，重试
- **Fallback**: 系统会自动使用模拟数据

**问题**: Sharpe Ratio 仍然过高 (> 5.0)
- **原因**: 可能存在数据泄露
- **解决**: 检查特征计算是否使用滚动窗口
- **验证**: 查看 create_dataset_v2.py 中的 `.rolling()` 调用

**问题**: 回测无交易 (Total Trades = 0)
- **原因**: 预测值范围太小，未触发信号
- **解决**: 降低阈值（当前 0.0001）
- **检查**: vbt_runner.py 中的 entries/exits 阈值

### 数据更新策略

#### 定期更新（建议）
```bash
# 每周执行一次数据更新
0 0 * * 0 cd /opt/mt5-crs && python3 src/feature_engineering/ingest_real_eodhd.py && python3 src/training/create_dataset_v2.py && python3 src/training/train_baseline.py
```

#### 手动更新
```bash
# 当需要更新模型时
cd /opt/mt5-crs
python3 src/feature_engineering/ingest_real_eodhd.py
python3 src/training/create_dataset_v2.py
python3 src/training/train_baseline.py
```

### 性能基准

**硬件要求**:
- CPU: 2+ cores
- RAM: 4GB+
- Disk: 100MB+

**执行时间**:
- 数据接入: ~10秒（API）或 ~5秒（Fallback）
- 特征工程: ~5秒
- 模型训练: ~10秒
- 回测验证: ~15秒
- **总计**: ~45秒

---

**维护者**: Data Engineer
**最后更新**: 2026-01-03
