# Task #106 - MT5 实盘连接器架构设计

## 1. 架构概述

### 1.1 核心目标
构建连接 Linux 推理节点 (Inf) 与 Windows 交易网关 (GTW) 的**双向零信任桥梁**，实现策略信号到 MT5 订单的毫秒级转换。

### 1.2 架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                         Linux Inf Node                             │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │               MT5 Live Connector (NEW)                        │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │  1. Signal Reception (from Strategy Engine)            │  │ │
│  │  │  2. Risk Validation (RiskMonitor - Task #105)          │  │ │
│  │  │  3. ZMQ Communication (send order / receive status)    │  │ │
│  │  │  4. State Synchronization (account/position flow back) │  │ │
│  │  │  5. Heartbeat Monitor (Ping/Pong - 5s timeout)         │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              ▲  ▼ ZMQ (REQ/REP + PUB/SUB)          │
└──────────────────────────────┼──┼─────────────────────────────────┘
                               │  │
                               │  │ Port 5555
                               │  │
┌──────────────────────────────┼──┼─────────────────────────────────┐
│                         Windows GTW Node                           │
│  ┌──────────────────────────┼──┼──────────────────────────────┐  │
│  │       MT5 ZMQ Server     │  │                               │  │
│  │  ┌───────────────────────▼──▼────────────────────────────┐ │  │
│  │  │  1. ZMQ REP Socket (receive order request)           │ │  │
│  │  │  2. MT5 API Call (mt5.order_send)                    │ │  │
│  │  │  3. Response Builder (ticket/price/status)           │ │  │
│  │  │  4. ZMQ PUB Socket (stream account/position updates) │ │  │
│  │  │  5. Auto-reconnect (handle MT5 disconnection)        │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │  │                                  │
│                              ▼  ▼                                  │
│                        MT5 Terminal (Real)                         │
└────────────────────────────────────────────────────────────────────┘
```

## 2. 现有代码复用

### 2.1 已有组件（无需重写）

| 组件 | 路径 | 功能 | 状态 |
|------|------|------|------|
| MT5Bridge | `src/connection/mt5_bridge.py` | 完整的 MT5 API 封装 | ✅ 可复用 |
| MT5Client | `src/gateway/mt5_client.py` | ZMQ 客户端（REQ/REP） | ✅ 可复用 |
| MT5Service | `src/gateway/mt5_service.py` | 单例 MT5 连接管理 | ✅ 可复用 |
| GTWAdapter | `scripts/execution/adapter.py` | ZMQ 协议定义 | ✅ 可扩展 |
| RiskMonitor | `src/execution/risk_monitor.py` | 风险监控（Task #105） | ✅ 必须集成 |
| CircuitBreaker | `src/risk/circuit_breaker.py` | 熔断器（Task #104） | ✅ 必须集成 |

### 2.2 新增组件（Task #106 交付）

| 组件 | 路径 | 功能 | 优先级 |
|------|------|------|--------|
| **MT5LiveConnector** | `src/execution/mt5_live_connector.py` | Linux 端统一连接器 | **P0** |
| **MT5ZmqServer** | `scripts/gateway/mt5_zmq_server.py` | Windows 端 ZMQ 服务器 | **P0** |
| **HeartbeatMonitor** | `src/execution/heartbeat_monitor.py` | 心跳探测器（5s 超时） | **P0** |
| **ProtocolSchema** | `config/mt5_protocol.yaml` | ZMQ 通讯协议定义 | P1 |
| **VerifyScript** | `scripts/verify/verify_mt5_bridge.py` | 物理验证脚本 | P1 |
| **AuditScript** | `scripts/audit_task_106.py` | Gate 1 审计脚本 | P1 |

## 3. 协议设计（Inf ↔ GTW）

### 3.1 请求协议（REQ → REP）

#### 3.1.1 PING（心跳探测）
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "action": "PING",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**响应**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ok",
  "server_time": "2026-01-15T02:08:34.234567Z",
  "latency_ms": 0.111
}
```

#### 3.1.2 OPEN（开仓）
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440001",
  "action": "OPEN",
  "symbol": "EURUSD",
  "type": "BUY",
  "volume": 0.01,
  "price": 0.0,
  "sl": 1.05000,
  "tp": 1.06000,
  "comment": "SentimentMomentum_v1",
  "risk_signature": "RISK_PASS:7a3f9e8b:2026-01-15T02:08:33Z",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**响应**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440001",
  "status": "FILLED",
  "ticket": 12345678,
  "symbol": "EURUSD",
  "volume": 0.01,
  "price": 1.05230,
  "execution_time": "2026-01-15T02:08:34.234567Z",
  "latency_ms": 1.234
}
```

**错误响应**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440001",
  "status": "REJECTED",
  "error_code": "INSUFFICIENT_MARGIN",
  "error_msg": "Not enough margin to open position",
  "timestamp": "2026-01-15T02:08:34.234567Z"
}
```

#### 3.1.3 CLOSE（平仓）
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440002",
  "action": "CLOSE",
  "ticket": 12345678,
  "symbol": "EURUSD",
  "volume": 0.01,
  "timestamp": "2026-01-15T02:10:00.123456Z"
}
```

#### 3.1.4 GET_ACCOUNT（账户查询）
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440003",
  "action": "GET_ACCOUNT",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**响应**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440003",
  "status": "ok",
  "balance": 100000.00,
  "equity": 100500.50,
  "margin": 500.00,
  "free_margin": 99500.50,
  "margin_level": 20100.1,
  "currency": "USD",
  "timestamp": "2026-01-15T02:08:34.234567Z"
}
```

#### 3.1.5 GET_POSITIONS（持仓查询）
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440004",
  "action": "GET_POSITIONS",
  "symbol": "EURUSD",
  "timestamp": "2026-01-15T02:08:34.123456Z"
}
```

**响应**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440004",
  "status": "ok",
  "positions": [
    {
      "ticket": 12345678,
      "symbol": "EURUSD",
      "type": "BUY",
      "volume": 0.01,
      "open_price": 1.05230,
      "current_price": 1.05280,
      "profit": 5.00,
      "open_time": "2026-01-15T02:08:34.234567Z"
    }
  ],
  "timestamp": "2026-01-15T02:08:35.123456Z"
}
```

### 3.2 流式协议（PUB → SUB）【可选，未来优化】

用于实时推送账户状态变化（避免轮询），降低延迟。

```json
{
  "type": "ACCOUNT_UPDATE",
  "balance": 100000.00,
  "equity": 100500.50,
  "margin_level": 20100.1,
  "timestamp": "2026-01-15T02:08:34.234567Z"
}
```

```json
{
  "type": "POSITION_UPDATE",
  "ticket": 12345678,
  "symbol": "EURUSD",
  "current_price": 1.05280,
  "profit": 5.00,
  "timestamp": "2026-01-15T02:08:35.234567Z"
}
```

## 4. 零信任验证（Risk Signature）

### 4.1 Risk Signature 生成

**强制要求**: 所有 `OPEN` 指令必须携带 `risk_signature` 字段，格式为：

```
RISK_PASS:<checksum>:<timestamp>
```

生成逻辑（在 Linux Inf 端）:
```python
from src.execution.risk_monitor import RiskMonitor

risk_monitor = RiskMonitor(...)
order_dict = {
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.01,
    ...
}

# 风险检查
is_safe, signature = risk_monitor.validate_order(order_dict)
if not is_safe:
    raise RuntimeError("Order rejected by RiskMonitor")

# 将 signature 附加到 ZMQ 请求
zmq_request["risk_signature"] = signature
```

### 4.2 Windows GTW 端验证

**强制要求**: Windows 端必须验证 `risk_signature`：
1. 检查是否存在
2. 检查时间戳（误差 < 2 秒）
3. 检查 checksum（基于 order_dict 的 hash）

如果验证失败，GTW 必须拒绝执行并返回 `REJECTED`。

## 5. 心跳探测机制（Kill Switch Trigger）

### 5.1 探测逻辑

Linux Inf 端每 **5 秒** 发送一次 PING：
```python
import time

while True:
    try:
        response = mt5_live_connector.ping()
        if response["status"] != "ok":
            raise ConnectionError("PING failed")
    except Exception as e:
        logger.error(f"Heartbeat失败: {e}")
        # 触发 Kill Switch
        circuit_breaker.engage("HEARTBEAT_FAILURE")
        break

    time.sleep(5)
```

### 5.2 超时处理

如果连续 **3 次** PING 超时（15 秒内无响应）：
1. 触发 `CircuitBreaker.engage("HEARTBEAT_FAILURE")`
2. 停止所有新订单
3. 记录错误日志
4. 可选：发送告警（邮件/钉钉）

## 6. TDD 测试策略

### 6.1 单元测试（scripts/tests/test_mt5_live_connector.py）

- 测试 1: `test_ping_success` - 心跳成功
- 测试 2: `test_ping_timeout` - 心跳超时（触发熔断）
- 测试 3: `test_order_with_risk_pass` - 带有风险签名的订单
- 测试 4: `test_order_without_risk_signature` - 缺少签名（应拒绝）
- 测试 5: `test_order_execution_success` - 订单成功执行
- 测试 6: `test_order_execution_rejected` - 订单被 MT5 拒绝
- 测试 7: `test_account_sync` - 账户状态同步
- 测试 8: `test_position_sync` - 持仓状态同步
- 测试 9: `test_zmq_reconnect` - ZMQ 重连机制

### 6.2 集成测试（scripts/verify/verify_mt5_bridge.py）

使用 **Mock MT5 Server** 模拟 Windows GTW：
1. 启动 Mock Server（监听 5555 端口）
2. Linux Connector 发送 PING → 验证响应
3. Linux Connector 发送 OPEN → 验证 FILLED 响应
4. 验证日志包含：`[RISK_PASS]`, `[ZMQ_SENT]`, `[MT5_FILLED]`

## 7. 部署架构

### 7.1 Linux Inf 端

```bash
# 启动 MT5 Live Connector
python3 src/execution/mt5_live_connector.py --mode=production

# 日志输出到
/var/log/mt5_crs/mt5_live_connector.log
```

### 7.2 Windows GTW 端

```bash
# 启动 MT5 ZMQ Server
python mt5_zmq_server.py --port=5555 --mt5-login=xxx --mt5-password=xxx

# 日志输出到
C:\mt5_crs\logs\mt5_zmq_server.log
```

## 8. 安全约束

1. **强制 Risk Validation**: 所有订单必须经过 RiskMonitor 验证
2. **Signature Expiry**: risk_signature 有效期 2 秒
3. **IP Whitelist**: GTW 仅接受来自 Inf 节点的连接（172.19.141.250）
4. **TLS 加密**（可选）: ZMQ 支持 CurveZMQ 加密
5. **Audit Log**: 所有订单必须记录到 `VERIFY_LOG.log`

## 9. 性能指标

| 指标 | 目标 | 验收标准 |
|------|------|----------|
| PING 延迟 | < 10ms | 99% 请求 < 10ms |
| 订单执行延迟 | < 50ms | 95% 请求 < 50ms |
| 心跳检测周期 | 5s | 固定 5s |
| 订单成功率 | > 99% | 排除市场拒绝 |
| ZMQ 重连时间 | < 2s | 自动重连 < 2s |

## 10. 交付清单

### 10.1 核心代码
- [ ] `src/execution/mt5_live_connector.py` (Linux 连接器)
- [ ] `scripts/gateway/mt5_zmq_server.py` (Windows 服务器)
- [ ] `src/execution/heartbeat_monitor.py` (心跳监控器)

### 10.2 配置文件
- [ ] `config/mt5_protocol.yaml` (协议定义)
- [ ] `config/mt5_connection.yaml` (连接配置)

### 10.3 测试代码
- [ ] `scripts/tests/test_mt5_live_connector.py` (单元测试)
- [ ] `scripts/tests/test_zmq_protocol.py` (协议测试)
- [ ] `scripts/verify/verify_mt5_bridge.py` (物理验证)

### 10.4 审计脚本
- [ ] `scripts/audit_task_106.py` (Gate 1 审计)

### 10.5 四大金刚
- [ ] `docs/archive/tasks/TASK_106_MT5_BRIDGE/COMPLETION_REPORT.md`
- [ ] `docs/archive/tasks/TASK_106_MT5_BRIDGE/QUICK_START.md`
- [ ] `docs/archive/tasks/TASK_106_MT5_BRIDGE/VERIFY_LOG.log`
- [ ] `docs/archive/tasks/TASK_106_MT5_BRIDGE/SYNC_GUIDE.md`

---

**架构版本**: v1.0
**作者**: Claude Sonnet 4.5
**日期**: 2026-01-15
**Protocol**: v4.3 (Zero-Trust Edition)
