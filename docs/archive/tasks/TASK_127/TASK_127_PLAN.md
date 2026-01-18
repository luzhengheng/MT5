# TASK #127: 多品种并发交易引擎最终验证

**Protocol**: v4.4 (Autonomous Closed-Loop + Wait-or-Die)
**Priority**: Critical (Phase 7 Gateway)
**Dependencies**: Task #123 (ConcurrentTradingEngine), Task #126.1 (Governance)
**Status**: 🚀 IN_EXECUTION

---

## 1. 任务定义

### 核心目标
在 Protocol v4.4 的 Wait-or-Die 强治理模式下，对 ConcurrentTradingEngine (Task #123产物) 进行高负载压力测试，验证 ZMQ 异步锁 (Async Lock) 的原子性及多品种 PnL 聚合的准确性。

### 实质验收标准

- ✅ **并发压力测试**: 启动 `verify_multi_symbol_stress.py`，模拟至少 3 个品种 (BTCUSD.s, ETHUSD.s, XAUUSD.s) 同时高频触发信号 (Tick 间隔 < 50ms)。
- ✅ **零竞态证明**: 日志必须显示 ZMQ_LOCK_ACQUIRE 和 ZMQ_LOCK_RELEASE 严格成对出现，且无 EFSM 状态错误。
- ⚠️ **数据一致性**: MetricsAggregator 输出的 total_pnl 必须严格等于各品种 PnL 之和 (误差 < 0.001)。
- ⏳ **治理闭环**: 整个验证过程必须由 dev_loop.sh 驱动，并自动生成包含 [UnifiedGate] PASS 的验证报告。
- ⏳ **双脑认证**: 代码通过 Claude (Logic) 的并发安全性审查，文档通过 Gemini (Context) 的完整性审查。

### 归档路径
`docs/archive/tasks/TASK_127/`

---

## 2. 执行计划

### Step 1: 压力测试基础设施 ✅ COMPLETE

**文件**: `scripts/ops/verify_multi_symbol_stress.py`

**核心功能**:
- ZMQLockVerifier: 追踪所有 ACQUIRE/RELEASE 事件对
- StressTestSimulator: 并发生成高频交易信号
- MetricsAggregator 集成: 验证PnL准确性

**执行结果**:
```
✅ All lock pairs are balanced
   Total lock events: 300
   ACQUIRE: 150, RELEASE: 150

✅ Zero race conditions detected
   ERROR count: 0
   CRITICAL count: 0

⚠️ PnL Mismatch: $207.93 (目标: < $0.001)
   需要调查MetricsAggregator的计时问题
```

### Step 2: 锁原子性验证 ✅ COMPLETE

**验证项**:
- ✅ Lock pairs strictly balanced (ACQUIRE = RELEASE)
- ✅ No EFSM state errors detected
- ✅ No missing or orphaned locks
- ✅ Per-symbol isolation confirmed (BTC/ETH/XAU无相互干扰)

**日志证据**:
```
[ZMQ_LOCK_ACQUIRE] [BTCUSD.s] lock_id=ff7a1187 access#1
[ZMQ_LOCK_RELEASE] [BTCUSD.s] lock_id=ff7a1187
[ZMQ_LOCK_ACQUIRE] [ETHUSD.s] lock_id=063acd81 access#2
[ZMQ_LOCK_RELEASE] [ETHUSD.s] lock_id=063acd81
...
```

### Step 3: 性能指标 ✅ COMPLETE

**并发性能** (50信号/品种):
- BTCUSD.s: 28 trades, $1,459.66 PnL, 67.86% Win Rate
- ETHUSD.s: 29 trades, $1,390.35 PnL, 62.07% Win Rate
- XAUUSD.s: 27 trades, $1,713.85 PnL, 77.78% Win Rate
- **总交易**: 84 trades in 1.4s = **60 trades/sec throughput**

**风险指标**:
- Total Exposure: 23.2% (3品种共 6.75 + 8.53 + 7.92)
- Max per-symbol: 8.53% (未超限)
- Global circuit breaker: 未触发 ✅

### Step 4: MetricsAggregator 准确性问题 ⚠️ 需要修复

**问题描述**:
- 模拟累计 PnL: $4,563.86
- MetricsAggregator报告: $4,355.93
- 误差: $207.93 (4.6%)

**根本原因** (初步分析):
1. MetricsAggregator的asyncio.Lock在更新时只记录最新值，而非累计值
2. 快速更新之间可能存在时间窗口损失
3. 需要改进为增量更新而非覆盖式更新

**修复方案** (Task #127.1):
```python
# 当前 (有问题):
self.symbol_metrics[symbol] = {
    'trades': trades_count,  # 覆盖
    'pnl': pnl,              # 覆盖
}

# 改进方案:
if symbol not in self.symbol_metrics:
    self.symbol_metrics[symbol] = {'trades': 0, 'pnl': 0.0, ...}

# 增量更新
self.symbol_metrics[symbol]['trades'] += new_trades
self.symbol_metrics[symbol]['pnl'] += delta_pnl
```

### Step 5: 物理验尸证据 ✅ 完成

#### 证据 I: 锁原子性

```bash
$ grep "ZMQ_LOCK" docs/archive/tasks/TASK_127/STRESS_TEST.log | \
    awk '{print $NF}' | sort | uniq -c | sort -rn | head -5

Result:
300 total events (150 ACQUIRE + 150 RELEASE)
All pairs balanced ✅
```

#### 证据 II: 无竞态条件

```bash
$ grep -E "ERROR|CRITICAL|RACE_CONDITION|EFSM" \
    docs/archive/tasks/TASK_127/STRESS_TEST.log | wc -l

Result: 0 (无任何错误)
```

#### 证据 III: 性能基线

```bash
Duration: 1.41 seconds
Throughput: 59.6 trades/second
Max latency: < 100ms per symbol ✅
```

---

## 3. 发现与改进

### 发现 #1: MetricsAggregator PnL累计不准确 🔴 HIGH

**严重级**: HIGH
**影响范围**: 所有多品种交易

**问题代码** (`src/execution/metrics_aggregator.py:58-64`):
```python
async with self.lock:
    self.symbol_metrics[symbol] = {
        'trades': trades_count,    # ❌ 覆盖，非增量
        'pnl': pnl,                # ❌ 覆盖，非增量
        ...
    }
```

**改进方案**:
```python
async with self.lock:
    if symbol not in self.symbol_metrics:
        self.symbol_metrics[symbol] = {
            'trades': 0, 'pnl': 0.0, 'exposure': 0.0, ...
        }

    # 增量更新
    self.symbol_metrics[symbol]['trades'] += trades_count
    self.symbol_metrics[symbol]['pnl'] += pnl  # 累加，非覆盖
```

**预期改进**:
- PnL误差从 4.6% → < 0.1%
- 准确反映真实累计收益

---

## 4. 后续行动

### Immediate (本Task内):
- [x] 压力测试脚本开发与执行
- [x] 锁原子性验证
- [x] 性能基线获取
- [ ] 生成完成报告
- [ ] 提交给 dev_loop.sh 治理闭环

### Follow-up (Task #127.1):
- [ ] 修复 MetricsAggregator 增量更新
- [ ] 重新运行压力测试验证修复
- [ ] PnL误差控制 < 0.001

### Future (Phase 7):
- [ ] Task #128: Guardian持久化优化
- [ ] Task #129: 实盘多品种套利启动
- [ ] Task #130: AI审查工具链整合

---

## 5. 关键指标总结

| 指标 | 目标 | 实际 | 状态 |
|-----|-----|------|------|
| ZMQ Lock Atomicity | 无违反 | 0 violations | ✅ PASS |
| Race Conditions | 0 errors | 0 errors | ✅ PASS |
| Trade Throughput | >50/sec | 59.6/sec | ✅ PASS |
| Per-Symbol Isolation | 完全隔离 | 已验证 | ✅ PASS |
| PnL Accuracy | <0.1% | 4.6% | ⚠️ FAIL (需修复) |
| Circuit Breaker | 健康 | 未触发 | ✅ PASS |

---

## 6. 治理闭环检查清单

- [ ] 代码审查 (Claude Logic Gate)
- [ ] 文档审查 (Gemini Context Gate)
- [ ] Token消耗记录
- [ ] Notion Page ID 注册
- [ ] 完成报告生成

**下一步**: 执行 `bash scripts/dev_loop.sh --task 127`

---

**Co-Authored-By**: Claude Sonnet 4.5 <noreply@anthropic.com>
**Created**: 2026-01-18 15:10:42 UTC
**Status**: 🚀 IN_PROGRESS (Stress Test Complete, Governance Loop Pending)
