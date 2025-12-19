"""
特征工程主类 - 整合价格数据和情感数据，生成完整特征集
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from .basic_features import BasicFeatures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """特征工程主类"""

    def __init__(self, config: dict = None):
        """
        Args:
            config: 特征工程配置（来自 features.yaml）
        """
        self.config = config or {}
        logger.info("初始化 FeatureEngineer")

    def load_price_data(self, symbol: str, data_path: str = "/opt/mt5-crs/data_lake/price_daily") -> Optional[pd.DataFrame]:
        """加载价格数据

        Args:
            symbol: 资产符号
            data_path: 数据路径

        Returns:
            价格数据 DataFrame
        """
        # 清理文件名中的特殊字符
        safe_symbol = symbol.replace('/', '_').replace('=', '_').replace('^', '_')
        file_path = Path(data_path) / f"{safe_symbol}.parquet"

        if not file_path.exists():
            logger.warning(f"价格数据文件不存在: {file_path}")
            return None

        try:
            df = pd.read_parquet(file_path)
            logger.info(f"加载 {symbol} 价格数据: {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"加载 {symbol} 价格数据失败: {e}")
            return None

    def load_news_sentiment(self, data_path: str = "/opt/mt5-crs/data_lake/news_processed") -> Optional[pd.DataFrame]:
        """加载新闻情感数据

        Args:
            data_path: 数据路径

        Returns:
            新闻情感数据 DataFrame
        """
        data_path = Path(data_path)

        # 查找所有 parquet 文件
        parquet_files = list(data_path.rglob("*.parquet"))

        if not parquet_files:
            logger.warning(f"未找到新闻数据文件: {data_path}")
            return None

        try:
            # 合并所有文件
            dfs = []
            for file_path in parquet_files:
                df = pd.read_parquet(file_path)
                dfs.append(df)

            news_df = pd.concat(dfs, ignore_index=True)
            logger.info(f"加载新闻情感数据: {len(news_df)} 条")
            return news_df

        except Exception as e:
            logger.error(f"加载新闻情感数据失败: {e}")
            return None

    def aggregate_sentiment_by_symbol(self, news_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """聚合指定 ticker 的情感数据（按日期）

        Args:
            news_df: 新闻 DataFrame
            symbol: 资产符号

        Returns:
            聚合后的情感数据（每日一条）
        """
        # 过滤包含该 ticker 的新闻
        symbol_news = news_df[news_df['ticker_list'].apply(
            lambda x: symbol in x if isinstance(x, list) else False
        )].copy()

        if symbol_news.empty:
            logger.warning(f"{symbol} 没有相关新闻")
            return pd.DataFrame()

        # 提取日期
        symbol_news['date'] = pd.to_datetime(symbol_news['timestamp']).dt.date

        # 按日期聚合
        daily_sentiment = symbol_news.groupby('date').agg({
            'sentiment_score': ['mean', 'std', 'count'],
            'sentiment_confidence': 'mean'
        }).reset_index()

        # 扁平化列名
        daily_sentiment.columns = ['date', 'sentiment_mean', 'sentiment_std', 'news_count', 'sentiment_confidence']

        # 填充缺失的标准差
        daily_sentiment['sentiment_std'] = daily_sentiment['sentiment_std'].fillna(0)

        # 转换日期类型
        daily_sentiment['date'] = pd.to_datetime(daily_sentiment['date'])

        logger.info(f"{symbol} 聚合情感数据: {len(daily_sentiment)} 天")
        return daily_sentiment

    def merge_price_sentiment(self, price_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
        """合并价格数据和情感数据

        Args:
            price_df: 价格数据
            sentiment_df: 情感数据

        Returns:
            合并后的数据
        """
        if sentiment_df.empty:
            # 如果没有情感数据，添加默认值
            price_df['sentiment_mean'] = 0.0
            price_df['sentiment_std'] = 0.0
            price_df['news_count'] = 0
            price_df['sentiment_confidence'] = 0.0
            return price_df

        # 确保日期类型一致
        price_df['date'] = pd.to_datetime(price_df['date'])
        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])

        # 左连接（保留所有价格数据）
        merged_df = pd.merge(price_df, sentiment_df, on='date', how='left')

        # 填充缺失的情感数据（没有新闻的日期）
        merged_df['sentiment_mean'] = merged_df['sentiment_mean'].fillna(0)
        merged_df['sentiment_std'] = merged_df['sentiment_std'].fillna(0)
        merged_df['news_count'] = merged_df['news_count'].fillna(0).astype(int)
        merged_df['sentiment_confidence'] = merged_df['sentiment_confidence'].fillna(0)

        logger.info(f"合并后数据: {len(merged_df)} 条")
        return merged_df

    def compute_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """计算所有特征

        Args:
            df: 包含价格和情感的数据
            symbol: 资产符号

        Returns:
            添加了特征的数据
        """
        logger.info(f"计算 {symbol} 的特征...")

        # 1. 计算基础技术指标特征（32 维）
        df = BasicFeatures.compute_all_basic_features(df)

        # 2. 添加情感相关特征（简化版，迭代 3 会扩展）
        df['sentiment_ma5'] = df['sentiment_mean'].rolling(window=5).mean()
        df['sentiment_ma10'] = df['sentiment_mean'].rolling(window=10).mean()
        df['sentiment_momentum'] = df['sentiment_mean'] - df['sentiment_mean'].shift(1)

        logger.info(f"{symbol} 特征计算完成，共 {len(df.columns)} 列")

        return df

    def validate_features(self, df: pd.DataFrame, symbol: str) -> Dict:
        """验证特征质量

        Args:
            df: 特征数据
            symbol: 资产符号

        Returns:
            验证结果字典
        """
        # 识别特征列（排除基础列）
        base_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                       'adjusted_close', 'quality']
        feature_columns = [col for col in df.columns if col not in base_columns]

        # 计算统计信息
        total_features = len(feature_columns)
        total_records = len(df)

        # 缺失值统计
        missing_counts = df[feature_columns].isnull().sum()
        total_missing = missing_counts.sum()
        missing_rate = total_missing / (total_features * total_records)

        # 无穷值统计
        inf_counts = np.isinf(df[feature_columns].select_dtypes(include=[np.number])).sum().sum()
        inf_rate = inf_counts / (total_features * total_records)

        # 特征完整率
        completeness_rate = 1 - missing_rate - inf_rate

        validation_result = {
            'symbol': symbol,
            'total_features': total_features,
            'total_records': total_records,
            'missing_rate': missing_rate,
            'inf_rate': inf_rate,
            'completeness_rate': completeness_rate,
            'features_with_missing': (missing_counts > 0).sum(),
        }

        logger.info(f"{symbol} 特征验证: 完整率 {completeness_rate:.2%}, "
                   f"缺失率 {missing_rate:.4%}, 无穷值率 {inf_rate:.4%}")

        return validation_result

    def save_features(self, df: pd.DataFrame, symbol: str,
                     output_path: str = "/opt/mt5-crs/data_lake/features_daily"):
        """保存特征数据

        Args:
            df: 特征数据
            symbol: 资产符号
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # 清理文件名
        safe_symbol = symbol.replace('/', '_').replace('=', '_').replace('^', '_')
        output_file = output_path / f"{safe_symbol}_features.parquet"

        # 保存
        df.to_parquet(output_file, engine='pyarrow', compression='gzip', index=False)

        logger.info(f"{symbol} 特征数据已保存到: {output_file}")

    def process_single_symbol(self, symbol: str,
                              price_path: str = "/opt/mt5-crs/data_lake/price_daily",
                              news_path: str = "/opt/mt5-crs/data_lake/news_processed",
                              output_path: str = "/opt/mt5-crs/data_lake/features_daily") -> Optional[pd.DataFrame]:
        """处理单个资产的完整流程

        Args:
            symbol: 资产符号
            price_path: 价格数据路径
            news_path: 新闻数据路径
            output_path: 输出路径

        Returns:
            特征数据 DataFrame
        """
        logger.info(f"{'='*60}")
        logger.info(f"处理 {symbol}")
        logger.info(f"{'='*60}")

        try:
            # 1. 加载价格数据
            price_df = self.load_price_data(symbol, price_path)
            if price_df is None:
                return None

            # 2. 加载新闻情感数据
            news_df = self.load_news_sentiment(news_path)

            # 3. 聚合情感数据
            if news_df is not None:
                sentiment_df = self.aggregate_sentiment_by_symbol(news_df, symbol)
            else:
                sentiment_df = pd.DataFrame()

            # 4. 合并价格和情感
            merged_df = self.merge_price_sentiment(price_df, sentiment_df)

            # 5. 计算特征
            features_df = self.compute_features(merged_df, symbol)

            # 6. 验证特征
            validation_result = self.validate_features(features_df, symbol)

            # 7. 保存特征
            self.save_features(features_df, symbol, output_path)

            logger.info(f"{symbol} 处理完成 ✓")
            return features_df

        except Exception as e:
            logger.error(f"处理 {symbol} 失败: {e}", exc_info=True)
            return None

    def process_multiple_symbols(self, symbols: List[str], **kwargs) -> Dict[str, pd.DataFrame]:
        """批量处理多个资产

        Args:
            symbols: 资产列表
            **kwargs: 传递给 process_single_symbol 的参数

        Returns:
            {symbol: DataFrame} 字典
        """
        results = {}
        validation_results = []

        logger.info(f"开始批量处理 {len(symbols)} 个资产...")

        for symbol in symbols:
            df = self.process_single_symbol(symbol, **kwargs)
            if df is not None:
                results[symbol] = df

        logger.info(f"批量处理完成: {len(results)}/{len(symbols)} 个资产成功")

        return results


def main():
    """主函数示例"""
    import yaml

    # 加载配置
    with open('/opt/mt5-crs/config/features.yaml', 'r') as f:
        config = yaml.safe_load(f)

    with open('/opt/mt5-crs/config/assets.yaml', 'r') as f:
        assets_config = yaml.safe_load(f)

    # 创建特征工程器
    engineer = FeatureEngineer(config)

    # 测试：处理几个资产
    test_symbols = ['AAPL.US', 'MSFT.US', 'BTC-USD', 'GSPC.INDX']

    results = engineer.process_multiple_symbols(test_symbols)

    # 打印结果
    print("\n" + "="*80)
    print("特征工程测试结果")
    print("="*80)

    for symbol, df in results.items():
        print(f"\n{symbol}:")
        print(f"  - 记录数: {len(df)}")
        print(f"  - 特征数: {len(df.columns)}")
        print(f"  - 日期范围: {df['date'].min()} 到 {df['date'].max()}")
        print(f"  - 前 5 个特征列: {list(df.columns[10:15])}")


if __name__ == '__main__':
    main()
