"""Ticker 提取器 - 从新闻文本中提取股票代码

作为 API 自带 ticker 的 fallback 机制
"""
import re
import logging
from typing import List, Set, Dict, Any

logger = logging.getLogger(__name__)


class TickerExtractor:
    """Ticker 提取器

    功能：
    1. 从新闻标题和内容中提取股票代码
    2. 支持常见格式：$AAPL, TSLA, Apple Inc.
    3. 使用预定义的公司名-代码映射表
    4. 去重和验证
    """

    def __init__(self):
        """初始化提取器"""
        # 常见公司名到 Ticker 的映射（示例）
        # 实际应用中应该使用更完整的数据库
        self.company_ticker_map = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'facebook': 'META',
            'nvidia': 'NVDA',
            'netflix': 'NFLX',
            'intel': 'INTC',
            'amd': 'AMD',
            'ibm': 'IBM',
            'oracle': 'ORCL',
            'cisco': 'CSCO',
            'qualcomm': 'QCOM',
            'paypal': 'PYPL',
            'adobe': 'ADBE',
            'salesforce': 'CRM',
            'broadcom': 'AVGO',
            'jpmorgan': 'JPM',
            'jp morgan': 'JPM',
            'bank of america': 'BAC',
            'wells fargo': 'WFC',
            'goldman sachs': 'GS',
            'morgan stanley': 'MS',
            'visa': 'V',
            'mastercard': 'MA',
            'berkshire hathaway': 'BRK.B',
            'johnson & johnson': 'JNJ',
            'unitedhealth': 'UNH',
            'exxon': 'XOM',
            'exxonmobil': 'XOM',
            'chevron': 'CVX',
            'walmart': 'WMT',
            'procter & gamble': 'PG',
            'coca cola': 'KO',
            'coca-cola': 'KO',
            'pepsi': 'PEP',
            'pepsico': 'PEP',
            'disney': 'DIS',
            'nike': 'NKE',
            'mcdonald': 'MCD',
            'starbucks': 'SBUX',
            'home depot': 'HD',
            'boeing': 'BA',
            'caterpillar': 'CAT',
            '3m': 'MMM',
            'general electric': 'GE',
            'ge': 'GE',
            'ford': 'F',
            'general motors': 'GM',
            'gm': 'GM',
        }

        # 常见的 ticker 模式（2-5个大写字母）
        self.ticker_pattern = re.compile(r'\b[A-Z]{2,5}\b')

        # $TICKER 格式
        self.dollar_ticker_pattern = re.compile(r'\$([A-Z]{2,5})\b')

        logger.info(f"TickerExtractor 已初始化，内置 {len(self.company_ticker_map)} 个公司映射")

    def extract(self, text: str, threshold: int = 1) -> List[str]:
        """从文本中提取 ticker

        Args:
            text: 新闻标题或内容
            threshold: 最小出现次数阈值

        Returns:
            提取到的 ticker 列表（已去重）
        """
        if not text:
            return []

        tickers = set()

        # 1. 提取 $TICKER 格式
        dollar_tickers = self.dollar_ticker_pattern.findall(text)
        tickers.update(dollar_tickers)

        # 2. 根据公司名映射
        text_lower = text.lower()
        for company_name, ticker in self.company_ticker_map.items():
            if company_name in text_lower:
                tickers.add(ticker)

        # 3. 提取可能的 TICKER（严格匹配）
        potential_tickers = self.ticker_pattern.findall(text)

        # 过滤常见的非 ticker 单词
        exclude_words = {
            'US', 'UK', 'EU', 'CEO', 'CFO', 'IPO', 'ETF', 'SEC', 'FBI', 'CIA',
            'NYSE', 'NASDAQ', 'DOW', 'SPX', 'API', 'AI', 'ML', 'IT', 'HR',
            'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'WILL', 'BE',
            'ARE', 'WAS', 'HAS', 'HAD', 'BUT', 'NOT', 'ALL', 'CAN', 'NEW',
            'BREAKING', 'UPDATE', 'LIVE', 'TOP', 'BEST', 'MARKET', 'STOCK',
        }

        for ticker in potential_tickers:
            if ticker not in exclude_words and len(ticker) <= 5:
                # 简单的启发式：如果是已知的 ticker，才添加
                if ticker in self.company_ticker_map.values():
                    tickers.add(ticker)

        return sorted(list(tickers))

    def extract_from_news(self, news_item: Dict[str, Any]) -> List[str]:
        """从新闻数据中提取 ticker

        优先使用 API 自带的 ticker，如果没有则从标题+内容中提取

        Args:
            news_item: 新闻数据字典

        Returns:
            提取到的 ticker 列表
        """
        # 1. 优先使用 API 自带的 ticker
        existing_tickers = news_item.get('tickers', [])
        if existing_tickers:
            logger.debug(f"使用 API 自带的 tickers: {existing_tickers}")
            return existing_tickers

        # 2. 如果没有，从标题和内容中提取
        title = news_item.get('title', '')
        content = news_item.get('content', '')

        # 先从标题提取（权重更高）
        title_tickers = self.extract(title)

        # 再从内容提取
        content_tickers = self.extract(content)

        # 合并去重（标题中的优先）
        all_tickers = []
        seen = set()

        for ticker in title_tickers + content_tickers:
            if ticker not in seen:
                all_tickers.append(ticker)
                seen.add(ticker)

        if all_tickers:
            logger.debug(f"Fallback 提取到 tickers: {all_tickers}")
        else:
            logger.debug("未能提取到 ticker")

        return all_tickers

    def add_company_mapping(self, company_name: str, ticker: str):
        """添加公司名-ticker 映射

        Args:
            company_name: 公司名（小写）
            ticker: 股票代码（大写）
        """
        self.company_ticker_map[company_name.lower()] = ticker.upper()
        logger.info(f"添加映射: {company_name} -> {ticker}")

    def batch_add_mappings(self, mappings: Dict[str, str]):
        """批量添加映射

        Args:
            mappings: {company_name: ticker} 字典
        """
        for company, ticker in mappings.items():
            self.add_company_mapping(company, ticker)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    extractor = TickerExtractor()

    # 测试用例
    test_cases = [
        "$AAPL surges to new high as iPhone sales exceed expectations",
        "Tesla CEO Elon Musk announces new factory",
        "Microsoft and Google compete in AI race",
        "Breaking: Amazon stock drops 5% after earnings miss",
        "TSLA MSFT GOOGL all seeing gains today",
        "The market is down but NVIDIA remains strong",
    ]

    print("=== Ticker 提取测试 ===\n")

    for text in test_cases:
        tickers = extractor.extract(text)
        print(f"文本: {text}")
        print(f"提取: {tickers}")
        print()
