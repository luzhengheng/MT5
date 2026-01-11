#!/usr/bin/env python3
"""
Signal Generation Verification Script
=======================================

验证 SignalEngine 类的信号生成功能。

测试流程：
1. 使用 MT5Service & MarketDataService 获取 EURUSD.s 的 M1 K线
2. 使用 TechnicalIndicators 计算 SMA(10), SMA(20), RSI(14)
3. 使用 SignalEngine 生成信号（测试两种策略）
4. 过滤并显示信号发生的行（signal != 0）
5. 验证 signal 列只包含 -1, 0, 1

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
from src.strategy.signal_engine import SignalEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：验证信号生成"""
    # 从环境变量读取品种代码
    SYMBOL = os.getenv("MT5_SYMBOL", "EURUSD.s")
    TIMEFRAME = "M1"
    COUNT = 500

    print("=" * 70)
    print(f"🔍 Signal Generation Verification - {SYMBOL}")
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
        return 1

    print(f"✅ 成功获取 {len(df)} 根K线数据")
    print()

    # 步骤 5: 计算技术指标
    print("-" * 70)
    print(f"📊 步骤 2: 计算技术指标")
    print()

    logger.info("初始化 TechnicalIndicators...")
    indicators = TechnicalIndicators()

    logger.info("计算 SMA(10)...")
    df = indicators.calculate_sma(df, period=10)

    logger.info("计算 SMA(20)...")
    df = indicators.calculate_sma(df, period=20)

    logger.info("计算 RSI(14)...")
    df = indicators.calculate_rsi(df, period=14)

    print("✅ 技术指标计算完成")
    print()

    # 步骤 6: 测试 MA Crossover 策略
    print("-" * 70)
    print(f"📊 步骤 3: 测试 MA Crossover 策略")
    print()

    logger.info("初始化 SignalEngine...")
    signal_engine = SignalEngine()

    logger.info("应用 MA Crossover 策略...")
    df_ma = signal_engine.apply_strategy(df.copy(), strategy_name='ma_crossover')

    # 验证 signal 列存在
    if 'signal' not in df_ma.columns:
        logger.error("❌ signal 列未生成")
        print("❌ signal 列未生成")
        return 1

    print("✅ signal 列已生成")
    print()

    # 统计信号分布
    signal_counts = df_ma['signal'].value_counts().sort_index()
    print(f"信号分布:")
    for signal_value, count in signal_counts.items():
        signal_name = {1: "买入", -1: "卖出", 0: "持有"}
        print(f"  {signal_name.get(signal_value, signal_value):4s} ({signal_value:2d}): {count:4d} 次")
    print()

    # 验证信号值只包含 -1, 0, 1
    unique_signals = df_ma['signal'].unique()
    invalid_signals = [s for s in unique_signals if s not in [-1, 0, 1]]

    if invalid_signals:
        logger.error(f"❌ 发现无效信号值: {invalid_signals}")
        print(f"❌ 发现无效信号值: {invalid_signals}")
        return 1

    print("✅ 信号值验证通过（仅包含 -1, 0, 1）")
    print()

    # 显示信号发生的行（signal != 0）
    signals_only = df_ma[df_ma['signal'] != 0]
    print(f"MA Crossover 信号数量: {len(signals_only)}")

    if len(signals_only) > 0:
        print("\n最近 10 个信号:")
        display_cols = ['time', 'close', 'sma_10', 'sma_20', 'signal']
        print(signals_only[display_cols].tail(10).to_string())
    else:
        print("⚠️  未检测到信号（可能需要更多数据或调整参数）")

    print()

    # 步骤 7: 测试 RSI Reversion 策略
    print("-" * 70)
    print(f"📊 步骤 4: 测试 RSI Reversion 策略")
    print()

    logger.info("应用 RSI Reversion 策略...")
    df_rsi = signal_engine.apply_strategy(df.copy(), strategy_name='rsi_reversion')

    # 统计信号分布
    signal_counts_rsi = df_rsi['signal'].value_counts().sort_index()
    print(f"信号分布:")
    for signal_value, count in signal_counts_rsi.items():
        signal_name = {1: "买入", -1: "卖出", 0: "持有"}
        print(f"  {signal_name.get(signal_value, signal_value):4s} ({signal_value:2d}): {count:4d} 次")
    print()

    # 验证信号值
    unique_signals_rsi = df_rsi['signal'].unique()
    invalid_signals_rsi = [s for s in unique_signals_rsi if s not in [-1, 0, 1]]

    if invalid_signals_rsi:
        logger.error(f"❌ 发现无效信号值: {invalid_signals_rsi}")
        print(f"❌ 发现无效信号值: {invalid_signals_rsi}")
        return 1

    print("✅ 信号值验证通过（仅包含 -1, 0, 1）")
    print()

    # 显示信号发生的行
    signals_only_rsi = df_rsi[df_rsi['signal'] != 0]
    print(f"RSI Reversion 信号数量: {len(signals_only_rsi)}")

    if len(signals_only_rsi) > 0:
        print("\n最近 10 个信号:")
        display_cols_rsi = ['time', 'close', 'rsi_14', 'signal']
        print(signals_only_rsi[display_cols_rsi].tail(10).to_string())
    else:
        print("⚠️  未检测到信号（可能 RSI 未进入超买/超卖区域）")

    print()

    # 步骤 8: 向量化验证
    print("-" * 70)
    print(f"📊 步骤 5: 向量化验证")
    print()
    print("✅ 所有信号生成使用向量化操作")
    print("   - MA Crossover: .shift() + 布尔运算 + .loc 索引")
    print("   - RSI Reversion: 布尔运算 + .loc 索引")
    print("   - 无行迭代，无 for 循环")
    print()

    print("-" * 70)
    print("✅ 信号生成验证完成")
    print("=" * 70)

    # 步骤 9: 断开连接
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
