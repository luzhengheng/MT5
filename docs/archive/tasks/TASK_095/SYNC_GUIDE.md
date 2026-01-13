# TASK #095 同步指南
## 部署变更清单与环境配置

**协议版本**: v4.3 (Hub-Native Edition)
**目标环境**: Hub 节点 (sg-nexus-hub-01)
**变更类型**: 新增功能 (Historical Data Pipeline)

---

## 📦 部署清单

### 新增文件

| 文件路径 | 类型 | 说明 | 权限 |
|----------|------|------|------|
| `scripts/audit/audit_task_095.py` | Python | Gate 1 审计脚本 | 755 (可执行) |
| `scripts/data/eodhd_bulk_loader.py` | Python | 数据加载器 | 755 (可执行) |
| `docs/archive/tasks/TASK_095/COMPLETION_REPORT.md` | Markdown | 完成报告 | 644 |
| `docs/archive/tasks/TASK_095/QUICK_START.md` | Markdown | 快速启动指南 | 644 |
| `docs/archive/tasks/TASK_095/VERIFY_LOG.log` | 日志 | 验证日志 | 644 |
| `docs/archive/tasks/TASK_095/SYNC_GUIDE.md` | Markdown | 本文档 | 644 |

### 修改文件

| 文件路径 | 变更类型 | 说明 |
|----------|----------|------|
| `docker-compose.yml` | 复用 | 未修改,使用现有 TimescaleDB 配置 |
| `.env` | 复用 | 确认包含 `EODHD_API_TOKEN` 和 `POSTGRES_*` 变量 |

### 数据库变更

| 对象 | 类型 | DDL |
|------|------|-----|
| `timescaledb` extension | Extension | `CREATE EXTENSION IF NOT EXISTS timescaledb;` |
| `market_data` | Hypertable | 见下方 SQL 迁移脚本 |
| `idx_market_data_symbol_time` | Index | `CREATE INDEX ... ON market_data (symbol, time DESC);` |

---

## 🔧 环境变量清单

### 必需变量 (Required)

```bash
# PostgreSQL / TimescaleDB
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password      # ⚠️ 生产环境请使用强密码
POSTGRES_DB=mt5_crs

# EODHD API
EODHD_API_TOKEN=6953782f2a2fe5.46192922  # ⚠️ 请勿泄露
```

### 可选变量 (Optional)

```bash
# 暂无
```

### 验证命令

```bash
# 检查所有必需变量
grep -E "POSTGRES_HOST|POSTGRES_PORT|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|EODHD_API_TOKEN" .env

# 预期输出: 6 行配置
```

---

## 🐍 Python 依赖包

### 新增依赖

| 包名 | 版本要求 | 用途 |
|------|----------|------|
| `psycopg2-binary` | >= 2.9.0 | PostgreSQL 数据库驱动 |
| `pandas` | >= 1.5.0 | 数据清洗与转换 |
| `requests` | >= 2.28.0 | HTTP 请求 (EODHD API) |
| `python-dotenv` | >= 0.19.0 | 环境变量加载 |

### 安装命令

```bash
# 方法 A: 使用 requirements.txt (如果已存在)
pip3 install -r requirements.txt

# 方法 B: 手动安装
pip3 install psycopg2-binary pandas requests python-dotenv
```

### 验证命令

```bash
# 检查依赖
python3 -c "
import psycopg2
import pandas
import requests
from dotenv import load_dotenv
print('✓ All dependencies installed')
"
```

---

## 🗄️ SQL 迁移脚本

### 迁移脚本: `init_market_data.sql`

```sql
-- ============================================================
-- TASK #095: Initialize market_data hypertable
-- Protocol: v4.3 (Hub-Native Edition)
-- ============================================================

-- 1. 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. 创建 market_data 表
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,       -- 交易时间 (UTC)
    symbol VARCHAR(10) NOT NULL,     -- 股票代码
    open NUMERIC(12, 4),             -- 开盘价
    high NUMERIC(12, 4),             -- 最高价
    low NUMERIC(12, 4),              -- 最低价
    close NUMERIC(12, 4),            -- 收盘价
    volume BIGINT                    -- 成交量
);

-- 3. 转换为超表 (时间分区,7 天一个 chunk)
SELECT create_hypertable(
    'market_data',
    'time',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- 4. 创建索引 (优化按 symbol 查询)
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time
    ON market_data (symbol, time DESC);

-- 5. 验证
SELECT * FROM timescaledb_information.hypertables
WHERE hypertable_name = 'market_data';

-- 预期输出: 1 行,显示 hypertable 元数据
```

### 自动化迁移

```bash
# 方法 A: 使用审计脚本的初始化模式 (推荐)
python3 scripts/audit/audit_task_095.py --init-only

# 方法 B: 手动执行 SQL (如果有 psql)
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U trader -d mt5_crs -f init_market_data.sql
```

---

## 🐳 Docker / Podman 变更

### 容器状态要求

| 容器名称 | 镜像 | 状态 | 端口映射 |
|----------|------|------|----------|
| `timescaledb` | `timescale/timescaledb:latest-pg14` | Running | 5432:5432 |

### 启动命令

```bash
# Podman (Hub 默认)
podman start timescaledb

# Docker Compose (如果可用)
docker-compose up -d timescaledb
```

### 健康检查

```bash
# 检查容器状态
podman ps | grep timescaledb

# 检查数据库连接
python3 -c "import psycopg2; psycopg2.connect(host='localhost', port=5432, user='trader', password='password', database='mt5_crs'); print('✓ DB OK')"
```

---

## 🔐 安全注意事项

### 1. 敏感信息管理

| 类型 | 存储位置 | 注意事项 |
|------|----------|----------|
| EODHD API Token | `.env` | 已加入 `.gitignore`,不提交到 Git |
| PostgreSQL 密码 | `.env` | 生产环境需使用强密码 (16+ 字符) |
| 数据库数据 | `./data/timescaledb/` | 已加入 `.gitignore`,需单独备份 |

### 2. 网络安全

- **端口暴露**: TimescaleDB 仅监听 `localhost:5432`,未暴露公网
- **防火墙**: 无需修改防火墙规则 (本地访问)

### 3. 访问控制

- **数据库用户**: 当前使用 `trader` 用户 (权限: SUPERUSER)
- **建议**: 生产环境创建只读用户用于查询

---

## 📊 监控与告警

### 建议监控指标

| 指标 | 阈值 | 检查命令 |
|------|------|----------|
| 容器状态 | Up | `podman ps \| grep timescaledb` |
| 数据库连接数 | < 100 | `SELECT count(*) FROM pg_stat_activity;` |
| 磁盘使用率 | < 80% | `df -h \| grep data/timescaledb` |
| 数据新鲜度 | < 24 小时 | `SELECT MAX(time) FROM market_data;` |

### 告警脚本示例

```bash
#!/bin/bash
# 文件: scripts/monitoring/check_market_data.sh

MAX_AGE_HOURS=24

LATEST=$(python3 -c "
import psycopg2
from datetime import datetime, timezone
conn = psycopg2.connect(host='localhost', port=5432, user='trader', password='password', database='mt5_crs')
cursor = conn.cursor()
cursor.execute('SELECT MAX(time) FROM market_data;')
result = cursor.fetchone()[0]
if result:
    age_hours = (datetime.now(timezone.utc) - result).total_seconds() / 3600
    print(int(age_hours))
else:
    print(9999)
conn.close()
")

if [ "$LATEST" -gt "$MAX_AGE_HOURS" ]; then
    echo "⚠️ WARNING: Market data is $LATEST hours old (threshold: $MAX_AGE_HOURS)"
    exit 1
else
    echo "✓ Market data is fresh ($LATEST hours old)"
    exit 0
fi
```

---

## 🔄 回滚计划

如果部署出现问题,按以下步骤回滚:

### Step 1: 删除数据库表

```sql
DROP TABLE IF EXISTS market_data CASCADE;
```

### Step 2: 删除新增文件

```bash
rm -f scripts/audit/audit_task_095.py
rm -f scripts/data/eodhd_bulk_loader.py
rm -rf docs/archive/tasks/TASK_095/
```

### Step 3: 恢复 Git 状态 (如果需要)

```bash
git reset --hard HEAD~1  # 回退最后一次提交
```

---

## ✅ 部署验证清单

部署完成后,请按顺序执行以下验证:

- [ ] **环境变量**: `grep -E "POSTGRES|EODHD" .env` 输出 6 行
- [ ] **依赖包**: `python3 -c "import psycopg2, pandas, requests, dotenv"`
- [ ] **容器状态**: `podman ps | grep timescaledb` 显示 "Up"
- [ ] **数据库连接**: `python3 scripts/audit/audit_task_095.py` 通过前 2 项检查
- [ ] **Schema 创建**: `python3 scripts/audit/audit_task_095.py --init-only` 成功
- [ ] **完整审计**: `python3 scripts/audit/audit_task_095.py` 全部通过 (7/7)
- [ ] **数据加载测试**: `python3 scripts/data/eodhd_bulk_loader.py --symbol AAPL --days 7 --verify` 成功

---

## 📞 支持与联系

- **技术文档**: `docs/archive/tasks/TASK_095/`
- **快速启动**: `docs/archive/tasks/TASK_095/QUICK_START.md`
- **Notion 任务**: https://www.notion.so/TASK-095-2e7c88582b4e80328457f7361f03a275

---

**文档版本**: 1.0
**最后更新**: 2026-01-13
**维护者**: MT5-CRS DevOps Team
**协议遵循**: Protocol v4.3 (Zero-Trust Edition)
