# Task #018.01: Real-time Inference & Execution Loop

## 执行摘要 (Executive Summary)

本任务将所有现有组件（MT5 Client、XGBoost模型、Feature API）整合到一个统一的实时交易机器人中。通过模拟模式验证完整的数据流：市场数据接收 → 特征计算 → 模型推理 → 订单执行。

**任务目标**:
1. 创建 `TradingBot` 类实现实时推理循环
2. 实现 ZMQ PUB/SUB 模式接收市场数据
3. 集成 Feature Serving API 进行特征查询
4. 使用 XGBoost 模型生成交易信号
5. 通过 MT5Client 执行订单
6. 完整的日志记录系统

## 1. 背景与现状 (Context)

### 前置任务完成情况
- ✅ Task #015.01: FastAPI Feature Serving (http://localhost:8000)
- ✅ Task #016.01: XGBoost Baseline Model (models/baseline_v1.json)
- ✅ Task #016.02: Hyperparameter Optimization (models/optimized_v1.json)
- ✅ Task #017.01: MT5 Execution Client (ZMQ REQ/REP)

### 现有资源
```
Models:       models/baseline_v1.json, models/optimized_v1.json
Feature API:  http://localhost:8000 (FastAPI)
Execution:    src/gateway/mt5_client.py (ZMQ REQ)
Data:         ZMQ PUB (Port 5556, Market Data)
```

## 2. 方案设计 (Solution Design)

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      REAL-TIME TRADING SYSTEM                   │
└─────────────────────────────────────────────────────────────────┘

   Mock Market Data                    Real Components
   ┌──────────────┐                    ┌──────────────┐
   │ ZMQ Publisher│                    │ Feature API  │
   │  (Port 5556) │                    │  (Port 8000) │
   │              │                    │              │
   │ Tick Stream  │                    │ Historical   │
   │ EURUSD 1.1000│                    │ Features     │
   └──────┬───────┘                    └──────▲───────┘
          │                                   │
          │ PUB/SUB                          │ HTTP GET
          │                                   │
          ▼                                   │
   ┌──────────────────────────────────────────┴───────┐
   │           TRADING BOT (Core Loop)                │
   │                                                   │
   │  1. on_tick()    ─────────────────────────────┐  │
   │     │                                          │  │
   │     ├─▶ Parse Tick Data                       │  │
   │     │                                          │  │
   │  2. fetch_features() ──▶ API Call             │  │
   │     │                                          │  │
   │  3. predict() ──────────▶ XGBoost Inference   │  │
   │     │                                          │  │
   │  4. execute_signal() ───▶ MT5Client.send()    │  │
   │                                                │  │
   └────────────────────────────┬───────────────────┘  │
                                │                      │
                                ▼                      │
                         ┌──────────────┐              │
                         │ Mock Gateway │              │
                         │  (Port 5555) │              │
                         │              │              │
                         │ Order Router │              │
                         └──────────────┘              │
                                                        │
                         ┌──────────────┐              │
                         │ trading.log  │◀─────────────┘
                         │              │  All Events
                         │ 2026-01-01   │
                         │ 02:30:00 ...│
                         └──────────────┘
```

### 2.2 数据流序列图

```sequence
participant Market as ZMQ Publisher\n(Mock Data)
participant Bot as TradingBot\n(Core Loop)
participant API as Feature API\n(Port 8000)
participant Model as XGBoost\n(optimized_v1)
participant Client as MT5Client\n(ZMQ REQ)
participant Gateway as Mock Gateway\n(Port 5555)

Market->>Bot: Tick: EURUSD 1.10000
Note right of Bot: on_tick()
Bot->>API: GET /features/latest?symbol=EURUSD
API-->>Bot: {sma_20: 1.0950, rsi_14: 65, ...}
Bot->>Model: predict(features)
Model-->>Bot: signal = 1 (BUY)
Note right of Bot: execute_signal()
Bot->>Client: send_order("EURUSD", "BUY", 0.1)
Client->>Gateway: {"action": "TRADE", ...}
Gateway-->>Client: {"status": "ok", "ticket": 123456}
Client-->>Bot: Order confirmed
Note right of Bot: Log: "Order #123456 filled"
```

### 2.3 TradingBot 类设计

**核心方法**:

```python
class TradingBot:
    """
    Real-time Trading Bot

    Features:
    - ZMQ PUB/SUB for market data
    - Feature API integration
    - XGBoost inference
    - MT5Client execution
    - Comprehensive logging
    """

    def __init__(
        self,
        symbols: List[str],
        model_path: str,
        api_url: str,
        zmq_market_url: str,
        zmq_execution_url: str
    ):
        """Initialize bot with all components"""

    def connect(self):
        """Connect to all external services"""

    def on_tick(self, tick: Dict[str, Any]):
        """Handle incoming market tick"""

    def fetch_features(self, symbol: str, timestamp: str) -> np.ndarray:
        """Fetch features from API"""

    def predict_signal(self, features: np.ndarray) -> int:
        """Generate trading signal (0=HOLD, 1=BUY, -1=SELL)"""

    def execute_signal(self, symbol: str, signal: int, price: float):
        """Execute trading signal"""

    def run(self, duration_seconds: int = 60):
        """Main event loop"""

    def shutdown(self):
        """Clean shutdown"""
```

### 2.4 Mock Market Data Protocol

**ZMQ PUB Message Format**:

```json
{
  "type": "tick",
  "symbol": "EURUSD",
  "timestamp": "2026-01-01T02:30:00.000Z",
  "bid": 1.10000,
  "ask": 1.10005,
  "last": 1.10003,
  "volume": 100
}
```

**Publish Frequency**: 1 tick per second per symbol

### 2.5 Logging Strategy

**Log Levels**:
- **INFO**: Tick received, Feature fetched, Signal generated, Order sent
- **WARNING**: API timeout, Feature missing, Model prediction uncertain
- **ERROR**: Connection failed, Order rejected, Critical exceptions

**Log Format**:
```
2026-01-01 02:30:00,123 - TradingBot - INFO - [TICK] EURUSD 1.10000
2026-01-01 02:30:00,234 - TradingBot - INFO - [FEAT] Fetched 18 features
2026-01-01 02:30:00,345 - TradingBot - INFO - [PRED] Signal: BUY (confidence: 0.72)
2026-01-01 02:30:00,456 - TradingBot - INFO - [EXEC] Order #123456 sent
2026-01-01 02:30:00,567 - TradingBot - INFO - [FILL] Order #123456 filled @ 1.10003
```

## 3. 实现步骤 (Implementation Steps)

### 步骤 1: 文档优先 (Documentation) ✅ 当前步骤

创建完整的实现计划文档 (本文件)

### 步骤 2: Bot 实现 (src/bot/trading_bot.py)

**核心功能**:
1. ZMQ Subscriber 连接到 `tcp://localhost:5556`
2. HTTP Client 调用 Feature API
3. XGBoost 模型加载和推理
4. MT5Client 订单执行
5. 完整的错误处理和日志

**关键挑战**:
- 特征缺失处理（API返回不完整数据）
- 模型输入格式验证（18个特征，正确顺序）
- 并发安全（避免同时下多个订单）
- 资源清理（ZMQ socket, HTTP session）

### 步骤 3: 模拟运行器 (scripts/run_paper_trading.py)

**组件**:
1. **MockMarketPublisher**: ZMQ PUB @ 5556
   - 读取历史数据（从数据库）
   - 以1秒间隔发布tick
   - 支持多交易对（EURUSD, XAUUSD）

2. **MockMT5Gateway**: ZMQ REP @ 5555
   - 接收订单请求
   - 模拟成交延迟（50-200ms）
   - 返回订单确认

3. **TradingBot**: 主事件循环
   - 订阅市场数据
   - 执行推理和交易逻辑
   - 记录所有事件

**运行流程**:
```python
# Start Mock Services
publisher = MockMarketPublisher(port=5556)
gateway = MockMT5Gateway(port=5555)

# Start Bot
bot = TradingBot(
    symbols=["EURUSD", "XAUUSD"],
    model_path="models/optimized_v1.json",
    api_url="http://localhost:8000",
    zmq_market_url="tcp://localhost:5556",
    zmq_execution_url="tcp://localhost:5555"
)

# Run for 60 seconds
bot.run(duration_seconds=60)

# Shutdown
bot.shutdown()
publisher.stop()
gateway.stop()
```

### 步骤 4: 审计检查 (Audit)

更新 `scripts/audit_current_task.py`:
- Section [16/16]: Task #018.01 检查项
- 验证 TradingBot 类存在
- 验证 run_paper_trading.py 可执行
- 验证日志文件生成
- 验证至少1个订单被执行

## 4. 预期结果 (Expected Results)

### 成功指标

**运行时指标** (60秒模拟):
- ✅ 接收至少 60 个市场tick（1 tick/s × 1 symbol）
- ✅ 成功获取至少 10 次特征（不是每个tick都触发交易）
- ✅ 生成至少 3 个交易信号（BUY/SELL）
- ✅ 执行至少 1 个订单
- ✅ 日志文件 `logs/trading.log` 存在且包含完整记录

**日志验证**:
```bash
$ grep -c "TICK" logs/trading.log
60

$ grep -c "PRED" logs/trading.log
10

$ grep -c "EXEC" logs/trading.log
3

$ grep -c "FILL" logs/trading.log
3
```

**输出示例**:

```
================================================================================
🤖 Paper Trading Simulation
================================================================================

Starting Mock Services...
✅ Mock Market Publisher started (Port 5556)
✅ Mock MT5 Gateway started (Port 5555)

Initializing Trading Bot...
✅ Model loaded: models/optimized_v1.json
✅ Feature API connected: http://localhost:8000
✅ MT5 Client connected: tcp://localhost:5555
✅ Market Data subscribed: tcp://localhost:5556

Running for 60 seconds...

[00:01] TICK: EURUSD 1.10000
[00:01] FEAT: Fetched 18 features
[00:01] PRED: Signal=BUY (confidence=0.72)
[00:01] EXEC: Order #123456 sent (EURUSD BUY 0.1)
[00:01] FILL: Order #123456 filled @ 1.10003

[00:05] TICK: EURUSD 1.10050
[00:05] FEAT: Fetched 18 features
[00:05] PRED: Signal=HOLD (confidence=0.45)

...

[01:00] TICK: EURUSD 1.10200

================================================================================
📊 Simulation Summary
================================================================================

Duration:        60 seconds
Ticks Received:  60
Features Fetched: 12
Signals Generated: 5
  - BUY:  2
  - SELL: 1
  - HOLD: 2
Orders Executed: 3
Orders Filled:   3
Orders Rejected: 0

✅ Simulation completed successfully
📝 Logs saved to: logs/trading_20260101_023000.log
```

## 5. 依赖项 (Dependencies)

**Python 包**:
```
xgboost>=2.0.0        # Model inference
pyzmq>=27.0.0         # ZMQ communication
requests>=2.28.0      # HTTP API calls
numpy>=1.24.0         # Array operations
pandas>=1.5.0         # Data handling (optional)
```

**运行时依赖**:
- Feature Serving API running @ http://localhost:8000
- TimescaleDB 数据库连接（用于历史数据）
- 模型文件存在：`models/optimized_v1.json` 或 `models/baseline_v1.json`

**可选依赖**:
- PostgreSQL 数据库（如果从数据库读取历史tick数据）

## 6. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|-------|-----------|
| Feature API 不可用 | 无法推理 | 中 | 缓存最近特征，降级为技术指标计算 |
| 模型预测延迟高 | 错过交易机会 | 低 | 异步推理，设置超时 |
| ZMQ 连接断开 | 数据中断 | 中 | 自动重连机制，心跳检测 |
| 订单执行失败 | 信号丢失 | 低 | 重试机制（最多3次），记录失败订单 |
| 内存泄漏 | 长时间运行崩溃 | 低 | 定期清理缓存，限制历史记录大小 |
| 并发订单冲突 | 重复下单 | 中 | 全局锁，订单状态追踪 |

## 7. 测试策略 (Testing Strategy)

### 单元测试
- `test_trading_bot.py`: TradingBot 类的各个方法
- `test_mock_services.py`: Mock Publisher 和 Gateway

### 集成测试
- `test_full_loop.py`: 完整的端到端流程
- 验证：Tick → Feature → Predict → Execute → Fill

### 性能测试
- **Latency**: Tick 到 Order 的端到端延迟 < 500ms
- **Throughput**: 支持至少 10 ticks/s
- **Memory**: 60秒运行内存增长 < 50MB

## 8. 时间线 (Timeline)

| 步骤 | 操作 | 预计时间 |
|------|------|----------|
| 1 | 创建计划文档 | 15 分钟 |
| 2 | 实现 TradingBot 类 | 40 分钟 |
| 3 | 实现 Mock Services | 30 分钟 |
| 4 | 创建运行器脚本 | 20 分钟 |
| 5 | 更新审计脚本 | 10 分钟 |
| 6 | 运行模拟测试 | 5 分钟 |
| 7 | 验证日志和结果 | 10 分钟 |
| **总计** | | **130 分钟** |

## 9. 验收标准 (Acceptance Criteria)

**硬性要求**:
- [ ] docs/TASK_018_01_PLAN.md 完整
- [ ] src/bot/trading_bot.py 实现并通过语法检查
- [ ] src/bot/__init__.py 导出 TradingBot
- [ ] scripts/run_paper_trading.py 存在并可执行
- [ ] 模拟运行60秒不崩溃
- [ ] logs/trading.log 包含所有事件类型（TICK, FEAT, PRED, EXEC, FILL）
- [ ] 审计 Section [16/16] 已添加
- [ ] 所有审计检查通过

**性能要求**:
- [ ] 端到端延迟 < 500ms
- [ ] 至少执行 1 个订单
- [ ] 无内存泄漏（60秒后干净退出）

**代码质量**:
- [ ] 代码通过语法检查
- [ ] 代码通过导入验证
- [ ] 日志格式清晰可读

## 10. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建 docs/TASK_018_01_PLAN.md
- ✅ 本地存储: 日志存储在 logs/ 目录
- ✅ 代码优先: 实现完整的 TradingBot 类
- ✅ 审计强制: Section [16/16] 验证所有要求
- ✅ Notion 仅状态: 不更新页面内容
- ✅ AI 审查: 使用 gemini_review_bridge.py

## 11. 扩展性考虑 (Scalability)

### 从模拟到实盘
1. **数据源切换**: Mock Publisher → 真实 MT5 数据流
2. **执行切换**: Mock Gateway → 真实 MT5 Gateway
3. **无需修改**: TradingBot 逻辑保持不变

### 多策略支持
- 策略工厂模式：`BaseStrategy`, `TrendFollowingStrategy`, `MeanReversionStrategy`
- 策略管理器：同时运行多个策略，统一风险控制

### 分布式部署
- Bot Cluster: 多个 Bot 实例处理不同交易对
- Load Balancer: 分发市场数据到不同 Bot
- Centralized Risk Manager: 统一风险控制和仓位管理

## 12. 参考资源 (References)

- [ZeroMQ Guide](https://zguide.zeromq.org/)
- [XGBoost Python API](https://xgboost.readthedocs.io/en/stable/python/python_api.html)
- [Algorithmic Trading Best Practices](https://www.quantstart.com/articles/)
- [Event-Driven Trading Systems](https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/)

---

**创建日期**: 2026-01-01

**协议版本**: v2.2 (Documentation-First, Local Storage, Code-First)

**任务状态**: Ready for Implementation

**预计完成时间**: 2-3 hours
