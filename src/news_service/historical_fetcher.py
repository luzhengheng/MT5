"""
历史新闻数据采集器
支持断点续拉、限流控制、分页处理
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import requests
import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalNewsFetcher:
    """历史新闻数据采集器"""

    def __init__(self, config: Dict):
        self.config = config
        self.api_key = os.getenv(config['data_source']['api_key_env'])
        self.endpoint = config['data_source']['endpoint']
        self.rate_limit = config['rate_limiting']['requests_per_minute']
        self.retry_attempts = config['rate_limiting']['retry_attempts']
        self.retry_delays = config['rate_limiting']['retry_delays']

        # 检查点配置
        self.checkpoint_enabled = config['checkpoint']['enabled']
        self.checkpoint_file = config['checkpoint']['checkpoint_file']
        self.save_interval = config['checkpoint']['save_interval']

        # 输出配置
        self.output_base_path = config['output']['base_path']

        # 确保输出目录存在
        Path(self.output_base_path).mkdir(parents=True, exist_ok=True)

        # 确保检查点目录存在
        if self.checkpoint_enabled:
            Path(self.checkpoint_file).parent.mkdir(parents=True, exist_ok=True)

        # 请求间隔（秒）
        self.request_interval = 60.0 / self.rate_limit

        logger.info(f"初始化 HistoricalNewsFetcher，限流: {self.rate_limit} req/min")

    def load_checkpoint(self) -> Optional[Dict]:
        """加载检查点"""
        if not self.checkpoint_enabled or not os.path.exists(self.checkpoint_file):
            return None

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            logger.info(f"加载检查点: {checkpoint}")
            return checkpoint
        except Exception as e:
            logger.error(f"加载检查点失败: {e}")
            return None

    def save_checkpoint(self, checkpoint: Dict):
        """保存检查点"""
        if not self.checkpoint_enabled:
            return

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"保存检查点: {checkpoint}")
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")

    def fetch_news_for_date(self, date: str, symbols: List[str] = None) -> List[Dict]:
        """获取指定日期的新闻数据

        Args:
            date: 日期字符串 (YYYY-MM-DD)
            symbols: 可选的 ticker 列表

        Returns:
            新闻列表
        """
        params = {
            'api_token': self.api_key,
            'from': date,
            'to': date,
            'limit': self.config['pagination']['limit_per_request'],
            'offset': 0
        }

        if symbols:
            params['s'] = ','.join(symbols)

        all_news = []
        offset = 0

        while True:
            params['offset'] = offset

            # 带重试的请求
            news_batch = self._request_with_retry(params)

            if not news_batch:
                break

            all_news.extend(news_batch)

            # 检查是否还有更多数据
            if len(news_batch) < params['limit']:
                break

            offset += self.config['pagination']['offset_increment']

            # 限流
            time.sleep(self.request_interval)

        logger.info(f"日期 {date} 获取到 {len(all_news)} 条新闻")
        return all_news

    def _request_with_retry(self, params: Dict) -> List[Dict]:
        """带指数退避重试的请求"""
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(self.endpoint, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                # EODHD API 返回格式可能不同，需要根据实际调整
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'news' in data:
                    return data['news']
                else:
                    logger.warning(f"未预期的响应格式: {type(data)}")
                    return []

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = self.retry_delays[attempt] if attempt < len(self.retry_delays) else self.retry_delays[-1]
                    logger.warning(f"触发限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP 错误: {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delays[attempt])
                    else:
                        return []

            except Exception as e:
                logger.error(f"请求失败: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delays[attempt])
                else:
                    return []

        return []

    def process_news_data(self, news_list: List[Dict]) -> pd.DataFrame:
        """处理原始新闻数据，提取关键字段

        Args:
            news_list: 原始新闻列表

        Returns:
            处理后的 DataFrame
        """
        processed_news = []

        for news in news_list:
            try:
                # 提取 ticker 列表
                # 注意：EODHD API 的字段名称可能不同，需根据实际调整
                ticker_field = news.get('symbols') or news.get('tickers') or news.get('tags') or ''

                if isinstance(ticker_field, str):
                    ticker_list = [t.strip() for t in ticker_field.split(',') if t.strip()]
                elif isinstance(ticker_field, list):
                    ticker_list = ticker_field
                else:
                    ticker_list = []

                # 如果配置要求必须有 ticker，则跳过没有 ticker 的新闻
                if self.config['filters']['require_ticker'] and not ticker_list:
                    continue

                processed_news.append({
                    'news_id': news.get('id') or news.get('uuid') or f"{news.get('date')}_{news.get('title', '')[:20]}",
                    'timestamp': pd.to_datetime(news.get('date') or news.get('published_at')),
                    'ticker_list': ticker_list,
                    'title': news.get('title', ''),
                    'content': news.get('content') or news.get('text') or '',
                    'source': news.get('source', ''),
                    'url': news.get('link') or news.get('url', ''),
                })

            except Exception as e:
                logger.warning(f"处理新闻失败: {e}")
                continue

        return pd.DataFrame(processed_news)

    def fetch_historical_news(self, start_date: str, end_date: str = None, symbols: List[str] = None) -> pd.DataFrame:
        """批量获取历史新闻数据

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
            symbols: 可选的 ticker 列表

        Returns:
            合并后的 DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # 加载检查点
        checkpoint = self.load_checkpoint()
        if checkpoint:
            start_date = checkpoint.get('last_date', start_date)
            logger.info(f"从检查点恢复，起始日期: {start_date}")

        # 生成日期列表
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_list = [(start + timedelta(days=x)).strftime('%Y-%m-%d')
                     for x in range((end - start).days + 1)]

        all_news_df = pd.DataFrame()
        news_count = 0

        logger.info(f"开始采集历史新闻: {start_date} 到 {end_date}，共 {len(date_list)} 天")

        for date in tqdm(date_list, desc="采集新闻"):
            try:
                # 获取当天新闻
                news_list = self.fetch_news_for_date(date, symbols)

                if news_list:
                    # 处理新闻数据
                    news_df = self.process_news_data(news_list)

                    if not news_df.empty:
                        all_news_df = pd.concat([all_news_df, news_df], ignore_index=True)
                        news_count += len(news_df)

                # 定期保存检查点
                if news_count > 0 and news_count % self.save_interval == 0:
                    self.save_checkpoint({'last_date': date, 'news_count': news_count})
                    logger.info(f"已采集 {news_count} 条新闻，保存检查点")

            except Exception as e:
                logger.error(f"采集日期 {date} 失败: {e}")
                continue

        logger.info(f"历史新闻采集完成，共 {len(all_news_df)} 条（含 ticker: {len(all_news_df[all_news_df['ticker_list'].str.len() > 0])} 条）")

        # 清除检查点
        if self.checkpoint_enabled and os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            logger.info("采集完成，清除检查点")

        return all_news_df

    def save_to_parquet(self, df: pd.DataFrame, partition_by_month: bool = True):
        """保存为 Parquet 文件

        Args:
            df: 新闻 DataFrame
            partition_by_month: 是否按月分区
        """
        if df.empty:
            logger.warning("DataFrame 为空，跳过保存")
            return

        df = df.copy()
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month

        if partition_by_month:
            # 按年月分区保存
            for (year, month), group in df.groupby(['year', 'month']):
                output_dir = Path(self.output_base_path) / str(year) / f"{month:02d}"
                output_dir.mkdir(parents=True, exist_ok=True)

                output_file = output_dir / f"news_raw_{year}{month:02d}.parquet"

                # 移除分区列
                group_to_save = group.drop(columns=['year', 'month'])

                group_to_save.to_parquet(
                    output_file,
                    engine='pyarrow',
                    compression='gzip',
                    index=False
                )

                logger.info(f"保存 {len(group)} 条新闻到 {output_file}")
        else:
            # 单文件保存
            output_file = Path(self.output_base_path) / "news_raw_all.parquet"
            df.to_parquet(
                output_file,
                engine='pyarrow',
                compression='gzip',
                index=False
            )
            logger.info(f"保存 {len(df)} 条新闻到 {output_file}")


def main():
    """主函数示例"""
    import yaml

    # 加载配置
    with open('/opt/mt5-crs/config/news_historical.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 创建采集器
    fetcher = HistoricalNewsFetcher(config)

    # 采集历史新闻
    start_date = config['date_range']['start_date']
    end_date = config['date_range']['end_date']

    news_df = fetcher.fetch_historical_news(start_date, end_date)

    # 保存数据
    fetcher.save_to_parquet(news_df, partition_by_month=True)

    # 打印统计信息
    print(f"\n=== 采集统计 ===")
    print(f"总新闻数: {len(news_df)}")
    print(f"含 ticker 新闻数: {len(news_df[news_df['ticker_list'].str.len() > 0])}")
    print(f"日期范围: {news_df['timestamp'].min()} 到 {news_df['timestamp'].max()}")
    print(f"唯一来源数: {news_df['source'].nunique()}")


if __name__ == '__main__':
    main()
