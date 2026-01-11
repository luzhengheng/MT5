#!/usr/bin/env python3
"""
MT5 Candles Verification Script
=================================

验证 MarketDataService 的 OHLCV K线数据获取功能。

测试流程：
1. 连接到 MT5 Terminal（使用 robust .env loader）
2. 获取 100 根 M1 K线数据
3. 显示前 3 和后 3 根K线
4. 验证 time 列为 datetime 类型
5. 验证数据完整性（无缺失）

环境变量：
- MT5_SYMBOL: 交易品种代码（默认 "EURUSD"）

注意：
- 此脚本在 Linux 上将失败（预期行为）
- 此脚本在 Windows 上且 MT5 Terminal 已连接时将成功运行
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.market_data import MarketDataService
from src.gateway.mt5_service import MT5Service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：验证 MT5 K线数据获取"""
    # 从环境变量读取品种代码，默认为 "EURUSD"
    SYMBOL = os.getenv("MT5_SYMBOL", "EURUSD")
    TIMEFRAME = "M1"
    COUNT = 100

    print("=" * 70)
    print(f"🔍 MT5 Candles Verification - {SYMBOL} {TIMEFRAME} Data")
    print("=" * 70)
    print()

    # 步骤 1: 初始化 MT5Service（使用 robust .env loader）
    logger.info("初始化 MT5 Service (使用 robust .env loader)...")
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

    # 步骤 5: 显示前 3 和后 3 根K线
    print("-" * 70)
    print(f"📊 步骤 2: 显示数据样本")
    print()
    print("前 3 根K线:")
    print(df.head(3).to_string())
    print()
    print("后 3 根K线:")
    print(df.tail(3).to_string())
    print()

    # 步骤 6: 验证 time 列为 datetime 类型
    print("-" * 70)
    print(f"📊 步骤 3: 验证数据类型")
    print()

    time_dtype = df['time'].dtype
    print(f"time 列数据类型: {time_dtype}")

    if 'datetime' in str(time_dtype):
        print(f"✅ time 列是 datetime 类型")
        # 显示样本时间
        sample_time = df['time'].iloc[0]
        print(f"   样本时间: {sample_time}")
        print(f"   时间类型: {type(sample_time)}")
    else:
        logger.error(f"❌ time 列不是 datetime 类型: {time_dtype}")
        print(f"❌ time 列类型错误: {time_dtype}")
        return 1

    print()

    # 步骤 7: 验证数据完整性
    print("-" * 70)
    print(f"📊 步骤 4: 验证数据完整性")
    print()

    # 检查是否有空值
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()

    print(f"空值统计:")
    print(null_counts.to_string())
    print()

    if total_nulls == 0:
        print(f"✅ 数据完整：无缺失值")
    else:
        logger.error(f"❌ 数据不完整：发现 {total_nulls} 个缺失值")
        print(f"❌ 数据不完整：发现 {total_nulls} 个缺失值")
        return 1

    print()

    # 步骤 8: 验证 DataFrame 不为空
    print("-" * 70)
    print(f"📊 步骤 5: 验证数据量")
    print()

    print(f"DataFrame 大小: {df.shape}")
    print(f"行数: {len(df)}")
    print(f"列数: {len(df.columns)}")
    print()

    if len(df) == 0:
        logger.error("❌ DataFrame 为空")
        print("❌ DataFrame 为空")
        return 1
    else:
        print(f"✅ DataFrame 包含 {len(df)} 行数据")

    print()

    # 步骤 9: 显示数据统计
    print("-" * 70)
    print(f"📊 数据统计信息")
    print()
    print(df.describe().to_string())
    print()

    print("-" * 70)
    print("✅ K线数据验证完成")
    print("=" * 70)

    # 步骤 10: 断开连接
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
