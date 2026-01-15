# Task #111 快速启动指南
## EODHD 历史数据连接器与标准化管道

---

## 快速使用

### 1. 准备环境

```bash
# 安装依赖
pip install pandas pyarrow fastparquet requests polars

# 设置 EODHD API Token
export EODHD_TOKEN="your_token_here"
```

### 2. 运行 ETL 管道

#### 方式 A: 使用 EODHD 实时数据（需要 Token）
```bash
python3 scripts/data/run_etl_pipeline.py --symbol EURUSD --fetch-new
```

#### 方式 B: 使用现有 CSV 数据（演示模式）
```bash
python3 scripts/data/demo_etl_pipeline.py
```

#### 方式 C: 运行单元测试
```bash
python3 scripts/audit_task_111.py
```

### 3. 查看输出

```bash
# 列出标准化文件
ls -lh data_lake/standardized/

# 验证 UTC 时间戳
python3 -c "
import pandas as pd
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')
print(df[['timestamp', 'close']].head())
"
```

---

## 工作流程

### 隔离损坏文件

```bash
python3 scripts/data/quarantine_corrupted_files.py
```

**输出**:
- 将 14 个损坏文件移动到 `data/quarantine/`
- 生成 `QUARANTINE_REPORT.json`

### 标准化 CSV 文件

```python
from src.data.processors.standardizer import DataStandardizer

standardizer = DataStandardizer()

# 读取 CSV
df = standardizer.standardize_csv(
    "data/raw/EURUSD_d.csv",
    symbol="EURUSD",
    timeframe="D1"
)

# 保存为 Parquet
path = standardizer.save_standardized(df, "EURUSD", "D1")

# 验证输出
standardizer.verify_output(path)
```

### 获取 EODHD 数据

```python
from src.data.connectors.eodhd import EODHDClient
from src.data.processors.standardizer import DataStandardizer

# 初始化
client = EODHDClient(token="your_token")
standardizer = DataStandardizer()

# 获取分钟线数据
data = client.fetch_intraday_data(
    "EURUSD.FOREX",
    interval=1,    # 1 分钟
    days_back=30   # 最近 30 天
)

# 标准化
df = standardizer.standardize_eodhd_json(
    data,
    symbol="EURUSD",
    timeframe="M1"
)

# 保存
path = standardizer.save_standardized(df, "EURUSD", "M1")
```

---

## 常见问题

### Q1: 如何获取 EODHD Token?
A: 访问 https://eodhd.com/ 注册账户，在 API 设置中获取 Token。

### Q2: 没有 Token 能用吗?
A: 可以，使用 `demo_etl_pipeline.py` 处理现有 CSV 文件。

### Q3: 如何添加新的交易品种?
A: 在 EODHD 中查询品种代码（如 `GBPUSD.FOREX`），然后运行：
```bash
python3 scripts/data/run_etl_pipeline.py --symbol GBPUSD --fetch-new
```

### Q4: 输出文件在哪里?
A: `data_lake/standardized/` 目录下，格式为 `{SYMBOL}_{TIMEFRAME}.parquet`

### Q5: 如何验证数据质量?
A: 运行验证脚本：
```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')
print(f'Rows: {len(df)}')
print(f'Timestamp range: {df[\"timestamp\"].min()} ~ {df[\"timestamp\"].max()}')
print(f'Data types: {df.dtypes}')
"
```

---

## 架构图

```
EODHD API 或 CSV 文件
        ↓
  EODHDClient / StandardCSV
        ↓
  DataStandardizer (规范化)
        ↓
 Column Mapping (列名映射)
        ↓
 Timestamp Normalization (UTC)
        ↓
 Data Cleaning (去重、去 NaN)
        ↓
 Parquet Save (Snappy 压缩)
        ↓
 Verification (验证输出)
        ↓
data_lake/standardized/
  ├── EURUSD_M1.parquet
  ├── EURUSD_D1.parquet
  ├── AUDUSD_D1.parquet
  └── ...
```

---

## 标准 Schema 参考

所有输出文件都遵循此 Schema：

| 列名 | 类型 | 说明 |
| --- | --- | --- |
| timestamp | datetime64[ns] | UTC 时间戳 |
| open | float64 | 开盘价 |
| high | float64 | 最高价 |
| low | float64 | 最低价 |
| close | float64 | 收盘价 |
| volume | float64 | 成交量 |

**示例**:
```
timestamp                 open     high      low    close   volume
2002-05-06 00:00:00  1.1295  1.1379  1.1290  1.1378  1000000
2002-05-07 00:00:00  1.1378  1.1485  1.1378  1.1485  1000000
2002-05-08 00:00:00  1.1485  1.1625  1.1485  1.1624  1000000
```

---

## 性能指标

| 指标 | 数值 |
| --- | --- |
| CSV 标准化速度 | ~50,000 rows/秒 |
| Parquet 读取速度 | ~1,000,000 rows/秒 |
| 压缩率 | 30-40% (Snappy) |
| 内存占用 | ~100MB (百万行) |

---

## 故障排除

### 问题: "EODHD_TOKEN not found"
**解决**:
```bash
export EODHD_TOKEN="your_token_here"
python3 scripts/data/run_etl_pipeline.py ...
```

### 问题: "No such file or directory"
**解决**:
```bash
mkdir -p data_lake/standardized/
# 然后重新运行
```

### 问题: "Invalid timestamp format"
**解决**:
检查 CSV 中的日期格式，确保为 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`

### 问题: "Unable to import polars"
**解决**:
```bash
pip install polars
```

---

## 测试覆盖

运行完整的单元测试套件（12 个测试）：

```bash
python3 scripts/audit_task_111.py
```

**输出示例**:
```
============================== test session starts ==============================
...
scripts/audit_task_111.py::TestEODHDConnector::test_eodhd_client_init PASSED
scripts/audit_task_111.py::TestDataStandardizer::test_standardizer_init PASSED
...
============================== 12 passed in 0.60s ==============================
```

---

## 更多信息

- **源代码**: `src/data/connectors/eodhd.py`, `src/data/processors/standardizer.py`
- **管道脚本**: `scripts/data/run_etl_pipeline.py`
- **测试脚本**: `scripts/audit_task_111.py`
- **完成报告**: `docs/archive/tasks/TASK_111_DATA_ETL/COMPLETION_REPORT.md`

---

**Last Updated**: 2026-01-15
**Protocol**: v4.3 (Zero-Trust Edition)
