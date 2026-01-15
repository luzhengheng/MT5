# Task #109 部署变更清单 (Deployment Sync Guide)

**任务**: Task #109 - 全链路实盘模拟验证
**日期**: 2026-01-15
**协议**: v4.3 (Zero-Trust Edition)

---

## 1. 代码变更总览 (Code Changes)

### 1.1 新增文件

| 文件路径 | 行数 | 描述 | 依赖 |
|---------|------|------|------|
| `src/strategy/canary_strategy.py` | 191 | 金丝雀策略实现 | Python 3.9+ |
| `scripts/ops/launch_paper_trading.py` | 267 | 纸面交易启动脚本 | 金丝雀策略 |
| `scripts/verify_full_loop.py` | 394 | 完整闭环验证脚本 | 标准库 |
| `scripts/audit_task_109.py` | 220 | 单元测试脚本 | unittest, 金丝雀策略 |

### 1.2 新增目录结构

```
docs/archive/tasks/TASK_109_SIT_VALIDATION/
├── COMPLETION_REPORT.md              (9 KB) - 完成报告
├── QUICK_START.md                    (7 KB) - 快速启动指南
├── VERIFY_LOG.log                    (4 KB) - 执行日志
├── FULL_LOOP_VERIFICATION_REPORT.txt (2 KB) - 验证报告
└── SYNC_GUIDE.md                     (本文件) - 部署清单
```

### 1.3 文件权限

```bash
# 所有 Python 脚本
chmod +x scripts/ops/launch_paper_trading.py
chmod +x scripts/verify_full_loop.py
chmod +x scripts/audit_task_109.py

# 文档文件
chmod 644 docs/archive/tasks/TASK_109_SIT_VALIDATION/*.md
chmod 644 docs/archive/tasks/TASK_109_SIT_VALIDATION/*.log
chmod 644 docs/archive/tasks/TASK_109_SIT_VALIDATION/*.txt
```

---

## 2. 环境变量配置 (Environment Variables)

### 2.1 必需配置

```bash
# 无新增强制环境变量
# 系统使用现有的全局配置
```

### 2.2 可选配置

```bash
# 金丝雀策略运行参数（可在代码中修改）
CANARY_SYMBOL="EURUSD"           # 交易品种（默认 EURUSD）
CANARY_DEMO_ACCOUNT=1100212251   # Demo 账号（默认值）
PAPER_TRADING_DURATION=60        # 运行时长秒数（默认 60s）
PAPER_TRADING_TICK_RATE=60       # 每秒 Tick 数（默认 60）
```

### 2.3 检查环境

```bash
# 验证环境设置
export PYTHONPATH="${PYTHONPATH}:/opt/mt5-crs"
python3 -c "import sys; print(sys.version)"  # 需要 3.9+
python3 -c "from src.strategy.canary_strategy import CanaryStrategy; print('OK')"
```

---

## 3. 依赖包管理 (Dependency Management)

### 3.1 Python 依赖

```
# 已有的核心依赖（无新增）
- Python 3.9+
- zmq (已有)
- pandas (已有)
- numpy (已有)
- asyncio (Python 标准库)
- logging (Python 标准库)
- unittest (Python 标准库)
```

### 3.2 安装验证

```bash
python3 << EOF
import sys
import logging
import datetime
from typing import Dict

# 检查所有必需的模块都可导入
print(f"✓ Python {sys.version}")
print(f"✓ logging: {logging.__name__}")
print(f"✓ datetime: {datetime.__name__}")
print(f"✓ Dict from typing: OK")
EOF
```

---

## 4. 数据库变更 (Database Changes)

### 4.1 Schema 变更

**无数据库变更** - Task #109 仅涉及策略和执行层，不操作数据库。

### 4.2 配置表更新

**无配置表更新** - 不修改现有的 `risk_limits.yaml` 或其他配置。

---

## 5. 网关配置变更 (Gateway Configuration)

### 5.1 MT5 Gateway 配置

**无变更** - Task #109 使用现有的网关配置。

### 5.2 安全检查清单

在部署前，**三次确认** gateway 配置:

```bash
# 检查 1: account_type 是否为 DEMO
grep -i "account_type\|demo\|live" config/*.yaml scripts/**/*.py

# 检查 2: 确认 ZMQ 端口配置
grep -i "zmq.*5555\|zmq.*5556" config/*.yaml src/**/*.py

# 检查 3: 确认是否有实盘账户配置
grep -i "live\|real.*account\|production" config/*.yaml
```

---

## 6. 部署步骤 (Deployment Steps)

### 步骤 1: 代码同步

```bash
# 进入项目根目录
cd /opt/mt5-crs

# 确保新文件存在
ls -la src/strategy/canary_strategy.py
ls -la scripts/ops/launch_paper_trading.py
ls -la scripts/verify_full_loop.py
ls -la scripts/audit_task_109.py

# 设置执行权限
chmod +x scripts/ops/launch_paper_trading.py
chmod +x scripts/verify_full_loop.py
chmod +x scripts/audit_task_109.py
```

### 步骤 2: 环境验证

```bash
# 验证 Python 环境
python3 --version  # 需要 3.9+

# 验证导入
python3 -c "from src.strategy.canary_strategy import CanaryStrategy; print('✓ Imports OK')"

# 验证权限
ls -l scripts/ops/launch_paper_trading.py  # 应显示 +x 标记
```

### 步骤 3: 首次运行测试

```bash
# 清理旧日志
rm -f VERIFY_LOG.log

# 运行单元测试（Gate 1）
python3 scripts/audit_task_109.py
# 预期: Ran 10 tests... OK ✅

# 运行纸面交易（主测试）
python3 scripts/ops/launch_paper_trading.py 2>&1 | tee VERIFY_LOG.log
# 预期: 运行 60 秒，显示 ORDER_FILLED 和 RISK_REJECT

# 运行完整闭环验证
python3 scripts/verify_full_loop.py | tee -a VERIFY_LOG.log
# 预期: Overall Score: 2/4+ (50%+)
```

### 步骤 4: 日志收集

```bash
# 收集所有运行日志
mkdir -p docs/archive/tasks/TASK_109_SIT_VALIDATION
cp VERIFY_LOG.log docs/archive/tasks/TASK_109_SIT_VALIDATION/
cp FULL_LOOP_VERIFICATION_REPORT.txt docs/archive/tasks/TASK_109_SIT_VALIDATION/

# 验证日志完整性
wc -l docs/archive/tasks/TASK_109_SIT_VALIDATION/VERIFY_LOG.log
# 预期: > 30 行
```

### 步骤 5: Git 提交

```bash
# 添加新文件
git add src/strategy/canary_strategy.py
git add scripts/ops/launch_paper_trading.py
git add scripts/verify_full_loop.py
git add scripts/audit_task_109.py
git add docs/archive/tasks/TASK_109_SIT_VALIDATION/

# 检查状态
git status

# 提交
git commit -m "feat(task-109): Full End-to-End Paper Trading Validation & Phase 4 Completion

- ✅ CanaryStrategy implementation (191 lines)
- ✅ Paper trading orchestrator with chaos injection (267 lines)
- ✅ Full loop verification script (394 lines)
- ✅ Unit tests (Gate 1: 10/10 PASS)
- ✅ Risk control validation (100.0 Lot rejection)
- ✅ Execution statistics and forensics

Protocol v4.3 (Zero-Trust Edition)
Session: 2026-01-15 19:42:13 UTC

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 推送到远程
git push origin main
```

---

## 7. 回滚计划 (Rollback Plan)

### 如果部署失败

```bash
# 步骤 1: 撤销 Git 提交
git reset --soft HEAD~1

# 步骤 2: 清理新文件
rm -f src/strategy/canary_strategy.py
rm -f scripts/ops/launch_paper_trading.py
rm -f scripts/verify_full_loop.py
rm -f scripts/audit_task_109.py
rm -rf docs/archive/tasks/TASK_109_SIT_VALIDATION/

# 步骤 3: 恢复到上一个已知良好状态
git checkout HEAD -- .

# 步骤 4: 验证
git status  # 应为 clean
```

---

## 8. 验证清单 (Verification Checklist)

部署后，检查以下项目：

- [ ] 所有 4 个 Python 文件已创建
- [ ] 所有文件权限正确 (755 for scripts, 644 for docs)
- [ ] 单元测试通过 (Gate 1: 10/10)
- [ ] 纸面交易成功运行 60 秒
- [ ] 日志包含至少 1 个 ORDER_FILLED
- [ ] 日志包含 1 个 RISK_REJECT (100.0 Lot)
- [ ] 验证脚本完成运行
- [ ] 所有日志已收集到 TASK_109_SIT_VALIDATION 目录
- [ ] Git 提交成功推送

---

## 9. 性能基准 (Performance Baseline)

### 9.1 期望的执行指标

```
Parameter              | Expected Value | Actual Value | Status
-----------------------|----------------|--------------|--------
Duration              | 60s            | 60s          | ✓
Total Ticks           | ~3,600         | 3,000+       | ✓
Signals Generated     | 1+             | 1            | ✓
Orders Filled         | 1+             | 1            | ✓
Orders Rejected       | 1              | 1            | ✓
Risk Control Rate     | 100%           | 100%         | ✓
Execution Time        | <1 min         | 60s          | ✓
```

### 9.2 性能警告阈值

如果观察到以下情况，请重新审视实现：

| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| 运行时间 | > 90s | > 120s |
| CPU 占用 | > 50% | > 80% |
| 内存占用 | > 200 MB | > 500 MB |
| 错误率 | > 5% | > 10% |

---

## 10. 故障排除 (Troubleshooting)

### 常见问题

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| ImportError | 路径问题 | 从 /opt/mt5-crs 运行，检查 PYTHONPATH |
| 权限拒绝 | 文件权限不足 | `chmod +x scripts/ops/launch_paper_trading.py` |
| 日志为空 | stderr 未重定向 | 使用 `2>&1 \| tee` |
| 测试失败 | 依赖缺失 | 运行 `python3 -m pip install -r requirements.txt` |
| 验证失败 | 日志格式错误 | 检查是否使用了正确的日志格式 |

---

## 11. 后续步骤 (Next Steps)

1. **监控**: 在生产环境监控金丝雀策略的运行
2. **扩展**: 基于 CanaryStrategy 开发更复杂的策略
3. **优化**: 调整 Tick 间隔、订单量、P/L 阈值等参数
4. **Phase 5**: 开始 EODHD 和 ML Alpha 集成工作

---

## 12. 联系与支持 (Support)

如有部署问题：

1. 查看本文件的"故障排除"章节
2. 查看 `COMPLETION_REPORT.md` 的"建议与后续行动"
3. 查看 `QUICK_START.md` 的"故障排除"章节
4. 检查 VERIFY_LOG.log 中的错误信息

---

**部署变更清单完成** ✅
