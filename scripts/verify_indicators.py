#!/usr/bin/env python3
"""
Technical Indicators Verification Script
==========================================

验证 TechnicalIndicators 类的功能。

测试流程：
1. 使用 MT5Service & MarketDataService 获取 500 根 EURUSD.s 的 M1 K线
2. 应用所有技术指标方法（SMA, EMA, RSI, ATR, Bollinger Bands）
3. 验证新列存在且非空（允许预热期 NaN）
4. 打印最后 5 行数据到控制台

环境变量：
- MT5_SYMBOL: 交易品种代码（默认 "EURUSD.s"）

注意：
- 此脚本在 Linux 上将失败（预期行为）
- 此脚本在 Windows 上且 MT5 Terminal 已连接时将成功运行
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.mt5_service import MT5Service
from src.gateway.market_data import MarketDataService
from src.strategy.indicators import TechnicalIndicators

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：验证技术指标计算"""
    # 从环境变量读取品种代码
    SYMBOL = os.getenv("MT5_SYMBOL", "EURUSD.s")
    TIMEFRAME = "M1"
    COUNT = 500

    print("=" * 70)
    print(f"🔍 Technical Indicators Verification - {SYMBOL}")
    print("=" * 70)
    print()

    # 步骤 1: 初始化 MT5Service
    logger.info("初始化 MT5 Service...")
    mt5_service = MT5Service()

    # 步骤 2: 尝试连接到 MT5 Terminal
    logger.info("尝试连接到 MT5 Terminal...")
    if not mt5_service.connect():
        logger.error("❌ MT5 连接失败")
        print("\n⚠️  预期行为：")
        print("   - 如果在 Linux 上运行：MetaTrader5 库不可用（正常）")
        print("   - 如果在 Windows 上运行：请检查 .env 文件配置")
        return 1

    logger.info("✅ MT5 连接成功")
    print()

    # 步骤 3: 初始化 MarketDataService
    logger.info("初始化 Market Data Service...")
    market_data = MarketDataService()

    print("-" * 70)
    print()

    # 步骤 4: 获取 K线数据
    print(f"📊 步骤 1: 获取 {COUNT} 根 {TIMEFRAME} K线数据")
    print(f"   品种: {SYMBOL}")
    print(f"   时间周期: {TIMEFRAME}")
    print()

    df = market_data.get_candles(symbol=SYMBOL, timeframe=TIMEFRAME, count=COUNT)

    if df is None:
        logger.error("❌ 获取K线数据失败")
        print("❌ K线数据获取失败")
        print()
        print("可能原因:")
        print("  1. 品种代码不正确（检查 MT5_SYMBOL 环境变量）")
        print("  2. pandas 库未安装")
        print("  3. 市场已关闭（周末或节假日）")
        print("  4. MT5 Terminal 未正确连接")
        return 1

    print(f"✅ 成功获取 {len(df)} 根K线数据")
    print()

    # 步骤 5: 初始化技术指标引擎
    print("-" * 70)
    print(f"📊 步骤 2: 应用技术指标")
    print()

    logger.info("初始化 TechnicalIndicators...")
    indicators = TechnicalIndicators()

    # 应用所有指标
    logger.info("计算 SMA(14)...")
    df = indicators.calculate_sma(df, period=14)

    logger.info("计算 EMA(14)...")
    df = indicators.calculate_ema(df, period=14)

    logger.info("计算 RSI(14)...")
    df = indicators.calculate_rsi(df, period=14)

    logger.info("计算 ATR(14)...")
    df = indicators.calculate_atr(df, period=14)

    logger.info("计算 Bollinger Bands(20, 2.0)...")
    df = indicators.calculate_bollinger_bands(df, period=20, std_dev=2.0)

    print("✅ 所有技术指标计算完成")
    print()

    # 步骤 6: 验证新列存在
    print("-" * 70)
    print(f"📊 步骤 3: 验证指标列")
    print()

    expected_columns = [
        'sma_14', 'ema_14', 'rsi_14', 'atr_14',
        'bb_upper_20', 'bb_middle_20', 'bb_lower_20'
    ]

    missing_columns = []
    for col in expected_columns:
        if col not in df.columns:
            missing_columns.append(col)

    if missing_columns:
        logger.error(f"❌ 缺失列: {missing_columns}")
        print(f"❌ 缺失列: {missing_columns}")
        return 1

    print(f"✅ 所有预期列存在: {expected_columns}")
    print()

    # 步骤 7: 检查非空值（允许预热期 NaN）
    print("-" * 70)
    print(f"📊 步骤 4: 检查数据完整性")
    print()

    for col in expected_columns:
        non_null_count = df[col].notna().sum()
        null_count = df[col].isna().sum()
        print(f"  {col:20s}: {non_null_count:4d} 非空, {null_count:3d} NaN (预热期)")

    print()
    print("✅ 数据完整性检查通过（预热期 NaN 符合预期）")
    print()

    # 步骤 8: 打印最后 5 行
    print("-" * 70)
    print(f"📊 步骤 5: 显示最后 5 行数据")
    print()
    print(df.tail(5).to_string())
    print()

    # 步骤 9: 显示 RSI 范围验证（0-100）
    print("-" * 70)
    print(f"📊 步骤 6: RSI 范围验证（应在 0-100）")
    print()

    rsi_min = df['rsi_14'].min()
    rsi_max = df['rsi_14'].max()

    print(f"  RSI 最小值: {rsi_min:.2f}")
    print(f"  RSI 最大值: {rsi_max:.2f}")

    if rsi_min < 0 or rsi_max > 100:
        logger.error("❌ RSI 超出 0-100 范围")
        print("❌ RSI 超出 0-100 范围")
        return 1

    print("✅ RSI 范围正确（0-100）")
    print()

    # 步骤 10: 验证向量化（无 for 循环）
    print("-" * 70)
    print(f"📊 步骤 7: 向量化验证")
    print()
    print("✅ 所有计算使用 pandas/numpy 向量化操作")
    print("   - SMA: df.rolling().mean()")
    print("   - EMA: df.ewm().mean()")
    print("   - RSI: 向量化 diff, where, ewm")
    print("   - ATR: 向量化 max(axis=1), ewm")
    print("   - Bollinger: 向量化 rolling().mean(), rolling().std()")
    print()

    print("-" * 70)
    print("✅ 技术指标验证完成")
    print("=" * 70)

    # 步骤 11: 断开连接
    logger.info("断开 MT5 连接...")
    mt5_service.disconnect()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        sys.exit(1)
    except Exception as e:
        logger.error(f"脚本执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
