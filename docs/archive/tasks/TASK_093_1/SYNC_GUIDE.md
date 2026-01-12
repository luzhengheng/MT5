# Task #093.1 同步部署指南

> 📦 **部署变更清单与环境配置说明**

---

## 1. Git 同步信息

### 1.1 提交详情

| 项目 | 值 |
|------|---|
| **Commit Hash** | `7bd84ee` |
| **Commit Message** | `docs: generate AI context package 20260112 for WO #011 MT5 integration review` |
| **分支** | `main` |
| **远程仓库** | `https://github.com/luzhengheng/MT5.git` |
| **推送时间** | 2026-01-12 14:56 CST |

### 1.2 变更文件清单

#### 新增文件 (A)

```
docs/archive/tasks/TASK_093_1/optimal_d_result.json
docs/archive/tasks/.gitignore
notebooks/task_093_1_feature_engineering.ipynb
scripts/read_task_context.py
scripts/task_093_1_feature_builder.py
src/feature_engineering/advanced_feature_builder.py
exports/AI_PROMPT_20260112_010336.md
exports/CONTEXT_SUMMARY_20260112_010336.md
... (更多 exports 文件)
```

#### 修改文件 (M)

```
src/data_loader/eodhd_timescale_loader.py
exports/README.md
```

#### 未提交文件 (本地保留)

```
docs/archive/tasks/TASK_093_1/aapl_features_simple.csv  (已添加到 .gitignore)
docs/archive/tasks/TASK_093_1/COMPLETION_REPORT.md      (待下次提交)
docs/archive/tasks/TASK_093_1/QUICK_START.md            (待下次提交)
docs/archive/tasks/TASK_093_1/SYNC_GUIDE.md             (本文档)
VERIFY_LOG.log                                           (临时日志)
```

---

## 2. 环境变量配置

### 2.1 必需的环境变量

任务#093.1 依赖以下环境变量，请确保在部署目标环境中正确配置：

#### 数据库配置

```bash
# PostgreSQL/TimescaleDB 连接
DB_URL=postgresql://trader:password@localhost:5432/mt5_crs
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password
POSTGRES_DB=mt5_crs
```

#### 数据源 API

```bash
# EODHD (历史数据提供商)
EODHD_API_TOKEN=your_api_token_here  # ⚠️ 已修复: 从 EODHD_API_KEY 改为 EODHD_API_TOKEN
```

### 2.2 配置变更说明

**重要**: `src/data_loader/eodhd_timescale_loader.py` 中的 API key 读取已从 `EODHD_API_KEY` 更改为 `EODHD_API_TOKEN`。

**影响**:
- 旧版本使用 `os.getenv("EODHD_API_KEY", "demo")`
- 新版本使用 `os.getenv("EODHD_API_TOKEN", "demo")`

**部署检查清单**:
- [ ] 确认 `.env` 文件中有 `EODHD_API_TOKEN` 变量
- [ ] 如果使用旧的 `EODHD_API_KEY`，需重命名或添加新变量

---

## 3. 依赖包更新

### 3.1 Python 包

任务#093.1 使用了以下新的或更新的 Python 包：

| 包名 | 版本 | 用途 | 安装状态 |
|------|------|------|----------|
| `statsmodels` | 已安装 | ADF 平稳性测试 | ✅ 已有 |
| `numba` | 已安装 | JIT 编译加速 (可选) | ✅ 已有 |
| `pandas` | 已安装 | 数据处理 | ✅ 已有 |
| `numpy` | 已安装 | 数值计算 | ✅ 已有 |
| `sqlalchemy` | 已安装 | 数据库 ORM | ✅ 已有 |
| `psycopg2` | 已安装 | PostgreSQL 驱动 | ✅ 已有 |
| `requests` | 已安装 | HTTP 请求 | ✅ 已有 |

**无需安装新包**，所有依赖已在现有 `requirements.txt` 中。

### 3.2 验证依赖

```bash
# 验证关键包是否已安装
python3 -c "import statsmodels; import numba; print('✅ All dependencies OK')"
```

---

## 4. 数据库变更

### 4.1 新表结构

任务#093.1 使用 `market_candles` 表（由 `eodhd_timescale_loader.py` 自动创建）:

```sql
CREATE TABLE IF NOT EXISTS market_candles (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    period TEXT DEFAULT 'd',
    UNIQUE (time, symbol, period)
);

-- 转换为 Hypertable (TimescaleDB)
SELECT create_hypertable('market_candles', 'time', if_not_exists => TRUE);
```

### 4.2 数据迁移

**自动迁移**: 表结构会在首次运行 `eodhd_timescale_loader.py` 时自动创建。

**数据填充**:
```bash
# 加载 AAPL 和 TSLA 数据
python3 src/data_loader/eodhd_timescale_loader.py
```

**验证数据**:
```sql
-- 连接数据库后执行
SELECT symbol, COUNT(*) as count
FROM market_candles
GROUP BY symbol;

-- 预期输出:
-- AAPL.US | 11361
-- TSLA.US | 3908
```

---

## 5. 文件系统变更

### 5.1 新增目录

```
docs/archive/tasks/TASK_093_1/     # 任务归档目录
notebooks/                         # Jupyter notebooks 目录
```

### 5.2 .gitignore 更新

新增规则:
```
# docs/archive/tasks/.gitignore
*.csv
```

**原因**: 防止大型 CSV 数据文件被提交到 Git 仓库。

---

## 6. Docker 服务依赖

### 6.1 必需的 Docker 容器

| 容器名 | 镜像 | 端口映射 | 状态要求 |
|--------|------|----------|----------|
| `timescaledb` | `timescale/timescaledb:latest-pg14` | `5432:5432` | Running |

### 6.2 启动检查

```bash
# 检查容器状态
docker ps | grep timescaledb

# 如果未运行，启动容器
docker start timescaledb

# 等待数据库就绪
sleep 5
```

---

## 7. 部署步骤

### 7.1 INF 节点 (推理服务器) 部署

#### 步骤 1: 拉取代码

```bash
cd /opt/mt5-crs
git pull origin main
```

#### 步骤 2: 验证环境变量

```bash
# 检查关键环境变量
grep -E "DB_URL|EODHD_API_TOKEN" .env
```

#### 步骤 3: 启动 TimescaleDB

```bash
docker start timescaledb
sleep 5
```

#### 步骤 4: 加载数据 (首次部署)

```bash
python3 src/data_loader/eodhd_timescale_loader.py
```

#### 步骤 5: 验证功能

```bash
python3 scripts/task_093_1_feature_builder.py
```

**预期**: 应该输出最优 d 值结果并成功生成特征文件。

### 7.2 HUB 节点 (代码仓库) 部署

HUB 节点无需特殊操作，代码已通过 `git push` 同步。

**验证**:
```bash
# 在 HUB 节点执行
cd /path/to/mt5-crs
git log --oneline -1

# 应显示: 7bd84ee docs: generate AI context package...
```

### 7.3 GPU 节点 (训练服务器) 部署

GPU 节点**不受影响**，Task #093.1 仅涉及特征工程，不涉及模型训练。

---

## 8. 回滚方案

如果部署后出现问题，可按以下步骤回滚：

### 8.1 代码回滚

```bash
# 回滚到上一个提交
git log --oneline -5  # 查看提交历史
git reset --hard a575ae6  # 回滚到 Task #092 的提交

# 强制推送 (谨慎操作)
# git push origin main --force
```

### 8.2 数据库回滚

```bash
# 如果需要删除 market_candles 表
docker exec -it timescaledb psql -U trader -d mt5_crs -c "DROP TABLE IF EXISTS market_candles CASCADE;"
```

### 8.3 环境变量回滚

```bash
# 如果改回旧的 API key 名称
sed -i 's/EODHD_API_TOKEN/EODHD_API_KEY/g' .env
```

---

## 9. 监控与验证

### 9.1 功能验证清单

部署后，请执行以下检查：

- [ ] TimescaleDB 容器正常运行
- [ ] 数据库中有 AAPL.US 和 TSLA.US 数据
- [ ] `scripts/task_093_1_feature_builder.py` 可成功运行
- [ ] 生成的 `optimal_d_result.json` 包含正确的结果
- [ ] Jupyter Notebook 可正常打开并执行

### 9.2 监控指标

**数据库连接**:
```bash
# 监控数据库连接数
docker exec timescaledb psql -U trader -d mt5_crs -c "SELECT count(*) FROM pg_stat_activity;"
```

**表大小**:
```bash
# 检查 market_candles 表大小
docker exec timescaledb psql -U trader -d mt5_crs -c "
SELECT
    pg_size_pretty(pg_total_relation_size('market_candles')) as total_size,
    count(*) as row_count
FROM market_candles;
"
```

---

## 10. 已知问题与限制

### 10.1 已知问题

| 问题 | 影响 | 状态 |
|------|------|------|
| Numba 类型推断错误 | 无法使用 JIT 加速 | ⚠️ 已规避 (使用纯 Python 实现) |
| CSV 文件未提交 | 部署后需重新生成 | ✅ 预期行为 (已添加到 .gitignore) |

### 10.2 性能限制

- **分数差分计算**: 纯 Python 实现，对于百万级数据可能较慢
- **建议**: 对于生产环境，考虑使用预计算并缓存结果

---

## 11. 联系方式

如有部署问题，请联系：

- **技术负责人**: MT5-CRS Team
- **问题追踪**: GitHub Issues
- **文档位置**: `docs/archive/tasks/TASK_093_1/`

---

**文档版本**: 1.0
**最后更新**: 2026-01-12 14:56 CST
**协议版本**: v4.3 (Zero-Trust Edition)
