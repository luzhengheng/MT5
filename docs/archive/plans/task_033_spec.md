# Task #033: Database Schema & Hypertable Setup

**Phase**: 2 (Data Intelligence - 数据智能)
**Protocol**: v2.6 (CLI --plan Integration)
**Status**: Ready for Implementation
**Dependencies**:
- Task #032: Data Nexus Infrastructure ✅
- Task #032.5: EODHD Data Verification ✅

---

## 🎯 目标

建立符合 `DATA_FORMAT_SPEC.md` 规范的数据库表结构，并启用 TimescaleDB 的超表（Hypertable）特性以优化时序查询。

**关键架构调整**:
由于 EODHD Bulk API 不可用（Task #032.5发现），Schema 必须支持**逐资产增量同步**。`Asset` 表的 `last_synced` 字段成为断点续传的核心机制。

---

## ✅ 交付内容

### 1. ORM 模型 (`src/data_nexus/models.py`)

定义以下 SQLAlchemy 模型：

#### Asset Table (资产清单表)
**Purpose**: 管理需要同步的股票列表和同步状态

```python
class Asset(Base):
    __tablename__ = "assets"

    symbol = Column(String(20), primary_key=True)  # e.g., AAPL.US
    exchange = Column(String(10), nullable=False)  # e.g., US, LSE
    asset_type = Column(String(20), nullable=False, default="Common Stock")
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced = Column(DateTime(timezone=True), nullable=True)  # 关键：断点续传
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Fields**:
- `symbol`: Primary key, ticker with exchange suffix
- `exchange`: Exchange code (from DATA_FORMAT_SPEC.md)
- `asset_type`: Common Stock, ETF, Index, etc.
- `is_active`: Control ingestion scope (pause/resume individual assets)
- `last_synced`: **Critical** - Last successful sync timestamp (for incremental updates)
- `created_at`, `updated_at`: Audit trail

#### MarketData Table (核心行情表 - Hypertable)
**Purpose**: Store OHLC historical data from EODHD EOD endpoint

```python
class MarketData(Base):
    __tablename__ = "market_data"

    time = Column(DateTime(timezone=True), primary_key=True)  # TimescaleDB partition key
    symbol = Column(String(20), primary_key=True)
    open = Column(Numeric(precision=12, scale=4), nullable=False)
    high = Column(Numeric(precision=12, scale=4), nullable=False)
    low = Column(Numeric(precision=12, scale=4), nullable=False)
    close = Column(Numeric(precision=12, scale=4), nullable=False)
    adjusted_close = Column(Numeric(precision=12, scale=4), nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_market_data_symbol_time", "symbol", "time"),
        {"timescaledb_hypertable": {"time_column_name": "time"}},
    )
```

**Fields**:
- `time`: Trading date (TIME ZONE aware), TimescaleDB partition key
- `symbol`: Stock ticker
- `open`, `high`, `low`, `close`: OHLC prices (NUMERIC for precision)
- `adjusted_close`: From DATA_FORMAT_SPEC.md (handles splits/dividends)
- `volume`: Trading volume (BIGINT for large volumes)

**Constraints**:
- Composite PK: (time, symbol)
- Index: (symbol, time DESC) for efficient time-series queries

#### CorporateAction Table (公司行动事件表)
**Purpose**: Track splits and dividends (affects adjusted_close calculation)

```python
class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    date = Column(Date, primary_key=True)
    symbol = Column(String(20), primary_key=True)
    action_type = Column(String(20), nullable=False)  # 'SPLIT' or 'DIVIDEND'
    value = Column(Numeric(precision=12, scale=6), nullable=False)
    currency = Column(String(3), nullable=True)

    __table_args__ = (
        Index("idx_corp_actions_symbol_date", "symbol", "date"),
    )
```

**Fields**:
- `date`: Event date
- `symbol`: Affected ticker
- `action_type`: SPLIT (stock split), DIVIDEND (dividend payment)
- `value`: Split ratio (e.g., 2.0 for 2-for-1) or dividend amount
- `currency`: USD, etc.

---

### 2. 数据库迁移 (Alembic)

#### Setup Alembic Framework
- Initialize Alembic in project root
- Configure `alembic.ini` with TimescaleDB connection string
- Create `alembic/env.py` with proper metadata import

#### Initial Migration Script
**File**: `alembic/versions/001_init_schema.py`

```python
"""Init schema with hypertables

Revision ID: 001_init_schema
Create Date: 2025-12-28
"""

def upgrade():
    # Create tables via SQLAlchemy metadata
    op.create_table('assets', ...)
    op.create_table('market_data', ...)
    op.create_table('corporate_actions', ...)

    # Convert market_data to hypertable (CRITICAL)
    op.execute("""
        SELECT create_hypertable(
            'market_data',
            'time',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 month'
        );
    """)

    # Enable compression (optional, for storage optimization)
    op.execute("""
        ALTER TABLE market_data SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'time DESC'
        );
    """)

def downgrade():
    # Drop hypertable first
    op.execute("DROP TABLE IF EXISTS market_data CASCADE;")
    op.drop_table('corporate_actions')
    op.drop_table('assets')
```

---

### 3. Hypertable Configuration

#### Partition Strategy
- **Chunk Size**: 1 month (balance between query performance and management overhead)
- **Partition Key**: `time` column
- **Segment By**: `symbol` (improves compression ratio)

#### Compression Policy
```sql
-- Compress chunks older than 7 days
SELECT add_compression_policy('market_data', INTERVAL '7 days');
```

#### Retention Policy (Future)
```sql
-- Drop chunks older than 5 years (for cost control)
SELECT add_retention_policy('market_data', INTERVAL '5 years');
```

---

### 4. 验证脚本 (`scripts/verify_schema.py`)

验证以下内容：

```python
def verify_schema():
    """Verify database schema setup"""
    # 1. Check tables exist
    tables = ['assets', 'market_data', 'corporate_actions']
    for table in tables:
        assert table_exists(table), f"Table {table} not found"

    # 2. Verify hypertable status
    result = query("SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name='market_data'")
    assert len(result) == 1, "market_data is not a hypertable"

    # 3. Insert test data
    insert_test_asset("TEST.US", "US", "Common Stock")
    insert_test_market_data("TEST.US", datetime.now(), 100.0, 105.0, 99.0, 103.0, 1000000)

    # 4. Query and verify
    data = query("SELECT * FROM market_data WHERE symbol='TEST.US'")
    assert len(data) == 1, "Test data not inserted"

    # 5. Clean up test data
    delete_test_data("TEST.US")

    print("✅ Schema verification passed")
```

---

## 📊 数据库设计决策

### 时间列选择: DateTime(timezone=True)
- **Reason**: EODHD data is in ET timezone
- **Storage**: PostgreSQL TIMESTAMP WITH TIME ZONE
- **Queries**: Use `AT TIME ZONE 'US/Eastern'` for market hours queries

### Numeric vs Float
- **Choice**: Numeric(precision=12, scale=4)
- **Reason**: Financial data requires exact decimal representation
- **Example**: 123.4567 stored exactly (no floating point errors)

### Symbol Format
- **Standard**: `{TICKER}.{EXCHANGE}` (e.g., AAPL.US, VOD.LSE)
- **Reason**: Matches EODHD convention
- **Length**: VARCHAR(20) sufficient for most tickers

### Asset Table Rationale
**Without Bulk API**, we must:
1. Maintain a list of assets to sync
2. Track last sync time per asset
3. Support pause/resume per asset
4. Handle incremental updates efficiently

**Field: last_synced**
- `NULL`: Never synced (initial state)
- `2025-12-20`: Last synced on this date
- **Usage**: `WHERE last_synced < NOW() - INTERVAL '1 day'` (find stale data)

---

## 🔄 依赖关系

**Input**:
- Task #032: TimescaleDB running ✅
- Task #032.5: `DATA_FORMAT_SPEC.md` ✅

**Output (for Task #034)**:
- `Asset` table: Provides list of symbols to ingest
- `MarketData` table: Target for EOD data
- `last_synced` field: Enables incremental sync logic

---

## 🛡️ 成功标准

| 标准 | 验收条件 |
|------|--------|
| Tables Created | assets, market_data, corporate_actions exist |
| Hypertable | `market_data` is a TimescaleDB hypertable |
| Compression | Compression policy enabled |
| Indexes | (symbol, time) index on market_data |
| Foreign Keys | None (denormalized for performance) |
| Migration | `alembic current` shows applied migration |
| Verification | `python3 scripts/verify_schema.py` returns 0 |

---

## 🚀 预期工作量

| 部分 | 时间 | 优先级 |
|------|------|--------|
| SQLAlchemy Models | 1 hour | ⭐⭐⭐ |
| Alembic Setup | 30 min | ⭐⭐⭐ |
| Migration Script | 1 hour | ⭐⭐⭐ |
| Hypertable Config | 30 min | ⭐⭐⭐ |
| Verification Script | 1 hour | ⭐⭐ |
| **总计** | **~4 hours** | |

---

## 🎓 学习成果

完成此任务后，你将拥有：
1. TimescaleDB hypertable 实战经验
2. SQLAlchemy ORM 与时序数据库集成
3. Alembic 数据库版本控制
4. 金融数据建模最佳实践
5. 增量同步架构设计思路

---

## 📝 技术栈

- **ORM**: SQLAlchemy 2.0+
- **Migration**: Alembic
- **Database**: TimescaleDB (PostgreSQL 14)
- **Data Types**: Numeric (exact decimal), BigInteger, DateTime(timezone=True)
- **Indexes**: B-tree on (symbol, time)
- **Partitioning**: TimescaleDB automatic time-based chunking

---

**Created**: 2025-12-28
**For Task**: #033
**Phase**: 2 (Data Intelligence)
**Protocol**: v2.6 (CLI --plan Integration)
**Critical Pivot**: Symbol-by-symbol sync (Bulk API unavailable)
