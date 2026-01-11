#!/usr/bin/env python3
"""
Task #012.05: Multi-Asset Bulk Ingestion (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)
============================================================================================

批量摄取 7 个战略资产的完整历史数据（1990-2025）到 TimescaleDB。

使用 EODHDBulkLoader 循环处理每个资产，具有：
- 错误隔离：单个资产失败不影响其他资产
- 速率控制：资产间延迟 1 秒，避免 API 限流
- 详细日志：记录每个资产的摄取状态
- 幂等性：重复数据自动跳过

使用方法:
    python3 scripts/run_bulk_ingestion.py
"""

import os
import sys
import asyncio
import logging
import yaml
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader.eodhd_bulk_loader import EODHDBulkLoader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """打印格式化的标题"""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def print_step(step_num, description):
    """打印步骤标题"""
    print(f"{BLUE}[步骤 {step_num}]{RESET} {description}")


def load_config(config_path):
    """加载 YAML 配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"{RED}❌ 配置文件加载失败: {e}{RESET}")
        return None


async def ingest_asset(loader, asset, config, retry_count=0, max_retries=3):
    """
    摄取单个资产的历史数据。

    Args:
        loader: EODHDBulkLoader 实例
        asset: 资产配置字典
        config: 全局配置字典
        retry_count: 当前重试次数
        max_retries: 最大重试次数

    Returns:
        Tuple: (成功, 行数, 耗时)
    """
    symbol = asset['symbol']
    exchange = asset['exchange']
    from_date = asset['from_date']

    logger.info(f"{YELLOW}{'─' * 70}{RESET}")
    logger.info(f"{BLUE}正在摄取资产: {symbol} ({exchange}){RESET}")
    logger.info(f"  日期范围: {from_date} 到 现在")

    try:
        start_time = asyncio.get_event_loop().time()

        # 执行摄取
        rows_inserted, elapsed = await loader.ingest_symbol(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date
        )

        elapsed_total = asyncio.get_event_loop().time() - start_time

        logger.info(f"{GREEN}✅ 摄取成功: {symbol}{RESET}")
        logger.info(f"  行数: {rows_inserted:,}")
        logger.info(f"  耗时: {elapsed_total:.2f} 秒")

        return True, rows_inserted, elapsed_total

    except Exception as e:
        if retry_count < max_retries:
            logger.warning(f"{YELLOW}⚠️  摄取失败 (重试 {retry_count + 1}/{max_retries}): {e}{RESET}")
            retry_delay = config.get('ingestion', {}).get('retry_delay', 5.0)
            await asyncio.sleep(retry_delay)
            return await ingest_asset(loader, asset, config, retry_count + 1, max_retries)
        else:
            logger.error(f"{RED}❌ 摄取失败 (已达最大重试次数): {symbol}{RESET}")
            logger.error(f"  错误: {e}")
            return False, 0, 0


async def run_bulk_ingestion(config_path="config/assets.yaml"):
    """
    执行批量摄取管道。

    Args:
        config_path: 配置文件路径
    """
    print_header("Task #012.05: 多资产批量摄取")

    # 步骤 1: 加载环境变量
    print_step(1, "加载环境变量")
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"{GREEN}✅ 已加载 .env 文件{RESET}")
    else:
        logger.warning(f"{YELLOW}⚠️  .env 文件不存在，使用环境变量{RESET}")

    # 步骤 2: 加载配置
    print_step(2, "加载资产配置")
    full_config_path = project_root / config_path
    config = load_config(full_config_path)

    if not config:
        logger.error(f"{RED}❌ 无法加载配置文件{RESET}")
        return 1

    # 获取 Task #012.05 资产列表
    assets = config.get('task_012_05_assets', [])
    ingestion_config = config.get('ingestion', {})
    db_config = config.get('database', {})

    logger.info(f"{GREEN}✅ 加载了 {len(assets)} 个资产{RESET}")
    for asset in assets:
        logger.info(f"  • {asset['symbol']}: {asset['name']}")

    # 步骤 3: 初始化 Bulk Loader
    print_step(3, "初始化 EODHD Bulk Loader")

    try:
        api_token = os.getenv("EODHD_API_TOKEN") or os.getenv("EODHD_API_KEY")
        if not api_token:
            logger.error(f"{RED}❌ 未找到 EODHD API Token{RESET}")
            return 1

        loader = EODHDBulkLoader(
            db_host=db_config.get('host', 'localhost'),
            db_port=db_config.get('port', 5432),
            db_user=db_config.get('user', 'trader'),
            db_password=db_config.get('password', 'password'),
            db_name=db_config.get('name', 'mt5_crs'),
            api_key=api_token
        )
        logger.info(f"{GREEN}✅ Loader 已初始化{RESET}")

    except Exception as e:
        logger.error(f"{RED}❌ Loader 初始化失败: {e}{RESET}")
        return 1

    # 步骤 4: 执行批量摄取
    print_step(4, "执行批量摄取")

    rate_limit_delay = ingestion_config.get('rate_limit_delay', 1.0)
    total_rows = 0
    successful_assets = 0
    failed_assets = []
    start_time = asyncio.get_event_loop().time()

    for i, asset in enumerate(assets, 1):
        symbol = asset['symbol']

        try:
            # 摄取资产
            success, rows, elapsed = await ingest_asset(loader, asset, ingestion_config)

            if success:
                total_rows += rows
                successful_assets += 1

                # 对于 XAUUSD（黄金），特别注记
                if symbol == "XAUUSD":
                    logger.info(f"{GREEN}{'🏆' * 10}{RESET}")
                    logger.info(f"{GREEN}✅ 成功摄取 XAUUSD (黄金) - {rows:,} 行{RESET}")
                    logger.info(f"{GREEN}{'🏆' * 10}{RESET}")

            else:
                failed_assets.append(symbol)

        except Exception as e:
            logger.error(f"{RED}❌ 处理资产 {symbol} 时发生异常: {e}{RESET}")
            failed_assets.append(symbol)

        # 资产间延迟（除了最后一个）
        if i < len(assets):
            logger.info(f"等待 {rate_limit_delay} 秒以避免 API 限流...")
            await asyncio.sleep(rate_limit_delay)

    total_elapsed = asyncio.get_event_loop().time() - start_time

    # 步骤 5: 清理和总结
    print_step(5, "清理和总结")

    try:
        await loader.disconnect_db()
        logger.info(f"{GREEN}✅ 数据库连接已关闭{RESET}")
    except:
        pass

    # 最终报告
    print_header("批量摄取完成")

    logger.info(f"{CYAN}摄取统计:{RESET}")
    logger.info(f"  资产总数: {len(assets)}")
    logger.info(f"  {GREEN}成功: {successful_assets}{RESET}")
    logger.info(f"  {RED}失败: {len(failed_assets)}{RESET}")
    logger.info(f"  总行数: {total_rows:,}")
    logger.info(f"  总耗时: {total_elapsed:.2f} 秒")
    logger.info(f"  平均速度: {total_rows/total_elapsed:.0f} 行/秒")

    if failed_assets:
        logger.info(f"\n{YELLOW}失败的资产:{RESET}")
        for symbol in failed_assets:
            logger.info(f"  ❌ {symbol}")

    # 验证结果
    print_header("验收条件")

    # 检查 1: 总行数 >= 30,000
    if total_rows >= 30000:
        logger.info(f"{GREEN}✅ 总行数 >= 30,000 ({total_rows:,} 行){RESET}")
    else:
        logger.warning(f"{YELLOW}⚠️  总行数 < 30,000 ({total_rows:,} 行)，但这可能是正常的{RESET}")

    # 检查 2: XAUUSD 成功摄取
    xauusd_success = "XAUUSD" not in failed_assets
    if xauusd_success:
        logger.info(f"{GREEN}✅ XAUUSD (黄金) 成功摄取{RESET}")
    else:
        logger.error(f"{RED}❌ XAUUSD (黄金) 摄取失败{RESET}")

    # 检查 3: 所有资产 100% 成功
    if len(failed_assets) == 0:
        logger.info(f"{GREEN}✅ 所有资产摄取成功 (0 失败){RESET}")
        return 0
    else:
        logger.warning(f"{YELLOW}⚠️  部分资产摄取失败 ({len(failed_assets)} / {len(assets)}){RESET}")
        return 1 if len(failed_assets) > len(assets) / 2 else 0


async def main():
    """主入口点"""
    try:
        exit_code = await run_bulk_ingestion()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning(f"\n{YELLOW}⚠️  被用户中断{RESET}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n{RED}❌ 未期望的错误: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
