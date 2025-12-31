# Task #012.05: 多资产批量摄取实施计划

**任务编号**: #071
**协议版本**: v2.2 (Docs-as-Code)
**角色**: 数据工程师
**创建日期**: 2025-12-31
**状态**: 进行中

---

## 1. 任务目标

在 Task #012.04 试点运行（EURUSD）成功的基础上，扩展批量摄取管道以支持 7 个战略资产的完整历史数据摄取（1990-2025）。

### 1.1 资产范围

| 资产类别 | 符号 | 交易所 | 数据起始日期 | 预期行数 |
|---------|------|--------|-------------|---------|
| 外汇主要货币对 | EURUSD | FOREX | 1990-01-01 | ~8,000 |
| 外汇主要货币对 | GBPUSD | FOREX | 1990-01-01 | ~8,000 |
| 外汇主要货币对 | USDJPY | FOREX | 1990-01-01 | ~8,000 |
| 外汇主要货币对 | AUDUSD | FOREX | 1990-01-01 | ~8,000 |
| 贵金属（黄金） | XAUUSD | FOREX | 1990-01-01 | ~8,000 |
| 美股指数 | GSPC | INDX | 1990-01-01 | ~8,000 |
| 美股指数 | DJI | INDX | 1990-01-01 | ~8,000 |

**总预期行数**: 约 30,000 - 50,000 行

### 1.2 核心需求

1. **批量处理**: 循环处理所有资产，每个资产独立摄取
2. **错误隔离**: 单个资产失败不影响其他资产的处理
3. **速率控制**: 资产间间隔 1 秒，避免 API 速率限制
4. **日志记录**: 详细记录每个资产的摄取状态
5. **数据验证**: 确保所有资产数据正确插入数据库

---

## 2. 技术架构

### 2.1 组件关系

```
config/assets.yaml
      ↓
scripts/run_bulk_ingestion.py
      ↓
src/data_loader/eodhd_bulk_loader.py (复用 Task #012.04)
      ↓
src/data_loader/eodhd_fetcher.py (EODHD API)
      ↓
TimescaleDB (market_data_ohlcv 表)
```

### 2.2 配置文件结构 (config/assets.yaml)

```yaml
# 战略资产配置
# 用于批量历史数据摄取

assets:
  # 外汇主要货币对
  - symbol: EURUSD
    exchange: FOREX
    name: 欧元/美元
    from_date: "1990-01-01"

  - symbol: GBPUSD
    exchange: FOREX
    name: 英镑/美元
    from_date: "1990-01-01"

  - symbol: USDJPY
    exchange: FOREX
    name: 美元/日元
    from_date: "1990-01-01"

  - symbol: AUDUSD
    exchange: FOREX
    name: 澳元/美元
    from_date: "1990-01-01"

  # 贵金属
  - symbol: XAUUSD
    exchange: FOREX
    name: 黄金/美元
    from_date: "1990-01-01"

  # 美股指数
  - symbol: GSPC
    exchange: INDX
    name: 标普500指数
    from_date: "1990-01-01"

  - symbol: DJI
    exchange: INDX
    name: 道琼斯工业平均指数
    from_date: "1990-01-01"

# 摄取配置
ingestion:
  batch_size: 5000
  rate_limit_delay: 1.0  # 秒
  max_retries: 3
  retry_delay: 5.0  # 秒
```

### 2.3 交易所映射规则

| 资产符号 | EODHD 格式 | 交易所代码 | 备注 |
|---------|-----------|-----------|------|
| EURUSD  | EURUSD.FOREX | FOREX | 外汇 |
| GBPUSD  | GBPUSD.FOREX | FOREX | 外汇 |
| USDJPY  | USDJPY.FOREX | FOREX | 外汇 |
| AUDUSD  | AUDUSD.FOREX | FOREX | 外汇 |
| XAUUSD  | XAUUSD.FOREX | FOREX | 黄金（外汇市场） |
| GSPC    | GSPC.INDX    | INDX  | S&P 500 指数 |
| DJI     | DJI.INDX     | INDX  | 道琼斯指数 |

**关键决策**: XAUUSD 使用 `FOREX` 交易所，而非 `COMM`（大宗商品），因为 EODHD API 的黄金数据在外汇端点更完整。

---

## 3. 错误处理策略

### 3.1 三层防护机制

#### 第一层：资产级别隔离
```python
for asset in assets:
    try:
        # 摄取单个资产
        ingest_asset(asset)
    except Exception as e:
        # 记录错误但继续处理下一个资产
        log_error(asset, e)
        continue
```

#### 第二层：重试机制
- API 请求失败：重试 3 次，间隔 5 秒
- 数据库连接失败：重试 3 次，间隔 5 秒
- 超时重试：单个资产超时 60 秒后跳过

#### 第三层：数据验证
- 检查返回行数 > 0
- 验证日期范围是否符合预期
- 检查 OHLCV 数据是否有效（非空、非负）

### 3.2 失败场景处理

| 场景 | 处理方式 | 影响 |
|------|---------|------|
| API 限流（429） | 等待 60 秒后重试 | 延迟但不影响其他资产 |
| 符号不存在（404） | 记录警告，跳过该资产 | 继续处理其他资产 |
| 数据库连接失败 | 重试 3 次，失败则终止全部 | 阻止无效插入 |
| 重复数据 | 自动跳过（unique 约束） | 幂等性保证 |
| 数据格式错误 | 记录错误，跳过该资产 | 继续处理其他资产 |

---

## 4. 实施步骤

### Step 1: 创建配置文件
- [x] 创建 `config/assets.yaml`
- [x] 定义 7 个资产配置
- [x] 设置摄取参数

### Step 2: 更新审计脚本
- [x] 修改 `scripts/audit_current_task.py`
- [x] 添加文档检查：`assert os.path.exists("docs/TASK_012_05_PLAN.md")`
- [x] 添加配置检查：`assert os.path.exists("config/assets.yaml")`
- [x] 添加代码检查：`import src.data_loader.eodhd_bulk_loader`

### Step 3: 实现批量摄取脚本
- [x] 创建 `scripts/run_bulk_ingestion.py`
- [x] 加载 `config/assets.yaml`
- [x] 循环处理每个资产
- [x] 实现错误隔离和重试逻辑
- [x] 添加进度报告

### Step 4: 执行摄取
- [ ] 运行审计：`python3 scripts/audit_current_task.py`
- [ ] 执行摄取：`python3 scripts/run_bulk_ingestion.py`
- [ ] 验证数据：`python3 scripts/verify_db_status.py`

### Step 5: 验证和完成
- [ ] 检查 `market_data_ohlcv` 表行数 (预期 30k-50k)
- [ ] 确认日志显示 "Successfully ingested XAUUSD"
- [ ] 运行 `python3 scripts/project_cli.py finish`

---

## 5. 性能预估

### 5.1 时间估算

| 阶段 | 每资产时间 | 7 资产总时间 |
|------|-----------|-------------|
| API 获取 | ~2-3 秒 | ~15-20 秒 |
| 数据清洗 | ~0.5 秒 | ~3-4 秒 |
| 数据库插入 | ~2-3 秒 | ~15-20 秒 |
| 速率控制延迟 | 1 秒/资产 | 6 秒 |
| **总计** | **~6 秒/资产** | **~40-50 秒** |

### 5.2 数据量估算

```
7 资产 × ~8,000 行/资产 = ~56,000 行
实际行数可能因市场休市日不同而有所差异
预期范围: 30,000 - 60,000 行
```

### 5.3 API 配额使用

- **EODHD API 调用**: 7 次（每资产 1 次）
- **免费层限制**: 500 次/天
- **使用占比**: 1.4%
- **结论**: 配额充足

---

## 6. 验收标准

### 6.1 必须满足的条件

- [x] `docs/TASK_012_05_PLAN.md` 文件存在
- [ ] `config/assets.yaml` 文件存在且格式正确
- [ ] `scripts/audit_current_task.py` 通过所有检查
- [ ] `market_data_ohlcv` 表包含 7 个资产的数据
- [ ] 总行数 >= 30,000
- [ ] 日志确认 "Successfully ingested XAUUSD"
- [ ] 无未处理的异常错误

### 6.2 数据质量检查

```sql
-- 检查每个资产的行数
SELECT symbol, COUNT(*) as row_count,
       MIN(time) as earliest_date,
       MAX(time) as latest_date
FROM market_data_ohlcv
GROUP BY symbol
ORDER BY symbol;

-- 预期输出:
-- AUDUSD  ~8000  2002-xx-xx  2025-12-31
-- DJI     ~8000  19xx-xx-xx  2025-12-31
-- EURUSD  ~8000  2002-xx-xx  2025-12-31
-- GBPUSD  ~8000  19xx-xx-xx  2025-12-31
-- GSPC    ~8000  19xx-xx-xx  2025-12-31
-- USDJPY  ~8000  19xx-xx-xx  2025-12-31
-- XAUUSD  ~8000  19xx-xx-xx  2025-12-31
```

---

## 7. 风险与缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| API 速率限制 | 摄取失败 | 中 | 资产间延迟 1 秒 |
| 数据源符号不存在 | 部分资产缺失 | 低 | Try-except 隔离 |
| 网络中断 | 摄取中断 | 低 | 重试机制 + 幂等性 |
| 磁盘空间不足 | 无法插入 | 极低 | 预检查磁盘空间 |
| EODHD 历史数据不完整 | 行数少于预期 | 中 | 记录警告但允许继续 |

---

## 8. 后续任务

完成 Task #012.05 后的可能扩展：

1. **Task #012.06**: 实时数据摄取（Hot Path）
2. **Task #012.07**: 定时增量更新（每日 EOD 数据）
3. **Task #012.08**: 数据质量监控与告警
4. **Task #012.09**: 多交易所支持（NYSE, NASDAQ 等）
5. **Task #012.10**: 数据回填自动化（检测缺失日期）

---

## 9. 参考文档

- [Task #012.04 完成报告](../TASK_012_04_COMPLETION_REPORT.md) - 试点运行经验
- [EODHD API 文档](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes/) - 官方 API 规范
- [TimescaleDB Hypertable 文档](https://docs.timescale.com/use-timescale/latest/hypertables/) - 时序数据库优化
- [Protocol v2.2 规范](../PROTOCOL_V2.2.md) - Docs-as-Code 强制要求

---

**文档版本**: 1.0
**最后更新**: 2025-12-31 07:50 UTC
**作者**: Claude Sonnet 4.5
**审核状态**: 待审核
