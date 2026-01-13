# Task #096 同步部署指南

**环境变更清单** - 其他环境部署时必读

---

## 📦 依赖变更

### Python 包依赖

**新增依赖**:
```txt
ta-lib==0.6.8
```

**安装命令**:
```bash
pip install ta-lib
```

**注意事项**:
- 原计划使用 `pandas-ta`，但因 Python 3.9 不兼容（需 >= 3.12）改用 `ta-lib`
- `ta-lib` 依赖系统级 C 库，首次安装需要编译环境

**系统依赖（如果 pip 安装失败）**:

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install ta-lib
```

macOS:
```bash
brew install ta-lib
pip install ta-lib
```

CentOS/RHEL:
```bash
sudo yum install -y gcc make wget
# 然后同 Ubuntu 的编译步骤
```

---

## 🗄️ 数据库变更

### 新增表结构

**表名**: `market_features`

```sql
CREATE TABLE market_features (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,

    -- Momentum Indicators
    rsi_14 DOUBLE PRECISION,

    -- Trend Indicators
    sma_20 DOUBLE PRECISION,
    sma_50 DOUBLE PRECISION,
    sma_200 DOUBLE PRECISION,
    ema_12 DOUBLE PRECISION,
    ema_26 DOUBLE PRECISION,

    -- Volatility Indicators
    atr_14 DOUBLE PRECISION,
    bbands_upper DOUBLE PRECISION,
    bbands_middle DOUBLE PRECISION,
    bbands_lower DOUBLE PRECISION,

    -- MACD
    macd DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    macd_hist DOUBLE PRECISION,

    -- Volume Indicators
    obv DOUBLE PRECISION,

    PRIMARY KEY (time, symbol)
);

-- 创建 TimescaleDB 超表
SELECT create_hypertable('market_features', 'time', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_market_features_symbol
ON market_features(symbol, time DESC);
```

**自动化脚本**:
```bash
python3 scripts/audit_task_096.py --init-only
```

**回滚 SQL**（如果需要删除）:
```sql
DROP TABLE IF EXISTS market_features CASCADE;
```

---

## 📂 新增文件清单

### 1. 核心业务代码
- **路径**: `scripts/data/feature_engine.py`
- **行数**: 401
- **功能**: 特征工程引擎主程序
- **权限**: `chmod +x`

### 2. TDD 审计脚本
- **路径**: `scripts/audit_task_096.py`
- **行数**: 372
- **功能**: 环境验证、表初始化、特征计算准确性测试
- **权限**: `chmod +x`

### 3. 文档归档
- **目录**: `docs/archive/tasks/TASK_096/`
- **文件**:
  - `COMPLETION_REPORT.md` - 完成报告
  - `QUICK_START.md` - 快速启动指南
  - `SYNC_GUIDE.md` - 本文件
  - `VERIFY_LOG.log` - 物理验尸日志

---

## 🔧 环境变量

**无新增环境变量** - 使用现有的 `.env` 配置：
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

---

## ✅ 部署验证清单

### Step 1: 环境验证
```bash
# 验证 TA-Lib
python3 -c "import talib; print(f'TA-Lib: {talib.__version__}')"
# 预期: TA-Lib: 0.6.8

# 验证数据库连接
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
print('Database connection: OK')
"
# 预期: Database connection: OK
```

### Step 2: 表结构初始化
```bash
python3 scripts/audit_task_096.py --init-only
```

**预期输出包含**:
```
✓ TA-Lib Environment: TA-Lib 0.6.8 installed
✓ Database Connection: Connected to PostgreSQL
✓ market_data Table: XXX rows, X symbols
✓ market_features table created successfully
  └─ Hypertable enabled with time partitioning
```

### Step 3: 功能测试
```bash
# 如果 market_data 为空，先下载数据
python3 scripts/data/eodhd_bulk_loader.py --symbol AAPL --days 365

# 运行特征计算
python3 scripts/data/feature_engine.py --symbol AAPL --task-id 096
```

**预期输出包含**:
```
[SUCCESS] Inserted XX feature rows for AAPL
PROCESSING STATISTICS
Symbols Processed: 1
Errors: 0
```

### Step 4: 完整审计
```bash
python3 scripts/audit_task_096.py
```

**预期输出**:
```
AUDIT SUMMARY
Total Tests: 5
✓ Passed: 5
[SUCCESS] All tests passed!
```

---

## 🚨 已知问题与解决方案

### Issue 1: TA-Lib 编译失败

**症状**:
```
error: command 'gcc' failed with exit status 1
```

**原因**: 缺少编译工具链或 ta-lib C 库

**解决**: 参考本文档「依赖变更 → 系统依赖」章节

### Issue 2: TimescaleDB 扩展未启用

**症状**:
```
ERROR:  function create_hypertable(unknown, unknown) does not exist
```

**原因**: 当前数据库未启用 TimescaleDB 扩展

**解决**:
```sql
-- 以 superuser 身份执行
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### Issue 3: 数据量不足

**症状**:
```
WARNING - Insufficient data for feature calculation (need 50+, got 19)
```

**原因**: market_data 表数据不足

**解决**: 下载更多历史数据
```bash
python3 scripts/data/eodhd_bulk_loader.py --symbol AAPL --days 365
```

---

## 🔄 数据迁移

### 从其他环境同步数据

**导出特征数据** (源环境):
```bash
PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
  -h localhost \
  -U trader \
  -d mt5_crs \
  -t market_features \
  --data-only \
  -F custom \
  -f market_features_backup.dump
```

**导入特征数据** (目标环境):
```bash
# 先创建表结构
python3 scripts/audit_task_096.py --init-only

# 导入数据
PGPASSWORD=$POSTGRES_PASSWORD pg_restore \
  -h localhost \
  -U trader \
  -d mt5_crs \
  --data-only \
  market_features_backup.dump
```

### 增量同步策略

如果目标环境需要定期从生产环境同步特征:

```bash
# 在生产环境执行增量计算
python3 scripts/data/feature_engine.py --all --incremental

# 导出最近 7 天的数据
PGPASSWORD=$POSTGRES_PASSWORD psql \
  -h localhost \
  -U trader \
  -d mt5_crs \
  -c "\copy (SELECT * FROM market_features WHERE time >= NOW() - INTERVAL '7 days') TO '/tmp/features_recent.csv' WITH CSV HEADER"

# 在目标环境导入
PGPASSWORD=$POSTGRES_PASSWORD psql \
  -h localhost \
  -U trader \
  -d mt5_crs \
  -c "\copy market_features FROM '/tmp/features_recent.csv' WITH CSV HEADER"
```

---

## 🔐 权限要求

### 数据库用户权限
```sql
-- 最小权限集
GRANT SELECT, INSERT, UPDATE ON market_data TO trader;
GRANT SELECT, INSERT, UPDATE, DELETE ON market_features TO trader;
GRANT USAGE ON SCHEMA public TO trader;
```

### 文件系统权限
```bash
chmod +x scripts/data/feature_engine.py
chmod +x scripts/audit_task_096.py
```

---

## 📊 性能优化建议

### 1. 索引优化
```sql
-- 如果经常按 symbol 查询特定时间范围
CREATE INDEX IF NOT EXISTS idx_features_symbol_time
ON market_features(symbol, time DESC);

-- 如果经常按特征值过滤（例如 RSI < 30）
CREATE INDEX IF NOT EXISTS idx_features_rsi
ON market_features(rsi_14) WHERE rsi_14 IS NOT NULL;
```

### 2. 批量插入优化

当前代码使用逐行插入，可优化为 COPY：

```python
# 在 write_features() 方法中替换为:
from io import StringIO

csv_buffer = StringIO()
feature_df[columns].to_csv(csv_buffer, index=False, header=False)
csv_buffer.seek(0)

cur.copy_expert(
    f"COPY market_features ({', '.join(columns)}) FROM STDIN WITH CSV",
    csv_buffer
)
```

**性能提升**: 从 28 行/秒 → 500+ 行/秒

### 3. 并行计算

对于多股票处理，使用多线程:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(engine.process_symbol, symbol) for symbol in symbols]
```

---

## 📞 技术支持

- **Issue Tracker**: GitHub Issues
- **文档**: [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- **快速启动**: [QUICK_START.md](./QUICK_START.md)

---

**文档版本**: v1.0
**最后更新**: 2026-01-13
**协议遵循**: v4.3 (Zero-Trust Edition)
