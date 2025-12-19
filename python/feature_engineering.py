#!/usr/bin/env python3
"""
多因子特征工程脚本

将原始数据处理为多因子宽表，用于模型训练
"""

import argparse
import logging
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiFactorEngineer:
    """多因子特征工程"""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.scaler = StandardScaler()

    def load_eod_data(self, symbol: str) -> pd.DataFrame:
        """加载EOD数据"""
        eod_file = self.input_dir / "eod" / f"{symbol}_eod.csv"
        if not eod_file.exists():
            return pd.DataFrame()

        df = pd.read_csv(eod_file, index_col='date', parse_dates=True)
        df['symbol'] = symbol
        return df

    def load_technical_data(self, symbol: str) -> pd.DataFrame:
        """加载技术指标数据"""
        tech_file = self.input_dir / "technical" / f"{symbol}_technical.csv"
        if not tech_file.exists():
            return pd.DataFrame()

        df = pd.read_csv(tech_file, index_col='date', parse_dates=True)
        return df

    def create_price_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建价格因子"""
        if 'close' not in df.columns:
            return df

        prices = df['close']

        # 动量因子
        df['momentum_1d'] = prices.pct_change(1)
        df['momentum_5d'] = prices.pct_change(5)
        df['momentum_20d'] = prices.pct_change(20)

        # 波动率因子
        df['volatility_5d'] = df['momentum_1d'].rolling(5).std()
        df['volatility_20d'] = df['momentum_1d'].rolling(20).std()

        # 成交量因子
        if 'volume' in df.columns:
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()

        return df

    def create_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建技术因子"""
        # RSI因子
        if 'rsi' in df.columns:
            df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
            df['rsi_oversold'] = (df['rsi'] < 30).astype(int)

        # MACD因子
        if 'macd_histogram' in df.columns:
            df['macd_signal'] = (df['macd_histogram'] > 0).astype(int)

        # 布林带因子
        if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'close']):
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['bb_breakout'] = ((df['close'] > df['bb_upper']) | (df['close'] < df['bb_lower'])).astype(int)

        return df

    def normalize_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化因子"""
        factor_cols = [col for col in df.columns if col not in ['symbol', 'date'] and df[col].dtype in ['float64', 'int64']]

        if factor_cols:
            # Z-score标准化
            df_normalized = df.copy()
            df_normalized[factor_cols] = self.scaler.fit_transform(df[factor_cols])
            return df_normalized

        return df

    def process_symbol(self, symbol: str) -> pd.DataFrame:
        """处理单个股票的多因子数据"""
        logger.info(f"处理 {symbol} 多因子数据...")

        # 加载基础数据
        eod_df = self.load_eod_data(symbol)
        tech_df = self.load_technical_data(symbol)

        if eod_df.empty:
            logger.warning(f"{symbol} EOD数据不存在")
            return pd.DataFrame()

        # 合并数据
        combined_df = eod_df.copy()
        if not tech_df.empty:
            # 合并技术指标数据
            combined_df = combined_df.join(tech_df, rsuffix='_tech')

        # 创建价格因子
        combined_df = self.create_price_factors(combined_df)

        # 创建技术因子
        combined_df = self.create_technical_factors(combined_df)

        # 重置索引，添加日期列
        combined_df = combined_df.reset_index()
        combined_df['date'] = pd.to_datetime(combined_df['date']).dt.date

        logger.info(f"{symbol} 多因子处理完成，生成 {len(combined_df)} 条记录")
        return combined_df

    def process_all_symbols(self, symbols: list = None) -> pd.DataFrame:
        """处理所有股票的多因子数据"""
        if symbols is None:
            # 默认主流股票
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

        all_data = []

        for symbol in symbols:
            try:
                symbol_data = self.process_symbol(symbol)
                if not symbol_data.empty:
                    all_data.append(symbol_data)
            except Exception as e:
                logger.error(f"处理 {symbol} 失败: {e}")
                continue

        if not all_data:
            logger.error("没有成功处理任何股票数据")
            return pd.DataFrame()

        # 合并所有股票数据
        combined_df = pd.concat(all_data, ignore_index=True)

        # 标准化因子
        normalized_df = self.normalize_factors(combined_df)

        return normalized_df

def main():
    parser = argparse.ArgumentParser(description="多因子特征工程")
    parser.add_argument("--input", required=True, help="输入数据目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--symbol", help="指定股票代码")
    parser.add_argument("--all-symbols", action="store_true", help="处理所有股票")

    args = parser.parse_args()

    engineer = MultiFactorEngineer(args.input, args.output)

    if args.symbol:
        result_df = engineer.process_symbol(args.symbol)
    elif args.all_symbols:
        result_df = engineer.process_all_symbols()
    else:
        logger.error("请指定 --symbol 或 --all-symbols")
        return

    if not result_df.empty:
        output_path = Path(args.output) / "multi_factor_dataset.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        logger.info(f"多因子数据集已保存到: {output_path}")
        logger.info(f"数据集形状: {result_df.shape}")
    else:
        logger.error("没有生成任何数据")

if __name__ == "__main__":
    main()
