# Task #017.01: MT5 Execution Client Implementation

## 执行摘要 (Executive Summary)

本任务实现 Python 客户端 (`MT5Client`) 与 Windows Gateway 通信，建立"热路径"(Hot Path) 架构的关键桥梁。通过 ZMQ REQ/REP 模式实现高性能、低延迟的订单执行和账户查询功能。

**任务目标**:
1. 实现 `MT5Client` 类使用 ZMQ REQ 模式
2. 提供核心交易功能: connect, send_order, get_account, get_positions
3. 添加超时 (2s) 和重试 (3x) 机制确保弹性
4. 定义清晰的 JSON 通信协议
5. 创建 Mock Server 验证端到端通信

## 1. 背景与现状 (Context)

### 前置条件完成情况
- ✅ ZMQ 端口开放: 5555 (命令) / 5556 (数据流)
- ✅ Notion Sync 已恢复 (Task #099.01)
- ✅ Windows Gateway 假设已部署并监听

### 架构概览: "Hot Path"

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Strategy (Linux)                   │
├─────────────────────────────────────────────────────────────┤
│  src/strategy/                                               │
│  ├── risk_manager.py         (风险控制)                      │
│  ├── position_tracker.py     (持仓跟踪)                      │
│  └── execution_engine.py     (执行引擎)                      │
│                      ↓                                        │
│  src/gateway/                                                │
│  └── mt5_client.py ← 本任务实现                             │
│           ↓ ZMQ REQ (tcp://172.19.141.255:5555)             │
└───────────┼─────────────────────────────────────────────────┘
            │
            │ JSON over ZMQ
            │
┌───────────┼─────────────────────────────────────────────────┐
│           ↓ ZMQ REP                                          │
│  MT5 Gateway (Windows)                                       │
│  ├── Listens on *:5555 (REQ/REP)                            │
│  ├── Listens on *:5556 (PUB for tick stream)                │
│  └── MQL5 Expert Advisor                                     │
│           ↓                                                   │
│  MetaTrader 5 Terminal                                       │
│  └── Broker Connection (OANDA, ICMarkets, etc.)             │
└─────────────────────────────────────────────────────────────┘
```

### 关键特性

- **低延迟**: ZMQ 零拷贝消息传递，<1ms 延迟
- **弹性**: 超时 + 重试避免挂起
- **简洁**: JSON 协议易于调试和扩展

## 2. 方案设计 (Solution Design)

### 2.1 JSON 通信协议

**Command Types**:
1. **PING** - 连接测试
2. **TRADE** - 下单
3. **GET_ACCOUNT** - 查询账户
4. **GET_POSITIONS** - 查询持仓

#### 2.1.1 PING Command

**Request**:
```json
{
  "action": "PING",
  "timestamp": "2026-01-01T01:10:00"
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "pong",
  "server_time": "2026-01-01T01:10:00.123"
}
```

#### 2.1.2 TRADE Command

**Request**:
```json
{
  "action": "TRADE",
  "symbol": "EURUSD",
  "order_type": "MARKET",
  "side": "BUY",
  "volume": 0.1,
  "price": 1.0850,
  "sl": 1.0800,
  "tp": 1.0900,
  "magic": 12345,
  "comment": "Strategy_A_Entry"
}
```

**Fields**:
- `symbol`: 交易品种 (EURUSD, GBPUSD, XAUUSD, etc.)
- `order_type`: MARKET, LIMIT, STOP
- `side`: BUY, SELL
- `volume`: 手数 (lots)
- `price`: 价格 (LIMIT/STOP 订单需要)
- `sl`: 止损价格 (可选)
- `tp`: 止盈价格 (可选)
- `magic`: Magic Number (策略标识)
- `comment`: 订单备注

**Response (Success)**:
```json
{
  "status": "ok",
  "ticket": 123456789,
  "message": "Order placed successfully",
  "price": 1.0851
}
```

**Response (Error)**:
```json
{
  "status": "error",
  "error_code": "INVALID_PRICE",
  "message": "Price is too far from current market"
}
```

#### 2.1.3 GET_ACCOUNT Command

**Request**:
```json
{
  "action": "GET_ACCOUNT"
}
```

**Response**:
```json
{
  "status": "ok",
  "balance": 10000.00,
  "equity": 10234.56,
  "margin": 512.30,
  "free_margin": 9722.26,
  "margin_level": 1997.45,
  "currency": "USD"
}
```

#### 2.1.4 GET_POSITIONS Command

**Request**:
```json
{
  "action": "GET_POSITIONS",
  "symbol": "EURUSD"  // 可选，不填返回所有
}
```

**Response**:
```json
{
  "status": "ok",
  "positions": [
    {
      "ticket": 123456789,
      "symbol": "EURUSD",
      "type": "BUY",
      "volume": 0.1,
      "open_price": 1.0850,
      "current_price": 1.0862,
      "sl": 1.0800,
      "tp": 1.0900,
      "profit": 12.00,
      "magic": 12345,
      "comment": "Strategy_A_Entry",
      "open_time": "2026-01-01T00:30:00"
    }
  ]
}
```

### 2.2 MT5Client 类设计

```python
class MT5Client:
    """
    MT5 Gateway 客户端 (ZMQ REQ 模式)
    
    特性:
    - 自动重连
    - 超时控制 (2s)
    - 重试机制 (3x)
    - JSON 序列化/反序列化
    """
    
    def __init__(self, host: str = "172.19.141.255", port: int = 5555):
        """
        初始化 MT5 客户端
        
        参数:
            host: Gateway 主机地址
            port: Gateway 端口 (默认 5555)
        """
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = None
        self._connected = False
        
    def connect(self) -> bool:
        """
        建立到 Gateway 的连接
        
        返回:
            True if connected, False otherwise
        """
        pass
    
    def send_command(
        self,
        command: dict,
        timeout_ms: int = 2000,
        retries: int = 3
    ) -> dict:
        """
        发送命令到 Gateway
        
        参数:
            command: 命令字典 (将被序列化为 JSON)
            timeout_ms: 超时时间 (毫秒)
            retries: 重试次数
            
        返回:
            响应字典
            
        异常:
            TimeoutError: 超时未收到响应
            ConnectionError: 连接失败
        """
        pass
    
    def ping(self) -> bool:
        """
        测试连接
        
        返回:
            True if server responds, False otherwise
        """
        pass
    
    def send_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        order_type: str = "MARKET",
        price: float = None,
        sl: float = None,
        tp: float = None,
        magic: int = 0,
        comment: str = ""
    ) -> dict:
        """
        下单
        
        参数:
            symbol: 交易品种
            side: BUY 或 SELL
            volume: 手数
            order_type: MARKET, LIMIT, STOP
            price: 价格 (LIMIT/STOP 需要)
            sl: 止损
            tp: 止盈
            magic: Magic Number
            comment: 备注
            
        返回:
            响应字典 (包含 ticket 等信息)
        """
        pass
    
    def get_account(self) -> dict:
        """
        查询账户信息
        
        返回:
            账户信息字典 (balance, equity, etc.)
        """
        pass
    
    def get_positions(self, symbol: str = None) -> list:
        """
        查询持仓
        
        参数:
            symbol: 过滤品种 (可选)
            
        返回:
            持仓列表
        """
        pass
    
    def close(self):
        """关闭连接"""
        pass
```

### 2.3 弹性机制设计

#### 2.3.1 超时控制

```python
# 设置 ZMQ socket 超时
self.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)  # 接收超时
self.socket.setsockopt(zmq.SNDTIMEO, timeout_ms)  # 发送超时
self.socket.setsockopt(zmq.LINGER, 0)             # 关闭时不等待
```

#### 2.3.2 重试逻辑

```python
for attempt in range(retries):
    try:
        # 发送请求
        self.socket.send_json(command)
        
        # 等待响应
        response = self.socket.recv_json()
        
        return response
        
    except zmq.Again:
        # 超时，重试
        if attempt < retries - 1:
            logger.warning(f"Timeout, retrying ({attempt + 1}/{retries})...")
            self._reconnect()
        else:
            raise TimeoutError(f"No response after {retries} retries")
    
    except zmq.ZMQError as e:
        logger.error(f"ZMQ error: {e}")
        raise ConnectionError(f"ZMQ error: {e}")
```

#### 2.3.3 断线重连

```python
def _reconnect(self):
    """重建 socket 连接"""
    if self.socket:
        self.socket.close()
    
    self.socket = self.context.socket(zmq.REQ)
    self.socket.connect(f"tcp://{self.host}:{self.port}")
    self.socket.setsockopt(zmq.RCVTIMEO, 2000)
    self.socket.setsockopt(zmq.LINGER, 0)
```

### 2.4 错误处理策略

| 错误类型 | 处理方式 | 用户影响 |
|---------|---------|---------|
| 网络超时 | 重试 3 次 | 延迟 6s |
| 连接失败 | 抛出 ConnectionError | 策略暂停 |
| 无效订单 | 返回 error 状态 | 记录日志，继续 |
| JSON 解析失败 | 抛出 ValueError | 策略暂停 |
| Gateway 崩溃 | 超时后抛出异常 | 策略暂停，告警 |

## 3. 实现步骤 (Implementation Steps)

### 步骤 1: 文档优先 (Documentation) ✅ 当前步骤

创建完整的实施计划文档 (本文件)

### 步骤 2: 实现 MT5Client 类

创建 `src/gateway/mt5_client.py`:

**核心功能**:
1. `__init__()` - 初始化 ZMQ context 和 socket
2. `connect()` - 建立连接
3. `send_command()` - 通用命令发送 (带超时和重试)
4. `ping()` - 连接测试
5. `send_order()` - 下单
6. `get_account()` - 账户查询
7. `get_positions()` - 持仓查询
8. `close()` - 清理资源

**依赖**:
```python
import zmq
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
```

### 步骤 3: 创建 Mock ZMQ Server

创建 `scripts/verify_execution_client.py`:

```python
import zmq
import json
import threading
import time

class MockMT5Gateway:
    """模拟 MT5 Gateway 用于测试"""
    
    def __init__(self, port=5555):
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.running = False
        
    def start(self):
        """启动 Mock Server (在独立线程)"""
        self.socket.bind(f"tcp://*:{self.port}")
        self.running = True
        
        while self.running:
            try:
                # 接收请求
                request = self.socket.recv_json(flags=zmq.NOBLOCK)
                
                # 处理命令
                response = self._handle_command(request)
                
                # 发送响应
                self.socket.send_json(response)
                
            except zmq.Again:
                time.sleep(0.01)
                
    def _handle_command(self, request: dict) -> dict:
        """处理命令并返回响应"""
        action = request.get("action")
        
        if action == "PING":
            return {
                "status": "ok",
                "message": "pong",
                "server_time": datetime.now().isoformat()
            }
        
        elif action == "GET_ACCOUNT":
            return {
                "status": "ok",
                "balance": 10000.00,
                "equity": 10234.56,
                "margin": 512.30,
                "free_margin": 9722.26,
                "currency": "USD"
            }
        
        # ... 其他命令处理
        
    def stop(self):
        """停止 Mock Server"""
        self.running = False
        self.socket.close()
```

**测试流程**:
1. 启动 Mock Server (独立线程)
2. 实例化 MT5Client (连接到 localhost:5555)
3. 测试 PING
4. 测试 GET_ACCOUNT
5. 测试 TRADE
6. 测试 GET_POSITIONS
7. 验证超时和重试机制
8. 停止 Mock Server

### 步骤 4: 更新 __init__.py

创建 `src/gateway/__init__.py`:
```python
from src.gateway.mt5_client import MT5Client

__all__ = ["MT5Client"]
```

### 步骤 5: 更新审计脚本

在 `scripts/audit_current_task.py` 中添加 Section [15/15]:

**检查项**:
- [ ] docs/TASK_017_01_PLAN.md 存在
- [ ] src/gateway/mt5_client.py 存在
- [ ] MT5Client 类可导入
- [ ] scripts/verify_execution_client.py 存在
- [ ] pyzmq 包已安装
- [ ] 验证脚本通过测试

## 4. 预期结果 (Expected Results)

### 4.1 成功的验证输出

```bash
$ python3 scripts/verify_execution_client.py

================================================================================
🧪 MT5 Execution Client Verification
================================================================================

🔹 Starting Mock MT5 Gateway on port 5555...
✅ Mock server started

🔹 Test 1: Client Connection
✅ MT5Client initialized
✅ Connected to localhost:5555

🔹 Test 2: PING Command
ℹ️ Sending PING...
✅ Received: {"status": "ok", "message": "pong"}

🔹 Test 3: GET_ACCOUNT Command
ℹ️ Sending GET_ACCOUNT...
✅ Balance: 10000.00 USD
✅ Equity: 10234.56 USD

🔹 Test 4: TRADE Command
ℹ️ Sending MARKET BUY EURUSD 0.1 lots...
✅ Order placed: Ticket #123456789

🔹 Test 5: GET_POSITIONS Command
ℹ️ Querying positions...
✅ Found 1 position(s)

🔹 Test 6: Timeout Handling
ℹ️ Testing timeout (mock server will delay 3s)...
⚠️ Timeout after 2s (expected)
✅ Retry logic working

🔹 Stopping Mock Gateway...
✅ Mock server stopped

================================================================================
✅ All 6 Tests Passed
================================================================================

Next steps:
  • Deploy Windows Gateway on 172.19.141.255:5555
  • Update MT5Client host to production IP
  • Integrate with execution_engine.py
```

### 4.2 输出文件

```
src/gateway/
├── __init__.py          # 包导出
└── mt5_client.py        # MT5Client 类

scripts/
└── verify_execution_client.py  # 验证脚本

docs/
└── TASK_017_01_PLAN.md  # 实施计划
```

## 5. 依赖项 (Dependencies)

**Python 包**:
```
pyzmq>=25.0.0  # ZMQ Python bindings
```

**系统要求**:
- Python 3.9+
- ZMQ library (libzmq5)
- 网络连通性到 172.19.141.255:5555

**安装**:
```bash
pip install pyzmq
```

## 6. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|-------|----------|
| Windows Gateway 未部署 | 无法测试实际连接 | 高 | 使用 Mock Server 验证客户端逻辑 |
| 网络延迟高 | 超时频繁 | 中 | 调整超时时间为 5s (生产环境) |
| JSON 解析错误 | 客户端崩溃 | 低 | 添加 try-except，优雅降级 |
| ZMQ REQ/REP 死锁 | 客户端挂起 | 中 | 严格的超时和 socket 重建 |
| Gateway 崩溃 | 订单丢失 | 低 | 添加订单持久化和重试队列 |

## 7. 时间线 (Timeline)

| 步骤 | 操作 | 预计时间 |
|------|------|----------|
| 1 | 创建 TASK_017_01_PLAN.md | 12 分钟 |
| 2 | 实现 MT5Client 类 | 25 分钟 |
| 3 | 创建 Mock Server 和验证脚本 | 20 分钟 |
| 4 | 更新审计脚本 | 8 分钟 |
| 5 | 运行验证测试 | 5 分钟 |
| **总计** | | **70 分钟** |

## 8. 验收标准 (Acceptance Criteria)

**硬性要求**:
- [ ] docs/TASK_017_01_PLAN.md 完整
- [ ] src/gateway/mt5_client.py 实现
- [ ] MT5Client 类可导入并实例化
- [ ] scripts/verify_execution_client.py 存在
- [ ] 所有 6 个测试通过
- [ ] 审计 Section [15/15] 已添加
- [ ] 所有审计检查通过

**功能要求**:
- [ ] MT5Client 可发送 JSON 命令
- [ ] MT5Client 可解析 JSON 响应
- [ ] 超时抛出 TimeoutError 而非挂起
- [ ] 重试机制工作正常
- [ ] Mock Server 验证通过

**代码质量**:
- [ ] 代码通过语法检查
- [ ] 类型注解完整
- [ ] 文档字符串清晰
- [ ] 错误处理完善

## 9. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建 docs/TASK_017_01_PLAN.md
- ✅ 代码实现: 完整的 MT5Client 类
- ✅ 测试验证: Mock Server 验证脚本
- ✅ 审计强制: Section [15/15] 验证所有要求
- ✅ Notion Sync: 使用 project_cli.py finish 触发

## 10. 参考资源 (References)

- [ZeroMQ Guide](https://zguide.zeromq.org/)
- [PyZMQ Documentation](https://pyzmq.readthedocs.io/)
- [MT5 Python Integration](https://www.mql5.com/en/docs/python_metatrader5)
- [REQ/REP Pattern](https://zguide.zeromq.org/docs/chapter3/#The-Request-Reply-Mechanisms)

---

**创建日期**: 2026-01-01

**协议版本**: v2.2 (Documentation-First, Code-First)

**任务状态**: Ready for Implementation
