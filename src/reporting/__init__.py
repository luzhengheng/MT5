"""
Reporting Package - Trading Bot Analytics
==========================================

Task #019.01: Signal Verification Dashboard

包含报告和分析相关的模块：
- log_parser.py: 解析交易日志生成结构化数据
"""

from .log_parser import TradeLogParser

__all__ = ['TradeLogParser']
