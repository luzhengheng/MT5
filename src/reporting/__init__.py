"""
回测报告模块 - 生成专业的交易策略分析报告
"""

from .tearsheet import TearSheetGenerator, calculate_deflated_sharpe_ratio

__all__ = ['TearSheetGenerator', 'calculate_deflated_sharpe_ratio']
