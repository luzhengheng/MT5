#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Data Loader for Model Training

从 Feature Serving API 和数据库加载特征数据用于模型训练。

协议: v2.2 (本地存储，文档优先)
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import requests
import asyncpg

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
import os

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
CYAN = "\033[96m"
RESET = "\033[0m"


class APIDataLoader:
    """从 Feature Serving API 加载特征数据"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        """初始化数据加载器"""
        self.api_url = api_url
        logger.info(f"{GREEN}✅ APIDataLoader 已初始化{RESET}")
        logger.info(f"   API URL: {api_url}")

    def fetch_features(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        从 API 获取特征数据

        参数:
            symbols: 交易对列表 ['EURUSD', 'XAUUSD']
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            features: 特征列表 (默认所有)

        返回:
            DataFrame with columns [time, symbol, sma_20, sma_50, ...]
        """
        if features is None:
            features = [
                'sma_20', 'sma_50', 'sma_200',
                'rsi_14',
                'macd_line', 'macd_signal', 'macd_histogram',
                'atr_14',
                'bb_upper', 'bb_middle', 'bb_lower'
            ]

        logger.info(f"从 API 获取特征数据...")
        logger.info(f"  符号: {symbols}")
        logger.info(f"  特征: {features}")
        logger.info(f"  时间: {start_date} 至 {end_date}")

        try:
            # 调用 API 获取历史特征
            payload = {
                "symbols": symbols,
                "features": features,
                "start_date": start_date,
                "end_date": end_date
            }

            response = requests.post(
                f"{self.api_url}/features/historical",
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise ValueError(f"API 返回状态码 {response.status_code}: {response.text}")

            data = response.json()

            if data.get('status') != 'success':
                raise ValueError(f"API 返回错误: {data.get('message')}")

            # 转换为 DataFrame
            records = data.get('data', [])
            logger.info(f"{GREEN}✅ 获取 {len(records)} 行特征数据{RESET}")

            # 格式化数据
            rows = []
            for record in records:
                row = {
                    'time': pd.to_datetime(record['time']),
                    'symbol': record['symbol']
                }
                row.update(record['values'])
                rows.append(row)

            df = pd.DataFrame(rows)

            # 确保列顺序
            cols = ['time', 'symbol'] + features
            available_cols = [c for c in cols if c in df.columns]
            df = df[available_cols]

            logger.info(f"特征数据格式化完成: {df.shape}")
            logger.info(f"  日期范围: {df['time'].min()} 至 {df['time'].max()}")
            logger.info(f"  符号数: {df['symbol'].nunique()}")

            return df

        except Exception as e:
            logger.error(f"{RED}❌ 获取特征数据失败: {e}{RESET}")
            raise

    async def fetch_ohlcv_async(
        self,
        symbol: str,
        start_date: str = "2010-01-01",
        end_date: str = "2025-12-31"
    ) -> pd.DataFrame:
        """
        异步获取 OHLCV 数据（从数据库）

        参数:
            symbol: 交易对 'EURUSD'
            start_date: 开始日期
            end_date: 结束日期

        返回:
            DataFrame with columns [time, symbol, open, high, low, close, volume]
        """
        load_dotenv(PROJECT_ROOT / ".env")

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

            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT time, symbol, open, high, low, close, volume
                    FROM market_data_ohlcv
                    WHERE symbol = $1
                    AND time >= $2::timestamp
                    AND time <= $3::timestamp
                    ORDER BY time
                """, symbol, start_date, end_date)

                if not rows:
                    logger.warning(f"{YELLOW}⚠️  未找到 {symbol} 的 OHLCV 数据{RESET}")
                    return pd.DataFrame()

                # 转换为 DataFrame
                data = [dict(row) for row in rows]
                df = pd.DataFrame(data)
                df['time'] = pd.to_datetime(df['time'])

                logger.info(f"获取 {symbol} 的 OHLCV 数据: {len(df)} 行")

                return df

            await pool.close()

        except Exception as e:
            logger.error(f"{RED}❌ 获取 OHLCV 数据失败: {e}{RESET}")
            raise

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: str = "2010-01-01",
        end_date: str = "2025-12-31"
    ) -> pd.DataFrame:
        """
        同步获取 OHLCV 数据（从数据库）

        参数:
            symbol: 交易对
            start_date: 开始日期
            end_date: 结束日期

        返回:
            DataFrame with [time, symbol, open, high, low, close, volume]
        """
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            df = loop.run_until_complete(
                self.fetch_ohlcv_async(symbol, start_date, end_date)
            )
            return df
        finally:
            loop.close()

    def merge_features_ohlcv(
        self,
        features_df: pd.DataFrame,
        ohlcv_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        合并特征和 OHLCV 数据

        参数:
            features_df: 特征 DataFrame
            ohlcv_df: OHLCV DataFrame

        返回:
            合并后的 DataFrame
        """
        logger.info(f"合并特征和 OHLCV 数据...")

        # 将 time 转换为日期 (去掉时间部分用于合并)
        features_df = features_df.copy()
        ohlcv_df = ohlcv_df.copy()

        features_df['date'] = features_df['time'].dt.date
        ohlcv_df['date'] = ohlcv_df['time'].dt.date

        # 按 symbol 和 date 合并
        merged = features_df.merge(
            ohlcv_df,
            on=['symbol', 'date'],
            how='inner'
        )

        logger.info(f"合并完成: {merged.shape[0]} 行")
        logger.info(f"  列数: {merged.shape[1]}")

        return merged
