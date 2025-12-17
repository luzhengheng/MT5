#!/usr/bin/env python3
"""
EODHD 技术指标数据下载脚本

下载RSI、MACD、布林带等技术指标数据
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalIndicatorsDownloader:
    """技术指标数据下载器"""

    def __init__(self, api_key: str, output_dir: str):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.base_url = "https://eodhd.com/api"
        self.session = requests.Session()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, prices: pd.Series,
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> tuple:
        """计算MACD指标"""
        fast_ema = prices.ewm(span=fast_period).mean()
        slow_ema = prices.ewm(span=slow_period).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, prices: pd.Series,
                                period: int = 20,
                                std_dev: float = 2.0) -> tuple:
        """计算布林带"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band, sma, lower_band

    def process_technical_indicators(self, eod_data_path: str, symbol: str) -> pd.DataFrame:
        """处理技术指标"""
        logger.info(f"处理 {symbol} 技术指标...")

        # 读取EOD数据
        df = pd.read_csv(eod_data_path, index_col='date', parse_dates=True)

        if 'close' not in df.columns:
            logger.error(f"{symbol} 数据缺少close价格列")
            return pd.DataFrame()

        prices = df['close']

        # 计算技术指标
        df['rsi'] = self.calculate_rsi(prices)
        df['macd_line'], df['macd_signal'], df['macd_histogram'] = self.calculate_macd(prices)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(prices)

        # 移动平均线
        df['sma_20'] = prices.rolling(window=20).mean()
        df['sma_50'] = prices.rolling(window=50).mean()
        df['ema_12'] = prices.ewm(span=12).mean()
        df['ema_26'] = prices.ewm(span=26).mean()

        # 波动率指标
        df['returns'] = prices.pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)

        logger.info(f"{symbol} 技术指标计算完成")
        return df

def main():
    parser = argparse.ArgumentParser(description="技术指标数据下载器")
    parser.add_argument("--symbol", help="股票代码")
    parser.add_argument("--all-symbols", action="store_true", help="处理所有股票")
    parser.add_argument("--api-key", required=True, help="EODHD API密钥")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--eod-dir", help="EOD数据目录", default="data/mt5/datasets/eod")

    args = parser.parse_args()

    downloader = TechnicalIndicatorsDownloader(args.api_key, args.output)

    # 主流股票列表
    major_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    symbols_to_process = major_symbols if args.all_symbols else [args.symbol]

    for symbol in symbols_to_process:
        try:
            eod_file = Path(args.eod_dir) / f"{symbol}_eod.csv"
            if not eod_file.exists():
                logger.warning(f"EOD数据文件不存在: {eod_file}")
                continue

            # 处理技术指标
            tech_df = downloader.process_technical_indicators(str(eod_file), symbol)
            if not tech_df.empty:
                output_path = Path(args.output) / f"technical/{symbol}_technical.csv"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                tech_df.to_csv(output_path)
                logger.info(f"{symbol} 技术指标数据已保存")

        except Exception as e:
            logger.error(f"处理 {symbol} 技术指标失败: {e}")
            continue

    logger.info("技术指标处理完成")

if __name__ == "__main__":
    main()
