#!/usr/bin/env python3
"""
EODHD EOD 和 Intraday 数据下载脚本

使用方法:
    python download_eod_intraday.py --symbol AAPL --api-key YOUR_API_KEY --output data/
    python download_eod_intraday.py --all-symbols --api-key YOUR_API_KEY --output data/
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EODHDDataDownloader:
    """EODHD数据下载器"""

    def __init__(self, api_key: str, output_dir: str):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.base_url = "https://eodhd.com/api"
        self.session = requests.Session()

        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'MT5-CRS-Data-Downloader/1.0'
        })

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """发送API请求"""
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params['api_token'] = self.api_key
        params['fmt'] = 'json'

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()

                # 检查API限制
                if response.status_code == 429:
                    logger.warning("API限流，等待重试...")
                    time.sleep(60 * (attempt + 1))
                    continue

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(5 * (attempt + 1))
                else:
                    raise e

    def get_eod_data(self, symbol: str, exchange: str = "US") -> pd.DataFrame:
        """获取EOD数据"""
        logger.info(f"获取 {symbol} EOD数据...")

        endpoint = f"eod/{symbol}.{exchange}"
        data = self._make_request(endpoint)

        if not data:
            logger.warning(f"未找到 {symbol} 的EOD数据")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        logger.info(f"{symbol} EOD数据: {len(df)} 条记录")
        return df

    def get_intraday_data(self, symbol: str, exchange: str = "US",
                         interval: str = "5m") -> pd.DataFrame:
        """获取分钟级数据"""
        logger.info(f"获取 {symbol} 分钟级数据 ({interval})...")

        endpoint = f"intraday/{symbol}.{exchange}"
        params = {'interval': interval}

        data = self._make_request(endpoint, params)

        if not data:
            logger.warning(f"未找到 {symbol} 的分钟级数据")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()

        logger.info(f"{symbol} 分钟级数据: {len(df)} 条记录")
        return df

    def save_data(self, df: pd.DataFrame, filename: str):
        """保存数据到CSV"""
        if df.empty:
            return

        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path)
        logger.info(f"数据已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="EODHD数据下载器")
    parser.add_argument("--symbol", help="股票代码 (如: AAPL)")
    parser.add_argument("--all-symbols", action="store_true",
                       help="下载所有主流股票")
    parser.add_argument("--api-key", required=True, help="EODHD API密钥")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--exchange", default="US", help="交易所 (默认: US)")
    parser.add_argument("--interval", default="5m",
                       help="分钟级数据间隔 (默认: 5m)")

    args = parser.parse_args()

    # 创建下载器
    downloader = EODHDDataDownloader(args.api_key, args.output)

    # 主流股票列表（可以根据需要扩展）
    major_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META',
        'NFLX', 'BABA', 'ORCL', 'CRM', 'AMD', 'INTC', 'UBER'
    ]

    symbols_to_download = major_symbols if args.all_symbols else [args.symbol]

    if not symbols_to_download:
        logger.error("请指定 --symbol 或使用 --all-symbols")
        sys.exit(1)

    # 下载数据
    for symbol in symbols_to_download:
        try:
            # EOD数据
            eod_df = downloader.get_eod_data(symbol, args.exchange)
            if not eod_df.empty:
                downloader.save_data(eod_df, f"eod/{symbol}_eod.csv")

            # 分钟级数据
            intraday_df = downloader.get_intraday_data(symbol, args.exchange, args.interval)
            if not intraday_df.empty:
                downloader.save_data(intraday_df, f"intraday/{symbol}_intraday_{args.interval}.csv")

            # 避免API限流
            time.sleep(1)

        except Exception as e:
            logger.error(f"下载 {symbol} 数据失败: {e}")
            continue

    logger.info("数据下载完成")

if __name__ == "__main__":
    main()
