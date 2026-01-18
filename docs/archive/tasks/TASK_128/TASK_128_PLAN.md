# Task #128 实施规划: Guardian Persistence Optimization

**任务代号**: TASK #128
**任务名称**: Guardian持久化优化
**Protocol**: v4.4 (Autonomous Closed-Loop + Wait-or-Die)
**优先级**: CRITICAL (Phase 7 关键路径)
**依赖**: Task #127 完成
**状态**: ✅ 规划完成 (by Plan Agent a7416e9)

---

## 执行摘要

Guardian持久化优化通过多层持久化架构（Redis + TimescaleDB + Checkpoint）实现：

- ✅ 99.99% 数据可用性
- ✅ < 30秒崩溃恢复时间
- ✅ 1000+ events/sec吞吐量
- ✅ 完整的24小时历史追溯
- ✅ 实时告警和仪表板能力

**关键原则**: 最小化交易性能影响 (Non-blocking I/O)

---

## 当前Guardian系统分析

### 三重护栏架构

1. **LatencySpikeDetector** - P99 < 100ms验证
2. **DriftMonitor** - 概念漂移监控 (PSI < 0.25)
3. **CircuitBreaker** - 电路断路器 (文件锁)

### 现状短板

| 问题 | 影响 | 优先级 |
|-----|-----|-------|
| 零持久化能力 | 重启后丧失历史 | P0 |
| 无恢复机制 | 无法从中断恢复 | P0 |
| 内存受限 (deque=100) | 无24小时分析 | P1 |
| 无分布式协调 | 多symbol无全局视图 | P2 |
| 无历史查询 | 审计困难 | P2 |

---

## 实现策略

### 多层持久化架构

```
Layer 1: Redis Cache (L1 Hot)
  └─ 毫秒级延迟，实时查询

Layer 2: TimescaleDB (L2 Cold)  
  └─ 秒级写入，24小时+历史

Layer 3: Checkpoint Files
  └─ 并行恢复机制
```

### 新增模块清单

**核心修改 (3个)**:
- `src/execution/live_guardian.py` (+80行)
- `src/execution/metrics_aggregator.py` (+60行)  
- `src/execution/live_launcher.py` (+40行)

**新增实现 (8个)**:
- `src/execution/guardian_redis_cache.py` (250行)
- `src/database/guardian_timescale.py` (200行)
- `src/execution/guardian_async_writer.py` (180行) ⭐ 使用asyncio Queue缓冲，确保主循环无阻塞
- `src/execution/guardian_checkpoint.py` (200行)
- `src/execution/guardian_recovery.py` (180行)
- `src/execution/guardian_consistency.py` (150行) ⭐ 包含故障降级策略：持久化失败→仅告警，不阻塞交易
- `src/execution/guardian_alerts.py` (180行)
- `src/serving/guardian_api.py` (250行) ⭐ 采用FastAPI框架，复用现有认证机制

**基础设施依赖** ⚠️ (AI审查补充):
- `docker-compose.yml` 更新：添加Redis (Alpine) + TimescaleDB服务
- 环境变量配置：REDIS_HOST, REDIS_PORT, TIMESCALEDB_URI

---

## 故障降级策略 (AI审查补充)

### 持久化层故障处理

| 故障场景 | 降级行为 | 告警级别 | 说明 |
|---------|--------|--------|------|
| Redis连接丧失 | 继续交易 | P1 | 持久化层故障不阻塞交易，仅触发告警 |
| TimescaleDB写入超时 | 异步重试 + 本地缓冲 | P1 | 使用Queue缓冲，等待DB恢复 |
| 双层都宕机 | Fail-open (继续交易) | P0 | 内存检查通过即执行，告警并记录 |
| Checkpoint恢复失败 | 从最近快照恢复 + 日志重放 | P0 | 确保系统可启动 |

**设计原则**:
- Fail-open (非阻塞): 持久化失败 ≠ 交易中止
- Guardian内存检查通过 → 优先交易执行
- 持久化失败 → 记录、重试、告警，但不阻止订单

---

## 执行计划

### Week 1: 实施 (5工作日)

**Mon-Tue**: 数据库和缓存层
**Wed**: 异步写入和故障恢复  
**Thu**: 可观测性
**Fri**: 压力测试和文档

### Week 2: 治理闭环 (5工作日)

**Mon-Tue**: Claude Logic Gate + Gemini Context Gate
**Wed-Thu**: 修复和优化
**Fri**: 最终验收

---

## 验收标准

### 性能指标

```
延迟: Redis < 5ms, Async < 10ms, 总体P99 < 100ms
吞吐: 1000+ events/sec
可靠性: 99.99%可用, 30秒恢复
一致性: 100%通过
```

### 依赖关系

✅ Task #127完成 (MultiSymbol并发+Guardian验证)
✅ MetricsAggregator修复
✅ Protocol v4.4框架

---

## 资源预期

- **代码量**: ~1,500行新增 + ~180行修改
- **Token消耗**: ~8,000-12,000 (实施+审查)
- **Timeline**: 5-7工作日

---

**本规划遵循Protocol v4.4 (Autonomous Closed-Loop + Wait-or-Die)**

**生成**: 2026-01-18 (Plan Agent a7416e9)
**外部AI审查**: ✅ APPROVED (gemini-3-pro-preview, 2026-01-18 17:31, 4,902 tokens)
  - 评分: ⭐⭐⭐⭐⭐ (5/5 - READY FOR INTEGRATION)
  - 反馈已应用: 性能声明修正、基础设施依赖补充、故障降级策略明确
**状态**: ✅ AI审查完成，待Stage 5 REGISTER (Notion)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
