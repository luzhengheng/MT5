#!/usr/bin/env python3
"""
Trading Bot Cycle Verification Script
=======================================

验证 TradingBot 类的完整周期执行功能。

测试流程（单周期干运行）：
1. 初始化 TradingBot
2. 执行一个单独的交易周期（不进入无限循环）
3. 验证各步骤执行结果
4. 打印周期摘要

环境变量：
- MT5_SYMBOL: 交易品种代码（默认 "EURUSD.s"）

注意：
- 此脚本在 Linux 上将失败（预期行为）
- 此脚本在 Windows 上且 MT5 Terminal 已连接时将成功运行
- 使用 DEMO 账户进行测试
- 测试手数为 0.01（最小手数）
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.mt5_service import MT5Service
from src.bot.trading_bot import TradingBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：验证交易机器人周期执行"""
    # 从环境变量读取品种代码
    SYMBOL = os.getenv("MT5_SYMBOL", "EURUSD.s")
    TIMEFRAME = "M1"
    STRATEGY = "ma_crossover"
    CANDLE_COUNT = 500
    VOLUME = 0.01

    print("=" * 70)
    print(f"🔍 Trading Bot Cycle Verification - {SYMBOL}")
    print("=" * 70)
    print()
    print("⚠️  重要提示:")
    print("   - 这是单周期干运行测试（不进入无限循环）")
    print("   - 请确保使用 DEMO 账户")
    print(f"   - 测试手数: {VOLUME} 手（最小手数）")
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

    # 步骤 3: 初始化 TradingBot
    print("-" * 70)
    print(f"📊 步骤 1: 初始化 TradingBot")
    print()

    logger.info("初始化 TradingBot...")
    bot = TradingBot()

    print("✅ TradingBot 初始化完成")
    print()

    # 步骤 4: 执行单个交易周期
    print("-" * 70)
    print(f"📊 步骤 2: 执行单个交易周期")
    print()
    print(f"参数:")
    print(f"  品种: {SYMBOL}")
    print(f"  时间周期: {TIMEFRAME}")
    print(f"  策略: {STRATEGY}")
    print(f"  K线数量: {CANDLE_COUNT}")
    print(f"  手数: {VOLUME}")
    print()

    logger.info("执行交易周期...")
    result = bot.run_cycle(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        strategy_name=STRATEGY,
        candle_count=CANDLE_COUNT,
        volume=VOLUME
    )

    print()

    # 步骤 5: 验证执行结果
    print("-" * 70)
    print(f"📊 步骤 3: 验证执行结果")
    print()

    # 验证数据获取
    if not result['data_fetched']:
        logger.error("❌ 数据获取失败")
        print(f"❌ 数据获取失败")
        print(f"   当前步骤: {result['step']}")
        print(f"   错误信息: {result['message']}")
        return 1

    print(f"✅ 数据获取成功")

    # 验证指标计算
    if not result['indicators_calculated']:
        logger.error("❌ 指标计算失败")
        print(f"❌ 指标计算失败")
        print(f"   当前步骤: {result['step']}")
        print(f"   错误信息: {result['message']}")
        return 1

    print(f"✅ 指标计算完成")

    # 验证信号生成
    if not result['signal_generated']:
        logger.error("❌ 信号生成失败")
        print(f"❌ 信号生成失败")
        print(f"   当前步骤: {result['step']}")
        print(f"   错误信息: {result['message']}")
        return 1

    print(f"✅ 信号生成完成")
    print()

    # 步骤 6: 显示周期摘要
    print("-" * 70)
    print(f"📊 步骤 4: 周期执行摘要")
    print()

    signal_name = {1: "买入 (BUY)", -1: "卖出 (SELL)", 0: "持有 (HOLD)"}
    print(f"执行状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"最终步骤: {result['step']}")
    print(f"数据获取: {'✅' if result['data_fetched'] else '❌'}")
    print(f"指标计算: {'✅' if result['indicators_calculated'] else '❌'}")
    print(f"信号生成: {'✅' if result['signal_generated'] else '❌'}")
    print(f"当前信号: {signal_name.get(result['signal_value'], result['signal_value'])}")
    print(f"交易执行: {'✅' if result['trade_executed'] else '⏸️  未执行'}")

    if result['trade_result']:
        print(f"\n交易详情:")
        print(f"  订单号: {result['trade_result']['ticket']}")
        print(f"  手数: {result['trade_result']['volume']}")
        print(f"  价格: {result['trade_result']['price']}")
        print(f"  备注: {result['trade_result']['comment']}")

    print(f"\n执行信息: {result['message']}")
    print()

    # 步骤 7: 验证周期完整性
    print("-" * 70)
    print(f"📊 步骤 5: 验证周期完整性")
    print()

    if not result['success']:
        logger.error("❌ 周期执行不完整")
        print("❌ 周期执行不完整")
        return 1

    print("✅ 周期执行完整")
    print()

    # 步骤 8: 最终验证
    print("-" * 70)
    print("✅ Trading Bot 周期验证完成")
    print("=" * 70)
    print()

    print("验证结果:")
    print("  ✅ TradingBot 初始化成功")
    print("  ✅ run_cycle() 方法执行成功")
    print("  ✅ 数据获取 → 指标计算 → 信号生成 → 交易决策 完整流程")
    print("  ✅ 所有步骤按预期执行")
    print()

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
