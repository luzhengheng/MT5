# TASK #024 JSON 交易架构 - 快速启动指南

**版本**: 1.0
**日期**: 2026-01-04
**协议**: v4.0 (Sync-Enforced)

---

## 概述

本指南指导你快速测试和验证 JSON 交易架构的实现。包括单元测试、集成测试和性能监控。

## 前置条件

### 硬件和网络
- Linux INF (策略引擎) 运行中
- Windows GTW (MT5 网关) 运行中
- 网络连通性检查: `ping 172.19.141.255`

### 软件依赖
```bash
pip3 install zmq  # ZeroMQ Python binding
pip3 install metatrader5  # MT5 Python SDK (可选)
```

### 部署清单
- [ ] EA 已上传到 MT5: `MQL5/Experts/Direct_Zmq.mq5`
- [ ] Python 客户端已安装: `src/client/json_trade_client.py`
- [ ] Gateway 路由器已部署: `src/gateway/json_gateway.py`
- [ ] 网络端口 5555 和 5556 已开放

---

## 1. 运行单元测试

### 1.1 基础连通性检查

```bash
# 测试 ZMQ 网络连通性
python3 scripts/test_zmq_connection.py

# 预期输出:
# ✅ Port 5555 [ZMQ REQ (Trade Command)] is OPEN
# ✅ Port 5556 [ZMQ PUB (Market Data)] is OPEN
```

### 1.2 运行 JSON 协议单元测试

```bash
cd /opt/mt5-crs

python3 scripts/test_order_json.py
```

**预期输出**:
```
============================================================
JSON Trading Protocol Unit Tests
============================================================

Integration Tests (requires running MT5 Gateway):

[TEST 1] Basic Buy Order
  Response: {
    "error": false,
    "ticket": 100234567,
    "msg": "Filled at 1.05123",
    "retcode": 10009,
    "latency_ms": 23.45
  }
  ✓ Order #100234567 filled
  ✓ Latency: 23.45ms

[TEST 2] Basic Sell Order
  ✓ Order #100234568 filled

[TEST 3] Order with SL/TP
  ✓ Order #100234569 with SL/TP

[TEST 4] UUID Uniqueness
  ✓ req_id 1: 550e8400...
  ✓ req_id 2: 550e8401...

[TEST 5] Latency Measurement
  Latency: 23.45ms
  ✓ Latency within threshold

Unit Tests (input validation):

[TEST 6] Invalid Order Type Rejection
  ✓ Correctly rejected: Invalid order type

[TEST 7] Invalid Volume Rejection
  ✓ Correctly rejected: Invalid volume

[TEST 8] Invalid Comment Rejection
  ✓ Correctly rejected: Comment too long

============================================================
Test Summary
============================================================
Total:  8
Passed: 8
Failed: 0
Success Rate: 100.0%
```

---

## 2. 手动测试

### 2.1 交互式 Python 测试

```python
from src.client.json_trade_client import JsonTradeClient

# 初始化客户端
client = JsonTradeClient()

# 发送买单
response = client.buy(
    symbol="EURUSD",
    volume=0.01,
    sl=1.04500,  # 止损
    tp=1.06000   # 止盈
)

print(f"Order #{response['ticket']}: {response['msg']}")
print(f"Latency: {response['latency_ms']}ms")

# 发送卖单
response = client.sell(
    symbol="GBPUSD",
    volume=0.02
)

# 关闭连接
client.close()
```

### 2.2 使用 curl 测试 JSON 格式（可选）

```bash
# 虽然通常通过 ZMQ 发送，但可以验证 JSON 格式

curl -X POST http://172.19.141.255:8080/json \
  -H "Content-Type: application/json" \
  -d '{
    "action": "ORDER_SEND",
    "req_id": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
      "symbol": "EURUSD",
      "type": "OP_BUY",
      "volume": 0.01,
      "magic": 123456,
      "comment": "Test",
      "sl": 1.04500,
      "tp": 1.06000
    }
  }'
```

---

## 3. 监控和日志

### 3.1 查看 MT5 EA 日志

```bash
# SSH 到 Windows GTW
ssh Administrator@gtw.crestive.net

# 启用 MT5 Journal 日志
# 菜单 -> Tools -> Options -> Logging
# 检查 `C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\logs\`
```

### 3.2 查看 Python Gateway 日志

```bash
# 在 Linux INF 上监控 Gateway 进程
tail -f /var/log/mt5-crs/gateway.log

# 预期日志:
# 2026-01-04 10:00:23 [JsonGatewayRouter] Executing: OP_BUY 0.01L EURUSD
# 2026-01-04 10:00:23 [JsonGatewayRouter] ✓ IDEMPOTENT: Returning cached ticket...
# 2026-01-04 10:00:23 [JsonGatewayRouter] ✅ SUCCESS: Ticket 100234567
```

### 3.3 查看 ZMQ 网络监控

```bash
# 监听 5555 端口的 JSON 请求（需要 tcpdump）
sudo tcpdump -i eth0 'port 5555' -A

# 预期输出:
# {"action":"ORDER_SEND","req_id":"550e8400-...","payload":{...}}
```

---

## 4. 自定义参数

### 4.1 修改测试参数

编辑 `scripts/test_order_json.py`:

```python
# 行 18-22
TEST_SYMBOL = "EURUSD"          # 修改品种
TEST_VOLUME = 0.01              # 修改手数
TEST_MAGIC = 123456             # 修改策略标识
TEST_COMMENT = "JsonTest"       # 修改备注
LATENCY_THRESHOLD_MS = 100      # 修改延迟阈值
```

### 4.2 修改订单参数

```python
# 修改止损和止盈
response = client.trade(
    symbol="EURUSD",
    order_type="OP_BUY",
    volume=0.01,
    sl=1.04000,        # 修改止损价格
    tp=1.07000,        # 修改止盈价格
    magic=999999,      # 修改 Magic 号
    comment="Custom"   # 修改备注
)
```

---

## 5. 常见问题

### Q1: 连接超时 (ZMQ timeout)

**现象**: `ConnectionError: Gateway Timeout`

**排查步骤**:
1. 检查网络连通性:
   ```bash
   ping 172.19.141.255
   nc -zv 172.19.141.255 5555
   ```

2. 检查 MTW Gateway 是否运行:
   ```bash
   ssh Administrator@gtw.crestive.net
   netstat -an | findstr 5555
   ```

3. 检查 EA 是否启用:
   - 打开 MT5
   - 右键 Expert Advisors → Direct_Zmq → 启用

### Q2: 订单被拒绝 (retcode != 10009)

**现象**: `"error": true, "retcode": 10019`（资金不足）

**解决方案**:
- 检查账户余额
- 减少手数
- 查看 MT5 错误代码说明（`docs/specs/PROTOCOL_JSON_v1.md` 第 3.3 节）

### Q3: JSON 解析失败 (retcode: -1)

**现象**: `"msg": "JSON parse failed"`

**排查步骤**:
1. 检查 JSON 格式是否正确
2. 确认必需字段存在（symbol, type, volume）
3. 检查字段类型（volume 必须是数字）

### Q4: 幂等性缓存溢出

**现象**: `Cache cleanup: removed oldest req_id`

**说明**: 这是正常的，缓存大小上限为 10000 条

**配置**:
编辑 `src/gateway/json_gateway.py`:
```python
CACHE_MAX_SIZE = 10000      # 修改此值
CACHE_TTL_SECONDS = 3600    # 修改缓存有效期
```

---

## 6. 性能基准

### 预期性能指标

| 指标 | 目标 | 说明 |
|:---|:---|:---|
| 往返延迟 | < 100ms | 包括网络 + ZMQ 处理 |
| 吞吐量 | > 100 orders/sec | 单条连接 |
| 成功率 | > 99.9% | 成功订单比率 |
| 缓存命中率 | 95%+ | 幂等性重传 |

### 性能测试脚本

```python
import time
from src.client.json_trade_client import JsonTradeClient

client = JsonTradeClient()

# 测试 100 个订单的延迟
latencies = []
for i in range(100):
    response = client.buy(symbol="EURUSD", volume=0.01)
    latencies.append(response["latency_ms"])

# 统计
avg_latency = sum(latencies) / len(latencies)
max_latency = max(latencies)
min_latency = min(latencies)

print(f"Avg Latency: {avg_latency:.2f}ms")
print(f"Max Latency: {max_latency:.2f}ms")
print(f"Min Latency: {min_latency:.2f}ms")

client.close()
```

---

## 7. 故障排查清单

- [ ] 网络连通性: `ping 172.19.141.255`
- [ ] 端口开放: `nc -zv 172.19.141.255 5555`
- [ ] Gateway 进程: `ssh gtw "tasklist | findstr MT5"`
- [ ] EA 启用: 检查 MT5 顶部是否显示 "Direct_Zmq"
- [ ] 日志文件: 检查 `/var/log/mt5-crs/gateway.log`
- [ ] ZMQ 版本: `python3 -c "import zmq; print(zmq.zmq_version())"`
- [ ] Python 版本: `python3 --version` (需要 3.6+)

---

## 8. 后续步骤

### Phase 1: 集成测试 ✅
- [x] 协议规范编写
- [x] Python 客户端实现
- [x] Gateway 路由器实现
- [x] MQL5 EA 实现
- [x] 单元测试脚本

### Phase 2: 部署 (后续)
- [ ] 上传 EA 到生产环境
- [ ] 配置日志存储
- [ ] 设置监控告警
- [ ] 性能基准测试

### Phase 3: 高级功能 (v1.1)
- [ ] 支持 ORDER_MODIFY 操作
- [ ] 支持 ORDER_CLOSE 操作
- [ ] 支持请求签名验证
- [ ] 支持消息压缩

---

## 参考资源

- **协议规范**: `docs/specs/PROTOCOL_JSON_v1.md`
- **代码文件**:
  - `src/client/json_trade_client.py`
  - `src/gateway/json_gateway.py`
  - `MQL5/Experts/Direct_Zmq.mq5`
- **MT5 API 文档**: https://www.mql5.com/en/docs
- **ZMQ 文档**: http://zguide.zeromq.org/

---

**最后更新**: 2026-01-04
**维护者**: MT5-CRS Project Team
