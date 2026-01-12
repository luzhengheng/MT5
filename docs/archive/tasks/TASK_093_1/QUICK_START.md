# Task #093.1 快速启动指南

> 🚀 **5分钟内复现 AAPL 最优分数差分特征工程**

---

## 📋 前置条件

### 1. 环境要求

- Python 3.9+
- TimescaleDB (Docker)
- 已配置 `.env` 文件

### 2. 必需的环境变量

```bash
# 数据库
DB_URL=postgresql://trader:password@localhost:5432/mt5_crs

# EODHD API
EODHD_API_TOKEN=your_api_token_here
```

---

## 🏃 快速开始

### Step 1: 启动 TimescaleDB

```bash
# 启动容器
docker start timescaledb

# 验证状态 (应显示 Up 状态)
docker ps | grep timescale
```

### Step 2: 加载历史数据

```bash
# 加载 AAPL 和 TSLA 数据到数据库
python3 src/data_loader/eodhd_timescale_loader.py
```

**预期输出**:
```
✅ DB Schema Ready
⏳ Fetching AAPL.US...
✅ Ingested 11361 rows for AAPL.US
⏳ Fetching TSLA.US...
✅ Ingested 3908 rows for TSLA.US
```

### Step 3: 运行特征工程脚本

```bash
# 执行主脚本
python3 scripts/task_093_1_feature_builder.py
```

**预期输出**:
```
============================================================
Task #093.1: 高级特征工程框架
============================================================
✅ DB Version: PostgreSQL 14.17...
✅ TimescaleDB Ready.

📊 载入 AAPL 数据...
✅ 载入 11361 行数据

🔍 搜索最优 d 值...
❌ d=0.00: p-value=0.0524, corr=0.9985
✅ d=0.05: p-value=0.0278, corr=0.9978
...

============================================================
最优结果:
  d 值: 0.05
  ADF p-value: 0.027785
  平稳性: ✅ 是
  相关性: 0.9978
============================================================

✅ 特征数据已保存
✅ 最优 d 值结果已保存

🎉 Task #093.1 特征工程完成!
```

---

## 📊 结果文件位置

运行完成后，以下文件会生成在任务目录：

```
docs/archive/tasks/TASK_093_1/
├── aapl_features_simple.csv        # AAPL 特征数据 (11,361 行)
├── optimal_d_result.json           # 最优 d 值结果
├── COMPLETION_REPORT.md            # 完成报告
├── QUICK_START.md                  # 本文档
└── VERIFY_LOG.log                  # 执行日志
```

---

## 🔍 查看结果

### 查看最优 d 值

```bash
cat docs/archive/tasks/TASK_093_1/optimal_d_result.json
```

**示例输出**:
```json
{
  "symbol": "AAPL.US",
  "optimal_d": 0.05,
  "adf_pvalue": 0.027785,
  "is_stationary": true,
  "correlation": 0.9978,
  "data_rows": 11361
}
```

### 查看特征数据 (前10行)

```bash
head -n 11 docs/archive/tasks/TASK_093_1/aapl_features_simple.csv | column -t -s,
```

---

## 🧪 使用 Jupyter Notebook (可选)

如果你想交互式探索特征工程过程：

```bash
# 1. 安装 Jupyter (如果还未安装)
pip install jupyter

# 2. 启动 Jupyter Lab
jupyter lab notebooks/task_093_1_feature_engineering.ipynb
```

Notebook 包含：
- 数据加载与预览
- 最优 d 值可视化
- 分数差分效果对比图
- 平稳性验证

---

## 🐛 常见问题

### 问题1: `数据库连接失败`

**错误**:
```
❌ DB Error: connection refused
```

**解决方案**:
```bash
# 检查 Docker 容器状态
docker ps -a | grep timescale

# 如果状态为 Exited，启动容器
docker start timescaledb

# 等待 5 秒让数据库完全启动
sleep 5
```

### 问题2: `表不存在 (relation "market_candles" does not exist)`

**原因**: 数据尚未加载

**解决方案**:
```bash
# 重新运行数据加载脚本
python3 src/data_loader/eodhd_timescale_loader.py
```

### 问题3: `载入 0 行数据`

**原因**:
- 数据库中没有指定symbol的数据
- SQL查询条件不匹配

**排查步骤**:
```python
# 进入 Python 交互式环境
python3

# 检查数据库中的 symbols
from sqlalchemy import text, create_engine
from src.config.env_loader import Config

engine = create_engine(Config.get_db_url())
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT symbol, COUNT(*) as count
        FROM market_candles
        GROUP BY symbol
        ORDER BY count DESC;
    """))
    for row in result:
        print(f"{row[0]}: {row[1]} rows")
```

### 问题4: `Numba 类型错误`

**错误**:
```
numba.core.errors.TypingError: non-precise type array(pyobject, 1d, C)
```

**解决方案**:

使用简化版本脚本（已自动处理）:
```bash
# 简化版本不使用 Numba，使用纯 Python 实现
python3 scripts/task_093_1_feature_builder.py
```

### 问题5: `API Key 错误`

**错误**:
```
⏳ Fetching AAPL.US...
(没有任何输出或超时)
```

**解决方案**:

检查 `.env` 文件中的 API key:
```bash
grep EODHD .env

# 应该显示:
# EODHD_API_TOKEN=your_valid_token_here
```

---

## 📚 进阶用法

### 1. 更改搜索范围

修改脚本中的 `d_range` 参数:

```python
opt_result = SimpleFeatureBuilder.find_optimal_d(
    df['close'],
    d_range=np.arange(0.0, 1.5, 0.01),  # 更细粒度搜索
    significance_level=0.05,
    verbose=True
)
```

### 2. 处理其他股票

```python
# 在脚本中修改 SQL 查询
query = """
SELECT ... FROM market_candles
WHERE symbol = 'TSLA.US'  -- 改为其他 symbol
...
"""
```

### 3. 导出为 Parquet 格式

```python
# 在脚本最后添加
import pyarrow.parquet as pq

df.to_parquet(
    f'{output_dir}/aapl_features.parquet',
    compression='snappy'
)
```

---

## 🎓 理解分数差分

### 什么是分数差分？

分数差分是介于普通差分 (d=1) 和不差分 (d=0) 之间的操作：

- **d=0**: 保留完整序列，但可能非平稳
- **d=1**: 完全差分，平稳但丢失记忆性
- **0<d<1**: 平衡平稳性与记忆性

### 为什么 d=0.05 是最优？

对于 AAPL.US：
- **d=0.00**: p-value=0.0524 > 0.05 (非平稳)
- **d=0.05**: p-value=0.0278 < 0.05 (平稳) ✅
- **相关性**: 0.9978 (保留99.78%的记忆性) ✅

这是在平稳性与记忆性之间找到的最佳平衡点。

---

## 🔗 相关文档

- [完成报告](./COMPLETION_REPORT.md)
- [执行日志](./VERIFY_LOG.log)
- [同步指南](./SYNC_GUIDE.md)
- [协议文档](../../../references/[System Instruction MT5-CRS Development Protocol v4.3].md)

---

**最后更新**: 2026-01-12
**维护者**: MT5-CRS Team
