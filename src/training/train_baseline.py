#!/usr/bin/env python3
"""
Baseline Model Training Script
Uses LightGBM for regression on technical indicators
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import json
from datetime import datetime

def main():
    # Load dataset
    df = pd.read_parquet('data/training_set.parquet')
    print(f"📊 Loaded dataset: {len(df)} rows")

    # Define features and target
    feature_cols = [col for col in df.columns if col not in ['ticker', 'event_timestamp', 'target', 'created_timestamp', 'close', 'timestamp']]
    X = df[feature_cols]
    y = df['target']

    # Time series split (80/20)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"🔹 Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Train LightGBM
    params = {
        'objective': 'regression',
        'metric': 'mse',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'verbose': -1
    }

    train_data = lgb.Dataset(X_train, label=y_train)
    model = lgb.train(params, train_data, num_boost_round=100)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print(f"\n📈 Model Performance:")
    print(f"   Test MSE: {mse:.6f}")
    print(f"   Test MAE: {mae:.6f}")

    # Feature importance
    importance = model.feature_importance()
    print(f"\n🔍 Top 5 Features:")
    for i, (feat, imp) in enumerate(sorted(zip(feature_cols, importance), key=lambda x: x[1], reverse=True)[:5]):
        print(f"   {i+1}. {feat}: {imp}")

    # Save model
    model.save_model('models/baseline_v1.txt')
    print(f"\n✅ Model saved to: models/baseline_v1.txt")

    # Save metadata
    metadata = {
        'model_type': 'LightGBM',
        'train_date': datetime.now().isoformat(),
        'features': feature_cols,
        'metrics': {'mse': float(mse), 'mae': float(mae)},
        'params': params,
        'train_size': len(X_train),
        'test_size': len(X_test)
    }
    with open('models/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved to: models/model_metadata.json")

if __name__ == '__main__':
    main()
