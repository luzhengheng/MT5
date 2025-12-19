"""
价格数据采集器 - MVP 版本
使用 Yahoo Finance 作为数据源（免费、可靠）
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import yfinance as yf
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceDataFetcher:
    """价格数据采集器（MVP 版本）"""

    def __init__(self, output_path: str = "/opt/mt5-crs/data_lake/price_daily"):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"初始化 PriceDataFetcher，输出路径: {self.output_path}")

    def _convert_symbol(self, symbol: str) -> str:
        """转换符号格式为 Yahoo Finance 格式

        Args:
            symbol: 标准符号 (如 AAPL.US, BTC-USD, EURUSD)

        Returns:
            Yahoo Finance 符号
        """
        # 股票：AAPL.US -> AAPL
        if symbol.endswith('.US'):
            return symbol.replace('.US', '')

        # 加密货币：已经是正确格式 (BTC-USD)
        if '-USD' in symbol:
            return symbol

        # 外汇：EURUSD -> EURUSD=X
        if symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'USDCNY']:
            return f"{symbol}=X"

        # 商品：GC.COMM -> GC=F (期货)
        if symbol.endswith('.COMM'):
            commodity_map = {
                'GC.COMM': 'GC=F',  # Gold
                'SI.COMM': 'SI=F',  # Silver
                'CL.COMM': 'CL=F',  # Oil WTI
                'NG.COMM': 'NG=F',  # Natural Gas
            }
            return commodity_map.get(symbol, symbol.replace('.COMM', '=F'))

        # 指数：GSPC.INDX -> ^GSPC
        if symbol.endswith('.INDX'):
            index_map = {
                'GSPC.INDX': '^GSPC',
                'NDX.INDX': '^NDX',
                'DJI.INDX': '^DJI',
            }
            return index_map.get(symbol, '^' + symbol.replace('.INDX', ''))

        return symbol

    def fetch_single_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """获取单个资产的历史价格数据

        Args:
            symbol: 资产符号
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天

        Returns:
            价格数据 DataFrame 或 None
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        yf_symbol = self._convert_symbol(symbol)

        try:
            logger.info(f"获取 {symbol} ({yf_symbol}) 的数据：{start_date} 到 {end_date}")

            # 使用 yfinance 下载数据
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

            if df.empty:
                logger.warning(f"{symbol} 没有数据")
                return None

            # 重命名列为标准格式
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adjusted_close'
            })

            # 重置索引，将日期作为列
            df = df.reset_index()
            df = df.rename(columns={'Date': 'date'})

            # 添加符号列
            df['symbol'] = symbol

            # 选择需要的列
            columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']
            df = df[columns]

            # 数据质量检查
            df = self._validate_ohlc(df, symbol)

            logger.info(f"{symbol} 获取到 {len(df)} 条数据")
            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 失败: {e}")
            return None

    def _validate_ohlc(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """验证 OHLC 逻辑

        检查：High >= Close >= Low, High >= Open >= Low
        """
        # 检查 OHLC 逻辑
        invalid_high = (df['high'] < df['close']) | (df['high'] < df['open']) | \
                       (df['high'] < df['low'])
        invalid_low = (df['low'] > df['close']) | (df['low'] > df['open']) | \
                      (df['low'] > df['high'])

        invalid_count = invalid_high.sum() + invalid_low.sum()

        if invalid_count > 0:
            logger.warning(f"{symbol} 有 {invalid_count} 条数据不符合 OHLC 逻辑")
            # 移除异常数据
            df = df[~(invalid_high | invalid_low)]

        # 检查极端价格变化（单日变化 > 100%）
        df['price_change'] = df['close'].pct_change()
        extreme_changes = df['price_change'].abs() > 1.0
        extreme_count = extreme_changes.sum()

        if extreme_count > 0:
            logger.warning(f"{symbol} 有 {extreme_count} 条极端价格变化数据")
            # 标记但不删除（可能是真实的分拆/并股）
            df['quality'] = 'original'
            df.loc[extreme_changes, 'quality'] = 'extreme_change'
        else:
            df['quality'] = 'original'

        df = df.drop(columns=['price_change'])

        return df

    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """批量获取多个资产的数据

        Args:
            symbols: 资产列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            {symbol: DataFrame} 字典
        """
        results = {}

        for symbol in tqdm(symbols, desc="获取价格数据"):
            df = self.fetch_single_symbol(symbol, start_date, end_date)
            if df is not None and not df.empty:
                results[symbol] = df

        logger.info(f"成功获取 {len(results)}/{len(symbols)} 个资产的数据")
        return results

    def save_to_parquet(self, data: Dict[str, pd.DataFrame]):
        """保存数据为 Parquet 文件（每个资产一个文件）

        Args:
            data: {symbol: DataFrame} 字典
        """
        for symbol, df in data.items():
            # 清理文件名中的特殊字符
            safe_symbol = symbol.replace('/', '_').replace('=', '_').replace('^', '_')
            output_file = self.output_path / f"{safe_symbol}.parquet"

            df.to_parquet(
                output_file,
                engine='pyarrow',
                compression='gzip',
                index=False
            )

            logger.info(f"保存 {symbol} 数据到 {output_file}")

    def generate_data_quality_report(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """生成数据质量报告

        Args:
            data: {symbol: DataFrame} 字典

        Returns:
            质量报告 DataFrame
        """
        reports = []

        for symbol, df in data.items():
            report = {
                'symbol': symbol,
                'total_records': len(df),
                'start_date': df['date'].min(),
                'end_date': df['date'].max(),
                'missing_days': 0,  # 简化版暂不计算
                'quality_original': (df['quality'] == 'original').sum(),
                'quality_extreme': (df['quality'] == 'extreme_change').sum(),
                'avg_volume': df['volume'].mean(),
                'avg_close': df['close'].mean(),
            }
            reports.append(report)

        report_df = pd.DataFrame(reports)

        # 保存报告
        report_file = self.output_path / "data_quality_report.csv"
        report_df.to_csv(report_file, index=False)
        logger.info(f"数据质量报告保存到 {report_file}")

        return report_df


def main():
    """主函数示例"""
    import yaml

    # 加载资产配置
    with open('/opt/mt5-crs/config/assets.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 创建采集器
    fetcher = PriceDataFetcher()

    # 获取所有资产列表
    all_symbols = []
    for category in ['stocks', 'crypto', 'forex', 'commodities', 'indices']:
        all_symbols.extend(config['assets'][category])

    logger.info(f"准备获取 {len(all_symbols)} 个资产的数据")

    # 获取数据
    start_date = config['data_collection']['start_date']
    data = fetcher.fetch_multiple_symbols(all_symbols, start_date)

    # 保存数据
    fetcher.save_to_parquet(data)

    # 生成质量报告
    report = fetcher.generate_data_quality_report(data)

    print("\n=== 数据采集统计 ===")
    print(f"成功获取: {len(data)}/{len(all_symbols)} 个资产")
    print(f"总记录数: {sum(len(df) for df in data.values())}")
    print("\n数据质量报告预览:")
    print(report.head(10))


if __name__ == '__main__':
    main()
