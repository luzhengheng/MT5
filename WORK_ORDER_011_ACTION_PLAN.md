# 🎯 工单 #011 行动计划 - MT5 实盘交易系统对接

**基于 Gemini Pro 专业评估**
**创建日期**: 2025-12-21
**预计完成**: 2 周

---

## 📋 快速概览

基于 Gemini Pro 的深度代码审查（[完整报告](docs/reviews/gemini_review_20251221_055201.md)），以下是工单 #011 的优先任务和详细实施计划。

---

## 🚨 P0 优先级任务（必须立即修复）

### 任务 1: 修复 KellySizer 单位转换

**问题**: 当前代码未处理 MT5 的手数（Lots）与 Backtrader 的单位（Units）转换

**影响**: 🔴 严重 - 直接下单会导致拒单或仓位大小严重偏离

**预计时间**: 0.5 天

**实施步骤**:

1. **修改 `src/strategy/risk_manager.py`**

```python
class KellySizer(bt.Sizer):
    params = (
        ('kelly_fraction', 0.25),
        ('stop_loss_multiplier', 2.0),
        ('min_probability', 0.55),

        # ✅ 新增: MT5 相关参数
        ('contract_size', 100000),  # 1手 = 100,000 单位（外汇标准）
        ('min_lot', 0.01),          # MT5 最小手数
        ('max_lot', 100.0),         # MT5 最大手数
        ('lot_step', 0.01),         # MT5 手数步长
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        """计算仓位大小（已修复 MT5 单位转换）"""

        # 1. 获取 ML 预测概率
        y_pred_proba = getattr(data, 'y_pred_proba_long', None)
        if y_pred_proba is None or len(y_pred_proba) == 0:
            logger.warning("无法获取预测概率，跳过交易")
            return 0

        p = y_pred_proba[0]
        if p < self.p.min_probability:
            return 0

        # 2. 计算 Kelly 风险比例
        b = getattr(self.strategy, 'take_profit_ratio', 2.0)
        f_star = (p * (b + 1) - 1) / b

        if f_star <= 0:
            return 0

        # 3. 计算风险金额
        account_value = self.broker.getvalue()
        risk_amount = account_value * f_star * self.p.kelly_fraction

        # 4. 获取 ATR（必须处理无效情况）
        atr = getattr(data, 'atr', None)
        if atr is None or len(atr) == 0 or atr[0] <= 0:
            logger.warning(f"ATR 无效 (atr={atr}), 无法计算仓位")
            return 0

        distance = atr[0] * self.p.stop_loss_multiplier

        # 5. 计算原始单位数量
        raw_units = risk_amount / distance

        # ✅ 6. 转换为 MT5 手数（核心修复）
        raw_lots = raw_units / self.p.contract_size

        # ✅ 7. 对齐手数步长（向下取整）
        lots = (raw_lots // self.p.lot_step) * self.p.lot_step

        # ✅ 8. 检查最小/最大限制
        if lots < self.p.min_lot:
            logger.debug(f"计算手数 {lots:.2f} 小于最小手数 {self.p.min_lot}, 跳过交易")
            return 0

        if lots > self.p.max_lot:
            logger.warning(f"计算手数 {lots:.2f} 超过最大手数 {self.p.max_lot}, 限制为最大值")
            lots = self.p.max_lot

        # ✅ 9. 转换回 Backtrader Units
        final_units = lots * self.p.contract_size

        logger.info(
            f"Kelly 仓位计算: "
            f"概率={p:.2%}, f*={f_star:.2%}, "
            f"风险金额={risk_amount:.2f}, ATR={atr[0]:.5f}, "
            f"原始单位={raw_units:.0f}, MT5手数={lots:.2f}, "
            f"最终单位={final_units:.0f}"
        )

        return final_units if isbuy else -final_units
```

2. **更新配置文件**

在策略初始化时传入 MT5 参数：

```python
# bin/run_backtest.py 或实盘启动脚本

cerebro.addsizer(
    KellySizer,
    kelly_fraction=0.25,
    stop_loss_multiplier=2.0,
    min_probability=0.55,
    # MT5 参数（根据品种调整）
    contract_size=100000,  # EURUSD: 100,000
    min_lot=0.01,
    max_lot=50.0,  # 根据账户大小和风险承受调整
    lot_step=0.01
)
```

3. **编写测试用例**

创建 `tests/test_kelly_mt5_fix.py`:

```python
import pytest
import backtrader as bt
from src.strategy.risk_manager import KellySizer

def test_kelly_sizer_mt5_conversion():
    """测试 MT5 单位转换逻辑"""

    # 模拟场景
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10000.0)

    # 添加 KellySizer
    sizer = KellySizer(
        kelly_fraction=0.25,
        contract_size=100000,
        min_lot=0.01,
        lot_step=0.01
    )

    # 模拟数据
    class MockData:
        y_pred_proba_long = [0.65]  # 65% 胜率
        atr = [0.0010]  # ATR = 10 pips

    # 计算仓位
    size = sizer._getsizing(None, 10000, MockData(), True)

    # 验证
    expected_lots = 0.06  # 预期约 0.06 手
    expected_units = expected_lots * 100000

    assert abs(size - expected_units) < 100000 * 0.01  # 允许 0.01 手误差
    print(f"✅ 测试通过: 计算单位 {size}, 对应手数 {size/100000:.2f}")

def test_kelly_sizer_min_lot_limit():
    """测试最小手数限制"""

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100.0)  # 小账户

    sizer = KellySizer(
        kelly_fraction=0.25,
        contract_size=100000,
        min_lot=0.01,
        lot_step=0.01
    )

    class MockData:
        y_pred_proba_long = [0.55]
        atr = [0.0010]

    size = sizer._getsizing(None, 100, MockData(), True)

    # 小账户应返回 0（低于最小手数）
    assert size == 0
    print("✅ 测试通过: 小账户正确返回 0")

if __name__ == "__main__":
    test_kelly_sizer_mt5_conversion()
    test_kelly_sizer_min_lot_limit()
```

4. **运行测试验证**

```bash
python3 tests/test_kelly_mt5_fix.py
```

**验收标准**:
- ✅ 单位正确转换为手数
- ✅ 手数正确对齐到步长
- ✅ 最小/最大手数限制生效
- ✅ 测试用例 100% 通过

---

### 任务 2: 异步 API 调用重构

**问题**: `nexus_with_proxy.py` 使用同步 `requests`，会阻塞交易主线程

**影响**: 🔴 严重 - 网络延迟会导致行情接收和订单执行延迟

**预计时间**: 1 天

**实施步骤**:

1. **创建 `src/async_llm_client.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步 LLM 客户端 - 不阻塞交易主线程
"""

import aiohttp
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AsyncLLMClient:
    """异步 LLM 调用客户端（Gemini Pro）"""

    def __init__(self, proxy_api_url: str, proxy_api_key: str):
        self.proxy_api_url = proxy_api_url
        self.proxy_api_key = proxy_api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager 入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager 出口"""
        if self.session:
            await self.session.close()

    async def call_gemini(
        self,
        prompt: str,
        max_tokens: int = 4000,
        timeout: int = 10
    ) -> Optional[str]:
        """异步调用 Gemini Pro"""

        if not self.session:
            raise RuntimeError("必须在 async with 上下文中使用")

        headers = {
            "Authorization": f"Bearer {self.proxy_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gemini-3-pro-preview",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }

        try:
            async with self.session.post(
                self.proxy_api_url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API 错误 {response.status}: {error_text}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Gemini API 超时 (>{timeout}s)")
            return None

        except Exception as e:
            logger.error(f"Gemini API 调用失败: {e}")
            return None

# 使用示例
async def main():
    """测试异步调用"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    async with AsyncLLMClient(
        proxy_api_url=os.getenv("PROXY_API_URL"),
        proxy_api_key=os.getenv("PROXY_API_KEY")
    ) as client:
        result = await client.call_gemini("当前市场状况分析", max_tokens=500, timeout=5)
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

2. **在交易策略中使用异步调用**

```python
# src/strategy/ml_strategy.py

import asyncio
from src.async_llm_client import AsyncLLMClient

class MLStrategy(bt.Strategy):

    def __init__(self):
        super().__init__()
        # 创建异步客户端
        self.llm_client = None
        self.llm_task = None

    def start(self):
        """策略启动时初始化异步客户端"""
        # 在后台运行异步任务
        self.llm_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.llm_loop)

    def next(self):
        """每个 Bar 执行"""

        # 交易逻辑（不阻塞）
        if self.should_enter_long():
            self.buy()

        # 异步获取 LLM 建议（不阻塞交易）
        if self.data.datetime.date() != self.last_llm_call_date:
            self._schedule_llm_analysis()

    def _schedule_llm_analysis(self):
        """调度异步 LLM 分析（不阻塞）"""

        async def analyze():
            async with AsyncLLMClient(
                proxy_api_url=self.p.proxy_api_url,
                proxy_api_key=self.p.proxy_api_key
            ) as client:
                prompt = f"分析当前市场状况: 价格={self.data.close[0]}"
                result = await client.call_gemini(prompt, timeout=5)
                logger.info(f"LLM 建议: {result}")

        # 在独立线程中运行，不阻塞主线程
        import threading
        thread = threading.Thread(target=lambda: asyncio.run(analyze()))
        thread.daemon = True
        thread.start()
```

3. **编写测试**

```bash
python3 src/async_llm_client.py
```

**验收标准**:
- ✅ LLM 调用不阻塞交易主线程
- ✅ 超时机制正常工作
- ✅ 错误处理完善

---

### 任务 3: MT5 连接保活与自动重连

**问题**: 缺少 `mt5.initialize()` 健康检查和自动重连机制

**影响**: 🔴 严重 - MT5 终端掉线会导致系统完全失效

**预计时间**: 1.5 天

**实施步骤**:

1. **创建 `src/mt5/connection_manager.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 连接管理器 - 连接池、健康检查、自动重连
"""

import MetaTrader5 as mt5
import threading
import time
import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConnectionStatus:
    """连接状态"""
    connected: bool
    last_check: datetime
    error_count: int
    last_error: Optional[str]

class MT5ConnectionManager:
    """MT5 连接管理器"""

    def __init__(
        self,
        account: int,
        password: str,
        server: str,
        pool_size: int = 3,
        health_check_interval: int = 30,
        max_retry: int = 5,
        retry_backoff: float = 2.0
    ):
        self.account = account
        self.password = password
        self.server = server
        self.pool_size = pool_size
        self.health_check_interval = health_check_interval
        self.max_retry = max_retry
        self.retry_backoff = retry_backoff

        self.status = ConnectionStatus(
            connected=False,
            last_check=datetime.now(),
            error_count=0,
            last_error=None
        )

        self.watchdog_thread: Optional[threading.Thread] = None
        self.running = False

    def initialize(self) -> bool:
        """初始化 MT5 连接"""

        for attempt in range(1, self.max_retry + 1):
            try:
                logger.info(f"MT5 连接尝试 {attempt}/{self.max_retry}")

                if not mt5.initialize():
                    error = mt5.last_error()
                    logger.error(f"MT5 初始化失败: {error}")
                    time.sleep(self.retry_backoff ** attempt)
                    continue

                # 登录
                if not mt5.login(self.account, self.password, self.server):
                    error = mt5.last_error()
                    logger.error(f"MT5 登录失败: {error}")
                    mt5.shutdown()
                    time.sleep(self.retry_backoff ** attempt)
                    continue

                # 成功
                self.status.connected = True
                self.status.error_count = 0
                self.status.last_error = None
                logger.info(f"✅ MT5 连接成功: {self.account}@{self.server}")

                # 启动守护线程
                self.start_watchdog()

                return True

            except Exception as e:
                logger.error(f"MT5 连接异常: {e}")
                time.sleep(self.retry_backoff ** attempt)

        # 所有尝试失败
        self.status.connected = False
        self.status.last_error = "超过最大重试次数"
        return False

    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查终端连接
            if not mt5.terminal_info():
                logger.warning("MT5 终端未连接")
                return False

            # 检查账户信息
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("无法获取账户信息")
                return False

            self.status.last_check = datetime.now()
            return True

        except Exception as e:
            logger.error(f"健康检查异常: {e}")
            return False

    def reconnect(self) -> bool:
        """重新连接"""
        logger.warning("🔄 正在重新连接 MT5...")

        # 关闭现有连接
        try:
            mt5.shutdown()
        except:
            pass

        # 重新初始化
        return self.initialize()

    def start_watchdog(self):
        """启动守护线程"""
        if self.watchdog_thread and self.watchdog_thread.is_alive():
            logger.warning("守护线程已在运行")
            return

        self.running = True
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        logger.info(f"✅ MT5 守护线程已启动（间隔 {self.health_check_interval}s）")

    def _watchdog_loop(self):
        """守护线程主循环"""
        while self.running:
            time.sleep(self.health_check_interval)

            if not self.health_check():
                logger.error("❌ MT5 健康检查失败，尝试重连...")
                self.status.error_count += 1

                if self.reconnect():
                    logger.info("✅ MT5 重连成功")
                    self.status.error_count = 0
                else:
                    logger.error(f"❌ MT5 重连失败（失败次数: {self.status.error_count}）")

    def stop(self):
        """停止守护线程"""
        self.running = False
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=5)
        mt5.shutdown()
        logger.info("MT5 连接管理器已停止")

    def get_status(self) -> ConnectionStatus:
        """获取连接状态"""
        return self.status

# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = MT5ConnectionManager(
        account=12345678,
        password="your_password",
        server="MetaQuotes-Demo",
        health_check_interval=10
    )

    if manager.initialize():
        print("✅ MT5 连接成功")

        # 保持运行，观察守护线程
        try:
            while True:
                status = manager.get_status()
                print(f"状态: 连接={status.connected}, 错误次数={status.error_count}")
                time.sleep(5)
        except KeyboardInterrupt:
            manager.stop()
    else:
        print("❌ MT5 连接失败")
```

2. **集成到实盘交易系统**

```python
# bin/run_live_trading.py

from src.mt5.connection_manager import MT5ConnectionManager
import os
from dotenv import load_dotenv

load_dotenv()

# 初始化 MT5 连接
mt5_manager = MT5ConnectionManager(
    account=int(os.getenv("MT5_ACCOUNT")),
    password=os.getenv("MT5_PASSWORD"),
    server=os.getenv("MT5_SERVER"),
    health_check_interval=30
)

if not mt5_manager.initialize():
    logger.error("❌ MT5 连接失败，退出")
    exit(1)

# 运行 Backtrader 策略
# ...

# 停止时清理
mt5_manager.stop()
```

3. **测试重连机制**

```bash
# 手动断开 MT5 终端，观察自动重连
python3 src/mt5/connection_manager.py
```

**验收标准**:
- ✅ 初始连接成功率 > 95%
- ✅ 健康检查每 30 秒运行
- ✅ 掉线后 60 秒内自动重连
- ✅ 守护线程稳定运行

---

## 🟡 P1 优先级任务（建议改进）

### 任务 4: 数据注入管道（ML 预测 → Backtrader）

**问题**: 实盘模式下 `y_pred_proba` 如何实时更新

**预计时间**: 2 天

**实施方案**: 使用 Redis 作为消息队列

```python
# src/data_pipeline/redis_feed.py

import redis
import backtrader as bt
import json

class RedisMLFeed(bt.DataBase):
    """从 Redis 读取 ML 预测的数据源"""

    params = (
        ('redis_host', 'localhost'),
        ('redis_port', 6379),
        ('redis_channel', 'ml_predictions'),
    )

    def __init__(self):
        super().__init__()
        self.redis_client = redis.Redis(
            host=self.p.redis_host,
            port=self.p.redis_port,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(self.p.redis_channel)

        # 添加 ML 预测字段
        self.lines.y_pred_proba_long = bt.LineSeries()

    def _load(self):
        """加载下一个数据点"""
        message = self.pubsub.get_message(timeout=1)
        if message and message['type'] == 'message':
            data = json.loads(message['data'])

            # 更新 OHLCV
            self.lines.datetime[0] = bt.date2num(data['timestamp'])
            self.lines.open[0] = data['open']
            self.lines.high[0] = data['high']
            self.lines.low[0] = data['low']
            self.lines.close[0] = data['close']
            self.lines.volume[0] = data['volume']

            # ✅ 更新 ML 预测
            self.lines.y_pred_proba_long[0] = data.get('y_pred_proba', 0.5)

            return True

        return False
```

---

### 任务 5: 结构化日志系统

**预计时间**: 1 天

**实施方案**: 使用 `structlog` + SQLite

```python
# src/logging/trade_logger.py

import structlog
import sqlite3
from datetime import datetime

class TradeLogger:
    """交易决策日志记录器"""

    def __init__(self, db_path="logs/trades.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_table()

        self.logger = structlog.get_logger()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                action TEXT,
                price REAL,
                y_pred_proba REAL,
                kelly_fraction REAL,
                atr REAL,
                position_size REAL,
                reason TEXT
            )
        """)
        self.conn.commit()

    def log_decision(self, **kwargs):
        """记录交易决策"""
        self.conn.execute("""
            INSERT INTO trade_decisions
            (timestamp, symbol, action, price, y_pred_proba, kelly_fraction, atr, position_size, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            kwargs.get('symbol'),
            kwargs.get('action'),
            kwargs.get('price'),
            kwargs.get('y_pred_proba'),
            kwargs.get('kelly_fraction'),
            kwargs.get('atr'),
            kwargs.get('position_size'),
            kwargs.get('reason')
        ))
        self.conn.commit()

        # 同时输出到控制台
        self.logger.info("trade_decision", **kwargs)
```

---

## 📅 时间表

### 第 1 周

**第 1-2 天**:
- ✅ 任务 1: 修复 KellySizer 单位转换（0.5 天）
- ✅ 任务 2: 异步 API 调用重构（1 天）
- ✅ 任务 3 开始: MT5 连接管理器基础实现（0.5 天）

**第 3-5 天**:
- ✅ 任务 3 完成: MT5 连接管理器完整实现和测试（1 天）
- ✅ 任务 4 开始: 数据注入管道（Redis 集成）（2 天）

### 第 2 周

**第 6-7 天**:
- ✅ 任务 5: 结构化日志系统（1 天）
- ✅ 集成测试：所有组件联合测试（1 天）

**第 8-10 天**:
- ✅ 演示账户测试（2 天）
- ✅ 性能优化和调试（1 天）

---

## ✅ 验收标准

### 功能性验收

- ✅ KellySizer 正确转换 MT5 手数
- ✅ LLM 调用不阻塞交易
- ✅ MT5 连接自动重连成功率 > 95%
- ✅ ML 预测实时更新到策略
- ✅ 所有交易决策被完整记录

### 性能验收

- ✅ 订单执行成功率 > 95%
- ✅ 平均订单延迟 < 100ms
- ✅ Kelly 公式计算准确性 100%
- ✅ 连接保活成功率 > 99%

### 代码质量验收

- ✅ 测试覆盖率 > 80%
- ✅ 无 P0/P1 级别的 Gemini Pro 警告
- ✅ 所有关键路径有错误处理
- ✅ 完整的日志记录

---

## 🎯 今天可以立即开始的任务

### 任务 1.1: 修复 KellySizer（20 分钟）

```bash
# 1. 打开文件
code src/strategy/risk_manager.py

# 2. 复制上面的修复代码替换 _getsizing 方法

# 3. 运行测试
python3 tests/test_kelly_mt5_fix.py
```

### 任务 1.2: 创建异步 LLM 客户端（30 分钟）

```bash
# 1. 创建文件
touch src/async_llm_client.py

# 2. 复制上面的代码

# 3. 测试
python3 src/async_llm_client.py
```

### 任务 1.3: 创建 MT5 连接管理器（1 小时）

```bash
# 1. 创建目录和文件
mkdir -p src/mt5
touch src/mt5/__init__.py
touch src/mt5/connection_manager.py

# 2. 复制上面的代码

# 3. 配置 .env
echo "MT5_ACCOUNT=your_demo_account" >> .env
echo "MT5_PASSWORD=your_password" >> .env
echo "MT5_SERVER=MetaQuotes-Demo" >> .env

# 4. 测试（演示账户）
python3 src/mt5/connection_manager.py
```

---

## 📚 参考文档

- [Gemini Pro 完整审查报告](docs/reviews/gemini_review_20251221_055201.md)
- [工单 #010.9 完成报告](WORK_ORDER_010.9_FINAL_SUMMARY.md)
- [双 AI 协同计划](DUAL_AI_COLLABORATION_PLAN.md)
- [回测系统指南](docs/BACKTEST_GUIDE.md)
- [机器学习训练指南](docs/ML_ADVANCED_GUIDE.md)

---

## 🎓 学习建议

### 推荐阅读顺序

1. **Gemini Pro 审查报告**（30 分钟）
   - 理解所有 P0/P1 问题
   - 理解修复代码的原理

2. **Kelly 公式原理**（15 分钟）
   - 为什么需要单位转换
   - MT5 手数规则

3. **异步编程基础**（30 分钟）
   - `asyncio` 和 `aiohttp` 使用
   - 如何不阻塞主线程

4. **MT5 API 文档**（1 小时）
   - `mt5.initialize()` 和 `mt5.login()`
   - 订单执行和持仓查询

---

**准备好开始了吗？从任务 1.1 开始，20 分钟见效！**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
