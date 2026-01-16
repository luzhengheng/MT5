# Task #119 快速开始指南
## Phase 6 Live Canary Execution

### 前置条件

✅ Task #118 已完成 (Decision Hash: 1ac7db5b277d4dd1)
✅ 所有 Gate 1 测试通过 (22/22)
✅ Gate 2 AI 审查通过

### 快速启动

#### 1. 验证 Decision Hash
```bash
# 检查 Task #118 报告
grep "1ac7db5b277d4dd1" docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md
# 预期输出: **Decision Hash**: 1ac7db5b277d4dd1

# 验证元数据 JSON
python3 -c "import json; d=json.load(open('docs/archive/tasks/TASK_118/ADMISSION_DECISION_METADATA.json')); print(f\"Hash: {d['decision_hash']}, Decision: {d['decision']}, Confidence: {d['approval_confidence']:.1%}\")"
# 预期输出: Hash: 1ac7db5b277d4dd1, Decision: GO, Confidence: 86.6%
```

#### 2. 运行 Gate 1 测试
```bash
# 执行 TDD 审计框架
python3 scripts/audit_task_119.py

# 预期输出:
# Tests Run: 22
# Passed: 22
# Failed: 0
```

#### 3. 启动 Phase 6 Canary
```bash
# 执行启动序列 (包括 hash 验证 + 初始化 + 金丝雀订单)
python3 src/execution/live_launcher.py

# 输出示例:
# ✅ Decision Hash verified: 1ac7db5b277d4dd1
# ✅ Authentication PASSED
# ✅ All preconditions validated
# ✅ Canary order FILLED: Ticket #1100000001
# ✅ PHASE 6 LIVE TRADING LAUNCHED SUCCESSFULLY
```

#### 4. 监控运行时护栏
```bash
# 启动 Guardian 监控器 (后台运行)
python3 -c "from src.execution.live_guardian import initialize_guardian; g = initialize_guardian(); \
import time; [print(f'Health: {g.get_system_health()} | Spikes: {g.latency_detector.spike_count}') for _ in range(5) if time.sleep(2) or True]"

# 预期输出:
# Health: HEALTHY | Spikes: 0
# Health: HEALTHY | Spikes: 0
```

### 关键命令

#### 查看启动报告
```bash
python3 src/execution/live_launcher.py 2>&1 | grep -E "✅|FILLED|Ticket|HEALTHY"
```

#### 监控系统健康
```bash
python3 -c "from src.execution.live_guardian import initialize_guardian; print(initialize_guardian().generate_report())"
```

#### 收集物理验尸证据
```bash
grep -E "DECISION_HASH|Ticket:|FILLED|PHASE 6|HEALTHY" VERIFY_LOG.log
```

### 警告与注意

⚠️ **严重警告**: 此命令启动真实交易账户操作！
- 账户: JustMarkets-Demo2 (ID: 1100212251)
- 初始仓位: 0.001 lot (10% 系数)
- 金丝雀: 用于验证系统，不代表最终性能

⚠️ **监控要求**:
- 首 24 小时必须持续监控
- 每 1 小时检查 Guardian 漂移检测报告
- 任何 P99 延迟 > 100ms 需要立即调查

### 故障排查

#### 问题: "Decision Hash 不匹配"
```bash
# 检查报告文件是否存在
ls -la docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md

# 检查 Hash 值
grep "Decision Hash" docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md

# 预期: 应该显示 1ac7db5b277d4dd1
```

#### 问题: "Guardian halt condition detected"
```bash
# 检查电路断路器状态
test -f /tmp/mt5_crs_kill_switch.lock && echo "Circuit breaker ENGAGED" || echo "Circuit breaker SAFE"

# 如需重置
rm -f /tmp/mt5_crs_kill_switch.lock
```

#### 问题: "P99 延迟超过 100ms"
```bash
# 检查延迟历史
python3 -c "from src.execution.live_guardian import initialize_guardian; g = initialize_guardian(); print(f\"P99: {g.latency_detector.get_p99_latency():.2f}ms, Spikes: {g.latency_detector.spike_count}\")"

# 如果 > 100ms，检查系统负载
top -bn1 | head -n 3
```

### 下一步

✅ 完成: Task #119 启动
📋 待做: Task #120 (Production Ramp-Up - 72 小时后评估)

### 相关文档

- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - 完整任务报告
- [SYNC_GUIDE.md](SYNC_GUIDE.md) - 部署变更清单
- [../../tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md](../../tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md) - Task #118 决策报告
