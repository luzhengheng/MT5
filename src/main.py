#!/usr/bin/env python3
"""
MT5-CRS Trading Bot - Main Entry Point
========================================

实时交易机器人的主入口，运行连续交易循环。

功能：
- 初始化交易机器人
- 运行连续交易循环（while True）
- 处理 KeyboardInterrupt（优雅退出）
- 错误重试机制（避免临时网络错误导致崩溃）
- 可配置的循环间隔

环境变量：
- MT5_SYMBOL: 交易品种（默认 "EURUSD.s"）
- MT5_TIMEFRAME: 时间周期（默认 "M1"）
- TRADING_STRATEGY: 策略名称（默认 "ma_crossover"）
- TRADING_VOLUME: 交易手数（默认 "0.01"）
- TRADING_INTERVAL: 循环间隔秒数（默认 "10"）
- CANDLE_COUNT: K线数量（默认 "500"）

使用方法：
    python3 src/main.py

    或使用自定义参数：
    MT5_SYMBOL=EURUSD.s TRADING_STRATEGY=rsi_reversion python3 src/main.py

注意：
- 请确保 .env 文件已正确配置 MT5 连接信息
- 建议先在 DEMO 账户测试
- 使用 Ctrl+C 优雅停止机器人
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bot.trading_bot import TradingBot
from src.gateway.mt5_service import MT5Service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'trading_bot.log')
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    """
    从环境变量加载配置

    返回：
        dict: 配置字典
    """
    config = {
        'symbol': os.getenv('MT5_SYMBOL', 'EURUSD.s'),
        'timeframe': os.getenv('MT5_TIMEFRAME', 'M1'),
        'strategy': os.getenv('TRADING_STRATEGY', 'ma_crossover'),
        'volume': float(os.getenv('TRADING_VOLUME', '0.01')),
        'interval': int(os.getenv('TRADING_INTERVAL', '10')),
        'candle_count': int(os.getenv('CANDLE_COUNT', '500'))
    }

    logger.info("配置加载完成:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    return config


def main():
    """
    主函数 - 启动连续交易循环

    工作流：
        1. 加载配置
        2. 初始化 MT5Service 和 TradingBot
        3. 进入无限循环
        4. 执行交易周期
        5. 等待指定间隔
        6. 处理异常和中断
    """
    print("=" * 70)
    print("🤖 MT5-CRS Trading Bot - Live Trading Runner")
    print("=" * 70)
    print()

    # 步骤 1: 加载配置
    logger.info("加载配置...")
    config = load_config()
    print()

    # 步骤 2: 初始化 MT5Service
    logger.info("初始化 MT5 Service...")
    mt5_service = MT5Service()

    # 步骤 3: 连接到 MT5
    logger.info("连接到 MT5 Terminal...")
    if not mt5_service.connect():
        logger.error("❌ MT5 连接失败，无法启动交易机器人")
        print("\n❌ MT5 连接失败")
        print("\n可能原因:")
        print("  1. MT5 Terminal 未运行（Windows 端）")
        print("  2. .env 文件配置不正确")
        print("  3. MT5_PATH、MT5_LOGIN、MT5_PASSWORD、MT5_SERVER 未设置")
        print("  4. 网络连接问题")
        return 1

    logger.info("✅ MT5 连接成功")
    print()

    # 步骤 4: 初始化 TradingBot
    logger.info("初始化 TradingBot...")
    bot = TradingBot()
    print()

    # 步骤 5: 显示启动信息
    print("=" * 70)
    print("✅ 交易机器人已启动")
    print("=" * 70)
    print()
    print("运行参数:")
    print(f"  品种: {config['symbol']}")
    print(f"  时间周期: {config['timeframe']}")
    print(f"  策略: {config['strategy']}")
    print(f"  手数: {config['volume']}")
    print(f"  循环间隔: {config['interval']} 秒")
    print(f"  K线数量: {config['candle_count']}")
    print()
    print("⚠️  重要提示:")
    print("  - 使用 Ctrl+C 停止机器人")
    print("  - 日志保存到: trading_bot.log")
    print("  - 建议在 DEMO 账户测试")
    print()
    print("=" * 70)
    print()

    # 步骤 6: 进入交易循环
    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            logger.info(f"========== 周期 #{cycle_count} 开始 ==========")
            print(f"\n🔄 周期 #{cycle_count} 开始...")

            try:
                # 执行交易周期
                result = bot.run_cycle(
                    symbol=config['symbol'],
                    timeframe=config['timeframe'],
                    strategy_name=config['strategy'],
                    candle_count=config['candle_count'],
                    volume=config['volume']
                )

                # 显示周期结果
                if result['success']:
                    signal_emoji = {1: "📈", -1: "📉", 0: "⏸️"}
                    signal_name = {1: "买入", -1: "卖出", 0: "持有"}

                    emoji = signal_emoji.get(result['signal_value'], "❓")
                    name = signal_name.get(result['signal_value'], "未知")

                    print(f"  {emoji} 信号: {name}")

                    if result['trade_executed']:
                        print(f"  ✅ 交易执行: {result['message']}")
                    else:
                        print(f"  ⏸️  无交易: {result['message']}")
                else:
                    print(f"  ⚠️  周期执行失败: {result['message']}")
                    logger.warning(f"周期 #{cycle_count} 失败: {result['message']}")

            except Exception as e:
                # 捕获周期内异常，不中断循环
                logger.error(f"周期 #{cycle_count} 异常: {str(e)}")
                print(f"  ❌ 周期异常: {str(e)}")
                print(f"  ⏳ 等待 {config['interval']} 秒后重试...")

            # 等待下一个周期
            logger.info(f"周期 #{cycle_count} 完成，等待 {config['interval']} 秒...")
            print(f"\n⏳ 等待 {config['interval']} 秒...")
            time.sleep(config['interval'])

    except KeyboardInterrupt:
        # 用户中断（Ctrl+C）
        print("\n\n")
        logger.info("收到停止信号 (Ctrl+C)")
        print("=" * 70)
        print("🛑 正在停止交易机器人...")
        print("=" * 70)
        print()

        logger.info("断开 MT5 连接...")
        mt5_service.disconnect()

        print(f"✅ 交易机器人已停止")
        print(f"   总周期数: {cycle_count}")
        print(f"   日志文件: trading_bot.log")
        print()

        return 0

    except Exception as e:
        # 未预期的异常
        logger.error(f"交易机器人致命错误: {str(e)}")
        print("\n\n")
        print("=" * 70)
        print("❌ 交易机器人遇到致命错误")
        print("=" * 70)
        print()
        print(f"错误: {str(e)}")
        print()

        import traceback
        traceback.print_exc()

        logger.info("断开 MT5 连接...")
        mt5_service.disconnect()

        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
        sys.exit(1)
