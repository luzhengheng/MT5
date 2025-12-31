# Feast Feature Store Configuration

## 概述 (Overview)

本目录包含 Feast Feature Store 的配置和定义，用于管理 MT5 交易研究系统的技术特征。

**特征数据源**:
- 表: `market_features` (TimescaleDB Hypertable)
- 行数: 726,793 (11 个特征 × 7 个资产)
- 资产: EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI
- 特征: SMA, RSI, MACD, ATR, Bollinger Bands

## 文件结构 (File Structure)

```
src/feature_store/
├── feature_store.yaml          # Feast 仓库配置
├── definitions.py              # Entity 和 FeatureView 定义
├── init_feature_store.py       # 初始化脚本
└── README.md                   # 本文档
```

## 配置详情 (Configuration Details)

### feature_store.yaml

```yaml
project: mt5_feature_store          # 项目名称
registry_type: sqlite               # 本地 SQLite 注册表
offline_store:
  type: postgres                     # PostgreSQL 离线存储
  host: localhost
  port: 5432
  database: mt5_crs
```

**特点**:
- ✅ 离线存储: PostgreSQL/TimescaleDB
- ✅ 本地注册表: SQLite (Protocol v2.2 合规)
- ✅ 没有在线存储: 纯批处理使用

### definitions.py

**Entity: symbol**
- 含义: 交易对符号 (EURUSD 等)
- 类型: String
- 唯一标识: 每个交易对

**FeatureView: market_features**
- 数据源: SQL 查询 (市场特征宽表)
- 时间戳列: `time`
- 特征列数: 11
- TTL: 90 天

**特征列**:
- `sma_20`: 20 期简单移动平均
- `sma_50`: 50 期简单移动平均
- `sma_200`: 200 期简单移动平均
- `rsi_14`: 14 期相对强度指数
- `macd_line`: MACD 线
- `macd_signal`: MACD 信号线
- `macd_histogram`: MACD 柱状图
- `atr_14`: 14 期平均真实波幅
- `bb_upper`: Bollinger Band 上轨
- `bb_middle`: Bollinger Band 中轨
- `bb_lower`: Bollinger Band 下轨

## SQL View: market_features_wide

**目的**: 将 EAV (Entity-Attribute-Value) 长格式转换为宽格式

**原始格式** (market_features 表):
```
time                | symbol  | feature     | value
2025-01-01 10:00:00 | EURUSD  | sma_20      | 1.0850
2025-01-01 10:00:00 | EURUSD  | sma_50      | 1.0875
2025-01-01 10:00:00 | EURUSD  | rsi_14      | 65.30
...
```

**转换后格式** (market_features_wide View):
```
time                | symbol | sma_20 | sma_50 | sma_200 | rsi_14 | macd_line | ...
2025-01-01 10:00:00 | EURUSD | 1.0850 | 1.0875 | 1.0890  | 65.30  | 0.0025    | ...
```

## 使用方法 (Usage)

### 1. 初始化 Feature Store

```bash
python3 src/feature_store/init_feature_store.py
```

**输出**:
- ✅ 创建 market_features_wide SQL View
- ✅ 验证 Feast 配置
- ✅ 检查数据统计

### 2. 使用 Feast CLI (可选)

```bash
# 初始化 Feast 仓库
cd src/feature_store
feast init-repo

# 应用 Feature Store 配置
feast apply

# 获取历史特征
feast get-historical-features
```

### 3. 在 Python 中使用

```python
from feast import FeatureStore

# 初始化 Feature Store
fs = FeatureStore(repo_path="src/feature_store")

# 查询特征
feature_refs = [
    "market_features:sma_20",
    "market_features:sma_50",
    "market_features:rsi_14",
]

entity_df = pd.DataFrame({
    "symbol": ["EURUSD", "GBPUSD"],
    "event_timestamp": ["2025-01-01", "2025-01-01"]
})

features = fs.get_historical_features(
    entity_df=entity_df,
    feature_refs=feature_refs
)

df = features.to_df()
```

## 数据流 (Data Flow)

```
OHLCV 数据
   ↓
特征工程 (FeatureBatchProcessor)
   ↓
market_features 表 (EAV 长格式)
   ↓
market_features_wide View (宽格式)
   ↓
Feast FeatureView
   ↓
Model 训练 / 推理
```

## 数据验证 (Data Validation)

### SQL 查询验证

```sql
-- 检查 View 是否存在
SELECT EXISTS(
    SELECT 1 FROM information_schema.views
    WHERE table_name = 'market_features_wide'
);

-- 查看数据样本
SELECT * FROM market_features_wide
LIMIT 10;

-- 数据统计
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT symbol) as unique_symbols,
    COUNT(DISTINCT DATE(time)) as unique_dates
FROM market_features_wide;
```

### Python 验证

```python
import asyncpg
import asyncio

async def check_data():
    pool = await asyncpg.create_pool(
        host='localhost',
        database='mt5_crs',
        user='trader',
        password='password'
    )

    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM market_features_wide")
        print(f"总特征行数: {count:,}")

    await pool.close()

asyncio.run(check_data())
```

## 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: README.md + TASK_014_01_PLAN.md
- ✅ 本地存储: SQLite 注册表 (feature_store.yaml)
- ✅ 代码优先: Feature 定义在 definitions.py
- ✅ 版本控制: 所有文件在 Git 中

## 故障排除 (Troubleshooting)

### 问题: "No such table: market_features_wide"

**原因**: SQL View 未创建

**解决方案**:
```bash
python3 src/feature_store/init_feature_store.py
```

### 问题: "Feast library not found"

**原因**: Feast 未安装

**解决方案**:
```bash
pip install feast
```

### 问题: "PostgreSQL connection refused"

**原因**: 数据库连接失败

**解决方案**:
1. 检查 .env 文件中的数据库凭证
2. 确保 PostgreSQL 容器正在运行
3. 检查网络连接: `telnet localhost 5432`

## 参考资料 (References)

- [Feast 官方文档](https://docs.feast.dev/)
- [PostgreSQL 离线存储](https://docs.feast.dev/reference/offline-stores/postgres)
- [SQL View 最佳实践](https://www.postgresql.org/docs/current/rules-views.html)

---

**创建日期**: 2025-12-31
**协议版本**: v2.2 (Documentation-first, Local Storage, Code-first)
**任务**: Task #014.01
