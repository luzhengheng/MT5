# Task #100 快速启动指南
## SentimentalMomentum 策略 - 快速上手

### 前置条件

✅ Task #099 (FusionEngine) 已部署
✅ TimescaleDB 和 ChromaDB 服务运行中
✅ 融合数据已生成

---

## 快速开始 (30 秒)

### 1. 运行审计测试

验证策略实现无误:

```bash
cd /opt/mt5-crs
python3 scripts/audit_task_100.py
```

预期输出:
```
✅ GATE 1 AUDIT PASSED
Tests run: 11
Successes: 11
```

### 2. 生成交易信号

```bash
python3 scripts/strategy/strategies/sentiment_momentum.py \
    --symbol AAPL \
    --days 60 \
    --limit 5
```

参数说明:
- `--symbol AAPL`: 交易品种 (可改为 MSFT, GOOGL 等)
- `--days 60`: 回溯天数
- `--limit 5`: 打印最近 N 个信号

### 3. 查看生成的信号

输出示例:

```
📈 Backtest Summary:
  Total Signals: 95
  BUY Signals: 8
  SELL Signals: 2
  Avg Confidence: 42.3%

📊 Recent 5 Trading Signals:
============================================================
1. 🟢 BUY | Time: 2025-12-15 14:00 | Price: 259.18
   RSI: 35.2 | Sentiment: 0.75 | Confidence: 68%

2. 🔴 SELL | Time: 2025-12-14 10:30 | Price: 261.45
   RSI: 68.9 | Sentiment: -0.82 | Confidence: 71%
```

---

## 在代码中使用策略

### 基础用法

```python
from scripts.strategy.strategies.sentiment_momentum import SentimentMomentumStrategy
from scripts.data.fusion_engine import FusionEngine

# 初始化
strategy = SentimentMomentumStrategy(symbol="AAPL")
engine = FusionEngine()

# 获取融合数据
fused_data = engine.get_fused_data("AAPL", days=60)

# 生成信号
signals = strategy.run(fused_data)

# 获取摘要统计
summary = strategy.backtest_summary(signals)
print(f"BUY 信号: {summary['buy_signals']}")
print(f"SELL 信号: {summary['sell_signals']}")
```

### 自定义参数

```python
# 调整策略参数
strategy = SentimentMomentumStrategy(
    symbol="MSFT",
    rsi_period=14,  # RSI 周期
    sentiment_buy_threshold=0.5,  # 买入舆情阈值
    sentiment_sell_threshold=-0.5,  # 卖出舆情阈值
    rsi_oversold=35,  # 超卖水平
    rsi_overbought=65  # 超买水平
)

signals = strategy.run(fused_data)
```

### 信号过滤

```python
# 只获取高信心信号
high_confidence = signals[signals['confidence'] > 0.7]

# 只获取买入信号
buy_signals = signals[signals['signal'] == 1]

# 只获取卖出信号
sell_signals = signals[signals['signal'] == -1]

print(f"高信心买入信号: {len(high_confidence[high_confidence['signal'] == 1])}")
```

---

## 测试与验证

### 运行单元测试

```bash
python3 scripts/audit_task_100.py
```

包含以下测试:

| 测试 | 功能 |
|-----|------|
| Test 1 | 策略初始化 |
| Test 2 | 输入验证 |
| Test 3 | RSI 计算 |
| Test 4 | 输出形状 |
| Test 5 | 信号值有效性 |
| Test 6 | **防未来函数验证** (关键) |
| Test 7 | 逻辑一致性 |
| Test 8 | 完整流程 |
| Test 9 | 抽象基类 |
| Test 10 | 边界情况 |

### 手工测试

```python
import pandas as pd
from scripts.strategy.strategies.sentiment_momentum import SentimentMomentumStrategy

# 创建合成测试数据
dates = pd.date_range('2025-12-01', periods=100, freq='1h')
df = pd.DataFrame({
    'close': 100 + (range(100) * 0.1),  # 上升趋势
    'open': 100 + (range(100) * 0.09),
    'high': 101 + (range(100) * 0.1),
    'low': 99 + (range(100) * 0.1),
    'volume': 1000000,
    'sentiment_score': 0.7  # 积极舆情
}, index=dates)
df.index.name = 'time'

strategy = SentimentMomentumStrategy()
signals = strategy.run(df)

# 验证结果
print(f"生成了 {len(signals)} 个信号")
print(f"买入信号: {(signals['signal'] == 1).sum()}")
print(f"卖出信号: {(signals['signal'] == -1).sum()}")
print(f"平均信心: {signals['confidence'].mean():.2%}")
```

---

## 常见问题

### Q1: 为什么没有生成信号?

**原因**: 数据中的情感分数为 0（缺少新闻数据）

**解决方案**:
1. 确认 Task #098 (Sentiment Analysis) 已完成
2. 检查 ChromaDB 中是否有新闻数据
3. 使用 `engine.get_fused_data()` 验证融合数据中的 sentiment_score

```python
from scripts.data.fusion_engine import FusionEngine
engine = FusionEngine()
data = engine.get_fused_data('AAPL')
print(data['sentiment_score'].describe())
```

### Q2: 如何修改策略逻辑?

编辑 `scripts/strategy/strategies/sentiment_momentum.py` 中的 `generate_signals()` 方法:

```python
def generate_signals(self, df):
    # 在这里修改信号生成逻辑
    # 例如: 修改阈值、添加新指标等

    # 重要: 测试你的修改
    # python3 scripts/audit_task_100.py
```

### Q3: 如何添加新策略?

1. 创建新文件: `scripts/strategy/strategies/my_strategy.py`
2. 继承 `StrategyBase`:

```python
from scripts.strategy.engine import StrategyBase, SignalType

class MyStrategy(StrategyBase):
    def validate_input(self, df):
        # 实现输入验证
        pass

    def generate_signals(self, df):
        # 实现信号生成
        pass
```

3. 运行测试确保无误
4. 在 `scripts/strategy/strategies/__init__.py` 中导出

### Q4: 信号数据结构是什么?

生成的信号 DataFrame 包含以下列:

```python
{
    'timestamp': datetime,      # 时间
    'signal': int,              # -1 (卖出), 0 (中立), 1 (买入)
    'confidence': float,        # 信心度 [0.0, 1.0]
    'reason': str,              # 信号原因描述
    'rsi': float,               # RSI 值
    'sentiment_score': float,   # 情感分数
    'close': float,             # 收盘价
    'open': float,              # 开盘价
    'high': float,              # 最高价
    'low': float,               # 最低价
    'volume': int               # 成交量
}
```

---

## 性能优化

### 大规模数据处理

对于大量数据,使用批处理:

```python
symbols = ['AAPL', 'MSFT', 'GOOGL']
strategy = SentimentMomentumStrategy()

for symbol in symbols:
    data = engine.get_fused_data(symbol, days=60)
    signals = strategy.run(data)
    print(f"{symbol}: {(signals['signal'] != 0).sum()} 信号生成")
```

### 内存优化

```python
# 只加载必要的列
import pandas as pd
parquet_file = 'data/fused_AAPL.parquet'
df = pd.read_parquet(
    parquet_file,
    columns=['close', 'sentiment_score']  # 只读需要的列
)
```

---

## 集成下一步

当 Task #101 (Execution Bridge) 完成后,信号将被转换为 MT5 订单:

```python
# 示例 (Task #101 中实现)
from scripts.broker.execution_bridge import ExecutionBridge

signals = strategy.run(fused_data)
bridge = ExecutionBridge()

for signal in signals[signals['signal'] != 0].iterrows():
    order = bridge.signal_to_order(signal)
    # bridge.place_order(order)  # 实盘执行
```

---

## 疑难排查

### 导入错误

```
ModuleNotFoundError: No module named 'scripts'
```

解决: 确保在项目根目录运行

```bash
cd /opt/mt5-crs
python3 scripts/...
```

### 数据库连接失败

```
psycopg2.OperationalError: could not connect to server
```

解决: 检查 PostgreSQL 连接:

```bash
psql -h localhost -U trader -d mt5_crs -c "SELECT 1"
```

### ChromaDB 错误

```
chromadb.errors.InvalidDimensionException
```

解决: 确保 ChromaDB 服务运行:

```bash
docker ps | grep chroma
```

---

## 支持与反馈

报告问题: 创建 Issue 或联系团队
问题模板: 包括错误日志、数据样本、可重现步骤

---

**最后更新**: 2026-01-14
**版本**: 1.0 (Task #100)
