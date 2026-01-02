#!/usr/bin/env python3
"""
TASK #021 - Walk-Forward Analysis Engine
样本外滚动前进验证
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import vectorbt as vbt
from sklearn.preprocessing import StandardScaler

print("=" * 60)
print("TASK #021: Walk-Forward Analysis")
print("=" * 60)

# 1. 加载数据
print("\n[1/6] Loading data...")
df = pd.read_parquet("data/real_market_data.parquet")
df = df.sort_values('timestamp').reset_index(drop=True)
print(f"  Loaded {len(df)} samples ({df.timestamp.min()} to {df.timestamp.max()})")

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
print(f"  Features ready: {len(df)} samples after dropna")

# 3. Walk-Forward 配置
print("\n[3/6] Configuring Walk-Forward...")
train_len = 3 * 365  # 3年训练
test_len = 1 * 365   # 1年测试
step = 1 * 365       # 每次前进1年

feature_cols = ['sma_7', 'sma_14', 'sma_30', 'rsi_14', 'macd', 'macd_signal', 'atr_14']
windows = []
start = 0
while start + train_len + test_len <= len(df):
    windows.append({
        'train_start': start,
        'train_end': start + train_len,
        'test_start': start + train_len,
        'test_end': start + train_len + test_len
    })
    start += step

print(f"  Generated {len(windows)} rolling windows")

# 4. 执行 Walk-Forward
print("\n[4/6] Running Walk-Forward validation...")
all_predictions = []
all_actuals = []
all_prices = []

for i, w in enumerate(windows):
    train_df = df.iloc[w['train_start']:w['train_end']]
    test_df = df.iloc[w['test_start']:w['test_end']]

    # 训练集标准化
    scaler = StandardScaler()
    X_train = pd.DataFrame(scaler.fit_transform(train_df[feature_cols]), columns=feature_cols)
    y_train = train_df['target'].values

    # 测试集标准化（使用训练集参数）
    X_test = pd.DataFrame(scaler.transform(test_df[feature_cols]), columns=feature_cols)
    y_test = test_df['target'].values

    # 训练模型（每次重新初始化）
    model = lgb.LGBMRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
    model.fit(X_train, y_train)

    # 预测
    pred = model.predict(X_test)

    # 记录结果
    all_predictions.extend(pred)
    all_actuals.extend(y_test)
    all_prices.extend(test_df['close'].values)

    print(f"  Window {i+1}/{len(windows)}: Train {train_df.timestamp.min().date()} to {train_df.timestamp.max().date()}, "
          f"Test {test_df.timestamp.min().date()} to {test_df.timestamp.max().date()}")

# 5. OOS 回测
print("\n[5/6] Running OOS backtest...")
all_predictions = np.array(all_predictions)
all_prices = np.array(all_prices)

entries = all_predictions > 0.0001
exits = all_predictions < -0.0001

pf = vbt.Portfolio.from_signals(
    close=all_prices,
    entries=entries,
    exits=exits,
    fees=0.0001,
    slippage=0.0001,
    freq='1D'
)

# 6. 输出结果
print("\n" + "=" * 60)
print("OOS BACKTEST RESULTS")
print("=" * 60)
print(pf.stats())

print("\n" + "=" * 60)
print("ROBUSTNESS ANALYSIS")
print("=" * 60)
oos_sharpe = pf.sharpe_ratio()
print(f"OOS Sharpe Ratio: {oos_sharpe:.4f}")

if oos_sharpe < 0.5:
    print("⚠️  VERDICT: Strategy FAILED - Overfitting confirmed")
elif oos_sharpe > 1.0:
    print("✅ VERDICT: Strategy ROBUST - Good generalization")
else:
    print("⚡ VERDICT: Strategy MARGINAL - Needs improvement")

print("=" * 60)
