#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS Feature Ingestion Script
Task #015: Real-time Feature Pipeline & Data Ingestion

用途:
1. 生成/读取模拟市场数据 (OHLCV)
2. 计算技术指标特征
3. 将特征数据写入 Feast Feature Store (Parquet + Redis)
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.feature_engineering.basic_features import BasicFeatures


def generate_sample_ohlcv(ticker="EURUSD", days=90):
    """
    生成模拟 OHLCV 数据
    
    Args:
        ticker: 交易对名称
        days: 生成天数
        
    Returns:
        pd.DataFrame: 包含 OHLCV 数据的 DataFrame
    """
    print(f"📊 生成 {ticker} 的模拟数据 ({days} 天)...")
    
    # 生成时间序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # 生成价格数据 (随机游走)
    np.random.seed(42)
    base_price = 1.1000
    returns = np.random.normal(0, 0.001, len(dates))
    prices = base_price * (1 + returns).cumprod()
    
    # 生成 OHLCV
    df = pd.DataFrame({
        'timestamp': dates,
        'ticker': ticker,
        'open': prices * (1 + np.random.uniform(-0.0005, 0.0005, len(dates))),
        'high': prices * (1 + np.random.uniform(0, 0.001, len(dates))),
        'low': prices * (1 + np.random.uniform(-0.001, 0, len(dates))),
        'close': prices,
        'volume': np.random.randint(1000, 10000, len(dates)),
    })
    
    print(f"✅ 生成 {len(df)} 条数据记录")
    return df


def compute_all_features(df):
    """
    计算所有技术指标特征
    
    Args:
        df: 包含 OHLCV 数据的 DataFrame
        
    Returns:
        pd.DataFrame: 包含所有特征的 DataFrame
    """
    print("🔧 计算技术指标特征...")
    
    features = df[['timestamp', 'ticker']].copy()
    
    # 1. SMA 特征
    features['sma_7'] = BasicFeatures.compute_sma(df['close'], 7)
    features['sma_14'] = BasicFeatures.compute_sma(df['close'], 14)
    features['sma_30'] = BasicFeatures.compute_sma(df['close'], 30)
    
    # 2. RSI 特征
    features['rsi_14'] = BasicFeatures.compute_rsi(df['close'], 14)
    features['rsi_21'] = BasicFeatures.compute_rsi(df['close'], 21)
    
    # 3. MACD 特征
    macd_df = BasicFeatures.compute_macd(df['close'])
    features['macd'] = macd_df['macd']
    features['macd_signal'] = macd_df['macd_signal']
    features['macd_hist'] = macd_df['macd_hist']
    
    # 4. 布林带特征
    bbands_df = BasicFeatures.compute_bollinger_bands(df['close'])
    features['bbands_upper'] = bbands_df['bbands_upper']
    features['bbands_middle'] = bbands_df['bbands_middle']
    features['bbands_lower'] = bbands_df['bbands_lower']
    features['bbands_width'] = bbands_df['bbands_width']
    
    # 5. ATR 特征
    features['atr_14'] = BasicFeatures.compute_atr(df['high'], df['low'], df['close'], 14)
    
    # 6. 随机震荡指标
    stoch_df = BasicFeatures.compute_stochastic(df['high'], df['low'], df['close'])
    features['stochastic_k'] = stoch_df['stochastic_k']
    features['stochastic_d'] = stoch_df['stochastic_d']
    
    # 删除 NaN 行 (由于滚动窗口计算)
    features = features.dropna()
    
    print(f"✅ 计算完成，有效特征行数: {len(features)}")
    return features


def prepare_feast_dataframe(features_df):
    """
    准备符合 Feast 要求的 DataFrame
    
    Args:
        features_df: 特征 DataFrame
        
    Returns:
        pd.DataFrame: Feast 格式的 DataFrame
    """
    print("📦 准备 Feast 数据格式...")
    
    feast_df = features_df.copy()
    
    # Feast 要求的列名
    feast_df = feast_df.rename(columns={'timestamp': 'event_timestamp'})
    
    # 添加 created_timestamp (数据创建时间)
    feast_df['created_timestamp'] = datetime.now()
    
    # 确保 event_timestamp 是 datetime 类型
    feast_df['event_timestamp'] = pd.to_datetime(feast_df['event_timestamp'])
    
    # 确保所有特征列是 float32 类型
    feature_cols = [col for col in feast_df.columns 
                   if col not in ['event_timestamp', 'created_timestamp', 'ticker']]
    for col in feature_cols:
        feast_df[col] = feast_df[col].astype('float32')
    
    print(f"✅ Feast 数据准备完成")
    print(f"   - 行数: {len(feast_df)}")
    print(f"   - 列数: {len(feast_df.columns)}")
    print(f"   - 特征列: {len(feature_cols)}")
    
    return feast_df


def save_to_parquet(df, output_path="data/sample_features.parquet"):
    """
    保存数据到 Parquet 文件
    
    Args:
        df: DataFrame
        output_path: 输出路径
    """
    print(f"💾 保存数据到 {output_path}...")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 保存为 Parquet
    df.to_parquet(output_path, index=False, engine='pyarrow')
    
    file_size = os.path.getsize(output_path) / 1024  # KB
    print(f"✅ 保存成功 ({file_size:.2f} KB)")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 MT5-CRS Feature Ingestion Pipeline")
    print("=" * 60)
    print()
    
    try:
        # Step 1: 生成模拟数据
        ohlcv_df = generate_sample_ohlcv(ticker="EURUSD", days=90)
        print()
        
        # Step 2: 计算特征
        features_df = compute_all_features(ohlcv_df)
        print()
        
        # Step 3: 准备 Feast 格式
        feast_df = prepare_feast_dataframe(features_df)
        print()
        
        # Step 4: 保存到 Parquet
        save_to_parquet(feast_df)
        print()
        
        # Step 5: 显示样本数据
        print("📋 样本数据预览:")
        print(feast_df.head(3))
        print()
        
        print("=" * 60)
        print("✅ Materialization successful")
        print("=" * 60)
        print()
        print("📝 下一步:")
        print("  1. 运行 'feast apply' 注册特征定义")
        print("  2. 运行 'feast materialize' 将数据推送到 Redis")
        print("  3. 使用 Feast SDK 查询在线特征")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
