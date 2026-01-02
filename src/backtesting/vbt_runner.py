#!/usr/bin/env python3
"""
TASK #018 - VectorBT 回测引擎
验证 Task #016 模型是否存在数据泄露
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import vectorbt as vbt

print("=" * 60)
print("TASK #018: VectorBT Backtesting Engine")
print("=" * 60)

# 1. 加载数据
print("\n[1/5] Loading data...")
df = pd.read_parquet("data/training_set.parquet")
print(f"  Loaded {len(df)} samples")

# 2. 加载模型
print("\n[2/5] Loading model...")
model = lgb.Booster(model_file="models/baseline_v1.txt")
print(f"  Model loaded: {model.num_trees()} trees")

# 3. 准备特征和价格
print("\n[3/5] Preparing features...")
feature_cols = ['sma_7', 'sma_14', 'sma_30', 'rsi_14', 'rsi_21',
                'macd', 'macd_signal', 'macd_hist',
                'bbands_upper', 'bbands_middle', 'bbands_lower', 'bbands_width',
                'atr_14', 'stochastic_k', 'stochastic_d']
X = df[feature_cols].values
close_price = df['close'].values  # 使用真实 close 价格

# 4. 生成预测
print("\n[4/5] Generating predictions...")
pred_y = model.predict(X)
print(f"  Predictions: min={pred_y.min():.6f}, max={pred_y.max():.6f}, mean={pred_y.mean():.6f}")

# 5. 生成交易信号
print("\n[5/5] Running backtest...")
entries = pred_y > 0.0001   # 做多信号（降低阈值）
exits = pred_y < -0.0001    # 平仓信号（降低阈值）

# 执行回测
pf = vbt.Portfolio.from_signals(
    close=close_price,
    entries=entries,
    exits=exits,
    fees=0.0001,      # 0.01% 手续费
    slippage=0.0001,  # 0.01% 滑点
    freq='1D'         # 日线数据
)

# 输出统计
print("\n" + "=" * 60)
print("BACKTEST RESULTS")
print("=" * 60)
print(pf.stats())

print("\n" + "=" * 60)
print("LEAKAGE DIAGNOSIS")
print("=" * 60)
sharpe = pf.sharpe_ratio()
print(f"Sharpe Ratio: {sharpe:.4f}")

if sharpe > 5.0:
    print("⚠️  VERDICT: LEAKED - Sharpe Ratio 过高，疑似数据泄露")
    print("   Task #016 模型可能使用了未来数据计算特征")
else:
    print("✅ VERDICT: SAFE - Sharpe Ratio 合理")

print("=" * 60)
