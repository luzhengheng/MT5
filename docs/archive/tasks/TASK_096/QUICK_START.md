# Task #096 快速启动指南

**特征工程引擎使用手册** - 5分钟快速上手

---

## 🎯 功能说明

从 TimescaleDB 原始行情表 (`market_data`) 计算技术指标，并存入特征表 (`market_features`)。

**支持的指标**:
- **动量**: RSI (14期)
- **趋势**: SMA (20/50/200), EMA (12/26)
- **波动率**: ATR (14期), 布林带
- **复合**: MACD (12/26/9)
- **成交量**: OBV

---

## 📋 前置条件

### 1. 环境依赖
```bash
# 确认 Python 版本
python3 --version  # 需要 >= 3.9

# 确认 TA-Lib 已安装
python3 -c "import talib; print(talib.__version__)"
# 输出: 0.6.8
```

如果未安装 TA-Lib:
```bash
pip install ta-lib
```

### 2. 数据库准备
```bash
# 确认 market_data 表有数据
python3 -c "
import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('.env'))
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=int(os.getenv('POSTGRES_PORT')),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = conn.cursor()
cur.execute('SELECT symbol, COUNT(*) FROM market_data GROUP BY symbol')
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} rows')
"
```

如果没有数据，先下载:
```bash
python3 scripts/data/eodhd_bulk_loader.py --symbol AAPL --days 365
```

### 3. 创建特征表
```bash
python3 scripts/audit_task_096.py --init-only
```

输出应包含:
```
✓ market_features table created successfully
  └─ Hypertable enabled with time partitioning
```

---

## 🚀 使用方法

### 场景 1: 单个股票特征计算（推荐新手使用）

```bash
# 为 AAPL 计算所有特征
python3 scripts/data/feature_engine.py --symbol AAPL --task-id 096
```

**预期输出**:
```
Task ID: 096
Processing symbol: AAPL
Mode: Full Backfill
Fetched 270 rows for AAPL
Calculated 14 features for 71 time periods
[SUCCESS] Inserted 71 feature rows for AAPL

PROCESSING STATISTICS
Symbols Processed: 1
Total Rows Inserted: 71
Errors: 0
```

### 场景 2: 增量更新（仅计算新数据）

```bash
# 仅处理最后一次特征计算之后的新数据
python3 scripts/data/feature_engine.py --symbol AAPL --incremental
```

**适用场景**: 每日定时任务，避免重复计算历史数据。

### 场景 3: 批量处理所有股票

```bash
# 处理 market_data 中所有股票
python3 scripts/data/feature_engine.py --all --task-id 096
```

**注意**: 如果有大量股票（>100），建议分批执行或使用增量模式。

---

## 🔍 验证结果

### 1. 查看计算统计
```bash
python3 -c "
import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('.env'))
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=int(os.getenv('POSTGRES_PORT')),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = conn.cursor()
cur.execute('''
    SELECT
        symbol,
        COUNT(*) as row_count,
        MIN(time) as earliest,
        MAX(time) as latest
    FROM market_features
    GROUP BY symbol
''')
print(f\"{'Symbol':<10} {'Rows':<10} {'Earliest':<20} {'Latest':<20}\")
print('-' * 60)
for row in cur.fetchall():
    print(f'{row[0]:<10} {row[1]:<10} {str(row[2])[:19]:<20} {str(row[3])[:19]:<20}')
"
```

### 2. 查看最新特征值
```bash
python3 -c "
import psycopg2, os, pandas as pd
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('.env'))
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=int(os.getenv('POSTGRES_PORT')),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
df = pd.read_sql('''
    SELECT time, symbol, rsi_14, sma_50, atr_14, macd
    FROM market_features
    WHERE symbol = 'AAPL'
    ORDER BY time DESC
    LIMIT 5
''', conn)
print(df.to_string(index=False))
"
```

### 3. 运行 TDD 审计（完整验证）
```bash
python3 scripts/audit_task_096.py
```

应该看到:
```
✓ TA-Lib Environment: TA-Lib 0.6.8 installed
✓ Database Connection: Connected to PostgreSQL
✓ market_data Table: XXX rows, X symbols
✓ market_features Table: XX feature rows
✓ Feature Calculation Accuracy: All indicators calculated correctly

[SUCCESS] All tests passed!
```

---

## ⚠️ 常见问题

### 问题 1: "Insufficient data for feature calculation"

**原因**: 数据行数 < 50（最少需求）或 < 200（SMA_200 需求）

**解决**:
```bash
# 下载更多历史数据
python3 scripts/data/eodhd_bulk_loader.py --symbol AAPL --days 365
```

### 问题 2: "market_features table does not exist"

**原因**: 忘记初始化表结构

**解决**:
```bash
python3 scripts/audit_task_096.py --init-only
```

### 问题 3: TA-Lib 导入错误

**错误信息**: `ModuleNotFoundError: No module named 'talib'`

**解决**:
```bash
pip install ta-lib

# 如果编译失败，需要先安装 C 库（Ubuntu）
sudo apt-get install libta-lib-dev

# macOS
brew install ta-lib
```

### 问题 4: UserWarning about SQLAlchemy

**警告信息**: `pandas only supports SQLAlchemy connectable...`

**说明**: 这是 pandas 的警告，不影响功能，可以忽略或安装 SQLAlchemy:
```bash
pip install sqlalchemy
```

### 问题 5: 特征值全是 NaN

**原因**: 数据不足或时间序列不连续

**调试**:
```bash
# 检查原始数据
python3 -c "
import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('.env'))
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=int(os.getenv('POSTGRES_PORT')),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*), MIN(time), MAX(time) FROM market_data WHERE symbol=%s', ('AAPL',))
print(cur.fetchone())
"
```

---

## 🔧 高级用法

### 定时任务（Crontab）

每天凌晨 2 点增量更新所有股票特征:
```bash
crontab -e
```

添加:
```cron
0 2 * * * cd /opt/mt5-crs && python3 scripts/data/feature_engine.py --all --incremental >> /var/log/feature_engine.log 2>&1
```

### 自定义指标

编辑 `scripts/data/feature_engine.py`，在 `calculate_features()` 方法中添加:
```python
# 添加 CCI 指标
features['cci_14'] = talib.CCI(high_prices, low_prices, close_prices, timeperiod=14)
```

记得同步更新 `market_features` 表结构:
```sql
ALTER TABLE market_features ADD COLUMN cci_14 DOUBLE PRECISION;
```

---

## 📊 性能参考

**测试环境**: 2 vCPU / 8GB / TimescaleDB 14.17

| 数据量 | 符号数 | 耗时 | 吞吐量 |
|--------|--------|------|---------|
| 250 行 | 1 | 2.5s | 28 行/秒 |
| 5000 行 | 20 | 45s | 111 行/秒 |

**优化建议**:
- 使用 `--incremental` 避免重复计算
- 大批量处理时考虑使用 COPY 批量插入（需修改代码）

---

## 📞 技术支持

- **文档**: [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- **部署指南**: [SYNC_GUIDE.md](./SYNC_GUIDE.md)
- **代码位置**:
  - 特征引擎: [scripts/data/feature_engine.py](../../../scripts/data/feature_engine.py)
  - 审计脚本: [scripts/audit_task_096.py](../../../scripts/audit_task_096.py)

---

**文档版本**: v1.0
**最后更新**: 2026-01-13
**协议遵循**: v4.3 (Zero-Trust Edition)
