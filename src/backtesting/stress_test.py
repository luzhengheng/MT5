#!/usr/bin/env python3
"""
TASK #022 - Stress Testing & Scenario Analysis Engine
策略压力测试与极端场景模拟
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import vectorbt as vbt
from sklearn.preprocessing import StandardScaler

print("=" * 60)
print("TASK #022: Stress Testing & Scenario Analysis")
print("=" * 60)

# 1. 加载数据
print("\n[1/6] Loading data...")
df = pd.read_parquet("data/real_market_data.parquet")
df = df.sort_values('timestamp').reset_index(drop=True)
print(f"  Loaded {len(df)} samples")

# 2. 特征工程
print("\n[2/6] Engineering features...")
df['sma_7'] = df['close'].rolling(7).mean()
df['sma_14'] = df['close'].rolling(14).mean()
df['sma_30'] = df['close'].rolling(30).mean()
df['rsi_14'] = 100 - (100 / (1 + df['close'].diff().clip(lower=0).rolling(14).mean() /
                                   (-df['close'].diff().clip(upper=0).rolling(14).mean())))
df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
df['macd_signal'] = df['macd'].ewm(span=9).mean()
df['atr_14'] = (df['high'] - df['low']).rolling(14).mean()
df['target'] = df['close'].pct_change().shift(-1)
df = df.dropna().reset_index(drop=True)

# 训练简单模型
feature_cols = ['sma_7', 'sma_14', 'sma_30', 'rsi_14', 'macd', 'macd_signal', 'atr_14']
train_size = int(len(df) * 0.7)
train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:]

scaler = StandardScaler()
X_train = pd.DataFrame(scaler.fit_transform(train_df[feature_cols]), columns=feature_cols)
y_train = train_df['target'].values
X_test = pd.DataFrame(scaler.transform(test_df[feature_cols]), columns=feature_cols)

model = lgb.LGBMRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print(f"  Model trained on {len(train_df)} samples, tested on {len(test_df)} samples")

# 3. 滑点敏感性测试 (Break-even Slippage)
print("\n[3/6] Testing slippage sensitivity...")
slippage_range = np.arange(0, 11, 1)  # 0-10 bps
sharpe_results = []

for slip_bps in slippage_range:
    slip_pct = slip_bps / 10000.0
    entries = predictions > 0.0001
    exits = predictions < -0.0001

    pf = vbt.Portfolio.from_signals(
        close=test_df['close'].values,
        entries=entries,
        exits=exits,
        fees=0.0001,
        slippage=slip_pct,
        freq='1D'
    )
    sharpe = pf.sharpe_ratio()
    sharpe_results.append(sharpe)

# 找到 Break-even Slippage
sharpe_arr = np.array(sharpe_results)
breakeven_idx = np.where(sharpe_arr <= 0)[0]
if len(breakeven_idx) > 0:
    breakeven_slippage = slippage_range[breakeven_idx[0]]
else:
    breakeven_slippage = slippage_range[-1]

print(f"  Break-even Slippage: {breakeven_slippage:.2f} bps")

# 4. Monte Carlo 风险模拟
print("\n[4/6] Running Monte Carlo simulation...")
returns = test_df['close'].pct_change().dropna().values
n_simulations = 1000
bootstrap_returns = []

np.random.seed(42)
for _ in range(n_simulations):
    sampled_returns = np.random.choice(returns, size=len(returns), replace=True)
    bootstrap_returns.append(sampled_returns)

# 计算 VaR 和 CVaR
all_final_returns = [np.prod(1 + r) - 1 for r in bootstrap_returns]
var_95 = np.percentile(all_final_returns, 5)
cvar_95 = np.mean([r for r in all_final_returns if r <= var_95])

print(f"  95% VaR: {var_95:.4f}")
print(f"  95% CVaR: {cvar_95:.4f}")

# 5. 闪崩场景注入
print("\n[5/6] Injecting flash crash scenario...")
crash_df = test_df.copy()
crash_idx = len(crash_df) // 2
crash_df.loc[crash_idx:crash_idx+5, 'close'] *= 0.95  # -5% crash

# 重新计算特征
crash_df['sma_7'] = crash_df['close'].rolling(7).mean()
crash_df['sma_14'] = crash_df['close'].rolling(14).mean()
crash_df['sma_30'] = crash_df['close'].rolling(30).mean()
crash_df = crash_df.dropna()

X_crash = pd.DataFrame(scaler.transform(crash_df[feature_cols]), columns=feature_cols)
pred_crash = model.predict(X_crash)

entries_crash = pred_crash > 0.0001
exits_crash = pred_crash < -0.0001

pf_crash = vbt.Portfolio.from_signals(
    close=crash_df['close'].values,
    entries=entries_crash,
    exits=exits_crash,
    fees=0.0001,
    slippage=0.0001,
    freq='1D'
)

crash_sharpe = pf_crash.sharpe_ratio()
crash_max_dd = pf_crash.max_drawdown()

print(f"  Crash Scenario Sharpe: {crash_sharpe:.4f}")
print(f"  Crash Scenario Max DD: {crash_max_dd:.2%}")

# 6. 输出结果
print("\n" + "=" * 60)
print("STRESS TEST SUMMARY")
print("=" * 60)
print(f"Break-even Slippage: {breakeven_slippage:.2f} bps")
print(f"95% VaR: {var_95:.4f}")
print(f"95% CVaR: {cvar_95:.4f}")
print(f"Flash Crash Max DD: {crash_max_dd:.2%}")

# 判定
if breakeven_slippage < 1.0:
    verdict = "FAIL - Strategy too fragile (slippage tolerance < 1bps)"
elif crash_max_dd > 0.20:
    verdict = "FAIL - Excessive drawdown in crash scenario (> 20%)"
else:
    verdict = "PASS - Strategy shows acceptable stress resilience"

print(f"\n🎯 VERDICT: {verdict}")
print("=" * 60)
