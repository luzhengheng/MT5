#!/usr/bin/env python3
"""
Task #013.01: 特征工程批处理器
====================================

将 OHLCV 数据转换为技术特征并存储在 market_features Hypertable 中。

核心功能:
1. 从 market_data_ohlcv 获取按符号的 OHLCV 数据
2. 计算 11 个技术指标 (SMA, RSI, MACD, ATR, Bollinger Bands)
3. 将宽格式转换为长格式 (EAV: time, symbol, feature, value)
4. 使用 COPY 协议批量插入 market_features

协议: v2.2 (异步 + 批量 COPY)
"""

import os
import sys
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List
from dotenv import load_dotenv
import asyncpg

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent.parent
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


class TechnicalIndicators:
    """技术指标计算引擎（无外部依赖）"""

    @staticmethod
    def sma(series: pd.Series, window: int) -> pd.Series:
        """简单移动平均 (SMA)"""
        return series.rolling(window=window).mean()

    @staticmethod
    def rsi(series: pd.Series, window: int = 14) -> pd.Series:
        """相对强度指数 (RSI)

        RSI = 100 - (100 / (1 + RS))
        其中 RS = 平均涨幅 / 平均跌幅
        """
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()

        # 避免除以零
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (移动平均收敛发散)

        返回: (macd_line, signal_line, histogram)
        """
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """平均真实范围 (ATR)

        真实范围 = max(high - low, |high - close_prev|, |low - close_prev|)
        """
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()

        return atr

    @staticmethod
    def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands (布林带)

        返回: (upper_band, middle_band, lower_band)
        """
        sma = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()

        upper = sma + (std * num_std)
        lower = sma - (std * num_std)

        return upper, sma, lower


class FeatureBatchProcessor:
    """批量特征处理引擎"""

    def __init__(self, db_host: str = "localhost", db_port: int = 5432,
                 db_user: str = "trader", db_password: str = "password",
                 db_name: str = "mt5_crs"):
        """初始化处理器"""
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.pool: Optional[asyncpg.Pool] = None

        # 特征列表
        self.features = [
            'sma_20', 'sma_50', 'sma_200',  # 移动平均线
            'rsi_14',                        # 动量指标
            'macd_line', 'macd_signal', 'macd_histogram',  # 趋势跟踪
            'atr_14',                        # 波动率
            'bb_upper', 'bb_middle', 'bb_lower'  # Bollinger Bands
        ]

        logger.info(f"{CYAN}FeatureBatchProcessor 已初始化{RESET}")
        logger.info(f"  数据库: {db_user}@{db_host}:{db_port}/{db_name}")
        logger.info(f"  特征数: {len(self.features)}")

    async def connect_db(self) -> asyncpg.Pool:
        """连接到数据库"""
        if self.pool is not None:
            return self.pool

        logger.info(f"正在连接到 TimescaleDB...")

        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"{GREEN}✅ 已连接到 TimescaleDB{RESET}")
            return self.pool
        except Exception as e:
            logger.error(f"{RED}❌ 连接失败: {e}{RESET}")
            raise

    async def disconnect_db(self):
        """断开数据库连接"""
        if self.pool:
            await self.pool.close()
            logger.info(f"已断开数据库连接")

    async def fetch_ohlcv_by_symbol(self, symbol: str) -> pd.DataFrame:
        """从 market_data_ohlcv 获取符号的 OHLCV 数据"""
        pool = await self.connect_db()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT time, open, high, low, close, volume
                FROM market_data_ohlcv
                WHERE symbol = $1
                ORDER BY time
            """, symbol)

            if not rows:
                logger.warning(f"{YELLOW}⚠️  未找到 {symbol} 的数据{RESET}")
                return pd.DataFrame()

            # 转换 asyncpg Records 为字典列表
            data = [dict(row) for row in rows]
            df = pd.DataFrame(data)
            df['time'] = pd.to_datetime(df['time'])

            logger.info(f"  已获取 {symbol}: {len(df)} 行")
            return df

    def calculate_indicators(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """计算所有技术指标"""
        if df.empty:
            return df

        # 确保数据有效
        df = df.copy()
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

        if len(df) == 0:
            logger.warning(f"  {symbol}: 数据不足，跳过")
            return df

        # 计算指标
        df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        df['sma_200'] = TechnicalIndicators.sma(df['close'], 200)

        df['rsi_14'] = TechnicalIndicators.rsi(df['close'], 14)

        macd_line, macd_signal, macd_histogram = TechnicalIndicators.macd(
            df['close'], fast=12, slow=26, signal=9
        )
        df['macd_line'] = macd_line
        df['macd_signal'] = macd_signal
        df['macd_histogram'] = macd_histogram

        df['atr_14'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'], 14)

        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(
            df['close'], window=20, num_std=2.0
        )
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower

        logger.info(f"  计算完成: {len(df)} 行，{len(self.features)} 个特征")
        return df

    def melt_to_long_format(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """将宽格式转换为长格式 (EAV: time, symbol, feature, value)"""
        if df.empty:
            return df

        # 保留必要列
        id_vars = ['time']
        value_vars = self.features

        # 检查哪些特征列存在
        available_features = [f for f in value_vars if f in df.columns]

        if not available_features:
            logger.warning(f"  {symbol}: 没有找到特征列")
            return pd.DataFrame()

        df_long = df[id_vars + available_features].copy()

        # 融合为长格式
        df_long = df_long.melt(
            id_vars=id_vars,
            value_vars=available_features,
            var_name='feature',
            value_name='value'
        )

        # 添加符号列
        df_long['symbol'] = symbol

        # 重新排列列顺序
        df_long = df_long[['time', 'symbol', 'feature', 'value']]

        # 移除 NaN 值
        df_long = df_long.dropna(subset=['value'])

        logger.info(f"  融合完成: {len(df_long)} 个特征数据点")
        return df_long

    async def bulk_insert_features(self, df_long: pd.DataFrame, batch_size: int = 5000) -> int:
        """使用 COPY 协议批量插入特征"""
        if df_long.empty:
            logger.warning(f"  数据框为空，跳过插入")
            return 0

        pool = await self.connect_db()

        try:
            async with pool.acquire() as conn:
                # 准备数据
                records = [
                    (row['time'], row['symbol'], row['feature'], float(row['value']))
                    for _, row in df_long.iterrows()
                ]

                total_inserted = 0

                # 分批插入
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]

                    try:
                        inserted = await conn.copy_records_to_table(
                            'market_features',
                            records=batch,
                            columns=['time', 'symbol', 'feature', 'value']
                        )

                        total_inserted += len(batch)
                        percent = (total_inserted / len(records)) * 100
                        logger.info(f"  进度: {total_inserted}/{len(records)} ({percent:.1f}%)")

                    except asyncpg.UniqueViolationError:
                        # 重复记录 - 自动跳过
                        logger.warning(f"  批次 {i//batch_size + 1}: 发现重复特征，已跳过")
                        continue
                    except Exception as e:
                        logger.error(f"{RED}❌ 批次 {i//batch_size + 1} 失败: {e}{RESET}")
                        raise

                logger.info(f"{GREEN}✅ 已插入 {total_inserted} 个特征{RESET}")
                return total_inserted

        except Exception as e:
            logger.error(f"{RED}❌ 批量插入失败: {e}{RESET}")
            raise

    async def process_symbol(self, symbol: str) -> Tuple[int, float]:
        """完整处理流程: 获取 → 计算 → 融合 → 插入"""
        logger.info(f"{YELLOW}{'─' * 70}{RESET}")
        logger.info(f"{BLUE}正在处理资产: {symbol}{RESET}")
        logger.info(f"{'─' * 70}")

        start_time = asyncio.get_event_loop().time()

        try:
            # Step 1: 获取 OHLCV 数据
            logger.info(f"[1/4] 获取 OHLCV 数据...")
            df_ohlcv = await self.fetch_ohlcv_by_symbol(symbol)

            if df_ohlcv.empty:
                logger.warning(f"{YELLOW}⚠️  {symbol} 没有数据{RESET}")
                return 0, 0

            # Step 2: 计算指标
            logger.info(f"[2/4] 计算技术指标...")
            df_features = self.calculate_indicators(df_ohlcv, symbol)

            if df_features.empty:
                logger.warning(f"{YELLOW}⚠️  {symbol} 指标计算失败{RESET}")
                return 0, 0

            # Step 3: 转换为长格式
            logger.info(f"[3/4] 转换为长格式...")
            df_long = self.melt_to_long_format(df_features, symbol)

            if df_long.empty:
                logger.warning(f"{YELLOW}⚠️  {symbol} 融合失败{RESET}")
                return 0, 0

            # Step 4: 批量插入
            logger.info(f"[4/4] 批量插入数据库...")
            rows_inserted = await self.bulk_insert_features(df_long)

            elapsed = asyncio.get_event_loop().time() - start_time

            logger.info(f"{GREEN}✅ {symbol} 处理完成{RESET}")
            logger.info(f"  插入行数: {rows_inserted}")
            logger.info(f"  耗时: {elapsed:.2f}秒")
            logger.info(f"  速度: {rows_inserted/elapsed:.0f} rows/sec")

            return rows_inserted, elapsed

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.error(f"{RED}❌ {symbol} 处理失败: {e}{RESET}")
            import traceback
            traceback.print_exc()
            return 0, elapsed


# ================================================================================
# 主函数 (用于测试)
# ================================================================================

async def main():
    """主入口点（示例）"""
    # 初始化
    processor = FeatureBatchProcessor()

    try:
        # 处理单个符号
        rows, elapsed = await processor.process_symbol("EURUSD")
        logger.info(f"\n结果: {rows} 行, {elapsed:.2f}秒")

    finally:
        await processor.disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
