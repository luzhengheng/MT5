# Task #093.2 部署同步清单

**生产环境部署指南**

---

## 📦 新增依赖

无新增 Python 包依赖（使用现有 `numba`、`pandas`、`sqlalchemy`）

---

## 🗄️ 数据库变更

**表结构**: 无变更（复用 `market_candles`）

**新增数据**:
- `EURUSD.FOREX`: 1938 行 (2020-01-01 至 2026-01-11)

**验证命令**:
```sql
SELECT COUNT(*) FROM market_candles WHERE symbol='EURUSD.FOREX';
-- Expected: 1938
```

---

## 🔐 环境变量

确保以下环境变量已配置：

```bash
EODHD_API_TOKEN=<your_token>  # Forex 数据访问
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=mt5_db
TIMESCALE_USER=mt5_user
TIMESCALE_PASSWORD=<password>
```

---

## 📁 新增文件

### 生产代码
- `src/data_loader/forex_loader.py`
- `src/feature_engineering/jit_operators.py`

### 测试代码
- `tests/test_jit_performance.py`

### 脚本工具
- `scripts/task_093_2_cross_asset_analysis.py`

---

## ⚙️ 配置变更

**无需配置变更**

---

## 🔄 数据迁移

**步骤 1**: 注入外汇数据
```bash
python3 src/data_loader/forex_loader.py --symbol EURUSD.FOREX --from 2020-01-01
```

**步骤 2**: 验证数据
```bash
python3 -c "
from src.database.timescale_client import TimescaleClient
import pandas as pd

client = TimescaleClient()
df = pd.read_sql(
    \"SELECT COUNT(*) FROM market_candles WHERE symbol='EURUSD.FOREX'\",
    client.engine
)
print(f'EURUSD rows: {df.iloc[0,0]}')
"
```

---

## 🚨 回滚计划

如需回滚，执行：
```sql
DELETE FROM market_candles WHERE symbol='EURUSD.FOREX';
```

代码回滚：
```bash
git revert HEAD
```

---

## ✅ 部署检查清单

- [ ] TimescaleDB 容器运行正常
- [ ] EODHD API Token 已配置
- [ ] EURUSD 数据已注入
- [ ] JIT 测试通过（5/5）
- [ ] 跨资产分析脚本可运行

---

**协议**: v4.3 Zero-Trust Edition

**部署负责人**: DevOps / SRE Team

**生成时间**: 2026-01-12
