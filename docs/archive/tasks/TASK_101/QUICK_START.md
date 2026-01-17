# Task #101 快速启动指南
## 交易执行桥接 - 快速上手

### 前置条件

✅ Task #100 (StrategyEngine) 已部署
✅ Task #099 (FusionEngine) 已部署
✅ TimescaleDB 和 ChromaDB 服务运行中
✅ 融合数据已生成

---

## 快速开始 (30 秒)

### 1. 运行审计测试

验证执行桥接实现无误:

```bash
cd /opt/mt5-crs
python3 scripts/audit_task_101.py
```

预期输出:
```
✅ GATE 1 AUDIT PASSED
Tests run: 15
Successes: 15
```

### 2. 执行 Dry-Run 模式

```bash
python3 scripts/execution/bridge.py --dry-run --symbol AAPL --limit 5
```

参数说明:
- `--dry-run`: 仅打印订单, 不执行
- `--symbol AAPL`: 交易品种
- `--limit 5`: 最多打印 5 个订单
- `--balance 10000.0`: 账户余额 (可选, 默认 10000)

### 3. 查看生成的订单

输出示例:

```
🎯 DRY RUN EXECUTION MODE
======================================================================
📅 Timestamp: 2026-01-14T11:23:00
📦 Total Orders: 3
======================================================================

📊 ORDER #1
======================================================================
Action:    TRADE_ACTION_DEAL
Symbol:    AAPL
Type:      ORDER_TYPE_BUY
Volume:    0.5000 lots
Price:     150.00
SL:        148.50
TP:        153.00
Magic:     123456
Comment:   SentimentMomentum: RSI=35.2, Sentiment=0.75, Conf=80%
Timestamp: 2026-01-14 11:00:00
======================================================================

✅ Dry run execution complete
```

---

## 在代码中使用

### 基础用法

```python
from scripts.execution.risk import RiskManager
from scripts.execution.bridge import ExecutionBridge
from scripts.data.fusion_engine import FusionEngine

# 初始化风险管理器
risk_mgr = RiskManager(
    account_balance=10000.0,
    risk_pct=1.0
)

# 初始化执行桥接
bridge = ExecutionBridge(
    risk_manager=risk_mgr,
    dry_run=True
)

# 获取融合数据 (来自 Task #099)
engine = FusionEngine()
fused_data = engine.get_fused_data('AAPL', days=60)

# 转换信号为订单
orders = bridge.convert_signals_to_orders(fused_data)

# 干运行执行
bridge.execute_dry_run(orders)

# 打印执行历史
history = bridge.get_execution_history()
print(f"执行了 {len(history)} 个订单")
```

### 自定义参数

```python
# 调整风险管理参数
risk_mgr = RiskManager(
    account_balance=50000.0,      # 账户余额
    risk_pct=2.0,                 # 每笔交易风险 2%
    min_volume=0.01,              # 最小手数
    max_volume=100.0              # 最大手数
)

# 调整执行参数
bridge = ExecutionBridge(
    risk_manager=risk_mgr,
    default_magic=789123,         # 魔法数字
    tp_pct=3.0,                   # TP 为入场价的 3%
    sl_pct=1.5,                   # SL 为入场价的 1.5%
    dry_run=False                 # 实际执行 (需要 MT5 连接)
)
```

### 订单过滤

```python
# 只执行高信心订单
high_conf_orders = [
    o for o in orders
    if o.get('comment', '').find('Conf=100%') > -1
]

# 按类型过滤
buy_orders = [
    o for o in orders
    if o['type'] == 'ORDER_TYPE_BUY'
]

# 按符号过滤
aapl_orders = [
    o for o in orders
    if o['symbol'] == 'AAPL'
]
```

---

## 测试与验证

### 运行单元测试

```bash
python3 scripts/audit_task_101.py
```

包含以下测试:

| 测试 | 功能 |
|-----|------|
| Test 1 | RiskManager 初始化 |
| Test 2 | 手数计算 |
| Test 3 | TP/SL 计算 |
| Test 4 | BUY 订单验证 |
| Test 5 | SELL 订单验证 |
| Test 6 | 重复订单防护 |
| Test 7 | ExecutionBridge 初始化 |
| Test 8 | BUY 信号转订单 |
| Test 9 | SELL 信号转订单 |
| Test 10 | 中立信号忽略 |
| Test 11 | 批量转换 |
| Test 12 | TP/SL 精度 |
| Test 13 | 干运行执行 |
| Test 14 | 无效信号处理 |
| Test 15 | 覆盖率报告 |

### 手工测试

```python
import pandas as pd
from scripts.execution.bridge import ExecutionBridge
from scripts.execution.risk import RiskManager

# 创建测试信号数据
dates = pd.date_range('2025-12-01', periods=50, freq='1h')
signals = pd.DataFrame({
    'timestamp': dates,
    'signal': [1, -1, 0, 1, -1] * 10,  # BUY, SELL, NEUTRAL 混合
    'confidence': 0.8,
    'reason': 'Test signal',
    'rsi': 35.0,
    'sentiment_score': 0.75,
    'close': 150.0,
    'symbol': 'AAPL'
}, index=dates)
signals.index.name = 'time'

# 转换
risk_mgr = RiskManager()
bridge = ExecutionBridge(risk_manager=risk_mgr, dry_run=True)
orders = bridge.convert_signals_to_orders(signals)

print(f"生成了 {len(orders)} 个订单")
for order in orders[:3]:
    print(f"  - {order['type']}: {order['symbol']} @ {order['price']}")
```

---

## RiskManager API 参考

### 位置管理

```python
# 计算手数
lot_size = risk_mgr.calculate_lot_size(
    entry_price=150.0,
    stop_loss_price=148.5,
    balance=10000.0
)

# 计算 TP/SL
tp, sl = risk_mgr.calculate_tp_sl(
    entry_price=100.0,
    action='BUY',
    tp_pct=2.0,
    sl_pct=1.0
)
```

### 订单验证

```python
# 验证订单
is_valid, msg = risk_mgr.validate_order(
    order={
        'action': 'TRADE_ACTION_DEAL',
        'symbol': 'AAPL',
        'volume': 0.5,
        'type': 'ORDER_TYPE_BUY',
        'price': 150.0,
        'sl': 148.5,
        'tp': 153.0
    },
    current_price=150.0
)

if is_valid:
    print("✅ 订单通过验证")
else:
    print(f"❌ 订单验证失败: {msg}")
```

### 重复防护

```python
# 检查重复
if risk_mgr.check_duplicate_order('AAPL', 'BUY'):
    print("⚠️ 同方向重复订单, 跳过")
else:
    # 注册订单
    risk_mgr.register_order('AAPL', 'BUY', 0.5, 150.0)

# 关闭订单
risk_mgr.unregister_order('AAPL', 'BUY')
```

---

## ExecutionBridge API 参考

### 信号转订单

```python
# 单个信号转订单
row = pd.Series({
    'signal': 1,
    'confidence': 0.8,
    'close': 150.0,
    'symbol': 'AAPL'
})

order = bridge.signal_to_order(row)
if order:
    print(f"✅ 生成订单: {order['type']}")
```

### 批量处理

```python
# 批量转换
orders = bridge.convert_signals_to_orders(
    signals_df=fused_data,
    symbol='AAPL',
    limit=10
)

print(f"📦 生成了 {len(orders)} 个订单")
```

### 执行

```python
# 干运行
bridge.execute_dry_run(orders)

# 实际执行 (需要 MT5 连接)
result = bridge.execute_orders(orders, mt5_connection=mt5_conn)
print(f"成功: {result['successful']}, 失败: {result['failed']}")
```

---

## 常见问题

### Q1: 订单生成为空?

**原因**: 信号数据缺失或全为中立信号 (signal=0)

**解决方案**:
1. 检查融合数据是否包含 BUY/SELL 信号
2. 检查 Task #100 是否成功生成信号

```python
# 检查信号分布
print(signals_df['signal'].value_counts())
# 应该包含 1 (BUY) 和 -1 (SELL)
```

### Q2: 如何修改 TP/SL 比例?

```python
bridge.tp_pct = 3.0   # TP 改为 3%
bridge.sl_pct = 2.0   # SL 改为 2%

orders = bridge.convert_signals_to_orders(signals_df)
```

### Q3: 如何使用不同的账户余额?

```python
# 创建新的风险管理器
risk_mgr = RiskManager(account_balance=50000.0)

# 创建新的桥接
bridge = ExecutionBridge(risk_manager=risk_mgr)
```

### Q4: 如何添加自定义魔法数字?

```python
bridge = ExecutionBridge(
    risk_manager=risk_mgr,
    default_magic=999999  # 自定义魔法数字
)
```

### Q5: 订单格式是什么?

```python
{
    'action': 'TRADE_ACTION_DEAL',          # 固定值
    'symbol': 'AAPL',                        # 交易品种
    'type': 'ORDER_TYPE_BUY',               # BUY 或 SELL
    'volume': 0.5,                          # 手数
    'price': 150.0,                         # 入场价
    'sl': 148.5,                            # 止损价
    'tp': 153.0,                            # 获利价
    'magic': 123456,                        # 魔法数字
    'comment': 'Strategy comment',          # 注释
    'timestamp': '2026-01-14T11:00:00'      # 时间戳
}
```

---

## 疑难排查

### ImportError: No module named 'scripts'

**解决**: 确保在项目根目录运行

```bash
cd /opt/mt5-crs
python3 scripts/execution/bridge.py
```

### AttributeError: 'NoneType' object has no attribute

**解决**: 检查融合数据是否为 None

```python
fused_data = engine.get_fused_data('AAPL', days=7)
if fused_data is None:
    print("❌ 没有融合数据")
else:
    orders = bridge.convert_signals_to_orders(fused_data)
```

### ValueError: Order validation failed

**解决**: 检查订单参数

```python
is_valid, msg = risk_mgr.validate_order(order)
if not is_valid:
    print(f"❌ {msg}")  # 查看具体错误信息
```

---

## 集成下一步

当 Task #102 (MT5 连接器) 完成后，订单将被发送到真实的 MT5 终端:

```python
# 未来示例 (Task #102 中实现)
from scripts.broker.mt5_connector import MT5Connector

# 连接到 MT5
mt5 = MT5Connector(host='localhost', port=5000)

# 执行订单
result = bridge.execute_orders(orders, mt5_connection=mt5)

# 监控执行
for order_result in result['orders']:
    print(f"订单状态: {order_result['status']}")
```

---

## 支持与反馈

报告问题: 创建 Issue 或联系团队
问题模板: 包括错误日志、订单数据、可重现步骤

---

**最后更新**: 2026-01-14
**版本**: 1.0 (Task #101)
