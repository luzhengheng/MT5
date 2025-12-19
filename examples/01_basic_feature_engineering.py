#!/usr/bin/env python3
"""
示例 1: 基础特征工程

本示例演示如何使用 MT5-CRS 系统计算基础技术指标特征
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import pandas as pd
import numpy as np
from datetime import datetime

from feature_engineering.basic_features import BasicFeatures


def create_sample_data():
    """创建示例价格数据"""
    print("创建示例价格数据...")

    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    data = {
        'time': dates,
        'open': 100 + np.random.randn(len(dates)).cumsum(),
        'high': 102 + np.random.randn(len(dates)).cumsum(),
        'low': 98 + np.random.randn(len(dates)).cumsum(),
        'close': 100 + np.random.randn(len(dates)).cumsum(),
        'volume': np.random.randint(1000000, 10000000, len(dates)),
        'tick_volume': np.random.randint(10000, 100000, len(dates)),
    }

    df = pd.DataFrame(data)

    # 确保 high >= low
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

    print(f"数据点数: {len(df)}")
    print(f"日期范围: {df['time'].min()} 到 {df['time'].max()}")
    print()

    return df


def calculate_basic_features(df):
    """计算基础特征"""
    print("=" * 60)
    print("计算基础特征")
    print("=" * 60)

    bf = BasicFeatures()

    # 1. 收益率
    print("\n1. 计算收益率...")
    df = bf.calculate_returns(df)
    print(f"   - return: 简单收益率")
    print(f"   - log_return: 对数收益率")
    print(f"   平均日收益率: {df['return'].mean():.4f}")
    print(f"   收益率标准差: {df['return'].std():.4f}")

    # 2. 移动平均线
    print("\n2. 计算移动平均线...")
    df = bf.calculate_sma(df, windows=[5, 20, 60])
    df = bf.calculate_ema(df, spans=[5, 20, 60])
    print(f"   - sma_5, sma_20, sma_60: 简单移动平均")
    print(f"   - ema_5, ema_20, ema_60: 指数移动平均")

    # 3. RSI
    print("\n3. 计算 RSI 指标...")
    df = bf.calculate_rsi(df, period=14)
    print(f"   - rsi_14: 相对强弱指标")
    print(f"   平均 RSI: {df['rsi_14'].mean():.2f}")

    # 4. MACD
    print("\n4. 计算 MACD 指标...")
    df = bf.calculate_macd(df, fast=12, slow=26, signal=9)
    print(f"   - macd: MACD 线")
    print(f"   - macd_signal: 信号线")
    print(f"   - macd_hist: MACD 直方图")

    # 5. 布林带
    print("\n5. 计算布林带...")
    df = bf.calculate_bollinger_bands(df, window=20, num_std=2)
    print(f"   - bb_upper: 上轨")
    print(f"   - bb_middle: 中轨")
    print(f"   - bb_lower: 下轨")
    print(f"   - bb_width: 带宽")
    print(f"   - bb_pct: BB%")

    # 6. ATR
    print("\n6. 计算 ATR...")
    df = bf.calculate_atr(df, period=14)
    print(f"   - atr_14: 平均真实波幅")
    print(f"   平均 ATR: {df['atr_14'].mean():.2f}")

    # 7. 成交量特征
    print("\n7. 计算成交量特征...")
    df = bf.calculate_volume_features(df)
    print(f"   - volume_ma_20: 成交量 20 日均值")
    print(f"   - volume_ratio: 成交量比率")

    # 8. 价格特征
    print("\n8. 计算价格特征...")
    df = bf.calculate_price_features(df)
    print(f"   - high_low_ratio: 最高最低价比率")
    print(f"   - close_open_ratio: 收盘开盘价比率")

    # 9. 动量指标
    print("\n9. 计算动量指标...")
    df = bf.calculate_momentum(df, periods=[5, 20])
    print(f"   - momentum_5: 5 日动量")
    print(f"   - momentum_20: 20 日动量")

    print("\n" + "=" * 60)
    print(f"总特征数: {len(df.columns)}")
    print("=" * 60)

    return df


def analyze_features(df):
    """分析特征"""
    print("\n" + "=" * 60)
    print("特征分析")
    print("=" * 60)

    # 数据完整性
    print("\n1. 数据完整性:")
    completeness = (1 - df.isnull().sum() / len(df)) * 100
    print(f"   平均完整率: {completeness.mean():.2f}%")

    # 列出完整率最低的 5 个特征
    print("\n   完整率最低的 5 个特征:")
    for col in completeness.nsmallest(5).index:
        print(f"   - {col}: {completeness[col]:.2f}%")

    # 数值范围
    print("\n2. 数值范围:")
    print(f"   收盘价: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
    print(f"   RSI: {df['rsi_14'].min():.2f} ~ {df['rsi_14'].max():.2f}")
    print(f"   成交量: {df['volume'].min():,.0f} ~ {df['volume'].max():,.0f}")

    # 趋势分析
    print("\n3. 趋势分析:")
    price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
    print(f"   总收益率: {price_change:+.2f}%")

    # 信号分析
    print("\n4. 交易信号 (最后 10 天):")
    last_10 = df.tail(10)

    for idx, row in last_10.iterrows():
        signals = []

        # 金叉/死叉
        if pd.notna(row['ema_5']) and pd.notna(row['ema_20']):
            if row['ema_5'] > row['ema_20']:
                signals.append("金叉")
            else:
                signals.append("死叉")

        # RSI 超买超卖
        if pd.notna(row['rsi_14']):
            if row['rsi_14'] > 70:
                signals.append("RSI 超买")
            elif row['rsi_14'] < 30:
                signals.append("RSI 超卖")

        # MACD 信号
        if pd.notna(row['macd_hist']):
            if row['macd_hist'] > 0:
                signals.append("MACD 多头")
            else:
                signals.append("MACD 空头")

        date_str = row['time'].strftime('%Y-%m-%d')
        print(f"   {date_str}: {', '.join(signals) if signals else '无明显信号'}")


def save_features(df, output_path='output/basic_features.parquet'):
    """保存特征数据"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output_file)
    print(f"\n特征数据已保存到: {output_file}")
    print(f"文件大小: {output_file.stat().st_size / 1024:.2f} KB")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("MT5-CRS 基础特征工程示例")
    print("=" * 60)
    print()

    # 1. 创建示例数据
    df = create_sample_data()

    # 2. 计算特征
    df = calculate_basic_features(df)

    # 3. 分析特征
    analyze_features(df)

    # 4. 保存特征
    save_features(df)

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)
    print("\n提示:")
    print("  - 查看生成的特征数据: output/basic_features.parquet")
    print("  - 尝试调整参数重新运行")
    print("  - 继续查看高级特征示例: 02_advanced_feature_engineering.py")
    print()


if __name__ == '__main__':
    main()
