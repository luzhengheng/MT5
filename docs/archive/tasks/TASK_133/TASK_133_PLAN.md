# TASK #133: ZMQ Message Latency Benchmarking & Baseline Establishment

**任务ID**: Task #133
**协议**: Protocol v4.4 (Autonomous Living System)
**优先级**: HIGH
**依赖**: Task #132 (Infrastructure IP Migration - Completed)
**状态**: PENDING

---

## 📋 任务定义 (Definition)

### 核心目标
建立双轨交易系统(EURUSD.s + BTCUSD.s)的ZMQ消息延迟基线，为后续性能优化提供基准数据。

### 背景分析
- Task #132完成了基础设施IP迁移(172.19.141.255 → 172.19.141.251)
- 双轨激活已验证网络连通性(5/5检查通过)
- 现需建立ZMQ消息延迟的性能基准

### 实质验收标准 (Substance)
- [ ] **延迟测量**: 在10分钟内收集至少1000条REQ-REP消息往返延迟
- [ ] **PUB-SUB性能**: 测量行情推送通道的消息吞吐和延迟
- [ ] **双品种对比**: 分别测试EURUSD.s和BTCUSD.s的延迟差异
- [ ] **统计分析**: 生成P50/P95/P99百分位数报告
- [ ] **物理证据**: 包含UUID + 时间戳 + 完整数据集

---

## 🎯 执行计划 (Execution Plan)

### Step 1: 基础设施与环境
- [ ] 验证Task #132的网络配置仍然有效
- [ ] 准备性能测试环境(开发或生产)
- [ ] 编写基准测试脚本: `scripts/benchmarks/zmq_latency_benchmark.py`

### Step 2: 核心开发
- [ ] 实现REQ-REP延迟测量
- [ ] 实现PUB-SUB吞吐测量
- [ ] 集成@wait_or_die装饰器确保网络弹性

### Step 3: 治理闭环 (dev_loop.sh)
- [ ] [AUDIT]: 双脑审查基准测试代码
- [ ] [SYNC]: 更新中央命令文档
- [ ] [PLAN]: 生成Task #134规划(多品种扩展)
- [ ] [REGISTER]: 推送至Notion获取Page ID

---

## 📊 预期输出

| 指标 | 目标 |
|------|------|
| REQ-REP P50延迟 | <5ms |
| REQ-REP P99延迟 | <20ms |
| PUB-SUB吞吐 | >1000 msgs/sec |
| 测试样本 | ≥1000条消息 |
| 报告行数 | 300+ |

---

## 🎁 交付物

- `scripts/benchmarks/zmq_latency_benchmark.py` (400+ lines)
- `TASK_133_LATENCY_REPORT.md` (300+ lines)
- `zmq_latency_results.json` (Structured data)

---

**下一阶段**: Task #134 - Multi-Symbol Expansion (三轨 or 多轨支持)

