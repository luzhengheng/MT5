#!/usr/bin/env python3
"""
Task #013.01: 特征工程管道执行脚本
=====================================

批量处理所有 7 个战略资产的特征工程。

使用方法:
    python3 scripts/run_feature_pipeline.py
"""

import os
import sys
import asyncio
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_engineering.batch_processor import FeatureBatchProcessor

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


async def process_feature_pipeline(config_path="config/assets.yaml"):
    """
    执行特征工程管道。

    步骤:
    1. 加载环境变量和配置
    2. 初始化特征处理器
    3. 循环处理每个资产
    4. 生成最终报告
    """
    print_header("Task #013.01: 特征工程管道")

    # 步骤 1: 加载环境变量
    print_step(1, "加载环境变量")
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"{GREEN}✅ 已加载 .env 文件{RESET}")
    else:
        logger.warning(f"{YELLOW}⚠️  .env 文件不存在，使用系统环境变量{RESET}")

    # 步骤 2: 加载配置
    print_step(2, "加载资产配置")
    full_config_path = PROJECT_ROOT / config_path
    config = load_config(full_config_path)

    if not config:
        logger.error(f"{RED}❌ 无法加载配置文件{RESET}")
        return 1

    # 获取资产列表
    assets = config.get('task_012_05_assets', [])
    db_config = config.get('database', {})

    logger.info(f"{GREEN}✅ 加载了 {len(assets)} 个资产{RESET}")
    for asset in assets:
        logger.info(f"  • {asset['symbol']}: {asset['name']}")

    # 步骤 3: 初始化特征处理器
    print_step(3, "初始化特征处理器")

    try:
        processor = FeatureBatchProcessor(
            db_host=db_config.get('host', 'localhost'),
            db_port=db_config.get('port', 5432),
            db_user=db_config.get('user', 'trader'),
            db_password=db_config.get('password', 'password'),
            db_name=db_config.get('name', 'mt5_crs')
        )
        logger.info(f"{GREEN}✅ 处理器已初始化{RESET}")

    except Exception as e:
        logger.error(f"{RED}❌ 处理器初始化失败: {e}{RESET}")
        return 1

    # 步骤 4: 执行特征工程
    print_step(4, "执行特征工程")

    total_rows = 0
    successful_assets = 0
    failed_assets = []
    start_time = asyncio.get_event_loop().time()

    for i, asset in enumerate(assets, 1):
        symbol = asset['symbol']

        try:
            # 处理资产
            rows, elapsed = await processor.process_symbol(symbol)

            if rows > 0:
                total_rows += rows
                successful_assets += 1
            else:
                failed_assets.append(symbol)

        except Exception as e:
            logger.error(f"{RED}❌ 处理资产 {symbol} 时发生异常: {e}{RESET}")
            failed_assets.append(symbol)

        # 资产间延迟（除了最后一个）
        if i < len(assets):
            logger.info(f"等待 1.0 秒以避免数据库压力...")
            await asyncio.sleep(1.0)

    total_elapsed = asyncio.get_event_loop().time() - start_time

    # 步骤 5: 清理和总结
    print_step(5, "清理和总结")

    try:
        await processor.disconnect_db()
        logger.info(f"{GREEN}✅ 数据库连接已关闭{RESET}")
    except:
        pass

    # 最终报告
    print_header("特征工程完成")

    logger.info(f"{CYAN}处理统计:{RESET}")
    logger.info(f"  资产总数: {len(assets)}")
    logger.info(f"  {GREEN}成功: {successful_assets}{RESET}")
    logger.info(f"  {RED}失败: {len(failed_assets)}{RESET}")
    logger.info(f"  总特征行数: {total_rows:,}")
    logger.info(f"  总耗时: {total_elapsed:.2f} 秒")
    logger.info(f"  平均速度: {total_rows/total_elapsed:.0f} 行/秒")

    if failed_assets:
        logger.info(f"\n{YELLOW}失败的资产:{RESET}")
        for symbol in failed_assets:
            logger.info(f"  ❌ {symbol}")

    # 验收条件
    print_header("验收条件")

    # 检查 1: 特征行数 >= 400,000
    if total_rows >= 400000:
        logger.info(f"{GREEN}✅ 特征行数 >= 400,000 ({total_rows:,} 行){RESET}")
    else:
        logger.warning(f"{YELLOW}⚠️  特征行数 < 400,000 ({total_rows:,} 行){RESET}")

    # 检查 2: 所有资产 100% 成功
    if len(failed_assets) == 0:
        logger.info(f"{GREEN}✅ 所有资产处理成功 (0 失败){RESET}")
        return 0
    else:
        logger.warning(f"{YELLOW}⚠️  部分资产处理失败 ({len(failed_assets)} / {len(assets)}){RESET}")
        return 1 if len(failed_assets) > len(assets) / 2 else 0


async def main():
    """主入口点"""
    try:
        exit_code = await process_feature_pipeline()
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
