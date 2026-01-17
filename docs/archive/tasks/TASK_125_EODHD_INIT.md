# TASK_125: EODHD 数据源初步接入

**Protocol**: v4.3 (Zero-Trust Edition)
**Priority**: High
**Status**: 新建

## 1. 任务定义 (Definition)

### 1.1 核心目标
实现从 EODHD API 下载历史 OHLCV 数据的 Python 脚本，并存储为 CSV 格式。

### 1.2 实质验收标准 (Substance)
- ☐ 脚本能从 EODHD API 拉取 AAPL 的历史数据
- ☐ **物理证据**: 生成的 CSV 文件包含时间戳和行数统计日志
- ☐ **后台对账**: API 响应状态码必须为 200，数据完整性验证通过
- ☐ 韧性: API 失败时有明确错误提示，无静默失败
- ☐ **环境变量验证**: 脚本启动时检查 EODHD_API_KEY，缺失时中止执行

## 2. 交付物矩阵 (Deliverable Matrix)

| 类型 | 文件路径 | Gate 1 刚性验收标准 |
|------|---------|------------------|
| 代码 | `src/data_loaders/eodhd_loader.py` | 无 Pylint 错误; 环境变量检查; 异常处理完整 |
| 脚本 | `scripts/ops/fetch_eodhd_data.py` | 执行无错误; 输出 CSV 文件有验证日志 |
| 测试 | `tests/test_eodhd_loader.py` | 覆盖率 > 80%; 包含 Mock API 测试 |
| 日志 | `VERIFY_LOG.log` | 包含 API 调用时间戳、Token 消耗、行数统计 |

## 3. 执行计划 (Zero-Trust Execution Plan)

### Step 1: 基础设施铺设 & 清理
- [ ] 删除旧证: `rm -f VERIFY_LOG.log docs/archive/tasks/TASK_125/AI_REVIEW.md`
- [ ] 创建目录: `mkdir -p src/data_loaders tests`

### Step 2: 核心开发
- [ ] 实现 `EODHDLoader` 类，继承 `DataLoaderBase`
- [ ] 支持的参数: `symbol`, `date_from`, `date_to`, `interval` (daily/intraday)
- [ ] 环境变量检查: `assert os.getenv('EODHD_API_KEY'), "❌ 缺少 EODHD_API_KEY"`

### Step 3: 编写测试与自测
- [ ] 编写单元测试，Mock API 响应
- [ ] 运行: `python3 scripts/ops/fetch_eodhd_data.py --symbol AAPL --output data.csv | tee VERIFY_LOG.log`

### Step 4: 智能闭环审查
- [ ] 执行: `python3 scripts/ai_governance/unified_review_gate.py review src/data_loaders/eodhd_loader.py`

### Step 5: 物理验尸 (Forensic Verification)
- [ ] `date` (证明当前系统时间)
- [ ] `wc -l data.csv` (CSV 行数统计)
- [ ] `grep -c "AAPL" data.csv` (验证数据完整性)
- [ ] `tail -5 VERIFY_LOG.log` (日志回显)

## 4. 物理验尸验证 (Forensic Verification)

执行以下命令验证交付物：

```bash
# 1. 检查文件存在
ls -lh src/data_loaders/eodhd_loader.py
ls -lh data.csv

# 2. 验证 CSV 内容
head -5 data.csv
wc -l data.csv

# 3. 检查日志
grep "EODHD" VERIFY_LOG.log | tail -10
```

## 5. 下一步行动 (Action Item)

- [ ] 完成代码实现
- [ ] 所有测试通过
- [ ] 提交 PR，获得审查批准
- [ ] 合并到主分支
- [ ] 启动 Task #126: 数据质量验证框架

---

**预计工作量**: 3-5小时
**依赖前置条件**: EODHD API 密钥可用
**预期交付日期**: 2026-01-25
