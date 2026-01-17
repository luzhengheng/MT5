# Task #108 快速启动指南

## 概述

此指南帮助你快速启动并验证 Task #108 状态同步机制。

## 前置条件

1. **环境**:
   - Linux 系统 (Ubuntu 20.04+)
   - Python 3.8+
   - ZeroMQ 库 (`pyzmq`)

2. **网络**:
   - Linux Inf 能访问 Windows GTW (172.19.141.255:5555)
   - 防火墙允许 ZMQ REQ/REP 通讯

3. **依赖**:
   ```bash
   pip install pyzmq python-dotenv
   ```

## 快速启动步骤

### 1. 验证导入

确认所有必需的模块都能导入:

```bash
python3 << 'EOF'
from src.live_loop.reconciler import (
    StateReconciler, SyncResponse, AccountInfo, Position,
    SystemHaltException, SyncTimeoutException, SyncResponseException
)
print("✅ All imports successful")
EOF
```

**预期输出**:
```
✅ All imports successful
```

### 2. 运行 TDD 审计 (Gate 1)

执行本地代码审计:

```bash
python3 scripts/audit_task_108.py
```

**预期输出**:
```
[IMPORT_CHECK] ✅ 通过
[STRUCTURE_CHECK] ✅ 通过
[FUNCTIONAL_CHECK] ✅ 通过
[UNIT_TESTS] ✅ 通过
審計總結: 4/4 通過
✅ Gate 1 审计通过
```

### 3. 运行 Phoenix 测试

验证崩溃恢复机制:

```bash
python3 scripts/phoenix_test_task_108.py
```

**预期输出**:
```
[STEP 1] Importing StateReconciler... ✅
[STEP 2] Testing basic initialization... ✅
[STEP 3] Simulating gateway with virtual positions... ✅
[STEP 4] Testing state recovery... ✅
[STEP 5] Simulating crash and recovery... ✅
✅ Phoenix Test PASSED
```

### 4. 测试状态同步 (集成)

创建一个简单的测试脚本:

```python
#!/usr/bin/env python3
from src.live_loop.reconciler import StateReconciler, SyncResponse

# 创建 reconciler 实例
reconciler = StateReconciler()

# 模拟网关响应
mock_response = {
    "status": "OK",
    "account": {
        "balance": 10000.0,
        "equity": 10050.0,
        "margin_free": 9000.0,
        "margin_used": 1000.0,
        "margin_level": 1005.0,
        "leverage": 100
    },
    "positions": [
        {
            "symbol": "EURUSD",
            "ticket": 123456,
            "volume": 0.1,
            "profit": 50.0,
            "price_current": 1.0850,
            "price_open": 1.0800,
            "type": "BUY",
            "time_open": 1705329600
        }
    ],
    "message": "Sync successful"
}

# 解析响应
sync_response = SyncResponse(mock_response)

# 验证
print(f"Status: {sync_response.status}")
print(f"Account Balance: ${sync_response.account.balance}")
print(f"Positions: {len(sync_response.positions)}")
print(f"Position 1: {sync_response.positions[0].symbol} {sync_response.positions[0].volume}@{sync_response.positions[0].price_current}")

assert sync_response.is_ok()
assert sync_response.account.balance == 10000.0
assert len(sync_response.positions) == 1

print("\n✅ State synchronization test passed")
```

运行测试:

```bash
python3 test_sync.py
```

## 与 StrategyEngine 集成

状态同步已经自动集成到 `StrategyEngine` 中。启动时会自动执行：

```python
from src.strategy.engine import StrategyEngine

# 创建引擎（自动触发状态同步）
engine = StrategyEngine(symbol="EURUSD")

# 日志输出：
# [INIT] Performing startup state synchronization...
# [INIT] ✅ State synchronized: 1 positions recovered
```

### 异常处理

如果同步失败，会收到异常:

```python
from src.live_loop.reconciler import SystemHaltException

try:
    engine = StrategyEngine(symbol="EURUSD")
except SystemHaltException as e:
    print(f"❌ Sync failed: {e}")
    # 系统无法启动 - 这是正确的行为
    # 等待网关恢复后重试
```

## 配置

### 环境变量

如果需要自定义配置，在 `.env` 文件中设置：

```bash
# Windows 网关地址
GATEWAY_HOST=172.19.141.255
GATEWAY_PORT=5555

# 同步参数
SYNC_TIMEOUT_S=3
SYNC_RETRY_COUNT=3
SYNC_RETRY_INTERVAL_S=1

# Magic Number (策略标识)
MAGIC_NUMBER=202401
```

## 故障排查

### 问题 1: 连接超时

**症状**: `SyncTimeoutException: Connection timeout`

**原因**: 网关无响应

**解决方案**:
```bash
# 检查网络连接
ping 172.19.141.255

# 检查网关是否运行
nc -zv 172.19.141.255 5555

# 查看网关日志
tail -f /opt/mt5-crs/scripts/gateway/mt5_zmq_server.log
```

### 问题 2: 无效响应格式

**症状**: `SyncResponseException: Invalid response format`

**原因**: 网关返回了意外的 JSON 格式

**解决方案**:
```bash
# 检查网关代码中 _handle_sync_all() 的实现
# 验证返回的 JSON 结构与文档一致

# 启用调试日志
export LOG_LEVEL=DEBUG
python3 -m src.strategy.engine
```

### 问题 3: 系统启动失败

**症状**: `SystemHaltException: Failed after 3 attempts`

**原因**:
- 网关长期离线
- 网络故障
- 持仓恢复失败

**解决方案**:
1. 重启 Windows 网关
2. 检查网络连接
3. 查看完整日志:
   ```bash
   python3 scripts/audit_task_108.py
   cat VERIFY_LOG.log
   ```

## 监控指标

启动后，监控以下指标确保健康运行：

```bash
# 查看同步日志
grep "State synchronized" VERIFY_LOG.log

# 查看恢复的持仓数
grep "positions recovered" VERIFY_LOG.log

# 查看任何同步错误
grep "State synchronization failed" VERIFY_LOG.log

# 统计同步成功率
grep -c "✅ State synchronized" VERIFY_LOG.log
```

## 性能基准

正常运行时的预期性能：

| 指标 | 范围 |
|------|------|
| 同步延迟 | 100-500ms |
| 重试响应 | 500-2000ms |
| 内存占用 | 10-20MB |
| CPU 占用 | <1% |

## 常见问题

**Q: 同步失败会怎样？**

A: 系统会抛出 `SystemHaltException` 异常，阻止启动。这是**正确的行为**——我们不希望系统在未知状态下运行。

**Q: 可以禁用同步吗？**

A: 不建议。同步是确保系统安全性的核心机制。如果必须禁用，需要修改 StrategyEngine 代码。

**Q: 为什么要同步两次（startup + heartbeat）？**

A:
- Startup: 初始化时获取完整状态（blocking gate）
- Heartbeat: 定期验证状态一致性（检测网关故障）

**Q: 持仓丢失会怎样？**

A: 下次启动时会重新从 MT5 恢复。本地内存中的持仓被视为缓存，不是真实来源。

## 高级话题

### 自定义 Magic Number

如果需要为不同的策略使用不同的 Magic Number：

```python
from src.live_loop.reconciler import StateReconciler

reconciler = StateReconciler()
# Magic Number 在 reconciler.py 中定义为常量 MAGIC_NUMBER = 202401
# 修改该常量可以改变策略标识
```

### 监听同步事件

如果需要在状态同步后执行自定义逻辑：

```python
from src.strategy.engine import StrategyEngine

engine = StrategyEngine()

# 同步后的恢复状态在这里
recovered_positions = engine.recovered_state.positions
recovered_account = engine.recovered_state.account

print(f"Recovered {len(recovered_positions)} positions")
print(f"Account balance: ${recovered_account.balance}")

# 在此处添加自定义初始化逻辑
```

### 调试模式

启用详细日志：

```python
import logging

# 在导入前设置
logging.basicConfig(level=logging.DEBUG)

from src.live_loop.reconciler import StateReconciler
from src.strategy.engine import StrategyEngine

# 现在会看到详细的调试日志
reconciler = StateReconciler()
engine = StrategyEngine()
```

## 下一步

1. ✅ 完成快速启动
2. → 阅读 [SYNC_GUIDE.md](./SYNC_GUIDE.md) 学习部署
3. → 查看 [COMPLETION_REPORT.md](./COMPLETION_REPORT.md) 了解技术细节
4. → 参考 [Protocol v4.3](../../protocols/PROTOCOL_V4_3_ZERO_TRUST.md) 了解整体架构

## 支持

遇到问题？

1. 查看 VERIFY_LOG.log 中的完整日志
2. 运行 `python3 scripts/audit_task_108.py` 诊断问题
3. 查看本指南的 "故障排查" 部分

---

**最后更新**: 2026-01-15
**Protocol 版本**: v4.3 (Zero-Trust Edition)
**Status**: ✅ Ready for Production
