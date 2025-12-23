# Gemini 审查行动清单 - 2025-12-23

**审查报告**: [gemini_review_20251223_031723.md](../reviews/gemini_review_20251223_031723.md)
**审查模型**: Gemini 3 Pro Preview
**审查时间**: 2025-12-23 03:17:23

---

## 🚨 P0 级关键问题 (必须立即修复)

### 1. ZMQ REQ/REP 模式的超时死锁问题

**文件**: [src/mt5_bridge/connection.py](../../src/mt5_bridge/connection.py)

**问题描述**:
- ZMQ REQ 模式下，`recv_json` 超时后 socket 内部状态仍处于 "Expecting Reply"
- 下一次 `send_json` 会直接报错 (EFSM)，导致死锁
- 实盘交易中遇到网络波动将导致系统瘫痪

**修复方案**:
```python
# 在 send_request 方法中添加 socket 重建逻辑
async def send_request(self, payload: Dict, timeout: float = 5.0) -> Optional[Dict]:
    async with self._lock:
        try:
            self.socket.send_json(payload)
            if self.socket.poll(timeout * 1000, zmq.POLLIN):
                return self.socket.recv_json()
            else:
                logger.error("⏱️ ZMQ 超时，重建 Socket...")
                # 关键修复：销毁并重建 Socket
                self.socket.close()
                self.socket = self.context.socket(zmq.REQ)
                self.socket.connect(self.endpoint)
                return None
        except Exception as e:
            logger.error(f"❌ ZMQ 异常，重建 Socket: {e}")
            self._rebuild_socket()
            raise
```

**验证标准**:
- [ ] 创建超时模拟测试
- [ ] 验证超时后第二次请求不会抛出 EFSM 错误
- [ ] 压力测试：连续 100 次请求，随机触发超时

**优先级**: 🔴 P0 (阻塞上线)

---

### 2. 订单超时后的状态歧义

**文件**: [src/mt5_bridge/executor.py](../../src/mt5_bridge/executor.py:86)

**问题描述**:
- 当前超时返回 `{"retcode": -1, "comment": "Network Timeout"}`
- 量化系统中，"网络超时" ≠ "订单失败"
- 超时意味着订单可能已成交也可能未成交（未知状态）

**修复方案**:
```python
# 1. 创建自定义异常
class AmbiguousOrderStateError(Exception):
    """订单状态未知异常（通常由网络超时引起）"""
    def __init__(self, request_id: str, symbol: str, volume: float, side: str):
        self.request_id = request_id
        self.symbol = symbol
        self.volume = volume
        self.side = side
        super().__init__(
            f"订单状态未知 - 需要查单 [{request_id[:8]}]: "
            f"{side} {volume} {symbol}"
        )

# 2. 修改 execute_order
async def execute_order(self, ...):
    try:
        response = await self.conn.send_request(payload, timeout=10.0)

        if not response:
            # 超时应抛出异常，而非返回失败
            raise AmbiguousOrderStateError(
                request_id=request_id,
                symbol=symbol,
                volume=volume,
                side=side
            )
        ...
    except AmbiguousOrderStateError:
        # 触发查单流程（需要实现 #012.3 - Order Inquiry）
        logger.critical(f"⚠️ 订单超时！需要查单: {request_id[:8]}")
        raise
```

**下游需求**:
- [ ] 实现 `query_order(request_id)` 方法
- [ ] 策略层需要处理 `AmbiguousOrderStateError`
- [ ] 增加订单状态对账机制

**优先级**: 🔴 P0 (风控核心)

---

## ⚠️ P1 级重要问题 (上线前修复)

### 3. Magic Number 硬编码

**文件**: [src/mt5_bridge/executor.py](../../src/mt5_bridge/executor.py:76)

**问题描述**:
- `magic: 123456` 被硬编码
- 无法区分不同策略实例（趋势策略 vs 震荡策略）

**修复方案**:
```python
# 1. 在 .env 中添加
MT5_MAGIC_NUMBER=123456
MT5_STRATEGY_MAGIC_BASE=120000  # 可选：策略基数

# 2. 在 config.py 中读取
import os
from dotenv import load_dotenv

load_dotenv()

class MT5Config:
    MAGIC_NUMBER = int(os.getenv("MT5_MAGIC_NUMBER", "123456"))

# 3. 在 OrderExecutor 中使用
from src.mt5_bridge.config import MT5Config

class OrderExecutor:
    def __init__(self, connection: MT5Connection, magic: int = None):
        self.conn = connection
        self.magic = magic or MT5Config.MAGIC_NUMBER
```

**验证标准**:
- [ ] 环境变量缺失时使用默认值 123456
- [ ] 支持每个策略实例使用不同的 magic
- [ ] 单元测试覆盖

**优先级**: 🟡 P1 (配置规范)

---

### 4. ZMQ Context 生命周期管理

**文件**: [src/mt5_bridge/connection.py](../../src/mt5_bridge/connection.py)

**问题描述**:
- 创建了 `self.context = zmq.asyncio.Context()` 但未销毁
- 频繁重启连接对象会导致文件句柄泄漏

**修复方案**:
```python
class MT5Connection:
    async def disconnect(self):
        """断开连接并清理资源"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.socket:
            self.socket.close()
            self.socket = None

        if self.context:
            self.context.term()  # 关键：销毁 Context
            self.context = None

        self.connected = False
        logger.info("🔌 ZMQ 连接已断开，资源已释放")

    def __del__(self):
        """析构函数确保资源释放"""
        if self.context:
            self.context.term()
```

**验证标准**:
- [ ] 使用 `lsof` 检查文件句柄是否正常释放
- [ ] 压力测试：连续 1000 次 connect/disconnect 循环

**优先级**: 🟡 P1 (资源管理)

---

## 🔧 P2 级代码改进 (技术债务)

### 5. 移除 Python 3.6 兼容性代码

**文件**: [tests/test_012_2_executor.py](../../tests/test_012_2_executor.py:16-19)

**问题描述**:
- 手动实现 `AsyncMock` 以兼容 Python 3.6
- 项目时间为 2025 年，Python 3.6 已 EOL

**修复方案**:
```python
# 直接使用标准库
from unittest.mock import AsyncMock, MagicMock

# 删除以下代码
# class AsyncMock(MagicMock):
#     async def __call__(self, *args, **kwargs):
#         return super(AsyncMock, self).__call__(*args, **kwargs)
```

**前置条件**:
- [ ] 确认系统 Python 版本 >= 3.8
- [ ] 更新 `requirements.txt` 指定 Python 3.8+

**优先级**: 🟢 P2 (代码清理)

---

### 6. 浮点数精度风险

**文件**: [src/mt5_bridge/executor.py](../../src/mt5_bridge/executor.py:73)

**问题描述**:
- `volume` 被强制转换为 `float`
- 可能产生 `0.1 + 0.2 != 0.3` 的精度问题

**修复方案**:
```python
from decimal import Decimal

async def execute_order(self,
                      symbol: str,
                      volume: Union[float, Decimal],
                      side: str,
                      ...):
    # 内部使用 Decimal，最后一刻转换
    volume_decimal = Decimal(str(volume))

    payload = {
        ...
        "volume": float(volume_decimal),  # 仅此处转换
        ...
    }
```

**优先级**: 🟢 P2 (精度优化)

---

## 🚀 P3 级架构优化 (长期规划)

### 7. 并发模式升级 (REQ/REP → DEALER/ROUTER)

**当前问题**:
- `REQ + asyncio.Lock` 本质上是串行系统
- 高频交易时吞吐量受限

**优化方案**:
- 升级为 `DEALER (Client) <-> ROUTER (Server)` 模式
- 发送后无需等待，通过 `request_id` 在回调中匹配
- 预期吞吐量提升 10-100 倍

**实施计划**:
- [ ] 创建 `src/mt5_bridge/dealer_connection.py`
- [ ] 实现异步回调机制
- [ ] 性能基准测试

**优先级**: 🔵 P3 (性能优化)

---

### 8. UUID 性能优化

**当前性能**: `uuid.uuid4()` 约 10-20 μs/次
**优化方案**: `Timestamp(ns) + AtomicCounter` 可达 1-2 μs/次

**适用场景**: 高频交易 (>1000 TPS)

**优先级**: 🔵 P3 (极致性能)

---

### 9. 心跳机制改进

**当前状态**: `_heartbeat_task` 提及但未实现
**建议改进**:
- 心跳携带 `Server Time`
- 若时间偏差 > 500ms，自动暂停交易
- 防止行情延迟导致滑点亏损

**优先级**: 🔵 P3 (风控增强)

---

## 📊 修复优先级矩阵

| 问题 | 优先级 | 影响 | 修复难度 | 预计时间 |
|------|--------|------|----------|----------|
| ZMQ 超时死锁 | P0 | 系统瘫痪 | 中 | 2-4 小时 |
| 订单状态歧义 | P0 | 资金风险 | 高 | 4-8 小时 |
| Magic Number | P1 | 配置混乱 | 低 | 30 分钟 |
| Context 泄漏 | P1 | 资源耗尽 | 低 | 1 小时 |
| Python 3.6 兼容 | P2 | 代码债务 | 低 | 15 分钟 |
| 浮点数精度 | P2 | 精度损失 | 中 | 1-2 小时 |
| DEALER/ROUTER | P3 | 性能瓶颈 | 高 | 2-3 天 |
| UUID 优化 | P3 | 性能边际 | 中 | 4-6 小时 |
| 心跳改进 | P3 | 风控增强 | 中 | 2-4 小时 |

---

## ✅ 行动计划

### Phase 1: P0 级修复 (立即执行)
1. ✅ 已完成 Gemini 审查
2. ⏳ 修复 ZMQ 超时死锁
3. ⏳ 实现 AmbiguousOrderStateError
4. ⏳ 创建订单查询机制 (#012.3)

### Phase 2: P1 级改进 (上线前)
1. ⏳ Magic Number 配置化
2. ⏳ Context 生命周期管理
3. ⏳ 完整的集成测试

### Phase 3: P2 级清理 (持续迭代)
1. ⏳ 移除 Python 3.6 兼容代码
2. ⏳ Decimal 精度处理
3. ⏳ 代码质量提升

### Phase 4: P3 级优化 (性能调优)
1. ⏳ DEALER/ROUTER 模式
2. ⏳ UUID 性能优化
3. ⏳ 心跳机制完善

---

## 📝 相关工单

- **#012.1**: ✅ ZMQ 连接层（已完成，需修复）
- **#012.2**: ✅ 订单执行器（已完成，需修复）
- **#012.3**: ⏳ 订单查询机制（待创建）
- **#012.4**: ⏳ DEALER/ROUTER 模式（长期）

---

**生成时间**: 2025-12-23 03:20
**下次审查**: 修复 P0/P1 问题后
**负责人**: Claude Builder + Gemini Architect
