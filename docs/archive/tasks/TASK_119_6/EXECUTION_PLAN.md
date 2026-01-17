# Task #119.6 执行计划
## 基于已验证链路的金丝雀策略重新执行

**任务 ID**: 119.6 (Re-execution)
**执行时间**: 2026-01-17 03:50+ CST
**优先级**: P0 (Critical)
**依赖**: Task #119.5 (Remote Link Verified ✅)

---

## 1. 任务背景

### 问题分析
- **Task #119 执行时刻**: 2026-01-17 03:00 UTC
- **当时的 ZMQ 配置**: 127.0.0.1:5555 (Localhost - 本地环回)
- **发现的问题**: INF 节点连接到自己，而非远端 GTW
- **影响**: 订单可能成交到本地 Mock 环境，而非真实 MT5

### Task #119.5 修复
- **修复内容**: 确认 GTW 真实私网 IP 为 172.19.141.255
- **链路验证**: INF↔GTW ZMQ 连接已验证畅通
- **MT5 响应**: 握手包往返成功，服务可达
- **完成时间**: 2026-01-17 03:40:40 UTC

### 重新执行的目的
在已验证的远程链路环境下，重新执行金丝雀策略，确保：
1. ✅ 交易信号正确传递到真实 MT5
2. ✅ 订单真实成交到 JustMarkets 账户
3. ✅ 完整的端到端链路验证

---

## 2. 链路验证清单

| 检查项 | 状态 | 证据 |
|--------|------|------|
| **Task #119.5 完成** | ✅ PASS | Commit 97278b0 |
| **ZMQ 套接字连接** | ✅ PASS | "[SUCCESS] ZMQ 套接字连接成功" |
| **握手包发送** | ✅ PASS | "[SUCCESS] 握手包已发送" |
| **MT5 响应接收** | ✅ PASS | "[RECV] 从 MT5 接收响应成功" |
| **链路可达性** | ✅ PASS | "🎉 链路连通性测试 SUCCESS" |
| **ZMQ 通道建立** | ✅ PASS | "✅ ZMQ REQ-REP 通道已建立" |
| **MT5 服务可达** | ✅ PASS | "✅ MT5 服务已响应" |

**综合结论**: ✅ **所有前置条件已就绪**

---

## 3. 重新执行步骤

### Step 1: 环境准备 (Preparation)

```bash
# 1. 确认当前 ZMQ 配置指向远端
grep GTW_HOST /opt/mt5-crs/.env
# 预期输出: GTW_HOST=172.19.141.255 ✅

# 2. 验证远程链路测试脚本
python3 scripts/ops/test_remote_link.py
# 预期输出: SUCCESS 🎉

# 3. 确认 Task #119 的决策哈希
grep "Decision Hash" docs/archive/tasks/TASK_119/TASK_119_COMPLETION_SUMMARY.md
# 预期输出: 1ac7db5b277d4dd1 ✅
```

### Step 2: 金丝雀执行 (Canary Execution)

```bash
# 1. 启动金丝雀策略
python3 src/execution/live_launcher.py --canary-rerun

# 2. 监控实时输出
tail -f VERIFY_LOG.log

# 3. 关键日志查看
grep -E "LAUNCH_APPROVED|DECISION_HASH|ORDER_FILLED|Ticket:" VERIFY_LOG.log
```

### Step 3: 物理验尸 (Physical Evidence)

```bash
# 1. 收集时间戳
date

# 2. 查看订单成交凭证
grep "Ticket:" VERIFY_LOG.log

# 3. 验证账户变化
grep "Balance:" VERIFY_LOG.log

# 4. 查看延迟指标
grep "P99\|Latency" VERIFY_LOG.log
```

### Step 4: 审查与同步 (Review & Sync)

```bash
# 1. 执行 AI 治理审查
python3 scripts/ai_governance/unified_review_gate.py | tee -a VERIFY_LOG.log

# 2. 生成完成报告
# (自动生成)

# 3. 提交到 Git
git add -A
git commit -m "feat(task-119.6): Re-execute canary with verified remote link"
git push origin main
```

---

## 4. 风险控制措施

| 控制项 | 措施 | 阈值 |
|--------|------|------|
| **仓位大小** | 严格限制 | 0.001 lot (10% 系数) |
| **延迟监控** | P99 硬限 | < 100ms (超过警告/熔断) |
| **漂移检测** | PSI 基础 | 每 1 小时检测一次 |
| **电路断路器** | 实时激活 | 异常立即停止 |
| **时间窗口** | 监控期 | 首个 24 小时密集监控 |

---

## 5. 成功标准

✅ **全部满足** 才能视为成功:

1. **链路验证**
   - ✅ 远程 ZMQ 连接成功
   - ✅ MT5 握手包往返成功

2. **决策链**
   - ✅ Decision Hash 验证通过 (1ac7db5b...)
   - ✅ GO 决策状态确认

3. **交易执行**
   - ✅ 金丝雀订单成交
   - ✅ Ticket ID > 0 (真实订单号)
   - ✅ 账户余额更新

4. **运行时护栏**
   - ✅ Guardian 健康状态
   - ✅ 延迟监控激活
   - ✅ 漂移检测循环运行

5. **物理证据**
   - ✅ Deal Ticket 记录
   - ✅ 时间戳准确
   - ✅ 日志完整

---

## 6. 关键数据点

| 项目 | 值 |
|------|-----|
| **源节点 (INF)** | 172.19.141.250 |
| **目标节点 (GTW)** | 172.19.141.255 |
| **ZMQ 端口** | 5555 (REQ-REP) |
| **协议版本** | ZeroMQ with JSON payload |
| **交易账户** | 1100212251 (JustMarkets-Demo2) |
| **初始仓位** | 0.001 lot (10%) |
| **最大杠杆** | 1:3000 |
| **初始余额** | $200 USD |

---

## 7. 应急预案

### 如果 ZMQ 连接失败
```bash
# 1. 检查远程链路
python3 scripts/ops/test_remote_link.py

# 2. 检查防火墙
# Windows GTW 上: netsh advfirewall firewall show rule name="ZMQ-MT5"

# 3. 检查安全组
# 阿里云: sg-t4n0dtkxxy1sxnbjsgk6 允许 5555 端口
```

### 如果订单无法成交
```bash
# 1. 检查 MT5 服务状态
# Windows GTW 上: tasklist | findstr MT5

# 2. 查看 ZMQ 错误码
grep "ERROR\|ERROR_CODE" VERIFY_LOG.log

# 3. 检查账户状态
# MT5 终端检查账户余额和杠杆
```

### 如果延迟超过 100ms
```bash
# 1. 立即停止
python3 scripts/ops/emergency_close_all.py

# 2. 分析原因
grep "P99\|Latency" VERIFY_LOG.log

# 3. 等待系统恢复后重试
```

---

## 8. 时间表

| 阶段 | 时间 | 内容 |
|------|------|------|
| **准备** | 即刻 | 环境检查，前置验证 |
| **执行** | 5 分钟内 | 金丝雀策略启动 |
| **监控** | 首 24 小时 | Guardian 密集监控 |
| **评估** | 24-72 小时 | 性能指标评估 |
| **决策** | 72 小时后 | 确定是否提升仓位 |

---

## 9. 文档交付

本次执行将生成以下文档:

- ✅ EXECUTION_PLAN.md (本文档)
- ✅ LIVE_EXECUTION_LOG.log (实时执行日志)
- ✅ PHYSICAL_EVIDENCE.log (物理证据/Deal Tickets)
- ✅ COMPLETION_REPORT.md (最终完成报告)
- ✅ Git Commit (代码版本记录)

---

## 10. 关键联系方式

| 紧急情况 | 处理步骤 |
|---------|--------|
| **交易出错** | 检查 VERIFY_LOG.log，查看错误码 |
| **系统崩溃** | 激活电路断路器: `emergency_close_all.py` |
| **网络异常** | 运行 `test_remote_link.py` 诊断 |
| **数据不一致** | 检查状态同步日志: `StateReconciler` |

---

**执行状态**: 🟢 **READY TO EXECUTE**
**风险等级**: 🟡 **MEDIUM** (已隔离风险)
**信心度**: ⭐⭐⭐⭐⭐ (5/5 - 完全准备)

---

**更新时间**: 2026-01-17 03:50:00 CST
**Protocol 版本**: v4.3 (Zero-Trust Edition)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
