# TASK #025: EODHD Real-Time WebSocket Feed - 快速启动指南

**版本**: 1.0
**日期**: 2026-01-04
**协议**: v4.0 (Sync-Enforced)

---

## 概述

TASK #025 实现了 EODHD WebSocket 客户端，为系统提供实时外汇行情数据（EURUSD, GBPUSD, USDJPY 等）。

**数据流**:
```
EODHD Cloud (WebSocket)
         ↓
EodhdWsClient (本地网关)
         ↓
ZMQ PUB (端口 5556)
         ↓
订阅者应用
```

---

## 前置条件

### 软件依赖

```bash
# 必需库
pip install websockets zmq python-dotenv

# 验证安装
python3 -c "import websockets; import zmq; print('✅ All dependencies installed')"
```

### 环境配置

编辑 `.env` 文件：

```bash
# EODHD API 配置
EODHD_API_TOKEN=6953782f2a2fe5.46192922          # 你的 API Token
EODHD_WS_URL=wss://ws.eodhistoricaldata.com/ws/forex

# ZMQ 配置
ZMQ_PORT_DATA=5556                               # 行情推送端口
```

### 网络配置

确保以下端口已开放：
- **5556**: ZMQ PUB（本地绑定）
- **WSS 443**: EODHD WebSocket（出站）

---

## 1. 运行行情客户端

### 1.1 基础启动

```bash
cd /opt/mt5-crs

# 启动 EODHD WebSocket 客户端（后台运行）
python3 -m src.gateway.market_data_feed &

# 或前台运行（便于调试）
python3 src/gateway/market_data_feed.py
```

### 1.2 预期输出

```
[2026-01-04 12:00:00] [INFO    ] EodhdWsClient 初始化完成
[2026-01-04 12:00:00] [INFO    ] ZMQ PUB 绑定到端口 5556
[2026-01-04 12:00:01] [SUCCESS ] WebSocket 已连接
[2026-01-04 12:00:02] [INFO    ] 已订阅品种: EURUSD,GBPUSD,USDJPY
[2026-01-04 12:00:03] [INFO    ] EURUSD: 1.05430
[2026-01-04 12:00:04] [INFO    ] GBPUSD: 1.27650
[2026-01-04 12:00:05] [INFO    ] USDJPY: 148.750
...
```

### 1.3 停止客户端

```bash
# 查找进程
ps aux | grep market_data_feed

# 杀死进程
kill <PID>

# 或按 Ctrl+C（前台运行时）
```

---

## 2. 运行测试脚本

### 2.1 执行测试

```bash
python3 scripts/test_market_feed.py
```

### 2.2 预期结果

```
================================================================================
EODHD Market Data Feed Test
================================================================================
测试配置: ZMQ_PORT=5556, TEST_DURATION=10s

[Test 1] 检查 ZMQ 可用性...
✅ PASS: ZMQ 库已安装

[Test 2] 订阅 ZMQ PUB 并接收数据...
等待 10 秒接收数据...
已接收 5 个 Tick | 品种: EURUSD, GBPUSD, USDJPY
已接收 10 个 Tick | 品种: EURUSD, GBPUSD, USDJPY
已接收 15 个 Tick | 品种: EURUSD, GBPUSD, USDJPY

[Test 3] 验证接收数据量...
✅ PASS: 接收到足够的数据 (15 >= 5)

[Test 4] 验证数据格式...
✅ PASS: 所有 15 个 Tick 格式有效

[Test 5] 数据内容示例...
  First Tick: EURUSD @ 1.05430
  Last Tick:  USDJPY @ 148.750
  观察到的品种: EURUSD, GBPUSD, USDJPY
✅ PASS: 数据内容有效

[Test 6] 性能指标...
  吞吐率: 1.5 ticks/sec
  数据点: 15
  品种数: 3
✅ PASS: 性能指标正常

================================================================================
✅ 所有测试通过 (6/6 PASSED)
================================================================================
```

### 2.3 测试项详解

| 测试项 | 验证内容 | 通过条件 |
|:---|:---|:---|
| Test 1 | ZMQ 库可用 | 库已安装 |
| Test 2 | 数据接收 | 接收到消息 |
| Test 3 | 数据量 | >= 5 个 Tick 在 10 秒内 |
| Test 4 | 数据格式 | 所有 Tick 包含必需字段 |
| Test 5 | 数据内容 | 价格合理、品种正确 |
| Test 6 | 性能 | 吞吐率 > 0.5 ticks/sec |

---

## 3. 数据格式参考

### 3.1 ZMQ 消息格式

**多部分消息**:
```
Part 0: symbol (字符串)  -> "EURUSD"
Part 1: data (JSON)     -> {"symbol": "EURUSD", "price": 1.05430, ...}
```

### 3.2 Tick 数据结构

```json
{
  "symbol": "EURUSD",           // 品种代码
  "price": 1.05430,              // 最新价格
  "bid": 1.05425,                // 买价
  "ask": 1.05435,                // 卖价
  "timestamp": 1704153600,        // Unix 时间戳
  "source": "EODHD"              // 数据源
}
```

### 3.3 EODHD WebSocket 协议

**订阅请求**:
```json
{
  "action": "subscribe",
  "symbols": "EURUSD,GBPUSD,USDJPY"
}
```

**订阅响应**:
```json
{
  "status": "subscribed",
  "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
}
```

**实时 Tick**:
```json
{
  "s": "EURUSD",
  "p": 1.05430,
  "bid": 1.05425,
  "ask": 1.05435,
  "t": 1704153600
}
```

---

## 4. 常见问题

### Q1: WebSocket 连接失败

**症状**: `[ERROR] WebSocket 连接出错: ConnectionRefusedError`

**解决方案**:
```bash
# 1. 检查网络连接
ping wss://ws.eodhistoricaldata.com

# 2. 验证 API Token
echo $EODHD_API_TOKEN

# 3. 检查防火墙
curl -I https://ws.eodhistoricaldata.com/

# 4. 验证 URL 正确性
cat .env | grep EODHD_WS_URL
```

### Q2: ZMQ 连接超时

**症状**: `[WARN] 等待中... (10.0s)`（测试脚本中）

**解决方案**:
```bash
# 1. 检查端口是否绑定
netstat -tuln | grep 5556

# 2. 确保客户端正在运行
ps aux | grep market_data_feed

# 3. 检查防火墙设置
sudo ufw allow 5556/tcp

# 4. 重启客户端
pkill -f market_data_feed
python3 src/gateway/market_data_feed.py &
```

### Q3: 收到的 Tick 数据格式不对

**症状**: `[ERROR] symbol 不是字符串: ...`

**检查项**:
1. EODHD API 是否返回了预期格式
2. JSON 解析是否正确
3. 数据字段是否符合文档规范

**调试**:
```python
# 添加调试日志到 market_data_feed.py
# 在 _process_tick 方法中添加：
print(f"[DEBUG] Raw tick data: {tick_data}")
```

### Q4: 性能指标低（吞吐率 < 0.5 ticks/sec）

**原因**:
- EODHD API 返回数据速率低
- 网络延迟较高
- ZMQ PUB 发送缓冲区满

**优化**:
```python
# 在 EodhdWsClient 中调整：
self.heartbeat_interval = 60  # 减少心跳频率
self.zmq_pub.setsockopt(zmq.SNDHWM, 1000)  # 增加发送缓冲
```

---

## 5. 监控和诊断

### 5.1 查看日志

```bash
# 实时查看
tail -f VERIFY_LOG.log

# 查看错误
grep ERROR VERIFY_LOG.log | tail -20

# 统计 Tick 收到数
grep "EURUSD:" VERIFY_LOG.log | wc -l
```

### 5.2 连接状态检查

```bash
# 检查 WebSocket 连接
netstat -tuln | grep -E "5556|443"

# 监控 ZMQ 消息
zmq_monitor tcp://127.0.0.1:5556

# 查看进程资源使用
ps aux | grep market_data_feed
```

### 5.3 数据质量验证

```bash
# 提取 Tick 数据（需要订阅 ZMQ）
python3 -c "
import zmq
import json

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB)
sub.connect('tcp://127.0.0.1:5556')
sub.setsockopt_string(zmq.SUBSCRIBE, '')

for i in range(10):
    msg = sub.recv_multipart()
    symbol = msg[0].decode()
    data = json.loads(msg[1])
    print(f'{symbol}: {data[\"price\"]:.5f}')
"
```

---

## 6. 集成指南

### 6.1 在其他应用中使用

```python
# 订阅市场数据
import zmq
import json

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:5556")
subscriber.setsockopt_string(zmq.SUBSCRIBE, "EURUSD")

while True:
    symbol, data_json = subscriber.recv_multipart()
    data = json.loads(data_json)
    print(f"{data['symbol']}: {data['price']}")
```

### 6.2 与交易系统集成

```python
# 接收实时行情用于下单
from src.gateway.market_data_feed import EodhdWsClient

client = EodhdWsClient(symbols={"EURUSD", "GBPUSD"})

# 订阅额外品种
client.subscribe("USDJPY", "AUDUSD")

# 启动客户端（异步）
asyncio.run(client.run())
```

---

## 7. 故障排查清单

- [ ] 依赖库已安装 (`websockets`, `zmq`, `python-dotenv`)
- [ ] `.env` 文件已配置 (`EODHD_API_TOKEN`, `EODHD_WS_URL`)
- [ ] 网络连接正常 (ping EODHD)
- [ ] 端口 5556 未被占用
- [ ] WebSocket 客户端已启动
- [ ] 测试脚本通过所有 6 项测试
- [ ] VERIFY_LOG.log 包含 Tick 数据示例
- [ ] 吞吐率 > 0.5 ticks/sec

---

## 参考资源

- **代码文件**: `src/gateway/market_data_feed.py`
- **测试脚本**: `scripts/test_market_feed.py`
- **日志文件**: `VERIFY_LOG.log`
- **EODHD 文档**: https://eodhistoricaldata.com/docs/
- **ZMQ 文档**: https://zguide.zeromq.org/

---

**最后更新**: 2026-01-04
**维护者**: MT5-CRS Project Team
