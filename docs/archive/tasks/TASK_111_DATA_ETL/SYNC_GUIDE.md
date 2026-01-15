# Task #111 部署变更清单 (SYNC_GUIDE)
## EODHD 历史数据连接器与标准化管道

---

## 1. 代码变更 (Code Changes)

### 新增文件

```
src/data/
├── connectors/
│   ├── __init__.py              (NEW)
│   └── eodhd.py                 (NEW) - EODHD API 客户端
└── processors/
    ├── __init__.py              (NEW)
    └── standardizer.py          (NEW) - 数据标准化处理器

scripts/data/
├── run_etl_pipeline.py          (NEW) - ETL 管道主脚本
├── demo_etl_pipeline.py         (NEW) - 演示脚本
└── quarantine_corrupted_files.py (NEW) - 隔离脚本

scripts/
├── audit_task_111.py            (NEW) - TDD 审计脚本
└── gate2_task_111_review.py     (NEW) - Gate 2 审查脚本

docs/archive/tasks/TASK_111_DATA_ETL/
├── COMPLETION_REPORT.md         (NEW) - 完成报告
├── QUICK_START.md               (NEW) - 快速启动指南
├── SYNC_GUIDE.md                (NEW) - 本文件
└── GATE2_TASK_111_REVIEW.json   (NEW) - Gate 2 审查结果
```

### 文件统计

| 类型 | 数量 | 代码行数 |
| --- | --- | --- |
| Python 模块 | 5 | 1,320 |
| 测试脚本 | 2 | 386 |
| 文档 | 4 | 400+ |
| 总计 | 11 | 2,100+ |

---

## 2. 依赖包 (Dependencies)

### 新增依赖

```
pandas>=1.3.0          # 数据处理
pyarrow>=8.0.0         # Parquet 文件格式
fastparquet>=0.8.0     # Parquet 快速读写
requests>=2.28.0       # HTTP 请求
polars>=0.17.0         # 高性能数据处理（可选）
```

### 安装命令

```bash
pip install pandas pyarrow fastparquet requests polars
```

### 版本检查

```bash
python3 -c "
import pandas; import pyarrow; import requests
print(f'pandas: {pandas.__version__}')
print(f'pyarrow: {pyarrow.__version__}')
print(f'requests: {requests.__version__}')
"
```

---

## 3. 环境变量 (Environment Variables)

### 新增环境变量

| 变量名 | 必需 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `EODHD_TOKEN` | 否 | 无 | EODHD API 认证令牌 |

### 配置方式

```bash
# 方式 1: 命令行
export EODHD_TOKEN="your_token_here"

# 方式 2: .env 文件
echo "EODHD_TOKEN=your_token_here" >> .env
source .env

# 方式 3: Python 脚本中
import os
os.environ["EODHD_TOKEN"] = "your_token_here"
```

---

## 4. 数据库变更 (Database Changes)

### 无数据库变更

- ✅ 不需要修改 TimescaleDB
- ✅ 不需要修改 ChromaDB
- ✅ 不需要修改任何现有表

### 文件系统变更

```bash
# 新增目录
mkdir -p data/quarantine            # 损坏文件隔离区
mkdir -p data_lake/standardized     # 标准化数据输出
```

---

## 5. 配置变更 (Configuration Changes)

### 无配置文件变更

- ✅ 不修改任何 YAML 配置
- ✅ 不修改 src/mt5_bridge/config.py
- ✅ 不修改 .env 文件

### 新增配置（可选）

如需完全控制管道，可创建 `config/etl_pipeline.yaml`:

```yaml
# ETL Pipeline Configuration
eodhd:
  enabled: true
  api_endpoint: "https://eodhd.com/api"
  # token: 从环境变量读取

standardizer:
  output_dir: "data_lake/standardized"
  compression: "snappy"
  chunk_size: 100000  # 内存优化

data_lake:
  quarantine_dir: "data/quarantine"
  archive_dir: "data/_archive"
```

---

## 6. 权限变更 (Permissions)

### 文件权限

```bash
# 确保脚本可执行
chmod +x scripts/data/run_etl_pipeline.py
chmod +x scripts/audit_task_111.py
chmod +x scripts/gate2_task_111_review.py

# 确保目录可写
chmod 755 data/quarantine
chmod 755 data_lake/standardized
```

### 进程权限

- ✅ 不需要 root 权限
- ✅ 不需要特殊用户
- ✅ 使用标准用户即可运行

---

## 7. 日志变更 (Logging Changes)

### 新增日志文件

| 文件 | 位置 | 用途 |
| --- | --- | --- |
| `VERIFY_LOG.log` | 项目根目录 | 执行日志 + 物理验尸证据 |
| `AUDIT_TASK_111.log` | 项目根目录 | 单元测试报告 |
| `GATE2_TASK_111_REVIEW.json` | 项目根目录 | Gate 2 审查结果 |

### 日志配置

```python
# 在主脚本中已配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('VERIFY_LOG.log', mode='a'),
        logging.StreamHandler()
    ]
)
```

---

## 8. 验证清单 (Verification Checklist)

### 部署前检查

- [ ] Python 3.9+ 可用
- [ ] 依赖包已安装: `pip list | grep -E "pandas|pyarrow|requests"`
- [ ] 目录结构完整: `test -d src/data/connectors && echo OK`
- [ ] 脚本可执行: `test -x scripts/data/run_etl_pipeline.py && echo OK`

### 部署后检查

- [ ] 运行单元测试: `python3 scripts/audit_task_111.py`
- [ ] 验证隔离脚本: `python3 scripts/data/quarantine_corrupted_files.py`
- [ ] 测试演示管道: `python3 scripts/data/demo_etl_pipeline.py`
- [ ] 检查输出文件: `ls -l data_lake/standardized/`

### 生产检查

- [ ] Gate 1 测试全部通过 (12/12)
- [ ] Gate 2 审查通过 (10.0/10 质量分)
- [ ] 物理验尸完整 (Session ID + Timestamp 有效)
- [ ] 归档文档完整 (4 文档)

---

## 9. 回滚计划 (Rollback Plan)

### 如何回滚

```bash
# 1. 删除新增文件
rm -rf src/data/connectors
rm -rf src/data/processors
rm scripts/data/run_etl_pipeline.py
rm scripts/data/demo_etl_pipeline.py
rm scripts/data/quarantine_corrupted_files.py
rm scripts/audit_task_111.py

# 2. 删除生成的数据
rm -rf data_lake/standardized
rm -f QUARANTINE_REPORT.json
rm -f VERIFY_LOG.log
rm -f GATE2_TASK_111_REVIEW.json

# 3. 恢复隔离的文件（如需要）
# 使用之前的备份或 git 恢复
```

### 回滚条件

- ✅ 如果生产 Gate 2 审查失败
- ✅ 如果数据质量不符合预期
- ✅ 如果与其他系统集成出现问题

---

## 10. 生产部署步骤 (Production Deployment)

### 第 1 步: 预检查
```bash
python3 scripts/audit_task_111.py
# 确保所有 12 个测试通过
```

### 第 2 步: 隔离损坏文件
```bash
python3 scripts/data/quarantine_corrupted_files.py
# 确保 14 个文件成功隔离
```

### 第 3 步: 运行演示管道
```bash
python3 scripts/data/demo_etl_pipeline.py
# 确保可以处理现有 CSV 文件
```

### 第 4 步: 准备 EODHD Token（可选）
```bash
export EODHD_TOKEN="your_production_token"
```

### 第 5 步: 运行完整管道
```bash
python3 scripts/data/run_etl_pipeline.py --symbol EURUSD --fetch-new
```

### 第 6 步: 验证输出
```bash
ls -lh data_lake/standardized/
python3 -c "import pandas as pd; df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet'); print(f'Rows: {len(df)}, Timestamp range: {df[\"timestamp\"].min()} ~ {df[\"timestamp\"].max()}')"
```

### 第 7 步: 提交变更
```bash
git add .
git commit -m "feat(task-111): EODHD Data ETL Pipeline Implementation"
git push origin main
```

---

## 11. 监控指标 (Monitoring Metrics)

### 关键指标

| 指标 | 目标 | 告警阈值 |
| --- | --- | --- |
| 处理速度 | >50,000 rows/sec | <10,000 rows/sec |
| 成功率 | 100% | <95% |
| 磁盘占用 | <5GB | >10GB |
| 内存占用 | <500MB | >1GB |

### 监控命令

```bash
# 检查处理速度
python3 -c "
import time, pandas as pd
start = time.time()
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')
elapsed = time.time() - start
print(f'Read {len(df)} rows in {elapsed:.2f}s = {len(df)/elapsed:.0f} rows/s')
"

# 检查磁盘占用
du -sh data_lake/standardized/

# 检查内存占用
ps aux | grep run_etl_pipeline.py
```

---

## 12. 常见问题与解决方案 (FAQ)

### Q: 如何跳过已处理的文件？
A: 使用 `--no-fetch` 标志仅使用本地数据：
```bash
python3 scripts/data/run_etl_pipeline.py --symbol EURUSD --no-fetch
```

### Q: 如何处理新的交易品种？
A: 在脚本中添加新符号：
```python
pipeline.process_eodhd_m1_data("GBPUSD.FOREX")
pipeline.process_eodhd_d1_data("GBPUSD")
```

### Q: 如何修改输出目录？
A: 修改初始化参数：
```python
standardizer = DataStandardizer(output_dir="custom/path/")
```

### Q: 如何调整时区处理？
A: 修改 standardizer.py 中的 `_normalize_timestamp` 方法。

---

## 13. 相关文档 (References)

- **完成报告**: COMPLETION_REPORT.md
- **快速启动**: QUICK_START.md
- **源代码**: `src/data/connectors/eodhd.py`, `src/data/processors/standardizer.py`
- **测试脚本**: `scripts/audit_task_111.py`

---

## 14. 交接信息 (Handoff)

### 负责人
- **开发**: MT5-CRS Development Team
- **审查**: Gate 2 AI Review (Session: 4365a170873a6b1e)
- **部署**: DevOps Team

### 联系方式
- 代码问题: 查看源代码注释
- 数据问题: 检查 VERIFY_LOG.log
- 配置问题: 参考 SYNC_GUIDE.md

---

**更新时间**: 2026-01-15 21:57:48 UTC
**Protocol**: v4.3 (Zero-Trust Edition)
