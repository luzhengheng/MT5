# Task #034: EODHD Async Ingestion Engine Specification

**Phase**: 2 (Data Intelligence - 数据智能)
**Protocol**: v2.6 (CLI --plan Integration)
**Status**: Ready for Implementation
**Dependencies**:
- Task #033: Database Schema ✅
- Task #032: Data Nexus Infrastructure ✅

---

## 🎯 目标

构建生产级异步 ETL 管道，实现两大功能：
1. **资产发现 (Asset Discovery)**: 获取交易所股票列表，维护 `assets` 表
2. **历史数据加载 (History Loader)**: 逐个下载 OHLCV 数据，增量更新 `market_data` 超表

**核心架构设计**: 利用 `Asset.last_synced` 作为游标，实现断点续传和暂停/恢复功能。

---

## 🛡️ 约束条件与策略

### 1. 存储约束: 80GB PL0 磁盘 (低 IOPS)

| 问题 | 对策 |
|------|------|
| IOPS 低 → 并发过高导致 I/O 锁 | 默认并发数 = 5-8 (可调) |
| 单次提交大量行导致内存溢出 | 批写入: 内存累积 5000+ 行再提交 |
| 频繁的小 INSERT 语句低效 | 使用 SQLAlchemy `bulk_save_objects()` |

### 2. API 约束: 无 Bulk API

| 问题 | 对策 |
|------|------|
| 无法一次性下载所有股票的数据 | 符号-逐符号循环 (Symbol-by-Symbol Loop) |
| 需要跟踪 N 个符号的同步状态 | `Asset.last_synced` 游标机制 |
| 中断后需要从上次断点继续 | 查询 `WHERE last_synced IS NULL OR last_synced < NOW() - INTERVAL '1 day'` |

### 3. 网络稳定性约束

| 问题 | 对策 |
|------|------|
| API 服务偶尔返回 5xx 错误 | 指数退避重试 (Exponential Backoff) |
| 连接超时 | 设置合理的 timeout (30s) |
| 一个符号失败不应中止整个过程 | Per-asset 错误处理和日志 |

---

## ✅ 交付内容

### 1. 资产发现服务 (`src/data_nexus/ingestion/asset_discovery.py`)

**职责**: 从 EODHD 获取交易所符号列表并保存到数据库。

```python
class AssetDiscovery:
    """Exchange symbol list discovery and ingestion."""

    def __init__(self, api_key: str, db_config: DatabaseConfig):
        self.api_key = api_key
        self.db_config = db_config

    async def discover_exchange(self, exchange: str) -> int:
        """
        Fetch symbols from EODHD exchange endpoint.

        Args:
            exchange: Exchange code (e.g., 'US', 'LSE', 'TSE')

        Returns:
            Number of new assets added to database

        Endpoint: /api/exchange-symbol-list/{exchange}
        Response format: CSV with columns [Code, Exchange, Name, Type, Country, Currency, ISIN, ...]

        Logic:
            1. Fetch symbol list from API
            2. Parse CSV response
            3. For each symbol:
               - Upsert into assets table
               - Set is_active=True
               - Set last_synced=NULL (needs data)
            4. Return count of newly added assets
        """
```

**数据库操作**:
```python
def _upsert_asset(self, session, symbol: str, exchange: str, asset_type: str):
    """Upsert single asset into database."""
    asset = session.query(Asset).filter_by(symbol=symbol).first()
    if asset:
        # Asset exists, reactivate if needed
        asset.is_active = True
    else:
        # New asset, create with last_synced=NULL
        asset = Asset(
            symbol=symbol,
            exchange=exchange,
            asset_type=asset_type,
            is_active=True,
            last_synced=None  # Signals: needs data
        )
        session.add(asset)
```

### 2. 核心加载器 (`src/data_nexus/ingestion/history_loader.py`)

**职责**: 异步下载历史 OHLCV 数据并批量写入数据库。

```python
class EODHistoryLoader:
    """
    High-performance async OHLCV data loader.

    Design Principles:
    1. Low Concurrency (5-8): Respect PL0 disk constraints
    2. Aggressive Batching: Accumulate 5000+ rows before insert
    3. Cursor-based: Use Asset.last_synced for resume capability
    4. Error Resilience: Per-asset error handling, exponential backoff
    """

    def __init__(self, api_key: str, db_config: DatabaseConfig):
        self.api_key = api_key
        self.db_config = db_config
        self.batch_size = 100  # Rows to fetch per API call
        self.write_batch_size = 5000  # Rows to accumulate before DB insert
        self.concurrency = 5  # Semaphore limit for concurrent requests
        self.timeout = 30  # Seconds per request

    async def run_cycle(self, limit: int = None, days_old: int = 1):
        """
        Run one cycle of incremental data loading.

        Args:
            limit: Max assets to process in this run (prevents OOM)
            days_old: Only sync assets where last_synced < NOW - {days_old} days

        Logic:
            1. Query assets to sync:
               SELECT * FROM assets
               WHERE is_active=True
               AND (last_synced IS NULL OR last_synced < NOW - INTERVAL '{days_old} days')
               ORDER BY last_synced ASC NULLS FIRST
               LIMIT {limit}

            2. Create asyncio.Queue with these assets

            3. Spawn N worker coroutines (controlled by Semaphore):
               - Fetch /api/eod/{symbol}.{exchange}
               - Parse response (handle both JSON and CSV formats)
               - Transform to MarketData objects
               - Accumulate in batch buffer
               - When batch reaches write_batch_size:
                 * Execute bulk_save_objects()
                 * Clear buffer

            4. Update Asset.last_synced = datetime.now()

            5. Return summary: {total_assets: N, total_rows: M, failed: L}
        """
```

**关键实现细节**:

**处理空值和异常**:
```python
async def _fetch_symbol(self, session: Session, asset: Asset) -> list[MarketData]:
    """Fetch and parse OHLCV data for single symbol."""
    try:
        # Construct URL: /api/eod/{symbol} with proper parameters
        url = f"{EODHD_API_URL}/eod/{asset.symbol}"
        params = {
            "api_token": self.api_key,
            "fmt": "json",
            "period": "d"  # Daily
        }

        # If asset.last_synced is not None, fetch only newer data
        if asset.last_synced:
            from_date = (asset.last_synced.date() + timedelta(days=1)).isoformat()
            params["from"] = from_date

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=self.timeout) as resp:
                if resp.status == 404:
                    logger.warning(f"Asset {asset.symbol} not found (404)")
                    return []
                elif resp.status == 429:
                    logger.warning(f"Rate limited on {asset.symbol}, backing off")
                    await asyncio.sleep(60)  # Back off 1 minute
                    return []
                elif resp.status >= 500:
                    logger.error(f"Server error {resp.status} for {asset.symbol}")
                    return []  # Don't update last_synced, retry next cycle

                data = await resp.json()

        # Parse response
        if isinstance(data, dict) and "error" in data:
            logger.error(f"API error for {asset.symbol}: {data['error']}")
            return []

        if not isinstance(data, list):
            logger.error(f"Unexpected response format for {asset.symbol}")
            return []

        # Transform to MarketData objects
        market_data_list = []
        for row in data:
            try:
                md = MarketData(
                    time=datetime.fromisoformat(row["date"]).replace(tzinfo=timezone.utc),
                    symbol=asset.symbol,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    adjusted_close=Decimal(str(row.get("adjusted_close", row["close"]))),
                    volume=int(row["volume"])
                )
                market_data_list.append(md)
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Parse error in {asset.symbol} row {row}: {e}")
                continue

        return market_data_list

    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {asset.symbol}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching {asset.symbol}: {e}")
        return []
```

**批写入逻辑 (Critical for PL0)**:
```python
async def _run_workers(self, assets_queue: asyncio.Queue, session: Session):
    """
    Worker coroutines that fetch data and batch-write to DB.

    Key: Accumulate rows in memory, write in large batches.
    """
    semaphore = asyncio.Semaphore(self.concurrency)
    batch_buffer = []
    assets_to_update = []

    async def worker():
        nonlocal batch_buffer, assets_to_update

        while True:
            try:
                asset = assets_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            async with semaphore:
                logger.info(f"Fetching {asset.symbol}...")
                market_data_list = await self._fetch_symbol(session, asset)

                if market_data_list:
                    batch_buffer.extend(market_data_list)
                    assets_to_update.append(asset)
                    logger.info(f"  → {len(market_data_list)} rows for {asset.symbol}")

                    # Check if we should flush batch to DB
                    if len(batch_buffer) >= self.write_batch_size:
                        logger.info(f"Flushing {len(batch_buffer)} rows to database...")
                        session.bulk_save_objects(batch_buffer)
                        session.commit()
                        batch_buffer.clear()
                else:
                    logger.warning(f"  → No data for {asset.symbol}")

                assets_queue.task_done()

    # Run workers
    workers = [asyncio.create_task(worker()) for _ in range(self.concurrency)]
    await asyncio.gather(*workers)

    # Final flush for remaining rows
    if batch_buffer:
        logger.info(f"Final flush: {len(batch_buffer)} rows to database...")
        session.bulk_save_objects(batch_buffer)
        session.commit()

    # Update asset.last_synced
    for asset in assets_to_update:
        asset.last_synced = datetime.now(timezone.utc)
    session.commit()
```

### 3. 命令行接口 (`bin/run_ingestion.py`)

```python
"""
CLI for asset discovery and historical data ingestion.

Usage:
    python3 bin/run_ingestion.py discover --exchange US
    python3 bin/run_ingestion.py backfill --limit 100 --concurrency 5 --days-old 1
"""

import asyncio
import click
from src.data_nexus.ingestion.asset_discovery import AssetDiscovery
from src.data_nexus.ingestion.history_loader import EODHistoryLoader
from src.data_nexus.config import DatabaseConfig

@click.group()
def cli():
    """EODHD Ingestion CLI"""
    pass

@cli.command()
@click.option('--exchange', required=True, help='Exchange code (US, LSE, TSE, etc.)')
def discover(exchange):
    """Discover and ingest assets for an exchange."""
    api_key = os.environ.get('EODHD_API_KEY')
    if not api_key:
        click.echo("❌ EODHD_API_KEY not found")
        return 1

    db_config = DatabaseConfig()
    discovery = AssetDiscovery(api_key, db_config)

    click.echo(f"📥 Discovering assets for {exchange}...")
    count = asyncio.run(discovery.discover_exchange(exchange))
    click.echo(f"✅ Added/updated {count} assets")
    return 0

@cli.command()
@click.option('--limit', default=100, help='Max assets to process (prevents OOM)')
@click.option('--concurrency', default=5, help='Concurrent API requests')
@click.option('--days-old', default=1, help='Sync assets older than N days')
def backfill(limit, concurrency, days_old):
    """
    Download historical OHLCV data for assets.

    Example:
        python3 bin/run_ingestion.py backfill --limit 500 --concurrency 5
    """
    api_key = os.environ.get('EODHD_API_KEY')
    if not api_key:
        click.echo("❌ EODHD_API_KEY not found")
        return 1

    db_config = DatabaseConfig()
    loader = EODHistoryLoader(api_key, db_config)
    loader.concurrency = concurrency

    click.echo(f"⏳ Starting backfill: limit={limit}, concurrency={concurrency}...")
    start_time = datetime.now()

    summary = asyncio.run(loader.run_cycle(limit=limit, days_old=days_old))

    elapsed = (datetime.now() - start_time).total_seconds()
    click.echo(f"✅ Backfill complete in {elapsed:.1f}s")
    click.echo(f"   Assets processed: {summary['total_assets']}")
    click.echo(f"   Rows inserted: {summary['total_rows']}")
    click.echo(f"   Failed: {summary['failed']}")

    return 0

if __name__ == '__main__':
    cli()
```

### 4. 验证脚本 (`scripts/verify_ingestion.py`)

```python
"""
Verify asset discovery and data ingestion.

Tests:
1. Discover: Fetch symbols and verify they're in DB
2. Backfill: Load data for 10 test assets
3. Query: Verify market_data rows exist and last_synced was updated
"""

def test_discover():
    """Test asset discovery for US exchange."""
    print("🧪 Testing asset discovery...")
    result = subprocess.run(
        ["python3", "bin/run_ingestion.py", "discover", "--exchange", "US"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Discovery failed: {result.stderr}")
        return False

    # Verify assets were added
    conn = PostgresConnection()
    count = conn.query_scalar("SELECT COUNT(*) FROM assets WHERE exchange='US'")

    if count > 0:
        print(f"✅ Discovery successful: {count} US assets in database")
        return True
    else:
        print("❌ No assets found after discovery")
        return False

def test_backfill():
    """Test data ingestion for small subset."""
    print("🧪 Testing data backfill...")
    result = subprocess.run(
        ["python3", "bin/run_ingestion.py", "backfill", "--limit", "10", "--concurrency", "2"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Backfill failed: {result.stderr}")
        return False

    # Verify data was inserted
    conn = PostgresConnection()
    rows = conn.query_scalar("SELECT COUNT(*) FROM market_data")

    if rows > 0:
        print(f"✅ Backfill successful: {rows} OHLCV rows in database")
        return True
    else:
        print("❌ No market data found after backfill")
        return False

def test_last_synced_updated():
    """Verify Asset.last_synced was updated."""
    print("🧪 Testing last_synced tracking...")
    conn = PostgresConnection()
    result = conn.query_scalar(
        "SELECT COUNT(*) FROM assets WHERE last_synced IS NOT NULL"
    )

    if result > 0:
        print(f"✅ last_synced updated for {result} assets")
        return True
    else:
        print("❌ last_synced not updated after backfill")
        return False
```

---

## 📊 项目结构

```
src/data_nexus/
├── ingestion/
│   ├── __init__.py
│   ├── asset_discovery.py      # Exchange symbol discovery
│   ├── history_loader.py       # Async OHLCV downloader
│   └── retry_policy.py         # Exponential backoff logic
├── models.py                   # SQLAlchemy ORM (from Task #033)
├── database/
│   └── connection.py           # PostgreSQL connection pool
└── config.py                   # Configuration (API key, DB URL)

bin/
└── run_ingestion.py           # CLI entry point

scripts/
└── verify_ingestion.py        # End-to-end tests
```

---

## 🔧 技术栈

| 组件 | 库 | 版本 | 用途 |
|------|-----|------|------|
| 异步运行时 | `asyncio` | stdlib | Event loop 和 coroutine 管理 |
| HTTP 客户端 | `aiohttp` | 3.9+ | 异步 HTTP 请求 |
| DNS 解析 | `aiodns` | 3.1+ | 异步 DNS (可选，加快 DNS 查询) |
| 数据库 | `SQLAlchemy` | 2.0+ | ORM 和 bulk operations |
| 数据库驱动 | `psycopg2` | 2.9+ | PostgreSQL 适配器 |
| CLI | `click` | 8.1+ | 命令行参数解析 |
| 日志 | `logging` | stdlib | 标准日志 |

**更新 requirements.txt**:
```
aiohttp>=3.9.0
aiodns>=3.1.0
```

---

## 🚀 预期工作量

| 部分 | 时间 | 优先级 |
|------|------|--------|
| 资产发现服务 | 1.5 hours | ⭐⭐⭐ |
| 历史加载器 | 2.5 hours | ⭐⭐⭐ |
| 命令行接口 | 1 hour | ⭐⭐⭐ |
| 验证脚本 | 1 hour | ⭐⭐ |
| **总计** | **6 hours** | |

---

## 🛡️ 成功标准

| 标准 | 验收条件 |
|------|---------|
| Asset Discovery | `python3 bin/run_ingestion.py discover --exchange US` 添加 10,000+ 资产 |
| Data Ingestion | `python3 bin/run_ingestion.py backfill --limit 100` 加载 50,000+ 行 OHLCV 数据 |
| Batch Writing | 观察日志显示批量写入 (5000+ 行/次) 而非行-逐-行 |
| Error Handling | 单个资产失败不中止整个过程，失败被记录 |
| Resume Capability | 第二次运行 backfill 应仅处理 `last_synced IS NULL` 或老化的资产 |
| Performance | 100 资产的完整周期 < 60 秒 (并发=5) |

---

## 🎓 关键设计决策

### 为什么是异步而非多进程?
- **理由**: aiohttp 轻量级，适合 I/O 密集的 API 调用。Python multiprocessing 对于网络 I/O 开销大。
- **权衡**: GIL 限制 CPU 并行，但我们主要是等待 I/O，所以 asyncio 足够。

### 为什么批写入而非逐行插入?
- **理由**: PL0 磁盘 IOPS 低。每个 INSERT 语句都是一次数据库往返，非常低效。
- **SQLAlchemy bulk_save_objects()**: 生成单个 INSERT...VALUES(...), (...), ... 语句，1000 行 = 1 个往返。
- **5000 行批大小**: 在内存和数据库性能之间的平衡。

### 为什么并发数限制为 5-8?
- **理由**: PL0 磁盘 IOPS 受限，过多的并发请求会导致数据库连接池 stall。
- **观察**: Semaphore(5) 限制并发 HTTP 请求，确保每个数据库写操作有足够的时间完成。
- **调优空间**: 如果监控显示 CPU/I/O 有余量，可以提升到 10-20。

### 为什么用 Asset.last_synced 而非单独的状态表?
- **理由**: Simple is better. 一个字段胜过额外的表。`NULL` 表示未同步，timestamp 表示最后成功时间。
- **恢复**: 重新启动 loader 后，自动继续处理 `last_synced IS NULL` 或 `< NOW() - INTERVAL '1 day'` 的资产。

---

## 📝 部署清单

- [ ] 安装依赖: `pip install -r requirements.txt`
- [ ] 验证 EODHD_API_KEY 在环境中设置
- [ ] 验证数据库连接 (Task #032)
- [ ] 运行 Alembic 迁移 (Task #033): `alembic upgrade head`
- [ ] 运行验证脚本: `python3 scripts/verify_ingestion.py`
- [ ] 首次运行: `python3 bin/run_ingestion.py discover --exchange US`
- [ ] 首次加载: `python3 bin/run_ingestion.py backfill --limit 1000 --concurrency 5`

---

**Created**: 2025-12-28
**For Task**: #034
**Phase**: 2 (Data Intelligence)
**Protocol**: v2.6 (CLI --plan Integration)
**Critical Constraints**: PL0 Disk (IOPS Low), No Bulk API
