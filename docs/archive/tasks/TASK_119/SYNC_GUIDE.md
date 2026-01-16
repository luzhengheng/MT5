# Task #119 部署变更清单 (SYNC_GUIDE)
## Phase 6 Live Canary Deployment

**部署时间**: 2026-01-17T03:07:18Z
**目标环境**: Production (Live Demo Account 1100212251)
**变更影响**: 运行时系统 (RESTART REQUIRED)

---

## 1. 环境变量配置

### 新增环境变量

```bash
# .env 文件新增或更新

# Task #119: Guardian 和 Launcher 配置
TASK_119_CANARY_ENABLED=true
TASK_119_DECISION_HASH_REQUIRED=1ac7db5b277d4dd1
TASK_119_POSITION_COEFFICIENT=0.1
TASK_119_POSITION_MAX_LOT=0.01

# Guardian 漂移监控配置
TASK_119_DRIFT_CHECK_INTERVAL=3600  # 1 hour
TASK_119_DRIFT_PSI_THRESHOLD=0.25
TASK_119_DRIFT_MAX_EVENTS_24H=5

# Guardian 延迟监控配置
TASK_119_LATENCY_CRITICAL_MS=100
TASK_119_LATENCY_WARNING_MS=50
TASK_119_LATENCY_WINDOW_SIZE=100
```

### 验证环境变量
```bash
# 检查是否正确设置
grep "TASK_119\|DECISION_HASH" .env

# 或使用 Python
python3 -c "import os; print({k: v for k, v in os.environ.items() if 'TASK_119' in k or 'HASH' in k})"
```

---

## 2. 代码文件变更

### 新增文件

| 路径 | 大小 | 说明 |
|------|------|------|
| `scripts/audit_task_119.py` | 321 行 | TDD 审计框架 (22 个单元测试) |
| `src/execution/live_guardian.py` | 331 行 | 运行时护栏模块 |
| `src/execution/live_launcher.py` | 372 行 | Phase 6 启动器 & 鉴权 |

### 文件清单

```bash
# 验证新增文件
ls -lh scripts/audit_task_119.py
ls -lh src/execution/live_guardian.py
ls -lh src/execution/live_launcher.py

# 统计代码行数
wc -l scripts/audit_task_119.py src/execution/live_guardian.py src/execution/live_launcher.py

# 预期输出:
#   321 scripts/audit_task_119.py
#   331 src/execution/live_guardian.py
#   372 src/execution/live_launcher.py
#  1024 total
```

### 修改的文件

#### ✅ 无修改
- 现有的 `src/analytics/shadow_autopsy.py` (Task #118)
- 现有的 `src/risk/circuit_breaker.py` (Task #104)
- 现有的 `src/gateway/mt5_client.py` (Task #106)

**说明**: Task #119 使用现有 DriftAuditor、LatencyAnalyzer、CircuitBreaker 组件的接口

---

## 3. 依赖项管理

### Python 依赖 (无新增)

```
已有的依赖项继续使用:
  ✅ pandas (数据处理)
  ✅ numpy (数学计算)
  ✅ pyzmq (ZMQ 网关)
  ✅ pydantic (数据验证)
  ✅ python-dotenv (环境变量)
  ✅ requests (HTTP 客户端)
```

### 验证依赖
```bash
# 确保依赖已安装
python3 -c "import pandas, numpy, zmq, pydantic, dotenv, requests; print('All dependencies OK')"

# 或使用 pip
pip list | grep -E "pandas|numpy|pyzmq|pydantic|python-dotenv"
```

---

## 4. 配置文件变更

### config/risk_limits.yaml (无修改)

现有配置继续有效:

```yaml
# 现有的风险限制继续应用
kill_switch_mode: "auto"
max_daily_drawdown: 0.02      # 2% 硬限
max_account_leverage: 5.0x    # 5x 杠杆限制
max_single_position_size: 1.0 # 1.0 lot 单笔限制
```

**注意**: Task #119 在此基础上新增内存中的 RiskScaler (0.1 系数)

### config/live_strategies.yaml (无修改)

现有策略配置继续有效。Task #119 在运行时增强位置大小计算。

---

## 5. 数据库 & 持久化 (无变更)

### 数据库迁移

无数据库迁移需要。

### 状态持久化

```bash
# Guardian 监控数据保存在内存中
# Circuit Breaker 状态通过文件锁维护
/tmp/mt5_crs_kill_switch.lock  # 电路断路器文件锁

# 重置电路断路器 (如需要)
rm -f /tmp/mt5_crs_kill_switch.lock
```

---

## 6. 日志配置

### 新增日志

Task #119 组件会输出以下日志:

```
[时间戳] [INFO] 🛡️ Live Guardian initialized (Task #119)
[时间戳] [INFO] 🚀 Live Launcher initialized
[时间戳] [INFO] ✅ Decision Hash verified: 1ac7db5b277d4dd1
[时间戳] [INFO] ✅ Authentication PASSED
[时间戳] [INFO] ✅ Canary order FILLED: Ticket #...
```

### 日志文件位置

```bash
VERIFY_LOG.log  # 启动验证日志
# 可选: 重定向到 /var/log/mt5_crs/task_119.log

# 配置日志轮转
# /etc/logrotate.d/mt5_crs (如需)
```

---

## 7. 部署步骤

### 部署前检查清单

```bash
# 1. 备份现有代码
git status
git branch -v

# 2. 验证 Task #118 完成
ls docs/archive/tasks/TASK_118/LIVE_TRADING_ADMISSION_REPORT.md
grep "1ac7db5b277d4dd1" docs/archive/tasks/TASK_118/ADMISSION_DECISION_METADATA.json

# 3. 检查现有依赖
python3 -c "import pandas, numpy, zmq; print('OK')"

# 4. 验证 Gate 1 通过
python3 scripts/audit_task_119.py 2>&1 | grep -E "Tests Run|Passed|Failed"
```

### 部署步骤

```bash
# Step 1: 拉取最新代码或应用文件
# (假设通过 git 或 scp 部署)

# Step 2: 验证文件完整性
ls -lh scripts/audit_task_119.py
ls -lh src/execution/live_guardian.py
ls -lh src/execution/live_launcher.py

# Step 3: 运行 Gate 1 测试
python3 scripts/audit_task_119.py

# Step 4: 设置环境变量
export TASK_119_CANARY_ENABLED=true
export TASK_119_DECISION_HASH_REQUIRED=1ac7db5b277d4dd1

# Step 5: 启动 Phase 6 Canary
python3 src/execution/live_launcher.py

# Step 6: 验证输出包含
# ✅ Decision Hash verified
# ✅ Authentication PASSED
# ✅ Canary order FILLED
# ✅ PHASE 6 LIVE TRADING LAUNCHED SUCCESSFULLY

# Step 7: 后台运行监控 (可选)
# python3 src/execution/live_launcher.py > logs/task_119_live.log 2>&1 &
```

---

## 8. 验证部署

### 部署后验证

```bash
# 检查启动器是否成功
python3 -c "from src.execution.live_launcher import LiveLauncher; \
l = LiveLauncher(); success, report = l.launch(); \
print('✅ LAUNCH SUCCESS' if success else '❌ LAUNCH FAILED'); \
print(f\"Status: {report['canary_order']['details']['status']}\")"

# 检查 Guardian 状态
python3 -c "from src.execution.live_guardian import initialize_guardian; \
g = initialize_guardian(); \
print(f\"Health: {g.get_system_health()}, Should Halt: {g.should_halt()}\")"

# 查看完整报告
python3 src/execution/live_launcher.py 2>&1 | tail -20
```

### 监控命令

```bash
# 1. 监控启动状态
tail -f VERIFY_LOG.log | grep -E "Decision Hash|Authentication|Canary order|HEALTHY"

# 2. 监控 Guardian 健康状态
watch -n 5 'python3 -c "from src.execution.live_guardian import initialize_guardian; \
g = initialize_guardian(); print(f\"Health: {g.get_system_health()}, Errors: {g.critical_error_count}\")"'

# 3. 检查延迟尖峰
watch -n 10 'python3 -c "from src.execution.live_guardian import initialize_guardian; \
g = initialize_guardian(); s = g.latency_detector.get_stats(); \
print(f\"P99: {s[\"p99_latency_ms\"]:.2f}ms, Spikes: {s[\"spike_count\"]}\")"'
```

---

## 9. 回滚程序

### 快速回滚

```bash
# 如需停止 Task #119 操作

# 方法 1: 激活电路断路器
echo "1" > /tmp/mt5_crs_kill_switch.lock

# 方法 2: 杀死进程
pkill -f "live_launcher.py"

# 方法 3: 禁用环境变量
export TASK_119_CANARY_ENABLED=false

# 方法 4: 完整回滚到上一个提交
git revert HEAD  # 或 git reset --hard HEAD~1
```

### 回滚验证

```bash
# 确认已停止
ps aux | grep live_launcher
# 应该没有进程 (或只有 grep 本身)

# 确认电路断路器状态
cat /tmp/mt5_crs_kill_switch.lock 2>/dev/null && echo "Circuit breaker ENGAGED" || echo "Circuit breaker SAFE"

# 确认 Guardian 已停止
# (后台 guardian 会自动停止)
```

---

## 10. 相关部署

### 依赖的已部署组件

```
✅ Task #104 (The Live Loop)
   └─ CircuitBreaker 电路断路器
   └─ LiveEngine 事件循环

✅ Task #105 (Live Risk Monitor)
   └─ RiskMonitor 风险监控
   └─ SecureModuleLoader 安全加载

✅ Task #106 (MT5 Live Connector)
   └─ MT5Client ZMQ 网关
   └─ HeartbeatMonitor 心跳监控

✅ Task #117 & #118 (Shadow Mode & Autopsy)
   └─ ShadowAutopsy 决策引擎
   └─ DriftAuditor 漂移检测
   └─ LatencyAnalyzer 延迟分析
```

### 后续部署

```
→ Task #120 (Production Ramp-Up)
   ├─ 72 小时后评估 Canary 表现
   ├─ 决定是否提升仓位系数 (0.1 → 0.25 → 0.5 → 1.0)
   └─ 部署自动扩大逻辑
```

---

## 11. 故障处理

### 故障场景

| 场景 | 症状 | 解决方案 |
|------|------|---------|
| Hash 不匹配 | `Authentication FAILED` | 检查 Task #118 报告是否存在 |
| Guardian 告警 | `System halt condition active` | 检查电路断路器文件 |
| 延迟尖峰 | `P99 > 100ms` | 检查系统负载, 可能需要调整 |
| ZMQ 连接失败 | `MT5 connection refused` | 检查 MT5 ZMQ 服务器状态 |

---

## 12. 性能基准

### 预期性能

```
启动时间:
  ├─ 认证阶段: ~0.1 秒
  ├─ 验证阶段: ~0.1 秒
  ├─ 执行阶段: ~0.2 秒
  └─ 总计: ~2.5 秒

资源占用:
  ├─ 内存: ~50 MB (Launcher + Guardian)
  ├─ CPU: <5% (基础系统)
  └─ 网络: <1 KB/s (监控数据)

金丝雀仓位:
  ├─ 单笔金额: 0.001 lot (10%)
  ├─ 账户: 1100212251 (JustMarkets-Demo2)
  └─ 杠杆: 1:3000 (根据账户配置)
```

---

## 13. 支持与问题报告

### 获取支持

```bash
# 查看启动日志
cat VERIFY_LOG.log

# 查看完整报告
python3 src/execution/live_launcher.py > debug.log 2>&1

# 查看文档
cat docs/archive/tasks/TASK_119/COMPLETION_REPORT.md
```

### 问题报告

如遇问题，请在 GitHub 中创建 Issue，包含:
- [ ] 启动日志 (VERIFY_LOG.log)
- [ ] 系统信息 (python --version, uname -a)
- [ ] 错误堆栈跟踪 (Python traceback)
- [ ] 时间戳和环境变量

---

**部署日期**: 2026-01-17
**部署验证**: ✅ Gate 1 (22/22) + Gate 2 (PASS)
**准备状态**: 🟢 READY FOR PRODUCTION
