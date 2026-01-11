#!/usr/bin/env python3
"""
Task #013.01: 特征存储表初始化
================================================

初始化 market_features Hypertable 用于存储技术指标。

协议: v2.2 (异步 + 批量 COPY)

使用方法:
    python3 scripts/init_feature_db.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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


async def init_feature_db():
    """
    初始化特征存储数据库。

    步骤:
    1. 连接到 TimescaleDB
    2. 创建 market_features 表
    3. 启用 Hypertable 分区
    4. 创建优化索引
    5. 验证表结构
    """
    print_header("Task #013.01: 特征存储初始化")

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

    # 步骤 2: 创建表
    print_step(2, "创建 market_features 表")

    async with pool.acquire() as conn:
        try:
            # 检查表是否已存在
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'market_features'
                )
            """)

            if table_exists:
                logger.info(f"{YELLOW}⚠️  表已存在，跳过创建{RESET}")
            else:
                # 创建表
                create_table_sql = """
                    CREATE TABLE market_features (
                        time TIMESTAMPTZ NOT NULL,
                        symbol TEXT NOT NULL,
                        feature TEXT NOT NULL,
                        value DOUBLE PRECISION,

                        CONSTRAINT market_features_time_symbol_feature_unique
                            UNIQUE (time, symbol, feature)
                    );
                """

                await conn.execute(create_table_sql)
                logger.info(f"{GREEN}✅ market_features 表已创建{RESET}")
                logger.info(f"   列:")
                logger.info(f"   ├─ time (TIMESTAMPTZ)")
                logger.info(f"   ├─ symbol (TEXT)")
                logger.info(f"   ├─ feature (TEXT)")
                logger.info(f"   └─ value (DOUBLE PRECISION)")

        except Exception as e:
            logger.error(f"{RED}❌ 创建表失败: {e}{RESET}")
            await pool.close()
            return 1

        # 步骤 3: 启用 Hypertable
        print_step(3, "启用 TimescaleDB Hypertable")

        try:
            result = await conn.fetchval("""
                SELECT create_hypertable('market_features', 'time', if_not_exists => TRUE)
            """)

            logger.info(f"{GREEN}✅ Hypertable 已启用{RESET}")
            logger.info(f"   时间列: time")
            logger.info(f"   自动分区间隔: 1 month (默认)")

        except Exception as e:
            logger.error(f"{RED}❌ 启用 Hypertable 失败: {e}{RESET}")
            await pool.close()
            return 1

        # 步骤 4: 创建索引
        print_step(4, "创建优化索引")

        try:
            # 主索引: (symbol, time DESC, feature)
            create_index_sql = """
                CREATE INDEX IF NOT EXISTS idx_market_features_symbol_time
                ON market_features (symbol, time DESC, feature);
            """

            await conn.execute(create_index_sql)
            logger.info(f"{GREEN}✅ 索引已创建{RESET}")
            logger.info(f"   索引: (symbol, time DESC, feature)")

        except Exception as e:
            logger.error(f"{RED}❌ 创建索引失败: {e}{RESET}")
            await pool.close()
            return 1

        # 步骤 5: 验证表结构
        print_step(5, "验证表结构")

        try:
            # 获取列信息
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'market_features'
                ORDER BY ordinal_position
            """)

            logger.info(f"{GREEN}✅ 表结构验证完成{RESET}")
            logger.info(f"   列定义:")

            for col in columns:
                nullable = "NOT NULL" if col['is_nullable'] == 'NO' else "NULL"
                logger.info(f"   ├─ {col['column_name']:15s} {col['data_type']:20s} {nullable}")

            # 检查约束
            constraints = await conn.fetch("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'market_features'
            """)

            if constraints:
                logger.info(f"   约束定义:")
                for constr in constraints:
                    logger.info(f"   ├─ {constr['constraint_name']:30s} ({constr['constraint_type']})")

            # 检查索引
            indexes = await conn.fetch("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'market_features'
            """)

            if indexes:
                logger.info(f"   索引定义:")
                for idx in indexes:
                    logger.info(f"   ├─ {idx['indexname']}")

        except Exception as e:
            logger.error(f"{RED}❌ 验证表结构失败: {e}{RESET}")
            await pool.close()
            return 1

        # 步骤 6: 检查 Hypertable 状态
        print_step(6, "检查 Hypertable 状态")

        try:
            # 检查是否是 Hypertable
            is_hypertable = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables
                    WHERE hypertable_name = 'market_features'
                )
            """)

            if is_hypertable:
                logger.info(f"{GREEN}✅ market_features 是 TimescaleDB Hypertable{RESET}")

                # 获取分区信息
                partition_info = await conn.fetch("""
                    SELECT * FROM timescaledb_information.hypertables
                    WHERE hypertable_name = 'market_features'
                """)

                if partition_info:
                    info = partition_info[0]
                    logger.info(f"   分区信息:")
                    logger.info(f"   ├─ 时间列: {info['time_column_name']}")
                    logger.info(f"   ├─ 压缩启用: {info['compression_enabled']}")
                    logger.info(f"   └─ 块大小: {info['chunk_time_interval']}")
            else:
                logger.warning(f"{YELLOW}⚠️  market_features 可能不是 Hypertable{RESET}")

        except Exception as e:
            logger.warning(f"{YELLOW}⚠️  无法检查 Hypertable 状态: {e}{RESET}")
            # 不中断流程，继续

    # 关闭连接池
    await pool.close()
    logger.info(f"{GREEN}✅ 数据库连接已关闭{RESET}")

    # 最终报告
    print_header("初始化完成")

    logger.info(f"{GREEN}✅ 成功{RESET}")
    logger.info(f"   表: market_features")
    logger.info(f"   类型: TimescaleDB Hypertable")
    logger.info(f"   列数: 4 (time, symbol, feature, value)")
    logger.info(f"   约束: UNIQUE (time, symbol, feature)")
    logger.info(f"   索引: 1 (symbol, time DESC, feature)")
    logger.info("")
    logger.info(f"{CYAN}后续步骤:{RESET}")
    logger.info(f"   1. 创建特征处理器: src/feature_engineering/batch_processor.py")
    logger.info(f"   2. 运行特征管道: python3 scripts/run_feature_pipeline.py")
    logger.info("")

    return 0


async def main():
    """主入口点"""
    try:
        exit_code = await init_feature_db()
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
