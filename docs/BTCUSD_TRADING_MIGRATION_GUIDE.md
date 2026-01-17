# BTC/USD 交易品种切换指南

**更新时间**: 2026-01-17
**目标**: 将交易品种从 EURUSD 切换到 BTC/USD
**目的**: 利用周末的交易机会进行持续测试
**预计收益**: +40% 交易天数 (+104天/年)

---

## 📊 为什么切换到 BTC/USD?

### 主要优势

| 优势 | 说明 | 影响 |
|------|------|------|
| **周末交易** | BTC/USD 全天 24/7 交易 | ✅ 周末不中断 (+2天/周) |
| **高波动性** | BTC 日均波动 800-1500 pips | ✅ 更多交易机会 |
| **高流动性** | BTC 最流动的加密品种 | ✅ 快速成交，低滑点 |
| **更多数据** | 年交易天数 365 天 vs 250 天 | ✅ 模型训练数据 +46% |
| **系统稳定性** | 测试 24/7 系统可靠性 | ✅ 验证系统周末表现 |

### 交易时间对比

```
┌─ 交易天数对比 ─────────────────────┐
│                                     │
│  EURUSD:  [====] 250 天/年 (69%)   │
│  BTC/USD: [========] 365 天/年 (100%) │
│                                     │
│  增加: +115 天 (+46%)              │
└─────────────────────────────────────┘
```

---

## 🚀 切换实施步骤

### Step 1: 准备工作 (15 分钟)

```bash
# 1.1 停止当前策略
systemctl stop mt5-strategy

# 1.2 备份当前配置
cp config/strategy_eurusd.yaml config/strategy_eurusd.yaml.bak

# 1.3 查看当前 EURUSD 持仓
python3 src/gateway/get_positions.py
```

**检查清单**:
- [ ] 所有 EURUSD 持仓已平仓
- [ ] 账户余额正常
- [ ] 备份文件已生成

### Step 2: 配置更新 (10 分钟)

```bash
# 2.1 使用新配置
cp config/strategy_btcusd.yaml config/strategy_active.yaml

# 2.2 验证配置内容
cat config/strategy_active.yaml | grep -A 5 "symbol:"

# Expected output:
# symbol: "BTCUSD.s"
```

**配置检查**:
- [ ] symbol 已改为 "BTCUSD.s"
- [ ] stop_loss_pips 已改为 500
- [ ] take_profit_pips 已改为 1000
- [ ] trading_hours.mode 已改为 "24/7"

### Step 3: MT5 验证 (10 分钟)

```bash
# 3.1 测试 MT5 是否支持 BTC/USD
python3 -c "
from src.gateway.mt5_service import MT5Service
mt5 = MT5Service()
if mt5.is_connected():
    # 查询 BTC/USD 信息
    info = mt5.get_symbol_info('BTCUSD.s')
    print(f'✅ BTC/USD 可用: {info}')
else:
    print('❌ MT5 未连接')
"

# 3.2 测试实时报价
python3 -c "
from src.gateway.market_data_feed import MarketDataFeed
feed = MarketDataFeed()
feed.subscribe('BTCUSD.s', '1H')
tick = feed.get_latest_tick()
print(f'Latest BTC/USD: ${tick[\"price\"]:.2f}')
"
```

**验证项**:
- [ ] MT5 能访问 BTCUSD.s 报价
- [ ] 历史数据可下载 (1H, 4H, 1D)
- [ ] 实时 tick 正常接收

### Step 4: 策略启动 (5 分钟)

```bash
# 4.1 启动新策略 (纸面交易模式)
python3 src/execution/live_launcher.py \
  --symbol BTCUSD.s \
  --mode PAPER_TRADING \
  --volume 0.001 \
  --risk-percentage 0.5

# 4.2 查看日志
tail -f logs/btcusd_trading.log

# 期望输出:
# [INFO] Strategy BTC_USD_Sentinel initialized
# [INFO] Symbol: BTCUSD.s
# [INFO] Trading Mode: PAPER_TRADING
# [INFO] Volume: 0.001 lot
```

**启动检查**:
- [ ] 策略成功启动
- [ ] 无错误日志
- [ ] 正在接收 tick 数据

### Step 5: 纸面交易验证 (3-7 天)

**目标**: 验证策略在 BTC/USD 上的表现

```bash
# 5.1 监控日志
tail -100 logs/btcusd_trading.log | grep -E "SIGNAL|TRADE|ERROR"

# 5.2 生成报告
python3 src/analysis/generate_report.py \
  --symbol BTCUSD.s \
  --mode PAPER \
  --days 7
```

**验证项**:
- [ ] 信号生成正常 (每天 2-5 个信号)
- [ ] 订单执行成功 (纸面成交率 >95%)
- [ ] 收益率正常 (期望 +0.5% - +1.5% 周收益)
- [ ] 无异常错误 (错误率 <1%)
- [ ] 周末成功交易 (至少 4 个周末交易)

### Step 6: 实盘上线 (如果验证通过)

```bash
# 6.1 关闭纸面交易
systemctl stop mt5-strategy

# 6.2 启动实盘交易
python3 src/execution/live_launcher.py \
  --symbol BTCUSD.s \
  --mode LIVE_TRADING \
  --volume 0.001 \
  --risk-percentage 0.5

# 6.3 启动监控
python3 src/execution/risk_monitor.py \
  --alert-level CRITICAL \
  --email admin@example.com
```

---

## ⚠️ 关键参数调整

### 风险参数

| 参数 | EURUSD | BTC/USD | 原因 |
|------|--------|---------|------|
| **止损** | 100 pips | 500 pips | BTC 波动性 5 倍 |
| **获利** | 200 pips | 1000 pips | BTC 日均波动大 |
| **手数** | 0.001 lot | 0.001 lot | 保持相同风险 |
| **风险%** | 0.5% | 0.5% | 保持保守 |
| **最大回撤** | 10% | 10% | 相同限制 |

### 市场特性调整

```yaml
# 交易时间
- EURUSD: 周一 17:00 - 周五 16:00 UTC
+ BTC/USD: 全天 24/7 (周末包括)

# 流动性
- EURUSD: 日均成交量 1.5T USD
+ BTC/USD: 日均成交量 20-30B USD (周末可能下降)

# 点差
- EURUSD: 正常 1-3 pips
+ BTC/USD: 正常 5-10 USD (周末可能扩大到 20+ USD)

# 滑点
- EURUSD: 快速成交 (<100ms)
+ BTC/USD: 周末可能延迟到 500-1000ms
```

---

## 📈 预期收益和风险

### 预期收益

```
年交易天数增加:
  • 当前 (EURUSD): 250 天
  • 目标 (BTC/USD): 365 天
  • 增加: +115 天 (+46%)

潜在收益提升:
  • 基于相同胜率 (55%)
  • 预期年收益: +46% (相同交易表现)

周末交易机会:
  • 每周末: 2 天 × ~3 小时 = 6 小时
  • 年度: 104 天 × 6 小时 = 624 小时
  • 额外交易机会: ~300-500 次
```

### 风险及缓解

| 风险 | 影响 | 缓解方案 |
|------|------|--------|
| **流动性下降** | 周末滑点大 | 周末降低手数 50% |
| **点差扩大** | 交易成本上升 | 监控点差自动暂停 |
| **波动性大** | 止损被触发概率高 | 更宽的止损 (500 pips) |
| **系统bug** | 周末无人值守 | 启用自动监控告警 |
| **滑点增加** | 实际成交价差 | 使用市价单替代限价单 |

---

## 🔍 监控和验证

### 实时监控指标

```bash
# 查看实时交易状态
python3 -c "
import requests
resp = requests.get('http://localhost:8080/api/status')
status = resp.json()
print(f\"Symbol: {status['symbol']}\")
print(f\"Mode: {status['mode']}\")
print(f\"Position: {status['position_size']} lot\")
print(f\"P&L: {status['pnl']:.2f} USD\")
print(f\"Last Signal: {status['last_signal_time']}\")
"
```

### 关键指标

- **信号生成**: 每小时 0.5-1 个信号
- **成交率**: >95% (纸面) / >85% (实盘周末)
- **平均获利**: +10-20 USD/成功单
- **最大回撤**: <2% 周回撤
- **错误率**: <1% 异常错误

### 验证清单

```
□ MT5 能访问 BTCUSD.s 报价
□ 历史数据完整 (至少 6 个月)
□ 实时 tick 正常接收
□ 策略信号正常生成
□ 纸面交易 7 天无异常
□ 周末成功执行至少 1 笔交易
□ 回撤在 <10% 范围内
□ 日志完整无错误
□ 监控告警正常
□ 备份和恢复机制就绪
```

---

## 🛠️ 快速回滚

如果发现问题，可快速回滚到 EURUSD:

```bash
# 紧急停止
systemctl stop mt5-strategy

# 恢复备份配置
cp config/strategy_eurusd.yaml.bak config/strategy_active.yaml

# 重新启动
systemctl start mt5-strategy

# 验证
tail -f logs/eurusd_trading.log
```

**回滚触发条件**:
- 日亏损 >$100
- 连续 5 笔亏损
- 系统错误率 >5%
- 流动性严重不足

---

## 📝 配置文件位置

- **新配置**: `config/strategy_btcusd.yaml`
- **备份配置**: `config/strategy_eurusd.yaml.bak`
- **日志**: `logs/btcusd_trading.log`
- **报告**: `reports/btcusd_report_*.json`

---

## 📞 支持和沟通

| 问题 | 联系 |
|------|------|
| 技术问题 | 查看 `logs/btcusd_trading.log` |
| 性能问题 | 运行 `python3 src/analysis/diagnose.py` |
| 紧急情况 | 运行 `回滚` 命令 |

---

## ✅ 最终检查

启动前，请确认:

- [ ] 已停止所有 EURUSD 交易
- [ ] EURUSD 持仓已全部平仓
- [ ] 账户余额检查无误
- [ ] BTC/USD 配置文件已准备
- [ ] MT5 能访问 BTCUSD.s 报价
- [ ] 日志目录有写权限
- [ ] 监控告警已配置
- [ ] 回滚计划已就绪
- [ ] 团队已知会
- [ ] 备份已完成

---

**生成者**: Claude Sonnet 4.5
**生成时间**: 2026-01-17
**版本**: 1.0

