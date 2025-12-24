#!/usr/bin/env python3
"""
MT5 Trade Verification Script
===============================

验证 TradeService 的交易执行功能。

测试流程：
1. 连接到 MT5 Terminal
2. 开立一个小额买单（0.01 手）
3. 验证订单成功开立
4. 查询当前持仓
5. 平仓刚才的订单
6. 验证平仓成功

环境变量：
- MT5_SYMBOL: 交易品种代码（默认 "EURUSD"）

注意：
- 此脚本在 Linux 上将失败（预期行为）
- 此脚本在 Windows 上且 MT5 Terminal 已连接时将成功运行
- 请确保使用 DEMO 账户进行测试
- 测试手数为 0.01（最小手数），以降低风险
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.trade_service import TradeService
from src.gateway.mt5_service import MT5Service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：验证 MT5 交易功能"""
    # 从环境变量读取品种代码，默认为 "EURUSD"
    SYMBOL = os.getenv("MT5_SYMBOL", "EURUSD")
    TEST_VOLUME = 0.01  # 测试手数（最小手数）

    print("=" * 70)
    print(f"🔍 MT5 Trade Verification - {SYMBOL}")
    print("=" * 70)
    print()
    print("⚠️  重要提示:")
    print("   - 请确保使用 DEMO 账户进行测试")
    print(f"   - 测试手数: {TEST_VOLUME} 手（最小手数）")
    print("   - 测试流程: 开仓 → 验证 → 平仓")
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

    # 步骤 3: 初始化 TradeService
    logger.info("初始化 Trade Service...")
    trade_service = TradeService()

    print("-" * 70)
    print()

    # 步骤 4: 开立买单
    print(f"📊 步骤 1: 开立买单")
    print(f"   品种: {SYMBOL}")
    print(f"   手数: {TEST_VOLUME}")
    print(f"   类型: 市价买单")
    print()

    order_result = trade_service.buy(
        symbol=SYMBOL,
        volume=TEST_VOLUME,
        comment="MT5-CRS Test Buy Order"
    )

    if order_result is None:
        logger.error("❌ 开仓失败")
        print("❌ 买单开立失败")
        print()
        print("可能原因:")
        print("  1. 品种代码不正确（检查 MT5_SYMBOL 环境变量）")
        print("  2. 最小手数限制（某些品种最小手数 > 0.01）")
        print("  3. 账户余额不足（即使是 DEMO 账户）")
        print("  4. 市场已关闭（周末或节假日）")
        return 1

    ticket = order_result['ticket']
    open_price = order_result['price']

    print(f"✅ 买单开立成功!")
    print(f"   订单号: {ticket}")
    print(f"   成交价: {open_price:.5f}")
    print(f"   手数: {TEST_VOLUME}")
    print()

    # 等待 2 秒
    print("等待 2 秒...")
    time.sleep(2)
    print()

    # 步骤 5: 查询当前持仓
    print(f"📊 步骤 2: 查询当前持仓")
    print()

    positions = trade_service.get_positions(symbol=SYMBOL)

    if len(positions) == 0:
        logger.warning("⚠️  未查询到持仓（可能已被自动平仓）")
        print("⚠️  未查询到持仓")
        print()
    else:
        print(f"✅ 查询到 {len(positions)} 个持仓:")
        for idx, pos in enumerate(positions, 1):
            print(f"   持仓 #{idx}:")
            print(f"      订单号: {pos['ticket']}")
            print(f"      品种: {pos['symbol']}")
            print(f"      类型: {pos['type']}")
            print(f"      手数: {pos['volume']}")
            print(f"      开仓价: {pos['price_open']:.5f}")
            print(f"      当前价: {pos['price_current']:.5f}")
            print(f"      盈亏: ${pos['profit']:.2f}")
            print()

    # 等待 2 秒
    print("等待 2 秒...")
    time.sleep(2)
    print()

    # 步骤 6: 平仓
    print(f"📊 步骤 3: 平仓订单 {ticket}")
    print()

    close_success = trade_service.close_position(
        ticket=ticket,
        comment="MT5-CRS Test Close"
    )

    if not close_success:
        logger.error("❌ 平仓失败")
        print("❌ 平仓失败")
        print()
        print("可能原因:")
        print("  1. 订单已被自动平仓")
        print("  2. 网络延迟导致超时")
        print("  3. 市场已关闭")
        print()
        print("请手动检查 MT5 终端确认持仓状态")
        return 1

    print(f"✅ 平仓成功!")
    print(f"   订单号: {ticket}")
    print()

    # 等待 2 秒
    print("等待 2 秒...")
    time.sleep(2)
    print()

    # 步骤 7: 再次查询持仓（应该为空）
    print(f"📊 步骤 4: 验证平仓结果")
    print()

    positions_after = trade_service.get_positions(symbol=SYMBOL)

    if len(positions_after) < len(positions):
        print(f"✅ 验证成功: 持仓数量减少")
        print(f"   平仓前: {len(positions)} 个")
        print(f"   平仓后: {len(positions_after)} 个")
    else:
        print(f"⚠️  持仓数量未变化")
        print(f"   当前持仓: {len(positions_after)} 个")

    print()
    print("-" * 70)
    print("✅ 交易功能验证完成")
    print("=" * 70)

    # 步骤 8: 断开连接
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
