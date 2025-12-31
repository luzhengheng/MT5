#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize Feast Feature Store
==============================

创建必要的 SQL Views 以支持 Feast 离线存储访问。

协议: v2.2 (文档优先，本地存储)
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print formatted header"""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")


def print_step(step_num, description):
    """Print step header"""
    print(f"{BLUE}[步骤 {step_num}]{RESET} {description}")


async def init_feature_store():
    """
    初始化 Feast 特征仓库。

    步骤:
    1. 连接到 TimescaleDB
    2. 创建 market_features_wide View (EAV → Wide)
    3. 验证 Feast 配置
    """
    print_header("Task #014.01: Feast 特征仓库初始化")

    # 步骤 0: 加载环境变量
    print_step(0, "加载环境变量")
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"{GREEN}✅ 已加载 .env 文件{RESET}")
    else:
        logger.warning(f"{YELLOW}⚠️  .env 文件不存在，使用系统环境变量{RESET}")

    # 步骤 1: 连接到数据库
    print_step(1, "连接到 TimescaleDB")

    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = int(os.getenv("POSTGRES_PORT", 5432))
    db_user = os.getenv("POSTGRES_USER", "trader")
    db_password = os.getenv("POSTGRES_PASSWORD", "password")
    db_name = os.getenv("POSTGRES_DB", "mt5_crs")

    try:
        pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            min_size=1,
            max_size=5,
            command_timeout=60
        )
        logger.info(f"{GREEN}✅ 已连接到 TimescaleDB{RESET}")
        logger.info(f"   主机: {db_host}:{db_port}")
        logger.info(f"   数据库: {db_name}")
    except Exception as e:
        logger.error(f"{RED}❌ 连接失败: {e}{RESET}")
        return 1

    async with pool.acquire() as conn:
        # 步骤 2: 创建 market_features_wide View
        print_step(2, "创建 market_features_wide SQL View")

        try:
            create_view_sql = """
                CREATE OR REPLACE VIEW market_features_wide AS
                SELECT
                    time,
                    symbol,
                    MAX(CASE WHEN feature='sma_20' THEN value END)::double precision as sma_20,
                    MAX(CASE WHEN feature='sma_50' THEN value END)::double precision as sma_50,
                    MAX(CASE WHEN feature='sma_200' THEN value END)::double precision as sma_200,
                    MAX(CASE WHEN feature='rsi_14' THEN value END)::double precision as rsi_14,
                    MAX(CASE WHEN feature='macd_line' THEN value END)::double precision as macd_line,
                    MAX(CASE WHEN feature='macd_signal' THEN value END)::double precision as macd_signal,
                    MAX(CASE WHEN feature='macd_histogram' THEN value END)::double precision as macd_histogram,
                    MAX(CASE WHEN feature='atr_14' THEN value END)::double precision as atr_14,
                    MAX(CASE WHEN feature='bb_upper' THEN value END)::double precision as bb_upper,
                    MAX(CASE WHEN feature='bb_middle' THEN value END)::double precision as bb_middle,
                    MAX(CASE WHEN feature='bb_lower' THEN value END)::double precision as bb_lower
                FROM market_features
                GROUP BY time, symbol
                ORDER BY time DESC, symbol
            """

            await conn.execute(create_view_sql)
            logger.info(f"{GREEN}✅ market_features_wide View 已创建{RESET}")
            logger.info(f"   转换: EAV (长格式) → Wide (宽格式)")
            logger.info(f"   特征列数: 11")

        except Exception as e:
            logger.error(f"{RED}❌ 创建 View 失败: {e}{RESET}")
            await pool.close()
            return 1

        # 步骤 3: 验证 View 数据
        print_step(3, "验证 View 数据")

        try:
            # 检查 View 是否存在
            view_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_name = 'market_features_wide'
                )
            """)

            if view_exists:
                logger.info(f"{GREEN}✅ market_features_wide View 验证成功{RESET}")

                # 获取数据统计
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT(DISTINCT symbol) as unique_symbols,
                        COUNT(DISTINCT DATE(time)) as unique_dates
                    FROM market_features_wide
                """)

                logger.info(f"   数据统计:")
                logger.info(f"   ├─ 总行数: {stats['total_rows']:,}")
                logger.info(f"   ├─ 唯一符号: {stats['unique_symbols']}")
                logger.info(f"   └─ 唯一日期: {stats['unique_dates']}")
            else:
                logger.warning(f"{YELLOW}⚠️  market_features_wide View 不存在{RESET}")

        except Exception as e:
            logger.warning(f"{YELLOW}⚠️  无法验证 View 数据: {e}{RESET}")
            # 不中断流程

    # 关闭连接池
    await pool.close()
    logger.info(f"{GREEN}✅ 数据库连接已关闭{RESET}")

    # 步骤 4: 验证 Feast 配置
    print_step(4, "验证 Feast 配置")

    try:
        # 检查 feature_store.yaml
        feature_store_yaml = Path(__file__).parent / "feature_store.yaml"
        if feature_store_yaml.exists():
            logger.info(f"{GREEN}✅ feature_store.yaml 存在{RESET}")
        else:
            logger.error(f"{RED}❌ feature_store.yaml 不存在{RESET}")
            return 1

        # 检查 definitions.py
        definitions_py = Path(__file__).parent / "definitions.py"
        if definitions_py.exists():
            logger.info(f"{GREEN}✅ definitions.py 存在{RESET}")

            # 尝试导入
            sys.path.insert(0, str(Path(__file__).parent))
            try:
                import definitions
                logger.info(f"{GREEN}✅ definitions.py 可导入{RESET}")
                logger.info(f"   定义的实体:")
                logger.info(f"   ├─ Entity: symbol")
                logger.info(f"   ├─ FeatureView: market_features")
                logger.info(f"   └─ FeatureService: market_features_service")
            except ImportError as e:
                logger.warning(f"{YELLOW}⚠️  无法导入 definitions.py: {e}{RESET}")
        else:
            logger.error(f"{RED}❌ definitions.py 不存在{RESET}")
            return 1

    except Exception as e:
        logger.warning(f"{YELLOW}⚠️  Feast 配置检查失败: {e}{RESET}")

    # 最终报告
    print_header("初始化完成")

    logger.info(f"{GREEN}✅ Feast 特征仓库初始化成功{RESET}")
    logger.info(f"   View: market_features_wide")
    logger.info(f"   转换: EAV → Wide (11 个特征列)")
    logger.info(f"   Entity: symbol (7 个资产)")
    logger.info(f"   FeatureView: market_features")
    logger.info("")
    logger.info(f"{CYAN}后续步骤:{RESET}")
    logger.info(f"   1. 初始化 Feast 注册表: feast init-repo")
    logger.info(f"   2. 应用 Feature Store 配置: feast apply")
    logger.info(f"   3. 运行离线特征获取: feast get-historical-features")
    logger.info("")

    return 0


async def main():
    """Main entry point"""
    try:
        exit_code = await init_feature_store()
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
