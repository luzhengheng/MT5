# feat: 完成工单 #003 - 统一 MT5 工作目录并解决路径混乱问题

**Status**: 完成
**Page ID**: 2d2c8858-2b4e-8196-9c57-d30a666154b5
**URL**: https://www.notion.so/feat-003-MT5-2d2c88582b4e81969c57d30a666154b5
**Created**: 2025-12-23T08:27:00.000Z
**Last Edited**: 2025-12-30T18:22:00.000Z

---

## Properties

- **类型**: 核心
- **优先级**: P0
- **状态**: 完成
- **标题**: feat: 完成工单 #003 - 统一 MT5 工作目录并解决路径混乱问题

---

## Content

---

## 📋 技术详情

### 架构选型

选择 TimescaleDB (PostgreSQL 扩展) 作为核心行情数据库。

* 优势: 支持标准 SQL，且针对时序数据有高压缩率。
* 超表设计: 按时间分片 (Chunking) 存储 `ticks` 和 `candles`。
### 💻 核心代码

```sql
SELECT create_hypertable('market_ticks', 'time');
CREATE INDEX ON market_ticks (symbol, time DESC);
```

---

## 📋 技术详情

### 架构选型

选择 TimescaleDB (PostgreSQL 扩展) 作为核心行情数据库。

* 优势: 支持标准 SQL，且针对时序数据有高压缩率。
* 超表设计: 按时间分片 (Chunking) 存储 `ticks` 和 `candles`。
### 💻 核心代码

```sql
SELECT create_hypertable('market_ticks', 'time');
CREATE INDEX ON market_ticks (symbol, time DESC);
```

---

## 📋 技术详情

### 架构选型

选择 TimescaleDB (PostgreSQL 扩展) 作为核心行情数据库。

* 优势: 支持标准 SQL，且针对时序数据有高压缩率。
* 超表设计: 按时间分片 (Chunking) 存储 `ticks` 和 `candles`。
### 💻 核心代码

```sql
SELECT create_hypertable('market_ticks', 'time');
CREATE INDEX ON market_ticks (symbol, time DESC);
```

