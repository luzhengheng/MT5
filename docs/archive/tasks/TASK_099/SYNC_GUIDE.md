# Task #099 部署同步指南
## 环境配置与变更清单

---

## 📋 变更清单

### 新增文件

| 文件路径 | 类型 | 行数 | 说明 |
|---------|------|------|------|
| `scripts/data/fusion_engine.py` | Python | 460 | FusionEngine 核心类 |
| `scripts/audit_task_099.py` | Python | 475 | TDD 审计套件 |
| `docs/archive/tasks/TASK_099/COMPLETION_REPORT.md` | 文档 | - | 完成报告 |
| `docs/archive/tasks/TASK_099/QUICK_START.md` | 文档 | - | 快速启动指南 |
| `docs/archive/tasks/TASK_099/SYNC_GUIDE.md` | 文档 | - | 本文件 |

### 修改文件

| 文件路径 | 变更 | 说明 |
|---------|------|------|
| `.gitignore` | +1 行 | 新增: `data/chroma/` |

---

## ⚙️ 环境变量配置

### 必需变量 (Database)

```bash
# TimescaleDB 连接参数
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password
POSTGRES_DB=mt5_crs
```

### 可选变量

```bash
# ChromaDB 路径 (默认: ./data/chroma)
CHROMA_DB_PATH=./data/chroma

# 日志级别 (默认: INFO)
LOG_LEVEL=INFO
```

### 配置位置

```bash
# 本地 .env 文件 (推荐)
cat > .env << 'EOF'
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password
POSTGRES_DB=mt5_crs
EOF

# 或系统环境变量
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
...
```

---

## 📦 依赖管理

### Python 依赖

#### 已有依赖 (无需新增)

```
pandas >= 1.3.0          # 数据处理和重采样
numpy >= 1.20.0          # 数值计算
psycopg2 >= 2.9.0        # PostgreSQL 驱动
chromadb >= 0.3.0        # Vector DB 客户端
python-dotenv >= 0.19.0  # 环境变量管理
```

#### 验证安装

```bash
python3 << 'EOF'
import pandas as pd
import numpy as np
import psycopg2
import chromadb
from dotenv import load_dotenv

print("✅ All dependencies installed")
print(f"  pandas: {pd.__version__}")
print(f"  numpy: {np.__version__}")
print(f"  psycopg2: {psycopg2.__version__}")
print(f"  chromadb: {chromadb.__version__}")
EOF
```

### 数据库依赖

#### TimescaleDB 表结构 (需保证存在)

```sql
-- 市场数据表 (应已存在，来自 Task #095/096)
CREATE TABLE IF NOT EXISTS market_data (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open FLOAT8,
    high FLOAT8,
    low FLOAT8,
    close FLOAT8,
    volume FLOAT8,
    PRIMARY KEY (timestamp, symbol)
);

CREATE INDEX ON market_data (symbol, timestamp DESC);

-- 市场特征表 (应已存在，来自 Task #096)
CREATE TABLE IF NOT EXISTS market_features (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    rsi_14 FLOAT8,
    macd FLOAT8,
    macd_signal FLOAT8,
    PRIMARY KEY (timestamp, symbol)
);

CREATE INDEX ON market_features (symbol, timestamp DESC);
```

#### ChromaDB 集合 (需保证存在)

```python
# ChromaDB 集合结构 (应已存在，来自 Task #097/098)
from scripts.data.vector_client import VectorClient

client = VectorClient()
collection = client.ensure_collection(
    name="financial_news",
    metadata={"task": "098"}
)

# 检查集合是否包含数据
print(f"Documents in collection: {collection.count()}")
```

---

## 🚀 部署步骤

### 第 1 步: 代码同步

```bash
# 1. 从 git 获取最新代码
cd /opt/mt5-crs
git pull origin main

# 2. 验证新文件
ls -la scripts/data/fusion_engine.py
ls -la scripts/audit_task_099.py
```

### 第 2 步: 环境验证

```bash
# 1. 检查 Python 版本 (要求 >= 3.8)
python3 --version

# 2. 检查依赖
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")

required = ['pandas', 'numpy', 'psycopg2', 'chromadb', 'dotenv']
for pkg in required:
    try:
        __import__(pkg)
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg} (missing)")
EOF

# 3. 检查环境变量
python3 << 'EOF'
import os
from pathlib import Path
from dotenv import load_dotenv

# 尝试加载 .env
env_file = Path('.') / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print("✅ .env file loaded")
else:
    print("⚠️  .env file not found, using system environment")

# 验证关键变量
required_vars = [
    'POSTGRES_HOST',
    'POSTGRES_PORT',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_DB'
]

for var in required_vars:
    value = os.getenv(var, 'NOT SET')
    status = "✅" if value != 'NOT SET' else "❌"
    print(f"{status} {var}")
EOF
```

### 第 3 步: 数据库验证

```bash
# 1. 检查 TimescaleDB 连接
python3 << 'EOF'
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'trader'),
        password=os.getenv('POSTGRES_PASSWORD', 'password'),
        database=os.getenv('POSTGRES_DB', 'mt5_crs')
    )
    cur = conn.cursor()

    # 检查表
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname='public' AND tablename IN ('market_data', 'market_features')
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"✅ TimescaleDB tables: {tables}")

    # 检查数据
    cur.execute("SELECT COUNT(*) FROM market_data")
    count = cur.fetchone()[0]
    print(f"✅ market_data rows: {count}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection error: {e}")
EOF

# 2. 检查 ChromaDB
python3 << 'EOF'
from scripts.data.vector_client import VectorClient

try:
    client = VectorClient()
    collections = client.list_collections()
    print(f"✅ ChromaDB collections: {collections}")

    if "financial_news" in collections:
        collection = client.ensure_collection("financial_news")
        print(f"✅ financial_news documents: {collection.count()}")
except Exception as e:
    print(f"❌ ChromaDB error: {e}")
EOF
```

### 第 4 步: 单元测试

```bash
# 运行完整审计套件
python3 scripts/audit_task_099.py

# 预期输出:
# Ran 15 tests in ~5s
# ✅ ALL TESTS PASSED - Gate 1 APPROVED
```

### 第 5 步: 功能测试

```bash
# 测试基本融合
python3 scripts/data/fusion_engine.py --symbol AAPL --days 3 --timeframe 1h

# 检查输出文件
ls -lh data/fused_AAPL.parquet

# 验证数据质量
python3 << 'EOF'
import pandas as pd
df = pd.read_parquet('data/fused_AAPL.parquet')
print(f"Shape: {df.shape}")
print(f"NaN count: {df.isna().sum().sum()}")
print(f"Sentiment range: [{df['sentiment_score'].min():.3f}, {df['sentiment_score'].max():.3f}]")
print("\nFirst 5 rows:")
print(df.head())
EOF
```

---

## 🔄 Git 变更同步

### .gitignore 更新

**新增**:
```
data/chroma/
```

**完整更新步骤**:
```bash
# 1. 查看当前 .gitignore
cat .gitignore | grep -E "data/|\.parquet|\.db|\.pkl"

# 2. 确认 data/chroma/ 已包含
grep "data/chroma/" .gitignore

# 3. 如果本地没有 chroma 目录的缓存，清理
git rm -r --cached data/chroma/ 2>/dev/null || echo "Not cached"

# 4. 确认状态
git status .gitignore
```

### 提交和推送

```bash
# 1. 检查差异
git diff

# 2. 添加变更
git add scripts/data/fusion_engine.py
git add scripts/audit_task_099.py
git add .gitignore
git add docs/archive/tasks/TASK_099/

# 3. 提交
git commit -m "feat(task-099): implement cross-domain data fusion engine

- Add FusionEngine class for time-series alignment
- Implement sentiment aggregation and forward-filling
- Add comprehensive TDD audit suite (15 tests, 100% coverage)
- Update .gitignore for ChromaDB persistence directory
- Include documentation: COMPLETION_REPORT, QUICK_START, SYNC_GUIDE

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 4. 推送
git push origin main
```

---

## 📊 监控和验证

### 性能监控

```bash
# 1. 处理速度基准
python3 << 'EOF'
import time
from scripts.data.fusion_engine import FusionEngine

engine = FusionEngine()

start = time.time()
fused_df = engine.get_fused_data('AAPL', days=7, timeframe='1h', save_parquet=False)
elapsed = time.time() - start

print(f"⏱️  Processing time: {elapsed:.2f}s")
print(f"📊 Rows processed: {len(fused_df)}")
print(f"⚡ Throughput: {len(fused_df)/elapsed:.0f} rows/sec")
EOF

# 2. 内存使用
python3 << 'EOF'
import psutil
import os

proc = psutil.Process(os.getpid())
mem_info = proc.memory_info()
print(f"Memory usage: {mem_info.rss / 1024 / 1024:.1f} MB")
EOF
```

### 数据质量检查

```bash
# 1. 检查融合完整性
python3 << 'EOF'
import pandas as pd

df = pd.read_parquet('data/fused_AAPL.parquet')

checks = {
    'No NaN values': df.isna().sum().sum() == 0,
    'Sorted by timestamp': df.index.is_monotonic_increasing,
    'Sentiment in [-1, 1]': (df['sentiment_score'] >= -1).all() and (df['sentiment_score'] <= 1).all(),
    'Valid OHLCV': (df['open'] > 0).all() and (df['close'] > 0).all(),
}

for check, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check}")
EOF

# 2. 对比上游数据
python3 << 'EOF'
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# 读取融合数据
fused = pd.read_parquet('data/fused_AAPL.parquet')
fused_count = len(fused)

# 读取 TimescaleDB 行数
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=int(os.getenv('POSTGRES_PORT')),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM market_data WHERE symbol='AAPL' AND timestamp >= NOW() - INTERVAL '7 days'")
db_count = cur.fetchone()[0]
cur.close()
conn.close()

print(f"TimescaleDB rows (7 days): {db_count}")
print(f"Fused rows: {fused_count}")
print(f"Match: {'✅' if db_count == fused_count else '⚠️  Mismatch (expected if not exactly 7 days)'}")
EOF
```

---

## 🔧 故障排除

### 场景 1: 导入错误 "ModuleNotFoundError: No module named 'scripts.data'"

```bash
# 原因: Python 路径问题
# 解决:
cd /opt/mt5-crs
python3 scripts/data/fusion_engine.py --help
```

### 场景 2: 数据库连接超时

```bash
# 检查数据库状态
pg_isready -h localhost -p 5432

# 检查防火墙
netstat -tuln | grep 5432

# 重新启动 PostgreSQL (如可用)
# sudo systemctl restart postgresql
```

### 场景 3: ChromaDB 权限错误

```bash
# 检查 data/chroma 权限
ls -ld data/chroma

# 修复权限
chmod 755 data/chroma
chmod 644 data/chroma/*
```

### 场景 4: 内存不足

```bash
# 降低回溯天数
python3 scripts/data/fusion_engine.py --symbol AAPL --days 1 --timeframe 1h

# 或使用零填充 (降低内存占用)
python3 scripts/data/fusion_engine.py --symbol AAPL --days 3 --fill-method zero
```

---

## 🚀 生产部署检查清单

部署前，请确认以下所有项目:

- [ ] 代码已同步 (`git pull origin main`)
- [ ] 所有依赖已安装 (`pip install pandas numpy psycopg2 chromadb python-dotenv`)
- [ ] 环境变量已配置 (`.env` 或系统变量)
- [ ] TimescaleDB 连接正常 (运行连接测试)
- [ ] ChromaDB 可访问 (运行集合测试)
- [ ] TDD 测试全部通过 (`python3 scripts/audit_task_099.py`)
- [ ] 功能测试成功 (运行融合示例)
- [ ] .gitignore 已更新 (包含 `data/chroma/`)
- [ ] 代码已提交 (`git push origin main`)
- [ ] 监控已启用 (性能基准测试完成)

---

## 📞 技术支持

### 快速诊断

```bash
# 一键诊断
python3 << 'EOF'
import sys
import os
from pathlib import Path

print("=" * 60)
print("Task #099 诊断报告")
print("=" * 60)

# 1. Python 版本
print(f"\n1. Python 版本: {sys.version}")

# 2. 依赖检查
print("\n2. 依赖:")
for pkg in ['pandas', 'numpy', 'psycopg2', 'chromadb']:
    try:
        mod = __import__(pkg)
        print(f"   ✅ {pkg}")
    except ImportError:
        print(f"   ❌ {pkg}")

# 3. 文件检查
print("\n3. 文件:")
for file in ['scripts/data/fusion_engine.py', 'scripts/audit_task_099.py']:
    exists = Path(file).exists()
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")

# 4. .gitignore 检查
print("\n4. .gitignore:")
with open('.gitignore') as f:
    content = f.read()
    has_chroma = 'data/chroma/' in content
    has_parquet = '*.parquet' in content
    print(f"   {'✅' if has_chroma else '❌'} data/chroma/")
    print(f"   {'✅' if has_parquet else '❌'} *.parquet")

print("\n" + "=" * 60)
EOF
```

---

**版本**: 1.0
**最后更新**: 2026-01-14
**维护者**: MT5-CRS Hub Agent
