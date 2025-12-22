# 🤖 Gemini Pro 审查行动项 - MT5 实盘对接

**审查时间**: 2025-12-23 00:58:39
**审查范围**: MT5 实盘对接核心风险评估
**报告位置**: [docs/reviews/gemini_review_20251223_005839.md](reviews/gemini_review_20251223_005839.md)

---

## 🎯 执行摘要

Gemini Pro 深度审查识别了 **3 个 P0 级关键风险**，如果不解决将导致实盘交易系统完全无法运行或产生重大资金风险。同时提供了 **6 个 P1/P2 优先级改进建议**，用于提升系统稳定性和性能。

**关键结论**: 当前代码架构在回测环境中运行良好，但存在严重的**回测-实盘架构断层**问题。必须立即解决 P0 级风险才能继续实盘对接工作。

---

## 🔴 P0 级关键风险 (Critical - 立即处理)

### 风险 #1: KellySizer 数据依赖性崩溃

**严重程度**: 🔴 Critical (阻塞实盘运行)

**问题描述**:
```python
# KellySizer 依赖预计算的 ML 预测数据
prob_long = data.y_pred_proba_long[0]  # ← 实盘中不存在!
```

**根本原因**:
- 回测环境: `MLDataFeed` 预先计算好所有 ML 预测并作为 Line 存储
- 实盘环境: MT5 推送实时 Tick/Bar 数据，ML 推理必须在 `next()` 中实时完成
- 架构断层: 没有机制在实盘中实时调用 ML 模型并注入结果到 DataFeed

**后果**:
- KellySizer 访问不存在的属性 → `AttributeError`
- 或获取 `NaN` 值 → Kelly 公式计算错误 → 仓位异常

**解决方案** (3 步):

#### 步骤 1: 添加空值安全检查
```python
def _get_win_probability(self, data) -> Optional[float]:
    """获取做多胜率，带空值保护"""
    try:
        # 尝试从 DataFeed 获取预测概率
        if hasattr(data, 'y_pred_proba_long'):
            prob = data.y_pred_proba_long[0]
            if prob is not None and not np.isnan(prob):
                return prob

        # 兜底: 返回默认中性胜率
        logger.warning("无法获取 ML 预测概率，使用默认胜率 0.5")
        return 0.5  # 或 None（跳过交易）

    except (AttributeError, IndexError) as e:
        logger.error(f"获取胜率失败: {e}")
        return 0.5  # 保守兜底
```

#### 步骤 2: 实现实时 ML 推理注入
```python
class MT5DataFeed(bt.DataBase):
    """MT5 实时数据流，支持实时 ML 推理"""

    def __init__(self, ml_model=None, feature_engineer=None):
        self.ml_model = ml_model
        self.feature_engineer = feature_engineer
        # 添加自定义 Line 用于存储实时预测
        self.lines = ('y_pred_proba_long', 'y_pred_proba_short')

    def _load(self):
        # 1. 从 MT5 获取最新 Tick/Bar
        tick_data = mt5.symbol_info_tick(self.symbol)

        # 2. 实时计算特征
        features = self.feature_engineer.compute_features(tick_data)

        # 3. 实时调用 ML 模型
        if self.ml_model:
            pred_proba = self.ml_model.predict_proba(features)
            self.lines.y_pred_proba_long[0] = pred_proba[1]  # 做多概率
            self.lines.y_pred_proba_short[0] = pred_proba[0]  # 做空概率

        return True
```

#### 步骤 3: 集成测试
```python
# tests/test_mt5_kelly_integration.py
def test_kelly_sizer_with_mt5_datafeed():
    """测试 KellySizer 与 MT5DataFeed 的集成"""
    cerebro = bt.Cerebro()

    # 使用 MT5 实时数据流
    datafeed = MT5DataFeed(ml_model=trained_model)
    cerebro.adddata(datafeed)

    # 使用 KellySizer
    cerebro.addsizer(KellySizer)

    # 运行并验证没有崩溃
    cerebro.run()

    assert True  # 如果到达这里，说明没有 AttributeError
```

**相关工单**: #012.1 - 修复 KellySizer 数据依赖性崩溃风险

---

### 风险 #2: 账户净值获取错误

**严重程度**: 🔴 Critical (资金风险)

**问题描述**:
```python
# 回测中获取模拟净值
account_value = self.broker.getvalue()  # ← 实盘中返回什么?
```

**根本原因**:
- 回测环境: `broker.getvalue()` 返回 Backtrader 模拟账户权益
- 实盘环境: 必须调用 `mt5.account_info().equity` 获取真实账户权益
- 风险: 如果 MT5Broker 未正确映射，Kelly 公式将使用错误的净值计算仓位

**后果**:
- 示例: 实际权益 $10,000，但 `getvalue()` 返回 $100,000
- Kelly 公式计算出 10 倍过大的仓位
- 极端杠杆 → 爆仓风险

**解决方案**:

#### 步骤 1: 实现 MT5Broker
```python
class MT5Broker(bt.BrokerBase):
    """MT5 实盘 Broker 适配器"""

    def getvalue(self):
        """获取账户权益（实时）"""
        try:
            account_info = mt5.account_info()
            if account_info is None:
                raise RuntimeError("无法获取 MT5 账户信息")

            equity = account_info.equity
            logger.info(f"MT5 账户权益: ${equity:.2f}")
            return equity

        except Exception as e:
            logger.error(f"获取账户净值失败: {e}")
            # 关键: 不要返回默认值，直接抛出异常
            raise RuntimeError("无法获取 MT5 账户净值，停止交易") from e
```

#### 步骤 2: 集成测试
```python
def test_mt5_broker_equity_accuracy():
    """测试 MT5Broker 净值准确性"""
    broker = MT5Broker()

    # 获取 Broker 返回的净值
    broker_equity = broker.getvalue()

    # 直接从 MT5 API 获取净值
    mt5_equity = mt5.account_info().equity

    # 验证一致性 (允许极小误差)
    assert abs(broker_equity - mt5_equity) < 0.01
```

**相关工单**: #012.2 - 验证 MT5Broker 账户净值映射准确性

---

### 风险 #3: MT5 同步阻塞

**严重程度**: 🔴 Critical (连接稳定性)

**问题描述**:
- 标准 `MetaTrader5` Python 库是**同步阻塞**的
- MLStrategy 的特征工程和 ML 推理可能耗时 100-500ms
- 阻塞期间无法接收 MT5 Tick 或响应心跳 → 连接断开

**根本原因**:
```python
def next(self):
    # 1. 特征计算 (50-100ms)
    features = self.compute_features()

    # 2. ML 推理 (50-200ms)  ← 阻塞!
    prediction = self.model.predict(features)

    # 3. 期间 MT5 Tick 数据累积，心跳可能超时
```

**后果**:
- MT5 服务器检测到心跳超时 → 强制断开连接
- 错过关键 Tick 数据 → 交易信号延迟或丢失
- 系统不稳定，频繁重连

**解决方案**: 实现异步架构

#### 步骤 1: 异步 MT5 数据获取
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncMT5Wrapper:
    """MT5 API 异步包装器"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.tick_queue = asyncio.Queue()

    async def get_tick_async(self, symbol):
        """异步获取 Tick 数据"""
        loop = asyncio.get_event_loop()
        # 在线程池中执行阻塞的 MT5 调用
        tick = await loop.run_in_executor(
            self.executor,
            mt5.symbol_info_tick,
            symbol
        )
        return tick

    async def tick_listener(self, symbol):
        """后台 Tick 监听器"""
        while True:
            tick = await self.get_tick_async(symbol)
            await self.tick_queue.put(tick)
            await asyncio.sleep(0.1)  # 100ms 轮询间隔
```

#### 步骤 2: 策略计算移到独立线程
```python
class AsyncMLStrategy(bt.Strategy):
    """支持异步计算的 ML 策略"""

    def __init__(self):
        self.ml_executor = ThreadPoolExecutor(max_workers=1)
        self.pending_prediction = None

    def next(self):
        # 非阻塞: 提交 ML 推理任务
        if self.pending_prediction is None or self.pending_prediction.done():
            self.pending_prediction = self.ml_executor.submit(
                self._compute_prediction
            )

        # 如果上一次预测已完成，使用结果
        if self.pending_prediction.done():
            try:
                prediction = self.pending_prediction.result()
                self._execute_trade(prediction)
            except Exception as e:
                logger.error(f"ML 推理失败: {e}")

    def _compute_prediction(self):
        """耗时的 ML 计算（在独立线程中执行）"""
        features = self.compute_features()  # 50-100ms
        return self.model.predict(features)  # 50-200ms
```

#### 步骤 3: 集成测试
```python
async def test_async_mt5_no_blocking():
    """测试异步架构不阻塞 MT5 连接"""
    wrapper = AsyncMT5Wrapper()

    # 启动 Tick 监听器
    tick_task = asyncio.create_task(wrapper.tick_listener("EURUSD"))

    # 模拟耗时计算
    await asyncio.sleep(0.5)  # 500ms

    # 验证在计算期间仍能接收 Tick
    assert wrapper.tick_queue.qsize() >= 4  # 至少收到 4 个 Tick
```

**相关工单**: #012.3 - 实现 MT5 异步架构防止连接阻塞

---

## ⚠️ P1 级风险缓解 (High Priority)

### 改进 #4: _get_win_probability 空值处理

**优先级**: P1
**相关工单**: #012.6

**当前问题**:
```python
def _get_win_probability(self, data) -> Optional[float]:
    # 可能返回 None
    return data.y_pred_proba_long[0]

# 调用方未处理 None
kelly_f = 2 * win_prob - 1  # ← TypeError if win_prob is None
```

**解决方案**:
```python
def _get_win_probability(self, data) -> float:  # 不再返回 Optional
    """获取胜率，保证返回有效值"""
    try:
        prob = data.y_pred_proba_long[0]
        if prob is not None and 0 <= prob <= 1:
            return prob
    except (AttributeError, IndexError):
        pass

    # 兜底: 返回保守的中性胜率
    return 0.5  # 或从配置读取 DEFAULT_WIN_PROBABILITY
```

---

### 改进 #5: API 异常处理细化

**优先级**: P1
**相关工单**: #012.5

**当前问题**:
```python
try:
    response = requests.post(url, json=payload)
except Exception as e:  # ← 太宽泛
    logger.error(f"请求失败: {e}")
    return None
```

**改进方案**:
```python
from requests.exceptions import Timeout, ConnectionError, HTTPError

def call_gemini_with_retry(payload, max_retries=3):
    """带重试的 Gemini API 调用"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()

        except Timeout:
            # 超时 → 指数退避重试
            wait_time = 2 ** attempt
            logger.warning(f"请求超时，{wait_time}s 后重试")
            time.sleep(wait_time)

        except ConnectionError as e:
            # 连接错误 → 检查网络后重试
            logger.error(f"连接失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise

        except HTTPError as e:
            # HTTP 错误 → 根据状态码决定
            if e.response.status_code == 429:  # 限流
                time.sleep(60)
            elif e.response.status_code >= 500:  # 服务端错误
                time.sleep(10)
            else:  # 客户端错误，不重试
                raise
```

---

### 改进 #6: 风控状态持久化

**优先级**: P1
**相关工单**: #012.4

**当前问题**:
```python
class DynamicRiskManager:
    def __init__(self):
        self.realized_pnl = 0  # ← 内存中，重启后丢失
        self.trade_count = 0
```

**风险场景**:
1. 当天已亏损 $4,900（接近 $5,000 日损限制）
2. 程序崩溃并重启
3. `realized_pnl` 重置为 0
4. 系统继续交易，再亏 $5,000 → 总计 $9,900 亏损！

**解决方案**:
```python
import sqlite3
from datetime import date

class PersistentRiskManager:
    """带持久化的风控管理器"""

    def __init__(self, db_path="risk_state.db"):
        self.db_path = db_path
        self._init_db()
        self._load_today_state()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_risk (
                trade_date TEXT PRIMARY KEY,
                realized_pnl REAL,
                trade_count INTEGER,
                max_drawdown REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _load_today_state(self):
        """加载今日风控状态"""
        today = date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT realized_pnl, trade_count FROM daily_risk WHERE trade_date = ?",
            (today,)
        )
        row = cursor.fetchone()

        if row:
            self.realized_pnl, self.trade_count = row
            logger.info(f"恢复今日风控状态: PnL=${self.realized_pnl}, 交易次数={self.trade_count}")
        else:
            self.realized_pnl = 0
            self.trade_count = 0
            logger.info("初始化今日风控状态")

        conn.close()

    def update_realized_pnl(self, pnl):
        """更新已实现盈亏（持久化）"""
        self.realized_pnl += pnl

        today = date.today().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO daily_risk (trade_date, realized_pnl, trade_count)
            VALUES (?, ?, ?)
        """, (today, self.realized_pnl, self.trade_count))
        conn.commit()
        conn.close()

        logger.info(f"风控状态已持久化: PnL=${self.realized_pnl}")
```

---

## 🚀 P2 级性能优化 (Optimization)

### 优化 #7: 推理延迟优化

**优先级**: P2
**相关工单**: #012.7

**方案 A: LRU 缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def compute_features(bar_data_hash):
    """缓存特征计算结果"""
    # 昂贵的特征计算
    return features
```

**方案 B: Parquet 预计算** (适合回测)
```python
# 一次性计算所有特征
features_df = compute_all_features(historical_data)
features_df.to_parquet("features_cache.parquet")

# 回测时直接加载
features = pd.read_parquet("features_cache.parquet")
```

---

### 优化 #8: 多进程清理

**优先级**: P2
**相关工单**: #012.8

**当前问题**: Windows 下 ProcessPoolExecutor 可能产生僵尸进程

**解决方案**:
```python
import signal
import atexit

def cleanup_processes():
    """优雅关闭所有子进程"""
    logger.info("清理子进程...")
    for process in active_processes:
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()

# 注册清理函数
atexit.register(cleanup_processes)
signal.signal(signal.SIGTERM, lambda s, f: cleanup_processes())
signal.signal(signal.SIGINT, lambda s, f: cleanup_processes())
```

---

### 优化 #9: 集成测试完善

**优先级**: P2
**相关工单**: #012.9

**测试套件**:
```python
# tests/integration/test_mt5_live.py

def test_end_to_end_live_trading():
    """端到端实盘交易测试"""
    # 1. 初始化 MT5 连接
    assert mt5.initialize()

    # 2. 创建 Cerebro + MT5DataFeed + MT5Broker + KellySizer
    cerebro = setup_live_cerebro()

    # 3. 运行 1 分钟
    cerebro.run(timeout=60)

    # 4. 验证: 无崩溃 + 正确接收数据 + Kelly 计算正常
    assert cerebro.completed_successfully
```

---

## 📋 工单创建清单

### 推荐创建的 Notion 工单

| 工单号 | 标题 | 优先级 | 预计时间 | 依赖 |
|--------|------|--------|----------|------|
| #012.1 | 修复 KellySizer 数据依赖性崩溃风险 | P0 | 1-2 天 | 无 |
| #012.2 | 验证 MT5Broker 账户净值映射准确性 | P0 | 1 天 | #012.1 |
| #012.3 | 实现 MT5 异步架构防止连接阻塞 | P0 | 2-3 天 | #012.1 |
| #012.4 | 实现风控状态持久化 (SQLite) | P1 | 1-2 天 | #012.2 |
| #012.5 | 改进 API 异常处理和重试机制 | P1 | 1 天 | 无 |
| #012.6 | 添加 _get_win_probability 空值处理 | P1 | 0.5 天 | #012.1 |
| #012.7 | 推理延迟优化 (Caching) | P2 | 1 天 | 无 |
| #012.8 | 多进程清理改进 (Signal 处理) | P2 | 0.5 天 | 无 |
| #012.9 | 集成测试完善 | P2 | 2 天 | #012.1-#012.3 |

**总预计时间**: P0 (4-6 天) + P1 (2.5-4 天) + P2 (3.5 天) = **10-13.5 天**

---

## 🎯 实施路线图

### 第 1 周: P0 关键风险修复

**目标**: 解除实盘对接的阻塞问题

**Day 1-2**: 工单 #012.1 - KellySizer 空值安全
- 添加空值检查和兜底逻辑
- 实现 MT5DataFeed 实时 ML 推理注入
- 单元测试

**Day 3**: 工单 #012.2 - MT5Broker 净值验证
- 实现 MT5Broker.getvalue()
- 集成测试验证准确性
- 文档化

**Day 4-6**: 工单 #012.3 - MT5 异步架构
- 实现 AsyncMT5Wrapper
- 重构 MLStrategy 为异步模式
- 压力测试

**里程碑**: 实盘架构断层问题解决，系统可以连接 MT5 并稳定运行

---

### 第 2 周: P1 风险缓解 + P2 优化

**Day 7-8**: 工单 #012.4 - 风控持久化
- 实现 PersistentRiskManager
- SQLite 数据库设计
- 崩溃恢复测试

**Day 9**: 工单 #012.5 + #012.6 - 异常处理改进
- 细化 API 异常分类
- 实现重试策略
- 完善空值处理

**Day 10-11**: 工单 #012.7 + #012.8 - 性能优化
- 推理缓存实现
- 多进程清理
- 性能基准测试

**Day 12-13**: 工单 #012.9 - 集成测试
- 端到端测试套件
- 压力测试
- 文档化

**里程碑**: 实盘系统达到生产级质量

---

### 第 3 周: 实盘验证

**Day 14-15**: 模拟盘测试
- 连接 MT5 Demo 账户
- 24 小时连续运行测试
- 监控日志和性能指标

**Day 16-18**: 小资金实盘测试
- 最小手数测试 (0.01 lot)
- 验证所有风控机制
- 收集实盘数据

**Day 19-20**: 评审和优化
- 分析实盘数据
- 修复发现的问题
- 准备正式上线

**里程碑**: 实盘系统验证完成

---

## ✅ 成功标准

### P0 完成标准
- [ ] KellySizer 在 MT5DataFeed 中无崩溃运行
- [ ] MT5Broker 净值与 MT5 API 误差 < 0.01%
- [ ] 策略计算不阻塞 MT5 连接，连续运行 24 小时无断线

### P1 完成标准
- [ ] 风控状态持久化，重启后正确恢复
- [ ] API 调用失败自动重试，成功率 > 99%
- [ ] 所有可能返回 None 的地方都有兜底处理

### P2 完成标准
- [ ] 特征计算耗时降低 30% 以上
- [ ] 无僵尸进程残留
- [ ] 集成测试覆盖率 > 80%

---

## 📊 进度追踪

| 阶段 | 开始日期 | 预计完成 | 实际完成 | 状态 |
|------|---------|----------|----------|------|
| P0 风险修复 | TBD | TBD | - | ⏳ 待开始 |
| P1 风险缓解 | TBD | TBD | - | ⏳ 待开始 |
| P2 性能优化 | TBD | TBD | - | ⏳ 待开始 |
| 实盘验证 | TBD | TBD | - | ⏳ 待开始 |

---

## 🔗 相关资源

### 文档
- [Gemini Pro 完整审查报告](reviews/gemini_review_20251223_005839.md)
- [工单 #011 进度总结](WORK_ORDER_011_PROGRESS.md)
- [Gemini 审查行动计划](GEMINI_REVIEW_ACTION_PLAN.md)

### 代码
- [src/strategy/risk_manager.py](../src/strategy/risk_manager.py) - KellySizer 实现
- [nexus_with_proxy.py](../nexus_with_proxy.py) - API 调用
- [bin/run_backtest.py](../bin/run_backtest.py) - 回测系统

### 测试
- [tests/test_kelly_fix.py](../tests/test_kelly_fix.py) - Kelly 公式测试

---

**生成时间**: 2025-12-23T01:05:00 UTC
**下一步**: 创建工单 #012.1-#012.9 到 Notion 并开始 P0 修复工作
