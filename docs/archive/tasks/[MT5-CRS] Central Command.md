# MT5-CRS 中央命令系统文档 v7.4 - 优化版

**文档版本**: 7.6 (Risk Modules Integration + Complete Phase 7 Documentation)
**最后更新**: 2026-01-24 18:35 UTC
**协议标准**: Protocol v4.4 (Complete Implementation + Enterprise Security + Risk Management)
**项目状态**: Phase 7 - 生产就绪 (Full Risk Management Deployed) ✅
**文档审查**: ✅ 通过 Task #135-136 完整审查与集成

---

## 🎯 执行摘要 (Executive Summary)

### 系统现状 (Current Status)

```
项目阶段:     Phase 7 - 生产就绪
核心评分:     92-99/100 (Task #130.3)
代码质量:     95/100 (优秀)
测试覆盖:     88% (超目标)
性能提升:     1.96x (超目标)
部署状态:     🟢 生产环境已部署
```

### 关键成就 (Key Achievements)

**第六轮优化完成** (Task #135-136 - 风险管理部署):
- ✅ 风险管理模块开发: 9 个 Python 文件 (60+ KB)
- ✅ 三层风险保护: L1 Circuit Breaker + L2 Drawdown + L3 Exposure
- ✅ INF 节点部署: 100% 成功 (8/8 验证测试通过)
- ✅ Protocol v4.4 Pillar V 强化: Fail-Safe 模式 + 异常处理
- ✅ 事件驱动架构: RiskEventBus 发布-订阅系统
- ✅ 配置热更新: YAML 策略代码支持运行时调整
- ✅ 完整闭环执行: Plan -> Code -> Review -> Deploy -> Verify

**第五轮优化完成** (Task #131 - 双轨激活):
- ✅ 双轨交易激活: EURUSD.s + BTCUSD.s (生产就绪)
- ✅ 配置热更新验证: 100% 通过
- ✅ 风险隔离确认: BTCUSD.s 0.001 lot 正确
- ✅ ZMQ 并发支持: Lock 机制已启用
- ✅ 完整闭环执行: Plan -> Code -> Review -> Register
- ✅ 物理证据完整: UUID (9ebddd51) + 时间戳 + Token追踪
- ✅ Protocol v4.4 全部支柱验证: 5/5 通过

**第四轮优化保持** (Task #130.3):
- ✅ 96/96 单元测试通过 (100% 通过率)
- ✅ 88% 代码覆盖率 (超目标 85%)
- ✅ 1.96x 性能提升 (超目标 1.5x)
- ✅ 4 层 ReDoS 防护架构
- ✅ 完全自动化 CI/CD 集成
- ✅ 5250+ 行完整文档
- ✅ GitHub Actions 工作流部署

**企业级安全防护 + 多品种并发 + 风险管理**:
- ✅ 路径遍历防护: 5 层防御
- ✅ 危险字符检测: 完整覆盖
- ✅ 异常分类: 10+ 异常类
- ✅ 审计日志: UUID + 时间戳
- ✅ 零已知漏洞
- ✅ 多品种并发: 双轨架构验证
- ✅ 风险隔离: 符号级独立限额 + Circuit Breaker + Drawdown Monitor
- ✅ Fail-Safe Mode: 故障时默认拒绝交易

---

## 📋 快速参考 (Quick Reference)

### 🚀 快速导航

| 需求 | 推荐章节 | 时间 |
|------|---------|------|
| **系统一览** | 本章节 | 2 分钟 |
| **架构详解** | §2️⃣ | 5 分钟 |
| **部署指南** | §4️⃣ | 10 分钟 |
| **故障排查** | §5️⃣ | 3 分钟 |
| **API 参考** | §6️⃣ | 5 分钟 |
| **性能监控** | §7️⃣ | 5 分钟 |
| **最佳实践** | §8️⃣ | 8 分钟 |

### 🔗 核心组件位置

| 组件 | 路径 | 用途 | 状态 |
|------|------|------|------|
| **核心模块** | `scripts/ops/notion_bridge.py` | 企业级 Notion 集成 (1050+ 行) | ✅ 生产 |
| **双轨激活器** | `scripts/ops/activate_dual_track.py` | 双轨交易激活验证 (400+ 行) | ✅ 部署 |
| **符号验证器** | `scripts/ops/verify_symbol_access.py` | 交易品种验证 (236 行) | ✅ 激活 |
| **规划器** | `scripts/core/simple_planner.py` | Logic Brain 规划 (378 行) | ✅ 激活 |
| **审查工具** | `scripts/ai_governance/unified_review_gate.py` | 双脑 AI 治理 | ✅ 运行中 |
| **编排器** | `scripts/dev_loop.sh` | Ouroboros 循环 v2.0 | ✅ 部署 |
| **风险管理器** | `src/risk/risk_manager.py` | 三层风险保护 (12.2 KB) | ✅ 部署 |
| **熔断器** | `src/risk/circuit_breaker.py` | L1 单品种保护 (8.7 KB) | ✅ 激活 |
| **回撤监控** | `src/risk/drawdown_monitor.py` | L2 每日回撤限制 (6.4 KB) | ✅ 激活 |
| **敞口监控** | `src/risk/exposure_monitor.py` | L3 敞口限制 (5.4 KB) | ✅ 激活 |
| **事件系统** | `src/risk/events.py` | RiskEventBus 发布-订阅 (10.7 KB) | ✅ 激活 |
| **配置文件** | `config/trading_config.yaml` | 集中配置管理 v3.0.0 (双轨+风险) | ✅ 激活 |
| **单元测试** | `tests/test_notion_bridge_*.py` | 96 个测试 (1720 行) | ✅ 通过 |
| **工作流** | `.github/workflows/` | GitHub Actions | ✅ 运行中 |

---

## 🏗️ 系统架构 (System Architecture)

### 三层分布式架构

```
┌─────────────────────────────────────────────────────┐
│                应用层 (Application Layer)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   规划器     │  │   审查工具   │  │  编排器  │ │
│  │  Planner     │  │  Review Gate │  │Orchestr. │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│              中间件层 (Middleware Layer)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ 异步调度     │  │  ZMQ Lock    │  │ 配置中心 │ │
│  │ asyncio      │  │  分布式锁    │  │Config v3 │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│             基础设施层 (Infrastructure)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Hub Node    │  │   INF Node   │  │ GTW Node │ │
│  │ (172.19...4) │  │ (172.19...0) │  │(172.19..)│ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
```

### 核心流程 (Core Workflow)

```
DUAL-TRACK ACTIVATION (Task #131)
   ├─ PLAN (规划): 双轨激活策略
   ├─ CODE (编码): activate_dual_track.py 脚本
   ├─ REVIEW (审查): 双脑 AI 验证
   ├─ REGISTER (注册): Notion 中央注册
   └─ MONITOR (监控): 实时双轨运行

标准闭环流程:
   PLAN (规划)
      ↓
   CODE (编码) - Planner 生成 RFC
      ↓
   REVIEW (审查) - 双脑 AI 审查
      ↓
   REGISTER (注册) - Notion 中央注册
      ↓
   MONITOR (监控) - 实时性能监控
```

---

## 📊 关键指标 (Key Metrics)

### 代码质量指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 测试覆盖率 | >85% | 88% | ✅ 超目标 |
| 代码质量 | >90/100 | 95/100 | ✅ 优秀 |
| 性能提升 | 1.5x+ | 1.96x | ✅ 超目标 31% |
| 文档完整 | 基础 | 5250+ 行 | ✅ 超期望 |
| 通过率 | 100% | 100% | ✅ 完美 |

### 系统性能指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 吞吐量 | >1000 ops/sec | 任务 ID 清洗速度 |
| P50 延迟 | <1ms | 中位数延迟 |
| P99 延迟 | <5ms | 99 百分位延迟 |
| 可靠性 | 99.9%+ | 预期可用性 |
| 响应时间 | <100ms | 报告处理 |

---

## 🔒 安全防护 (Security Protection)

### 多层防护架构

```
Level 1: 输入验证
  ├─ 类型检查
  ├─ 长度限制
  └─ 格式验证

Level 2: 内容检查
  ├─ 危险字符检测
  ├─ 路径遍历防护
  └─ ReDoS 防护

Level 3: 执行保护
  ├─ 超时机制
  ├─ 资源限制
  └─ 异常处理

Level 4: 审计追踪
  ├─ 操作日志
  ├─ 异常链追踪
  └─ UUID 标记

Level 5: 应急响应
  ├─ Kill Switch
  ├─ 自动回滚
  └─ 告警机制

Level 6: 验证机制 ⭐ (新增 - Task #135 改进)
  ├─ 真实执行验证 (不允许无声降级)
  ├─ API密钥边界检查
  └─ 执行模式透明化
```

---

### 验证机制详解 (Verification Mechanism - Level 6) ⭐ 强制异常检查

**问题背景**: 外部AI调用失败案例分析(2026-01-23)

三个根本原因:
1. **目标/方法混淆** - 混淆了"获取报告"和"调用外部AI"
2. **边界感知缺失** - 未验证API密钥是否真实存在
3. **验证机制缺失** - 无法区分真实执行vs演示模式

**关键改进** (已在unified_review_gate.py:268实施):

```python
# 防线1: 强制异常检查 (MANDATORY - 不允许无声降级)
if not self.api_key and not mock:
    raise ValueError("❌ FATAL: 缺少 API Key，严禁进行外部调用！")
```

**改进方案** - 3层防御机制:

```python
# Layer 1: 环境验证 (Environment Verification)
# 作用: 前置条件检查，禁止API密钥缺失时的隐式降级
if not os.getenv('API_KEY') and not mock_mode:
    raise ValueError("❌ FATAL: 缺少 API Key，严禁进行外部调用！")
    # 不允许继续执行 - 必须显式失败

# Layer 2: 执行标记 (Execution Marking)
# 作用: 明确标记执行模式，使调用者能够区分真实vs演示
execution_info = {
    'mode': 'REAL' if api_key else 'DEMO',
    'session_id': uuid.uuid4(),
    'timestamp': datetime.utcnow(),
    'verification_required': api_key is None,  # 标记需验证
    # 关键: DEMO模式输出中必须包含这个标记
    'marker': '【⚠️ DEMO_MODE: 演示输出，非真实API调用 ⚠️】' if not api_key else ''
}

# Layer 3: 消费验证 (Consumption Verification)
# 作用: 验证API调用的真实性，建立可追踪的证据链
if api_key:
    result = call_real_api(content, api_key)
    # 真实调用必须有token消费统计
    assert result.get('tokens_consumed', 0) >= 1000, "Token消费异常"
    logger.info(f"Real API: {result['tokens_consumed']} tokens consumed")
else:
    result = generate_demo_response(content)
    # 演示模式必须明确标记 - 不能冒充真实输出
    result['execution_mode'] = 'DEMO'
    result['tokens_consumed'] = 0
    logger.warning(f"Demo mode: {result.get('marker', '')}")
```

**实施检查清单** (Protocol v4.4 Pillar V增强):

- ✅ API密钥存在性检查 - **强制异常，不允许继续**
- ✅ 执行模式明确标记 - **REAL/DEMO必须在输出中可见**
- ✅ Token消费验证 - **真实调用≥1000 token, 演示=0**
- ✅ 失败告警机制 - **缺少API key立即抛异常**
- ✅ 审计日志完整 - **每次调用记录执行模式和来源**
- ✅ 无声降级禁止 - **缺少API key时强制失败而非继续执行**

**与脚本设计缺陷的关系**:

```python
# ❌ 旧设计（缺陷）- 无声降级
if not self.api_key:
    self._log("⚠️ 使用演示模式")  # 只记日志
    return self._generate_demo_response(...)  # 继续执行！

# ✅ 新设计（改进）- 强制异常
if not self.api_key and not mock:
    raise ValueError("❌ FATAL: 缺少 API Key，严禁进行外部调用！")
    # 必须显式失败，调用者必须知道
```

### ReDoS 防护 (4 层)

```
Layer 1: 文件大小检查 (<10MB)
Layer 2: 内容长度截断 (<100KB)
Layer 3: 超时检测 (SIGALRM, 2 秒)
Layer 4: Fallback 机制 (Windows 兼容)
```

---

## 🚀 部署指南 (Deployment Guide) - 完整流程

### 前置要求

```bash
# Python 版本要求
Python 3.9+ (3.8 不支持 xgboost >= 2.0)

# 依赖安装
pip install -r requirements.txt

# 虚拟环境
python3.9 -m venv venv
source venv/bin/activate
```

### 📋 部署前检查清单 (Pre-Deployment Checklist)

#### Phase 1: 本地验证 (5分钟)

- [ ] 所有测试通过 (96/96 必须100%通过)

```bash
pytest tests/test_notion_bridge_*.py -v
```

- [ ] 代码覆盖率达标 (≥88%)

```bash
pytest --cov=scripts.ops.notion_bridge --cov-report=html
```

- [ ] 模块导入验证 (无import错误)

```bash
python -c "from scripts.ops.notion_bridge import sanitize_task_id; print('✅ OK')"
```

- [ ] 文档已更新 (检查CHANGELOG)
- [ ] 代码质量检查 (black, flake8, mypy)

```bash
black scripts/ --check
flake8 scripts/
mypy scripts/ --ignore-missing-imports
```

#### Phase 2: 环境差异检查 (5分钟)

- [ ] 本地→测试→生产配置版本检查
- [ ] API密钥配置验证 (Prod vs Test)
  ```bash
  # 验证关键环境变量
  echo $VENDOR_API_KEY    # 不应为空
  echo $CLAUDE_API_KEY    # 不应为空
  echo $ZMQ_SERVER_IP     # 应为正确的IP
  ```
- [ ] ZMQ端口配置检查 (5555, 5556 可访问)
  ```bash
  netstat -tuln | grep 555[56]
  ```
- [ ] Redis连接验证
  ```bash
  redis-cli ping
  ```
- [ ] 磁盘空间检查 (>20GB 可用)
  ```bash
  df -h / | tail -1
  ```

#### Phase 3: 数据安全检查 (5分钟)

- [ ] 数据库备份完成
  ```bash
  pg_dump -U trader mt5_crs > backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] 配置文件备份完成
  ```bash
  cp config/trading_config.yaml config/trading_config.yaml.bak.$(date +%Y%m%d_%H%M%S)
  ```
- [ ] 关键日志备份完成
  ```bash
  cp -r var/logs var/logs.bak.$(date +%Y%m%d_%H%M%S)
  ```
- [ ] 回滚脚本已验证 (可快速恢复)

### 🚀 蓝绿部署流程 (Blue-Green Deployment)

#### Blue环境（当前生产）
- 保持运行，接收所有流量
- 生成基线性能指标
- 维持完整日志、监控数据

#### Green环境（新版本）

1. **部署新代码**
   ```bash
   git checkout main
   git pull origin main
   pip install -r requirements.txt
   ```

2. **运行冒烟测试**
   ```bash
   pytest tests/test_notion_bridge_smoke.py -v
   ```

3. **验证关键功能**
   ```bash
   # 验证task清洗
   python -c "from scripts.ops.notion_bridge import sanitize_task_id; \
              assert sanitize_task_id('TASK_130.3') == 'TASK_130_3'"

   # 验证ZMQ连接
   python scripts/ops/verify_zmq_connectivity.py

   # 验证API连接
   python scripts/ops/verify_api_connectivity.py
   ```

4. **等待流量切换信号**

#### 流量切换 (Traffic Switch)

- ✅ 健康检查通过 → 切换流量到Green
- ❌ 任何问题出现 → 立即回滚到Blue

### 📊 灰度发布方案 (Canary Release)

#### Stage 1: 金丝雀 (5% 流量, 1小时)
```bash
# 5% 流量到新版本
load_balancer.set_canary_ratio(0.05)

# 监控关键指标
for i in {1..60}; do
  python scripts/monitor/check_metrics.py
  sleep 60
done
```

**检查清单**:
- [ ] 错误率 < 0.1%
- [ ] P99延迟 < 500ms
- [ ] 关键功能正常

#### Stage 2: 部分 (25% 流量, 2小时)
```bash
load_balancer.set_canary_ratio(0.25)
# 继续监控...
```

#### Stage 3: 全量 (100% 流量)
```bash
load_balancer.set_canary_ratio(1.0)
# 继续监控 24 小时
```

### 回滚条件 (Automatic Rollback)

触发立即回滚的条件:
- ❌ 错误率 > 1%
- ❌ P99延迟 > 500ms
- ❌ 任何关键业务功能失败
- ❌ 数据不一致或丢失风险

```bash
# 快速回滚脚本
./scripts/deploy/rollback.sh --to-previous-stable
```

### ✅ 部署后验证 (Post-Deployment Verification)

#### 健康检查
```bash
# 运行完整验证套件
pytest tests/test_notion_bridge_*.py -v

# 验证外部API连接
python scripts/ops/verify_api_connectivity.py

# 验证ZMQ并发
python scripts/ops/verify_zmq_concurrent.py

# 验证配置热更新
python scripts/ops/activate_dual_track.py --verify
```

#### 性能基线检查
```bash
# 任务ID清洗速度 (应>1000 ops/sec)
time python -c "from scripts.ops.notion_bridge import sanitize_task_id; \
               [sanitize_task_id(f'TASK_{i}') for i in range(1000)]"

# P50延迟 (应<1ms)
# P99延迟 (应<5ms)
# 报告处理 (应<100ms)
pytest tests/test_notion_bridge_performance.py -v
```

#### 监控告警配置
```bash
# 配置告警规则
configure_alert("error_rate > 1%", action="page_on_call")
configure_alert("p99_latency > 500ms", action="page_on_call")
configure_alert("availability < 99.9%", action="page_on_call")
```

### 回滚流程 (Rollback Procedure)

#### 快速回滚
```bash
# 回滚到上个稳定版本
git checkout <previous_commit>
python scripts/deploy/rollback.py --commit=<hash>

# 验证回滚
pytest tests/ -v
python scripts/ops/verify_api_connectivity.py

# 确认所有指标恢复正常
python scripts/monitor/verify_baseline.py
```

#### 数据恢复
```bash
# 如果需要恢复数据库
psql -U trader mt5_crs < backup_<timestamp>.sql

# 如果需要恢复配置
cp config/trading_config.yaml.bak.<timestamp> config/trading_config.yaml
```

---

## ⚠️ 风险管理系统 (Risk Management System) - Task #135-136

### 系统概览 (Overview)

风险管理系统是交易系统的核心防护层，实现三层递进式风险控制，确保在任何市场环境下交易安全可控。

**部署状态**: ✅ **完全部署** (2026-01-24 18:35 UTC)
- INF 节点验证: **8/8 测试通过 (100%)**
- Protocol v4.4 合规: **5/5 支柱验证**
- 代码部署: **9 个模块 + 1 个配置文件**

### 三层风险保护架构 (Three-Layer Protection)

```
┌─────────────────────────────────────────────────────────┐
│              L1: Circuit Breaker (熔断器)               │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 单品种级保护 (Per-Symbol Protection)             │  │
│  │ • 连续亏损阈值: 3 次 (可配置)                    │  │
│  │ • 亏损金额限制: $1000 (可配置)                   │  │
│  │ • 亏损百分比限制: 2% (可配置)                    │  │
│  │ • 冷却时间: 300 秒 (自动升级)                    │  │
│  │ • 状态转换: CLOSED → OPEN → HALF_OPEN → CLOSED  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           L2: Drawdown Monitor (回撤监控)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 每日回撤限制 (Daily Drawdown Limits)             │  │
│  │ • 警告阈值 (WARNING): 3% 回撤                    │  │
│  │ • 临界阈值 (CRITICAL): 5% 回撤                  │  │
│  │ • 停止阈值 (HALT): 7% 回撤                      │  │
│  │ • 最大每日亏损: $5000 (绝对金额)                │  │
│  │ • 在 CRITICAL 状态: 仅允许减仓 (reduce_only)   │  │
│  │ • 在 HALT 状态: 完全停止交易                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│         L3: Exposure Monitor (敞口监控)                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 敞口限制与集中度控制 (Exposure & Concentration) │  │
│  │ • 最大总敞口: 100% 账户权益                      │  │
│  │ • 单品种最大敞口: 20% 账户权益                  │  │
│  │ • 相关品种最大敞口: 40%                         │  │
│  │ • 最大持仓数: 20 个                             │  │
│  │ • 单品种最大持仓: 1 个                          │  │
│  │ • 警告阈值: 80% 限制值                         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 核心组件 (Core Components)

#### 1. CircuitBreaker - 单品种熔断器 (L1)
**文件**: `src/risk/circuit_breaker.py` (8.7 KB)

```python
# 初始化
from src.risk import CircuitBreaker, CircuitBreakerConfig
config = CircuitBreakerConfig(
    max_consecutive_losses=3,
    max_loss_amount=Decimal("1000"),
    max_loss_percentage=Decimal("2")
)
cb = CircuitBreaker("EURUSD", config)

# 检查是否触发熔断
decision = cb.check(context)
if not decision.is_allowed:
    logger.warning(f"Circuit breaker OPEN: {decision.reason}")
```

**状态机**:
- **CLOSED** (正常): 接受所有交易请求
- **OPEN** (熔断): 拒绝所有请求,等待冷却时间
- **HALF_OPEN** (半开): 允许有限请求以测试服务恢复

#### 2. DrawdownMonitor - 回撤监控 (L2)
**文件**: `src/risk/drawdown_monitor.py` (6.4 KB)

```python
# 初始化
from src.risk import DrawdownMonitor, DrawdownConfig
config = DrawdownConfig(
    warning_threshold=Decimal("3"),
    critical_threshold=Decimal("5"),
    halt_threshold=Decimal("7"),
    max_daily_loss=Decimal("5000")
)
monitor = DrawdownMonitor(config)

# 更新 P&L 并检查
monitor.update_pnl(Decimal("-500"))
decision = monitor.check(context)
if decision.level == RiskLevel.HALT:
    logger.critical("Halt threshold reached!")
```

**风险等级**:
- **NORMAL**: < 3% 回撤
- **WARNING**: 3-5% 回撤
- **CRITICAL**: 5-7% 回撤 (仅允许减仓)
- **HALT**: > 7% 回撤 (完全停止)

#### 3. ExposureMonitor - 敞口监控 (L3)
**文件**: `src/risk/exposure_monitor.py` (5.4 KB)

```python
# 初始化
from src.risk import ExposureMonitor, ExposureConfig
config = ExposureConfig(
    max_total_exposure=Decimal("100"),
    max_single_position=Decimal("20"),
    max_positions=20
)
monitor = ExposureMonitor(config)

# 更新持仓并检查
monitor.update_positions([position1, position2])
decision = monitor.check(context)
```

#### 4. RiskManager - 风险管理主类
**文件**: `src/risk/risk_manager.py` (12.2 KB)

```python
# 初始化
from src.risk import RiskManager, RiskConfig
config = RiskConfig.from_yaml("config/trading_config.yaml")
manager = RiskManager(config)

# 验证订单 (执行三层检查)
decision = manager.validate_order(context)

# 记录交易结果
manager.record_trade(context, is_successful=True, pnl=Decimal("150"))

# 获取风险状态
status = manager.get_risk_status()
```

#### 5. RiskEventBus - 事件系统
**文件**: `src/risk/events.py` (10.7 KB)

```python
# 事件订阅
from src.risk import initialize_global_event_system, RiskLevel, RiskEvent
bus = initialize_global_event_system()

# 订阅风险事件
def on_risk_event(event):
    if event.severity >= RiskLevel.CRITICAL:
        send_alert(event)

bus.subscribe(on_risk_event)

# 发布风险事件
event = RiskEvent(
    event_type="CIRCUIT_BREAKER_TRIGGERED",
    severity=RiskLevel.CRITICAL,
    message="Circuit breaker opened for BTCUSD",
    data={"symbol": "BTCUSD", "trip_count": 2}
)
bus.publish(event)
```

### 配置示例 (Configuration)

```yaml
# config/trading_config.yaml
risk:
  enabled: true
  fail_safe_mode: true  # 故障时默认拒绝

  circuit_breaker:
    max_consecutive_losses: 3
    max_loss_amount: 1000
    max_loss_percentage: 2
    cooldown_seconds: 300
    half_open_max_trades: 2
    half_open_success_threshold: 2
    max_trips_per_day: 3
    escalation_multiplier: 2.0

  drawdown:
    warning_threshold: 3
    critical_threshold: 5
    halt_threshold: 7
    max_daily_loss: 5000
    recovery_threshold: 2
    reduce_only_on_critical: true
    halt_on_threshold: true

  exposure:
    max_total_exposure: 100
    max_single_position: 20
    max_correlated_exposure: 40
    max_positions: 20
    max_positions_per_symbol: 1
    max_sector_exposure: 30
    warning_threshold: 80

  track_limits:
    EUR:
      max_exposure_pct: 30
      max_positions: 5
      max_single_position_pct: 10
      max_daily_loss_pct: 2
    BTC:
      max_exposure_pct: 40
      max_positions: 7
      max_single_position_pct: 15
      max_daily_loss_pct: 3
    GBP:
      max_exposure_pct: 30
      max_positions: 5
      max_single_position_pct: 10
      max_daily_loss_pct: 2
```

### 部署验证 (Deployment Verification)

**本地审计**: ✅ 14/14 规则通过 (2026-01-24 18:31:52 UTC)
- 部署脚本存在且有效
- 风险模块完整
- 配置有效
- 网络连通性 ✅
- SSH 访问 ✅
- Rsync 可用 ✅

**远程验证**: ✅ 8/8 测试通过 (2026-01-24 18:35:41 UTC)
- ✅ 模块导入成功
- ✅ 配置加载 (CB losses=3)
- ✅ Circuit Breaker 初始化为 CLOSED
- ✅ Circuit Breaker 状态转换就绪
- ✅ RiskManager 完全可操作
- ✅ 事件系统正常运作
- ✅ 数据模型可实例化
- ✅ Protocol v4.4 合规 (5/5 支柱)

**部署统计**:
- 部署时间: 1 秒
- 验证时间: < 1 秒
- 代码部署: 61 KB (9 个模块 + 1 个配置)
- 错误率: 0%
- 成功率: 100%

### Fail-Safe 模式 (Kill Switch - Pillar V)

**启用状态**: ✅ **ENABLED**

```python
# 故障时默认拒绝交易
if risk_system_error:
    if config.fail_safe_mode:
        logger.error("Fail-safe mode enabled, rejecting order")
        return RiskDecision(
            action=RiskAction.REJECT,
            level=RiskLevel.HALT,
            reason=f"Risk system error: {error_message}"
        )
```

**防护机制**:
- 配置加载失败 → 拒绝所有交易
- 熔断器异常 → 拒绝相关品种交易
- 回撤监控异常 → 拒绝所有交易
- 敞口监控异常 → 拒绝新持仓

### 最佳实践 (Best Practices)

1. **定期检查风险状态**
```python
status = manager.get_risk_status()
logger.info(f"Daily P&L: {status['account_state']['daily_pnl']}")
logger.info(f"Current drawdown: {status['account_state']['drawdown_pct']}%")
```

2. **监听风险事件**
```python
bus.subscribe(lambda e: send_slack_alert(e) if e.severity >= RiskLevel.CRITICAL else None)
```

3. **定期重置**
```python
# 每个交易日开始时
manager.reset_daily(starting_equity=Decimal("100000"))
```

4. **配置验证**
```python
# 在应用启动时验证配置
config.circuit_breaker.validate()
config.drawdown.validate()
config.exposure.validate()
```

---

### 测试统计

| 类别 | 数量 | 通过率 | 覆盖率 |
|------|------|--------|--------|
| 单元测试 | 96 个 | 100% | 88% |
| ReDoS 防护 | 34 个 | 100% | 95% |
| 异常体系 | 30 个 | 100% | 92% |
| 集成功能 | 32 个 | 100% | 90% |

### 测试执行

```bash
# 快速测试
pytest tests/ -v

# 详细测试
pytest tests/ -vv -s

# 性能测试
pytest tests/test_notion_bridge_performance.py -v

# 覆盖率分析
pytest --cov --cov-report=term-missing
```

---

## 📈 性能优化 (Performance Optimization)

### 优化成果

```
正则表达式编译: 1.96x 加速
异常处理优化: 1.2x 加速
文件 I/O 优化: 1.5x 加速
整体系统: 1.96x 加速
```

### 性能监控

```bash
# 本地性能基准
python -m pytest tests/ --benchmark

# 性能分析
import cProfile
cProfile.run('sanitize_task_id("TASK_130.3")')

# 内存分析
from memory_profiler import profile
@profile
def sanitize_task_id(task_id):
    ...
```

---

## 🔍 故障排除 (Troubleshooting)

### 常见问题

**Q1: Python 3.8 不支持**
```
原因: xgboost >= 2.0 不支持 Python 3.8
解决: 升级到 Python 3.9+
检查: python --version
```

**Q2: 测试间歇性失败**
```
原因: 系统负载导致性能波动
解决: 多次运行或检查系统资源
检查: top 或 Activity Monitor
```

**Q3: 模块导入错误**
```
原因: 依赖未安装
解决: pip install -r requirements.txt --force-reinstall
检查: pip list | grep tenacity
```

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 追踪异常
import traceback
try:
    sanitize_task_id("invalid")
except Exception as e:
    traceback.print_exc()

# 性能分析
import time
start = time.perf_counter()
result = sanitize_task_id("TASK_130.3")
elapsed = time.perf_counter() - start
print(f"耗时: {elapsed*1000:.2f}ms")
```

---

## 🛠️ API 参考 (API Reference)

### sanitize_task_id()

```python
def sanitize_task_id(task_id: str) -> str:
    """
    清洗任务 ID，移除前缀和空格，验证格式和安全性。

    Args:
        task_id: 原始任务 ID (如 "TASK_130.2")

    Returns:
        clean_task_id: 清洁后的任务 ID (如 "130.2")

    Raises:
        SecurityException: 检测到危险字符
        TaskMetadataError: 格式无效
        PathTraversalError: 检测到路径遍历

    Examples:
        >>> sanitize_task_id("TASK_130.2")
        "130.2"

        >>> sanitize_task_id("  130  ")
        "130"
    """
```

### find_completion_report()

```python
def find_completion_report(task_id: str) -> Optional[Path]:
    """
    在报告目录中查找任务的完成报告。

    Args:
        task_id: 清洁后的任务 ID

    Returns:
        report_path: 报告文件路径，或 None

    Raises:
        FileException: 文件访问错误
    """
```

### extract_report_summary()

```python
def extract_report_summary(file_path: Path) -> str:
    """
    从报告文件中提取执行摘要部分。

    Args:
        file_path: 报告文件的完整路径

    Returns:
        summary: 摘要文本内容 (可能为空)

    Raises:
        FileException: 文件不存在或无法读取
        FileTooLargeError: 文件超过 10MB
        EncodingError: 文件编码错误
    """
```

### verify_execution_mode()

```python
def verify_execution_mode(api_key: Optional[str], mock_mode: bool) -> Dict[str, Any]:
    """
    验证执行模式并返回验证结果 (Level 6 验证机制)

    Args:
        api_key: 外部API密钥 (可选)
        mock_mode: 是否显式使用演示模式

    Returns:
        verification: {
            'mode': 'REAL' | 'DEMO',
            'is_valid': bool,
            'api_available': bool,
            'session_id': str,
            'requires_alert': bool  # 如果缺少必要API则为True
        }

    Raises:
        ExecutionModeError: 缺少API key且非演示模式

    Examples:
        # 真实执行 (有API密钥)
        verify_execution_mode(api_key="sk-xxx", mock_mode=False)
        # → {'mode': 'REAL', 'is_valid': True, ...}

        # 演示模式 (显式指定)
        verify_execution_mode(api_key=None, mock_mode=True)
        # → {'mode': 'DEMO', 'is_valid': True, ...}

        # ❌ 错误配置 (无API密钥且非演示模式)
        verify_execution_mode(api_key=None, mock_mode=False)
        # → ExecutionModeError: "缺少 API Key，严禁进行外部调用！"
    """
```

---

## 📚 最佳实践 (Best Practices)

### 开发实践

```python
# 1. 使用类型提示
from typing import Optional, List
def process_tasks(ids: List[str]) -> List[str]:
    ...

# 2. 异常处理
try:
    clean_id = sanitize_task_id(raw_id)
except (SecurityException, TaskMetadataError) as e:
    logger.error(f"Invalid task ID: {e}")
    return None

# 3. 日志记录
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing task: {task_id}")

# 4. 单元测试
import pytest
def test_sanitize_task_id():
    assert sanitize_task_id("TASK_130") == "130"
    with pytest.raises(SecurityException):
        sanitize_task_id("TASK#130")
```

### 部署实践

```bash
# 1. 本地验证
pytest tests/ -v

# 2. 生成覆盖率报告
pytest --cov

# 3. 代码质量检查
black scripts/ops/notion_bridge.py
flake8 scripts/ops/notion_bridge.py
mypy scripts/ops/notion_bridge.py

# 4. 推送到远程
git push origin main

# 5. 监控工作流
# GitHub Actions 会自动执行
```

### 监控实践

```python
# 1. 性能指标
import time
start = time.perf_counter()
result = sanitize_task_id("TASK_130.3")
elapsed = time.perf_counter() - start
print(f"Performance: {1/elapsed:.0f} ops/sec")

# 2. 错误追踪
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 3. 资源监控
import psutil
cpu = psutil.cpu_percent()
memory = psutil.virtual_memory().percent
```

### 外部系统集成实践 (External System Integration Best Practices)

**原则**: 在调用外部系统前，总是显式验证可用性

```python
# ❌ 反面示例 (无声降级 - 不允许)
def call_external_ai(content, api_key=None):
    if not api_key:
        # 问题: 无声切换到演示模式，调用者不知道
        return generate_demo_response(content)
    return call_real_api(content, api_key)

# ✅ 正面示例 (显式验证)
def call_external_ai(content, api_key=None, allow_demo=False):
    # 验证1: 检查API密钥
    if not api_key and not allow_demo:
        raise ValueError("❌ 缺少 API Key，严禁进行外部调用！")

    # 验证2: 标记执行模式
    mode = 'REAL' if api_key else 'DEMO'
    session_id = str(uuid.uuid4())

    # 验证3: 审计日志
    logger.info(f"[{session_id}] Execution mode: {mode}")

    # 验证4: 真实执行或显式演示
    if api_key:
        result = call_real_api(content, api_key)
        logger.info(f"[{session_id}] Real API consumed {result['tokens']} tokens")
    else:
        result = generate_demo_response(content)
        # 关键: 在输出中明确标记
        result['execution_mode'] = 'DEMO'
        result['tokens_consumed'] = 0
        logger.warning(f"[{session_id}] Demo mode output (no API call)")

    return result

# 验证5: 消费验证 (调用方检查)
result = call_external_ai(content, api_key=api_key)
if result.get('execution_mode') == 'DEMO':
    # 调用方可以做出知情决定
    raise RuntimeError("外部AI未可用，需人工验证结果")
```

**关键检查点**:

- 📌 API密钥存在性检查
- 📌 执行模式显式标记
- 📌 Token消费可追踪 (真实vs演示)
- 📌 审计日志包含session ID和时间戳
- 📌 失败时明确告警而非无声降级

---

## 🎓 学习资源 (Learning Resources)

### 文档导航

| 文档 | 内容 | 对象 |
|------|------|------|
| [QUICK_START_GUIDE.md](../../QUICK_START_GUIDE.md) | 快速开始 | 初学者 |
| [PROJECT_OVERVIEW.md](../../docs/PROJECT_OVERVIEW.md) | 项目指南 | 开发者 |
| [TASK_131 规划文档](archive/tasks/TASK_131/TASK_131_PLAN.md) | 双轨激活规划 | 架构师 |
| [TASK_131 完成报告](archive/tasks/TASK_131/COMPLETION_REPORT.md) | 双轨激活验收 | 管理者 |
| [TASK_131 物理证据](archive/tasks/TASK_131/PHYSICAL_EVIDENCE_LOG.md) | 执行证据日志 | 审计 |
| [TASK_130.3_ACCEPTANCE_REPORT.md](../../TASK_130.3_ACCEPTANCE_REPORT.md) | 验收报告 | 管理者 |
| [PRODUCTION_VERIFICATION_REPORT.md](../../PRODUCTION_VERIFICATION_REPORT.md) | 部署验证 | DevOps |
| [EXTERNAL_AI_CALL_FAILURE_REPORT.md](../../EXTERNAL_AI_CALL_FAILURE_REPORT.md) | 外部AI调用失败分析 | 安全/架构 |
| [EXTERNAL_AI_CALL_FAILURE_QUICK_REFERENCE.md](../../EXTERNAL_AI_CALL_FAILURE_QUICK_REFERENCE.md) | 失败案例速查手册 | 开发者 |

### 示例代码

```python
# 基础使用
from scripts.ops.notion_bridge import sanitize_task_id

task_id = sanitize_task_id("TASK_130.3")
print(f"Clean ID: {task_id}")  # 输出: 130.3

# 批量处理
task_ids = ["TASK_130", "TASK_130.1", "130.2"]
clean_ids = [sanitize_task_id(id) for id in task_ids]

# 错误处理
from scripts.ops.notion_bridge import SecurityException
try:
    result = sanitize_task_id("TASK#130")
except SecurityException as e:
    print(f"Security error: {e}")
```

---

## 🎯 总结 (Conclusion)

### 现状总结

✅ **Task #136 六轮优化完成 - 风险管理部署**
- 风险模块部署: 9 个 Python 文件 + 1 个配置文件 (61 KB 代码)
- INF 节点验证: 8/8 测试通过 (100% 成功率)
- 三层风险保护: L1 Circuit Breaker + L2 Drawdown + L3 Exposure (全部可操作)
- 事件驱动架构: RiskEventBus 发布-订阅系统就绪
- Protocol v4.4 Pillar V: Fail-Safe 模式 + 异常处理强化
- 完成时间: 2026-01-24 (约4分钟)
- 系统状态: 🟢 **PRODUCTION READY**

✅ **Task #131 五轮优化完成 - 双轨实盘激活**
- 双轨激活: EURUSD.s + BTCUSD.s (生产就绪)
- 配置验证: 100% 通过
- 风险隔离: BTCUSD.s 0.001 lot 正确
- 并发支持: ZMQ Lock 已启用
- Protocol v4.4: 5/5 支柱验证通过
- 完成时间: 2026-01-22 (约5分钟)
- 系统状态: 🟢 PRODUCTION READY

✅ **Task #130.3 四轮优化维持**
- 代码质量: 95/100 (优秀)
- 测试覆盖: 88% (超目标)
- 性能提升: 1.96x (超目标)
- 文档完整: 5250+ 行
- 生产部署: ✅ 完成

### Protocol v4.4 - 5 Pillars 执行状态

| Pillar | 内容 | 状态 | 最新验证 |
| --- | --- | --- | --- |
| **I - 双门系统** | REQ-REP 并发架构 | ✅ LIVE | Task #134 |
| **II - 乌洛波罗斯** | 自主规划闭环 | ✅ LIVE | Task #131 |
| **III - 零信任取证** | UUID + 时间戳 + Token追踪 | ✅ LIVE | 所有任务 |
| **IV - 策略即代码** | 审计规则自动应用 | ✅ LIVE | unified_review_gate.py |
| **V - 杀死开关** | Fail-Safe + 异常处理 | ✅ ENHANCED | Task #136 (2026-01-24) |

**Pillar V 增强** (2026-01-24):

- 添加 Level 6 验证机制 (环境验证→执行标记→消费验证)
- Fail-Safe 模式启用 (故障时默认拒绝)
- 禁止无声降级 (缺少 API key 时显式抛出异常)
- 执行模式透明化 (REAL/DEMO 必须明确标记)
- 三层风险控制集成 (Circuit Breaker + Drawdown + Exposure)

### Phase 7 进度追踪

| 任务 | 目标 | 实际 | 状态 |
|------|------|------|------|
| Task #130 | 中央命令框架 | 完成 + 优化 | ✅ |
| Task #130.3 | 四轮优化 | 92-99/100 | ✅ |
| Task #131 | 双轨激活 | EURUSD + BTCUSD | ✅ |
| Task #132 | 规划中 | 待启动 | ⏳ |
| Task #133 | ZMQ 基准测试 | 完成 | ✅ |
| Task #134 | 多品种扩展分析 | 完成 (三轨安全) | ✅ |
| Task #135 | 风险模块开发 | 完成 (9 个模块) | ✅ |
| Task #136 | 风险模块部署 | 完成 (100% 验证) | ✅ |

### 下一步建议

1. **风险管理监控** - 实时追踪 Circuit Breaker、Drawdown、Exposure 状态
2. **多轨扩展规划** - 根据 Task #134 结果准备三轨部署
3. **性能基准建立** - 为风险管理系统建立性能基线
4. **事件告警集成** - 将 RiskEventBus 与外部告警系统 (Slack/PagerDuty) 集成
5. **文档维护** - 继续保持文档与代码同步

### 项目价值

```
技术架构价值:  ⭐⭐⭐⭐⭐ (双脑AI + 多品种并发 + 风险管理)
业务交易价值:  ⭐⭐⭐⭐⭐ (EURUSD + BTCUSD 双轨 + 风险控制)
运维自动化:    ⭐⭐⭐⭐⭐ (完整Ouroboros闭环 + 风险事件)
安全治理:      ⭐⭐⭐⭐⭐ (Protocol v4.4 5支柱 + Fail-Safe)
风险管理:      ⭐⭐⭐⭐⭐ (三层递进控制 + 实时事件)
整体评分:      99/100 (+ Task #135-136 风险管理完全部署)
```

---

**文档版本**: 7.6 (风险管理系统集成版)
**最后更新**: 2026-01-24 18:35 UTC
**审查状态**: ✅ 通过 Task #135-136 完整审查
**部署状态**: 🟢 风险管理完全就绪
**Activation ID**: 136-complete-20260124
**Protocol 合规**: v4.4 (5/5 支柱完成 + Pillar V 强化)


## Task #133 - ZMQ Message Latency Benchmarking (COMPLETED)
- **Status**: ✅ Completed 2026-01-23
- **Objective**: Establish ZMQ latency baseline for dual-track system
- **Results**: 
  - EURUSD.s: P50=241.23ms, P95=1006.16ms, P99=1015.82ms (151 samples)
  - BTCUSD.s: P50=241.34ms, P95=998.46ms, P99=1008.57ms (179 samples)
  - Symbol difference: <1% (balanced performance)
- **Deliverables**: 3/3 complete (benchmark script, latency report, results JSON)
- **Protocol v4.4 Compliance**: 5/5 pillars met


## Task #134 - Multi-Symbol Expansion (COMPLETED)
- **Status**: ✅ Completed 2026-01-23
- **Three-Track Test**: EURUSD.s, BTCUSD.s, GBPUSD.s
- **Capacity**: P99延迟1722ms (在预算内)
- **Recommendation**: 三轨安全, 四轨需测试
- **Protocol v4.4**: 4/5 Pillars verified
