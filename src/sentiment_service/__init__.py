"""情感分析服务模块"""
from .finbert_analyzer import FinBERTAnalyzer
from .news_filter_consumer import NewsFilterConsumer

__all__ = ['FinBERTAnalyzer', 'NewsFilterConsumer']
