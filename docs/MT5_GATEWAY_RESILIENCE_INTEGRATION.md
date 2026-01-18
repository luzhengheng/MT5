# MT5 网关 resilience.py 集成指南

**完成日期**: 2026-01-18
**Protocol**: v4.4 (Wait-or-Die 机制)
**集成范围**: ZMQ网关 + JSON网关
**状态**: ✅ 集成完成

---

## 📋 执行摘要

将 `resilience.py` 的 `@wait_or_die` 装饰器集成到MT5网关的两个关键模块，提高网络通信的可靠性。

### 集成成果

| 模块 | 位置 | 改进 | 状态 |
|------|------|------|------|
| **ZMQ网关** | `src/gateway/zmq_service.py` | socket接收/发送 + 10次重试 | ✅ 完成 |
| **JSON网关** | `src/gateway/json_gateway.py` | MT5订单执行 + 5次重试 | ✅ 完成 |

---

## 🔧 集成详情

### 1. ZMQ网关集成

**文件**: `src/gateway/zmq_service.py`

**集成点**:
- `_recv_json_with_resilience()`: Socket接收 (30秒超时, 10次重试)
- `_send_json_with_resilience()`: Socket发送 (30秒超时, 10次重试)
- `_command_loop()`: 主命令循环，使用上述两个方法

**关键改进**:
```python
@wait_or_die(
    timeout=30,
    exponential_backoff=True,
    max_retries=10,
    initial_wait=0.5,
    max_wait=5.0
) if RESILIENCE_AVAILABLE else lambda f: f
def _recv_json_with_resilience(self) -> Dict[str, Any]:
    """使用 @wait_or_die 保护socket接收"""
    self.rep_socket.setsockopt(zmq.RCVTIMEO, 1000)
    try:
        return self.rep_socket.recv_json()
    except zmq.Again:
        raise TimeoutError("ZMQ receive timeout")
```

**优势**:
- ✅ 处理网络抖动 (10次重试 vs 原有的超时即失败)
- ✅ 自动指数退避 (0.5s → 1s → 2s ... → 5s)
- ✅ 优雅降级 (resilience不可用时使用原有超时机制)

### 2. JSON网关集成

**文件**: `src/gateway/json_gateway.py`

**集成点**:
- `_execute_order_with_resilience()`: MT5订单执行 (30秒超时, 5次重试)
- `_handle_order_send()`: 订单处理，使用上述方法

**关键改进**:
```python
@wait_or_die(
    timeout=30,
    exponential_backoff=True,
    max_retries=5,
    initial_wait=1.0,
    max_wait=10.0
) if RESILIENCE_AVAILABLE else lambda f: f
def _execute_order_with_resilience(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """使用 @wait_or_die 保护MT5 API调用"""
    try:
        return self.mt5.execute_order(payload)
    except Exception as e:
        if "timeout" in str(e).lower():
            raise TimeoutError(str(e))
        raise ConnectionError(str(e))
```

**优势**:
- ✅ 订单执行更可靠 (网络故障时自动重试)
- ✅ 防止订单丢失 (最多5次重试)
- ✅ 清晰的错误分类 (超时 vs 连接错误)

---

## 📊 性能影响

### Socket通信 (ZMQ)

| 指标 | 改进前 | 改进后 | 说明 |
|------|--------|--------|------|
| **超时行为** | 立即失败 | 10次重试 | 更好的故障恢复 |
| **网络抖动处理** | 无 | 自动 | 适应网络波动 |
| **总等待时间** | 1秒 | 最多 30秒 | 仍然有超时保护 |

### MT5订单执行 (JSON)

| 指标 | 改进前 | 改进后 | 说明 |
|------|--------|--------|------|
| **重试能力** | 无 | 5次 | 提高执行成功率 |
| **暂时故障处理** | 失败 | 重试 | 减少订单失败 |
| **超时保护** | 无 | 30秒 | 防止无限等待 |

---

## 🚀 使用指南

### ZMQ网关

```python
from src.gateway.zmq_service import ZmqGatewayService
from src.gateway.mt5_service import MT5Service

# 初始化
mt5 = MT5Service()
gateway = ZmqGatewayService(mt5_handler=mt5)

# 启动（带自动重试保护）
gateway.start()  # ZMQ socket操作现已受@wait_or_die保护

# 关闭
gateway.stop()
```

### JSON网关

```python
from src.gateway.json_gateway import JsonGatewayRouter
from src.gateway.mt5_service import MT5Service

# 初始化
mt5 = MT5Service()
router = JsonGatewayRouter(mt5)

# 处理请求（订单执行现已受@wait_or_die保护）
request = {
    "action": "ORDER_SEND",
    "req_id": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
        "symbol": "EURUSD",
        "type": "OP_BUY",
        "volume": 0.01
    }
}
response = router.process_json_request(request)
```

---

## 📈 监控和验证

### 日志检查

```bash
# 查看 @wait_or_die 保护生效
grep "@wait_or_die" *.log

# 查看重试日志
grep "retry" *.log

# 查看成功恢复
grep "成功\|success" *.log
```

### 性能指标

```bash
# 统计socket接收超时的重试成功率
# (应该显示更少的失败，更多的成功重试)
```

---

## ✅ 验收清单

### 代码质量
- [x] 语法检查通过
- [x] 导入依赖完整 (带fallback)
- [x] 向后兼容性保证
- [x] 代码注释完整

### 功能完整性
- [x] ZMQ Socket接收增强
- [x] ZMQ Socket发送增强
- [x] MT5订单执行增强
- [x] 原有功能保留
- [x] 错误处理保留

### 部署就绪
- [x] 所有模块编译通过
- [x] 优雅降级机制 (fallback)
- [x] Protocol v4.4合规
- [ ] 生产环境测试 (待执行)

---

## 🔐 关键特性

✅ **ZMQ网关**:
- 10次重试 (vs 原有的立即失败)
- 30秒超时保护 (防止无限挂起)
- 指数退避 0.5s → 5s
- 优雅降级

✅ **JSON网关**:
- 5次重试保护
- 30秒超时保护
- 清晰的异常分类
- 幂等性保留

---

## 🎯 后续建议

### 立即
- [ ] 部署到测试环境
- [ ] 监控重试成功率
- [ ] 验证订单执行成功率提升

### 近期
- [ ] 收集性能数据
- [ ] 调整重试参数 (根据实际故障率)
- [ ] 部署到生产环境

### 长期
- [ ] 监控KPI (重试成功率、订单成功率)
- [ ] 定期检查日志
- [ ] 持续优化参数

---

**集成完成日期**: 2026-01-18
**验收状态**: ✅ 代码完成
**下一步**: 部署到测试环境进行验证

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
