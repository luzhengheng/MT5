# TASK #095 快速启动指南
## EODHD 历史数据冷路径 - 傻瓜式操作手册

**目标用户**: 运维人员、测试人员、新加入开发者
**预计时间**: 5-10 分钟
**前置条件**: 已配置 `.env` 文件中的 EODHD API Token

---

## 🚀 快速启动 (3 步走)

### Step 1: 启动 TimescaleDB 容器

```bash
# 方法 A: 使用 Podman (推荐,Hub 节点默认)
podman start timescaledb

# 方法 B: 使用 Docker Compose (如果可用)
docker-compose up -d timescaledb

# 验证容器状态
podman ps | grep timescale
# 期望输出: Up X minutes
```

### Step 2: 初始化数据库 Schema (首次运行)

```bash
# 运行审计脚本的初始化模式
python3 scripts/audit/audit_task_095.py --init-only

# 期望输出:
# ✓ TimescaleDB extension created
# ✓ Table 'market_data' created
# ✓ Hypertable created
# ✓ Index created
# ✅ Database initialization completed successfully
```

### Step 3: 下载历史数据

```bash
# 示例 1: 下载单只股票 (AAPL)
python3 scripts/data/eodhd_bulk_loader.py \
    --symbol AAPL \
    --days 30 \
    --task-id 095 \
    --verify

# 示例 2: 下载多只股票
python3 scripts/data/eodhd_bulk_loader.py \
    --symbols AAPL,MSFT,GOOGL,TSLA \
    --days 90

# 示例 3: 从文件批量下载
echo -e "AAPL\nMSFT\nGOOGL" > tickers.txt
python3 scripts/data/eodhd_bulk_loader.py \
    --symbols-file tickers.txt \
    --days 365 \
    --task-id 095
```

---

## 🔍 验证与测试

### 验证 1: 运行完整审计

```bash
# 运行 Gate 1 审计 (7 项检查)
python3 scripts/audit/audit_task_095.py

# 期望输出:
# ✅ GATE 1 PASSED - All checks successful
```

### 验证 2: 查看数据库内容

```bash
# 使用 Python 快速查询
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='trader',
    password='password',
    database='mt5_crs'
)
cursor = conn.cursor()
cursor.execute('SELECT symbol, COUNT(*), MIN(time), MAX(time) FROM market_data GROUP BY symbol;')
print('Symbol | Rows | Min Date | Max Date')
print('-' * 80)
for row in cursor.fetchall():
    print(f'{row[0]} | {row[1]} | {row[2]} | {row[3]}')
conn.close()
"
```

### 验证 3: 检查超表状态

```bash
# 查看超表分区信息
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, user='trader', password='password', database='mt5_crs')
cursor = conn.cursor()
cursor.execute('SELECT * FROM timescaledb_information.hypertables;')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

---

## 📋 脚本参数说明

### `eodhd_bulk_loader.py` 参数

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--symbol` | 否* | 单个股票代码 | `--symbol AAPL` |
| `--symbols` | 否* | 逗号分隔的多个代码 | `--symbols AAPL,MSFT` |
| `--symbols-file` | 否* | 包含代码的文本文件 | `--symbols-file list.txt` |
| `--days` | 否 | 历史数据天数 (默认 30) | `--days 90` |
| `--task-id` | 否 | 任务 ID (用于日志追踪) | `--task-id 095` |
| `--verify` | 否 | 完成后查询验证 | `--verify` |

**注意**: `--symbol`, `--symbols`, `--symbols-file` 三者必须提供其一。

### `audit_task_095.py` 参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `--init-only` | 否 | 仅初始化数据库,不运行审计 |
| (无参数) | - | 运行完整的 7 项审计检查 |

---

## 🛠️ 常见问题排查

### Q1: 容器无法启动

```bash
# 检查 Podman 服务
podman version

# 查看容器日志
podman logs timescaledb

# 重新创建容器
podman-compose up -d --force-recreate timescaledb
```

### Q2: 数据库连接失败

```bash
# 检查容器端口
podman port timescaledb

# 检查 .env 配置
grep POSTGRES .env

# 测试连接
python3 -c "import psycopg2; psycopg2.connect(host='localhost', port=5432, user='trader', password='password', database='mt5_crs'); print('✓ Connection OK')"
```

### Q3: EODHD API 返回错误

```bash
# 检查 API Token
grep EODHD_API_TOKEN .env

# 测试 API (手动)
curl "https://eodhistoricaldata.com/api/eod/AAPL.US?api_token=YOUR_TOKEN&fmt=json&from=2026-01-01&to=2026-01-10"
```

### Q4: 数据插入失败

```bash
# 删除并重建表
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, user='trader', password='password', database='mt5_crs')
conn.autocommit = True
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS market_data CASCADE;')
print('Table dropped')
conn.close()
"

# 重新初始化
python3 scripts/audit/audit_task_095.py --init-only
```

---

## 📊 数据库 Schema 参考

### `market_data` 表结构

```sql
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,       -- 交易日期时间 (UTC)
    symbol VARCHAR(10) NOT NULL,     -- 股票代码
    open NUMERIC(12, 4),             -- 开盘价
    high NUMERIC(12, 4),             -- 最高价
    low NUMERIC(12, 4),              -- 最低价
    close NUMERIC(12, 4),            -- 收盘价
    volume BIGINT                    -- 成交量
);

-- 转换为超表 (按时间分区)
SELECT create_hypertable('market_data', 'time');

-- 索引 (优化查询性能)
CREATE INDEX idx_market_data_symbol_time ON market_data (symbol, time DESC);
```

---

## 🔄 日常维护任务

### 每日数据更新 (示例)

```bash
#!/bin/bash
# 文件: scripts/daily_eodhd_sync.sh

# 主要股票池
SYMBOLS="AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA"

# 下载最近 7 天数据 (覆盖周末)
python3 scripts/data/eodhd_bulk_loader.py \
    --symbols "$SYMBOLS" \
    --days 7 \
    --task-id daily-sync

# 运行数据质量检查
python3 scripts/audit/audit_task_095.py
```

### 备份数据库

```bash
# 导出为 SQL
podman exec timescaledb pg_dump -U trader mt5_crs > backup_$(date +%Y%m%d).sql

# 或使用 TimescaleDB 的 pg_dump
podman exec timescaledb pg_dump -U trader -Fc mt5_crs > backup_$(date +%Y%m%d).dump
```

---

## 📞 故障升级

如果遇到无法解决的问题:

1. **收集日志**:
   ```bash
   podman logs timescaledb > db_logs.txt
   cat VERIFY_LOG.log > verify_logs.txt
   python3 scripts/audit/audit_task_095.py > audit_logs.txt 2>&1
   ```

2. **检查环境**:
   ```bash
   podman version
   python3 --version
   grep -E "POSTGRES|EODHD" .env
   ```

3. **联系支持**: 将上述日志和环境信息发送给技术团队。

---

**文档版本**: 1.0
**最后更新**: 2026-01-13
**维护者**: MT5-CRS DevOps Team
