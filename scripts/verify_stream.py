#!/usr/bin/env python3
"""
MT5 Stream Verification Script
================================

验证 MarketDataService 的实时 tick 数据获取功能。

测试目标：
- 品种：EURUSD
- 循环次数：5 次
- 间隔时间：1 秒

注意：
- 此脚本在 Linux 上将失败（预期行为，因为 MetaTrader5 库不可用）
- 此脚本在 Windows 上且 MT5 Terminal 已连接时将成功运行
"""

import sys
import time
import logging
from pathlib import Path

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
    """主函数：验证 MT5 实时数据流"""
    print("=" * 70)
    print("🔍 MT5 Stream Verification - EURUSD Tick Data")
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
        print("   - 如果在 Windows 上运行：请检查 MT5_PATH 环境变量")
        return 1

    logger.info("✅ MT5 连接成功")

    # 步骤 3: 初始化 MarketDataService
    logger.info("初始化 Market Data Service...")
    market_data = MarketDataService()

    # 步骤 4: 目标品种
    symbol = "EURUSD"
    loop_count = 5

    print(f"\n📊 开始监控 {symbol} 的实时 tick 数据")
    print(f"循环次数: {loop_count} 次")
    print(f"间隔时间: 1 秒")
    print("-" * 70)
    print()

    # 步骤 5: 循环获取 tick 数据
    for i in range(1, loop_count + 1):
        logger.info(f"[{i}/{loop_count}] 获取 {symbol} tick 数据...")

        # 获取 tick 数据
        tick_data = market_data.get_tick(symbol)

        if tick_data:
            print(f"📈 Tick #{i}: {tick_data}")
            print(f"   时间: {tick_data['time']}")
            print(f"   买价: {tick_data['bid']:.5f}")
            print(f"   卖价: {tick_data['ask']:.5f}")
            print(f"   成交量: {tick_data['volume']}")
            print()
        else:
            logger.error(f"❌ 无法获取 {symbol} 的 tick 数据")
            print(f"❌ Tick #{i}: 数据获取失败")
            print()

        # 如果不是最后一次循环，等待 1 秒
        if i < loop_count:
            time.sleep(1)

    print("-" * 70)
    print("✅ 验证完成")
    print("=" * 70)

    # 步骤 6: 断开连接
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
