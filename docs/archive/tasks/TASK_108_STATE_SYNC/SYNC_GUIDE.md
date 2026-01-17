# Task #108 部署同步指南

## 概述

此文档记录 Task #108 引入的所有部署变更，便于同步到其他环境。

## 环境变量 (ENV)

### 新增环境变量

```bash
# 网关配置
export GATEWAY_HOST=172.19.141.255
export GATEWAY_PORT=5555

# 同步参数
export SYNC_TIMEOUT_S=3
export SYNC_RETRY_COUNT=3
export SYNC_RETRY_INTERVAL_S=1

# 策略标识
export MAGIC_NUMBER=202401
```

### 环境变量验证

```bash
# 检查是否设置正确
echo "GATEWAY_HOST=$GATEWAY_HOST"
echo "GATEWAY_PORT=$GATEWAY_PORT"
echo "SYNC_TIMEOUT_S=$SYNC_TIMEOUT_S"
```

## 依赖包 (Dependencies)

### Python 依赖

新增或更新的包：

```bash
# ZeroMQ Python 绑定
pip install pyzmq>=23.0

# 标准库 (Python 3.8+ 已内置)
# - threading
# - zmq
# - json
# - logging
# - time
# - dataclasses
```

### 安装命令

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或仅安装新增包
pip install pyzmq>=23.0
```

### 依赖检查

```bash
# 验证 pyzmq 安装
python3 -c "import zmq; print(f'ZMQ version: {zmq.zmq_version()}')"

# 验证导入
python3 -c "from src.live_loop.reconciler import StateReconciler; print('OK')"
```

## 文件系统 (Files)

### 新增文件

```
src/live_loop/
├── __init__.py                          (已存在)
├── reconciler.py                        ⭐ NEW (656 行)
└── main.py                              (已存在)

scripts/
├── audit_task_108.py                    ⭐ NEW (525+ 行)
└── phoenix_test_task_108.py             ⭐ NEW (330+ 行)

docs/archive/tasks/TASK_108_STATE_SYNC/
├── COMPLETION_REPORT.md                 ⭐ NEW
├── QUICK_START.md                       ⭐ NEW
├── SYNC_GUIDE.md                        ⭐ NEW (此文件)
└── VERIFY_LOG.log                       ⭐ NEW

tests/
└── test_state_reconciler.py             ⭐ NEW (自动生成)
```

### 修改的文件

```
src/strategy/engine.py
├── 导入: from src.live_loop.reconciler import StateReconciler, SystemHaltException
├── __init__(): 新增 reconciler 初始化和 perform_startup_sync() 调用
└── 修改行数: +15 行

scripts/gateway/mt5_zmq_server.py
├── 新增方法: _handle_sync_all() (130 行)
├── 修改方法: _process_request() (添加 SYNC_ALL 路由)
└── 修改行数: +135 行
```

## 部署步骤 (Deployment Steps)

### 1. 代码同步

```bash
# 进入项目目录
cd /opt/mt5-crs

# 拉取最新代码
git pull origin main
# 或
git pull origin feat/task-108

# 确认代码已更新
git log -1 --oneline
# 应显示: feat(task-108): State Synchronization & Crash Recovery...
```

### 2. 环境准备

```bash
# 设置环境变量
export GATEWAY_HOST=172.19.141.255
export GATEWAY_PORT=5555
export SYNC_TIMEOUT_S=3
export SYNC_RETRY_COUNT=3
export MAGIC_NUMBER=202401

# 或写入 .env 文件
cat > .env << 'EOF'
GATEWAY_HOST=172.19.141.255
GATEWAY_PORT=5555
SYNC_TIMEOUT_S=3
SYNC_RETRY_COUNT=3
SYNC_RETRY_INTERVAL_S=1
MAGIC_NUMBER=202401
EOF

# 加载 .env
set -a
source .env
set +a
```

### 3. 依赖安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 或仅安装新增包
pip install pyzmq>=23.0

# 验证
python3 -c "import zmq; print(f'ZMQ {zmq.zmq_version()}')"
```

### 4. 验证配置

```bash
# 运行 TDD 审计
python3 scripts/audit_task_108.py

# 预期输出:
# [IMPORT_CHECK] ✅ 通过
# [STRUCTURE_CHECK] ✅ 通过
# [FUNCTIONAL_CHECK] ✅ 通过
# [UNIT_TESTS] ✅ 通过
# 审计总结: 4/4 通过
```

### 5. 验证网络连接

```bash
# 检查到网关的连接
nc -zv 172.19.141.255 5555

# 或使用 Python
python3 << 'EOF'
import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.setsockopt(zmq.LINGER, 0)
sock.connect('tcp://172.19.141.255:5555')
print("✅ Connected to gateway")
sock.close()
ctx.term()
EOF
```

### 6. 运行 Phoenix 测试

```bash
# 测试崩溃恢复机制
python3 scripts/phoenix_test_task_108.py

# 预期输出:
# [STEP 1] Importing StateReconciler... ✅
# [STEP 2] Testing basic initialization... ✅
# [STEP 3] Simulating gateway with virtual positions... ✅
# [STEP 4] Testing state recovery... ✅
# [STEP 5] Simulating crash and recovery... ✅
# ✅ Phoenix Test PASSED
```

### 7. 启动策略引擎

```bash
# 直接运行
python3 -m src.strategy.engine

# 或使用部署脚本
bash deploy/start_strategy_engine.sh

# 预期日志输出:
# [INIT] Strategy Engine initialized for EURUSD
# [INIT] Performing startup state synchronization...
# [INIT] ✅ State synchronized: X positions recovered
# [INIT] Model: models/xgboost_price_predictor.json
```

## 回滚计划 (Rollback)

### 快速回滚

如果需要回滚到之前版本：

```bash
# 方法 1: 回滚到上一个提交
git revert HEAD

# 方法 2: 硬重置 (谨慎使用)
git reset --hard HEAD~1

# 重启应用
systemctl restart mt5-strategy-engine
```

### 备份恢复

```bash
# 备份当前代码
cp -r src/live_loop src/live_loop.backup
cp -r scripts/gateway scripts/gateway.backup

# 还原备份
rm -rf src/live_loop scripts/gateway
mv src/live_loop.backup src/live_loop
mv scripts/gateway.backup scripts/gateway
```

## 验证清单 (Verification Checklist)

部署完成后，请验证以下项目：

- [ ] Git 代码已更新 (`git log` 显示 Task #108 提交)
- [ ] 环境变量已设置 (`echo $GATEWAY_HOST`)
- [ ] 依赖已安装 (`pip show pyzmq`)
- [ ] 导入验证成功 (`python3 scripts/audit_task_108.py`)
- [ ] 网络连接正常 (`nc -zv 172.19.141.255 5555`)
- [ ] Phoenix 测试通过 (`python3 scripts/phoenix_test_task_108.py`)
- [ ] 策略引擎启动成功 (查看日志中的 INIT 信息)
- [ ] 状态同步成功 (查看日志中的 "State synchronized")

## 监控和告警 (Monitoring)

### 关键指标

监控以下指标：

```bash
# 启动状态同步成功
grep "State synchronized" VERIFY_LOG.log | wc -l

# 同步恢复的持仓数
grep "positions recovered" VERIFY_LOG.log | tail -1

# 任何同步错误
grep "State synchronization failed" VERIFY_LOG.log | wc -l

# 连接错误
grep "Connection failed" VERIFY_LOG.log | wc -l
```

### 告警规则

配置告警触发条件：

- ⚠️ **同步失败**: 连续 2 次启动同步失败
- ⚠️ **持仓不一致**: 恢复持仓数与 MT5 不符
- ⚠️ **网络中断**: 10 秒无网关响应
- ⚠️ **异常崩溃**: 系统非正常关闭

## 性能基准 (Baseline)

部署后的预期性能：

| 指标 | 预期值 | 告警阈值 |
|------|--------|----------|
| 启动同步延迟 | 100-500ms | > 3000ms |
| 重试响应时间 | 1-2s | > 9s |
| 内存占用 | 10-20MB | > 50MB |
| CPU 占用 | <1% | > 5% |
| 持仓恢复准确率 | 100% | < 100% |

## 常见问题 (FAQ)

### Q: 如何在 Windows 环境中部署？

A: Task #108 分两部分：
- **Linux (Inf)**: `reconciler.py` - 发送 SYNC_ALL 请求
- **Windows (GTW)**: `mt5_zmq_server.py` - 处理请求

Windows 网关已在 Task #106 部署。此任务主要是 Linux 端的变更。

### Q: 如何处理同步超时？

A: 系统会自动重试最多 3 次，间隔 1 秒。如果仍然失败：
1. 检查网络连接
2. 重启 Windows 网关
3. 增加 `SYNC_TIMEOUT_S` (不推荐)

### Q: 可以禁用同步吗？

A: 不建议。同步是安全机制的核心。如果确实需要，修改 `src/strategy/engine.py` 删除 `perform_startup_sync()` 调用。

### Q: 为什么系统拒绝启动？

A: `SystemHaltException` 抛出意味着：
- 无法连接到网关
- 网关响应超时
- 响应格式错误

这是**正确的行为**，确保系统不在未知状态下运行。

### Q: 如何自定义同步参数？

A: 修改 `.env` 文件或环境变量：
```bash
SYNC_TIMEOUT_S=5          # 增加超时
SYNC_RETRY_COUNT=5        # 增加重试次数
SYNC_RETRY_INTERVAL_S=2   # 增加重试间隔
```

## 相关文档

| 文档 | 用途 |
|------|------|
| [完成报告](./COMPLETION_REPORT.md) | 技术细节和成果总结 |
| [快速启动](./QUICK_START.md) | 快速验证步骤 |
| [验证日志](./VERIFY_LOG.log) | 审计和测试记录 |
| [Protocol v4.3](../../protocols/PROTOCOL_V4_3_ZERO_TRUST.md) | 整体架构 |
| [基础设施档案](../../asset_inventory.md) | 系统架构拓扑 |

---

**文档生成**: 2026-01-15
**Protocol 版本**: v4.3 (Zero-Trust Edition)
**最后更新**: Task #108 完成
