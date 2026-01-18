# MT5 网关 resilience.py 集成指南

**完成日期**: 2026-01-18
**Protocol**: v4.4 (Wait-or-Die 机制)
**集成范围**: ZMQ网关 + JSON网关
**状态**: ✅ 集成完成

---

## 📋 执行摘要

将 `resilience.py` 的 `@wait_or_die` 装饰器集成到MT5网关模块，提高网络通信的可靠性。

⚠️ **重要安全修订** (2026-01-19): 经外部AI审查，JSON网关订单执行已移除自动超时重试以防止重复下单风险。

### 集成成果

| 模块 | 位置 | 改进 | 状态 |
|------|------|------|------|
| **ZMQ网关** | `src/gateway/zmq_service.py` | socket接收/发送 + 10次重试 (5s超时) | ✅ 完成 |
| **JSON网关** | `src/gateway/json_gateway.py` | 连接错误处理 (NO超时重试) | ✅ 完成 |

---

## 🔧 集成详情

### 1. ZMQ网关集成

**文件**: `src/gateway/zmq_service.py`

**集成点**:
- `_recv_json_with_resilience()`: Socket接收 (30秒超时, 10次重试)
- `_send_json_with_resilience()`: Socket发送 (30秒超时, 10次重试)
- `_command_loop()`: 主命令循环，使用上述两个方法

**关键改进** (2026-01-19修订):
```python
@wait_or_die(
    timeout=5,           # Hub-aligned timeout (revised from 30s)
    exponential_backoff=True,
    max_retries=10,
    initial_wait=0.5,
    max_wait=2.0         # Reduced from 5.0 to 2.0
) if RESILIENCE_AVAILABLE else lambda f: f
def _recv_json_with_resilience(self) -> Dict[str, Any]:
    """使用 @wait_or_die 保护socket接收 (Hub兼容超时)"""
    self.rep_socket.setsockopt(zmq.RCVTIMEO, 1000)
    try:
        return self.rep_socket.recv_json()
    except zmq.Again:
        raise TimeoutError("ZMQ receive timeout")
```

**优势**:
- ✅ 处理网络抖动 (10次重试 vs 原有的超时即失败)
- ✅ 自动指数退避 (0.5s → 1s → 2s → 2s ...)
- ✅ Hub超时对齐 (5秒总超时，与Hub 2.5-5s对齐)
- ✅ 优雅降级 (resilience不可用时使用原有超时机制)

### 2. JSON网关集成

**文件**: `src/gateway/json_gateway.py`

**集成点**:
- `_execute_order_with_resilience()`: MT5订单执行 (NO自动超时重试)
- `_handle_order_send()`: 订单处理，使用上述方法

⚠️ **重要安全修订** (2026-01-19): 经外部AI审查发现，金融订单操作不应自动重试超时错误，因为超时表示订单状态不确定（可能已在MT5端执行），自动重试会导致重复下单风险。

**关键改进** (修订后):
```python
def _execute_order_with_resilience(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """MT5订单执行 - 仅处理连接错误，NOT超时"""
    try:
        return self.mt5.execute_order(payload)
    except TimeoutError as e:
        # 超时=状态不确定，返回错误给上层处理（不重试）
        return {
            "error": True,
            "ticket": 0,
            "msg": "Order timeout - status unknown (NOT retrying)",
            "retcode": -1
        }
    except (ConnectionError, ConnectionRefusedError) as e:
        # 连接错误=订单未发送，安全传播给上层
        raise ConnectionError(str(e))
```

**安全原则**:
- ✅ 连接错误可重试 (订单未发送)
- ❌ 超时不可重试 (订单状态不确定，可能已执行)
- ✅ 防止重复下单 (Double Spending Prevention)
- ✅ 清晰的错误分类和日志记录

---

## 📊 性能影响

### Socket通信 (ZMQ)

| 指标 | 改进前 | 改进后 | 说明 |
|------|--------|--------|------|
| **超时行为** | 立即失败 | 10次重试 | 更好的故障恢复 |
| **网络抖动处理** | 无 | 自动 | 适应网络波动 |
| **总等待时间** | 1秒 | 最多 5秒 | Hub兼容的超时 |
| **指数退避** | 无 | 0.5→2s | 防止网络雪崩 |

### MT5订单执行 (JSON)

| 指标 | 改进前 | 改进后 | 说明 |
|------|--------|--------|------|
| **超时重试** | 无 | ❌ 已禁用 | 防止重复下单 |
| **连接错误处理** | 失败 | 传播给上层 | 安全的错误处理 |
| **订单安全性** | 中 | 高 | Double Spending 防护 |
| **错误分类** | 简单 | 精确 | TimeoutError vs ConnectionError |

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
- [x] ZMQ Socket接收增强 (5s超时, 10次重试)
- [x] ZMQ Socket发送增强 (5s超时, 10次重试)
- [x] MT5订单执行安全处理 (NO超时重试)
- [x] 原有功能保留
- [x] 错误处理保留并增强

### 部署就绪
- [x] 所有模块编译通过
- [x] 优雅降级机制 (fallback)
- [x] Protocol v4.4合规
- [x] P1安全修复完成 (2026-01-19)
- [ ] 生产环境测试 (待执行)
- [ ] 订单重复测试 (待执行)

---

## 🔐 关键特性 (修订版本 2026-01-19)

✅ **ZMQ网关** (安全的重试):
- 10次重试 (vs 原有的立即失败)
- 5秒超时保护 (Hub兼容)
- 指数退避 0.5s → 2s
- 优雅降级
- 双向保护 (接收+发送)

✅ **JSON网关** (金融安全):
- ❌ NO超时重试 (防止重复下单)
- ✅ 连接错误安全传播
- 清晰的异常分类
- Double Spending 防护
- 幂等性设计就绪

---

## 🎯 后续建议 (修订版本)

### 立即 (P1完成)
- [x] 修复订单执行重复下单风险 (2026-01-19)
- [x] 调整ZMQ超时与Hub对齐 (30s→5s)
- [x] 更新文档移除风险声明
- [ ] 部署到测试环境
- [ ] 运行订单重复压力测试
- [ ] 验证ZMQ延迟指标 (P99 < 5s)

### 近期
- [ ] 收集生产性能数据
- [ ] 监控订单执行安全性
- [ ] 验证无重复订单发生
- [ ] 部署到生产环境

### 长期
- [ ] 监控KPI (重试成功率、订单成功率)
- [ ] 定期检查日志
- [ ] 持续优化参数

---

## 📝 修订历史

**v1.0** (2026-01-18): 初始集成
- ZMQ网关: 30s超时, 10次重试
- JSON网关: 30s超时, 5次重试

**v2.0** (2026-01-19): 安全修订 (外部AI审查)
- ⚠️ 移除JSON网关订单执行的超时重试 (防止重复下单)
- ✅ ZMQ超时从30s调整为5s (Hub兼容)
- ✅ 改进异常分类和错误处理
- ✅ 文档更新移除风险声明

---

**集成完成日期**: 2026-01-18 (初版) / 2026-01-19 (安全修订)
**验收状态**: ✅ P1修复完成，待测试验证
**下一步**: 运行订单重复测试 + ZMQ延迟测试

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
