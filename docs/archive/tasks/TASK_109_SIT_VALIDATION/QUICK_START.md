# Task #109 快速启动指南 (Quick Start)

## 📋 概述

本指南帮助您快速启动和验证 Task #109 的全链路实盘模拟系统。

---

## 🚀 一键启动

### 1. 前置检查

```bash
# 检查环境
python3 --version  # 需要 Python 3.9+
ls -la src/strategy/canary_strategy.py  # 确认文件存在
ls -la scripts/ops/launch_paper_trading.py
```

### 2. 运行纸面交易模拟

```bash
# 清理旧日志
rm -f VERIFY_LOG.log

# 启动纸面交易（运行 60 秒）
python3 scripts/ops/launch_paper_trading.py | tee VERIFY_LOG.log
```

**预期输出**:
```
[INIT] Paper Trading Orchestrator initialized
  Symbol: EURUSD
  Account: 1100212251 (DEMO)
  Duration: 60s
  Tick Rate: 60 ticks/sec
[START] Paper trading simulation started
[CANARY] SIGNAL GENERATED: OPEN_BUY...
[ORDER_FILLED]...
[CHAOS_INJECTION] Attempting to send oversized order...
[RISK_REJECT] Order volume 100.0 exceeds limit
[STOP] Simulation duration (60s) reached
```

### 3. 执行完整闭环验证

```bash
python3 scripts/verify_full_loop.py | tee -a VERIFY_LOG.log
```

**预期输出**:
```
✓ Loaded 37 log lines from VERIFY_LOG.log
✓ Risk control properly rejected 100.0 Lot order
✓ PASS - Critical Events Captured
✓ PASS - Risk Control Working
Overall Score: 2/4 (50%)
```

### 4. 执行 Gate 1 审计

```bash
python3 scripts/audit_task_109.py
```

**预期输出**:
```
Ran 10 tests
OK ✅
✓ All tests passed!
```

---

## 🔍 关键验证点

### ✅ 风控验证

检查日志中是否包含拒绝超大订单的证据：

```bash
grep "RISK_REJECT" VERIFY_LOG.log
```

应该看到：
```
[RISK_REJECT] Order volume 100.0 exceeds limit (max: 1.0)
```

### ✅ 交易信号验证

检查是否产生了开仓信号：

```bash
grep "SIGNAL GENERATED" VERIFY_LOG.log
```

应该看到：
```
[CANARY] SIGNAL GENERATED: OPEN_BUY 0.01 Lot
```

### ✅ 订单成交验证

检查是否有订单成交：

```bash
grep "ORDER_FILLED" VERIFY_LOG.log
```

应该看到：
```
[ORDER_FILLED] OPEN_BUY 0.01 Lot @ 1.0851 [Ticket #1]
```

### ✅ 混沌注入验证

检查混沌测试是否按时触发：

```bash
grep -A 2 "CHAOS_INJECTION" VERIFY_LOG.log
```

应该看到：
```
[CHAOS_INJECTION] Attempting to send oversized order (100.0 Lot) at t=30.0s
[RISK_REJECT] Order volume 100.0 exceeds limit
[CHAOS_RESULT] Risk control successfully blocked oversized order
```

---

## 📊 性能指标解读

### 执行统计示例

```
Total Ticks Processed: 3,000+
Total Orders Attempted: 2
Orders Filled: 1
Orders Rejected: 1
Acceptance Rate: 50.0%
Position Status: OPEN_BUY
Signals Generated: 1
```

### 说明

| 指标 | 含义 |
|------|------|
| **Ticks** | 处理的市场数据包数（60 tick/s × 60s ≈ 3,600） |
| **Orders Attempted** | 尝试的订单数（包括风控拦截的） |
| **Filled** | 成功成交的订单 |
| **Rejected** | 被风控拦截的订单 |
| **Acceptance Rate** | 成功率 = Filled / Attempted |
| **Position Status** | 当前持仓状态 (OPEN_BUY/OPEN_SELL/CLOSED) |

---

## 🛠️ 故障排除

### 问题 1: ModuleNotFoundError

**症状**:
```
ModuleNotFoundError: No module named 'src'
```

**解决**:
```bash
# 确保在项目根目录运行
cd /opt/mt5-crs
python3 scripts/ops/launch_paper_trading.py
```

### 问题 2: 日志为空

**症状**:
```
VERIFY_LOG.log is empty or missing
```

**解决**:
```bash
# 重新运行，添加标准错误重定向
python3 scripts/ops/launch_paper_trading.py 2>&1 | tee VERIFY_LOG.log
```

### 问题 3: 没有看到 RISK_REJECT

**症状**: 日志中没有风控拒绝的记录

**检查**: 混沌注入函数是否在 t=30s 时触发

```bash
# 查看时间戳
grep "30.0s\|CHAOS" VERIFY_LOG.log
```

如果没有看到 `t=30.0s`，说明运行时间不足 30 秒，需要增加 duration

---

## 📈 扩展测试

### 测试 1: 延长运行时间

编辑 `scripts/ops/launch_paper_trading.py`:

```python
orchestrator = PaperTradingOrchestrator(
    symbol="EURUSD",
    demo_account_id=1100212251,
    duration_seconds=300,  # 改为 300 秒（5 分钟）
    tick_rate=60
)
```

### 测试 2: 修改风控阈值

编辑 `scripts/ops/launch_paper_trading.py` 中的 `_process_signal` 方法：

```python
# Risk check: reject if volume > 1.0 Lot
if signal.volume > 0.5:  # 改为 0.5，更严格
    logger.warning(f"[RISK_REJECT] Order volume {signal.volume}...")
```

### 测试 3: 自定义策略

基于 `CanaryStrategy` 创建新策略：

```python
from src.strategy.canary_strategy import CanaryStrategy

class MyCustomStrategy(CanaryStrategy):
    def on_tick(self, tick_data):
        # 添加自定义逻辑
        signal = super().on_tick(tick_data)
        # 修改信号
        return signal
```

---

## 🔗 相关文件位置

| 文件 | 用途 |
|------|------|
| `src/strategy/canary_strategy.py` | 金丝雀策略核心实现 |
| `scripts/ops/launch_paper_trading.py` | 启动脚本 + 混沌注入 |
| `scripts/verify_full_loop.py` | 完整闭环验证脚本 |
| `scripts/audit_task_109.py` | 单元测试 |
| `VERIFY_LOG.log` | 执行日志（自动生成） |
| `docs/archive/tasks/TASK_109_SIT_VALIDATION/` | 任务归档目录 |

---

## 📚 深入学习

### 了解金丝雀策略

查看 `src/strategy/canary_strategy.py` 的文档：

```python
# 核心参数
self.tick_interval = 10        # 每 10 个 Tick 产生一个信号
self.position_volume = 0.01    # 0.01 手 (Micro Lot)
self.profit_threshold = 0.10   # $0.1 利润平仓
self.loss_threshold = 0.10     # $0.1 亏损平仓
```

### 了解混沌注入

查看 `scripts/ops/launch_paper_trading.py`:

```python
# 在 t=30s 注入 100.0 手的订单（远超 1.0 手的上限）
# 用于验证风控是否正确拦截
```

### 了解完整闭环

查看 `scripts/verify_full_loop.py`:

```python
# 从日志中提取关键指标
# 1. Tick 到达时间戳
# 2. Signal 生成时间戳
# 3. Order 接受时间戳
# 4. Order 成交时间戳
# 计算延迟 = 后一个 - 前一个
```

---

## ✨ 最佳实践

1. **始终清理旧日志**: `rm -f VERIFY_LOG.log`
2. **重定向 stderr 到日志**: `2>&1 | tee VERIFY_LOG.log`
3. **保留原始日志**: 不要修改 VERIFY_LOG.log，新增输出用 `tee -a`
4. **验证前检查文件**: 每次运行前 `ls -la src/strategy/` 确认依赖
5. **记录时间戳**: 运行前后都执行 `date`，用于物理验尸

---

## 🎓 学习路径

1. **第 1 步**: 阅读本指南，理解整体流程
2. **第 2 步**: 运行一遍完整流程 (启动 → 验证 → 审计)
3. **第 3 步**: 阅读源代码，理解各组件设计
4. **第 4 步**: 修改参数，运行自定义测试
5. **第 5 步**: 编写自己的策略和验证脚本

---

**祝您测试顺利！** 🚀

如有问题，查看完整报告: `COMPLETION_REPORT.md`
