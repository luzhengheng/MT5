# Task #032: Data Nexus Infrastructure Deployment

**Phase**: 2 (Data Intelligence - 数据智能)
**Protocol**: v2.6 (CLI --plan Integration)
**Status**: Ready for Implementation

---

## 🎯 目标

根据**EODHD使用方案**部署**"离线/实时分离"**的数据存储基础设施，为后续的数据摄取和特征工程奠定基础。

核心理念：
- **TimescaleDB** (持久化): 存储历史数据、特征、训练标签
- **Redis** (实时): 缓存行情数据、特征、交易信号
- **Docker**: 容器化部署，实现可复现的环境

---

## ✅ 交付内容

### 1. 容器和基础设施 (Docker)

#### TimescaleDB Service
```yaml
Service: timescaledb
Image: timescale/timescaledb:latest-pg14
Port: 5432:5432
Volume: ./data/timescaledb:/var/lib/postgresql/data
Environment:
  - POSTGRES_USER=trader
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  - POSTGRES_DB=mt5_crs
```

**功能**:
- 存储 OHLC 行情数据 (symbols, timeframes)
- 存储特征工程结果 (32 technical indicators)
- 存储标签数据 (24h lookahead labels)
- 存储训练集、验证集、测试集

**Schema Design** (Phase 3):
- `market_data` (symbol, timestamp, ohlc)
- `features` (symbol, timestamp, feature_values)
- `labels` (symbol, timestamp, label)

#### Redis Service
```yaml
Service: redis
Image: redis:7-alpine
Port: 6379:6379
Command: redis-server --appendonly yes
```

**功能**:
- 缓存最新行情 (real-time ticks)
- 缓存计算中的特征 (feature cache)
- 缓存交易信号 (signal cache)
- 缓存会话数据 (session cache)

**Key Patterns** (Phase 3):
- `market:{symbol}:latest` → JSON price data
- `features:{symbol}:{timestamp}` → Feature vector
- `signals:{symbol}:pending` → Trading signals
- `sessions:{trader_id}:state` → State JSON

#### Docker Network
```yaml
networks:
  mt5-network:
    driver: bridge
```

**目的**: 容器间通信，允许应用层 (Python) 连接到数据存储

### 2. 项目结构初始化

创建 Python 模块层次:

```
src/
├── data_nexus/              # NEW: 数据中心核心
│   ├── __init__.py
│   ├── config.py            # 配置加载器
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py    # TimescaleDB 连接管理
│   │   ├── schema.py        # 表定义 (Phase 3)
│   │   └── migrations.py    # Alembic 迁移 (Phase 3)
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── redis_client.py  # Redis 客户端包装
│   │   └── serializers.py   # JSON 序列化
│   └── health.py            # 健康检查端点

scripts/
├── verify_data_infra.py     # NEW: 基础设施验证脚本
└── docker-compose.yml       # NEW: 容器编排配置
```

### 3. 配置管理

#### .env 文件变量
```bash
# Database
POSTGRES_USER=trader
POSTGRES_PASSWORD=secure_password_change_in_production
POSTGRES_DB=mt5_crs
DB_HOST=timescaledb
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### config.py 示例
```python
import os
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", 5432))
    user: str = os.getenv("POSTGRES_USER", "trader")
    password: str = os.getenv("POSTGRES_PASSWORD")
    database: str = os.getenv("POSTGRES_DB", "mt5_crs")

    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6379))
    db: int = int(os.getenv("REDIS_DB", 0))

    def connection_url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"
```

### 4. 验证脚本 (verify_data_infra.py)

```python
#!/usr/bin/env python3
"""
Verification Script for Data Infrastructure

Tests:
1. TimescaleDB connectivity
2. Redis connectivity
3. Table creation capability
4. Caching capability
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_postgres():
    """Verify TimescaleDB connectivity"""
    from src.data_nexus.database.connection import PostgresConnection

    try:
        conn = PostgresConnection()
        version = conn.query_scalar("SELECT version()")
        print(f"✅ PostgreSQL: {version[:50]}...")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False

def verify_redis():
    """Verify Redis connectivity"""
    from src.data_nexus.cache.redis_client import RedisClient

    try:
        redis = RedisClient()
        redis.ping()
        print(f"✅ Redis: Connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis Error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("📊 DATA INFRASTRUCTURE VERIFICATION")
    print("=" * 60)
    print()

    results = []

    print("[1/2] Testing PostgreSQL/TimescaleDB...")
    results.append(verify_postgres())
    print()

    print("[2/2] Testing Redis...")
    results.append(verify_redis())
    print()

    print("=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - Infrastructure ready")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Check setup")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 5. 依赖关系和版本

```
# requirements.txt additions
sqlalchemy==2.0.23          # ORM for TimescaleDB
psycopg2-binary==2.9.9     # PostgreSQL adapter
redis==5.0.1                # Redis client
python-dotenv==1.0.0       # .env file support
```

---

## 📊 分阶段交付计划

### Phase 2.1: Infrastructure (THIS TASK)
- ✅ Docker Compose 配置
- ✅ Python 模块结构
- ✅ 配置管理系统
- ✅ 基础连接代码
- ✅ 验证脚本

### Phase 2.2: Schema & Migration (Task #033)
- Database schema definition
- TimescaleDB hypertable setup
- Index strategy
- Alembic migration framework

### Phase 2.3: Data Loaders (Task #034)
- EODHD API async loader
- Real-time tick consumer (ZMQ)
- Data cleaning & validation

### Phase 2.4: Feature Store (Task #035)
- Feature computation pipeline
- Feature caching in Redis
- Batch & online serving

---

## 🔄 依赖关系

**前置**:
- Task #001-#027: Complete (✅)
- Task #030: History Healing (✅)
- Task #031: Content Injection (✅)

**后续**:
- Task #033: EODHD Async Loader (depends on this)
- Task #034: Feature Engineering (depends on this)
- Task #035: Feature Store (depends on this)

---

## 🛡️ 成功标准

| 标准 | 验收条件 |
|------|--------|
| Docker Setup | `docker-compose up` 启动 TimescaleDB + Redis |
| Python Modules | 所有 imports 在 `from src.data_nexus` 下成功 |
| Config Loading | `.env` 文件正确加载到 config objects |
| DB Connection | PostgreSQL 连接字符串有效，SELECT 1 返回成功 |
| Redis Connection | Redis PING 命令返回 PONG |
| Verification Script | `python3 scripts/verify_data_infra.py` 返回 0 |

---

## 📝 技术选型说明

### 为什么 TimescaleDB?
- 基于 PostgreSQL，支持 SQL 和 JSON 混合
- Time-series 优化（hypertables）
- 内置时间索引和压缩
- 成熟的生产级支持

### 为什么 Redis?
- 极低延迟（毫秒级）
- 支持多种数据结构（strings, hashes, lists, sets)
- 内置过期策略（自动清理旧数据）
- 支持 Pub/Sub（future: 实时数据推送）

### 为什么分离而不是单数据库?
```
❌ 单数据库问题:
  - 高 TPS 下性能下降
  - 持久化 ≠ 缓存需求不同
  - 备份策略不同

✅ 分离好处:
  - 针对性优化
  - 独立扩展
  - 失败隔离
```

---

## 🚀 预期工作量

| 部分 | 时间 | 优先级 |
|------|------|--------|
| Docker Compose | 30 min | ⭐⭐⭐ |
| Python Modules | 1 hour | ⭐⭐⭐ |
| Config & .env | 15 min | ⭐⭐ |
| Verification | 30 min | ⭐⭐⭐ |
| **总计** | **~2.5 hours** | |

---

## 🎓 学习成果

完成此任务后，你将拥有：
1. Docker 容器编排经验
2. Python SQLAlchemy ORM 基础
3. Redis 客户端集成知识
4. 时间序列数据库设计思路
5. 可复现的开发环境

---

**Created**: 2025-12-28
**For Task**: #032
**Phase**: 2 (Data Intelligence)
**Protocol**: v2.6 (CLI --plan Integration)
